from ninja import NinjaAPI
from ninja.errors import ValidationError
from django.http import JsonResponse
from django.db import models
from accounts.auth import JWTAuth, AdminAuth, create_access_token, create_refresh_token
from accounts.schemas import (
    LoginSchema, RegisterSchema, TokenSchema,
    UserSchema, MessageSchema, CompanyTypeSchema, DocumentSchema,
    ESRSCategorySchema, ESRSStandardSchema, ESRSStandardDetailSchema,
    SaveNotesSchema, SaveManualAnswerSchema, SaveFinalAnswerSchema, LinkDocumentSchema, GetAIAnswerSchema,
    ESRSUserResponseSchema, DocumentEvidenceSchema,
    AITaskStatusSchema, StartAITaskResponse, UpdateNotesSchema, GenerateImageSchema,
    StartConversationSchema, SendMessageSchema, SelectVersionSchema, ToggleChartSelectionSchema,
    StandardTypeSchema, CategoryWithProgressSchema, UpdateChartSchema, UpdateTableSchema,
    ChartSelectionResponseSchema, WebsiteUrlSchema, AssignDisclosureSchema, UpdateRAGSettingsSchema
)
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.hashers import make_password
from asgiref.sync import sync_to_async
from accounts.tasks import send_welcome_email
from accounts.team_models import ActivityLog
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


# ===== TEAM COLLABORATION HELPER FUNCTIONS =====

def get_organization_owner(user):
    """Get the organization owner for a user"""
    from accounts.team_models import UserRole
    
    if user.is_organization_owner:
        return user
    
    try:
        role = UserRole.objects.get(user=user)
        return role.organization
    except UserRole.DoesNotExist:
        return user  # Fallback to user itself


def log_activity_sync(user, action, disclosure=None, details=None):
    """Synchronous activity logging"""
    organization = get_organization_owner(user)
    ActivityLog.objects.create(
        user=user,
        organization=organization,
        action=action,
        disclosure=disclosure,
        details=details or {}
    )


async def log_activity(user, action, disclosure=None, details=None):
    """Async activity logging"""
    await sync_to_async(log_activity_sync)(user, action, disclosure, details)


api = NinjaAPI(
    title="Greenmind AI API",
    version="1.0.0",
    description="Django Ninja API z OAuth2 podporo - Greenmind AI"
)

# Import conversation API router
from .conversation_api import router as conversation_router
api.add_router("", conversation_router)

# Import team management API router
from .team_api import router as team_router
api.add_router("", team_router)

# Import admin API router
from .admin_api import router as admin_router
api.add_router("/admin", admin_router, tags=["Admin"])

# Import model selection API router
from .model_selection_api import router as model_selection_router
api.add_router("/ai", model_selection_router)

# Import branding API router
from .branding_api import router as branding_router
api.add_router("", branding_router)

@api.post("/auth/register", response=TokenSchema)
async def register(request, data: RegisterSchema):
    """Async registracija uporabnika"""
    logger.info(f"Registration attempt for email: {data.email}")
    if data.password != data.password_confirm:
        logger.warning(f"Registration failed - passwords don't match for email: {data.email}")
        return JsonResponse(
            {"message": "Gesli se ne ujemata"},
            status=400
        )
    
    # Preveri če email že obstaja
    if await User.objects.filter(email=data.email).aexists():
        logger.warning(f"Registration failed - email already exists: {data.email}")
        return JsonResponse(
            {"message": "Email že obstaja"},
            status=400
        )
    
    # Preveri če username že obstaja
    if await User.objects.filter(username=data.username).aexists():
        logger.warning(f"Registration failed - username already exists: {data.username}")
        return JsonResponse(
            {"message": "Uporabniško ime že obstaja"},
            status=400
        )

    # Ustvari uporabnika
    user = await sync_to_async(User.objects.create)(
        email=data.email,
        username=data.username,
        password=make_password(data.password)
    )
    logger.info(f"User registered successfully: {user.email} (ID: {user.id})")

    # Pošlji welcome email async (Celery)
    send_welcome_email.delay(user.email, user.username)
    logger.debug(f"Welcome email task queued for: {user.email}")

    # Ustvari tokena
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "avatar": user.avatar,
            "oauth_provider": user.oauth_provider,
            "is_active": user.is_active,
            "date_joined": user.date_joined,
            "wizard_completed": user.wizard_completed,
            "company_type": user.company_type
        }
    }

@api.post("/auth/login", response=TokenSchema)
async def login(request, data: LoginSchema):
    """Async prijava uporabnika"""
    logger.info(f"Login attempt for email: {data.email}")
    try:
        user = await User.objects.aget(email=data.email)
    except User.DoesNotExist:
        logger.warning(f"Login failed - user not found: {data.email}")
        return JsonResponse(
            {"message": "Napačen email ali geslo"},
            status=401
        )
    
    # Preveri geslo
    if not user.check_password(data.password):
        logger.warning(f"Login failed - incorrect password for: {data.email}")
        return JsonResponse(
            {"message": "Napačen email ali geslo"},
            status=401
        )

    if not user.is_active:
        logger.warning(f"Login failed - account inactive: {data.email}")
        return JsonResponse(
            {"message": "Račun je deaktiviran"},
            status=403
        )

    # Ustvari tokena
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    logger.info(f"User logged in successfully: {user.email} (ID: {user.id})")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "avatar": user.avatar,
            "oauth_provider": user.oauth_provider,
            "is_active": user.is_active,
            "date_joined": user.date_joined,
            "wizard_completed": user.wizard_completed,
            "company_type": user.company_type
        }
    }

@api.get("/auth/me", response=UserSchema, auth=JWTAuth())
async def get_current_user(request):
    """Pridobi trenutnega uporabnika"""
    return {
        "id": request.auth.id,
        "email": request.auth.email,
        "username": request.auth.username,
        "avatar": request.auth.avatar,
        "oauth_provider": request.auth.oauth_provider,
        "is_active": request.auth.is_active,
        "date_joined": request.auth.date_joined,
        "wizard_completed": request.auth.wizard_completed,
        "company_type": request.auth.company_type,
        "website_url": request.auth.website_url,
        "is_staff": request.auth.is_staff,
        "is_organization_owner": request.auth.is_organization_owner
    }

@api.post("/auth/logout", response=MessageSchema, auth=JWTAuth())
async def logout(request):
    """Odjava uporabnika"""
    return {"message": "Uspešna odjava", "success": True}

@api.get("/auth/rag-settings", response=dict, auth=JWTAuth())
async def get_rag_settings(request):
    """Get user's RAG TIER configuration"""
    user = request.auth
    return {
        "rag_tier1_enabled": user.rag_tier1_enabled,
        "rag_tier2_threshold": user.rag_tier2_threshold,
        "rag_tier3_enabled": user.rag_tier3_enabled,
        "rag_tier3_threshold": user.rag_tier3_threshold
    }

@api.post("/auth/update-rag-settings", response=MessageSchema, auth=JWTAuth())
async def update_rag_settings(request, data: UpdateRAGSettingsSchema):
    """Update user's RAG TIER configuration"""
    user = request.auth

    user.rag_tier1_enabled = data.rag_tier1_enabled
    user.rag_tier2_threshold = data.rag_tier2_threshold
    user.rag_tier3_enabled = data.rag_tier3_enabled
    user.rag_tier3_threshold = data.rag_tier3_threshold

    await sync_to_async(user.save)()

    return {"message": "RAG settings updated successfully", "success": True}

@api.get("/auth/google/login")
def google_login(request):
    """Redirect na Google OAuth2"""
    from allauth.socialaccount.providers.google.views import oauth2_login
    return oauth2_login(request)

@api.get("/auth/apple/login")
def apple_login(request):
    """Redirect na Apple OAuth2"""
    from allauth.socialaccount.providers.apple.views import oauth2_login
    return oauth2_login(request)

@api.post("/profile/company-type", response=MessageSchema, auth=JWTAuth())
async def set_company_type(request, data: CompanyTypeSchema):
    """Nastavi tip podjetja in website URL"""
    user = request.auth
    logger.info(f"Setting company type: {data.company_type} for user {user.id}")
    user.company_type = data.company_type

    # Save website URL if provided
    if hasattr(data, 'website_url') and data.website_url:
        user.website_url = data.website_url
        logger.debug(f"Website URL set: {data.website_url} for user {user.id}")

    await sync_to_async(user.save)()

    return {"message": "Company type saved successfully", "success": True}

@api.post("/profile/scrape-website", response=MessageSchema, auth=JWTAuth())
async def scrape_website(request, data: dict):
    """Trigger website scraping task (for wizard - saves to user.website_url)"""
    from accounts.website_scraper_task import scrape_company_website_task

    user = request.auth
    website_url = data.get('website_url')

    if not website_url:
        logger.warning(f"Website scraping failed - no URL provided by user {user.id}")
        return {"message": "Website URL is required", "success": False}

    logger.info(f"Website scraping request: {website_url} for user {user.id}")

    # Save to user profile
    user.website_url = website_url
    await sync_to_async(user.save)()

    # Trigger async scraping task
    task = await sync_to_async(scrape_company_website_task.delay)(user.id, website_url)
    logger.info(f"Website scraping task started: task_id={task.id}, url={website_url}, user={user.id}")

    return {"message": "Website scraping started", "success": True, "task_id": task.id}

@api.post("/profile/update-website", response=MessageSchema, auth=JWTAuth())
async def update_website(request, data: dict):
    """Update specific website document and trigger re-scraping"""
    from accounts.website_scraper_task import scrape_company_website_task
    from accounts.models import Document
    
    user = request.auth
    website_url = data.get('website_url')
    document_id = data.get('document_id')  # Optional: specific document to update
    
    if not website_url:
        return {"message": "Website URL is required", "success": False}
    
    # If document_id provided, delete that specific document
    if document_id:
        await sync_to_async(Document.objects.filter(
            id=document_id,
            user=user,
            file_name__startswith='Company Website:'
        ).delete)()
    
    # Update user's website URL (for primary website)
    user.website_url = website_url
    await sync_to_async(user.save)()
    
    # Trigger async scraping task
    task = await sync_to_async(scrape_company_website_task.delay)(user.id, website_url)
    
    return {"message": "Website updated and re-scraping started", "success": True, "task_id": task.id}

@api.post("/documents/add-website", response=MessageSchema, auth=JWTAuth())
async def add_website(request, data: WebsiteUrlSchema):
    """Add additional website as global document"""
    from accounts.website_scraper_task import scrape_company_website_task
    
    user = request.auth
    website_url = data.website_url.strip()  # Clean URL
    
    if not website_url:
        return {"message": "Website URL is required", "success": False}
    
    # Trigger async scraping task (will create new website document)
    task = await sync_to_async(scrape_company_website_task.delay)(user.id, website_url)
    
    return {"message": f"Website crawling started for {website_url}. This may take a few minutes...", "success": True, "task_id": task.id}

@api.post("/profile/complete-wizard", response=MessageSchema, auth=JWTAuth())
async def complete_wizard(request):
    """Označi wizard kot zaključen"""
    user = request.auth
    user.wizard_completed = True
    await sync_to_async(user.save)()
    
    return {"message": "Wizard completed successfully", "success": True}

@api.post("/documents/upload", auth=JWTAuth())
async def upload_document(request):
    """Naloži dokument in izvleči tekst za AI"""
    from django.core.files.storage import default_storage
    from django.core.files.base import ContentFile
    from accounts.models import Document
    from accounts.document_parser import parse_document, is_supported_format, get_supported_formats_message
    from django.conf import settings
    import os

    if not request.FILES.get('file'):
        logger.warning(f"Document upload failed - no file provided by user {request.auth.id}")
        return JsonResponse({"message": "No file provided"}, status=400)

    file = request.FILES['file']
    user = request.auth
    logger.info(f"Document upload started: {file.name} by user {user.id} ({user.email})")

    # Check if file format is supported
    if not is_supported_format(file.name):
        logger.warning(f"Document upload failed - unsupported format: {file.name} by user {user.id}")
        return JsonResponse({
            "message": f"Unsupported file format. {get_supported_formats_message()}",
            "success": False
        }, status=400)
    
    try:
        # Ustvari mapo za uporabnika
        user_folder = f"documents/user_{user.id}"
        os.makedirs(os.path.join('media', user_folder), exist_ok=True)
        
        # Shrani original datoteko
        file_path = f"{user_folder}/{file.name}"
        saved_path = default_storage.save(file_path, ContentFile(file.read()))
        full_file_path = os.path.join(settings.MEDIA_ROOT, saved_path)
        
        # Extract text content for AI
        try:
            extracted_text, format_info = await sync_to_async(parse_document)(
                full_file_path,
                file.name
            )
            
            # Save extracted text as .txt file for AI to use
            text_file_name = f"{file.name}.extracted.txt"
            text_file_path = f"{user_folder}/{text_file_name}"
            text_saved_path = default_storage.save(
                text_file_path,
                ContentFile(extracted_text.encode('utf-8'))
            )
            
            logger.info(f'Document parsed successfully: {file.name} ({format_info})')
            
        except ValueError as e:
            # Unsupported format
            default_storage.delete(saved_path)
            return JsonResponse({"message": str(e), "success": False}, status=400)
        
        except Exception as e:
            # Parsing failed but keep original file
            logger.error(f'Document parsing failed for {file.name}: {str(e)}')
            extracted_text = None
            text_saved_path = None
        
        # Check if this is a wizard upload (has company_type) - make documents global
        company_type = request.POST.get('company_type', '')
        is_wizard_upload = bool(company_type)
        
        # Allow manual is_global setting from Documents page
        is_global_param = request.POST.get('is_global', '')
        if is_global_param:
            # Frontend explicitly set is_global
            is_global = is_global_param.lower() == 'true'
        else:
            # Default to wizard upload behavior
            is_global = is_wizard_upload
        
        # Ustvari Document zapis (samo v Django bazi, brez OpenAI)
        document = await sync_to_async(Document.objects.create)(
            user=user,
            file_name=file.name,
            file_path=saved_path,
            file_size=file.size,
            file_type=file.content_type,
            is_global=is_global
        )
        
        logger.info(f'Document {document.id} saved to database: {file.name} (is_global={is_global})')
        
        # Start RAG processing in background (chunking + embeddings)
        from accounts.document_rag_tasks import process_document_with_rag
        task = process_document_with_rag.delay(document.id)
        logger.info(f'Started RAG processing for document {document.id} (task: {task.id})')
        
        return {
            "message": "File uploaded successfully" + (" and text extracted for AI" if extracted_text else ""),
            "file_id": document.id,
            "file_name": document.file_name,
            "text_extracted": extracted_text is not None,
            "rag_task_id": task.id
        }
    
    except Exception as e:
        logger.error(f'Upload failed for {file.name}: {str(e)}')
        return JsonResponse({
            "message": f"Upload failed: {str(e)}",
            "success": False
        }, status=500)

@api.get("/documents/list", auth=JWTAuth())
async def list_documents(request):
    """Pridobi seznam dokumentov z usage info"""
    from accounts.models import Document, DocumentEvidence
    
    documents = await sync_to_async(list)(
        Document.objects.filter(user=request.auth)
    )
    
    # Add usage info for each document
    result = []
    for doc in documents:
        # Check if document is linked to any disclosures
        linked_evidence = await sync_to_async(list)(
            DocumentEvidence.objects.filter(
                document=doc, 
                user=request.auth, 
                is_excluded=False
            ).select_related('disclosure')
        )
        
        linked_count = len(linked_evidence)
        
        # Get disclosure codes for question-specific documents
        linked_disclosure_codes = []
        if not doc.is_global and linked_evidence:
            linked_disclosure_codes = [ev.disclosure.code for ev in linked_evidence]
        
        # Use actual is_global field from database
        is_global = doc.is_global
        doc_type = "Global" if is_global else "Question-Specific"
        
        result.append({
            'id': doc.id,
            'file_name': doc.file_name,
            'file_size': doc.file_size,
            'file_type': doc.file_type,
            'uploaded_at': doc.uploaded_at,
            'document_type': doc_type,
            'linked_questions_count': linked_count,
            'linked_disclosure_codes': linked_disclosure_codes,  # ✅ NEW: List of disclosure codes
            'is_global': is_global,
            'rag_processing_status': doc.rag_processing_status,
            'rag_chunks_count': doc.rag_chunks_count
        })
    
    return result

