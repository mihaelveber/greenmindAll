"""
ASGI config for config project.
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Get Django ASGI application - This will handle everything including Ninja API  
application = get_asgi_application()
