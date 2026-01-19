"""
API endpoints for company branding and logo management
"""

import logging
from ninja import Router, File
from ninja.files import UploadedFile
from django.http import JsonResponse
from accounts.auth import JWTAuth
from accounts.brand_analyzer import BrandAnalyzer
from django.core.files.storage import default_storage
from pathlib import Path
from asgiref.sync import sync_to_async
import os

logger = logging.getLogger(__name__)

router = Router(tags=["Branding"])


@router.post("/branding/upload-logo", auth=JWTAuth())
async def upload_logo(request, file: UploadedFile = File(...)):
    """
    Upload company logo and automatically analyze brand style with AI

    - Saves logo to user's account
    - Uses Claude Vision API to analyze logo and generate brand style guide
    - Returns extracted colors, typography, layout preferences
    """
    try:
        user = request.auth

        # Validate file type
        allowed_types = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp']
        if file.content_type not in allowed_types:
            return JsonResponse(
                {"message": "Invalid file type. Please upload PNG, JPG, or WEBP image."},
                status=400
            )

        # Validate file size (max 5MB)
        if file.size > 5 * 1024 * 1024:
            return JsonResponse(
                {"message": "File too large. Maximum size is 5MB."},
                status=400
            )

        # Save the uploaded file (sync operation)
        file_name = f"company_logos/{user.id}_{file.name}"
        file_path = await sync_to_async(default_storage.save)(file_name, file)
        full_path = await sync_to_async(default_storage.path)(file_path)

        logger.info(f"Logo uploaded for user {user.email}: {file_path}")

        # Update user model (sync operation)
        def save_logo_to_user():
            user.company_logo = file_path
            user.save(update_fields=['company_logo'])

        await sync_to_async(save_logo_to_user)()

        # Analyze logo with AI (sync operation - uses Claude API)
        def analyze_and_save():
            logger.info(f"🎨 Starting AI analysis of logo at: {full_path}")
            brand_analyzer = BrandAnalyzer()
            style_guide = brand_analyzer.analyze_logo(full_path)
            logger.info(f"🎨 AI Analysis complete. Primary color: {style_guide.get('colors', {}).get('primary', 'N/A')}")
            logger.info(f"🎨 Full style guide: {style_guide}")
            user.brand_style = style_guide
            user.save(update_fields=['brand_style'])
            logger.info(f"🎨 Style guide saved to database for user {user.email}")
            return style_guide

        style_guide = await sync_to_async(analyze_and_save)()

        logger.info(f"Brand style analyzed and saved for user {user.email}")

        # Get URL (sync operation)
        def get_full_url():
            from django.conf import settings
            relative_url = default_storage.url(file_path)
            # Build full URL for frontend
            if relative_url.startswith('http'):
                return relative_url
            return f"http://localhost:8090{relative_url}"

        logo_url = await sync_to_async(get_full_url)()

        return JsonResponse({
            "message": "Logo uploaded and analyzed successfully",
            "logo_url": logo_url,
            "brand_style": style_guide
        }, status=200)

    except Exception as e:
        logger.error(f"Failed to upload logo: {e}", exc_info=True)
        return JsonResponse(
            {"message": f"Failed to upload logo: {str(e)}"},
            status=500
        )


@router.get("/branding/style", auth=JWTAuth())
async def get_brand_style(request):
    """
    Get current brand style for authenticated user

    Returns the AI-analyzed brand style guide or default if not set
    """
    try:
        user = request.auth

        # Get user data async
        def get_user_branding():
            has_logo = bool(user.company_logo)
            if user.company_logo:
                relative_url = default_storage.url(user.company_logo)
                logo_url = f"http://localhost:8090{relative_url}" if not relative_url.startswith('http') else relative_url
            else:
                logo_url = None
            brand_style = user.brand_style
            return has_logo, logo_url, brand_style

        has_logo, logo_url, brand_style = await sync_to_async(get_user_branding)()

        if brand_style:
            return JsonResponse({
                "has_logo": has_logo,
                "logo_url": logo_url,
                "brand_style": brand_style
            }, status=200)
        else:
            # Return default style
            def get_default_style():
                brand_analyzer = BrandAnalyzer()
                return brand_analyzer._get_default_style_guide()

            default_style = await sync_to_async(get_default_style)()

            return JsonResponse({
                "has_logo": False,
                "logo_url": None,
                "brand_style": default_style,
                "message": "Using default style. Upload a logo to get custom branding."
            }, status=200)

    except Exception as e:
        logger.error(f"Failed to get brand style: {e}")
        return JsonResponse(
            {"message": f"Failed to get brand style: {str(e)}"},
            status=500
        )


@router.post("/branding/regenerate-style", auth=JWTAuth())
async def regenerate_brand_style(request):
    """
    Regenerate brand style from existing logo using AI

    Useful if you want to re-analyze the logo with updated AI model
    """
    try:
        user = request.auth

        if not user.company_logo:
            return JsonResponse(
                {"message": "No logo uploaded. Please upload a logo first."},
                status=400
            )

        # Get logo path and re-analyze
        def regenerate():
            logo_path = default_storage.path(user.company_logo)
            brand_analyzer = BrandAnalyzer()
            style_guide = brand_analyzer.analyze_logo(logo_path)
            user.brand_style = style_guide
            user.save(update_fields=['brand_style'])
            return style_guide

        style_guide = await sync_to_async(regenerate)()

        logger.info(f"Brand style regenerated for user {user.email}")

        return JsonResponse({
            "message": "Brand style regenerated successfully",
            "brand_style": style_guide
        }, status=200)

    except Exception as e:
        logger.error(f"Failed to regenerate brand style: {e}")
        return JsonResponse(
            {"message": f"Failed to regenerate brand style: {str(e)}"},
            status=500
        )


@router.delete("/branding/logo", auth=JWTAuth())
async def delete_logo(request):
    """
    Delete company logo and reset brand style to default
    """
    try:
        user = request.auth

        def delete_logo_file():
            if user.company_logo:
                # Delete file from storage - convert ImageFieldFile to string path
                logo_path = str(user.company_logo)
                if default_storage.exists(logo_path):
                    default_storage.delete(logo_path)

            # Reset fields
            user.company_logo = None
            user.brand_style = {}
            user.save(update_fields=['company_logo', 'brand_style'])

        await sync_to_async(delete_logo_file)()

        logger.info(f"Logo deleted for user {user.email}")

        return JsonResponse({
            "message": "Logo deleted successfully"
        }, status=200)

    except Exception as e:
        logger.error(f"Failed to delete logo: {e}")
        return JsonResponse(
            {"message": f"Failed to delete logo: {str(e)}"},
            status=500
        )