@api.get("/documents/download/{document_id}")
async def download_document(request, document_id: int, token: str = None):
    """Download ali preview dokumenta"""
    from accounts.models import Document
    from django.core.files.storage import default_storage
    from django.http import FileResponse
    import jwt
    from django.conf import settings
    import mimetypes
    
    try:
        # Preveri JWT token (iz query parametra za browser preview)
        if not token:
            # Poskusi iz Authorization headerja
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
            else:
                return JsonResponse({"message": "Authentication required"}, status=401)
        
        # Dekodiranje JWT tokena
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            user_id = payload.get('user_id')
            user = await sync_to_async(User.objects.get)(id=user_id)
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, User.DoesNotExist) as e:
            return JsonResponse({"message": f"Invalid or expired token: {str(e)}"}, status=401)
        
        # Pridobi dokument in preveri lastništvo
        document = await sync_to_async(Document.objects.get)(
            id=document_id,
            user=user
        )
        
        # Preveri če datoteka obstaja
        if not document.file_path or not default_storage.exists(document.file_path):
            return JsonResponse({"message": "File not found"}, status=404)
        
        # Odpri datoteko
        file_path = default_storage.path(document.file_path)
        file = open(file_path, 'rb')
        
        # Določi MIME type
        content_type = document.file_type or mimetypes.guess_type(document.file_name)[0] or 'application/octet-stream'
        
        # Vedno uporabi inline disposition - browser bo odločil ali lahko odpre ali ne
        response = FileResponse(file, content_type=content_type)
        response['Content-Disposition'] = f'inline; filename="{document.file_name}"'
        response['Content-Length'] = document.file_size
        
        return response
    
    except Document.DoesNotExist:
        return JsonResponse({"message": "Document not found or access denied"}, status=404)
    except Exception as e:
        return JsonResponse({"message": f"Error: {str(e)}"}, status=500)

@api.delete("/documents/delete/{document_id}", response=MessageSchema, auth=JWTAuth())
async def delete_document(request, document_id: int):
    """Izbriši dokument"""
    from accounts.models import Document
    from django.core.files.storage import default_storage
    import os

    logger.info(f"Delete document request: document_id={document_id}, user={request.auth.id}")

    try:
        # Pridobi dokument in preveri lastništvo
        document = await sync_to_async(Document.objects.get)(
            id=document_id,
            user=request.auth
        )

        # Izbriši fizično datoteko
        if document.file_path and default_storage.exists(document.file_path):
            await sync_to_async(default_storage.delete)(document.file_path)
            logger.debug(f"Deleted file from storage: {document.file_path}")

        # Izbriši database zapis
        await sync_to_async(document.delete)()
        logger.info(f"Document deleted successfully: document_id={document_id}, file={document.file_name}, user={request.auth.id}")

        return {"message": "Document deleted successfully", "success": True}

    except Document.DoesNotExist:
        logger.warning(f"Delete document failed - not found or access denied: document_id={document_id}, user={request.auth.id}")
        return JsonResponse({"message": "Document not found or access denied"}, status=404)


@api.put("/documents/{document_id}/toggle-global", response=MessageSchema, auth=JWTAuth())
async def toggle_document_global(request, document_id: int):
    """Toggle is_global status for a document"""
    from accounts.models import Document
    
    try:
        document = await sync_to_async(Document.objects.get)(
            id=document_id,
            user=request.auth
        )
        
        # Toggle is_global
        document.is_global = not document.is_global
        await sync_to_async(document.save)()
        
        status = "global" if document.is_global else "question-specific"
        return {
            "message": f"Document marked as {status}", 
            "success": True,
            "is_global": document.is_global
        }
    
    except Document.DoesNotExist:
        return JsonResponse({"message": "Document not found"}, status=404)


# ========== DYNAMIC STANDARDS ENDPOINTS ==========

@api.get("/standards/types", response=list[StandardTypeSchema], auth=JWTAuth())
async def get_standard_types(request):
    """Get all available standard types with completion statistics"""
    from accounts.models import ESRSCategory, ESRSStandard, ESRSDisclosure, ESRSUserResponse
    from accounts.schemas import StandardTypeSchema
    from django.db.models import Q, Count
    
    def calculate_types():
        # Get unique standard types from database
        all_categories = ESRSCategory.objects.all()
        standard_types = list(set(cat.standard_type for cat in all_categories))
        
        # Filter by user's allowed standards (if specified)
        user_allowed = request.auth.allowed_standards or []
        if user_allowed:  # If empty list, allow all
            standard_types = [st for st in standard_types if st in user_allowed]
        
        result = []
        
        # Standard type metadata
        type_metadata = {
            'ESRS': {
                'name': 'ESRS Reporting',
                'description': 'European Sustainability Reporting Standards',
                'icon': '🌍'
            },
            'ISO9001': {
                'name': 'ISO 9001:2015',
                'description': 'Quality Management System',
                'icon': '🏆'
            }
        }
        
        for std_type in standard_types:
            metadata = type_metadata.get(std_type, {
                'name': std_type,
                'description': f'{std_type} Standards',
                'icon': '📋'
            })
            
            # Count total requirements for this type
            total = ESRSDisclosure.objects.filter(
                standard__standard_type=std_type
            ).count()
            
            # Count answered requirements for this user and type
            answered = ESRSUserResponse.objects.filter(
                user=request.auth,
                disclosure__standard__standard_type=std_type
            ).filter(
                Q(ai_answer__isnull=False) | Q(manual_answer__isnull=False)
            ).count()
            
            percentage = (answered / total * 100) if total > 0 else 0
            
            result.append({
                'type': std_type,
                'name': metadata['name'],
                'description': metadata['description'],
                'icon': metadata['icon'],
                'total_requirements': total,
                'answered_requirements': answered,
                'completion_percentage': round(percentage, 1)
            })
        
        # Sort by type (ESRS first)
        result.sort(key=lambda x: (x['type'] != 'ESRS', x['type']))
        return result
    
    return await sync_to_async(calculate_types)()


@api.get("/standards/{standard_type}/categories", response=list[CategoryWithProgressSchema], auth=JWTAuth())
async def get_categories_by_type(request, standard_type: str):
    """Get all categories for a specific standard type with user progress"""
    from accounts.models import ESRSCategory, ESRSStandard, ESRSDisclosure, ESRSUserResponse
    from accounts.schemas import CategoryWithProgressSchema
    from django.db.models import Q
    
    # Permission check
    if not request.auth.has_standard_access(standard_type):
        return {"categories": []}
    
    def calculate_categories():
        categories = ESRSCategory.objects.filter(
            standard_type=standard_type
        ).order_by('order')
        
        result = []
        
        for category in categories:
            # Count total disclosures in this category
            total_disclosures = ESRSDisclosure.objects.filter(
                standard__category=category,
                standard__standard_type=standard_type
            ).count()
            
            # Count answered disclosures
            answered_disclosures = ESRSUserResponse.objects.filter(
                user=request.auth,
                disclosure__standard__category=category,
                disclosure__standard__standard_type=standard_type
            ).filter(
                Q(ai_answer__isnull=False) | Q(manual_answer__isnull=False)
            ).count()
            
            percentage = (answered_disclosures / total_disclosures * 100) if total_disclosures > 0 else 0
            
            result.append({
                'id': category.id,
                'name': category.name,
                'code': category.code,
                'description': category.description,
                'order': category.order,
                'standard_type': category.standard_type,
                'total_disclosures': total_disclosures,
                'answered_disclosures': answered_disclosures,
                'completion_percentage': round(percentage, 1)
            })
        
        return result
    
    return await sync_to_async(calculate_categories)()


# ========== ESRS ENDPOINTS ==========

@api.get("/esrs/dashboard-statistics", auth=JWTAuth())
async def get_dashboard_statistics(request):
    """Pridobi statistiko za dashboard - odgovorjena vprašanja po kategorijah"""
    from accounts.models import ESRSCategory, ESRSStandard, ESRSDisclosure, ESRSUserResponse
    from django.db.models import Count, Q
    
    def calculate_stats():
        categories_stats = []
        
        # Filter categories by user permissions
        user_allowed = request.auth.allowed_standards or []
        if user_allowed:
            categories = ESRSCategory.objects.filter(
                standard_type__in=user_allowed
            ).order_by('order')
        else:
            categories = ESRSCategory.objects.all().order_by('order')
        
        for category in categories:
            standards = ESRSStandard.objects.filter(category=category)
            total_disclosures = 0
            answered_disclosures = 0
            
            for standard in standards:
                # Count all disclosures (including sub-disclosures)
                disclosure_count = ESRSDisclosure.objects.filter(standard=standard).count()
                total_disclosures += disclosure_count
                
                # Count answered disclosures (either AI answer or manual answer)
                answered_count = ESRSUserResponse.objects.filter(
                    user=request.auth,
                    disclosure__standard=standard
                ).filter(
                    Q(ai_answer__isnull=False) | Q(manual_answer__isnull=False)
                ).count()
                answered_disclosures += answered_count
            
            percentage = (answered_disclosures / total_disclosures * 100) if total_disclosures > 0 else 0
            
            categories_stats.append({
                'category_id': category.id,
                'category_name': category.name,
                'category_code': category.code,
                'total_disclosures': total_disclosures,
                'answered_disclosures': answered_disclosures,
                'completion_percentage': round(percentage, 1)
            })
        
        return categories_stats
    
    stats = await sync_to_async(calculate_stats)()
    return {'statistics': stats}


@api.get("/esrs/confidence-scores", auth=JWTAuth())
async def get_confidence_scores(request):
    """Get confidence scores for all answered questions"""
    from accounts.models import ESRSUserResponse, ESRSDisclosure
    from django.db.models import Q
    
    def get_scores():
        # Get all answered responses with confidence scores
        responses = ESRSUserResponse.objects.filter(
            user=request.auth,
            confidence_score__isnull=False
        ).filter(
            Q(ai_answer__isnull=False) | Q(manual_answer__isnull=False)
        ).select_related('disclosure').order_by('disclosure__code')
        
        result = []
        for response in responses:
            result.append({
                'disclosure_code': response.disclosure.code,
                'disclosure_name': response.disclosure.name,
                'confidence_score': round(response.confidence_score, 1),
                'answered_at': response.updated_at.isoformat() if response.updated_at else None
            })
        
        return result
    
    scores = await sync_to_async(get_scores)()
    return {'confidence_scores': scores}


@api.get("/esrs/categories", response=list[ESRSCategorySchema], auth=JWTAuth())
async def list_esrs_categories(request):
    """Pridobi vse ESRS kategorije"""
    from accounts.models import ESRSCategory
    
    # Filter by user permissions
    user_allowed = request.auth.allowed_standards or []
    if user_allowed:
        categories = await sync_to_async(list)(
            ESRSCategory.objects.filter(standard_type__in=user_allowed)
        )
    else:
        categories = await sync_to_async(list)(
            ESRSCategory.objects.all()
        )
    
    return categories


@api.get("/esrs/disclosure-codes", response=list, auth=JWTAuth())
async def list_disclosure_codes(request):
    """Get all disclosure codes for assignment dropdown - formatted with names"""
    from accounts.models import ESRSDisclosure, ESRSStandard
    
    # Get user's allowed standards
    user_allowed = request.auth.allowed_standards or []
    
    # Build query - filter by user's allowed standards if set
    if user_allowed:
        disclosures = await sync_to_async(list)(
            ESRSDisclosure.objects.select_related('standard')
            .filter(standard__standard_type__in=user_allowed, parent__isnull=True)
            .order_by('standard__standard_type', 'code')
            .values('code', 'name', 'standard__standard_type', 'standard__name')
        )
    else:
        disclosures = await sync_to_async(list)(
            ESRSDisclosure.objects.select_related('standard')
            .filter(parent__isnull=True)
            .order_by('standard__standard_type', 'code')
            .values('code', 'name', 'standard__standard_type', 'standard__name')
        )
    
    # Format as dropdown options: "E1-1: Climate change mitigation"
    result = []
    for d in disclosures:
        label = f"{d['code']}: {d['name']}"
        result.append({
            'value': d['code'],
            'label': label,
            'standard': d['standard__standard_type']
        })
    
    return result


@api.get("/esrs/standards", response=list[ESRSStandardSchema], auth=JWTAuth())
async def list_esrs_standards(request):
    """Pridobi vse ESRS standarde"""
    from accounts.models import ESRSStandard
    
    # Filter by user permissions
    user_allowed = request.auth.allowed_standards or []
    if user_allowed:
        standards = await sync_to_async(list)(
            ESRSStandard.objects.select_related('category').filter(
                standard_type__in=user_allowed
            )
        )
    else:
        standards = await sync_to_async(list)(
            ESRSStandard.objects.select_related('category').all()
        )
    
    return standards


@api.get("/esrs/standards/{standard_id}", response=ESRSStandardDetailSchema, auth=JWTAuth())
async def get_esrs_standard_detail(request, standard_id: int):
    """Pridobi podrobnosti ESRS standarda z vsemi disclosures in pod-točkami"""
    from accounts.models import ESRSStandard
    
    def build_disclosure_tree(standard):
        """Build hierarchical tree of disclosures with sub-disclosures"""
        # Get all disclosures for this standard
        all_disclosures = list(standard.disclosures.all())
        
        # Separate parent and child disclosures
        parents = [d for d in all_disclosures if d.parent_id is None]
        children_map = {}
        
        for disclosure in all_disclosures:
            if disclosure.parent_id:
                if disclosure.parent_id not in children_map:
                    children_map[disclosure.parent_id] = []
                children_map[disclosure.parent_id].append({
                    'id': disclosure.id,
                    'code': disclosure.code,
                    'name': disclosure.name,
                    'description': disclosure.description,
                    'requirement_text': disclosure.requirement_text,
                    'is_mandatory': disclosure.is_mandatory,
                    'order': disclosure.order,
                    'parent_id': disclosure.parent_id,
                    'sub_disclosures': []
                })
        
        # Build parent disclosures with their children
        result = []
        for parent in parents:
            parent_dict = {
                'id': parent.id,
                'code': parent.code,
                'name': parent.name,
                'description': parent.description,
                'requirement_text': parent.requirement_text,
                'is_mandatory': parent.is_mandatory,
                'order': parent.order,
                'parent_id': None,
                'sub_disclosures': children_map.get(parent.id, [])
            }
            result.append(parent_dict)
        
        return result
    
    try:
        standard = await sync_to_async(
            lambda: ESRSStandard.objects.select_related('category').prefetch_related('disclosures').get(id=standard_id)
        )()
        
        # Build hierarchical disclosure tree
        disclosure_tree = await sync_to_async(build_disclosure_tree)(standard)
        
        return {
            'id': standard.id,
            'code': standard.code,
            'name': standard.name,
            'description': standard.description,
            'order': standard.order,
            'category': {
                'id': standard.category.id,
                'name': standard.category.name,
                'code': standard.category.code,
                'description': standard.category.description,
                'order': standard.category.order,
                'standard_type': standard.category.standard_type
            },
            'disclosures': disclosure_tree
        }
    
    except ESRSStandard.DoesNotExist:
        return JsonResponse({"message": "Standard not found"}, status=404)


