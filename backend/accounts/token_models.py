"""
Token usage tracking models for monitoring OpenAI API costs
"""
from django.db import models
from django.conf import settings


class TokenUsage(models.Model):
    """
    Track OpenAI API token usage and costs per user and organization.
    Records every API call for billing, analytics, and cost optimization.
    """
    
    ACTION_TYPES = [
        ('ai_answer', 'AI Answer Generation'),
        ('conversation', 'Conversation Chat'),
        ('rag_search', 'RAG Document Search'),
        ('embedding', 'Document Embedding'),
        ('summary', 'Document Summary'),
        ('other', 'Other'),
    ]
    
    # User context
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='token_usage',
        help_text='User who initiated the action'
    )
    organization = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='org_token_usage',
        help_text='Organization owner (for aggregated billing)'
    )
    
    # Action details
    action_type = models.CharField(
        max_length=50, 
        choices=ACTION_TYPES,
        db_index=True,
        help_text='Type of action that consumed tokens'
    )
    disclosure = models.ForeignKey(
        'accounts.ESRSDisclosure',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='token_usage',
        help_text='Related disclosure (if applicable)'
    )
    
    # API call details
    model = models.CharField(
        max_length=50,
        help_text='LLM model used (e.g., gpt-4o, claude-3-5-sonnet, gemini-1.5-pro)'
    )
    model_provider = models.CharField(
        max_length=20,
        default='openai',
        choices=[
            ('openai', 'OpenAI'),
            ('anthropic', 'Anthropic'),
            ('google', 'Google'),
        ],
        help_text='LLM provider (OpenAI, Anthropic, Google)'
    )
    prompt_tokens = models.IntegerField(
        help_text='Number of tokens in the prompt/input'
    )
    completion_tokens = models.IntegerField(
        default=0,
        help_text='Number of tokens in the completion/output'
    )
    total_tokens = models.IntegerField(
        help_text='Total tokens (prompt + completion)'
    )
    
    # Cost calculation
    cost_usd = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        help_text='Cost in USD (precise to 6 decimals)'
    )
    
    # Metadata
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text='When the API call was made'
    )
    request_duration_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text='API request duration in milliseconds'
    )
    error = models.TextField(
        null=True,
        blank=True,
        help_text='Error message if request failed'
    )
    
    # Additional context
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional metadata (task_id, conversation_id, etc.)'
    )
    
    class Meta:
        db_table = 'token_usage'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['organization', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action_type', '-timestamp']),
            models.Index(fields=['-timestamp']),
        ]
        verbose_name = 'Token Usage'
        verbose_name_plural = 'Token Usage Records'
    
    def __str__(self):
        return f"{self.user.email} - {self.action_type} - {self.total_tokens} tokens (${self.cost_usd})"
    
    @classmethod
    def calculate_cost(cls, model: str, prompt_tokens: int, completion_tokens: int, provider: str = 'openai') -> float:
        """
        Calculate cost in USD based on LLM provider pricing (as of Dec 2024)
        
        Pricing per 1M tokens:
        
        OpenAI:
        - gpt-4o: $2.50 input, $10.00 output
        - gpt-4o-mini: $0.150 input, $0.600 output
        - text-embedding-3-small: $0.020 input
        - text-embedding-3-large: $0.130 input
        
        Anthropic:
        - claude-3-5-sonnet: $3.00 input, $15.00 output
        - claude-3-5-haiku: $0.80 input, $4.00 output
        
        Google:
        - gemini-1.5-pro: $1.25 input, $5.00 output
        - gemini-1.5-flash: $0.075 input, $0.30 output
        """
        
        # OpenAI pricing
        openai_pricing = {
            'gpt-4o': {'input': 2.50, 'output': 10.00},
            'gpt-4o-mini': {'input': 0.150, 'output': 0.600},
            'gpt-4': {'input': 30.00, 'output': 60.00},  # Legacy
            'gpt-3.5-turbo': {'input': 0.50, 'output': 1.50},
            'text-embedding-3-small': {'input': 0.020, 'output': 0},
            'text-embedding-3-large': {'input': 0.130, 'output': 0},
            'text-embedding-ada-002': {'input': 0.10, 'output': 0},  # Legacy
        }
        
        # Anthropic pricing
        anthropic_pricing = {
            'claude-3-5-sonnet-20241022': {'input': 3.00, 'output': 15.00},
            'claude-3-5-haiku-20241022': {'input': 0.80, 'output': 4.00},
        }
        
        # Google pricing
        google_pricing = {
            'gemini-1.5-pro': {'input': 1.25, 'output': 5.00},
            'gemini-1.5-flash': {'input': 0.075, 'output': 0.30},
        }
        
        # Select pricing based on provider
        if provider == 'anthropic':
            pricing_table = anthropic_pricing
            default_model = 'claude-3-5-sonnet-20241022'
        elif provider == 'google':
            pricing_table = google_pricing
            default_model = 'gemini-1.5-pro'
        else:  # openai
            pricing_table = openai_pricing
            default_model = 'gpt-4o'
        
        # Get pricing for model (default to provider's default if unknown)
        model_pricing = pricing_table.get(model, pricing_table.get(default_model, {'input': 2.50, 'output': 10.00}))
        
        # Calculate cost (price is per 1 million tokens)
        input_cost = (prompt_tokens / 1_000_000) * model_pricing['input']
        output_cost = (completion_tokens / 1_000_000) * model_pricing['output']
        
        return round(input_cost + output_cost, 6)
    
    def save(self, *args, **kwargs):
        """Auto-calculate total_tokens and cost if not provided"""
        if not self.total_tokens:
            self.total_tokens = self.prompt_tokens + self.completion_tokens
        
        if not self.cost_usd:
            self.cost_usd = self.calculate_cost(
                self.model,
                self.prompt_tokens,
                self.completion_tokens,
                self.model_provider
            )
        
        super().save(*args, **kwargs)


class OrganizationTokenStats(models.Model):
    """
    Daily aggregated token usage statistics per organization.
    Pre-computed for faster dashboard queries.
    """
    organization = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='token_stats'
    )
    date = models.DateField(
        db_index=True,
        help_text='Date of the statistics'
    )
    
    # Aggregated metrics
    total_tokens = models.BigIntegerField(default=0)
    total_cost_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    api_calls_count = models.IntegerField(default=0)
    
    # Per action type
    ai_answer_tokens = models.BigIntegerField(default=0)
    conversation_tokens = models.BigIntegerField(default=0)
    rag_search_tokens = models.BigIntegerField(default=0)
    embedding_tokens = models.BigIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'organization_token_stats'
        unique_together = [['organization', 'date']]
        ordering = ['-date']
        indexes = [
            models.Index(fields=['organization', '-date']),
        ]
        verbose_name = 'Organization Token Statistics'
        verbose_name_plural = 'Organization Token Statistics'
    
    def __str__(self):
        return f"{self.organization.email} - {self.date} - {self.total_tokens} tokens (${self.total_cost_usd})"
