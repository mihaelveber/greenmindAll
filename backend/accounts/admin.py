from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Document

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'username', 'company_type', 'wizard_completed', 'is_active', 'date_joined')
    list_filter = ('company_type', 'wizard_completed', 'is_active', 'oauth_provider')
    search_fields = ('email', 'username')
    ordering = ('-date_joined',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Company Info', {'fields': ('company_type', 'wizard_completed')}),
        ('OAuth', {'fields': ('oauth_provider', 'oauth_id', 'avatar')}),
    )

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'user', 'file_size', 'file_type', 'uploaded_at')
    list_filter = ('file_type', 'uploaded_at')
    search_fields = ('file_name', 'user__email')
    ordering = ('-uploaded_at',)
    readonly_fields = ('uploaded_at',)