# ========== ESRS USER RESPONSE ENDPOINTS (Notes, Completion) ==========

@api.post("/esrs/notes", response=MessageSchema, auth=JWTAuth())
async def save_notes(request, data: SaveNotesSchema):
    """Shrani ali posodobi zapiske za disclosure točko"""
    from accounts.models import ESRSUserResponse, ESRSDisclosure

    logger.info(f"Save notes: disclosure_id={data.disclosure_id}, user={request.auth.id}")

    try:
        disclosure = await sync_to_async(ESRSDisclosure.objects.get)(id=data.disclosure_id)
        
        # Get or create user response
        user_response, created = await sync_to_async(
            lambda: ESRSUserResponse.objects.get_or_create(
                user=request.auth,
                disclosure=disclosure,
                defaults={
                    'notes': data.notes,
                    'ai_temperature': 0.2
                }
            )
        )()
        
        if not created:
            user_response.notes = data.notes
            await sync_to_async(user_response.save)()

        logger.debug(f"Notes {'created' if created else 'updated'} for disclosure_id={data.disclosure_id}, user={request.auth.id}")
        return {"message": "Notes saved successfully", "success": True}

    except ESRSDisclosure.DoesNotExist:
        logger.error(f"Save notes failed - disclosure not found: disclosure_id={data.disclosure_id}, user={request.auth.id}")
        return JsonResponse({"message": "Disclosure not found"}, status=404)


@api.post("/esrs/manual-answer", response=MessageSchema, auth=JWTAuth())
async def save_manual_answer(request, data: SaveManualAnswerSchema):
    """Shrani ali posodobi ročni odgovor za disclosure točko in ustvari version"""
    from accounts.models import ESRSUserResponse, ESRSDisclosure, ItemVersion
    
    try:
        disclosure = await sync_to_async(ESRSDisclosure.objects.get)(id=data.disclosure_id)
        
        # Get or create user response
        user_response, created = await sync_to_async(
            lambda: ESRSUserResponse.objects.get_or_create(
                user=request.auth,
                disclosure=disclosure,
                defaults={
                    'manual_answer': data.manual_answer,
                    'ai_temperature': 0.2,
                    'created_by': request.auth,
                    'modified_by': request.auth
                }
            )
        )()
        
        if not created:
            user_response.manual_answer = data.manual_answer
            user_response.modified_by = request.auth
            await sync_to_async(user_response.save)()
        
        # Create new ItemVersion for manual text edit
        max_version = await sync_to_async(
            lambda: ItemVersion.objects.filter(
                item_type='TEXT',
                item_id=user_response.id,
                user=request.auth
            ).aggregate(models.Max('version_number'))['version_number__max'] or 0
        )()
        
        # Find parent version (current selected version)
        parent_version = await sync_to_async(
            lambda: ItemVersion.objects.filter(
                item_type='TEXT',
                item_id=user_response.id,
                is_selected=True
            ).first()
        )()
        
        new_version = await sync_to_async(ItemVersion.objects.create)(
            user=request.auth,
            disclosure=disclosure,
            item_type='TEXT',
            item_id=user_response.id,
            version_number=max_version + 1,
            parent_version=parent_version,
            change_type='MANUAL_EDIT',
            change_description=f"Manual answer for {disclosure.code}",
            content={"text": data.manual_answer, "format": "html"},
            conversation=None,
            is_selected=True,  # Make this the active version
            created_by_user=True,
            created_by=request.auth
        )
        
        # Deselect old version
        if parent_version:
            parent_version.is_selected = False
            await sync_to_async(parent_version.save)()
        
        # Log activity
        await log_activity(
            user=request.auth,
            action='manual_answer',
            disclosure=disclosure,
            details={'version_id': str(new_version.id), 'action': 'created' if created else 'updated'}
        )
        
        return {"message": "Manual answer saved successfully", "success": True}
    
    except ESRSDisclosure.DoesNotExist:
        return JsonResponse({"message": "Disclosure not found"}, status=404)


@api.post("/esrs/final-answer", response=MessageSchema, auth=JWTAuth())
async def save_final_answer(request, data: SaveFinalAnswerSchema):
    """Shrani ali posodobi končni odobreni odgovor za disclosure točko (za report) in ustvari version"""
    from accounts.models import ESRSUserResponse, ESRSDisclosure, ItemVersion

    logger.info(f"Save final answer: disclosure_id={data.disclosure_id}, user={request.auth.id}")

    try:
        disclosure = await sync_to_async(ESRSDisclosure.objects.get)(id=data.disclosure_id)
        
        # Get or create user response
        user_response, created = await sync_to_async(
            lambda: ESRSUserResponse.objects.get_or_create(
                user=request.auth,
                disclosure=disclosure,
                defaults={
                    'final_answer': data.final_answer,
                    'ai_temperature': 0.2
                }
            )
        )()
        
        if not created:
            user_response.final_answer = data.final_answer
            await sync_to_async(user_response.save)()
        
        # Create new ItemVersion for final approved answer
        max_version = await sync_to_async(
            lambda: ItemVersion.objects.filter(
                item_type='TEXT',
                item_id=user_response.id,
                user=request.auth
            ).aggregate(models.Max('version_number'))['version_number__max'] or 0
        )()
        
        # Find parent version (current selected version)
        parent_version = await sync_to_async(
            lambda: ItemVersion.objects.filter(
                item_type='TEXT',
                item_id=user_response.id,
                is_selected=True
            ).first()
        )()
        
        new_version = await sync_to_async(ItemVersion.objects.create)(
            user=request.auth,
            disclosure=disclosure,
            item_type='TEXT',
            item_id=user_response.id,
            version_number=max_version + 1,
            parent_version=parent_version,
            change_type='MANUAL_EDIT',
            change_description=f"Final approved answer for {disclosure.code}",
            content={"text": data.final_answer, "format": "html"},
            conversation=None,
            is_selected=True,  # Make this the active version
            created_by_user=True
        )
        
        # Deselect old version
        if parent_version:
            parent_version.is_selected = False
            await sync_to_async(parent_version.save)()

        logger.info(f"Final answer saved successfully: disclosure_id={data.disclosure_id}, version={new_version.version_number}, user={request.auth.id}")
        return {"message": "Final answer saved successfully", "success": True}

    except ESRSDisclosure.DoesNotExist:
        logger.error(f"Save final answer failed - disclosure not found: disclosure_id={data.disclosure_id}, user={request.auth.id}")
        return JsonResponse({"message": "Disclosure not found"}, status=404)


@api.get("/esrs/notes/{disclosure_id}", response=ESRSUserResponseSchema, auth=JWTAuth())
async def get_notes(request, disclosure_id: int):
    """Pridobi zapiske za disclosure točko"""
    from accounts.models import ESRSUserResponse, ESRSDisclosure
    
    try:
        user_response = await sync_to_async(
            ESRSUserResponse.objects.get
        )(user=request.auth, disclosure_id=disclosure_id)
        
        # Convert to dict and add assigned_to_id explicitly
        return {
            'id': user_response.id,
            'disclosure_id': user_response.disclosure_id,
            'notes': user_response.notes,
            'manual_answer': user_response.manual_answer,
            'is_completed': user_response.is_completed,
            'ai_answer': user_response.ai_answer,
            'final_answer': user_response.final_answer,
            'ai_sources': user_response.ai_sources,
            'numeric_data': user_response.numeric_data,
            'chart_data': user_response.chart_data,
            'table_data': user_response.table_data,
            'ai_temperature': user_response.ai_temperature,
            'confidence_score': user_response.confidence_score,
            'assigned_to': user_response.assigned_to_id,  # Return ID, not object
            'created_at': user_response.created_at,
            'updated_at': user_response.updated_at
        }
    
    except ESRSUserResponse.DoesNotExist:
        # Return empty response if not exists
        from datetime import datetime
        now = datetime.now()
        return {
            'id': 0,
            'disclosure_id': disclosure_id,
            'notes': None,
            'manual_answer': None,
            'is_completed': False,
            'ai_answer': None,
            'final_answer': None,
            'ai_sources': None,
            'numeric_data': None,
            'chart_data': None,
            'table_data': None,
            'ai_temperature': 0.2,
            'confidence_score': None,
            'assigned_to': None,
            'created_at': now,
            'updated_at': now
        }


@api.post("/esrs/notes/{disclosure_id}", response=MessageSchema, auth=JWTAuth())
async def update_notes(request, disclosure_id: int, data: UpdateNotesSchema):
    """Update notes, manual_answer, or ai_temperature for disclosure"""
    from accounts.models import ESRSUserResponse, ESRSDisclosure
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        disclosure = await sync_to_async(ESRSDisclosure.objects.get)(id=disclosure_id)
        
        user_response, created = await sync_to_async(
            lambda: ESRSUserResponse.objects.get_or_create(
                user=request.auth,
                disclosure=disclosure,
                defaults={'ai_temperature': 0.2}
            )
        )()
        
        # Update fields if provided
        if data.notes is not None:
            user_response.notes = data.notes
        if data.manual_answer is not None:
            user_response.manual_answer = data.manual_answer
        if data.ai_temperature is not None:
            logger.info(f"Updating temperature to {data.ai_temperature} for disclosure {disclosure_id}")
            user_response.ai_temperature = float(data.ai_temperature)
        
        await sync_to_async(user_response.save)()
        
        return {"message": "Updated successfully", "success": True}
    
    except ESRSDisclosure.DoesNotExist:
        return JsonResponse({"message": "Disclosure not found"}, status=404)
    except Exception as e:
        logger.error(f"Error updating notes/temperature: {str(e)}")
        return JsonResponse({"message": f"Error: {str(e)}"}, status=500)


@api.post("/esrs/toggle-completion/{disclosure_id}", response=MessageSchema, auth=JWTAuth())
async def toggle_completion(request, disclosure_id: int):
    """Preklopi status zaključenosti disclosure točke"""
    from accounts.models import ESRSUserResponse, ESRSDisclosure
    
    try:
        disclosure = await sync_to_async(ESRSDisclosure.objects.get)(id=disclosure_id)
        
        user_response, created = await sync_to_async(
            lambda: ESRSUserResponse.objects.get_or_create(
                user=request.auth,
                disclosure=disclosure,
                defaults={
                    'is_completed': True,
                    'ai_temperature': 0.2
                }
            )
        )()
        
        if not created:
            user_response.is_completed = not user_response.is_completed
            await sync_to_async(user_response.save)()
        
        return {"message": "Completion status updated", "success": True}
    
    except ESRSDisclosure.DoesNotExist:
        return JsonResponse({"message": "Disclosure not found"}, status=404)


@api.post("/esrs/assign-disclosure", response=MessageSchema, auth=JWTAuth())
async def assign_disclosure(request, data: AssignDisclosureSchema):
    """Assign disclosure to a team member"""
    from accounts.models import ESRSUserResponse, ESRSDisclosure
    from accounts.team_models import UserRole
    
    try:
        disclosure = await sync_to_async(ESRSDisclosure.objects.get)(id=data.disclosure_id)
        
        # Get organization owner
        organization = get_organization_owner(request.auth)
        
        # If assigned_to_id is None, unassign
        assigned_to_user = None
        if data.assigned_to_id:
            # Verify assigned user is in the same organization
            assigned_to_user = await sync_to_async(User.objects.get)(id=data.assigned_to_id)
            assigned_org = get_organization_owner(assigned_to_user)
            if assigned_org.id != organization.id:
                return JsonResponse({"message": "Cannot assign to user from different organization"}, status=403)
        
        # Get or create user response for the organization owner
        user_response, created = await sync_to_async(
            lambda: ESRSUserResponse.objects.get_or_create(
                user=organization,  # Always use organization owner
                disclosure=disclosure,
                defaults={
                    'assigned_to': assigned_to_user,
                    'ai_temperature': 0.2
                }
            )
        )()
        
        if not created:
            user_response.assigned_to = assigned_to_user
            await sync_to_async(user_response.save)()
        
        # Log activity
        await sync_to_async(log_activity_sync)(
            user=request.auth,
            action='assigned_disclosure' if assigned_to_user else 'unassigned_disclosure',
            disclosure=disclosure,
            details={'assigned_to': assigned_to_user.email if assigned_to_user else None}
        )
        
        message_text = f"Disclosure assigned to {assigned_to_user.email}" if assigned_to_user else "Disclosure unassigned"
        return {"message": message_text, "success": True}
    
    except ESRSDisclosure.DoesNotExist:
        return JsonResponse({"message": "Disclosure not found"}, status=404)
    except User.DoesNotExist:
        return JsonResponse({"message": "Assigned user not found"}, status=404)


# ========== DOCUMENT EVIDENCE ENDPOINTS ==========

@api.post("/esrs/link-document", response=MessageSchema, auth=JWTAuth())
async def link_document_to_disclosure(request, data: LinkDocumentSchema):
    """Poveži dokument z ESRS disclosure točko (ONE document can be linked to MULTIPLE disclosures)"""
    from accounts.models import DocumentEvidence, Document, ESRSDisclosure
    from django.db import IntegrityError

    logger.info(f"Link document: document_id={data.document_id}, disclosure_id={data.disclosure_id}, excluded={data.is_excluded}, user={request.auth.id}")

    try:
        # Verify document belongs to user
        document = await sync_to_async(
            Document.objects.get
        )(id=data.document_id, user=request.auth)

        disclosure = await sync_to_async(ESRSDisclosure.objects.get)(id=data.disclosure_id)
        
        # Check if this specific document is already linked to THIS disclosure
        existing = await sync_to_async(
            lambda: DocumentEvidence.objects.filter(
                document=document,
                disclosure=disclosure,
                user=request.auth
            ).first()
        )()
        
        if existing:
            # Already linked to THIS disclosure - update notes and is_excluded
            existing.notes = data.notes
            existing.is_excluded = data.is_excluded if data.is_excluded is not None else existing.is_excluded
            await sync_to_async(existing.save)()
            action = "excluded" if data.is_excluded else "updated"
            logger.info(f"Document evidence {action}: evidence_id={existing.id}, user={request.auth.id}")
            return {"message": f"Document evidence {action}", "success": True}

        # Create new link (document can be linked to multiple disclosures)
        evidence = DocumentEvidence(
            document=document,
            disclosure=disclosure,
            user=request.auth,
            notes=data.notes,
            is_excluded=data.is_excluded if data.is_excluded is not None else False
        )
        await sync_to_async(evidence.save)()
        logger.info(f"Document linked successfully: evidence_id={evidence.id}, document={document.file_name}, user={request.auth.id}")

        return {"message": "Document linked successfully", "success": True}

    except Document.DoesNotExist:
        logger.warning(f"Link document failed - document not found: document_id={data.document_id}, user={request.auth.id}")
        return JsonResponse({"message": "Document not found or access denied"}, status=404)
    except ESRSDisclosure.DoesNotExist:
        logger.warning(f"Link document failed - disclosure not found: disclosure_id={data.disclosure_id}, user={request.auth.id}")
        return JsonResponse({"message": "Disclosure not found"}, status=404)
    except IntegrityError as e:
        # unique_together constraint violation
        logger.warning(f"Link document failed - already linked: document_id={data.document_id}, disclosure_id={data.disclosure_id}, user={request.auth.id}")
        return JsonResponse({
            "message": "Document is already linked to this disclosure",
            "success": False
        }, status=400)


