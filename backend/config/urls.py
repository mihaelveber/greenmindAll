from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from api.api import api

# Admin site customization
admin.site.site_header = "Greenmind AI Admin"
admin.site.site_title = "Greenmind AI Admin Portal"
admin.site.index_title = "Dobrodošli v Greenmind AI"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls),
    path('accounts/', include('allauth.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
