from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.db.models import Count, Q
from .models import (
    User, Document, ESRSCategory, ESRSStandard, ESRSDisclosure,
    ESRSUserResponse, DocumentEvidence, AITaskStatus,
    ConversationThread, ConversationMessage
)
import json

# ========== USER ADMIN ==========

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'username', 'company_type', 'allowed_standards_display', 
                    'is_staff', 'wizard_completed', 'is_active', 'date_joined')
    list_filter = ('company_type', 'is_staff', 'is_superuser', 'wizard_completed', 
                   'is_active', 'oauth_provider')
    search_fields = ('email', 'username', 'company_type')
    ordering = ('-date_joined',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Company Info', {'fields': ('company_type', 'website_url', 'wizard_completed')}),
        ('Standard Permissions', {'fields': ('allowed_standards',)}),
        ('OAuth', {'fields': ('oauth_provider', 'oauth_id', 'avatar')}),
    )
    
    def allowed_standards_display(self, obj):
        if obj.is_superuser:
            return format_html('<span style="color: green;">✓ Superuser (All Standards)</span>')
        standards = obj.allowed_standards or []
        if not standards:
            return format_html('<span style="color: red;">❌ No Access</span>')
        return ', '.join(standards)
    allowed_standards_display.short_description = 'Standard Access'
    
    actions = ['assign_esrs', 'assign_iso9001', 'assign_all_standards', 'make_staff']
    
    def assign_esrs(self, request, queryset):
        for user in queryset:
            standards = user.allowed_standards or []
            if 'ESRS' not in standards:
                standards.append('ESRS')
                user.allowed_standards = standards
                user.save()
        self.message_user(request, f'{queryset.count()} users granted ESRS access')
    assign_esrs.short_description = 'Grant ESRS access'
    
    def assign_iso9001(self, request, queryset):
        for user in queryset:
            standards = user.allowed_standards or []
            if 'ISO9001' not in standards:
                standards.append('ISO9001')
                user.allowed_standards = standards
                user.save()
        self.message_user(request, f'{queryset.count()} users granted ISO 9001 access')
    assign_iso9001.short_description = 'Grant ISO 9001 access'
    
    def assign_all_standards(self, request, queryset):
        queryset.update(allowed_standards=['ESRS', 'ISO9001'])
        self.message_user(request, f'{queryset.count()} users granted all standards access')
    assign_all_standards.short_description = 'Grant all standards access'
    
    def make_staff(self, request, queryset):
        queryset.update(is_staff=True, is_superuser=True)
        self.message_user(request, f'{queryset.count()} users set as staff/superuser')
    make_staff.short_description = 'Make users staff (admin access)'

# ========== DOCUMENT ADMIN ==========

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'user', 'is_global', 'file_size_display', 
                    'file_type', 'uploaded_at')
    list_filter = ('is_global', 'file_type', 'uploaded_at')
    search_fields = ('file_name', 'user__email', 'parsed_text')
    ordering = ('-uploaded_at',)
    readonly_fields = ('uploaded_at',)
    
    def file_size_display(self, obj):
        if obj.file_size:
            size_mb = obj.file_size / (1024 * 1024)
            return f'{size_mb:.2f} MB'
        return '-'
    file_size_display.short_description = 'Size'

# ========== STANDARDS ADMIN ==========

@admin.register(ESRSCategory)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'standard_type', 'order', 'standard_count')
    list_filter = ('standard_type',)
    search_fields = ('code', 'name', 'description')
    ordering = ('standard_type', 'order')
    
    def standard_count(self, obj):
        return obj.esrsstandard_set.count()
    standard_count.short_description = 'Standards'

@admin.register(ESRSStandard)
class StandardAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'category', 'standard_type_display', 
                    'order', 'disclosure_count')
    list_filter = ('category__standard_type', 'category')
    search_fields = ('code', 'name', 'description')
    ordering = ('category__standard_type', 'category__order', 'order')
    
    def standard_type_display(self, obj):
        return obj.category.standard_type
    standard_type_display.short_description = 'Type'
    
    def disclosure_count(self, obj):
        return obj.esrsdisclosure_set.count()
    disclosure_count.short_description = 'Disclosures'