@api.get("/esrs/linked-documents/{disclosure_id}", response=list[DocumentEvidenceSchema], auth=JWTAuth())
async def get_linked_documents(request, disclosure_id: int):
    """Pridobi vse dokumente povezane z disclosure točko (excluding excluded global documents)"""
    from accounts.models import DocumentEvidence
    
    evidence_list = await sync_to_async(list)(
        DocumentEvidence.objects.filter(
            disclosure_id=disclosure_id,
            user=request.auth,
            is_excluded=False  # Filter out excluded global documents
        ).select_related('document')
    )
    
    return [
        {
            'id': evidence.id,
            'document_id': evidence.document.id,
            'document': {
                'id': evidence.document.id,
                'file_name': evidence.document.file_name,
                'file_size': evidence.document.file_size,
                'file_type': evidence.document.file_type,
                'uploaded_at': evidence.document.uploaded_at,
                'is_global': evidence.document.is_global  # Include global flag
            },
            'linked_at': evidence.linked_at,
            'notes': evidence.notes
        }
        for evidence in evidence_list
    ]


@api.get("/esrs/excluded-documents/{disclosure_id}", response=list[DocumentEvidenceSchema], auth=JWTAuth())
async def get_excluded_documents(request, disclosure_id: int):
    """Get excluded global documents for this disclosure (user can re-link them)"""
    from accounts.models import DocumentEvidence
    
    evidence_list = await sync_to_async(list)(
        DocumentEvidence.objects.filter(
            disclosure_id=disclosure_id,
            user=request.auth,
            is_excluded=True,  # Only excluded documents
            document__is_global=True  # Only global documents
        ).select_related('document')
    )
    
    return [
        {
            'id': evidence.id,
            'document_id': evidence.document.id,
            'document': {
                'id': evidence.document.id,
                'file_name': evidence.document.file_name,
                'file_size': evidence.document.file_size,
                'file_type': evidence.document.file_type,
                'uploaded_at': evidence.document.uploaded_at,
                'is_global': evidence.document.is_global
            },
            'linked_at': evidence.linked_at,
            'notes': evidence.notes
        }
        for evidence in evidence_list
    ]


@api.delete("/esrs/unlink-document/{evidence_id}", response=MessageSchema, auth=JWTAuth())
async def unlink_document(request, evidence_id: int):
    """Exclude document from disclosure (for global docs) or unlink (for regular docs)"""
    from accounts.models import DocumentEvidence
    
    try:
        evidence = await sync_to_async(
            DocumentEvidence.objects.select_related('document').get
        )(id=evidence_id, user=request.auth)
        
        # For global documents, mark as excluded instead of deleting
        if evidence.document.is_global:
            evidence.is_excluded = True
            await sync_to_async(evidence.save)()
            return {"message": "Global document excluded successfully", "success": True}
        else:
            # For regular documents, delete the link
            await sync_to_async(evidence.delete)()
            return {"message": "Document unlinked successfully", "success": True}
    
    except DocumentEvidence.DoesNotExist:
        return JsonResponse({"message": "Evidence not found or access denied"}, status=404)


@api.post("/esrs/relink-document/{evidence_id}", response=MessageSchema, auth=JWTAuth())
async def relink_document(request, evidence_id: int):
    """Re-link an excluded global document (set is_excluded=False)"""
    from accounts.models import DocumentEvidence
    
    try:
        evidence = await sync_to_async(
            DocumentEvidence.objects.select_related('document').get
        )(id=evidence_id, user=request.auth, is_excluded=True)
        
        # Only allow re-linking global documents
        if not evidence.document.is_global:
            return JsonResponse({"message": "Only global documents can be re-linked"}, status=400)
        
        evidence.is_excluded = False
        await sync_to_async(evidence.save)()
        return {"message": "Global document re-linked successfully", "success": True}
    
    except DocumentEvidence.DoesNotExist:
        return JsonResponse({"message": "Evidence not found or already linked"}, status=404)


# ========== AI ANSWER ENDPOINT ==========

@api.post("/esrs/ai-answer", response=StartAITaskResponse, auth=JWTAuth())
async def get_ai_answer(request, data: GetAIAnswerSchema):
    """Zaženi Celery task za generiranje AI odgovora"""
    from accounts.models import ESRSDisclosure, AITaskStatus
    from accounts.tasks import generate_ai_answer_task

    logger.info(f"AI answer request: disclosure_id={data.disclosure_id}, model={data.model_id}, user={request.auth.id}")

    try:
        # Verify disclosure exists
        disclosure = await sync_to_async(ESRSDisclosure.objects.select_related('standard').get)(id=data.disclosure_id)

        # Generate task ID first
        from celery import uuid as celery_uuid
        task_id = celery_uuid()

        # Create task status record BEFORE starting task (to avoid race condition)
        task_status = await sync_to_async(AITaskStatus.objects.create)(
            task_id=task_id,
            user=request.auth,
            disclosure=disclosure,
            task_type='single',
            status='pending',
            progress=0,
            total_items=1,
            completed_items=0
        )
        logger.debug(f"AI task status created: task_id={task_id}, disclosure={disclosure.code}")

        # Start Celery task with selected model (using pre-generated task_id)
        task = generate_ai_answer_task.apply_async(
            args=(data.disclosure_id, request.auth.id, data.ai_temperature, data.model_id),
            task_id=task_id
        )
        logger.info(f"AI answer task started: task_id={task.id}, disclosure={disclosure.code}, model={data.model_id}")

        return StartAITaskResponse(
            task_id=task.id,
            message=f"AI answer generation started for {disclosure.code} using {data.model_id}"
        )

    except ESRSDisclosure.DoesNotExist:
        logger.error(f"AI answer failed - disclosure not found: disclosure_id={data.disclosure_id}, user={request.auth.id}")
        return JsonResponse({"message": "Disclosure not found"}, status=404)
    except Exception as e:
        logger.exception(f"AI answer failed with exception: disclosure_id={data.disclosure_id}, user={request.auth.id}")
        return JsonResponse({"message": f"Error starting AI task: {str(e)}"}, status=500)


@api.post("/esrs/extract-charts/{disclosure_id}", response=MessageSchema, auth=JWTAuth())
async def extract_charts(request, disclosure_id: int):
    """Extract charts and tables from existing AI answer"""
    from accounts.models import ESRSUserResponse, ESRSDisclosure
    from accounts.openai_service import OpenAIService
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        disclosure = await sync_to_async(ESRSDisclosure.objects.get)(id=disclosure_id)
        user_response = await sync_to_async(ESRSUserResponse.objects.get)(
            user=request.auth, disclosure=disclosure
        )
        
        if not user_response.ai_answer:
            return JsonResponse({"message": "No AI answer found", "success": False}, status=400)
        
        # Extract charts
        openai_service = OpenAIService()
        analytics = openai_service.extract_charts_from_answer(
            user_response.ai_answer, 
            disclosure.code
        )
        
        if analytics:
            user_response.chart_data = analytics.get('charts')
            user_response.table_data = analytics.get('tables')
            user_response.numeric_data = analytics.get('numeric_data')
            await sync_to_async(user_response.save)()
            
            logger.info(f"Extracted {len(analytics.get('charts', []))} charts for disclosure {disclosure_id}")
            return {"message": "Charts extracted successfully", "success": True}
        else:
            return {"message": "No charts found in answer", "success": False}
    
    except ESRSUserResponse.DoesNotExist:
        return JsonResponse({"message": "AI answer not found", "success": False}, status=404)
    except ESRSDisclosure.DoesNotExist:
        return JsonResponse({"message": "Disclosure not found"}, status=404)
    except Exception as e:
        logger.error(f"Error extracting charts: {str(e)}")
        return JsonResponse({"message": f"Error: {str(e)}", "success": False}, status=500)


@api.post("/esrs/generate-image/{disclosure_id}", response=MessageSchema, auth=JWTAuth())
async def generate_image(request, disclosure_id: int, data: GenerateImageSchema):
    """Generate image with DALL-E based on prompt"""
    from accounts.models import ESRSUserResponse, ESRSDisclosure
    from openai import OpenAI
    import logging
    import base64
    import requests
    logger = logging.getLogger(__name__)
    
    try:
        disclosure = await sync_to_async(ESRSDisclosure.objects.get)(id=disclosure_id)
        user_response, created = await sync_to_async(
            lambda: ESRSUserResponse.objects.get_or_create(
                user=request.auth,
                disclosure=disclosure,
                defaults={'ai_temperature': 0.2}
            )
        )()
        
        prompt = data.prompt
        
        # Call DALL-E
        client = OpenAI()
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )
        
        image_url = response.data[0].url
        
        # Download and convert to base64
        img_response = requests.get(image_url)
        img_base64 = base64.b64encode(img_response.content).decode('utf-8')
        
        # Save to response (we'll add generated_image field to model)
        if not user_response.chart_data:
            user_response.chart_data = []
        
        # Add as a special chart type
        user_response.chart_data.append({
            'id': f'img_{len(user_response.chart_data) + 1}',
            'type': 'image',
            'title': 'AI Generated Image',
            'image_base64': img_base64,
            'prompt': prompt,
            'selected_for_report': True
        })
        
        await sync_to_async(user_response.save)()
        
        logger.info(f"Generated image for disclosure {disclosure_id}")
        return {"message": "Image generated successfully", "success": True}
    
    except ESRSDisclosure.DoesNotExist:
        return JsonResponse({"message": "Disclosure not found"}, status=404)
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}")
        return JsonResponse({"message": f"Error: {str(e)}", "success": False}, status=500)


@api.post("/esrs/update-chart", response=MessageSchema, auth=JWTAuth())
async def update_chart(request, payload: UpdateChartSchema):
    """Update a specific chart in disclosure and create new version"""
    from accounts.models import ESRSUserResponse, ItemVersion
    import logging
    import json
    logger = logging.getLogger(__name__)
    
    logger.info(f"🔍 Received chart update request")
    logger.info(f"📊 Full request data: {payload.dict()}")
    
    try:
        disclosure_id = payload.disclosure_id
        chart_id = payload.chart_id
        chart_data = payload.chart_data
        
        logger.info(f"✅ disclosure_id: {disclosure_id}")
        logger.info(f"✅ chart_id: {chart_id}")
        logger.info(f"📈 chart_data type: {type(chart_data)}")
        logger.info(f"📈 chart_data: {json.dumps(chart_data, indent=2) if chart_data else None}")
        
        if not all([disclosure_id, chart_id, chart_data]):
            logger.error(f"❌ Missing fields: disclosure_id={disclosure_id}, chart_id={chart_id}, chart_data={bool(chart_data)}")
            return JsonResponse({"message": "Missing required fields", "success": False}, status=400)
        
        # Get user response
        user_response = await sync_to_async(
            lambda: ESRSUserResponse.objects.get(
                user=request.auth,
                disclosure_id=disclosure_id
            )
        )()
        
        if not user_response.chart_data:
            return JsonResponse({"message": "No charts found", "success": False}, status=404)
        
        # Find and update the chart
        chart_found = False
        updated_chart = None
        for i, chart in enumerate(user_response.chart_data):
            if chart.get('id') == chart_id:
                user_response.chart_data[i] = {**chart, **chart_data}
                updated_chart = user_response.chart_data[i]
                chart_found = True
                break
        
        if not chart_found:
            return JsonResponse({"message": "Chart not found", "success": False}, status=404)
        
        await sync_to_async(user_response.save)()
        
        # Create new ItemVersion for manual chart edit
        max_version = await sync_to_async(
            lambda: ItemVersion.objects.filter(
                item_type='CHART',
                item_id=user_response.id,
                user=request.auth
            ).aggregate(models.Max('version_number'))['version_number__max'] or 0
        )()
        
        # Find parent version (current selected version)
        parent_version = await sync_to_async(
            lambda: ItemVersion.objects.filter(
                item_type='CHART',
                item_id=user_response.id,
                is_selected=True
            ).first()
        )()
        
        new_version = await sync_to_async(ItemVersion.objects.create)(
            user=request.auth,
            disclosure_id=disclosure_id,
            item_type='CHART',
            item_id=user_response.id,
            version_number=max_version + 1,
            parent_version=parent_version,
            change_type='MANUAL_EDIT',
            change_description=f"Manually edited chart: {updated_chart.get('title', 'Chart')}",
            content=updated_chart,
            conversation=None,
            is_selected=True,  # Make this the active version
            created_by_user=True
        )
        
        # Deselect old version
        if parent_version:
            parent_version.is_selected = False
            await sync_to_async(parent_version.save)()
        
        logger.info(f"Updated chart {chart_id} for disclosure {disclosure_id}, created version {new_version.version_number}")
        
        return {"message": "Chart updated successfully", "success": True}
    
    except ESRSUserResponse.DoesNotExist:
        return JsonResponse({"message": "Response not found", "success": False}, status=404)
    except Exception as e:
        logger.error(f"Error updating chart: {str(e)}")
        return JsonResponse({"message": f"Error: {str(e)}", "success": False}, status=500)


@api.post("/esrs/update-table", response=MessageSchema, auth=JWTAuth())
async def update_table(request, payload: UpdateTableSchema):
    """Update a specific table in disclosure and create new version"""
    from accounts.models import ESRSUserResponse, ItemVersion
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        disclosure_id = payload.disclosure_id
        table_id = payload.table_id
        table_data = payload.table_data
        
        if not all([disclosure_id, table_id is not None, table_data]):
            return JsonResponse({"message": "Missing required fields", "success": False}, status=400)
        
        # Get user response
        user_response = await sync_to_async(
            lambda: ESRSUserResponse.objects.get(
                user=request.auth,
                disclosure_id=disclosure_id
            )
        )()
        
        if not user_response.table_data:
            return JsonResponse({"message": "No tables found", "success": False}, status=404)
        
        # Find and update the table
        table_found = False
        updated_table = None
        for i, table in enumerate(user_response.table_data):
            if table.get('id') == table_id:
                user_response.table_data[i] = {**table, **table_data}
                updated_table = user_response.table_data[i]
                table_found = True
                break
        
        if not table_found:
            return JsonResponse({"message": "Table not found", "success": False}, status=404)
        
        await sync_to_async(user_response.save)()
        
        # Create new ItemVersion for manual table edit
        max_version = await sync_to_async(
            lambda: ItemVersion.objects.filter(
                item_type='TABLE',
                item_id=user_response.id,
                user=request.auth
            ).aggregate(models.Max('version_number'))['version_number__max'] or 0
        )()
        
        # Find parent version (current selected version)
        parent_version = await sync_to_async(
            lambda: ItemVersion.objects.filter(
                item_type='TABLE',
                item_id=user_response.id,
                is_selected=True
            ).first()
        )()
        
        new_version = await sync_to_async(ItemVersion.objects.create)(
            user=request.auth,
            disclosure_id=disclosure_id,
            item_type='TABLE',
            item_id=user_response.id,
            version_number=max_version + 1,
            parent_version=parent_version,
            change_type='MANUAL_EDIT',
            change_description=f"Manually edited table: {updated_table.get('title', 'Table')}",
            content=updated_table,
            conversation=None,
            is_selected=True,  # Make this the active version
            created_by_user=True
        )
        
        # Deselect old version
        if parent_version:
            parent_version.is_selected = False
            await sync_to_async(parent_version.save)()
        
        logger.info(f"Updated table {table_id} for disclosure {disclosure_id}, created version {new_version.version_number}")
        
        return {"message": "Table updated successfully", "success": True}
    
    except ESRSUserResponse.DoesNotExist:
        return JsonResponse({"message": "Response not found", "success": False}, status=404)
    except Exception as e:
        logger.error(f"Error updating table: {str(e)}")
        return JsonResponse({"message": f"Error: {str(e)}", "success": False}, status=500)


# ==================== VERSION SYSTEM & AI REFINEMENT ====================

