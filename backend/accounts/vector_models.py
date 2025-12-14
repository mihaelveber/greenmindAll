"""
Vector storage models for pgvector integration
Stores document chunks with embeddings for hybrid search
"""

from django.db import models
from django.contrib.postgres.indexes import GinIndex
from pgvector.django import VectorField


class DocumentChunk(models.Model):
    """
    Individual chunks of documents with embeddings and metadata
    Supports hybrid search (BM25 + semantic)
    """
    document = models.ForeignKey(
        'Document', 
        on_delete=models.CASCADE, 
        related_name='chunks'
    )
    
    # Chunk identification
    chunk_index = models.IntegerField(help_text='Position of chunk in document (0-based)')
    chunk_id = models.CharField(max_length=100, unique=True, help_text='Unique identifier: doc_{id}_chunk_{idx}')
    
    # Content
    content = models.TextField(help_text='Actual chunk text content')
    context = models.TextField(blank=True, help_text='Contextual description (50-100 tokens)')
    contextualized_content = models.TextField(
        blank=True, 
        help_text='Context + content for better retrieval'
    )
    
    # Chunk metadata
    position = models.CharField(
        max_length=20, 
        choices=[
            ('beginning', 'Beginning'),
            ('middle', 'Middle'),
            ('end', 'End')
        ],
        default='middle'
    )
    char_count = models.IntegerField(default=0)
    word_count = models.IntegerField(default=0)
    token_count = models.IntegerField(default=0, help_text='Approximate token count')
    
    # Vector embeddings (pgvector)
    embedding = VectorField(
        dimensions=3072,  # OpenAI text-embedding-3-large (3072 dimensions)
        blank=True,
        null=True,
        help_text='Semantic embedding vector'
    )
    
    # Alternative embeddings (for comparison)
    voyage_embedding = VectorField(dimensions=1024, blank=True, null=True)
    jina_embedding = VectorField(dimensions=768, blank=True, null=True)
    
    # BM25 sparse representation (for hybrid search)
    bm25_tokens = models.JSONField(
        default=dict,
        blank=True,
        help_text='Token frequencies for BM25: {token_id: frequency}'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Metadata from parent document
    document_type = models.CharField(
        max_length=50,
        blank=True,
        choices=[
            ('financial_report', 'Financial Report'),
            ('esg_report', 'ESG Report'),
            ('policy', 'Policy Document'),
            ('annual_report', 'Annual Report'),
            ('sustainability', 'Sustainability Report'),
            ('other', 'Other')
        ]
    )
    date_range = models.CharField(max_length=50, blank=True, help_text='Q1_2024, FY_2023, etc')
    esrs_categories = models.JSONField(default=list, blank=True, help_text='[E1, E2, S1, etc]')
    language = models.CharField(max_length=10, default='en')
    
    class Meta:
        db_table = 'document_chunks'
        ordering = ['document', 'chunk_index']
        indexes = [
            models.Index(fields=['document', 'chunk_index']),
            models.Index(fields=['document_type']),
            models.Index(fields=['date_range']),
            GinIndex(fields=['esrs_categories'], name='esrs_cat_gin_idx'),
        ]
    
    def __str__(self):
        return f"{self.document.file_name} - Chunk {self.chunk_index}"
    
    def save(self, *args, **kwargs):
        """Auto-generate chunk_id and contextualized_content"""
        if not self.chunk_id:
            self.chunk_id = f"doc_{self.document_id}_chunk_{self.chunk_index}"
        
        if self.context and self.content and not self.contextualized_content:
            self.contextualized_content = f"{self.context}\n\n{self.content}"
        
        # Calculate counts
        if self.content:
            self.char_count = len(self.content)
            self.word_count = len(self.content.split())
            self.token_count = len(self.content) // 4  # Rough estimate
        
        super().save(*args, **kwargs)


class SearchQuery(models.Model):
    """
    Track search queries for RAG evaluation
    Used for hit rate, MRR, and relevance metrics
    """
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='search_queries')
    disclosure = models.ForeignKey(
        'ESRSDisclosure', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='search_queries'
    )
    
    # Query details
    query_text = models.TextField()
    query_variations = models.JSONField(default=list, blank=True, help_text='Multi-query expansion')
    
    # Search parameters
    search_method = models.CharField(
        max_length=20,
        choices=[
            ('hybrid', 'Hybrid (BM25 + Embeddings)'),
            ('semantic', 'Semantic Only'),
            ('bm25', 'BM25 Only'),
            ('full_text', 'Full Text')
        ],
        default='hybrid'
    )
    alpha = models.FloatField(default=0.5, help_text='Hybrid search weight (0=BM25, 1=semantic)')
    top_k = models.IntegerField(default=20, help_text='Number of results returned')
    use_reranking = models.BooleanField(default=True)
    
    # Retrieved chunks (for evaluation)
    retrieved_chunks = models.JSONField(
        default=list,
        blank=True,
        help_text='List of chunk IDs retrieved'
    )
    chunk_scores = models.JSONField(
        default=dict,
        blank=True,
        help_text='Scores for each retrieved chunk'
    )
    
    # Execution metrics
    retrieval_time_ms = models.IntegerField(default=0)
    reranking_time_ms = models.IntegerField(default=0)
    total_time_ms = models.IntegerField(default=0)
    
    # Quality metrics (RAG Triad)
    context_relevance = models.FloatField(null=True, blank=True, help_text='0.0-1.0')
    groundedness = models.FloatField(null=True, blank=True, help_text='0.0-1.0')
    answer_relevance = models.FloatField(null=True, blank=True, help_text='0.0-1.0')
    
    # Hit rate evaluation
    has_relevant_doc = models.BooleanField(default=False)
    first_relevant_rank = models.IntegerField(null=True, blank=True, help_text='For MRR calculation')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'search_queries'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['disclosure']),
            models.Index(fields=['search_method']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.query_text[:50]}"
    
    @property
    def mrr_score(self):
        """Mean Reciprocal Rank - position of first relevant result"""
        if self.first_relevant_rank:
            return 1.0 / self.first_relevant_rank
        return 0.0


