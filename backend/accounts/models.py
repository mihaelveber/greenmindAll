from django.contrib.auth.models import AbstractUser
from django.db import models

# Import vector models
from .vector_models import (
    DocumentChunk, 
    SearchQuery, 
    EmbeddingModel, 
    RerankerModel
)

# Import version models
from .version_models import (
    AIConversation,
    ItemVersion
)

# Import team collaboration models
from .team_models import (
    UserRole,
    UserInvitation,
    DisclosureAssignment,
    ActivityLog
)

# Import token usage tracking models
from .token_models import (
    TokenUsage,
    OrganizationTokenStats
)

class User(AbstractUser):
    email = models.EmailField(unique=True)
    avatar = models.URLField(blank=True, null=True)
    oauth_provider = models.CharField(max_length=50, blank=True, null=True)
    oauth_id = models.CharField(max_length=255, blank=True, null=True)
    wizard_completed = models.BooleanField(default=False)
    company_type = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('small', 'Small Company'),
        ('sme', 'SME (Medium Enterprise)'),
        ('large', 'Large Corporation'),
    ])
    website_url = models.URLField(blank=True, null=True, help_text='Company website URL for content analysis')
    openai_vector_store_id = models.CharField(max_length=255, blank=True, null=True, help_text='OpenAI Vector Store ID for file search tool')
    allowed_standards = models.JSONField(
        default=list,
        blank=True,
        help_text='List of allowed standard types for this user (e.g., ["ESRS", "ISO9001"]). Empty = all standards allowed.'
    )

    # Company Branding for PDF Reports
    company_logo = models.ImageField(upload_to='company_logos/', blank=True, null=True, help_text='Company logo for branded PDF reports')
    brand_style = models.JSONField(
        default=dict,
        blank=True,
        help_text='AI-generated brand style guide: colors, fonts, layout preferences. Generated from logo analysis.'
    )
    
    # Team Collaboration
    is_organization_owner = models.BooleanField(
        default=True,
        help_text='True if this user owns their account/organization. False if team member.'
    )
    
    # AI Model Preferences
    preferred_llm_model = models.CharField(
        max_length=50,
        default='gpt-4o',
        choices=[
            # OpenAI
            ('gpt-4o', 'GPT-4o (OpenAI)'),
            ('gpt-4o-mini', 'GPT-4o Mini (OpenAI)'),
            ('gpt-5', 'GPT-5 o1 - Deep Reasoning (OpenAI)'),
            ('gpt-5-mini', 'GPT-5 Mini o1 - Faster Reasoning (OpenAI)'),
            # Anthropic - Extended Thinking Models
            ('claude-sonnet-3-7', 'Claude Sonnet 3.7 + Extended Thinking (Anthropic)'),
            ('claude-sonnet-4', 'Claude Sonnet 4 + Extended Thinking (Anthropic)'),
            ('claude-sonnet-4-5', 'Claude Sonnet 4.5 + Extended Thinking (Anthropic)'),
            ('claude-haiku-4-5', 'Claude Haiku 4.5 + Extended Thinking (Anthropic)'),
            ('claude-opus-4', 'Claude Opus 4 + Extended Thinking (Anthropic)'),
            ('claude-opus-4-1', 'Claude Opus 4.1 + Extended Thinking (Anthropic)'),
            ('claude-opus-4-5', 'Claude Opus 4.5 + Extended Thinking (Anthropic)'),
            # Anthropic - Classic Models
            ('claude-3-5-sonnet-20241022', 'Claude 3.5 Sonnet (Anthropic)'),
            ('claude-3-5-haiku-20241022', 'Claude 3.5 Haiku (Anthropic)'),
            # Google
            ('gemini-1.5-pro', 'Gemini 1.5 Pro (Google)'),
            ('gemini-1.5-flash', 'Gemini 1.5 Flash (Google)'),
        ],
        help_text='Preferred LLM model for AI responses. Auto-selects best model for task type.'
    )
    
    # RAG Tier Settings - Confidence thresholds
    rag_tier1_enabled = models.BooleanField(
        default=True,
        help_text='Enable TIER 1: Hybrid BM25 + Embeddings search'
    )
    rag_tier2_enabled = models.BooleanField(
        default=True,
        help_text='Enable TIER 2: Multi-Query + Document Expansion'
    )
    rag_tier3_enabled = models.BooleanField(
        default=True,
        help_text='Enable TIER 3: LLM Self-Reflection + Reranking for highest quality answers'
    )
    rag_tier2_threshold = models.IntegerField(
        default=100,
        help_text='Minimum confidence to skip TIER 2 enhancements (0-100). Below this triggers multi-query.'
    )
    rag_tier3_threshold = models.IntegerField(
        default=85,
        help_text='Minimum confidence to skip TIER 3 enhancements (0-100). Below this triggers LLM refinement.'
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return self.email
    
    def has_standard_access(self, standard_type):
        """Check if user has access to a specific standard type"""
        if not self.allowed_standards:  # Empty list = all standards allowed
            return True
        return standard_type in self.allowed_standards
    
    def get_allowed_standards(self):
        """Get list of allowed standard types. Empty = all allowed."""
        return self.allowed_standards if self.allowed_standards else []
    
    def set_default_standards(self):
        """Set ESRS as default standard if none specified"""
        if not self.allowed_standards:
            self.allowed_standards = ['ESRS']
            self.save(update_fields=['allowed_standards'])
    
    class Meta:
        db_table = 'users'


class Document(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    file_size = models.BigIntegerField()
    file_type = models.CharField(max_length=100)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_global = models.BooleanField(default=False, help_text='Global documents are automatically linked to all disclosures')
    openai_file_id = models.CharField(max_length=255, blank=True, null=True, help_text='OpenAI File API ID for vector store integration')
    
    # RAG Processing Status
    rag_processing_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed')
        ],
        default='pending',
        help_text='Status of RAG chunk processing'
    )
    rag_processed_at = models.DateTimeField(null=True, blank=True, help_text='When RAG processing completed')
    rag_error = models.TextField(blank=True, help_text='Error message if RAG processing failed')
    rag_chunks_count = models.IntegerField(default=0, help_text='Number of chunks created')
    
    def __str__(self):
        return f"{self.user.email} - {self.file_name}"
    
    class Meta:
        db_table = 'documents'
        ordering = ['-uploaded_at']