@api.post("/conversations/start", auth=JWTAuth())
async def start_conversation(request, data: StartConversationSchema):
    """Start a new AI conversation for refining content"""
    from accounts.models import AIConversation, ESRSDisclosure
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        disclosure = await sync_to_async(ESRSDisclosure.objects.get)(id=data.disclosure_id)
        
        conversation = await sync_to_async(AIConversation.objects.create)(
            user=request.auth,
            disclosure=disclosure,
            item_type=data.item_type,
            item_id=data.item_id,
            messages=[]
        )
        
        return {
            "id": str(conversation.id),
            "item_type": conversation.item_type,
            "item_id": conversation.item_id,
            "messages": [],
            "created_at": conversation.created_at.isoformat()
        }
    except ESRSDisclosure.DoesNotExist:
        return JsonResponse({"message": "Disclosure not found"}, status=404)
    except Exception as e:
        logger.error(f"Error starting conversation: {str(e)}")
        return JsonResponse({"message": f"Error: {str(e)}"}, status=500)


@api.get("/conversations/{item_type}/{item_id}", auth=JWTAuth())
async def get_conversation(request, item_type: str, item_id: int):
    """Get existing conversation for an item"""
    from accounts.models import AIConversation
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        conversation = await sync_to_async(
            AIConversation.objects.filter(
                user=request.auth,
                item_type=item_type.upper(),
                item_id=item_id
            ).first
        )()
        
        if not conversation:
            return JsonResponse({"message": "No conversation found"}, status=404)
        
        return {
            "id": str(conversation.id),
            "item_type": conversation.item_type,
            "item_id": conversation.item_id,
            "messages": conversation.messages,
            "created_at": conversation.created_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Error loading conversation: {str(e)}")
        return JsonResponse({"message": f"Error: {str(e)}"}, status=500)


@api.post("/conversations/{conversation_id}/message", auth=JWTAuth())
async def send_message(request, conversation_id: str, data: SendMessageSchema):
    """Send a message in conversation and get AI response"""
    from accounts.models import AIConversation, ItemVersion, ESRSUserResponse
    from openai import OpenAI
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        conversation = await sync_to_async(AIConversation.objects.get)(
            id=conversation_id, user=request.auth
        )
        
        # Add user message to conversation
        user_message = {
            "role": "user",
            "content": data.message,
            "timestamp": sync_to_async(lambda: None)()  # Will be set by Django
        }
        conversation.messages.append(user_message)
        await sync_to_async(conversation.save)()
        
        # Get current content to refine
        if conversation.item_type == 'TEXT':
            user_response = await sync_to_async(ESRSUserResponse.objects.get)(
                id=conversation.item_id
            )
            current_content = user_response.ai_answer or user_response.manual_answer or ""
            context = f"Disclosure: {user_response.disclosure.requirement_text}"
        else:
            # For charts/images/tables, get from ItemVersion
            selected_version = await sync_to_async(
                ItemVersion.objects.filter(
                    item_type=conversation.item_type,
                    item_id=conversation.item_id,
                    is_selected=True
                ).first
            )()
            if selected_version:
                current_content = selected_version.content
            else:
                return JsonResponse({"message": "No version found"}, status=404)
            context = ""
        
        # Call OpenAI for refinement
        client = OpenAI()
        
        system_prompt = f"""You are an AI assistant helping to refine content for ESRS sustainability reporting.
        
{context}

Current content:
{current_content if isinstance(current_content, str) else str(current_content)}

User wants to refine this content. Follow their instructions while maintaining accuracy and compliance."""
        
        response = client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": data.message}
            ],
            temperature=0.3
        )
        
        ai_response = response.choices[0].message.content
        
        # Add AI response to conversation
        ai_message = {
            "role": "assistant",
            "content": ai_response,
            "timestamp": sync_to_async(lambda: None)()
        }
        conversation.messages.append(ai_message)
        await sync_to_async(conversation.save)()
        
        # Create new version
        if conversation.item_type == 'TEXT':
            # Get or create parent version
            parent_version = await sync_to_async(
                ItemVersion.objects.filter(
                    item_type='TEXT',
                    item_id=conversation.item_id,
                    user=request.auth
                ).order_by('-version_number').first
            )()
            
            if not parent_version:
                # Create initial version from current content
                parent_version = await sync_to_async(ItemVersion.objects.create)(
                    user=request.auth,
                    disclosure=conversation.disclosure,
                    item_type='TEXT',
                    item_id=conversation.item_id,
                    version_number=1,
                    change_type='INITIAL',
                    change_description='Initial version',
                    content={"text": current_content, "format": "markdown"},
                    is_selected=True,
                    created_by_user=False
                )
            
            # Create new refined version
            max_version = await sync_to_async(
                lambda: ItemVersion.objects.filter(
                    item_type='TEXT',
                    item_id=conversation.item_id,
                    user=request.auth
                ).aggregate(models.Max('version_number'))['version_number__max'] or 0
            )()
            
            new_version = await sync_to_async(ItemVersion.objects.create)(
                user=request.auth,
                disclosure=conversation.disclosure,
                item_type='TEXT',
                item_id=conversation.item_id,
                version_number=max_version + 1,
                parent_version=parent_version,
                change_type='AI_REFINEMENT',
                change_description=data.message[:100],  # First 100 chars of instruction
                content={"text": ai_response, "format": "markdown"},
                conversation=conversation,
                is_selected=False,
                created_by_user=False
            )
            
            logger.info(f"Created version {new_version.version_number} for TEXT item {conversation.item_id}")
        
        return {
            "message": ai_response,
            "version_id": str(new_version.id) if conversation.item_type == 'TEXT' else None,
            "conversation_id": str(conversation.id)
        }
        
    except AIConversation.DoesNotExist:
        return JsonResponse({"message": "Conversation not found"}, status=404)
    except Exception as e:
        logger.error(f"Error in conversation: {str(e)}", exc_info=True)
        return JsonResponse({"message": f"Error: {str(e)}"}, status=500)


