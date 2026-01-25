from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse, HttpResponse
from api.api import api

# Admin site customization
admin.site.site_header = "Greenmind AI Admin"
admin.site.site_title = "Greenmind AI Admin Portal"
admin.site.index_title = "Dobrodošli v Greenmind AI"

def healthcheck(request):
    """Health check endpoint for AWS Copilot/ALB"""
    return JsonResponse({"status": "healthy"})


def root(request):
    """Return a minimal response for the site root to avoid noisy 404s."""
    return JsonResponse({"status": "ok"})


def empty_favicon(request):
    """Return an empty 204 for favicon requests to prevent template errors."""
    return HttpResponse(status=204)


def simple_404(request, exception=None):
    """JSON 404 handler that avoids template resolution on bad paths."""
    return JsonResponse({"detail": "Not found"}, status=404)


def catch_all_404(request, path=''):
    """Catch-all handler for any unmatched URLs."""
    return JsonResponse({"detail": "Not found"}, status=404)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', root),
    path('favicon.ico', empty_favicon),
    path('api/', api.urls),
    path('api/healthcheck/', healthcheck),
    path('accounts/', include('allauth.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Catch-all pattern MUST be last - catches any URL not matched above
urlpatterns += [
    re_path(r'^(?P<path>.*)$', catch_all_404),
]
