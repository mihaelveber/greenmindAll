"""
Task for processing documents with RAG engine
Generates chunks, contexts, and embeddings for uploaded documents
"""

import logging
import time
from celery import shared_task
from accounts.models import Document
from accounts.vector_models import DocumentChunk as VectorDocumentChunk
from accounts.rag_engine import SemanticChunker, ContextGenerator
from accounts.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)


class AnthropicRateLimiter:
    """
    Token bucket rate limiter for Anthropic API
    TIER 1: 50,000 tokens/min
    Conservative: 40,000 tokens/min (80% of limit)
    Average chunk: ~2000 tokens (document + chunk text)
    Max chunks/min: 20 chunks (40,000 / 2000)
    """
    def __init__(self, tokens_per_minute=40000, tokens_per_chunk=2000):
        self.tokens_per_minute = tokens_per_minute
        self.tokens_per_chunk = tokens_per_chunk
        self.max_chunks_per_minute = tokens_per_minute // tokens_per_chunk
        self.last_reset = time.time()
        self.chunks_processed = 0
        
    def wait_if_needed(self):
        """Wait if we've hit rate limit"""
        current_time = time.time()
        elapsed = current_time - self.last_reset
        
        # Reset counter every minute
        if elapsed >= 60:
            self.chunks_processed = 0
            self.last_reset = current_time
            return
        
        # If we've hit limit, wait until minute resets
        if self.chunks_processed >= self.max_chunks_per_minute:
            wait_time = 60 - elapsed
            logger.info(f'⏱️ Rate limit reached ({self.chunks_processed} chunks), waiting {wait_time:.1f}s...')
            time.sleep(wait_time)
            self.chunks_processed = 0
            self.last_reset = time.time()
        
        self.chunks_processed += 1