class ESRSCategory(models.Model):
    """Generic Standard Category - supports ESRS, ISO, GDPR, and EU Regulations"""
    STANDARD_TYPE_CHOICES = [
        ('ESRS', 'ESRS - European Sustainability Reporting Standards'),
        ('ISO9001', 'ISO 9001 - Quality Management System'),
        ('ISO14001', 'ISO 14001 - Environmental Management System'),
        ('ISO27001', 'ISO 27001 - Information Security Management'),
        ('ISO45001', 'ISO 45001 - Occupational Health and Safety'),
        ('ISO50001', 'ISO 50001 - Energy Management System'),
        ('GDPR', 'GDPR - General Data Protection Regulation'),
        ('NIS2', 'NIS2 - Network and Information Security Directive'),
        ('CSRD', 'CSRD - Corporate Sustainability Reporting Directive'),
        ('DORA', 'DORA - Digital Operational Resilience Act'),
        ('CSDDD', 'CSDDD - Corporate Sustainability Due Diligence Directive'),
        ('EUTaxonomy', 'EU Taxonomy - Sustainable Finance Regulation'),
    ]
    
    standard_type = models.CharField(max_length=20, choices=STANDARD_TYPE_CHOICES, default='ESRS', help_text='Type of standard')
    name = models.CharField(max_length=50)  # Environmental, Social, Governance, Cross-cutting (ESRS) OR Context, Leadership, etc. (ISO)
    code = models.CharField(max_length=10)  # E, S, G, CC (ESRS) OR 4, 5, 6, 7, 8, 9, 10 (ISO)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    translations = models.JSONField(default=dict, blank=True)  # {"sl": {"name": "...", "description": "..."}, "de": {...}}
    
    def __str__(self):
        return f"[{self.standard_type}] {self.code} - {self.name}"
    
    class Meta:
        db_table = 'esrs_categories'
        ordering = ['standard_type', 'order']
        verbose_name_plural = 'Standard Categories'
        unique_together = [['code', 'standard_type']]  # Allow same code for different standards


class ESRSStandard(models.Model):
    """Generic Standard - supports ESRS, ISO, GDPR, and EU Regulations"""
    STANDARD_TYPE_CHOICES = [
        ('ESRS', 'ESRS - European Sustainability Reporting Standards'),
        ('ISO9001', 'ISO 9001 - Quality Management System'),
        ('ISO14001', 'ISO 14001 - Environmental Management System'),
        ('ISO27001', 'ISO 27001 - Information Security Management'),
        ('ISO45001', 'ISO 45001 - Occupational Health and Safety'),
        ('ISO50001', 'ISO 50001 - Energy Management System'),
        ('GDPR', 'GDPR - General Data Protection Regulation'),
        ('NIS2', 'NIS2 - Network and Information Security Directive'),
        ('CSRD', 'CSRD - Corporate Sustainability Reporting Directive'),
        ('DORA', 'DORA - Digital Operational Resilience Act'),
        ('CSDDD', 'CSDDD - Corporate Sustainability Due Diligence Directive'),
        ('EUTaxonomy', 'EU Taxonomy - Sustainable Finance Regulation'),
    ]
    
    standard_type = models.CharField(max_length=20, choices=STANDARD_TYPE_CHOICES, default='ESRS', help_text='Type of standard')
    category = models.ForeignKey(ESRSCategory, on_delete=models.CASCADE, related_name='standards')
    code = models.CharField(max_length=10)  # E1, E2, S1, G1, ESRS 1, ESRS 2 (ESRS) OR 4.1, 5.1, etc. (ISO)
    name = models.CharField(max_length=200)  # Climate change, Pollution (ESRS) OR Context of organization, Leadership (ISO)
    description = models.TextField()
    order = models.IntegerField(default=0)
    translations = models.JSONField(default=dict, blank=True)  # {"sl": {"name": "...", "description": "..."}, "de": {...}}
    ai_prompt = models.TextField(blank=True, null=True)  # Custom AI prompt template for this standard
    
    def __str__(self):
        return f"[{self.standard_type}] {self.code}: {self.name}"
    
    class Meta:
        db_table = 'esrs_standards'
        ordering = ['standard_type', 'category__order', 'order']
        unique_together = [['code', 'standard_type']]  # Allow same code for different standards


