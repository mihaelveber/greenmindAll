from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
import logging
from accounts.token_tracking import OpenAIUsageTracker
import anthropic

logger = logging.getLogger(__name__)

@shared_task
def send_invitation_email_task(email: str, invited_by_name: str, role: str, temp_password: str, token: str, expires_at: str):
    """
    Celery task for sending invitation emails asynchronously
    
    Args:
        email: Recipient email address
        invited_by_name: Name of the person who sent the invitation
        role: Role of the new user (admin/member)
        temp_password: Temporary password
        token: Invitation token
        expires_at: Expiration datetime string
    """
    try:
        accept_url = f"{settings.FRONTEND_URL}/accept-invitation?token={token}"
        subject = f"Invitation to join {invited_by_name}'s team"
        message = f"""
Hello,

You have been invited to join {invited_by_name}'s organization as a {role}.

Your temporary credentials:
Email: {email}
Password: {temp_password}

Please visit the following link to accept the invitation and set your permanent password:
{accept_url}

This invitation will expire on {expires_at}.

Best regards,
Greenmind AI Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        logger.info(f'Invitation email sent to {email}')
        return True
    except Exception as e:
        logger.error(f'Failed to send invitation email to {email}: {str(e)}')
        return False


@shared_task
def send_welcome_email(user_email: str, user_name: str):
    """Async task za pošiljanje pozdravnega emaila"""
    try:
        send_mail(
            subject='Dobrodošli!',
            message=f'Pozdravljeni {user_name}, dobrodošli v naši aplikaciji!',
            from_email='noreply@example.com',
            recipient_list=[user_email],
            fail_silently=False,
        )
        logger.info(f'Welcome email sent to {user_email}')
        return True
    except Exception as e:
        logger.error(f'Failed to send email to {user_email}: {str(e)}')
        return False

@shared_task
def cleanup_inactive_users():
    """Async task za čiščenje neaktivnih uporabnikov"""
    from datetime import timedelta
    from django.utils import timezone
    from accounts.models import User
    
    threshold = timezone.now() - timedelta(days=365)
    inactive_users = User.objects.filter(
        last_login__lt=threshold,
        is_active=True
    )
    
    count = inactive_users.count()
    inactive_users.update(is_active=False)
    
    logger.info(f'Deactivated {count} inactive users')
    return count


@shared_task(bind=True)
def generate_ai_answer_task(self, disclosure_id: int, user_id: int, ai_temperature: float = 0.2, model_id: str = 'gpt-4o'):
    """
    Celery task za generiranje AI odgovora za eno disclosure točko
    Uses OpenAI Responses API with file_search tool for unlimited document size
    Supports multiple LLM providers: OpenAI, Anthropic, Google
    """
    from accounts.models import ESRSUserResponse, ESRSDisclosure, DocumentEvidence, Document, User, AITaskStatus
    from accounts.llm_router import LLMRouter
    from django.conf import settings
    import openai
    
    task_id = self.request.id

    # Helper function to update task status only if it exists
    def update_status(**kwargs):
        if task_status:
            for key, value in kwargs.items():
                setattr(task_status, key, value)
            task_status.save()

    try:
        # Update task status to running (if it exists - may not exist when called from bulk task)
        task_status = None
        try:
            task_status = AITaskStatus.objects.get(task_id=task_id)
            task_status.status = 'running'
            task_status.progress = 10
            task_status.save()
        except AITaskStatus.DoesNotExist:
            # Task called from bulk operation, no individual status tracking needed
            pass
        
        # Get user and disclosure
        user = User.objects.get(id=user_id)
        disclosure = ESRSDisclosure.objects.select_related('standard').get(id=disclosure_id)
        
        logger.info(f'Generating AI answer for {disclosure.code} (user: {user.email}) using model: {model_id}')
        
        # Get user response data
        user_notes = ""
        manual_answer = ""
        try:
            user_response = ESRSUserResponse.objects.get(user=user, disclosure=disclosure)
            user_notes = user_response.notes or ""
            manual_answer = user_response.manual_answer or ""
            # Note: ai_temperature is passed as task parameter from UI
        except ESRSUserResponse.DoesNotExist:
            pass
        
        update_status(progress=30, current_step="🔗 Auto-linking global documents...")
        
        # Auto-link global documents if not excluded
        global_documents = Document.objects.filter(user=user, is_global=True)
        global_doc_count = global_documents.count()
        for global_doc in global_documents:
            evidence, created = DocumentEvidence.objects.get_or_create(
                document=global_doc,
                disclosure=disclosure,
                user=user,
                is_excluded=False,  # Part of lookup - will not re-activate excluded docs
                defaults={'notes': 'Auto-linked global document'}
            )
        
        logger.info(f'Auto-linked {global_doc_count} global documents to {disclosure.code}')
        
        # Get linked documents with evidence notes (excluding explicitly excluded global docs)
        evidence_list = list(
            DocumentEvidence.objects.filter(
                disclosure=disclosure,
                user=user,
                is_excluded=False  # Filter out excluded global documents
            ).select_related('document')
        )
        
        update_status(progress=50, current_step=f"📚 Analyzing {len(evidence_list)} linked documents...", documents_used=len(evidence_list))
        
        # Check if we have RAG chunks available for semantic search
        from accounts.models import DocumentChunk
        
        has_rag_chunks = DocumentChunk.objects.filter(document__user=user).exists()
        
        if has_rag_chunks:
            # Use custom AI prompt if set, otherwise use requirement_text
            disclosure_requirement = disclosure.ai_prompt if disclosure.ai_prompt else disclosure.requirement_text
            
            # Build context about linked documents
            linked_docs_context = ""
            if evidence_list:
                linked_docs_context = "\n\n📎 DOCUMENTS LINKED TO THIS DISCLOSURE:\n"
                for ev in evidence_list:
                    linked_docs_context += f"- {ev.document.file_name}"
                    if ev.notes:
                        linked_docs_context += f" (Notes: {ev.notes})"
                    linked_docs_context += "\n"
            
            # Prepare Responses API prompt
            prompt = f"""📋 DISCLOSURE REQUIREMENT:
