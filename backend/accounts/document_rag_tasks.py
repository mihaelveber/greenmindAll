"""
Task for processing documents with RAG engine
Generates chunks, contexts, and embeddings for uploaded documents
"""

import logging
from celery import shared_task
from accounts.models import Document
from accounts.vector_models import DocumentChunk as VectorDocumentChunk
from accounts.rag_engine import SemanticChunker, ContextGenerator
from accounts.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)


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
                'task_type': 'rag_processing',
                'status': 'running',
                'progress': 0
            }
        )
        if not created:
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
        
        # Semantic chunking
        chunker = SemanticChunker()
        chunks = chunker.chunk_by_paragraphs(content, max_chunk_size=1000, overlap=200)
        
        logger.info(f'Created {len(chunks)} chunks for document {document.file_name}')
        
        task_status.progress = 30
        task_status.metadata = {'stage': 'generating_contexts', 'total_chunks': len(chunks)}
        task_status.save()
        
        # Generate contexts for each chunk
        context_generator = ContextGenerator()
        chunk_contexts = []
        
        for i, chunk_text in enumerate(chunks):
            position = 'beginning' if i == 0 else ('end' if i == len(chunks)-1 else 'middle')
            
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
        text, _ = parse_document(file_path, doc.file_name)
        
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