@admin.register(ESRSDisclosure)
class DisclosureAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'standard', 'standard_type_display', 
                    'order', 'response_count')
    list_filter = ('standard__category__standard_type', 'standard__category', 'standard')
    search_fields = ('code', 'name', 'description')
    ordering = ('standard__category__standard_type', 'standard__order', 'order')
    
    def standard_type_display(self, obj):
        return obj.standard.category.standard_type
    standard_type_display.short_description = 'Type'
    
    def response_count(self, obj):
        return obj.esrsuserresponse_set.count()
    response_count.short_description = 'Responses'

# ========== USER RESPONSE ADMIN ==========

@admin.register(ESRSUserResponse)
class UserResponseAdmin(admin.ModelAdmin):
    list_display = ('user', 'disclosure_code', 'standard_type_display', 
                    'is_completed', 'has_ai_answer', 'has_final_answer', 
                    'updated_at')
    list_filter = ('is_completed', 'disclosure__standard__category__standard_type',
                   'disclosure__standard__category', 'updated_at')
    search_fields = ('user__email', 'disclosure__code', 'disclosure__name', 
                     'notes', 'manual_answer')
    ordering = ('-updated_at',)
    readonly_fields = ('created_at', 'updated_at')
    
    def disclosure_code(self, obj):
        return obj.disclosure.code
    disclosure_code.short_description = 'Disclosure'
    
    def standard_type_display(self, obj):
        return obj.disclosure.standard.category.standard_type
    standard_type_display.short_description = 'Standard Type'
    
    def has_ai_answer(self, obj):
        return bool(obj.ai_answer)
    has_ai_answer.boolean = True
    has_ai_answer.short_description = 'AI Answer'
    
    def has_final_answer(self, obj):
        return bool(obj.final_answer)
    has_final_answer.boolean = True
    has_final_answer.short_description = 'Final Answer'

# ========== EVIDENCE ADMIN ==========

@admin.register(DocumentEvidence)
class DocumentEvidenceAdmin(admin.ModelAdmin):
    list_display = ('document_name', 'disclosure_code', 'user', 'is_excluded', 'linked_at')
    list_filter = ('is_excluded', 'linked_at', 'disclosure__standard__category__standard_type')
    search_fields = ('document__file_name', 'disclosure__code', 'user__email')
    ordering = ('-linked_at',)
    readonly_fields = ('linked_at',)
    
    def document_name(self, obj):
        return obj.document.file_name
    document_name.short_description = 'Document'
    
    def disclosure_code(self, obj):
        return obj.disclosure.code
    disclosure_code.short_description = 'Disclosure'

# ========== AI TASK ADMIN ==========

@admin.register(AITaskStatus)
class AITaskStatusAdmin(admin.ModelAdmin):
    list_display = ('task_id', 'user', 'disclosure_code', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('task_id', 'user__email', 'disclosure__code')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    
    def disclosure_code(self, obj):
        if obj.disclosure:
            return obj.disclosure.code
        return '-'
    disclosure_code.short_description = 'Disclosure'

# ========== CONVERSATION ADMIN ==========

@admin.register(ConversationThread)
class ConversationThreadAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'disclosure_code', 'title', 'message_count', 
                    'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at', 'disclosure__standard__category__standard_type')
    search_fields = ('user__email', 'disclosure__code', 'title')
    ordering = ('-updated_at',)
    readonly_fields = ('created_at', 'updated_at')
    
    def disclosure_code(self, obj):
        return obj.disclosure.code
    disclosure_code.short_description = 'Disclosure'
    
    def message_count(self, obj):
        return obj.conversationmessage_set.count()
    message_count.short_description = 'Messages'

@admin.register(ConversationMessage)
class ConversationMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'thread_id', 'role', 'content_preview', 'temperature', 
                    'confidence_score', 'created_at')
    list_filter = ('role', 'created_at', 'edited', 'regenerated')
    search_fields = ('thread__user__email', 'content')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    
    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content'