Standard: {disclosure.standard.code} - {disclosure.standard.name}
Disclosure: {disclosure.code} - {disclosure.name}

Description: {disclosure.description}

Requirement: {disclosure_requirement}
{linked_docs_context}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 USER'S EXISTING ANSWER (if any):
{manual_answer if manual_answer else "No manual answer provided yet."}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 USER'S NOTES:
{user_notes if user_notes else "No notes provided yet."}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

YOUR TASK:
Write a complete, professional answer for this disclosure requirement using the company documents provided below.
- Include all relevant data, statistics, and information from the documents
- Structure your answer appropriately for this type of disclosure
- If certain required information is not available, note what is missing"""

            update_status(progress=70)

            # Get relevant documents for RAG search
            global_docs = Document.objects.filter(user=user, is_global=True)
            linked_doc_ids = [evidence.document_id for evidence in evidence_list]
            specific_docs = Document.objects.filter(id__in=linked_doc_ids)
            
            # Combine and get unique document IDs
            relevant_doc_ids = list(set(
                list(global_docs.values_list('id', flat=True)) +
                list(specific_docs.values_list('id', flat=True))
            ))
            
            logger.info(f'Using RAG search on {len(relevant_doc_ids)} documents: {len(global_docs)} global + {len(specific_docs)} specific')
            
            update_status(current_step=f"🔍 Running TIER 1+2 RAG search on {len(relevant_doc_ids)} documents...")
            
            # Use unified TIER 1+2 RAG engine
            from accounts.rag_tier_engine import run_tier_rag
            
            query_text = f"{disclosure.code} {disclosure.name} {disclosure_requirement}"
            
            # Run TIER 1+2 RAG with user's settings
            rag_context, expanded_chunks, avg_confidence, processing_steps = run_tier_rag(
                user=user,
                query_text=query_text,
                relevant_doc_ids=relevant_doc_ids,
                temperature=ai_temperature
            )
            
            logger.info(f'TIER RAG complete: {len(expanded_chunks)} chunks, {avg_confidence:.2%} confidence, context={len(rag_context)} chars')
            
            # Update task status with processing steps
            update_status(
                current_step=f"📊 TIER RAG complete: {len(expanded_chunks)} chunks analyzed...",
                chunks_used=len(expanded_chunks),
                processing_steps=processing_steps
            )
            
            # Build cited documents list from expanded_chunks
            cited_documents = []
            seen_docs = set()
            
            for idx, (chunk, hybrid_score, semantic_score, bm25_score, chunk_type) in enumerate(expanded_chunks):
                doc = chunk.document
                
                cited_documents.append({
                    'id': doc.id,
                    'file_name': doc.file_name,
                    'file_type': doc.file_type,
                    'chunk_text': chunk.content[:500],
                    'full_chunk_text': chunk.content,
                    'chunk_index': chunk.chunk_index,
                    'relevance_score': hybrid_score,  # Real hybrid score from TIER 1
                    'uploaded_at': doc.uploaded_at.isoformat(),
                    'chunk_type': chunk_type  # 'main' or 'neighbor' from TIER 2
                })
                seen_docs.add(doc.id)
            
            # Add RAG context to prompt with clear header
            full_prompt = prompt + f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 COMPANY DOCUMENTS - EXTRACT DATA FROM HERE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{rag_context}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Remember: Your answer MUST include specific numbers and statistics from the documents above!
If the documents contain data like percentages (e.g., 0.70 = 70%), present them clearly.
"""
            
            logger.info(f'Built TIER RAG context with {len(rag_context)} characters from {len(cited_documents)} chunks')
            
            update_status(
                current_step=f"🤖 Generating AI response using GPT-4o with context from {len(cited_documents)} sections...",
                progress=80
            )
            
            # Call OpenAI Chat Completions API with RAG context + track token usage
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            
            # Get organization owner for billing (team members bill to their admin)
            if hasattr(user, 'team_role') and user.team_role:
                org_owner = user.team_role.organization
            else:
                org_owner = user  # User is organization owner
            
            # Check if using OpenAI o1 reasoning models (gpt-5, gpt-5-mini, gpt-5-nano)
            is_o1_model = model_id in ['gpt-5', 'gpt-5-mini', 'gpt-5-nano']
            
            # Check if using Claude models with Extended Thinking support
            is_claude_model = model_id.startswith('claude-') if model_id else False
            supports_extended_thinking = is_claude_model and model_id in [
                'claude-sonnet-3-7', 'claude-sonnet-4', 'claude-sonnet-4-5',
                'claude-haiku-4-5', 'claude-opus-4', 'claude-opus-4-1', 'claude-opus-4-5'
            ]
            
            reasoning_summary = None
            
            # System message for all models - GENERIC for all disclosure types
            esrs_system_message = """You are an expert sustainability report writer helping to answer ESRS disclosure requirements.

CRITICAL RULES:
1. ONLY use information from the provided documents
2. If documents lack sufficient information, respond: "⚠️ INSUFFICIENT INFORMATION: Cannot answer without [specific data needed]. Please upload relevant documents."
3. NEVER provide generic or assumed answers

WHEN SUFFICIENT INFORMATION EXISTS:
- Extract actual data, numbers, facts from documents
- Write as if writing the actual report section
- Include specific numbers, percentages, dates
- Structure clearly with sections/tables/bullets
- Be comprehensive

Write professional answers using document data. State "INSUFFICIENT INFORMATION" if needed."""
            
            with OpenAIUsageTracker(user.id, org_owner.id, 'ai_answer', disclosure.id) as tracker:
                if is_o1_model:
                    # Use OpenAI Chat Completions API for o1/o3 models
                    # Note: o1 models don't support system messages or temperature
                    # Map gpt-5 names to actual OpenAI model names
                    o1_model_map = {
                        'gpt-5': 'o1',
                        'gpt-5-mini': 'o1-mini', 
                        'gpt-5-nano': 'o3-mini'
                    }
                    actual_model = o1_model_map.get(model_id, model_id)
                    
                    # Combine system message into user message for o1 models
                    combined_prompt = f"{esrs_system_message}\n\n---\n\n{full_prompt}"
                    
                    response = client.chat.completions.create(
                        model=actual_model,
                        messages=[{"role": "user", "content": combined_prompt}],
                        max_completion_tokens=4096
                    )
                    
                    ai_answer = response.choices[0].message.content
                    reasoning_summary = None  # o1 models don't expose reasoning in standard API
                    
                    tracker.record(response, model=actual_model)
                elif is_claude_model:
                    # Use Anthropic Messages API for Claude models
                    anthropic_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
                    
                    # Map frontend model names to actual Anthropic API model names
                    claude_model_map = {
                        'claude-sonnet-3-7': 'claude-sonnet-4-20250514',  # Claude Sonnet 4 (latest)
                        'claude-sonnet-4': 'claude-sonnet-4-20250514',
                        'claude-sonnet-4-5': 'claude-sonnet-4-5-20250514',
                        'claude-haiku-4-5': 'claude-haiku-4-5-20250514',
                        'claude-opus-4': 'claude-opus-4-20250514',
                        'claude-opus-4-1': 'claude-opus-4-20250514',
                        'claude-opus-4-5': 'claude-opus-4-20250514',
                    }
                    actual_model = claude_model_map.get(model_id, model_id)
                    logger.info(f'Claude model mapping: {model_id} -> {actual_model}')
                    
                    # Prepare request parameters - use same system message
                    request_params = {
                        "model": actual_model,
                        "max_tokens": 4096,
                        "system": esrs_system_message,  # Use unified system message
                        "messages": [{"role": "user", "content": full_prompt}],
                    }
                    
                    # Add Extended Thinking for supported models
                    if supports_extended_thinking:
                        request_params["thinking"] = {
                            "type": "enabled",
                            "budget_tokens": 2000  # Allow 2000 tokens for thinking
                        }
                        # Extended thinking requires temperature=1
                        request_params["temperature"] = 1
                        logger.info(f'Enabled Extended Thinking for {actual_model} with 2000 token budget (temperature=1 required)')
                    else:
                        # Only set temperature for non-thinking models
                        request_params["temperature"] = ai_temperature
                    
                    response = anthropic_client.messages.create(**request_params)
                    
                    # Extract thinking content from response (Claude Extended Thinking)
                    for content_block in response.content:
                        if content_block.type == 'thinking':
                            # Extended Thinking returns thinking content directly
                            reasoning_summary = getattr(content_block, 'thinking', None)
                            if reasoning_summary:
                                logger.info(f'Extracted Claude thinking: {len(reasoning_summary)} chars')
                            break
                    
                    # Extract answer from text content
                    ai_answer = ""
                    for content_block in response.content:
                        if content_block.type == 'text':
                            ai_answer += content_block.text
                    
                    # Track usage (adapt to Anthropic response format)
                    # Note: Anthropic uses different usage format - will need to adapt tracker
                    logger.info(f'Claude response: input_tokens={response.usage.input_tokens}, output_tokens={response.usage.output_tokens}')
                else:
                    # Use Chat Completions API for non-o1 models (GPT-4o, etc.)
                    response = client.chat.completions.create(
                        model=model_id if model_id else "gpt-4o",
                        messages=[
                            {"role": "system", "content": esrs_system_message},
                            {"role": "user", "content": full_prompt}
                        ],
                        max_tokens=2000,
                        temperature=ai_temperature
                    )
                    ai_answer = response.choices[0].message.content
                    tracker.record(response, model=model_id if model_id else "gpt-4o")
            
            # Store reasoning summary if available
            if reasoning_summary:
                update_status(reasoning_summary=reasoning_summary)
            
            if not ai_answer:
                raise ValueError('No answer generated by OpenAI')
            
            logger.info(f'Generated AI answer using RAG: {len(ai_answer)} characters')
            
            # TIER 3: LLM Self-Reflection + Reranking (if confidence < 85%)
            update_status(current_step=f"🔬 Running TIER 3 refinement (confidence: {avg_confidence:.1%})...")
            
            from accounts.rag_tier_engine import run_tier3_refinement
            
            refined_answer, final_confidence, updated_steps = run_tier3_refinement(
                user=user,
                query_text=query_text,
                context=rag_context,
                initial_answer=ai_answer,
                confidence=avg_confidence,
                expanded_chunks=expanded_chunks,
                processing_steps=processing_steps
            )
            
            # Use refined answer and confidence
            ai_answer = refined_answer
            avg_confidence = final_confidence
            processing_steps = updated_steps
            
            # Update task_status with TIER 3 processing steps
            update_status(processing_steps=processing_steps)
            
            logger.info(f'TIER 3 complete: Final confidence {avg_confidence:.2%}')
        
        else:
            # Generate AI answer WITHOUT file_search for users with old documents (pre-migration)
            logger.info(f'Generating AI answer WITHOUT file_search for {disclosure.code}')
            cited_documents = []
            
            # Use custom AI prompt if set, otherwise use requirement_text
            disclosure_requirement = disclosure.ai_prompt if disclosure.ai_prompt else disclosure.requirement_text
            
            # Build simpler prompt without document context
            system_prompt = f"""You are an ESRS expert assistant.

CRITICAL: Without sufficient information, respond: "⚠️ INSUFFICIENT INFORMATION: Cannot answer without relevant company documents containing [specific data needed]."
DO NOT provide generic or assumed answers.

DISCLOSURE: {disclosure.code} - {disclosure.name}
REQUIREMENT: {disclosure_requirement}
"""
            
            if user_notes:
                system_prompt += f"\n\nUSER NOTES:\n{user_notes}"
            
            if manual_answer:
                system_prompt += f"\n\nMANUAL ANSWER PROVIDED:\n{manual_answer}"
            
            # Call Chat Completions API without file_search + track token usage
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            
            # Get organization owner for billing
            org_owner = user
            
            with OpenAIUsageTracker(user.id, org_owner.id, 'ai_answer', disclosure.id) as tracker:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": system_prompt}],
                    max_tokens=2000,
                    temperature=ai_temperature
                )
                tracker.record(response, model="gpt-4o")
            
            # Extract answer from chat completion response
            ai_answer = response.choices[0].message.content
            
            if not ai_answer:
                raise ValueError('No answer generated by OpenAI (no file_search)')
            
            logger.info(f'Generated AI answer WITHOUT file_search: {len(ai_answer)} chars')
        
        # Common code for both paths
        update_status(progress=90, current_step="📊 Calculating confidence score...")
        
        # Calculate confidence score from TIER RAG or basic calculation
        if has_rag_chunks and cited_documents:
            # Use avg_confidence from TIER RAG (real hybrid scores)
            confidence_score = round(avg_confidence * 100, 1)
            logger.info(f'Using TIER RAG confidence score: {confidence_score}% (hybrid search)')
        else:
            # Fallback: basic confidence calculation for old system
            def calculate_confidence_score(answer_text: str, cited_docs: list) -> float:
                """Calculate confidence: % of sentences with document citations"""
                if not answer_text or not cited_docs:
                    return 0.0
                
                # Split into sentences (simple approach)
                sentences = [s.strip() for s in answer_text.split('.') if s.strip()]
                if not sentences:
                    return 0.0
                
                # Count sentences with citations
                cited_sentences = sum(1 for s in sentences if any(keyword in s.lower() for keyword in ['document', 'file', 'according to', 'based on', 'source', 'from the']))
                
                # If we have cited documents, assume higher confidence
                base_confidence = (cited_sentences / len(sentences)) * 100
                if len(cited_docs) > 0:
                    base_confidence = min(base_confidence + 20, 100)
                
                return round(base_confidence, 1)
            
            confidence_score = calculate_confidence_score(ai_answer, cited_documents)
            logger.info(f'Calculated confidence score: {confidence_score}% (basic calculation)')
        
        update_status(
            confidence_score=confidence_score,
            current_step=f"✅ Finalizing answer (Confidence: {confidence_score}%)..."
        )
        
        # Prepare source information
        sources = {
            'linked_documents': [
                {
                    'id': ev.document.id,
                    'file_name': ev.document.file_name,
                    'file_type': ev.document.file_type,
                    'uploaded_at': ev.document.uploaded_at.isoformat(),
                    'notes': ev.notes or '',
                    'is_global': ev.document.is_global
                }
                for ev in evidence_list
            ],
            'cited_documents': cited_documents,
            'user_provided': {
                'has_notes': bool(user_notes),
                'has_manual_answer': bool(manual_answer)
            },
            'method': 'rag_semantic_search' if has_rag_chunks else 'basic_generation',
            'confidence_score': confidence_score
        }
        
        # === SEPARATE AI TASK: Extract Charts from Answer ===
        # IMPORTANT: We send a SEPARATE AI request to extract chart data
        # This is better than regex and keeps user's ability to edit charts!
        analytics = None
        
        try:
            logger.info(f'Extracting chart data via separate AI task: {disclosure.code}')
            from accounts.openai_service import OpenAIService
            openai_service = OpenAIService()
            
            # Send separate AI request to extract charts from the answer
            chart_extraction_result = openai_service.extract_charts_from_answer(
                answer_text=ai_answer,
                disclosure_code=disclosure.code,
                temperature=ai_temperature
            )
            
            if chart_extraction_result:
                analytics = {
                    'has_numeric_data': len(chart_extraction_result.get('charts', [])) > 0,
                    'charts': chart_extraction_result.get('charts', []),
                    'tables': chart_extraction_result.get('tables', []),
                    'numeric_data': [],
                    'categories': {},
                    'output_format': 'json'
                }
                logger.info(f'AI chart extraction: {len(analytics["charts"])} charts, {len(analytics["tables"])} tables')
            else:
                logger.warning('AI chart extraction returned empty result')
                
        except Exception as e:
            logger.warning(f'AI chart extraction failed: {e}')
            analytics = None
        
        # Save AI answer and sources to database
        user_response, created = ESRSUserResponse.objects.get_or_create(
            user=user,
            disclosure=disclosure,
            defaults={
                'ai_answer': ai_answer,
                'ai_sources': sources,
                'confidence_score': confidence_score,
                'ai_temperature': ai_temperature,
                'numeric_data': analytics.get('numeric_data') if analytics else None,
                'chart_data': analytics.get('charts') if analytics else None,
                'table_data': analytics.get('tables') if analytics else None,
                'created_by': user,
                'modified_by': user
            }
        )
        
        if not created:
            user_response.ai_answer = ai_answer
            user_response.ai_sources = sources
            user_response.confidence_score = confidence_score
            user_response.ai_temperature = ai_temperature
            user_response.modified_by = user
            # Update analytics data
            if analytics:
                user_response.numeric_data = analytics.get('numeric_data')
                user_response.chart_data = analytics.get('charts')
                user_response.table_data = analytics.get('tables')
            user_response.save()
        
        # === CREATE VERSION FOR AI ANSWER ===
        from accounts.models import ItemVersion
        
        # Get latest version number
        latest_version = ItemVersion.objects.filter(
            item_type='TEXT',
            item_id=user_response.id,
            user=user
        ).order_by('-version_number').first()
        
        next_version_number = (latest_version.version_number + 1) if latest_version else 1
        
        # Create new version
        ItemVersion.objects.create(
            item_type='TEXT',
            item_id=user_response.id,
            user=user,
            disclosure=disclosure,
            version_number=next_version_number,
            content={'text': ai_answer, 'format': 'markdown'},
            change_type='INITIAL',
            change_description=f'AI generated answer (temperature: {ai_temperature}, confidence: {confidence_score}%)',
            created_by_user=False,  # AI generated
            created_by=user,  # Track which user triggered the AI generation
            is_selected=True,  # Auto-select latest AI answer
            parent_version=latest_version
        )
        
        # Deselect previous versions
        if latest_version:
            ItemVersion.objects.filter(
                item_type='TEXT',
                item_id=user_response.id,
                user=user
            ).exclude(version_number=next_version_number).update(is_selected=False)
        
        # Log activity for AI answer generation
        from accounts.team_models import ActivityLog, UserRole
        organization = user if user.is_organization_owner else UserRole.objects.filter(user=user).first().organization if UserRole.objects.filter(user=user).exists() else user
        ActivityLog.objects.create(
            user=user,
            organization=organization,
            action='ai_answer',
            disclosure=disclosure,
            details={
                'confidence_score': confidence_score,
                'temperature': ai_temperature,
                'charts_count': len(analytics.get('charts', [])) if analytics else 0,
                'chunks_used': len(cited_documents)
            }
        )
        
        # Mark task as completed
        result_msg = f"AI answer generated for {disclosure.code}"
        if analytics and analytics.get('has_numeric_data'):
            result_msg += f" with {len(analytics.get('charts', []))} charts"

        update_status(
            status='completed',
            progress=100,
            completed_items=1,
            result=result_msg
        )
        
        logger.info(f'AI answer generated successfully for {disclosure.code}')
        
        return {
            'success': True,
            'disclosure_code': disclosure.code,
            'ai_answer': ai_answer
        }
        
    except Exception as e:
        logger.error(f'Error generating AI answer: {str(e)}')
        
        # Mark task as failed (if task_status exists)
        try:
            if task_status:
                update_status(status='failed', error_message=str(e))
            else:
                # Try to fetch it one more time in case it was created
                try:
                    task_status_fallback = AITaskStatus.objects.get(task_id=task_id)
                    task_status_fallback.status = 'failed'
                    task_status_fallback.error_message = str(e)
                    task_status_fallback.save()
                except Exception:
                    pass
        except Exception:
            pass
        
        raise


