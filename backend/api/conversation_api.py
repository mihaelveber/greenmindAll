from ninja import Router, Schema
from ninja.responses import Response
from django.http import JsonResponse
from asgiref.sync import sync_to_async
from typing import List, Dict, Any, Optional
import logging
import time

from accounts.models import (
    ESRSUserResponse, ESRSDisclosure, User, Document, DocumentEvidence,
    ConversationThread, ConversationMessage
)
from accounts.vector_models import DocumentChunk
from accounts.openai_service import OpenAIService
from accounts.token_tracking import track_openai_usage
from accounts.rag_tier_engine import run_tier3_refinement
from .api import JWTAuth, MessageSchema
from .team_api import get_organization_owner

logger = logging.getLogger(__name__)
router = Router()


# Schemas for conversation API
class SendMessageSchema(Schema):
    message: str
    temperature: Optional[float] = 0.2


class RegenerateMessageSchema(Schema):
    temperature: Optional[float] = 0.2


class AIExplainSchema(Schema):
    question: str


class ImageGenerateSchema(Schema):
    prompt: str


@router.post("/esrs/conversation/start/{disclosure_id}", response=dict, auth=JWTAuth())
async def start_conversation(request, disclosure_id: int):
    """
    Start a new conversation thread for a disclosure
    Returns thread_id and initial context
    """
    try:
        disclosure = await sync_to_async(ESRSDisclosure.objects.get)(id=disclosure_id)
        
        # Get or create active thread for this user+disclosure
        thread, created = await sync_to_async(
            lambda: ConversationThread.objects.get_or_create(
                user=request.auth,
                disclosure=disclosure,
                is_active=True,
                defaults={'title': f"Conversation about {disclosure.code}"}
            )
        )()
        
        # Get existing messages
        messages = await sync_to_async(
            lambda: list(thread.messages.all().values(
                'id', 'role', 'content', 'temperature', 'confidence_score',
                'created_at', 'chart_data', 'table_data', 'image_data'
            ))
        )()
        
        # Get linked documents for context
        evidence_docs = await sync_to_async(
            lambda: list(DocumentEvidence.objects.filter(
                disclosure=disclosure,
                user=request.auth,
                is_excluded=False
            ).select_related('document').values(
                'document__id', 'document__file_name', 'document__is_global'
            ))
        )()
        
        return {
            "thread_id": thread.id,
            "disclosure_code": disclosure.code,
            "disclosure_name": disclosure.name,
            "messages": messages,
            "documents": evidence_docs,
            "created": created
        }
        
    except Exception as e:
        logger.error(f"Error starting conversation: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


@router.post("/esrs/conversation/message/{thread_id}", response=dict, auth=JWTAuth())
async def send_message(request, thread_id: int, data: SendMessageSchema):
    """
    Send a message in conversation thread
    Generates AI response with full context (previous messages + documents)
    """
    try:
        user_message = data.message
        temperature = data.temperature
        
        if not user_message:
            return JsonResponse({"error": "Message is required"}, status=400)
        
        # Get thread
        thread = await sync_to_async(
            lambda: ConversationThread.objects.select_related('disclosure', 'user').get(
                id=thread_id, user=request.auth
            )
        )()
        
        # Save user message
        user_msg = await sync_to_async(
            lambda: ConversationMessage.objects.create(
                thread=thread,
                role='user',
                content=user_message
            )
        )()
        
        # Get all previous messages for context
        previous_messages = await sync_to_async(
            lambda: list(thread.messages.order_by('created_at').values('role', 'content'))
        )()
        
        # Get ALL user documents (global + linked to this disclosure)
        from accounts.models import Document
        
        all_user_docs = await sync_to_async(
            lambda: list(Document.objects.filter(user=request.auth))
        )()
        
        print(f"DEBUG: User {request.auth.email} has {len(all_user_docs)} documents")
        for doc in all_user_docs:
            print(f"DEBUG:   - {doc.file_name} (id={doc.id}, is_global={doc.is_global})")
        
        # Build context for AI using TIER 1 + TIER 2 RAG enhancements
        document_context = ""
        doc_ids = [doc.id for doc in all_user_docs]
        processing_steps = []  # Track processing for UI display
        
        # Get user's RAG tier settings
        user = request.auth
        tier1_enabled = user.rag_tier1_enabled
        tier2_enabled = user.rag_tier2_enabled
        tier2_threshold = user.rag_tier2_threshold
        
        if doc_ids:
            query_variations = [user_message]  # Always include original query
            
            # TIER 2: Multi-Query - Generate query variations (if enabled)
            if tier2_enabled:
                from accounts.embedding_service import EmbeddingService
                from rank_bm25 import BM25Okapi
                
                processing_steps.append({
                    "step": "multi_query",
                    "status": "in_progress",
                    "message": "Generating query variations..."
                })
                
                openai_service = OpenAIService()
                multi_query_prompt = f"""Generate 2 alternative phrasings of this question for better document retrieval:
"{user_message}"

Focus on:
1. Using different ESRS terminology
2. Expanding acronyms
3. Adding relevant context

Return only the questions, one per line, without numbering or explanations."""

                start_time = time.time()
                multi_query_response = await sync_to_async(
                    lambda: openai_service.client.chat.completions.create(
                        model="gpt-4o-2024-08-06",
                        messages=[{"role": "user", "content": multi_query_prompt}],
                        temperature=0.3,
                        max_tokens=150
                    )
                )()
                duration_ms = int((time.time() - start_time) * 1000)
                
                # Track token usage for multi-query generation
                org_owner = await sync_to_async(get_organization_owner)(user)
                await sync_to_async(track_openai_usage)(
                    user_id=user.id,
                    organization_id=org_owner.id if org_owner else user.id,
                    action_type='conversation',
                    model='gpt-4o-2024-08-06',
                    prompt_tokens=multi_query_response.usage.prompt_tokens,
                    completion_tokens=multi_query_response.usage.completion_tokens,
                    request_duration_ms=duration_ms,
                    metadata={'step': 'multi_query_generation'}
                )
                
                generated_queries = multi_query_response.choices[0].message.content.strip().split('\n')
                query_variations.extend([q.strip() for q in generated_queries if q.strip()])
                
                logger.info(f"TIER 2 enabled - Generated {len(query_variations)} query variations: {query_variations}")
                
                processing_steps[-1]["status"] = "completed"
                processing_steps[-1]["result"] = f"{len(query_variations)} queries"
            else:
                logger.info(f"TIER 2 disabled - using single query only")
            
            # Get all chunks from user documents
            if tier1_enabled or tier2_enabled:
                from accounts.embedding_service import EmbeddingService
                from rank_bm25 import BM25Okapi
            
            all_chunks = await sync_to_async(
                lambda: list(DocumentChunk.objects.filter(
                    document_id__in=doc_ids
                ).select_related('document').order_by('document_id', 'chunk_index'))
            )()
            
            logger.info(f"Found {len(all_chunks)} total chunks from {len(doc_ids)} documents")
            print(f"DEBUG: Found {len(all_chunks)} total chunks from {len(doc_ids)} documents")
            
            # Build document lookup to avoid lazy loading in async context
            doc_lookup = {}
            for chunk in all_chunks:
                if chunk.document_id not in doc_lookup:
                    doc_lookup[chunk.document_id] = {
                        'id': chunk.document_id,
                        'file_name': chunk.document.file_name
                    }
            
            if all_chunks:
                # TIER 1: Hybrid BM25 + Embeddings for EACH query variation
                if tier1_enabled:
                    processing_steps.append({
                        "step": "hybrid_search",
                        "status": "in_progress",
                        "message": "Running hybrid BM25+Embeddings search..."
                    })
                    logger.info(f"TIER 1 enabled - using hybrid BM25+Embeddings")
                else:
                    processing_steps.append({
                        "step": "semantic_search",
                        "status": "in_progress",
                        "message": "Running semantic search..."
                    })
                    logger.info(f"TIER 1 disabled - using pure semantic search")
                
                all_scored_chunks = []  # Collect scores from all queries
                embedding_service = EmbeddingService()
                
                for query_idx, query in enumerate(query_variations):
                    logger.info(f"Processing query {query_idx + 1}/{len(query_variations)}: {query}")
                    
                    if tier1_enabled:
                        # 1. BM25 Keyword Search
                        chunk_texts = [chunk.content for chunk in all_chunks]
                        tokenized_corpus = [text.lower().split() for text in chunk_texts]
                        bm25 = BM25Okapi(tokenized_corpus)
                        tokenized_query = query.lower().split()
                        bm25_scores = bm25.get_scores(tokenized_query)
                        
                        # Normalize BM25 scores to 0-1 range
                    max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1
                    bm25_scores_norm = [score / max_bm25 for score in bm25_scores]
                    
                    # 2. Semantic Embedding Search
                    query_embedding = await sync_to_async(
                        lambda q=query: embedding_service.embed_text(q)
                    )()
                    
                    semantic_scores = []
                    if query_embedding:
                        for chunk in all_chunks:
                            if chunk.embedding is not None:
                                similarity = embedding_service.cosine_similarity(query_embedding, chunk.embedding)
                                semantic_scores.append(similarity)
                            else:
                                semantic_scores.append(0.0)
                    else:
                        semantic_scores = [0.0] * len(all_chunks)
                    
                    # 3. Hybrid Score or Pure Semantic
                    if tier1_enabled:
                        # Hybrid: 60% semantic + 40% BM25
                        for i in range(len(all_chunks)):
                            hybrid_score = (0.6 * semantic_scores[i]) + (0.4 * bm25_scores_norm[i])
                            all_scored_chunks.append((all_chunks[i], hybrid_score, semantic_scores[i], bm25_scores_norm[i]))
                    else:
                        # Pure semantic
                        for i in range(len(all_chunks)):
                            all_scored_chunks.append((all_chunks[i], semantic_scores[i], semantic_scores[i], 0.0))
                
                # Deduplicate and average scores for chunks that appear multiple times
                chunk_score_map = {}
                for chunk, hybrid, semantic, bm25 in all_scored_chunks:
                    if chunk.id not in chunk_score_map:
                        chunk_score_map[chunk.id] = {
                            'chunk': chunk,
                            'hybrid_scores': [],
                            'semantic_scores': [],
                            'bm25_scores': []
                        }
                    chunk_score_map[chunk.id]['hybrid_scores'].append(hybrid)
                    chunk_score_map[chunk.id]['semantic_scores'].append(semantic)
                    chunk_score_map[chunk.id]['bm25_scores'].append(bm25)
                
                # Average scores for each chunk
                averaged_chunks = []
                for chunk_id, data in chunk_score_map.items():
                    avg_hybrid = sum(data['hybrid_scores']) / len(data['hybrid_scores'])
                    avg_semantic = sum(data['semantic_scores']) / len(data['semantic_scores'])
                    avg_bm25 = sum(data['bm25_scores']) / len(data['bm25_scores'])
                    averaged_chunks.append((data['chunk'], avg_hybrid, avg_semantic, avg_bm25))
                
                # Sort by hybrid score and take top 10
                averaged_chunks.sort(key=lambda x: x[1], reverse=True)
                top_chunks = averaged_chunks[:10]
                
                # Calculate average confidence of top chunks
                avg_confidence = sum(score[1] for score in top_chunks) / len(top_chunks) if top_chunks else 0
                
                logger.info(f"Top 10 chunks selected, avg confidence: {avg_confidence:.2%}")
                
                processing_steps[-1]["status"] = "completed"
                processing_steps[-1]["result"] = f"Top 10 chunks, {avg_confidence:.1%} confidence"
                
                # TIER 2: Document Expansion - Include neighboring chunks (if enabled and low confidence)
                expanded_chunks = list(top_chunks)  # Start with top chunks as tuples (chunk, hybrid, semantic, bm25)
                
                if tier2_enabled and avg_confidence < tier2_threshold:
                    processing_steps.append({
                        "step": "document_expansion",
                        "status": "in_progress",
                        "message": f"Low confidence ({avg_confidence:.1%}) - expanding with neighboring chunks..."
                    })
                    logger.info(f"TIER 2 expansion triggered - confidence {avg_confidence:.2%} < threshold {tier2_threshold}")
                    
                    # Convert to format with chunk_type
                    expanded_chunks = []
                    chunk_lookup = {chunk.id: chunk for chunk in all_chunks}
                    
                    for chunk, hybrid_score, semantic_score, bm25_score in top_chunks:
                        # Add the main chunk
                        expanded_chunks.append((chunk, hybrid_score, semantic_score, bm25_score, 'main'))
                        
                        # Find neighbors (same document, adjacent chunk_index)
                        neighbors = await sync_to_async(
                            lambda c=chunk: list(DocumentChunk.objects.filter(
                                document_id=c.document_id,
                                chunk_index__in=[c.chunk_index - 1, c.chunk_index + 1]
                            ))
                        )()
                        
                        for neighbor in neighbors:
                            # Add neighbor with slightly reduced score
                            expanded_chunks.append((
                                neighbor,
                                hybrid_score * 0.7,  # Reduced confidence for neighbors
                                semantic_score * 0.7,
                                bm25_score * 0.7,
                                'neighbor'
                            ))
                    
                    logger.info(f"Expanded to {len(expanded_chunks)} chunks (including neighbors)")
                    
                    processing_steps[-1]["status"] = "completed"
                    processing_steps[-1]["result"] = f"{len(expanded_chunks)} total chunks"
                else:
                    # No expansion - convert top_chunks to expanded format with 'main' marker
                    expanded_chunks = [(chunk, hybrid, sem, bm25, 'main') for chunk, hybrid, sem, bm25 in top_chunks]
                    if tier2_enabled:
                        logger.info(f"TIER 2 expansion skipped - confidence {avg_confidence:.2%} >= threshold {tier2_threshold}")
                    else:
                        logger.info(f"TIER 2 disabled - no expansion")
                
                # Build context from expanded chunks (in document order for coherence)
                processing_steps.append({
                    "step": "context_building",
                    "status": "in_progress",
                    "message": "Building context..."
                })
                
                # Group by document and sort by chunk index
                doc_chunks = {}
                for chunk, hybrid_score, semantic_score, bm25_score, chunk_type in expanded_chunks:
                    doc_id = chunk.document_id  # Use document_id to avoid lazy loading
                    if doc_id not in doc_chunks:
                        doc_chunks[doc_id] = {
                            'document_name': doc_lookup[doc_id]['file_name'],  # Use pre-loaded lookup
                            'chunks': []
                        }
                    doc_chunks[doc_id]['chunks'].append((chunk, hybrid_score, semantic_score, bm25_score, chunk_type))
                
                # Build context with document structure
                for doc_id, data in doc_chunks.items():
                    doc_name = data['document_name']
                    chunks = sorted(data['chunks'], key=lambda x: x[0].chunk_index)
                    
                    # Find highest score for this document
                    max_score = max(c[1] for c in chunks)
                    
                    document_context += f"\n\n=== {doc_name} (max relevance: {max_score:.2%}) ==="
                    
                    for chunk, hybrid_score, semantic_score, bm25_score, chunk_type in chunks:
                        marker = "⭐" if chunk_type == "main" else "↔️"
                        document_context += f"\n{marker} {chunk.content}"
                
                logger.info(f"Built document_context with {len(document_context)} characters from {len(doc_chunks)} documents")
                print(f"DEBUG: Built document_context with {len(document_context)} chars from {len(doc_chunks)} documents")
                
                processing_steps[-1]["status"] = "completed"
                processing_steps[-1]["result"] = f"{len(doc_chunks)} documents"
            else:
                # Fallback: no chunks available
                logger.warning("No document chunks found for context")
                print("DEBUG: No document chunks found for context!")
                avg_confidence = 0
        
        # Log what's being sent to AI
        logger.info(f"document_context length: {len(document_context)} chars")
        logger.info(f"First 500 chars of document_context: {document_context[:500] if document_context else 'EMPTY'}")
        print(f"DEBUG: document_context length: {len(document_context)} chars")
        print(f"DEBUG: First 1000 chars of document_context: {document_context[:1000] if document_context else 'EMPTY'}")
        
        # Build conversation history
        conversation_history = []
        for msg in previous_messages[:-1]:  # Exclude the message we just added
            conversation_history.append({
                "role": msg['role'],
                "content": msg['content']
            })
        
        # Generate AI response
        openai_service = OpenAIService()
        system_prompt = f"""You are an expert ESRS (European Sustainability Reporting Standards) consultant.
        
Disclosure: {thread.disclosure.code} - {thread.disclosure.name}
Requirement: {thread.disclosure.requirement_text}

COMPANY DOCUMENTS WITH ACTUAL DATA:
{document_context}

CRITICAL INSTRUCTIONS:
1. If the documents above DO NOT contain sufficient information to answer the user's question, you MUST respond with:
   "⚠️ INSUFFICIENT INFORMATION: The available documents do not contain the information needed to answer your question. Please upload relevant documents or provide additional context."
2. DO NOT make up, assume, or provide generic answers when documents lack specific information
3. ONLY use information explicitly present in the documents above
4. The documents contain REAL company data including numerical values, percentages, and statistics
5. When you see data like "value | 0.267 | 0.26 | 0.25" these are actual metrics for years 2021, 2022, 2023
6. ALWAYS cite exact numbers from the documents in your response
7. Format numerical data clearly in tables or bullet points
8. If the user asks for specific metrics, search the document content above carefully for those exact values"""
        
        # Call OpenAI API
        messages_for_api = [{"role": "system", "content": system_prompt}]
        messages_for_api.extend(conversation_history)
        messages_for_api.append({"role": "user", "content": user_message})
        
        processing_steps.append({
            "step": "ai_generation",
            "status": "in_progress",
            "message": "Generating AI response..."
        })
        
        start_time = time.time()
        response = await sync_to_async(
            lambda: openai_service.client.chat.completions.create(
                model="gpt-4o-2024-08-06",
                messages=messages_for_api,
                temperature=temperature,
                max_tokens=4000
            )
        )()
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Track token usage for main conversation response
        org_owner = await sync_to_async(get_organization_owner)(user)
        await sync_to_async(track_openai_usage)(
            user_id=user.id,
            organization_id=org_owner.id if org_owner else user.id,
            action_type='conversation',
            model='gpt-4o-2024-08-06',
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            disclosure_id=thread.disclosure.id,
            request_duration_ms=duration_ms,
            metadata={'step': 'main_response', 'thread_id': thread.id}
        )
        
        ai_answer = response.choices[0].message.content
        
        processing_steps[-1]["status"] = "completed"
        processing_steps[-1]["result"] = f"{avg_confidence:.1%} confidence"
        
        # TIER 3: LLM Self-Reflection + Reranking (always executed when enabled)
        tier3_enabled = user.rag_tier3_enabled
        if tier3_enabled and doc_ids and 'expanded_chunks' in locals():
            processing_steps.append({
                "step": "tier3_start",
                "status": "in_progress",
                "message": "Starting TIER 3: LLM Self-Reflection..."
            })
            
            from accounts.rag_tier_engine import run_tier3_refinement
            
            # Run TIER 3 refinement
            refined_answer, new_confidence, processing_steps = await sync_to_async(
                lambda: run_tier3_refinement(
                    user=user,
                    query_text=user_message,
                    context=document_context,
                    initial_answer=ai_answer,
                    confidence=avg_confidence,
                    expanded_chunks=expanded_chunks,
                    processing_steps=processing_steps
                )
            )()
            
            ai_answer = refined_answer
            avg_confidence = new_confidence
            print(f"DEBUG: TIER 3 complete - new confidence: {avg_confidence:.2%}")
        else:
            if not tier3_enabled:
                print("DEBUG: TIER 3 disabled")
            else:
                print("DEBUG: TIER 3 skipped - no documents or chunks")
        
        # TIER 1: Smart Retry if confidence < 40%
        if avg_confidence < 0.40:
            processing_steps.append({
                "step": "smart_retry",
                "status": "in_progress",
                "message": f"Low confidence ({avg_confidence:.1%}) - reformulating query..."
            })
            
            logger.warning(f"Low confidence ({avg_confidence:.2%}) - will be handled by multi-query in next iteration")
            # Note: Multi-query already handles this by generating variations upfront
            # No need for additional retry loop
            
            processing_steps[-1]["status"] = "completed"
            processing_steps[-1]["result"] = "Handled by multi-query"
        
        # Use hybrid confidence from retrieval
        confidence = avg_confidence * 100  # Convert to percentage
        
        # Prepare AI sources with chunk details for References button
        ai_sources_data = []
        if 'expanded_chunks' in locals() and expanded_chunks:
            # Use expanded chunks for sources
            for chunk, hybrid_score, semantic_score, bm25_score, chunk_type in expanded_chunks[:10]:  # Top 10 only
                ai_sources_data.append({
                    'document_id': chunk.document_id,  # Use document_id to avoid lazy loading
                    'document_name': doc_lookup[chunk.document_id]['file_name'],  # Use pre-loaded lookup
                    'chunk_id': chunk.id,
                    'chunk_index': chunk.chunk_index,
                    'chunk_text': chunk.content[:500],  # Preview
                    'full_chunk_text': chunk.content,   # Full text
                    'hybrid_score': float(hybrid_score),
                    'semantic_score': float(semantic_score),
                    'bm25_score': float(bm25_score),
                    'chunk_type': chunk_type,  # 'main' or 'neighbor'
                    'page_number': chunk.page_number if hasattr(chunk, 'page_number') else None
                })
        
        # Save AI response
        ai_msg = await sync_to_async(
            lambda: ConversationMessage.objects.create(
                thread=thread,
                role='assistant',
                content=ai_answer,
                temperature=temperature,
                confidence_score=confidence,
                documents_used=[doc.id for doc in all_user_docs],
                chart_data={
                    'ai_sources': ai_sources_data,
                    'processing_steps': processing_steps
                } if ai_sources_data else None
            )
        )()
        
        # Update thread timestamp
        await sync_to_async(thread.save)()
        
        return {
            "message_id": ai_msg.id,
            "content": ai_answer,
            "confidence_score": confidence,
            "temperature": temperature,
            "documents_used": len(all_user_docs),
            "ai_sources": ai_sources_data,
            "processing_steps": processing_steps
        }
        
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return JsonResponse({"error": str(e)}, status=500)


@router.get("/esrs/conversation/{thread_id}/messages", response=dict, auth=JWTAuth())
async def get_conversation_history(request, thread_id: int):
    """
    Get full conversation history for a thread
    """
    try:
        thread = await sync_to_async(
            lambda: ConversationThread.objects.get(id=thread_id, user=request.auth)
        )()
        
        messages = await sync_to_async(
            lambda: list(thread.messages.order_by('created_at').values(
                'id', 'role', 'content', 'temperature', 'confidence_score',
                'created_at', 'chart_data', 'table_data', 'image_data',
                'edited', 'regenerated'
            ))
        )()
        
        return {
            "thread_id": thread.id,
            "messages": messages
        }
        
    except Exception as e:
        logger.error(f"Error getting history: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


@router.post("/esrs/conversation/message/{message_id}/regenerate", response=dict, auth=JWTAuth())
async def regenerate_message(request, message_id: int, data: RegenerateMessageSchema):
    """
    Regenerate an AI response with new temperature
    """
    try:
        temperature = data.temperature
        
        # Get original message
        original_msg = await sync_to_async(
            lambda: ConversationMessage.objects.select_related('thread', 'thread__disclosure').get(
                id=message_id, role='assistant'
            )
        )()
        
        thread = original_msg.thread
        
        # Get conversation history up to this point
        previous_messages = await sync_to_async(
            lambda: list(thread.messages.filter(
                created_at__lt=original_msg.created_at
            ).order_by('created_at').values('role', 'content'))
        )()
        
        # Get the user message that triggered this response
        user_msg = previous_messages[-1] if previous_messages else {"role": "user", "content": "Please help"}
        
        # Get ALL user documents for semantic search
        from accounts.models import Document
        
        all_user_docs = await sync_to_async(
            lambda: list(Document.objects.filter(user=thread.user))
        )()
        
        doc_ids = [doc.id for doc in all_user_docs]
        
        # Build context using HYBRID BM25 + EMBEDDINGS search
        document_context = ""
        avg_confidence = 0
        
        if doc_ids:
            from accounts.embedding_service import EmbeddingService
            from rank_bm25 import BM25Okapi
            
            # Get all chunks
            all_chunks = await sync_to_async(
                lambda: list(DocumentChunk.objects.filter(
                    document_id__in=doc_ids
                ).select_related('document'))
            )()
            
            # Build document lookup to avoid lazy loading in async context
            doc_lookup = {}
            for chunk in all_chunks:
                if chunk.document_id not in doc_lookup:
                    doc_lookup[chunk.document_id] = {
                        'id': chunk.document_id,
                        'file_name': chunk.document.file_name
                    }
            
            if all_chunks:
                user_message = user_msg.get('content', '')
                
                # BM25 search
                chunk_texts = [chunk.content for chunk in all_chunks]
                tokenized_corpus = [text.lower().split() for text in chunk_texts]
                bm25 = BM25Okapi(tokenized_corpus)
                tokenized_query = user_message.lower().split()
                bm25_scores = bm25.get_scores(tokenized_query)
                max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1
                bm25_scores_norm = [score / max_bm25 for score in bm25_scores]
                
                # Semantic search
                embedding_service = EmbeddingService()
                query_embedding = await sync_to_async(
                    lambda: embedding_service.embed_text(user_message)
                )()
                
                semantic_scores = []
                if query_embedding:
                    for chunk in all_chunks:
                        if chunk.embedding is not None:
                            similarity = embedding_service.cosine_similarity(query_embedding, chunk.embedding)
                            semantic_scores.append(similarity)
                        else:
                            semantic_scores.append(0.0)
                else:
                    semantic_scores = [0.0] * len(all_chunks)
                
                # Hybrid scoring
                hybrid_scores = []
                for i in range(len(all_chunks)):
                    hybrid_score = (0.6 * semantic_scores[i]) + (0.4 * bm25_scores_norm[i])
                    hybrid_scores.append((all_chunks[i], hybrid_score, semantic_scores[i], bm25_scores_norm[i]))
                
                hybrid_scores.sort(key=lambda x: x[1], reverse=True)
                top_chunks = hybrid_scores[:10]
                avg_confidence = sum(score[1] for score in top_chunks) / len(top_chunks) if top_chunks else 0
                
                seen_docs = set()
                for chunk, hybrid_score, semantic_score, bm25_score in top_chunks:
                    doc = chunk.document
                    if doc.id not in seen_docs:
                        document_context += f"\n\n=== {doc.file_name} (hybrid: {hybrid_score:.2%}, semantic: {semantic_score:.2%}, keyword: {bm25_score:.2%}) ==="
                        seen_docs.add(doc.id)
                    document_context += f"\n{chunk.content}"
        
        # Generate new response
        openai_service = OpenAIService()
        system_prompt = f"""You are an expert ESRS consultant.

CRITICAL: If the available documents DO NOT contain sufficient information to answer the question, respond with:
"⚠️ INSUFFICIENT INFORMATION: The available documents do not contain the necessary information. Please upload relevant documents."
DO NOT provide generic or assumed answers without document support.
        
Disclosure: {thread.disclosure.code} - {thread.disclosure.name}
Requirement: {thread.disclosure.requirement_text}

Available Documents:
{document_context}"""
        
        messages_for_api = [{"role": "system", "content": system_prompt}]
        messages_for_api.extend(previous_messages[:-1])  # All except the user msg we're about to add
        messages_for_api.append({"role": "user", "content": user_msg['content']})
        
        response = await sync_to_async(
            lambda: openai_service.client.chat.completions.create(
                model="gpt-4o-2024-08-06",
                messages=messages_for_api,
                temperature=temperature,
                max_tokens=4000
            )
        )()
        
        ai_answer = response.choices[0].message.content
        
        # Use hybrid confidence
        confidence = avg_confidence * 100 if avg_confidence > 0 else 60.0
        
        # Prepare AI sources with chunk details
        ai_sources_data = []
        if 'top_chunks' in locals() and top_chunks:
            for chunk, hybrid_score, semantic_score, bm25_score in top_chunks:
                ai_sources_data.append({
                    'document_id': chunk.document_id,  # Use document_id to avoid lazy loading
                    'document_name': doc_lookup[chunk.document_id]['file_name'],  # Use pre-loaded lookup
                    'chunk_id': chunk.id,
                    'chunk_index': chunk.chunk_index,
                    'chunk_text': chunk.content[:500],
                    'full_chunk_text': chunk.content,
                    'hybrid_score': float(hybrid_score),
                    'semantic_score': float(semantic_score),
                    'bm25_score': float(bm25_score),
                    'page_number': chunk.page_number if hasattr(chunk, 'page_number') else None
                })
        
        # Update original message
        original_msg.content = ai_answer
        original_msg.temperature = temperature
        original_msg.confidence_score = confidence
        original_msg.regenerated = True
        original_msg.chart_data = {'ai_sources': ai_sources_data} if ai_sources_data else None
        await sync_to_async(original_msg.save)()
        
        return {
            "message_id": original_msg.id,
            "content": ai_answer,
            "confidence_score": confidence,
            "temperature": temperature,
            "ai_sources": ai_sources_data
        }
        
    except Exception as e:
        logger.error(f"Error regenerating message: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


@router.post("/esrs/extract-charts/{disclosure_id}", response=MessageSchema, auth=JWTAuth())
async def extract_charts(request, disclosure_id: int):
    """
    Extract charts and tables from AI answer using Function Calling
    """
    from accounts.models import ESRSUserResponse, ESRSDisclosure
    
    try:
        # Get disclosure and user response
        disclosure = await sync_to_async(ESRSDisclosure.objects.get)(id=disclosure_id)
        user_response = await sync_to_async(
            lambda: ESRSUserResponse.objects.get(user=request.auth, disclosure=disclosure)
        )()
        
        if not user_response.ai_answer:
            return JsonResponse({"message": "No AI answer found to extract charts from", "success": False}, status=400)
        
        # Extract charts using OpenAI Function Calling
        openai_service = OpenAIService()
        temperature = user_response.ai_temperature or 0.2
        
        analytics = openai_service.extract_charts_from_answer(
            answer_text=user_response.ai_answer,
            disclosure_code=disclosure.code,
            temperature=temperature
        )
        
        # Update user response with extracted data
        if analytics:
            user_response.chart_data = analytics.get('charts')
            user_response.table_data = analytics.get('tables')
            user_response.numeric_data = analytics.get('numeric_data')
            await sync_to_async(user_response.save)()
            
            return {"message": f"Extracted {len(analytics.get('charts', []))} charts and {len(analytics.get('tables', []))} tables", "success": True}
        else:
            return {"message": "No charts or tables found in the answer", "success": False}
            
    except ESRSUserResponse.DoesNotExist:
        return JsonResponse({"message": "Please generate AI answer first", "success": False}, status=404)
    except Exception as e:
        logger.error(f"Error extracting charts: {str(e)}")
        return JsonResponse({"message": f"Error: {str(e)}", "success": False}, status=500)


@router.post("/esrs/generate-image/{disclosure_id}", response=MessageSchema, auth=JWTAuth())
async def generate_image(request, disclosure_id: int, data: ImageGenerateSchema):
    """
    Generate image using DALL-E 3 based on user prompt
    """
    from accounts.models import ESRSUserResponse, ESRSDisclosure
    import openai
    import base64
    import requests
    
    try:
        prompt = data.prompt
        if not prompt:
            return JsonResponse({"message": "Prompt is required", "success": False}, status=400)
        
        disclosure = await sync_to_async(ESRSDisclosure.objects.get)(id=disclosure_id)
        
        # Generate image with DALL-E 3
        openai_service = OpenAIService()
        client = openai_service.client
        
        response = await sync_to_async(
            lambda: client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
        )()
        
        image_url = response.data[0].url
        
        # Download image and convert to base64
        image_response = requests.get(image_url)
        image_base64 = base64.b64encode(image_response.content).decode('utf-8')
        
        # Get or create user response
        user_response, created = await sync_to_async(
            lambda: ESRSUserResponse.objects.get_or_create(
                user=request.auth,
                disclosure=disclosure,
                defaults={'ai_temperature': 0.2}
            )
        )()
        
        # Store image (add to chart_data as special type)
        if not user_response.chart_data:
            user_response.chart_data = []
        
        user_response.chart_data.append({
            'type': 'ai_image',
            'title': 'AI Generated Visualization',
            'prompt': prompt,
            'image_url': image_url,
            'image_base64': image_base64,
            'selected_for_report': True
        })
        
        await sync_to_async(user_response.save)()
        
        return {"message": "Image generated successfully", "success": True}
        
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}")
        return JsonResponse({"message": f"Error: {str(e)}", "success": False}, status=500)


@router.post("/esrs/conversation/message/{message_id}/use-as-answer", response=dict, auth=JWTAuth())
async def use_message_as_answer(request, message_id: int):
    """
    Save conversation message as the final AI answer for the disclosure
    """
    from accounts.models import ESRSUserResponse
    
    try:
        # Get message
        message = await sync_to_async(
            lambda: ConversationMessage.objects.select_related(
                'thread', 'thread__disclosure', 'thread__user'
            ).get(id=message_id, role='assistant')
        )()
        
        thread = message.thread
        
        # Verify user owns this thread
        if thread.user.id != request.auth.id:
            return JsonResponse({"error": "Unauthorized"}, status=403)
        
        # Get or create user response
        user_response = await sync_to_async(
            lambda: ESRSUserResponse.objects.get_or_create(
                user=request.auth,
                disclosure=thread.disclosure
            )[0]
        )()
        
        # Save message content as AI answer ONLY (not final_answer - that's approved section)
        user_response.ai_answer = message.content
        await sync_to_async(user_response.save)()
        
        # === CREATE VERSION FOR CONVERSATION ANSWER ===
        from accounts.models import ItemVersion
        
        # Get latest version number
        latest_version = await sync_to_async(
            lambda: ItemVersion.objects.filter(
                item_type='TEXT',
                item_id=user_response.id,
                user=request.auth
            ).order_by('-version_number').first()
        )()
        
        next_version_number = (latest_version.version_number + 1) if latest_version else 1
        
        # Create new version
        await sync_to_async(ItemVersion.objects.create)(
            item_type='TEXT',
            item_id=user_response.id,
            user=request.auth,
            disclosure=thread.disclosure,
            version_number=next_version_number,
            content={'text': message.content, 'format': 'markdown'},
            change_type='AI_REFINEMENT',
            change_description=f'Saved from conversation: {thread.title}',
            created_by_user=False,  # AI generated in conversation
            is_selected=True,
            parent_version=latest_version
            # Note: conversation field expects AIConversation, not ConversationThread
            # We track the source in change_description instead
        )
        
        # Deselect previous versions
        if latest_version:
            await sync_to_async(
                lambda: ItemVersion.objects.filter(
                    item_type='TEXT',
                    item_id=user_response.id,
                    user=request.auth
                ).exclude(version_number=next_version_number).update(is_selected=False)
            )()
        
        logger.info(f"Saved conversation message {message_id} as answer for disclosure {thread.disclosure.code} (version {next_version_number})")
        
        return {
            "message": "Answer saved successfully",
            "success": True,
            "ai_answer": message.content
        }
        
    except ConversationMessage.DoesNotExist:
        return JsonResponse({"error": "Message not found"}, status=404)
    except Exception as e:
        logger.error(f"Error saving message as answer: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


@router.post("/esrs/ai-explain/{disclosure_id}", response=dict, auth=JWTAuth())
async def ai_explain(request, disclosure_id: int, data: AIExplainSchema):
    """
    AI Explain - Help user understand what to answer in disclosure
    Modal-only display, no save needed
    """
    from accounts.models import ESRSDisclosure, DocumentEvidence
    
    try:
        question = data.question
        if not question:
            return JsonResponse({"error": "Question is required"}, status=400)
        
        disclosure = await sync_to_async(ESRSDisclosure.objects.get)(id=disclosure_id)
        
        # Get linked documents for context
        evidence_docs = await sync_to_async(
            lambda: list(DocumentEvidence.objects.filter(
                disclosure=disclosure,
                user=request.auth,
                is_excluded=False
            ).select_related('document'))
        )()
        
        # Build document context
        document_context = ""
        for evidence in evidence_docs:
            doc = evidence.document
            # Get first few chunks from document
            chunks = await sync_to_async(
                lambda d=doc: list(DocumentChunk.objects.filter(document=d).order_by('chunk_index')[:5])
            )()
            if chunks:
                doc_text = "\n".join([chunk.content for chunk in chunks])
                document_context += f"\n\n=== {doc.file_name} ===\n{doc_text[:3000]}"
        
        # Generate AI explanation
        openai_service = OpenAIService()
        system_prompt = f"""You are an expert ESRS (European Sustainability Reporting Standards) consultant.

CRITICAL: If you DO NOT have sufficient information to provide a complete answer, clearly state:
"⚠️ INSUFFICIENT INFORMATION: I cannot provide a complete answer without [specific documents/data needed]. Please upload relevant documents."
DO NOT provide generic guidance without specific document support.

Your task is to help the user understand what they need to include in their answer for this disclosure.

Disclosure: {disclosure.code} - {disclosure.name}
Requirement: {disclosure.requirement_text}

Available Documents:
{document_context if document_context else "No documents linked to this disclosure yet."}

User's Question: {question}

Provide a clear, helpful explanation that:
1. If no documents are available, explain what specific documents/data are needed
2. If documents are available, explain what information is required for this disclosure
3. Reference specific requirements from ESRS
4. Suggest what to include based on available documents
5. Give practical examples if helpful
6. Use markdown formatting for clarity

Be supportive and educational. This is guidance only - the user will write their actual answer separately."""
        
        response = await sync_to_async(
            lambda: openai_service.client.chat.completions.create(
                model="gpt-4o-2024-08-06",
                messages=[{"role": "user", "content": system_prompt}],
                temperature=0.3,
                max_tokens=2000
            )
        )()
        
        explanation = response.choices[0].message.content
        
        return {
            "explanation": explanation,
            "disclosure_code": disclosure.code,
            "documents_used": len(evidence_docs)
        }
        
    except Exception as e:
        logger.error(f"Error in AI explain: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)
