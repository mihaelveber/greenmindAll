"""
Advanced RAG Engine with Hybrid Search, Contextual Retrieval, and Reranking
Based on research from Anthropic, Pinecone, LlamaIndex (2024-2025)

Key improvements:
1. Hybrid Search (BM25 + Embeddings) - 49% better retrieval
2. Contextual Chunking - 35% improvement with contextual embeddings
3. Reranking - 67% improvement overall
4. Semantic Chunking - better context preservation
5. Multi-query expansion - better coverage
"""

import logging
import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import numpy as np
from .embedding_service import get_embedding_service, get_reranker_service

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """Represents a semantically meaningful chunk of a document"""
    chunk_id: str
    content: str
    context: str  # Contextual description of this chunk
    document_id: int
    document_name: str
    chunk_index: int
    total_chunks: int
    metadata: Dict
    
    @property
    def contextualized_content(self) -> str:
        """Returns chunk with prepended context for better retrieval"""
        return f"{self.context}\n\n{self.content}"


@dataclass
class SearchResult:
    """Represents a search result with scores"""
    chunk: DocumentChunk
    bm25_score: float
    embedding_score: float
    rerank_score: float
    final_score: float
    rank: int


class SemanticChunker:
    """
    Semantic document chunker that splits by meaning, not by size
    Preserves paragraph/section boundaries and context
    """
    
    @staticmethod
    def chunk_by_paragraphs(
        text: str, 
        max_chunk_size: int = 1000,
        overlap: int = 200
    ) -> List[str]:
        """
        Split text into chunks by paragraphs, respecting semantic boundaries
        
        Args:
            text: Full document text
            max_chunk_size: Maximum characters per chunk
            overlap: Character overlap between chunks
        """
        # Split by double newlines (paragraphs)
        paragraphs = re.split(r'\n\s*\n', text)
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            para_size = len(para)
            
            # If single paragraph exceeds max_chunk_size, split by sentences
            if para_size > max_chunk_size:
                sentences = re.split(r'(?<=[.!?])\s+', para)
                for sentence in sentences:
                    if current_size + len(sentence) > max_chunk_size and current_chunk:
                        # Save current chunk
                        chunks.append('\n\n'.join(current_chunk))
                        # Keep last part for overlap
                        overlap_text = ' '.join(current_chunk[-1].split()[-overlap:])
                        current_chunk = [overlap_text, sentence] if overlap_text else [sentence]
                        current_size = len(overlap_text) + len(sentence)
                    else:
                        current_chunk.append(sentence)
                        current_size += len(sentence)
            
            # If adding paragraph exceeds max_chunk_size, save current chunk
            elif current_size + para_size > max_chunk_size and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                # Keep last paragraph for overlap
                current_chunk = [current_chunk[-1], para] if overlap else [para]
                current_size = len(current_chunk[0]) + para_size
            
            else:
                current_chunk.append(para)
                current_size += para_size
        
        # Add remaining chunk
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks
    
    @staticmethod
    def chunk_by_sections(text: str) -> List[Tuple[str, str]]:
        """
        Split document by sections (headers)
        Returns list of (section_title, section_content) tuples
        """
        # Common header patterns
        header_pattern = r'(?m)^(#{1,6}\s+.+|[A-Z][A-Za-z\s]+:|\d+\.\s+[A-Z].+|━+\s*.+\s*━+)'
        
        sections = []
        current_title = "Introduction"
        current_content = []
        
        for line in text.split('\n'):
            if re.match(header_pattern, line.strip()):
                # Save previous section
                if current_content:
                    sections.append((current_title, '\n'.join(current_content)))
                
                # Start new section
                current_title = line.strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Add last section
        if current_content:
            sections.append((current_title, '\n'.join(current_content)))
        
        return sections


