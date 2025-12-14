from django.contrib import admin
from django.urls import path, include
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
