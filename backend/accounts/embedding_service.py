"""
Embedding Service - Support multiple embedding providers
Allows switching between OpenAI, Voyage, Jina, Cohere models
Based on LlamaIndex research showing JinaAI-Base + CohereRerank = 0.933 hit rate
"""

import logging
from typing import List, Optional, Dict
import numpy as np
from django.conf import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Universal embedding service supporting multiple providers
    Automatically handles API calls, caching, and model selection
    """
    
    SUPPORTED_MODELS = {
        'openai': {
            'text-embedding-3-small': {'dimensions': 1536, 'cost_per_1m': 0.02},
            'text-embedding-3-large': {'dimensions': 3072, 'cost_per_1m': 0.13},
            'text-embedding-ada-002': {'dimensions': 1536, 'cost_per_1m': 0.10},
        },
        'voyage': {
            'voyage-large-2': {'dimensions': 1536, 'cost_per_1m': 0.12},
            'voyage-code-2': {'dimensions': 1536, 'cost_per_1m': 0.12},
            'voyage-2': {'dimensions': 1024, 'cost_per_1m': 0.10},
        },
        'jina': {
            'jina-embeddings-v2-base-en': {'dimensions': 768, 'cost_per_1m': 0.02},
            'jina-embeddings-v2-small-en': {'dimensions': 512, 'cost_per_1m': 0.01},
        },
        'cohere': {
            'embed-english-v3.0': {'dimensions': 1024, 'cost_per_1m': 0.10},
            'embed-multilingual-v3.0': {'dimensions': 1024, 'cost_per_1m': 0.10},
        }
    }
    
    def __init__(self, provider: str = 'openai', model: str = None):
        """
        Initialize embedding service
        
        Args:
            provider: 'openai', 'voyage', 'jina', 'cohere'
            model: Specific model name (optional, uses default if not specified)
        """
        self.provider = provider.lower()
        self.model = model or self._get_default_model()
        self.client = None
        
        self._validate_provider()
        self._initialize_client()
    
    def _get_default_model(self) -> str:
        """Get default model for provider"""
        defaults = {
            'openai': 'text-embedding-3-large',
            'voyage': 'voyage-large-2',
            'jina': 'jina-embeddings-v2-base-en',
            'cohere': 'embed-english-v3.0'
        }
        return defaults.get(self.provider, 'text-embedding-3-large')
    
    def _validate_provider(self):
        """Validate provider and model combination"""
        if self.provider not in self.SUPPORTED_MODELS:
            raise ValueError(f"Unsupported provider: {self.provider}")
        
        if self.model not in self.SUPPORTED_MODELS[self.provider]:
            available = list(self.SUPPORTED_MODELS[self.provider].keys())
            raise ValueError(
                f"Model '{self.model}' not available for {self.provider}. "
                f"Available: {available}"
            )
    
    def _initialize_client(self):
        """Initialize API client for provider"""
        try:
            if self.provider == 'openai':
                import openai
                api_key = getattr(settings, 'OPENAI_API_KEY', None)
                if not api_key:
                    raise ValueError("OPENAI_API_KEY not found in settings. Please add it to use OpenAI embeddings.")
                self.client = openai.OpenAI(api_key=api_key)
            
            elif self.provider == 'voyage':
                import voyageai
                api_key = getattr(settings, 'VOYAGE_API_KEY', None)
                if not api_key:
                    raise ValueError("VOYAGE_API_KEY not found in settings. Please add it to use Voyage AI embeddings.")
                self.client = voyageai.Client(api_key=api_key)
            
            elif self.provider == 'jina':
                import requests
                self.client = requests.Session()
                api_key = getattr(settings, 'JINA_API_KEY', None)
                if not api_key:
                    logger.warning("JINA_API_KEY not found. Jina embeddings will not work.")
                else:
                    self.client.headers.update({'Authorization': f'Bearer {api_key}'})
            
            elif self.provider == 'cohere':
                import cohere
                api_key = getattr(settings, 'COHERE_API_KEY', None)
                if not api_key:
                    raise ValueError("COHERE_API_KEY not found in settings. Please add it to use Cohere embeddings.")
                self.client = cohere.Client(api_key)
            
            logger.info(f"Initialized {self.provider} embedding client with model {self.model}")
        
        except ImportError as e:
            logger.error(f"Failed to import {self.provider} library: {e}")
            raise
        except ValueError as e:
            logger.error(f"API key missing for {self.provider}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize {self.provider} client: {e}")
            raise
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for single text
        
        Args:
            text: Input text to embed
        
        Returns:
            List of floats representing the embedding vector
        """
        return self.embed_batch([text])[0]
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for batch of texts
        More efficient than multiple single calls
        
        Args:
            texts: List of texts to embed
        
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        try:
            if self.provider == 'openai':
                response = self.client.embeddings.create(
                    model=self.model,
                    input=texts
                )
                return [data.embedding for data in response.data]
            
            elif self.provider == 'voyage':
                response = self.client.embed(
                    texts=texts,
                    model=self.model
                )
                return response.embeddings
            
            elif self.provider == 'jina':
                url = "https://api.jina.ai/v1/embeddings"
                response = self.client.post(
                    url,
                    json={
                        'model': self.model,
                        'input': texts
                    }
                )
                response.raise_for_status()
                data = response.json()
                return [item['embedding'] for item in data['data']]
            
            elif self.provider == 'cohere':
                response = self.client.embed(
                    texts=texts,
                    model=self.model
                )
                return response.embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings with {self.provider}: {e}")
            raise
    
    def get_dimensions(self) -> int:
        """Get embedding dimensions for current model"""
        return self.SUPPORTED_MODELS[self.provider][self.model]['dimensions']
    
    def get_cost_per_1m_tokens(self) -> float:
        """Get cost per 1M tokens for current model"""
        return self.SUPPORTED_MODELS[self.provider][self.model]['cost_per_1m']
    
    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)
        
        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    @staticmethod
    def batch_cosine_similarity(query_vec: List[float], doc_vecs: List[List[float]]) -> List[float]:
        """
        Calculate cosine similarity between query and multiple documents
        Vectorized for efficiency
        """
        query_np = np.array(query_vec)
        docs_np = np.array(doc_vecs)
        
        # Normalize query
        query_norm = query_np / np.linalg.norm(query_np)
        
        # Normalize documents
        doc_norms = docs_np / np.linalg.norm(docs_np, axis=1, keepdims=True)
        
        # Compute similarities
        similarities = np.dot(doc_norms, query_norm)
        
        return similarities.tolist()