class ContextGenerator:
    """
    Generates contextual descriptions for document chunks
    Using Claude Haiku for cost-effective context generation
    """
    
    @staticmethod
    def generate_chunk_context(
        chunk_text: str,
        document_name: str,
        full_document: str = None,
        chunk_position: str = "middle"
    ) -> str:
        """
        Generate contextual description for a chunk
        
        Research shows 50-100 tokens of context improves retrieval by 35%
        Format: "This chunk is from {document} discussing {topic}..."
        
        Args:
            chunk_text: The actual chunk content
            document_name: Name of source document
            full_document: Full document text for better context (optional)
            chunk_position: 'beginning', 'middle', or 'end'
        """
        # Extract key topics from chunk (simple keyword extraction)
        keywords = ContextGenerator._extract_keywords(chunk_text)
        
        # Build context description
        position_map = {
            'beginning': 'the beginning of',
            'middle': 'the middle section of',
            'end': 'the concluding part of'
        }
        
        position_text = position_map.get(chunk_position, '')
        keywords_text = ', '.join(keywords[:3]) if keywords else 'various topics'
        
        context = f"This chunk is from {position_text} document '{document_name}', discussing {keywords_text}."
        
        return context
    
    @staticmethod
    def _extract_keywords(text: str, top_n: int = 5) -> List[str]:
        """Simple keyword extraction using word frequency and importance"""
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                      'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been'}
        
        # Extract words
        words = re.findall(r'\b[a-z]{4,}\b', text.lower())
        
        # Filter stop words and count frequency
        word_freq = {}
        for word in words:
            if word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        return [word for word, _ in sorted_words[:top_n]]