@api.get("/versions/{item_type}/{item_id}", auth=JWTAuth())
async def get_versions(request, item_type: str, item_id: int):
    """Get all versions for an item"""
    from accounts.models import ItemVersion
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        versions = await sync_to_async(list)(
            ItemVersion.objects.filter(
                item_type=item_type,
                item_id=item_id,
                user=request.auth
            ).select_related('parent_version').order_by('-version_number')
        )
        
        # Build version data without triggering lazy loads
        version_data = []
        for v in versions:
            # Access parent_version_id directly to avoid lazy loading
            parent_id = v.parent_version_id
            
            # Get created_by email if available
            created_by_email = None
            if v.created_by_id:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                try:
                    creator = await sync_to_async(User.objects.get)(id=v.created_by_id)
                    created_by_email = creator.email
                except:
                    pass
            
            version_data.append({
                "id": str(v.id),
                "version_number": v.version_number,
                "change_type": v.change_type,
                "change_description": v.change_description,
                "content": v.content,
                "is_selected": v.is_selected,
                "created_at": v.created_at.isoformat(),
                "created_by_user": v.created_by_user,
                "created_by_email": created_by_email,
                "parent_version_id": str(parent_id) if parent_id else None,
                "conversation_id": None  # conversation field nullable
            })
        
        return {"versions": version_data}
    except Exception as e:
        logger.error(f"Error getting versions for {item_type}/{item_id}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return JsonResponse({"message": f"Error: {str(e)}"}, status=500)


@api.post("/versions/select", auth=JWTAuth())
async def select_version(request, data: SelectVersionSchema):
    """Select a version as the active one"""
    from accounts.models import ItemVersion, ESRSUserResponse
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        version = await sync_to_async(ItemVersion.objects.get)(
            id=data.version_id,
            user=request.auth
        )
        
        # Deselect all other versions
        await sync_to_async(
            ItemVersion.objects.filter(
                item_type=version.item_type,
                item_id=version.item_id,
                user=request.auth
            ).update
        )(is_selected=False)
        
        # Select this version
        version.is_selected = True
        await sync_to_async(version.save)()
        
        # Update ESRSUserResponse with selected text version
        if version.item_type == 'TEXT':
            user_response = await sync_to_async(ESRSUserResponse.objects.get)(id=version.item_id)
            user_response.manual_answer = version.content.get('text', '')
            await sync_to_async(user_response.save)()
        
        logger.info(f"Selected version {version.version_number} for {version.item_type} item {version.item_id}")
        
        return {"message": "Version selected successfully", "version_id": str(version.id)}
        
    except ItemVersion.DoesNotExist:
        return JsonResponse({"message": "Version not found"}, status=404)
    except Exception as e:
        logger.error(f"Error selecting version: {str(e)}")
        return JsonResponse({"message": f"Error: {str(e)}"}, status=500)


@api.delete("/versions/{version_id}", auth=JWTAuth())
async def delete_version(request, version_id: str):
    """Delete a version (but not if it's selected or has children)"""
    from accounts.models import ItemVersion
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        version = await sync_to_async(ItemVersion.objects.get)(
            id=version_id,
            user=request.auth
        )
        
        # Check if version is selected
        if version.is_selected:
            return JsonResponse({
                "message": "Cannot delete selected version. Please select another version first."
            }, status=400)
        
        # Check if version has children
        has_children = await sync_to_async(
            lambda: ItemVersion.objects.filter(parent_version=version).exists()
        )()
        
        if has_children:
            return JsonResponse({
                "message": "Cannot delete version that has child versions. Delete children first."
            }, status=400)
        
        # Delete version
        version_number = version.version_number
        await sync_to_async(version.delete)()
        
        logger.info(f"Deleted version {version_number} (ID: {version_id})")
        
        return {"message": "Version deleted successfully"}
        
    except ItemVersion.DoesNotExist:
        return JsonResponse({"message": "Version not found"}, status=404)
    except Exception as e:
        logger.error(f"Error deleting version: {str(e)}", exc_info=True)
        return JsonResponse({"message": f"Error: {str(e)}"}, status=500)


@api.post("/esrs/bulk-ai-answer/{standard_id}", response=StartAITaskResponse, auth=JWTAuth())
async def get_bulk_ai_answers(request, standard_id: int):
    """Zaženi Celery task za generiranje AI odgovorov za VSE disclosure točke v standardu"""
    from accounts.models import ESRSStandard, ESRSDisclosure, AITaskStatus
    from accounts.tasks import generate_bulk_ai_answers_task

    logger.info(f"Bulk AI answer request: standard_id={standard_id}, user={request.auth.id}")

    try:
        # Verify standard exists
        standard = await sync_to_async(ESRSStandard.objects.get)(id=standard_id)

        # Count disclosures
        disclosure_count = await sync_to_async(
            lambda: ESRSDisclosure.objects.filter(standard=standard).count()
        )()
        logger.info(f"Starting bulk AI task for {disclosure_count} disclosures in standard {standard.code}")

        # Create task status record FIRST, then start Celery task
        # This prevents race condition where task tries to fetch status before it's created
        import uuid
        task_id = str(uuid.uuid4())

        task_status = await sync_to_async(AITaskStatus.objects.create)(
            task_id=task_id,
            user=request.auth,
            standard=standard,
            task_type='bulk',
            status='pending',
            progress=0,
            total_items=disclosure_count,
            completed_items=0
        )

        # Now start Celery task with the pre-created task_id
        task = generate_bulk_ai_answers_task.apply_async(
            args=[standard_id, request.auth.id],
            task_id=task_id
        )

        logger.info(f"Bulk AI task started: task_id={task.id}, standard={standard.code}, count={disclosure_count}, user={request.auth.id}")

        return StartAITaskResponse(
            task_id=task.id,
            message=f"Bulk AI generation started for {standard.code} ({disclosure_count} disclosures)"
        )

    except ESRSStandard.DoesNotExist:
        logger.error(f"Bulk AI failed - standard not found: standard_id={standard_id}, user={request.auth.id}")
        return JsonResponse({"message": "Standard not found"}, status=404)
    except Exception as e:
        logger.exception(f"Bulk AI failed with exception: standard_id={standard_id}, user={request.auth.id}")
        return JsonResponse({"message": f"Error starting bulk AI task: {str(e)}"}, status=500)


@api.get("/esrs/task-status/{task_id}", response=AITaskStatusSchema, auth=JWTAuth())
async def get_task_status(request, task_id: str):
    """Pridobi status Celery taska"""
    from accounts.models import AITaskStatus
    
    try:
        task_status = await sync_to_async(
            AITaskStatus.objects.select_related('disclosure', 'standard').get
        )(task_id=task_id, user=request.auth)
        
        # Prepare response with disclosure/standard codes
        response_data = {
            'id': task_status.id,
            'task_id': task_status.task_id,
            'task_type': task_status.task_type,
            'status': task_status.status,
            'progress': task_status.progress,
            'total_items': task_status.total_items,
            'completed_items': task_status.completed_items,
            'result': task_status.result,
            'error_message': task_status.error_message,
            'disclosure_code': task_status.disclosure.code if task_status.disclosure else None,
            'standard_code': task_status.standard.code if task_status.standard else None,
            'current_step': task_status.current_step,
            'steps_completed': task_status.steps_completed,
            'processing_steps': task_status.processing_steps,  # TIER RAG steps for UI
            'documents_used': task_status.documents_used,
            'chunks_used': task_status.chunks_used,
            'confidence_score': task_status.confidence_score,
            'reasoning_summary': task_status.reasoning_summary,  # AI reasoning from o1/Claude
            'created_at': task_status.created_at,
            'updated_at': task_status.updated_at
        }
        
        return AITaskStatusSchema(**response_data)
        
    except AITaskStatus.DoesNotExist:
        return JsonResponse({"message": "Task not found"}, status=404)
    except Exception as e:
        return JsonResponse({"message": f"Error: {str(e)}"}, status=500)


@api.get("/esrs/active-tasks", response=list[AITaskStatusSchema], auth=JWTAuth())
async def get_active_tasks(request):
    """Pridobi vse aktivne Celery taske za trenutnega uporabnika"""
    from accounts.models import AITaskStatus
    
    try:
        # Get tasks that are pending or running
        active_tasks = await sync_to_async(list)(
            AITaskStatus.objects.filter(
                user=request.auth,
                status__in=['pending', 'running']
            ).select_related('disclosure', 'standard', 'document').order_by('-created_at')
        )
        
        # Prepare response
        result = []
        for task in active_tasks:
            result.append(AITaskStatusSchema(
                id=task.id,
                task_id=task.task_id,
                task_type=task.task_type,
                status=task.status,
                progress=task.progress,
                total_items=task.total_items,
                completed_items=task.completed_items,
                result=task.result,
                error_message=task.error_message,
                disclosure_code=task.disclosure.code if task.disclosure else None,
                standard_code=task.standard.code if task.standard else None,
                document_name=task.document.file_name if task.document else None,
                created_at=task.created_at,
                updated_at=task.updated_at
            ))
        
        return result
        
    except Exception as e:
        return JsonResponse({"message": f"Error: {str(e)}"}, status=500)


# ========== ADMIN ENDPOINTS ==========

@api.get("/admin/statistics", auth=AdminAuth())
async def get_admin_statistics(request):
    """Get system statistics - admin only"""
    from accounts.models import User, Document, ESRSUserResponse, ItemVersion, AIConversation
    from django.db.models import Count, Q, Sum
    from datetime import datetime, timedelta
    
    
    total_users = await sync_to_async(User.objects.count)()
    total_companies = await sync_to_async(
        User.objects.filter(company_type__isnull=False).count
    )()
    total_documents = await sync_to_async(Document.objects.count)()
    total_ai_answers = await sync_to_async(
        ESRSUserResponse.objects.filter(ai_answer__isnull=False).count
    )()
    
    # New: Version statistics
    total_versions = await sync_to_async(ItemVersion.objects.count)()
    ai_refinements = await sync_to_async(
        ItemVersion.objects.filter(change_type='AI_REFINEMENT').count
    )()
    manual_edits = await sync_to_async(
        ItemVersion.objects.filter(created_by_user=True).count
    )()
    
    # New: Conversation statistics
    total_conversations = await sync_to_async(AIConversation.objects.count)()
    
    # Active users (last 7 days)
    week_ago = datetime.now() - timedelta(days=7)
    active_users = await sync_to_async(
        ItemVersion.objects.filter(created_at__gte=week_ago)
            .values('user').distinct().count
    )()
    
    return {
        "total_users": total_users,
        "total_companies": total_companies,
        "total_documents": total_documents,
        "total_ai_answers": total_ai_answers,
        "total_versions": total_versions,
        "ai_refinements": ai_refinements,
        "manual_edits": manual_edits,
        "total_conversations": total_conversations,
        "active_users_7_days": active_users
    }


@api.get("/admin/users", auth=AdminAuth())
async def get_all_users(request):
    """Get all users with statistics - admin only"""
    from accounts.models import User, Document, ESRSUserResponse, ItemVersion
    from django.db.models import Count, Q
    
    users = await sync_to_async(lambda: list(
        User.objects.annotate(
            document_count=Count('documents'),
            ai_answer_count=Count('esrs_responses', filter=Q(esrs_responses__ai_answer__isnull=False)),
            version_count=Count('item_versions'),
            ai_refinement_count=Count('item_versions', filter=Q(item_versions__change_type='AI_REFINEMENT'))
        ).values(
            'id', 'email', 'username', 'company_type', 'allowed_standards',
            'wizard_completed', 'date_joined', 'is_active',
            'document_count', 'ai_answer_count', 'version_count', 'ai_refinement_count'
        ).order_by('-date_joined')
    ))()
    
    return users


@api.put("/admin/users/{user_id}/allowed-standards", response=MessageSchema, auth=AdminAuth())
async def update_user_allowed_standards(request, user_id: int, allowed_standards: list[str]):
    """Update user's allowed standards - admin only"""
    from accounts.models import User
    
    
    def update_standards():
        try:
            user = User.objects.get(id=user_id)
            user.allowed_standards = allowed_standards
            user.save()
            return {
                "message": f"Updated allowed standards for {user.email}",
                "success": True
            }
        except User.DoesNotExist:
            return {"message": "User not found", "success": False}
    
    return await sync_to_async(update_standards)()


@api.post("/admin/prompts/{standard_id}", response=MessageSchema, auth=AdminAuth())
async def update_ai_prompt(request, standard_id: int, data: dict):
    """Update AI prompt template for ESRS standard - admin only"""
    from accounts.models import ESRSStandard
    
    
    try:
        standard = await sync_to_async(ESRSStandard.objects.get)(id=standard_id)
        standard.ai_prompt = data.get('ai_prompt', '')
        await sync_to_async(standard.save)()
        
        return {"message": "AI prompt updated successfully", "success": True}
    
    except ESRSStandard.DoesNotExist:
        return JsonResponse({"message": "Standard not found"}, status=404)


@api.get("/admin/disclosure/{disclosure_id}/prompt", auth=AdminAuth())
async def get_disclosure_prompt(request, disclosure_id: int):
    """Get AI prompt for specific disclosure - admin only"""
    from accounts.models import ESRSDisclosure
    
    
    try:
        disclosure = await sync_to_async(
            ESRSDisclosure.objects.select_related('standard').get
        )(id=disclosure_id)
        
        return {
            'disclosure_id': disclosure.id,
            'code': disclosure.code,
            'name': disclosure.name,
            'requirement_text': disclosure.requirement_text,
            'ai_prompt': disclosure.ai_prompt or '',
            'has_custom_prompt': bool(disclosure.ai_prompt)
        }
    
    except ESRSDisclosure.DoesNotExist:
        return JsonResponse({"message": "Disclosure not found"}, status=404)


@api.put("/admin/disclosure/{disclosure_id}/prompt", response=MessageSchema, auth=AdminAuth())
async def update_disclosure_prompt(request, disclosure_id: int, data: dict):
    """Update AI prompt for specific disclosure - admin only"""
    from accounts.models import ESRSDisclosure
    
    
    try:
        disclosure = await sync_to_async(ESRSDisclosure.objects.get)(id=disclosure_id)
        
        # If ai_prompt is empty string, set to None (use default)
        new_prompt = data.get('ai_prompt', '').strip()
        disclosure.ai_prompt = new_prompt if new_prompt else None
        
        await sync_to_async(disclosure.save)()
        
        return {
            "message": "Disclosure AI prompt updated successfully",
            "success": True,
            "using_custom": bool(disclosure.ai_prompt)
        }
    
    except ESRSDisclosure.DoesNotExist:
        return JsonResponse({"message": "Disclosure not found"}, status=404)


@api.post("/admin/settings", response=MessageSchema, auth=AdminAuth())
async def update_system_settings(request, data: dict):
    """Update system settings - admin only"""
    
    # Store settings in database or config file
    # For now, just return success
    return {"message": "Settings updated successfully", "success": True}


# ========== RAG ADMIN ENDPOINTS ==========

@api.get("/admin/rag/overview", auth=AdminAuth())
async def get_rag_overview(request):
    """Get RAG system overview with key metrics - admin only"""
    from accounts.vector_models import DocumentChunk, SearchQuery, EmbeddingModel, RerankerModel
    from django.db.models import Avg, Count, F, FloatField, ExpressionWrapper
    
    
    try:
        # Total documents and chunks
        total_documents = await sync_to_async(Document.objects.count)()
        total_chunks = await sync_to_async(DocumentChunk.objects.count)()
        total_searches = await sync_to_async(SearchQuery.objects.count)()
        
        # Performance metrics
        avg_retrieval_time = await sync_to_async(
            lambda: SearchQuery.objects.aggregate(avg_time=Avg('retrieval_time_ms'))['avg_time'] or 0
        )()
        
        avg_reranking_time = await sync_to_async(
            lambda: SearchQuery.objects.aggregate(avg_time=Avg('reranking_time_ms'))['avg_time'] or 0
        )()
        
        # Hit rate
        searches_with_hits = await sync_to_async(
            lambda: SearchQuery.objects.filter(has_relevant_doc=True).count()
        )()
        hit_rate = (searches_with_hits / total_searches * 100) if total_searches > 0 else 0
        
        # Average MRR
        avg_mrr = await sync_to_async(
            lambda: SearchQuery.objects.filter(
                first_relevant_rank__isnull=False
            ).annotate(
                mrr=ExpressionWrapper(1.0 / F('first_relevant_rank'), output_field=FloatField())
            ).aggregate(avg_mrr=Avg('mrr'))['avg_mrr'] or 0
        )()
        
        # RAG Triad metrics
        avg_context_relevance = await sync_to_async(
            lambda: SearchQuery.objects.filter(
                context_relevance__isnull=False
            ).aggregate(avg=Avg('context_relevance'))['avg'] or 0
        )()
        
        avg_groundedness = await sync_to_async(
            lambda: SearchQuery.objects.filter(
                groundedness__isnull=False
            ).aggregate(avg=Avg('groundedness'))['avg'] or 0
        )()
        
        avg_answer_relevance = await sync_to_async(
            lambda: SearchQuery.objects.filter(
                answer_relevance__isnull=False
            ).aggregate(avg=Avg('answer_relevance'))['avg'] or 0
        )()
        
        # Active models
        active_embeddings = await sync_to_async(
            lambda: list(EmbeddingModel.objects.filter(is_active=True).values(
                'id', 'name', 'provider', 'dimensions', 'avg_hit_rate', 'total_queries', 'is_default'
            ))
        )()
        
        active_rerankers = await sync_to_async(
            lambda: list(RerankerModel.objects.filter(is_active=True).values(
                'id', 'name', 'provider', 'avg_improvement', 'total_rerank_operations', 'is_default'
            ))
        )()
        
        return {
            "overview": {
                "total_documents": total_documents,
                "total_chunks": total_chunks,
                "total_searches": total_searches,
                "avg_chunks_per_doc": round(total_chunks / total_documents, 1) if total_documents > 0 else 0
            },
            "performance": {
                "hit_rate": round(hit_rate, 2),
                "avg_mrr": round(avg_mrr, 3),
                "avg_retrieval_time_ms": round(avg_retrieval_time, 1),
                "avg_reranking_time_ms": round(avg_reranking_time, 1),
                "avg_total_time_ms": round(avg_retrieval_time + avg_reranking_time, 1)
            },
            "quality": {
                "avg_context_relevance": round(avg_context_relevance, 3),
                "avg_groundedness": round(avg_groundedness, 3),
                "avg_answer_relevance": round(avg_answer_relevance, 3)
            },
            "models": {
                "embeddings": active_embeddings,
                "rerankers": active_rerankers
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting RAG overview: {e}", exc_info=True)
        return JsonResponse({"message": str(e)}, status=500)


@api.get("/admin/rag/embedding-models", auth=AdminAuth())
async def get_embedding_models_list(request):
    """Get all embedding models with stats - admin only"""
    from accounts.vector_models import EmbeddingModel
    
    
    try:
        models = await sync_to_async(
            lambda: list(EmbeddingModel.objects.all().values(
                'id', 'name', 'provider', 'model_id', 'dimensions',
                'cost_per_1m_tokens', 'avg_hit_rate', 'avg_mrr',
                'avg_retrieval_time_ms', 'total_queries',
                'is_active', 'is_default', 'created_at'
            ).order_by('-is_default', '-is_active', 'provider'))
        )()
        
        return {"models": models, "total_count": len(models)}
    
    except Exception as e:
        logger.error(f"Error getting embedding models: {e}", exc_info=True)
        return JsonResponse({"message": str(e)}, status=500)


@api.post("/admin/rag/embedding-models/{model_id}/toggle", auth=AdminAuth())
async def toggle_embedding_model_active(request, model_id: int):
    """Toggle embedding model active status - admin only"""
    from accounts.vector_models import EmbeddingModel
    
    
    try:
        model = await sync_to_async(EmbeddingModel.objects.get)(id=model_id)
        model.is_active = not model.is_active
        await sync_to_async(model.save)()
        
        return {"success": True, "model_id": model_id, "is_active": model.is_active}
    
    except EmbeddingModel.DoesNotExist:
        return JsonResponse({"message": "Model not found"}, status=404)
    except Exception as e:
        logger.error(f"Error toggling model: {e}", exc_info=True)
        return JsonResponse({"message": str(e)}, status=500)


@api.post("/admin/rag/embedding-models/{model_id}/set-default", auth=AdminAuth())
async def set_default_embedding_model_api(request, model_id: int):
    """Set embedding model as default - admin only"""
    from accounts.vector_models import EmbeddingModel
    
    
    try:
        # Remove default from all models
        await sync_to_async(lambda: EmbeddingModel.objects.all().update(is_default=False))()
        
        # Set new default and activate
        model = await sync_to_async(EmbeddingModel.objects.get)(id=model_id)
        model.is_default = True
        model.is_active = True
        await sync_to_async(model.save)()
        
        return {"success": True, "model_id": model_id, "model_name": model.name}
    
    except EmbeddingModel.DoesNotExist:
        return JsonResponse({"message": "Model not found"}, status=404)
    except Exception as e:
        logger.error(f"Error setting default model: {e}", exc_info=True)
        return JsonResponse({"message": str(e)}, status=500)


# ========== USER ESRS PROGRESS ENDPOINTS ==========

@api.get("/admin/users/{user_id}/esrs-progress", auth=AdminAuth())
async def get_user_esrs_progress_admin(request, user_id: int):
    """Get detailed ESRS progress for specific user - admin only"""
    from accounts.models import ESRSStandard, ESRSDisclosure, ESRSUserResponse
    from django.db.models import Count, Q
    
    
    try:
        # Get user
        user = await sync_to_async(User.objects.get)(id=user_id)
        
        # Get all standards with disclosure counts
        standards = await sync_to_async(
            lambda: list(ESRSStandard.objects.annotate(
                total_disclosures=Count('disclosures'),
                user_answered=Count(
                    'disclosures__esrsuserresponse',
                    filter=Q(
                        disclosures__esrsuserresponse__user=user,
                        disclosures__esrsuserresponse__final_answer__isnull=False,
                        disclosures__esrsuserresponse__final_answer__gt=''
                    )
                ),
                ai_used=Count(
                    'disclosures__esrsuserresponse',
                    filter=Q(
                        disclosures__esrsuserresponse__user=user,
                        disclosures__esrsuserresponse__ai_answer__isnull=False,
                        disclosures__esrsuserresponse__ai_answer__gt=''
                    )
                ),
                manual_only=Count(
                    'disclosures__esrsuserresponse',
                    filter=Q(
                        disclosures__esrsuserresponse__user=user,
                        disclosures__esrsuserresponse__manual_answer__isnull=False,
                        disclosures__esrsuserresponse__manual_answer__gt='',
                        disclosures__esrsuserresponse__ai_answer__isnull=True
                    )
                )
            ).values(
                'id', 'code', 'name_en', 'category',
                'total_disclosures', 'user_answered', 'ai_used', 'manual_only'
            ).order_by('code'))
        )()
        
        # Calculate percentages
        for standard in standards:
            total = standard['total_disclosures']
            standard['completion_percentage'] = round(
                (standard['user_answered'] / total * 100) if total > 0 else 0, 1
            )
            standard['ai_usage_percentage'] = round(
                (standard['ai_used'] / total * 100) if total > 0 else 0, 1
            )
        
        # Overall stats
        total_disclosures = await sync_to_async(ESRSDisclosure.objects.count)()
        total_answered = await sync_to_async(
            lambda: ESRSUserResponse.objects.filter(
                user=user,
                final_answer__isnull=False,
                final_answer__gt=''
            ).count()
        )()
        total_ai_used = await sync_to_async(
            lambda: ESRSUserResponse.objects.filter(
                user=user,
                ai_answer__isnull=False,
                ai_answer__gt=''
            ).count()
        )()
        
        # Recent activity
        recent_responses = await sync_to_async(
            lambda: list(ESRSUserResponse.objects.filter(
                user=user,
                updated_at__isnull=False
            ).select_related(
                'disclosure', 'disclosure__standard'
            ).order_by('-updated_at')[:10].values(
                'disclosure__code',
                'disclosure__name_en',
                'disclosure__standard__code',
                'has_ai_answer',
                'has_manual_answer',
                'updated_at'
            ))
        )()
        
        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "company_name": user.company_name or "",
                "wizard_completed": user.wizard_completed
            },
            "overall": {
                "total_disclosures": total_disclosures,
                "total_answered": total_answered,
                "total_ai_used": total_ai_used,
                "completion_percentage": round(
                    (total_answered / total_disclosures * 100) if total_disclosures > 0 else 0, 1
                ),
                "ai_usage_percentage": round(
                    (total_ai_used / total_disclosures * 100) if total_disclosures > 0 else 0, 1
                )
            },
            "by_standard": standards,
            "recent_activity": recent_responses
        }
    
    except User.DoesNotExist:
        return JsonResponse({"message": "User not found"}, status=404)
    except Exception as e:
        logger.error(f"Error getting user ESRS progress: {e}", exc_info=True)
        return JsonResponse({"message": str(e)}, status=500)


@api.get("/admin/users/{user_id}/documents", auth=AdminAuth())
async def get_user_documents_admin(request, user_id: int):
    """Get all documents for user with RAG stats - admin only"""
    from accounts.vector_models import DocumentChunk
    from django.db.models import Count
    
    
    try:
        user = await sync_to_async(User.objects.get)(id=user_id)
        
        documents = await sync_to_async(
            lambda: list(Document.objects.filter(user=user).annotate(
                chunks_count=Count('documentchunk')
            ).values(
                'id', 'file_name', 'file_size', 'file_type',
                'uploaded_at', 'chunks_count'
            ).order_by('-uploaded_at'))
        )()
        
        # Format file sizes
        for doc in documents:
            size_bytes = doc['file_size']
            if size_bytes < 1024:
                doc['file_size_formatted'] = f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                doc['file_size_formatted'] = f"{size_bytes / 1024:.1f} KB"
            else:
                doc['file_size_formatted'] = f"{size_bytes / (1024 * 1024):.1f} MB"
        
        return {
            "user_id": user_id,
            "user_email": user.email,
            "documents": documents,
            "total_count": len(documents)
        }
    
    except User.DoesNotExist:
        return JsonResponse({"message": "User not found"}, status=404)
    except Exception as e:
        logger.error(f"Error getting user documents: {e}", exc_info=True)
        return JsonResponse({"message": str(e)}, status=500)


# ========== ADMIN ANALYTICS & STATISTICS ==========

@api.get("/admin/users/{user_id}/ai-usage", auth=AdminAuth())
async def get_user_ai_usage(request, user_id: int):
    """Get detailed AI usage statistics for user"""
    from accounts.models import ItemVersion, AIConversation
    from django.db.models import Count, Q
    import logging
    logger = logging.getLogger(__name__)
    
    
    try:
        user = await sync_to_async(User.objects.get)(id=user_id)
        
        # Count AI refinements
        ai_refinements = await sync_to_async(
            ItemVersion.objects.filter(
                user=user,
                change_type='AI_REFINEMENT'
            ).count
        )()
        
        # Count by item type
        version_stats = await sync_to_async(
            lambda: list(ItemVersion.objects.filter(
                user=user,
                change_type='AI_REFINEMENT'
            ).values('item_type').annotate(count=Count('id')))
        )()
        
        # Count conversations
        total_conversations = await sync_to_async(
            AIConversation.objects.filter(user=user).count
        )()
        
        # Count total messages in conversations
        conversations = await sync_to_async(
            lambda: list(AIConversation.objects.filter(user=user).values('messages'))
        )()
        
        total_messages = sum(len(conv['messages']) for conv in conversations if conv['messages'])
        
        # Estimate tokens and cost (rough estimates)
        # Assume avg 100 tokens per message, $0.01 per 1000 tokens
        estimated_tokens = total_messages * 100
        estimated_cost = (estimated_tokens / 1000) * 0.01
        
        return {
            "user_id": user_id,
            "email": user.email,
            "ai_refinements_total": ai_refinements,
            "refinements_by_type": {stat['item_type']: stat['count'] for stat in version_stats},
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "estimated_tokens": estimated_tokens,
            "estimated_cost_usd": round(estimated_cost, 2)
        }
        
    except User.DoesNotExist:
        return JsonResponse({"message": "User not found"}, status=404)
    except Exception as e:
        logger.error(f"Error getting AI usage: {e}", exc_info=True)
        return JsonResponse({"message": str(e)}, status=500)


@api.get("/admin/users/{user_id}/version-stats", auth=AdminAuth())
async def get_user_version_stats(request, user_id: int):
    """Get version history statistics for user"""
    from accounts.models import ItemVersion
    from django.db.models import Count, Avg
    import logging
    logger = logging.getLogger(__name__)
    
    
    try:
        user = await sync_to_async(User.objects.get)(id=user_id)
        
        # Total versions
        total_versions = await sync_to_async(
            ItemVersion.objects.filter(user=user).count
        )()
        
        # Versions by type
        by_type = await sync_to_async(
            lambda: list(ItemVersion.objects.filter(user=user)
                .values('item_type')
                .annotate(count=Count('id')))
        )()
        
        # Versions by change type
        by_change_type = await sync_to_async(
            lambda: list(ItemVersion.objects.filter(user=user)
                .values('change_type')
                .annotate(count=Count('id')))
        )()
        
        # Created by user vs AI
        manual_count = await sync_to_async(
            ItemVersion.objects.filter(user=user, created_by_user=True).count
        )()
        
        ai_count = await sync_to_async(
            ItemVersion.objects.filter(user=user, created_by_user=False).count
        )()
        
        # Average versions per item
        items_with_versions = await sync_to_async(
            lambda: ItemVersion.objects.filter(user=user)
                .values('item_type', 'item_id')
                .distinct()
                .count()
        )()
        
        avg_versions_per_item = round(total_versions / items_with_versions, 2) if items_with_versions > 0 else 0
        
        return {
            "user_id": user_id,
            "email": user.email,
            "total_versions": total_versions,
            "by_item_type": {stat['item_type']: stat['count'] for stat in by_type},
            "by_change_type": {stat['change_type']: stat['count'] for stat in by_change_type},
            "manual_edits": manual_count,
            "ai_generated": ai_count,
            "items_with_versions": items_with_versions,
            "avg_versions_per_item": avg_versions_per_item
        }
        
    except User.DoesNotExist:
        return JsonResponse({"message": "User not found"}, status=404)
    except Exception as e:
        logger.error(f"Error getting version stats: {e}", exc_info=True)
        return JsonResponse({"message": str(e)}, status=500)


@api.get("/admin/users/{user_id}/activity-timeline", auth=AdminAuth())
async def get_user_activity_timeline(request, user_id: int, days: int = 30):
    """Get user activity timeline (versions, responses, documents)"""
    from accounts.models import ItemVersion, ESRSUserResponse, Document
    from datetime import datetime, timedelta
    import logging
    logger = logging.getLogger(__name__)
    
    
    try:
        user = await sync_to_async(User.objects.get)(id=user_id)
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Recent versions
        recent_versions = await sync_to_async(
            lambda: list(ItemVersion.objects.filter(
                user=user,
                created_at__gte=start_date
            ).order_by('-created_at')[:50].values(
                'id', 'item_type', 'change_type', 'created_at',
                'created_by_user', 'version_number'
            ))
        )()
        
        # Recent responses
        recent_responses = await sync_to_async(
            lambda: list(ESRSUserResponse.objects.filter(
                user=user,
                updated_at__gte=start_date
            ).select_related('disclosure').order_by('-updated_at')[:50].values(
                'id', 'disclosure__code', 'ai_answer', 'manual_answer',
                'updated_at'
            ))
        )()
        
        # Recent documents
        recent_documents = await sync_to_async(
            lambda: list(Document.objects.filter(
                user=user,
                uploaded_at__gte=start_date
            ).order_by('-uploaded_at')[:20].values(
                'id', 'file_name', 'uploaded_at'
            ))
        )()
        
        # Combine into timeline
        timeline = []
        
        for v in recent_versions:
            timeline.append({
                "type": "version",
                "timestamp": v['created_at'].isoformat(),
                "data": {
                    "item_type": v['item_type'],
                    "change_type": v['change_type'],
                    "created_by": "User" if v['created_by_user'] else "AI",
                    "version_number": v['version_number']
                }
            })
        
        for r in recent_responses:
            has_ai = bool(r['ai_answer'])
            has_manual = bool(r['manual_answer'])
            timeline.append({
                "type": "response",
                "timestamp": r['updated_at'].isoformat(),
                "data": {
                    "disclosure_code": r['disclosure__code'],
                    "has_ai_answer": has_ai,
                    "has_manual_answer": has_manual
                }
            })
        
        for d in recent_documents:
            timeline.append({
                "type": "document",
                "timestamp": d['uploaded_at'].isoformat(),
                "data": {
                    "file_name": d['file_name']
                }
            })
        
        # Sort by timestamp descending
        timeline.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return {
            "user_id": user_id,
            "email": user.email,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            },
            "timeline": timeline[:100]  # Limit to 100 most recent
        }
        
    except User.DoesNotExist:
        return JsonResponse({"message": "User not found"}, status=404)
    except Exception as e:
        logger.error(f"Error getting activity timeline: {e}", exc_info=True)
        return JsonResponse({"message": str(e)}, status=500)


