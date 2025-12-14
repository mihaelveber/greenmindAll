from celery import shared_task
from django.core.mail import send_mail
import logging

logger = logging.getLogger(__name__)

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
def generate_ai_answer_task(self, disclosure_id: int, user_id: int, ai_temperature: float = 0.2):
    """
    Celery task za generiranje AI odgovora za eno disclosure točko
    Uses OpenAI Responses API with file_search tool for unlimited document size
    """
    from accounts.models import ESRSUserResponse, ESRSDisclosure, DocumentEvidence, Document, User, AITaskStatus
    from django.conf import settings
    import openai
    
    task_id = self.request.id
    
    try:
        # Update task status to running
        task_status = AITaskStatus.objects.get(task_id=task_id)
        task_status.status = 'running'
        task_status.progress = 10
        task_status.save()
        
        # Get user and disclosure
        user = User.objects.get(id=user_id)
        disclosure = ESRSDisclosure.objects.select_related('standard').get(id=disclosure_id)
        
        logger.info(f'Generating AI answer for {disclosure.code} (user: {user.email}) using Responses API')
        
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
        
        task_status.progress = 30
        task_status.save()
        
        # Auto-link global documents if not excluded
        global_documents = Document.objects.filter(user=user, is_global=True)
        for global_doc in global_documents:
            evidence, created = DocumentEvidence.objects.get_or_create(
                document=global_doc,
                disclosure=disclosure,
                user=user,
                is_excluded=False,  # Part of lookup - will not re-activate excluded docs
                defaults={'notes': 'Auto-linked global document'}
            )
        
        # Get linked documents with evidence notes (excluding explicitly excluded global docs)
        evidence_list = list(
            DocumentEvidence.objects.filter(
                disclosure=disclosure,
                user=user,
                is_excluded=False  # Filter out excluded global documents
            ).select_related('document')
        )
        
        task_status.progress = 50
        task_status.save()
        
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
            prompt = f"""You are an expert in European Sustainability Reporting Standards (ESRS).

📋 DISCLOSURE REQUIREMENT:
Standard: {disclosure.standard.code} - {disclosure.standard.name}
Disclosure: {disclosure.code} - {disclosure.name}

Description: {disclosure.description}

Requirement: {disclosure_requirement}
{linked_docs_context}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 USER'S MANUAL ANSWER:
{manual_answer if manual_answer else "No manual answer provided yet."}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 USER'S NOTES:
{user_notes if user_notes else "No notes provided yet."}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TASK: Using the file_search tool to search through the user's uploaded documents, provide a comprehensive answer that addresses this ESRS disclosure requirement. Be specific, cite relevant information from the documents, and provide actionable guidance. Focus especially on documents linked to this disclosure."""

            task_status.progress = 70
            task_status.save()
            
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
            
            # Get RAG chunks from relevant documents
            from accounts.models import DocumentChunk
            relevant_chunks = DocumentChunk.objects.filter(
                document_id__in=relevant_doc_ids
            ).select_related('document').order_by('-created_at')[:20]  # Get up to 20 most recent chunks
            
            logger.info(f'Found {len(relevant_chunks)} relevant chunks from RAG search')
            
            # Build context from RAG chunks
            rag_context = "\n\n📚 RELEVANT INFORMATION FROM YOUR DOCUMENTS:\n\n"
            cited_documents = []
            seen_docs = set()
            
            for chunk in relevant_chunks:
                doc = chunk.document
                if doc.id not in seen_docs:
                    cited_documents.append({
                        'id': doc.id,
                        'file_name': doc.file_name,
                        'file_type': doc.file_type,
                        'uploaded_at': doc.uploaded_at.isoformat()
                    })
                    seen_docs.add(doc.id)
                
                rag_context += f"[From {doc.file_name}]:\n{chunk.content}\n\n"
            
            # Add RAG context to prompt
            full_prompt = prompt + rag_context
            
            logger.info(f'Built RAG context with {len(rag_context)} characters from {len(cited_documents)} documents')
            
            # Call OpenAI Chat Completions API with RAG context
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": full_prompt}],
                max_tokens=2000,
                temperature=ai_temperature
            )
            
            # Extract AI answer from chat completion response
            ai_answer = response.choices[0].message.content
            
            if not ai_answer:
                raise ValueError('No answer generated by OpenAI')
            
            logger.info(f'Generated AI answer using RAG: {len(ai_answer)} characters')
        
        else:
            # Generate AI answer WITHOUT file_search for users with old documents (pre-migration)
            logger.info(f'Generating AI answer WITHOUT file_search for {disclosure.code}')
            cited_documents = []
            
            # Use custom AI prompt if set, otherwise use requirement_text
            disclosure_requirement = disclosure.ai_prompt if disclosure.ai_prompt else disclosure.requirement_text
            
            # Build simpler prompt without document context
            system_prompt = f"""You are an ESRS (European Sustainability Reporting Standards) expert assistant.
Generate a comprehensive answer for the following disclosure requirement.

DISCLOSURE: {disclosure.code} - {disclosure.name}
CATEGORY: {disclosure.standard.category.name}
STANDARD: {disclosure.standard.name}

REQUIREMENT:
{disclosure_requirement}
"""
            
            if user_notes:
                system_prompt += f"\n\nUSER NOTES:\n{user_notes}"
            
            if manual_answer:
                system_prompt += f"\n\nMANUAL ANSWER PROVIDED:\n{manual_answer}"
            
            # Call Chat Completions API without file_search
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": system_prompt}],
                max_tokens=2000,
                temperature=ai_temperature
            )
            
            # Extract answer from chat completion response
            ai_answer = response.choices[0].message.content
            
            if not ai_answer:
                raise ValueError('No answer generated by OpenAI (no file_search)')
            
            logger.info(f'Generated AI answer WITHOUT file_search: {len(ai_answer)} chars')
        
        # Common code for both paths
        task_status.progress = 90
        task_status.save()
        
        # Calculate confidence score (% from documents vs AI reasoning)
        def calculate_confidence_score(answer_text: str, cited_docs: list) -> float:
            """Calculate confidence: % of sentences with document citations"""
            if not answer_text or not cited_docs:
                return 0.0
            
            # Split into sentences (simple approach)
            sentences = [s.strip() for s in answer_text.split('.') if s.strip()]
            if not sentences:
                return 0.0
            
            # Count sentences with citations (looking for keywords like "document", "file", "according to")
            cited_sentences = sum(1 for s in sentences if any(keyword in s.lower() for keyword in ['document', 'file', 'according to', 'based on', 'source', 'from the']))
            
            # If we have cited documents, assume higher confidence
            base_confidence = (cited_sentences / len(sentences)) * 100
            if len(cited_docs) > 0:
                # Boost confidence if we have documents
                base_confidence = min(base_confidence + 20, 100)
            
            return round(base_confidence, 1)
        
        confidence_score = calculate_confidence_score(ai_answer, cited_documents)
        logger.info(f'Calculated confidence score: {confidence_score}% (from documents)')
        
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
                'table_data': analytics.get('tables') if analytics else None
            }
        )
        
        if not created:
            user_response.ai_answer = ai_answer
            user_response.ai_sources = sources
            user_response.confidence_score = confidence_score
            user_response.ai_temperature = ai_temperature
            # Update analytics data
            if analytics:
                user_response.numeric_data = analytics.get('numeric_data')
                user_response.chart_data = analytics.get('charts')
                user_response.table_data = analytics.get('tables')
            user_response.save()
        
        # Mark task as completed
        task_status.status = 'completed'
        task_status.progress = 100
        task_status.completed_items = 1
        task_status.result = f"AI answer generated for {disclosure.code}"
        if analytics and analytics.get('has_numeric_data'):
            task_status.result += f" with {len(analytics.get('charts', []))} charts"
        task_status.save()
        
        logger.info(f'AI answer generated successfully for {disclosure.code}')
        
        return {
            'success': True,
            'disclosure_code': disclosure.code,
            'ai_answer': ai_answer
        }
        
    except Exception as e:
        logger.error(f'Error generating AI answer: {str(e)}')
        
        # Mark task as failed
        try:
            task_status = AITaskStatus.objects.get(task_id=task_id)
            task_status.status = 'failed'
            task_status.error_message = str(e)
            task_status.save()
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