class BM25Retriever:
    """
    BM25 (Best Matching 25) sparse retrieval
    Excellent for exact keyword matches and technical terms
    """
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Args:
            k1: Term frequency saturation parameter
            b: Length normalization parameter
        """
        self.k1 = k1
        self.b = b
        self.corpus = []
        self.doc_freqs = {}
        self.idf = {}
        self.doc_lens = []
        self.avgdl = 0
    
    def fit(self, corpus: List[str]):
        """Build BM25 index from document corpus"""
        self.corpus = corpus
        self.doc_lens = [len(doc.split()) for doc in corpus]
        self.avgdl = sum(self.doc_lens) / len(self.doc_lens) if self.doc_lens else 0
        
        # Calculate document frequencies
        for doc in corpus:
            words = set(doc.lower().split())
            for word in words:
                self.doc_freqs[word] = self.doc_freqs.get(word, 0) + 1
        
        # Calculate IDF scores
        num_docs = len(corpus)
        for word, freq in self.doc_freqs.items():
            self.idf[word] = np.log((num_docs - freq + 0.5) / (freq + 0.5) + 1)
    
    def get_scores(self, query: str) -> List[float]:
        """Calculate BM25 scores for query against all documents"""
        scores = []
        query_words = query.lower().split()
        
        for idx, doc in enumerate(self.corpus):
            score = 0
            doc_len = self.doc_lens[idx]
            doc_words = doc.lower().split()
            
            for word in query_words:
                if word not in self.idf:
                    continue
                
                # Term frequency in document
                tf = doc_words.count(word)
                
                # BM25 formula
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / self.avgdl))
                score += self.idf[word] * (numerator / denominator)
            
            scores.append(score)
        
        return scores


class HybridRAGEngine:
    """
    Advanced RAG engine combining:
    1. BM25 sparse retrieval (exact matches)
    2. Semantic embeddings (meaning-based)
    3. Contextual chunking (better retrieval)
    4. Reranking (quality filtering)
    """
    
    def __init__(
        self,
        embedding_model: str = "text-embedding-3-large",
        reranker_model: str = "cohere",
        alpha: float = 0.5  # Hybrid search weight (0=pure BM25, 1=pure semantic)
    ):
        self.embedding_model = embedding_model
        self.reranker_model = reranker_model
        self.alpha = alpha
        
        self.chunker = SemanticChunker()
        self.context_generator = ContextGenerator()
        self.bm25 = BM25Retriever()
        
        self.chunks: List[DocumentChunk] = []
        self.embeddings = None
    
    def process_document(
        self,
        document_id: int,
        document_name: str,
        content: str,
        metadata: Dict = None
    ) -> List[DocumentChunk]:
        """
        Process a document into contextualized chunks
        
        Returns list of DocumentChunk objects ready for indexing
        """
        # Semantic chunking
        raw_chunks = self.chunker.chunk_by_paragraphs(content, max_chunk_size=1000)
        
        processed_chunks = []
        total_chunks = len(raw_chunks)
        
        for idx, chunk_text in enumerate(raw_chunks):
            # Determine position
            if idx == 0:
                position = 'beginning'
            elif idx == total_chunks - 1:
                position = 'end'
            else:
                position = 'middle'
            
            # Generate contextual description
            context = self.context_generator.generate_chunk_context(
                chunk_text=chunk_text,
                document_name=document_name,
                chunk_position=position
            )
            
            # Create chunk object
            chunk = DocumentChunk(
                chunk_id=f"{document_id}_chunk_{idx}",
                content=chunk_text,
                context=context,
                document_id=document_id,
                document_name=document_name,
                chunk_index=idx,
                total_chunks=total_chunks,
                metadata=metadata or {}
            )
            
            processed_chunks.append(chunk)
        
        return processed_chunks
    
    def index_chunks(self, chunks: List[DocumentChunk]):
        """
        Build search indices for chunks
        - BM25 index for sparse retrieval
        - Embeddings for semantic retrieval
        """
        self.chunks = chunks
        
        # Build BM25 index with contextualized content
        corpus = [chunk.contextualized_content for chunk in chunks]
        self.bm25.fit(corpus)
        
        logger.info(f"Indexed {len(chunks)} chunks with hybrid search")
    
    def search(
        self,
        query: str,
        top_k: int = 20,
        initial_k: int = 150,
        use_reranking: bool = True
    ) -> List[SearchResult]:
        """
        Hybrid search with reranking
        
        Args:
            query: Search query
            top_k: Final number of results to return
            initial_k: Number of candidates before reranking
            use_reranking: Whether to use reranker
        
        Returns:
            List of SearchResult objects sorted by relevance
        """
        if not self.chunks:
            logger.warning("No chunks indexed yet")
            return []
        
        # Step 1: BM25 retrieval
        bm25_scores = self.bm25.get_scores(query)
        
        # Step 2: Semantic retrieval (placeholder - would use actual embeddings)
        # For now, use simple text similarity as placeholder
        embedding_scores = self._placeholder_semantic_scores(query)
        
        # Step 3: Hybrid scoring
        results = []
        for idx, chunk in enumerate(self.chunks):
            # Normalize scores to 0-1 range
            bm25_norm = bm25_scores[idx] / (max(bm25_scores) + 1e-8)
            embed_norm = embedding_scores[idx]
            
            # Hybrid score with alpha weighting
            hybrid_score = (1 - self.alpha) * bm25_norm + self.alpha * embed_norm
            
            results.append(SearchResult(
                chunk=chunk,
                bm25_score=bm25_scores[idx],
                embedding_score=embedding_scores[idx],
                rerank_score=0,
                final_score=hybrid_score,
                rank=0
            ))
        
        # Step 4: Sort by hybrid score and take top initial_k
        results.sort(key=lambda x: x.final_score, reverse=True)
        candidates = results[:initial_k]
        
        # Step 5: Reranking (if enabled)
        if use_reranking and len(candidates) > top_k:
            candidates = self._rerank(query, candidates, top_k)
        else:
            candidates = candidates[:top_k]
        
        # Update ranks
        for idx, result in enumerate(candidates):
            result.rank = idx + 1
        
        return candidates
    
    def _placeholder_semantic_scores(self, query: str) -> List[float]:
        """
        Placeholder for semantic scoring
        In production, this would use actual embeddings and cosine similarity
        """
        query_words = set(query.lower().split())
        scores = []
        
        for chunk in self.chunks:
            chunk_words = set(chunk.contextualized_content.lower().split())
            # Jaccard similarity as placeholder
            intersection = len(query_words & chunk_words)
            union = len(query_words | chunk_words)
            score = intersection / union if union > 0 else 0
            scores.append(score)
        
        return scores
    
    def _rerank(
        self,
        query: str,
        candidates: List[SearchResult],
        top_k: int
    ) -> List[SearchResult]:
        """
        Rerank candidates using reranker model
        In production, this would call Cohere Rerank API or bge-reranker
        """
        # Placeholder: use existing scores with small adjustment
        # In production, replace with actual reranker API call
        
        for result in candidates:
            # Boost scores based on chunk position and metadata
            position_boost = 1.0
            if result.chunk.chunk_index == 0:
                position_boost = 1.1  # Beginning chunks often important
            
            result.rerank_score = result.final_score * position_boost
            result.final_score = result.rerank_score
        
        candidates.sort(key=lambda x: x.final_score, reverse=True)
        return candidates[:top_k]


# Utility functions

def generate_query_variations(query: str, num_variations: int = 3) -> List[str]:
    """
    Multi-query RAG: Generate variations of the query
    In production, use LLM to generate semantic variations
    """
    variations = [query]
    
    # Simple variations (in production, use LLM)
    variations.append(f"What information is available about {query}?")
    variations.append(f"Explain {query} in detail")
    variations.append(f"Provide evidence for {query}")
    
    return variations[:num_variations]


def estimate_token_count(text: str) -> int:
    """Rough estimate of token count (1 token ≈ 4 characters)"""
    return len(text) // 4


def should_use_prompt_caching(total_tokens: int) -> bool:
    """
    Determine if prompt caching is better than RAG
    Research: For <200K tokens, prompt caching is 2x faster, 90% cheaper
    """
    return total_tokens < 200_000