# ========== CHART MANAGEMENT ENDPOINTS ==========

@api.post("/esrs/toggle-chart-selection", response=ChartSelectionResponseSchema, auth=JWTAuth())
async def toggle_chart_selection(request, data: ToggleChartSelectionSchema):
    """Toggle chart selection for report"""
    from accounts.models import ESRSUserResponse
    
    try:
        response_obj = await sync_to_async(ESRSUserResponse.objects.get)(
            disclosure_id=data.disclosure_id,
            user=request.auth
        )
        
        if not response_obj.chart_data:
            return JsonResponse({"message": "No charts available"}, status=404)
        
        # Toggle selected_for_report flag
        selected_state = False
        for chart in response_obj.chart_data:
            if chart.get('id') == data.chart_id:
                chart['selected_for_report'] = not chart.get('selected_for_report', False)
                selected_state = chart['selected_for_report']
                break
        
        await sync_to_async(response_obj.save)()
        
        return {
            "message": "Chart selection updated",
            "selected_for_report": selected_state
        }
    
    except ESRSUserResponse.DoesNotExist:
        return JsonResponse({"message": "Response not found"}, status=404)
    except Exception as e:
        logger.error(f"Error toggling chart selection: {e}", exc_info=True)
        return JsonResponse({"message": str(e)}, status=500)


@api.post("/esrs/ai-edit-chart", response=MessageSchema, auth=JWTAuth())
async def ai_edit_chart(request, data: dict):
    """
    Use AI to edit chart labels/title based on user instruction
    
    IMPORTANT: Works with NEW JSON chart structure (array of {label, value, color} objects)
    NOT the old PNG chart structure!
    """
    import openai
    from django.conf import settings
    import json
    
    disclosure_id = data.get('disclosure_id')
    chart_id = data.get('chart_id')
    edit_instruction = data.get('user_instruction', '')
    
    if not disclosure_id or not chart_id or not edit_instruction:
        return JsonResponse({"message": "Missing required parameters"}, status=400)
    
    try:
        response_obj = await sync_to_async(ESRSUserResponse.objects.get)(
            disclosure_id=disclosure_id,
            user=request.auth
        )
        
        if not response_obj.chart_data:
            return JsonResponse({"message": "No charts available"}, status=404)
        
        # Find the chart
        target_chart = None
        chart_index = None
        for idx, chart in enumerate(response_obj.chart_data):
            if chart.get('id') == chart_id:
                target_chart = chart
                chart_index = idx
                break
        
        if not target_chart or not isinstance(target_chart.get('data'), list):
            return JsonResponse({"message": "Chart not found or has invalid format"}, status=404)
        
        # Extract current chart data (NEW JSON structure: array of {label, value, color})
        current_data = target_chart.get('data', [])
        labels = [item.get('label') for item in current_data]
        values = [item.get('value') for item in current_data]
        
        # Build AI prompt with Structured Outputs
        prompt = f"""You are editing a chart for ESRS reporting.

CURRENT CHART:
- Type: {target_chart.get('type')}
- Title: {target_chart.get('title')}
- Data: {json.dumps(current_data, indent=2)}

USER REQUEST: {edit_instruction}

Analyze the request and update the chart accordingly. You can:
1. Change the title
2. Change labels (e.g., "Women" → "Female employees")
3. Keep the same number of data points (values must match)

Return updated chart data."""

        # Use Structured Outputs to ensure valid JSON
        chart_update_schema = {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Updated chart title"
                },
                "data": {
                    "type": "array",
                    "description": "Updated data points (same count as original)",
                    "items": {
                        "type": "object",
                        "properties": {
                            "label": {"type": "string"},
                            "value": {"type": "number"}
                        },
                        "required": ["label", "value"],
                        "additionalProperties": False
                    }
                }
            },
            "required": ["title", "data"],
            "additionalProperties": False
        }
        
        # Call OpenAI with Structured Outputs
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        ai_response = await sync_to_async(client.chat.completions.create)(
            model="gpt-4o-2024-08-06",
            messages=[{"role": "user", "content": prompt}],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "chart_update",
                    "strict": True,
                    "schema": chart_update_schema
                }
            },
            max_tokens=800,
            temperature=0.3
        )
        
        # Parse AI response
        updates = json.loads(ai_response.choices[0].message.content)
        
        # Validate data count matches
        if len(updates['data']) != len(current_data):
            return JsonResponse({
                "message": f"Data count mismatch: expected {len(current_data)}, got {len(updates['data'])}"
            }, status=400)
        
        # Apply updates while preserving colors
        target_chart['title'] = updates['title']
        for i, updated_item in enumerate(updates['data']):
            target_chart['data'][i]['label'] = updated_item['label']
            target_chart['data'][i]['value'] = updated_item['value']
            # Keep original color!
        
        # Save updated chart data
        response_obj.chart_data[chart_index] = target_chart
        await sync_to_async(response_obj.save)()
        
        logger.info(f"Chart {chart_id} updated successfully via AI")
        return {"message": "Chart updated successfully"}
    
    except ESRSUserResponse.DoesNotExist:
        return JsonResponse({"message": "Response not found"}, status=404)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response: {e}")
        return JsonResponse({"message": "AI response format error"}, status=500)
    except Exception as e:
        logger.error(f"Error editing chart: {e}", exc_info=True)
        return JsonResponse({"message": str(e)}, status=500)


# ========== EXPORT ENDPOINTS ==========

@api.get("/export/pdf", auth=JWTAuth())
async def export_report_pdf(request, standard_id: Optional[int] = None, disclosure_ids: Optional[str] = None):
    """
    Export ESRS report as PDF
    Query params:
    - standard_id: Filter by specific standard (optional)
    - disclosure_ids: Comma-separated disclosure IDs (optional)
    """
    from django.http import HttpResponse
    from accounts.report_generator import ESRSReportGenerator
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Parse disclosure_ids if provided
        parsed_disclosure_ids = None
        if disclosure_ids:
            parsed_disclosure_ids = [int(id.strip()) for id in disclosure_ids.split(',')]
        
        # Generate report (run in sync context)
        generator = await sync_to_async(ESRSReportGenerator)(
            user=request.auth,
            standard_id=standard_id,
            disclosure_ids=parsed_disclosure_ids
        )
        
        pdf_buffer = await sync_to_async(generator.generate_pdf)()
        
        # Create response
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        filename = f"ESRS_Report_{request.auth.email}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        logger.info(f"PDF report generated for user {request.auth.email}")
        return response
    
    except Exception as e:
        logger.error(f"Error generating PDF report: {e}", exc_info=True)
        return JsonResponse({"message": f"Failed to generate PDF: {str(e)}"}, status=500)