@shared_task(bind=True)
def process_document_with_rag(self, document_id: int):
    """
    Process uploaded document: chunk, generate contexts, create embeddings
    
    Args:
        document_id: ID of uploaded Document
    """
    from accounts.models import AITaskStatus
    
    task_id = self.request.id
    
    try:
        # Get document first to link task to user
        document = Document.objects.get(id=document_id)
        
        # Create or get task status
        task_status, created = AITaskStatus.objects.get_or_create(
            task_id=task_id,
            defaults={
                'user': document.user,
                'document': document,
                'task_type': 'rag_processing',
                'status': 'running',
                'progress': 0
            }
        )
        if not created:
            task_status.document = document
            task_status.status = 'running'
            task_status.progress = 0
            task_status.save()
        
        logger.info(f'Processing document {document.file_name} (ID: {document_id}) with RAG engine')
        
        # Set document status to processing
        document.rag_processing_status = 'processing'
        document.save(update_fields=['rag_processing_status'])
        
        task_status.progress = 10
        task_status.metadata = {'stage': 'reading_file'}
        task_status.save()
        
        # Read document content
        content = _read_document_content(document)
        if not content:
            raise ValueError(f"Could not extract text from document {document.file_name}")
        
        task_status.progress = 20
        task_status.metadata = {'stage': 'chunking', 'content_length': len(content)}
        task_status.save()
        
        # Semantic chunking with larger size for Excel/CSV (better table preservation)
        chunker = SemanticChunker()
        if document.file_type in ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
                                   'application/vnd.ms-excel', 'text/csv']:
            # Larger chunks for structured data (tables) - prevents splitting rows
            chunks = chunker.chunk_by_paragraphs(content, max_chunk_size=2000, overlap=300)
            logger.info(f'Created {len(chunks)} LARGE chunks for Excel/CSV document {document.file_name}')
        else:
            # Normal chunks for text documents
            chunks = chunker.chunk_by_paragraphs(content, max_chunk_size=1000, overlap=200)
            logger.info(f'Created {len(chunks)} chunks for document {document.file_name}')
        
        task_status.progress = 30
        task_status.metadata = {'stage': 'generating_contexts', 'total_chunks': len(chunks)}
        task_status.save()
        
        # Generate contexts for each chunk using Anthropic Contextual Retrieval
        context_generator = ContextGenerator()
        chunk_contexts = []
        
        # Anthropic Contextual Retrieval with Prompt Caching
        # This improves RAG accuracy by 49% according to Anthropic research
        from anthropic import Anthropic
        from django.conf import settings
        import os
        
        # Check if contextual chunking is enabled (default: True with rate limiting)
        enable_contextual_chunking = os.getenv('ENABLE_CONTEXTUAL_CHUNKING', 'true').lower() == 'true'
        
        # For large documents (>100 chunks) - disable to avoid rate limits
        # But for normal Excel files with reasonable size, keep enabled
        if len(chunks) > 100:
            logger.warning(f'⚠️ Very large document ({len(chunks)} chunks) - disabling contextual chunking')
            enable_contextual_chunking = False
        
        # For Excel/CSV files - use slower rate limit but keep enabled for better RAG quality
        is_excel_csv = document.file_type in ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
                                               'application/vnd.ms-excel', 'text/csv']
        
        # Initialize rate limiter - slower for Excel/CSV (10 chunks/min vs 20)
        if is_excel_csv and enable_contextual_chunking:
            rate_limiter = AnthropicRateLimiter(tokens_per_minute=20000, tokens_per_chunk=2000)  # More conservative
            logger.info(f'📊 Excel/CSV document - using conservative rate limit (10 chunks/min)')
        else:
            rate_limiter = AnthropicRateLimiter() if enable_contextual_chunking else None
        
        anthropic_client = None
        if enable_contextual_chunking and hasattr(settings, 'ANTHROPIC_API_KEY') and settings.ANTHROPIC_API_KEY:
            anthropic_client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            logger.info('✅ Using Anthropic Claude Haiku with Prompt Caching + Rate Limiting')
        else:
            logger.info('⚡ Contextual chunking disabled - using fast simple context')
        
        for i, chunk_text in enumerate(chunks):
            position = 'beginning' if i == 0 else ('end' if i == len(chunks)-1 else 'middle')
            
            # Try Anthropic Contextual Retrieval first, fallback to simple context
            if anthropic_client:
                # Wait if we're hitting rate limits
                if rate_limiter:
                    rate_limiter.wait_if_needed()
                
                try:
                    # Anthropic prompt for context generation WITH PROMPT CACHING
                    # Cache the whole document once, reuse for all chunks (90% cheaper!)
                    response = anthropic_client.messages.create(
                        model="claude-3-5-haiku-20241022",
                        max_tokens=200,
                        temperature=0.0,
                        system=[
                            {
                                "type": "text",
                                "text": "You are a document context generator. Generate concise context for document chunks to improve search retrieval.",
                                "cache_control": {"type": "ephemeral"}
                            }
                        ],
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": f"<document>\n{content}\n</document>",
                                        "cache_control": {"type": "ephemeral"}  # Cache entire document!
                                    },
                                    {
                                        "type": "text",
                                        "text": f"""Here is the chunk we want to situate within the whole document:
<chunk>
{chunk_text}
</chunk>

Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk. Answer only with the succinct context and nothing else."""
                                    }
                                ]
                            }
                        ]
                    )
                    
                    context = response.content[0].text
                    
                    # Log cache performance
                    usage = response.usage
                    cache_read = getattr(usage, 'cache_read_input_tokens', 0)
                    cache_creation = getattr(usage, 'cache_creation_input_tokens', 0)
                    logger.info(f'Chunk {i}/{len(chunks)}: context={len(context)} chars, cache_read={cache_read}, cache_creation={cache_creation}')
                    
                except Exception as e:
                    logger.warning(f'Anthropic context generation failed for chunk {i}: {e}, falling back to simple context')
                    context = context_generator.generate_chunk_context(
                        chunk_text=chunk_text,
                        document_name=document.file_name,
                        chunk_position=position
                    )
            else:
                # Fallback to simple context generation
                context = context_generator.generate_chunk_context(
                    chunk_text=chunk_text,
                    document_name=document.file_name,
                    chunk_position=position
                )
            
            chunk_contexts.append((chunk_text, context))
            
            # Update progress
            progress = 30 + int((i / len(chunks)) * 20)
            task_status.progress = progress
            task_status.save()
        
        task_status.progress = 50
        task_status.metadata = {'stage': 'generating_embeddings'}
        task_status.save()
        
        # Get embedding service (uses default from database with fallback)
        embedding_service = get_embedding_service()
        
        if not embedding_service:
            # No embedding service available (no API keys configured)
            logger.warning(f'No embedding service available for document {document.file_name}. Skipping embeddings.')
            
            # Still save chunks without embeddings
            chunk_objects = []
            for i, (chunk_text, context) in enumerate(chunk_contexts):
                chunk_id = f"{document.id}_{i}"
                position = 'beginning' if i == 0 else ('end' if i == len(chunks)-1 else 'middle')
                
                chunk_obj = VectorDocumentChunk(
                    document=document,
                    chunk_index=i,
                    chunk_id=chunk_id,
                    content=chunk_text,
                    context=context,
                    contextualized_content=f"{context}\n\n{chunk_text}",
                    position=position,
                    char_count=len(chunk_text),
                    word_count=len(chunk_text.split()),
                    token_count=len(chunk_text) // 4,
                    language='en',
                )
                chunk_objects.append(chunk_obj)
            
            VectorDocumentChunk.objects.bulk_create(chunk_objects)
            
            task_status.status = 'completed'
            task_status.progress = 100
            task_status.metadata = {
                'stage': 'completed_without_embeddings',
                'total_chunks': len(chunk_objects),
                'warning': 'No embedding API keys configured'
            }
            task_status.save()
            
            return {
                'success': True,
                'document_id': document_id,
                'filename': document.file_name,
                'chunks_created': len(chunk_objects),
                'embeddings_generated': False,
                'warning': 'No embedding API keys configured'
            }
        
        logger.info(f'Using embedding model: {embedding_service.provider}/{embedding_service.model}')
        
        # Generate embeddings for all chunks (batch processing)
        contextualized_texts = [f"{ctx}\n\n{txt}" for txt, ctx in chunk_contexts]
        embeddings = embedding_service.embed_batch(contextualized_texts)
        
        task_status.progress = 70
        task_status.metadata = {'stage': 'saving_to_database'}
        task_status.save()
        
        # Delete old chunks for this document
        VectorDocumentChunk.objects.filter(document=document).delete()
        
        # Save chunks to database with embeddings
        chunk_objects = []
        for i, ((chunk_text, context), embedding) in enumerate(zip(chunk_contexts, embeddings)):
            chunk_id = f"{document.id}_{i}"
            position = 'beginning' if i == 0 else ('end' if i == len(chunks)-1 else 'middle')
            
            chunk_obj = VectorDocumentChunk(
                document=document,
                chunk_index=i,
                chunk_id=chunk_id,
                content=chunk_text,
                context=context,
                contextualized_content=f"{context}\n\n{chunk_text}",
                position=position,
                char_count=len(chunk_text),
                word_count=len(chunk_text.split()),
                token_count=len(chunk_text) // 4,  # Rough estimate
                language='en',
            )
            
            # Set primary embedding based on provider
            if embedding_service.provider == 'openai':
                chunk_obj.embedding = embedding
            elif embedding_service.provider == 'voyage':
                chunk_obj.voyage_embedding = embedding
            elif embedding_service.provider == 'jina':
                chunk_obj.jina_embedding = embedding
            
            chunk_objects.append(chunk_obj)
            
            # Update progress
            progress = 70 + int((i / len(chunks)) * 25)
            task_status.progress = progress
            task_status.save()
        
        # Bulk create all chunks
        VectorDocumentChunk.objects.bulk_create(chunk_objects)
        
        logger.info(f'Saved {len(chunk_objects)} chunks to database')
        
        # Update document RAG status
        from django.utils import timezone
        document.rag_processing_status = 'completed'
        document.rag_chunks_count = len(chunk_objects)
        document.rag_processed_at = timezone.now()
        document.rag_error = ''
        document.save(update_fields=['rag_processing_status', 'rag_chunks_count', 'rag_processed_at', 'rag_error'])
        
        task_status.status = 'completed'
        task_status.progress = 100
        task_status.metadata = {
            'stage': 'completed',
            'total_chunks': len(chunk_objects),
            'embedding_model': f"{embedding_service.provider}/{embedding_service.model}",
            'embedding_dimensions': embedding_service.get_dimensions()
        }
        task_status.save()
        
        return {
            'success': True,
            'document_id': document_id,
            'filename': document.file_name,
            'chunks_created': len(chunk_objects)
        }
    
    except Document.DoesNotExist:
        error = f'Document {document_id} not found'
        logger.error(error)
        
        if 'task_status' in locals():
            task_status.status = 'failed'
            task_status.error = error
            task_status.save()
        
        return {'success': False, 'error': error}
    
    except Exception as e:
        error = f'Error processing document {document_id}: {str(e)}'
        logger.error(error, exc_info=True)
        
        # Update document status to failed
        if 'document' in locals():
            document.rag_processing_status = 'failed'
            document.rag_error = str(e)
            document.save(update_fields=['rag_processing_status', 'rag_error'])
        
        if 'task_status' in locals():
            task_status.status = 'failed'
            task_status.error = error
            task_status.save()
        
        return {'success': False, 'error': error}