class ESRSDisclosure(models.Model):
    """Generic Disclosure/Requirement - supports ESRS, ISO, GDPR, and EU Regulations"""
    STANDARD_TYPE_CHOICES = [
        ('ESRS', 'ESRS - European Sustainability Reporting Standards'),
        ('ISO9001', 'ISO 9001 - Quality Management System'),
        ('ISO14001', 'ISO 14001 - Environmental Management System'),
        ('ISO27001', 'ISO 27001 - Information Security Management'),
        ('ISO45001', 'ISO 45001 - Occupational Health and Safety'),
        ('ISO50001', 'ISO 50001 - Energy Management System'),
        ('GDPR', 'GDPR - General Data Protection Regulation'),
        ('NIS2', 'NIS2 - Network and Information Security Directive'),
        ('CSRD', 'CSRD - Corporate Sustainability Reporting Directive'),
        ('DORA', 'DORA - Digital Operational Resilience Act'),
        ('CSDDD', 'CSDDD - Corporate Sustainability Due Diligence Directive'),
        ('EUTaxonomy', 'EU Taxonomy - Sustainable Finance Regulation'),
    ]
    
    standard_type = models.CharField(max_length=20, choices=STANDARD_TYPE_CHOICES, default='ESRS', help_text='Type of standard')
    standard = models.ForeignKey(ESRSStandard, on_delete=models.CASCADE, related_name='disclosures')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sub_disclosures')  # Za hierarhijo
    code = models.CharField(max_length=20)  # E1-1, E1-2, E1-3a, S1-1 (ESRS) OR 4.1.1, 5.1.1 (ISO)
    name = models.CharField(max_length=500)
    description = models.TextField()
    requirement_text = models.TextField()  # Celotno besedilo zahteve
    is_mandatory = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    translations = models.JSONField(default=dict, blank=True)  # {"sl": {"name": "...", "description": "...", "requirement_text": "..."}, "de": {...}}
    ai_prompt = models.TextField(blank=True, null=True)  # Custom AI prompt template (overrides requirement_text if set)
    
    def __str__(self):
        return f"[{self.standard_type}] {self.code}: {self.name}"
    
    class Meta:
        db_table = 'esrs_disclosures'
        ordering = ['standard_type', 'standard', 'order']
        unique_together = [['standard', 'code']]  # Unique within same standard