@shared_task(bind=True)
def generate_bulk_ai_answers_task(self, standard_id: int, user_id: int):
    """Celery task za generiranje AI odgovorov za VSE disclosure točke v standardu"""
    from accounts.models import ESRSStandard, ESRSDisclosure, User, AITaskStatus
    
    task_id = self.request.id
    
    try:
        # Get task status
        task_status = AITaskStatus.objects.get(task_id=task_id)
        task_status.status = 'running'
        task_status.save()
        
        # Get user and standard
        user = User.objects.get(id=user_id)
        standard = ESRSStandard.objects.get(id=standard_id)
        
        # Get all disclosures for this standard (including sub-disclosures)
        disclosures = ESRSDisclosure.objects.filter(standard=standard).order_by('order')
        total = disclosures.count()
        
        task_status.total_items = total
        task_status.save()
        
        logger.info(f'Starting bulk AI generation for {standard.code}: {total} disclosures')
        
        completed = 0
        errors = []
        
        for disclosure in disclosures:
            try:
                # Generate AI answer for this disclosure
                generate_ai_answer_task.apply(args=[disclosure.id, user_id])
                completed += 1
                
                # Update progress
                progress = int((completed / total) * 100)
                task_status.progress = progress
                task_status.completed_items = completed
                task_status.save()
                
                logger.info(f'Progress: {completed}/{total} ({progress}%)')
                
            except Exception as e:
                errors.append(f"{disclosure.code}: {str(e)}")
                logger.error(f'Error processing {disclosure.code}: {str(e)}')
        
        # Mark as completed
        task_status.status = 'completed'
        task_status.progress = 100
        task_status.result = f"Completed {completed}/{total} disclosures"
        if errors:
            task_status.error_message = "\n".join(errors)
        task_status.save()
        
        logger.info(f'Bulk AI generation completed: {completed}/{total}')
        
        return {
            'success': True,
            'standard_code': standard.code,
            'completed': completed,
            'total': total,
            'errors': errors
        }
        
    except Exception as e:
        logger.error(f'Error in bulk AI generation: {str(e)}')
        
        try:
            task_status = AITaskStatus.objects.get(task_id=task_id)
            task_status.status = 'failed'
            task_status.error_message = str(e)
            task_status.save()
        except Exception:
            pass
        
        raise
