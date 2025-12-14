"""
Management command to populate embedding and reranker models
Sets up default models for RAG system
"""

from django.core.management.base import BaseCommand
from accounts.vector_models import EmbeddingModel, RerankerModel


class Command(BaseCommand):
    help = 'Populate embedding and reranker models with defaults'

    def handle(self, *args, **options):
        self.stdout.write('Setting up embedding models...')
        
        # OpenAI models
        openai_large, created = EmbeddingModel.objects.get_or_create(
            name='OpenAI text-embedding-3-large',
            defaults={
                'provider': 'openai',
                'model_id': 'text-embedding-3-large',
                'dimensions': 3072,
                'cost_per_1m_tokens': 0.13,
                'is_default': True,
                'is_active': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created {openai_large.name}'))
        else:
            self.stdout.write(f'- {openai_large.name} already exists')
        
        openai_small, created = EmbeddingModel.objects.get_or_create(
            name='OpenAI text-embedding-3-small',
            defaults={
                'provider': 'openai',
                'model_id': 'text-embedding-3-small',
                'dimensions': 1536,
                'cost_per_1m_tokens': 0.02,
                'is_active': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created {openai_small.name}'))
        
        # Voyage AI models
        voyage_large, created = EmbeddingModel.objects.get_or_create(
            name='Voyage AI Large v2',
            defaults={
                'provider': 'voyage',
                'model_id': 'voyage-large-2',
                'dimensions': 1536,
                'cost_per_1m_tokens': 0.12,
                'is_active': False,  # Not active until API key configured
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created {voyage_large.name}'))
        
        voyage_standard, created = EmbeddingModel.objects.get_or_create(
            name='Voyage AI v2',
            defaults={
                'provider': 'voyage',
                'model_id': 'voyage-2',
                'dimensions': 1024,
                'cost_per_1m_tokens': 0.10,
                'is_active': False,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created {voyage_standard.name}'))
        
        # Jina AI models (best hit rate: 0.933)
        jina_base, created = EmbeddingModel.objects.get_or_create(
            name='Jina AI Base v2',
            defaults={
                'provider': 'jina',
                'model_id': 'jina-embeddings-v2-base-en',
                'dimensions': 768,
                'cost_per_1m_tokens': 0.02,
                'is_active': False,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created {jina_base.name}'))
        
        jina_small, created = EmbeddingModel.objects.get_or_create(
            name='Jina AI Small v2',
            defaults={
                'provider': 'jina',
                'model_id': 'jina-embeddings-v2-small-en',
                'dimensions': 512,
                'cost_per_1m_tokens': 0.01,
                'is_active': False,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created {jina_small.name}'))
        
        # Cohere models
        cohere_english, created = EmbeddingModel.objects.get_or_create(
            name='Cohere Embed English v3',
            defaults={
                'provider': 'cohere',
                'model_id': 'embed-english-v3.0',
                'dimensions': 1024,
                'cost_per_1m_tokens': 0.10,
                'is_active': False,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created {cohere_english.name}'))
        
        self.stdout.write('\nSetting up reranker models...')
        
        # Cohere rerankers (best performance: 0.927-0.933 hit rate)
        cohere_rerank, created = RerankerModel.objects.get_or_create(
            name='Cohere Rerank English v3',
            defaults={
                'provider': 'cohere',
                'model_id': 'rerank-english-v3.0',
                'cost_per_1k_searches': 2.00,
                'is_default': True,
                'is_active': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created {cohere_rerank.name}'))
        else:
            self.stdout.write(f'- {cohere_rerank.name} already exists')
        
        cohere_multilingual, created = RerankerModel.objects.get_or_create(
            name='Cohere Rerank Multilingual v3',
            defaults={
                'provider': 'cohere',
                'model_id': 'rerank-multilingual-v3.0',
                'cost_per_1k_searches': 2.00,
                'is_active': False,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created {cohere_multilingual.name}'))
        
        # BGE rerankers (free, local)
        bge_large, created = RerankerModel.objects.get_or_create(
            name='BGE Reranker Large',
            defaults={
                'provider': 'bge',
                'model_id': 'bge-reranker-large',
                'cost_per_1k_searches': 0.00,
                'is_active': False,  # Requires model download
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created {bge_large.name}'))
        
        bge_base, created = RerankerModel.objects.get_or_create(
            name='BGE Reranker Base',
            defaults={
                'provider': 'bge',
                'model_id': 'bge-reranker-base',
                'cost_per_1k_searches': 0.00,
                'is_active': False,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created {bge_base.name}'))
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('✓ Successfully populated embedding and reranker models'))
        self.stdout.write('='*60)
        
        # Show active models
        active_embedding = EmbeddingModel.objects.filter(is_active=True).count()
        default_embedding = EmbeddingModel.objects.filter(is_default=True).first()
        active_reranker = RerankerModel.objects.filter(is_active=True).count()
        default_reranker = RerankerModel.objects.filter(is_default=True).first()
        
        self.stdout.write(f'\nActive embedding models: {active_embedding}')
        if default_embedding:
            self.stdout.write(f'Default: {default_embedding.name} ({default_embedding.dimensions}D)')
        
        self.stdout.write(f'\nActive reranker models: {active_reranker}')
        if default_reranker:
            self.stdout.write(f'Default: {default_reranker.name}')
        
        self.stdout.write('\n' + self.style.WARNING('Note: Configure API keys in settings for non-OpenAI models:'))
        self.stdout.write('  - VOYAGE_API_KEY for Voyage AI')
        self.stdout.write('  - JINA_API_KEY for Jina AI')
        self.stdout.write('  - COHERE_API_KEY for Cohere (embeddings + reranking)')