class ESRSUserResponse(models.Model):
    """Uporabnikovi odgovori/zapiski za vsako ESRS disclosure točko"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='esrs_responses')
    disclosure = models.ForeignKey(ESRSDisclosure, on_delete=models.CASCADE, related_name='user_responses')
    notes = models.TextField(blank=True, null=True)  # Uporabnikovi zapiski
    manual_answer = models.TextField(blank=True, null=True)  # Ročni odgovor uporabnika
    is_completed = models.BooleanField(default=False)  # Ali je točka označena kot zaključena
    ai_answer = models.TextField(blank=True, null=True)  # AI generirani odgovor
    final_answer = models.TextField(blank=True, null=True)  # Končni odobreni odgovor za report (override AI/manual)
    ai_sources = models.JSONField(blank=True, null=True, default=dict)  # Source documents and chunks used by AI
    
    # === NOVA POLJA ZA CHARTS & ANALYTICS ===
    numeric_data = models.JSONField(blank=True, null=True)  # Extracted numeric data: {has_data: bool, data_points: [...], categories: {...}}
    chart_data = models.JSONField(blank=True, null=True)  # Chart information: [{id: str, type: 'bar/pie/line', title: str, data: {...}, image_base64: str, selected_for_report: bool}]
    table_data = models.JSONField(blank=True, null=True)  # Structured tables: [{title: str, headers: [...], rows: [[...]]}]
    
    # === AI GENERATION SETTINGS ===
    ai_temperature = models.FloatField(default=0.2, help_text='AI creativity level: 0.0=factual, 1.0=creative')
    confidence_score = models.FloatField(null=True, blank=True, help_text='AI confidence score: % of content from documents vs AI reasoning')
    
    # === USER TRACKING FOR MULTI-USER COLLABORATION ===
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_responses', help_text='User who created this response')
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='modified_responses', help_text='User who last modified this response')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_responses', help_text='Team member assigned to work on this disclosure')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.disclosure.code}"
    
    class Meta:
        db_table = 'esrs_user_responses'
        unique_together = ['user', 'disclosure']
        ordering = ['-updated_at']


class DocumentEvidence(models.Model):
    """Povezava med dokumenti in ESRS disclosure točkami (ONE document can be linked to MULTIPLE disclosures)"""
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='esrs_evidence')
    disclosure = models.ForeignKey(ESRSDisclosure, on_delete=models.CASCADE, related_name='evidence_documents')
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Za preverjanje pravic
    linked_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)  # Opcijski opis zakaj je ta dokument dodan
    is_excluded = models.BooleanField(default=False)  # For global docs: user explicitly excluded this doc from this disclosure
    
    def __str__(self):
        return f"{self.document.file_name} -> {self.disclosure.code}"
    
    class Meta:
        db_table = 'document_evidence'
        ordering = ['-linked_at']
        unique_together = [['document', 'disclosure']]  # Prepreči duplicate links


class AITaskStatus(models.Model):
    """Tracking Celery tasks za AI odgovore"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    task_id = models.CharField(max_length=255, unique=True)  # Celery task ID
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_tasks')
    disclosure = models.ForeignKey(ESRSDisclosure, on_delete=models.CASCADE, related_name='ai_tasks', null=True, blank=True)
    standard = models.ForeignKey('ESRSStandard', on_delete=models.CASCADE, related_name='ai_tasks', null=True, blank=True)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='ai_tasks', null=True, blank=True)
    task_type = models.CharField(max_length=50, default='single')  # 'single' or 'bulk' or 'rag_processing'
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress = models.IntegerField(default=0)  # 0-100
    total_items = models.IntegerField(default=1)  # Število disclosure točk
    completed_items = models.IntegerField(default=0)
    result = models.TextField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    
    # Detailed progress tracking
    current_step = models.CharField(max_length=500, blank=True, null=True, help_text='Current step description')
    steps_completed = models.JSONField(default=list, blank=True, help_text='List of completed steps with details')
    processing_steps = models.JSONField(default=list, blank=True, help_text='TIER RAG processing steps for UI display')
    documents_used = models.IntegerField(default=0, help_text='Number of documents analyzed')
    chunks_used = models.IntegerField(default=0, help_text='Number of chunks/sections analyzed')
    confidence_score = models.FloatField(default=0.0, help_text='AI confidence score 0-100')
    reasoning_summary = models.TextField(blank=True, null=True, help_text='AI reasoning summary from OpenAI o1 models (gpt-5, gpt-5-mini, gpt-5-nano). Shows thinking process before generating answer.')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.task_type} - {self.status}"
    
    class Meta:
        db_table = 'ai_task_status'
        ordering = ['-created_at']


class ConversationThread(models.Model):
    """
    Conversation thread for AI follow-up questions on a disclosure
    Each disclosure can have one active conversation thread
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversation_threads')
    disclosure = models.ForeignKey(ESRSDisclosure, on_delete=models.CASCADE, related_name='conversation_threads')
    title = models.CharField(max_length=500, help_text='Auto-generated from first question')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.disclosure.code}: {self.title[:50]}"
    
    class Meta:
        db_table = 'conversation_threads'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'disclosure', 'is_active']),
        ]


class ConversationMessage(models.Model):
    """
    Individual message in a conversation thread
    Stores user questions and AI responses with full context
    """
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]
    
    thread = models.ForeignKey(ConversationThread, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField(help_text='Message content')
    
    # AI generation settings (for assistant messages)
    temperature = models.FloatField(null=True, blank=True, help_text='Temperature used for this message')
    
    # Document context (which documents were used)
    documents_used = models.JSONField(default=list, blank=True, help_text='List of document IDs used for this message')
    
    # Extracted artifacts from this message
    chart_data = models.JSONField(null=True, blank=True)
    table_data = models.JSONField(null=True, blank=True)
    image_data = models.JSONField(null=True, blank=True)
    
    # Metadata
    confidence_score = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    edited = models.BooleanField(default=False)
    regenerated = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}"
    
    class Meta:
        db_table = 'conversation_messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['thread', 'created_at']),
        ]