class RerankerService:
    """
    Reranking service supporting multiple providers
    Research: Cohere Rerank achieves 0.927-0.933 hit rate
    """
    
    SUPPORTED_MODELS = {
        'cohere': {
            'rerank-english-v3.0': {'cost_per_1k': 2.00},
            'rerank-multilingual-v3.0': {'cost_per_1k': 2.00},
        },
        'bge': {
            'bge-reranker-large': {'cost_per_1k': 0},  # Free, local model
            'bge-reranker-base': {'cost_per_1k': 0},
        }
    }
    
    def __init__(self, provider: str = 'cohere', model: str = None):
        """
        Initialize reranker service
        
        Args:
            provider: 'cohere' or 'bge'
            model: Specific model name
        """
        self.provider = provider.lower()
        self.model = model or self._get_default_model()
        self.client = None
        
        self._initialize_client()
    
    def _get_default_model(self) -> str:
        defaults = {
            'cohere': 'rerank-english-v3.0',
            'bge': 'bge-reranker-large'
        }
        return defaults.get(self.provider, 'rerank-english-v3.0')
    
    def _initialize_client(self):
        """Initialize reranker client"""
        try:
            if self.provider == 'cohere':
                import cohere
                api_key = getattr(settings, 'COHERE_API_KEY', None)
                if not api_key:
                    raise ValueError("COHERE_API_KEY not found in settings")
                self.client = cohere.Client(api_key)
            
            elif self.provider == 'bge':
                from sentence_transformers import CrossEncoder
                self.client = CrossEncoder(f'BAAI/{self.model}')
            
            logger.info(f"Initialized {self.provider} reranker with model {self.model}")
        
        except Exception as e:
            logger.error(f"Failed to initialize {self.provider} reranker: {e}")
            raise
    
    def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int = 20
    ) -> List[Dict]:
        """
        Rerank documents by relevance to query
        
        Args:
            query: Search query
            documents: List of document texts
            top_k: Number of top results to return
        
        Returns:
            List of dicts with 'index', 'text', 'score'
        """
        try:
            if self.provider == 'cohere':
                response = self.client.rerank(
                    query=query,
                    documents=documents,
                    model=self.model,
                    top_n=top_k
                )
                
                return [
                    {
                        'index': result.index,
                        'text': documents[result.index],
                        'score': result.relevance_score
                    }
                    for result in response.results
                ]
            
            elif self.provider == 'bge':
                # Create query-document pairs
                pairs = [[query, doc] for doc in documents]
                
                # Get scores
                scores = self.client.predict(pairs)
                
                # Sort by score and take top_k
                ranked = sorted(
                    enumerate(scores),
                    key=lambda x: x[1],
                    reverse=True
                )[:top_k]
                
                return [
                    {
                        'index': idx,
                        'text': documents[idx],
                        'score': float(score)
                    }
                    for idx, score in ranked
                ]
        
        except Exception as e:
            logger.error(f"Reranking failed with {self.provider}: {e}")
            raise


# Factory functions for easy instantiation

def get_embedding_service(
    provider: Optional[str] = None,
    model: Optional[str] = None
) -> Optional[EmbeddingService]:
    """
    Get embedding service instance with fallback logic
    Returns None if no valid provider with API key is found
    """
    from django.conf import settings
    
    if not provider:
        # Get default from database
        from accounts.vector_models import EmbeddingModel
        try:
            # Try to find active model with available API key
            active_models = EmbeddingModel.objects.filter(is_active=True).order_by('-is_default')
            
            for model_obj in active_models:
                test_provider = model_obj.provider
                test_model = model_obj.model_id
                
                # Check if API key exists
                api_key_name = f'{test_provider.upper()}_API_KEY'
                api_key = getattr(settings, api_key_name, None)
                
                if api_key:
                    provider = test_provider
                    model = test_model
                    logger.info(f"Using {provider}/{model} (API key found)")
                    break
            else:
                # No model with API key found
                logger.warning("No embedding model with valid API key found. Please configure API keys in settings.")
                return None
                
        except Exception as e:
            logger.error(f"Error finding embedding model: {e}")
            return None
    
    try:
        return EmbeddingService(provider=provider, model=model)
    except ValueError as e:
        logger.error(f"Cannot create embedding service: {e}")
        return None


def get_reranker_service(
    provider: Optional[str] = None,
    model: Optional[str] = None
) -> RerankerService:
    """
    Get reranker service instance
    Uses default from database RerankerModel if not specified
    """
    if not provider:
        # Get default from database
        from accounts.vector_models import RerankerModel
        try:
            default_model = RerankerModel.objects.filter(
                is_default=True,
                is_active=True
            ).first()
            
            if default_model:
                provider = default_model.provider
                model = default_model.model_id
            else:
                provider = 'cohere'
                model = 'rerank-english-v3.0'
        except Exception:
            provider = 'cohere'
            model = 'rerank-english-v3.0'
    
    return RerankerService(provider=provider, model=model)