class EmbeddingModel(models.Model):
    """
    Track different embedding models and their performance
    Allows A/B testing of models
    """
    name = models.CharField(max_length=100, unique=True)
    provider = models.CharField(
        max_length=50,
        choices=[
            ('openai', 'OpenAI'),
            ('cohere', 'Cohere'),
            ('voyage', 'Voyage AI'),
            ('jina', 'Jina AI'),
            ('huggingface', 'HuggingFace'),
            ('local', 'Local Model')
        ]
    )
    model_id = models.CharField(max_length=200, help_text='API model identifier')
    dimensions = models.IntegerField(help_text='Vector dimensions')
    
    # Cost per 1M tokens
    cost_per_1m_tokens = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    
    # Performance metrics (aggregated)
    avg_hit_rate = models.FloatField(default=0.0)
    avg_mrr = models.FloatField(default=0.0)
    avg_retrieval_time_ms = models.IntegerField(default=0)
    
    # Usage stats
    total_queries = models.IntegerField(default=0)
    total_embeddings_generated = models.IntegerField(default=0)
    
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'embedding_models'
        ordering = ['-avg_hit_rate']
    
    def __str__(self):
        return f"{self.name} ({self.provider})"
    
    def save(self, *args, **kwargs):
        """Ensure only one default model"""
        if self.is_default:
            EmbeddingModel.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class RerankerModel(models.Model):
    """
    Track reranker models and performance
    """
    name = models.CharField(max_length=100, unique=True)
    provider = models.CharField(
        max_length=50,
        choices=[
            ('cohere', 'Cohere Rerank'),
            ('bge', 'BGE Reranker'),
            ('jina', 'Jina Reranker'),
            ('cross_encoder', 'Cross-Encoder'),
        ]
    )
    model_id = models.CharField(max_length=200)
    
    # Cost per 1K searches
    cost_per_1k_searches = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    
    # Performance metrics
    avg_improvement = models.FloatField(default=0.0, help_text='% improvement in hit rate')
    avg_reranking_time_ms = models.IntegerField(default=0)
    
    total_rerank_operations = models.IntegerField(default=0)
    
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'reranker_models'
        ordering = ['-avg_improvement']
    
    def __str__(self):
        return f"{self.name} ({self.provider})"
    
    def save(self, *args, **kwargs):
        """Ensure only one default model"""
        if self.is_default:
            RerankerModel.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)