def _read_document_content(doc: Document) -> str:
    """Read extracted text content from document"""
    import os
    from django.conf import settings
    
    # Try to read extracted text file first
    extracted_file = f"{doc.file_path}.extracted.txt"
    extracted_path = os.path.join(settings.MEDIA_ROOT, extracted_file)
    
    if os.path.exists(extracted_path):
        try:
            with open(extracted_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.warning(f'Failed to read extracted file {extracted_path}: {e}')
    
    # Fallback: extract text from original file
    file_path = os.path.join(settings.MEDIA_ROOT, doc.file_path)
    if not os.path.exists(file_path):
        return ""
    
    try:
        from accounts.document_parser import parse_document
        # Use actual file path for extension detection, not display name
        text, _ = parse_document(file_path, os.path.basename(file_path))
        
        if text:
            # Save extracted text for future use
            os.makedirs(os.path.dirname(extracted_path), exist_ok=True)
            with open(extracted_path, 'w', encoding='utf-8') as f:
                f.write(text)
        
        return text
    except Exception as e:
        logger.error(f'Failed to extract text from {file_path}: {e}')
        return ""


@shared_task
def reprocess_all_documents():
    """
    Reprocess all existing documents with RAG engine
    Useful after upgrading chunking or embedding models
    """
    from accounts.models import Document
    
    documents = Document.objects.all()
    total = documents.count()
    
    logger.info(f'Reprocessing {total} documents with RAG engine')
    
    results = {
        'total': total,
        'success': 0,
        'failed': 0,
        'errors': []
    }
    
    for i, doc in enumerate(documents):
        try:
            logger.info(f'Processing document {i+1}/{total}: {doc.filename}')
            process_document_with_rag.delay(doc.id)
            results['success'] += 1
        except Exception as e:
            logger.error(f'Failed to queue document {doc.id}: {e}')
            results['failed'] += 1
            results['errors'].append({
                'document_id': doc.id,
                'filename': doc.filename,
                'error': str(e)
            })
    
    return results
