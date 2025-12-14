from ninja import Router, Schema
from ninja.responses import Response
from django.http import JsonResponse
from asgiref.sync import sync_to_async
from typing import List, Dict, Any, Optional
import logging

from accounts.models import (
    ESRSUserResponse, ESRSDisclosure, User, Document, DocumentEvidence,
    ConversationThread, ConversationMessage
)
from accounts.vector_models import DocumentChunk
from accounts.openai_service import OpenAIService
from .api import JWTAuth, MessageSchema

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
        
        # Build context for AI using RAG semantic search on ALL documents
        document_context = ""
        doc_ids = [doc.id for doc in all_user_docs]
        
        if doc_ids:
            # Use semantic search to find relevant chunks based on user's question
            from accounts.embedding_service import EmbeddingService
            
            # Generate embedding for user's query
            embedding_service = EmbeddingService()
            query_embedding = await sync_to_async(
                lambda: embedding_service.embed_text(user_message)
            )()
            
            logger.info(f"Query embedding generated: {query_embedding is not None}, length: {len(query_embedding) if query_embedding else 0}")
            
            # Get all chunks from linked documents that have embeddings
            all_chunks = await sync_to_async(
                lambda: list(DocumentChunk.objects.filter(
                    document_id__in=doc_ids,
                    embedding__isnull=False
                ).select_related('document'))
            )()
            
            logger.info(f"Found {len(all_chunks)} chunks with embeddings from {len(doc_ids)} documents")
            
            if all_chunks and query_embedding:
                # Calculate cosine similarity for each chunk
                chunk_similarities = []
                for chunk in all_chunks:
                    similarity = embedding_service.cosine_similarity(query_embedding, chunk.embedding)
                    chunk_similarities.append((chunk, similarity))
                
                # Sort by similarity and take top 10
                chunk_similarities.sort(key=lambda x: x[1], reverse=True)
                top_chunks = chunk_similarities[:10]
                
                # Build context from most relevant chunks
                seen_docs = set()
                for chunk, similarity in top_chunks:
                    doc = chunk.document
                    if doc.id not in seen_docs:
                        document_context += f"\n\n=== {doc.file_name} (relevance: {similarity:.2%}) ==="
                        seen_docs.add(doc.id)
                    document_context += f"\n{chunk.content}"
            else:
                # Fallback: no embeddings available, use first chunks from all docs
                for doc in all_user_docs[:5]:  # Limit to first 5 documents
                    chunks = await sync_to_async(
                        lambda d=doc: list(DocumentChunk.objects.filter(document=d).order_by('chunk_index')[:3])
                    )()
                    if chunks:
                        doc_text = "\n".join([chunk.content for chunk in chunks])
                        document_context += f"\n\n=== {doc.file_name} ===\n{doc_text[:2000]}"
        
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

Available Documents:
{document_context}

Provide detailed, accurate answers based on the documents and ESRS requirements.
Include specific citations when referencing documents."""
        
        # Call OpenAI API
        messages_for_api = [{"role": "system", "content": system_prompt}]
        messages_for_api.extend(conversation_history)
        messages_for_api.append({"role": "user", "content": user_message})
        
        response = await sync_to_async(
            lambda: openai_service.client.chat.completions.create(
                model="gpt-4o-2024-08-06",
                messages=messages_for_api,
                temperature=temperature,
                max_tokens=4000
            )
        )()
        
        ai_answer = response.choices[0].message.content
        
        # Calculate simple confidence score based on document usage
        num_docs = len(all_user_docs) if all_user_docs else 0
        confidence = min(95.0, 60.0 + (num_docs * 5))
        
        # Save AI response
        ai_msg = await sync_to_async(
            lambda: ConversationMessage.objects.create(
                thread=thread,
                role='assistant',
                content=ai_answer,
                temperature=temperature,
                confidence_score=confidence,
                documents_used=[doc.id for doc in all_user_docs]
            )
        )()
        
        # Update thread timestamp
        await sync_to_async(thread.save)()
        
        return {
            "message_id": ai_msg.id,
            "content": ai_answer,
            "confidence_score": confidence,
            "temperature": temperature,
            "documents_used": num_docs
        }
        
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
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
        
        # Build context using semantic search
        document_context = ""
        
        if doc_ids:
            from accounts.embedding_service import EmbeddingService
            
            embedding_service = EmbeddingService()
            query_embedding = await sync_to_async(
                lambda: embedding_service.embed_text(user_msg.get('content', ''))
            )()
            
            all_chunks = await sync_to_async(
                lambda: list(DocumentChunk.objects.filter(
                    document_id__in=doc_ids,
                    embedding__isnull=False
                ).select_related('document'))
            )()
            
            if all_chunks and query_embedding:
                chunk_similarities = []
                for chunk in all_chunks:
                    similarity = embedding_service.cosine_similarity(query_embedding, chunk.embedding)
                    chunk_similarities.append((chunk, similarity))
                
                chunk_similarities.sort(key=lambda x: x[1], reverse=True)
                top_chunks = chunk_similarities[:10]
                
                seen_docs = set()
                for chunk, similarity in top_chunks:
                    doc = chunk.document
                    if doc.id not in seen_docs:
                        document_context += f"\n\n=== {doc.file_name} (relevance: {similarity:.2%}) ==="
                        seen_docs.add(doc.id)
                    document_context += f"\n{chunk.content}"
        
        # Generate new response
        openai_service = OpenAIService()
        system_prompt = f"""You are an expert ESRS consultant.
        
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
        
        # Calculate simple confidence based on number of documents found
        num_docs = len(all_user_docs) if all_user_docs else 0
        confidence = min(95.0, 60.0 + (num_docs * 5))
        
        # Update original message
        original_msg.content = ai_answer
        original_msg.temperature = temperature
        original_msg.confidence_score = confidence
        original_msg.regenerated = True
        await sync_to_async(original_msg.save)()
        
        return {
            "message_id": original_msg.id,
            "content": ai_answer,
            "confidence_score": confidence,
            "temperature": temperature
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
        
        logger.info(f"Saved conversation message {message_id} as answer for disclosure {thread.disclosure.code}")
        
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

Your task is to help the user understand what they need to include in their answer for this disclosure.

Disclosure: {disclosure.code} - {disclosure.name}
Requirement: {disclosure.requirement_text}

Available Documents:
{document_context if document_context else "No documents linked to this disclosure yet."}

User's Question: {question}

Provide a clear, helpful explanation that:
1. Explains what information is required for this disclosure
2. References specific requirements from ESRS
3. Suggests what to include based on available documents (if any)
4. Gives practical examples if helpful
5. Uses markdown formatting for clarity

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