@api.get("/export/word", auth=JWTAuth())
async def export_report_word(request, standard_id: Optional[int] = None, disclosure_ids: Optional[str] = None):
    """
    Export ESRS report as Word document
    Query params:
    - standard_id: Filter by specific standard (optional)
    - disclosure_ids: Comma-separated disclosure IDs (optional)
    """
    from django.http import HttpResponse
    from accounts.report_generator import ESRSReportGenerator
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Parse disclosure_ids if provided
        parsed_disclosure_ids = None
        if disclosure_ids:
            parsed_disclosure_ids = [int(id.strip()) for id in disclosure_ids.split(',')]
        
        # Generate report (run in sync context)
        generator = await sync_to_async(ESRSReportGenerator)(
            user=request.auth,
            standard_id=standard_id,
            disclosure_ids=parsed_disclosure_ids
        )
        
        word_buffer = await sync_to_async(generator.generate_word)()
        
        # Create response
        response = HttpResponse(
            word_buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        filename = f"ESRS_Report_{request.auth.email}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        logger.info(f"Word report generated for user {request.auth.email}")
        return response
    
    except Exception as e:
        logger.error(f"Error generating Word report: {e}", exc_info=True)
        return JsonResponse({"message": f"Failed to generate Word document: {str(e)}"}, status=500)


# ==================== SIMPLIFIED REFINEMENT ENDPOINTS ====================

@api.post("/api/refine/text", auth=JWTAuth())
async def refine_text(request, data: dict):
    """Simplified text refinement endpoint"""
    from accounts.models import AIConversation, ItemVersion, ESRSUserResponse, ESRSDisclosure
    from openai import OpenAI
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        disclosure_id = data.get('disclosure_id')
        instruction = data.get('instruction')
        
        if not disclosure_id or not instruction:
            return JsonResponse({"message": "disclosure_id and instruction are required"}, status=400)
        
        # Get disclosure and user response
        disclosure = await sync_to_async(ESRSDisclosure.objects.get)(id=disclosure_id)
        user_response = await sync_to_async(
            ESRSUserResponse.objects.filter(user=request.auth, disclosure=disclosure).first
        )()
        
        if not user_response:
            return JsonResponse({"message": "No response found for this disclosure"}, status=404)
        
        # Get current content
        current_content = user_response.final_answer or user_response.ai_answer or user_response.manual_answer or ""
        
        # Get or create conversation
        conversation, created = await sync_to_async(
            lambda: AIConversation.objects.get_or_create(
                user=request.auth,
                disclosure=disclosure,
                item_type='TEXT',
                item_id=user_response.id,
                defaults={'messages': []}
            )
        )()
        
        # Add user message
        user_msg = {
            "role": "user",
            "content": instruction,
            "timestamp": datetime.now().isoformat()
        }
        conversation.messages.append(user_msg)
        await sync_to_async(conversation.save)()
        
        # Call OpenAI
        client = OpenAI()
        system_prompt = f"""You are an AI assistant helping to refine content for ESRS sustainability reporting.

Disclosure requirement: {disclosure.requirement_text}

Current answer:
{current_content}

User wants to refine this answer. Follow their instructions while maintaining accuracy and ESRS compliance."""
        
        response = client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": instruction}
            ],
            temperature=0.3
        )
        
        ai_response = response.choices[0].message.content
        
        # Add AI message
        ai_msg = {
            "role": "assistant",
            "content": ai_response,
            "timestamp": datetime.now().isoformat()
        }
        conversation.messages.append(ai_msg)
        await sync_to_async(conversation.save)()
        
        # Create version
        # Get parent version (latest)
        parent_version = await sync_to_async(
            lambda: ItemVersion.objects.filter(
                item_type='TEXT',
                item_id=user_response.id,
                user=request.auth
            ).order_by('-version_number').first()
        )()
        
        if not parent_version:
            # Create initial version
            parent_version = await sync_to_async(ItemVersion.objects.create)(
                user=request.auth,
                disclosure=disclosure,
                item_type='TEXT',
                item_id=user_response.id,
                version_number=1,
                change_type='INITIAL',
                change_description='Initial version',
                content={"text": current_content, "format": "markdown"},
                is_selected=True,
                created_by_user=False
            )
        
        # Get max version number
        max_version = await sync_to_async(
            lambda: ItemVersion.objects.filter(
                item_type='TEXT',
                item_id=user_response.id,
                user=request.auth
            ).aggregate(models.Max('version_number'))['version_number__max'] or 0
        )()
        
        # Deselect old version
        if parent_version and parent_version.is_selected:
            parent_version.is_selected = False
            await sync_to_async(parent_version.save)()
        
        # Create new version
        new_version = await sync_to_async(ItemVersion.objects.create)(
            user=request.auth,
            disclosure=disclosure,
            item_type='TEXT',
            item_id=user_response.id,
            version_number=max_version + 1,
            parent_version=parent_version,
            change_type='AI_REFINEMENT',
            change_description=instruction[:200],
            content={"text": ai_response, "format": "markdown"},
            conversation=conversation,
            is_selected=True,  # Auto-activate AI refinement
            created_by_user=False
        )
        
        # Update user response with new AI answer
        user_response.ai_answer = ai_response
        await sync_to_async(user_response.save)()
        
        logger.info(f"Created version {new_version.version_number} for user {request.auth.email}")
        
        return {
            "message": ai_response,
            "version_id": str(new_version.id),
            "version_number": new_version.version_number,
            "conversation_id": str(conversation.id)
        }
        
    except ESRSDisclosure.DoesNotExist:
        return JsonResponse({"message": "Disclosure not found"}, status=404)
    except Exception as e:
        logger.error(f"Error refining text: {str(e)}", exc_info=True)
        return JsonResponse({"message": f"Error: {str(e)}"}, status=500)


@api.post("/api/refine/chart", auth=JWTAuth())
async def refine_chart(request, data: dict):
    """AI-powered chart refinement with version creation"""
    from accounts.models import AIConversation, ItemVersion, ESRSUserResponse, ESRSDisclosure
    from openai import OpenAI
    import json
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        disclosure_id = data.get('disclosure_id')
        instruction = data.get('instruction')
        
        if not disclosure_id or not instruction:
            return JsonResponse({"message": "disclosure_id and instruction are required"}, status=400)
        
        disclosure = await sync_to_async(ESRSDisclosure.objects.get)(id=disclosure_id)
        user_response = await sync_to_async(
            ESRSUserResponse.objects.filter(user=request.auth, disclosure=disclosure).first
        )()
        
        if not user_response or not user_response.chart_data:
            return JsonResponse({"message": "No chart found for this disclosure"}, status=404)
        
        # Get current chart (first one)
        current_chart = user_response.chart_data[0] if user_response.chart_data else {}
        
        # Call OpenAI to refine chart
        client = OpenAI()
        system_prompt = f"""You are an AI assistant helping to refine charts for ESRS sustainability reporting.

Current chart:
{json.dumps(current_chart, indent=2)}

User instruction: {instruction}

Generate an updated chart JSON object with the same structure. Only modify what the user requested.
Return ONLY valid JSON, no explanations."""
        
        response = client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Generate the updated chart JSON:"}
            ],
            temperature=0.3
        )
        
        ai_response = response.choices[0].message.content
        # Parse JSON from response
        try:
            refined_chart = json.loads(ai_response)
        except:
            # Try to extract JSON from markdown
            import re
            json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', ai_response, re.DOTALL)
            if json_match:
                refined_chart = json.loads(json_match.group(1))
            else:
                refined_chart = json.loads(ai_response.strip())
        
        # Update chart in database
        user_response.chart_data[0] = refined_chart
        await sync_to_async(user_response.save)()
        
        # Create version
        max_version = await sync_to_async(
            lambda: ItemVersion.objects.filter(
                item_type='CHART',
                item_id=user_response.id,
                user=request.auth
            ).aggregate(models.Max('version_number'))['version_number__max'] or 0
        )()
        
        parent_version = await sync_to_async(
            lambda: ItemVersion.objects.filter(
                item_type='CHART',
                item_id=user_response.id,
                is_selected=True
            ).first()
        )()
        
        # Deselect old version
        if parent_version:
            parent_version.is_selected = False
            await sync_to_async(parent_version.save)()
        
        new_version = await sync_to_async(ItemVersion.objects.create)(
            user=request.auth,
            disclosure=disclosure,
            item_type='CHART',
            item_id=user_response.id,
            version_number=max_version + 1,
            parent_version=parent_version,
            change_type='AI_REFINEMENT',
            change_description=instruction[:200],
            content=refined_chart,
            is_selected=True,
            created_by_user=False
        )
        
        logger.info(f"Created chart version {new_version.version_number}")
        
        return {
            "message": "Chart refined successfully!",
            "chart": refined_chart,
            "version_id": str(new_version.id),
            "version_number": new_version.version_number
        }
        
    except Exception as e:
        logger.error(f"Error refining chart: {str(e)}", exc_info=True)
        return JsonResponse({"message": f"Error: {str(e)}"}, status=500)


@api.post("/api/refine/image", auth=JWTAuth())
async def refine_image(request, data: dict):
    """AI-powered image refinement (regenerate with modified prompt)"""
    from accounts.models import AIConversation, ItemVersion, ESRSUserResponse, ESRSDisclosure
    from openai import OpenAI
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        disclosure_id = data.get('disclosure_id')
        instruction = data.get('instruction')
        
        if not disclosure_id or not instruction:
            return JsonResponse({"message": "disclosure_id and instruction are required"}, status=400)
        
        disclosure = await sync_to_async(ESRSDisclosure.objects.get)(id=disclosure_id)
        user_response = await sync_to_async(
            ESRSUserResponse.objects.filter(user=request.auth, disclosure=disclosure).first
        )()
        
        if not user_response or not user_response.image_data:
            return JsonResponse({"message": "No image found for this disclosure"}, status=404)
        
        # Get current image
        current_image = user_response.image_data[0] if user_response.image_data else {}
        current_prompt = current_image.get('prompt', '')
        
        # Modify prompt based on user instruction
        client = OpenAI()
        system_prompt = f"""You are an AI assistant helping to refine image generation prompts for ESRS sustainability reporting.

Current prompt: {current_prompt}

User instruction: {instruction}

Generate an updated DALL-E prompt that incorporates the user's feedback.
Return ONLY the new prompt text, no explanations."""
        
        response = client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Generate the updated prompt:"}
            ],
            temperature=0.5
        )
        
        new_prompt = response.choices[0].message.content.strip()
        
        # Generate new image with DALL-E
        image_response = client.images.generate(
            model="dall-e-3",
            prompt=new_prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )
        
        new_image_url = image_response.data[0].url
        
        # Update image in database
        refined_image = {
            "id": current_image.get('id', 'img_1'),
            "prompt": new_prompt,
            "url": new_image_url,
            "alt": f"AI-generated visualization for {disclosure.code}",
            "created_at": datetime.now().isoformat()
        }
        user_response.image_data[0] = refined_image
        await sync_to_async(user_response.save)()
        
        # Create version
        max_version = await sync_to_async(
            lambda: ItemVersion.objects.filter(
                item_type='IMAGE',
                item_id=user_response.id,
                user=request.auth
            ).aggregate(models.Max('version_number'))['version_number__max'] or 0
        )()
        
        parent_version = await sync_to_async(
            lambda: ItemVersion.objects.filter(
                item_type='IMAGE',
                item_id=user_response.id,
                is_selected=True
            ).first()
        )()
        
        # Deselect old version
        if parent_version:
            parent_version.is_selected = False
            await sync_to_async(parent_version.save)()
        
        new_version = await sync_to_async(ItemVersion.objects.create)(
            user=request.auth,
            disclosure=disclosure,
            item_type='IMAGE',
            item_id=user_response.id,
            version_number=max_version + 1,
            parent_version=parent_version,
            change_type='AI_REFINEMENT',
            change_description=instruction[:200],
            content=refined_image,
            is_selected=True,
            created_by_user=False
        )
        
        logger.info(f"Created image version {new_version.version_number}")
        
        return {
            "message": "Image refined successfully!",
            "image": refined_image,
            "version_id": str(new_version.id),
            "version_number": new_version.version_number
        }
        
    except Exception as e:
        logger.error(f"Error refining image: {str(e)}", exc_info=True)
        return JsonResponse({"message": f"Error: {str(e)}"}, status=500)


@api.post("/api/refine/table", auth=JWTAuth())
async def refine_table(request, data: dict):
    """AI-powered table refinement with version creation"""
    from accounts.models import AIConversation, ItemVersion, ESRSUserResponse, ESRSDisclosure
    from openai import OpenAI
    import json
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        disclosure_id = data.get('disclosure_id')
        instruction = data.get('instruction')
        
        if not disclosure_id or not instruction:
            return JsonResponse({"message": "disclosure_id and instruction are required"}, status=400)
        
        disclosure = await sync_to_async(ESRSDisclosure.objects.get)(id=disclosure_id)
        user_response = await sync_to_async(
            ESRSUserResponse.objects.filter(user=request.auth, disclosure=disclosure).first
        )()
        
        if not user_response or not user_response.table_data:
            return JsonResponse({"message": "No table found for this disclosure"}, status=404)
        
        # Get current table (first one)
        current_table = user_response.table_data[0] if user_response.table_data else {}
        
        # Call OpenAI to refine table
        client = OpenAI()
        system_prompt = f"""You are an AI assistant helping to refine tables for ESRS sustainability reporting.

Current table:
{json.dumps(current_table, indent=2)}

User instruction: {instruction}

Generate an updated table JSON object with the same structure. Only modify what the user requested.
Return ONLY valid JSON, no explanations."""
        
        response = client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Generate the updated table JSON:"}
            ],
            temperature=0.3
        )
        
        ai_response = response.choices[0].message.content
        # Parse JSON from response
        try:
            refined_table = json.loads(ai_response)
        except:
            # Try to extract JSON from markdown
            import re
            json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', ai_response, re.DOTALL)
            if json_match:
                refined_table = json.loads(json_match.group(1))
            else:
                refined_table = json.loads(ai_response.strip())
        
        # Update table in database
        user_response.table_data[0] = refined_table
        await sync_to_async(user_response.save)()
        
        # Create version
        max_version = await sync_to_async(
            lambda: ItemVersion.objects.filter(
                item_type='TABLE',
                item_id=user_response.id,
                user=request.auth
            ).aggregate(models.Max('version_number'))['version_number__max'] or 0
        )()
        
        parent_version = await sync_to_async(
            lambda: ItemVersion.objects.filter(
                item_type='TABLE',
                item_id=user_response.id,
                is_selected=True
            ).first()
        )()
        
        # Deselect old version
        if parent_version:
            parent_version.is_selected = False
            await sync_to_async(parent_version.save)()
        
        new_version = await sync_to_async(ItemVersion.objects.create)(
            user=request.auth,
            disclosure=disclosure,
            item_type='TABLE',
            item_id=user_response.id,
            version_number=max_version + 1,
            parent_version=parent_version,
            change_type='AI_REFINEMENT',
            change_description=instruction[:200],
            content=refined_table,
            is_selected=True,
            created_by_user=False
        )
        
        logger.info(f"Created table version {new_version.version_number}")
        
        return {
            "message": "Table refined successfully!",
            "table": refined_table,
            "version_id": str(new_version.id),
            "version_number": new_version.version_number
        }
        
    except Exception as e:
        logger.error(f"Error refining table: {str(e)}", exc_info=True)
        return JsonResponse({"message": f"Error: {str(e)}"}, status=500)


@api.post("/api/versions/select", auth=JWTAuth())
async def select_version_api(request, data: dict):
    """Select a version as active (simplified endpoint)"""
    from accounts.models import ItemVersion, ESRSUserResponse
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        version_id = data.get('version_id')
        if not version_id:
            return JsonResponse({"message": "version_id is required"}, status=400)
        
        version = await sync_to_async(ItemVersion.objects.get)(
            id=version_id,
            user=request.auth
        )
        
        # Deselect all other versions for this item
        await sync_to_async(
            lambda: ItemVersion.objects.filter(
                item_type=version.item_type,
                item_id=version.item_id,
                user=request.auth
            ).update(is_selected=False)
        )()
        
        # Select this version
        version.is_selected = True
        await sync_to_async(version.save)()
        
        # Update ESRSUserResponse with selected content
        if version.item_type == 'TEXT':
            user_response = await sync_to_async(ESRSUserResponse.objects.get)(id=version.item_id)
            user_response.manual_answer = version.content.get('text', '')
            await sync_to_async(user_response.save)()
            logger.info(f"Updated manual_answer for response {version.item_id}")
        
        logger.info(f"Selected version {version.version_number} for {version.item_type} item {version.item_id}")
        
        return {
            "message": "Version selected successfully",
            "version_id": str(version.id),
            "version_number": version.version_number
        }
        
    except ItemVersion.DoesNotExist:
        return JsonResponse({"message": "Version not found"}, status=404)
    except Exception as e:
        logger.error(f"Error selecting version: {str(e)}", exc_info=True)
        return JsonResponse({"message": f"Error: {str(e)}"}, status=500)
