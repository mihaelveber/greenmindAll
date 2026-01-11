"""
RAG TIER Engine - Unified TIER 1 + TIER 2 + TIER 3 logic
Used by both conversation_api.py and tasks.py
"""

import logging
import json
from typing import List, Tuple, Dict, Any, Optional
from accounts.models import DocumentChunk, User
from accounts.embedding_service import EmbeddingService
from accounts.llm_router import LLMRouter, LLMModel
from rank_bm25 import BM25Okapi

logger = logging.getLogger(__name__)


def run_tier_rag(
    user: User,
    query_text: str,
    relevant_doc_ids: List[int],
    temperature: float = 0.2
) -> Tuple[str, List[Dict], float, List[Dict]]:
    """
    Run TIER 1 + TIER 2 RAG pipeline
    
    Args:
        user: User object with RAG settings
        query_text: User's question or disclosure requirement
        relevant_doc_ids: List of document IDs to search
        temperature: AI temperature setting
        
    Returns:
        Tuple of (context_string, top_chunks, avg_confidence, processing_steps)
    """
    
    processing_steps = []
    
    # Get user's RAG settings
    tier1_enabled = user.rag_tier1_enabled
    tier2_threshold = user.rag_tier2_threshold
    
    # Get all chunks from relevant documents
    all_chunks = list(DocumentChunk.objects.filter(
        document_id__in=relevant_doc_ids
    ).select_related('document').order_by('document_id', 'chunk_index'))
    
    logger.info(f"[RAG] Found {len(all_chunks)} total chunks from {len(relevant_doc_ids)} documents")
    
    if not all_chunks:
        logger.warning("[RAG] No chunks available")
        return "", [], 0.0, []
    
    # TIER 2: Multi-Query Generation (if threshold met)
    query_variations = [query_text]  # Start with original
    use_tier2 = False  # We'll decide after initial search
    
    processing_steps.append({
        "step": "tier_check",
        "status": "completed",
        "message": f"TIER 1: {'Enabled' if tier1_enabled else 'Disabled'}, TIER 2 threshold: {tier2_threshold}%",
        "result": f"TIER 1: {tier1_enabled}"
    })
    
    # TIER 1: Hybrid BM25 + Embeddings (if enabled)
    if tier1_enabled:
        processing_steps.append({
            "step": "tier1_hybrid",
            "status": "in_progress",
            "message": "Running TIER 1: Hybrid BM25+Embeddings search..."
        })
        
        embedding_service = EmbeddingService()
        all_scored_chunks = []
        
        for query in query_variations:
            # BM25 Keyword Search
            chunk_texts = [chunk.content for chunk in all_chunks]
            tokenized_corpus = [text.lower().split() for text in chunk_texts]
            bm25 = BM25Okapi(tokenized_corpus)
            tokenized_query = query.lower().split()
            bm25_scores = bm25.get_scores(tokenized_query)
            
            # Normalize
            max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1
            bm25_scores_norm = [score / max_bm25 for score in bm25_scores]
            
            # Semantic Embedding Search
            query_embedding = embedding_service.embed_text(query)
            
            semantic_scores = []
            if query_embedding:
                for chunk in all_chunks:
                    if chunk.embedding is not None:
                        similarity = embedding_service.cosine_similarity(query_embedding, chunk.embedding)
                        semantic_scores.append(similarity)
                    else:
                        semantic_scores.append(0.0)
            else:
                semantic_scores = [0.0] * len(all_chunks)
            
            # Hybrid Score: 60% semantic + 40% BM25
            for i in range(len(all_chunks)):
                hybrid_score = (0.6 * semantic_scores[i]) + (0.4 * bm25_scores_norm[i])
                all_scored_chunks.append((all_chunks[i], hybrid_score, semantic_scores[i], bm25_scores_norm[i]))
        
        # Deduplicate and average scores
        chunk_score_map = {}
        for chunk, hybrid, semantic, bm25 in all_scored_chunks:
            if chunk.id not in chunk_score_map:
                chunk_score_map[chunk.id] = {
                    'chunk': chunk,
                    'hybrid_scores': [],
                    'semantic_scores': [],
                    'bm25_scores': []
                }
            chunk_score_map[chunk.id]['hybrid_scores'].append(hybrid)
            chunk_score_map[chunk.id]['semantic_scores'].append(semantic)
            chunk_score_map[chunk.id]['bm25_scores'].append(bm25)
        
        averaged_chunks = []
        for chunk_id, data in chunk_score_map.items():
            avg_hybrid = sum(data['hybrid_scores']) / len(data['hybrid_scores'])
            avg_semantic = sum(data['semantic_scores']) / len(data['semantic_scores'])
            avg_bm25 = sum(data['bm25_scores']) / len(data['bm25_scores'])
            averaged_chunks.append((data['chunk'], avg_hybrid, avg_semantic, avg_bm25))
        
        # Sort and take top 10
        averaged_chunks.sort(key=lambda x: x[1], reverse=True)
        top_chunks = averaged_chunks[:10]
        
        avg_confidence = sum(score[1] for score in top_chunks) / len(top_chunks) if top_chunks else 0
        
        processing_steps[-1]["status"] = "completed"
        processing_steps[-1]["result"] = f"Top 10 chunks, {avg_confidence:.1%} confidence"
        
        logger.info(f"[RAG] TIER 1 complete: Top 10 chunks, avg confidence: {avg_confidence:.2%}")
        
        # TIER 2 always enabled - no confidence check
        use_tier2 = True
        logger.info(f"[RAG] TIER 2 always enabled (confidence: {avg_confidence:.2%})")
    else:
        # TIER 1 disabled - use simple semantic search
        processing_steps.append({
            "step": "semantic_only",
            "status": "in_progress",
            "message": "TIER 1 disabled - using semantic search only..."
        })
        
        embedding_service = EmbeddingService()
        query_embedding = embedding_service.embed_text(query_text)
        
        chunk_similarities = []
        if query_embedding:
            for chunk in all_chunks:
                if chunk.embedding is not None:
                    similarity = embedding_service.cosine_similarity(query_embedding, chunk.embedding)
                    chunk_similarities.append((chunk, similarity, similarity, 0.0))
        
        chunk_similarities.sort(key=lambda x: x[1], reverse=True)
        top_chunks = chunk_similarities[:10]
        avg_confidence = sum(score[1] for score in top_chunks) / len(top_chunks) if top_chunks else 0
        
        processing_steps[-1]["status"] = "completed"
        processing_steps[-1]["result"] = f"Top 10 chunks, {avg_confidence:.1%} confidence"
        
        # TIER 2 always enabled - no confidence check
        use_tier2 = True
    
    # TIER 2: Document Expansion (always executed)
    expanded_chunks = []
    if use_tier2:
        processing_steps.append({
            "step": "tier2_expansion",
            "status": "in_progress",
            "message": "Running TIER 2: Document Expansion..."
        })
        
        chunk_lookup = {chunk.id: chunk for chunk in all_chunks}
        
        for chunk, hybrid_score, semantic_score, bm25_score in top_chunks:
            # Add main chunk
            expanded_chunks.append((chunk, hybrid_score, semantic_score, bm25_score, 'main'))
            
            # Find neighbors
            neighbors = DocumentChunk.objects.filter(
                document_id=chunk.document_id,
                chunk_index__in=[chunk.chunk_index - 1, chunk.chunk_index + 1]
            )
            
            for neighbor in neighbors:
                expanded_chunks.append((
                    neighbor,
                    hybrid_score * 0.7,
                    semantic_score * 0.7,
                    bm25_score * 0.7,
                    'neighbor'
                ))
        
        processing_steps[-1]["status"] = "completed"
        processing_steps[-1]["result"] = f"{len(expanded_chunks)} total chunks"
        
        logger.info(f"[RAG] TIER 2 complete: Expanded to {len(expanded_chunks)} chunks")
    else:
        # No expansion needed
        expanded_chunks = [(chunk, hybrid_score, semantic_score, bm25_score, 'main') 
                          for chunk, hybrid_score, semantic_score, bm25_score in top_chunks]
        
        processing_steps.append({
            "step": "tier2_skip",
            "status": "completed",
            "message": "TIER 2 skipped - confidence sufficient",
            "result": f"Confidence {avg_confidence:.1%} >= {tier2_threshold}%"
        })
    
    # Build context
    processing_steps.append({
        "step": "context_building",
        "status": "in_progress",
        "message": "Building context..."
    })
    
    doc_chunks = {}
    for chunk, hybrid_score, semantic_score, bm25_score, chunk_type in expanded_chunks:
        doc_id = chunk.document.id
        if doc_id not in doc_chunks:
            doc_chunks[doc_id] = {
                'document': chunk.document,
                'chunks': []
            }
        doc_chunks[doc_id]['chunks'].append((chunk, hybrid_score, semantic_score, bm25_score, chunk_type))
    
    document_context = ""
    for doc_id, data in doc_chunks.items():
        doc = data['document']
        chunks = sorted(data['chunks'], key=lambda x: x[0].chunk_index)
        
        max_score = max(c[1] for c in chunks)
        document_context += f"\n\n=== {doc.file_name} (max relevance: {max_score:.2%}) ===\n"
        
        for chunk, hybrid_score, semantic_score, bm25_score, chunk_type in chunks:
            marker = "⭐" if chunk_type == "main" else "↔️"
            document_context += f"{marker} {chunk.content}\n"
    
    processing_steps[-1]["status"] = "completed"
    processing_steps[-1]["result"] = f"{len(doc_chunks)} documents"
    
    logger.info(f"[RAG] Context built from {len(doc_chunks)} documents, {len(expanded_chunks)} chunks")
    
    return document_context, expanded_chunks, avg_confidence, processing_steps


def run_tier3_refinement(
    user: User,
    query_text: str,
    context: str,
    initial_answer: str,
    confidence: float,
    expanded_chunks: List[Tuple],
    processing_steps: List[Dict]
) -> Tuple[str, float, List[Dict]]:
    """
    TIER 3: LLM Self-Reflection + Query Reformulation + Reranking
    
    Triggered when confidence < tier3_threshold (default 70%)
    Uses LLM to:
    1. Critique the initial answer
    2. Reformulate query if needed
    3. Rerank documents with cross-encoder logic
    4. Regenerate answer if quality insufficient
    
    Args:
        user: User object with RAG and LLM settings
        query_text: Original user question
        context: Document context from TIER 1/2
        initial_answer: First answer generated
        confidence: Confidence score from TIER 1/2
        expanded_chunks: Chunks from TIER 1/2
        processing_steps: Existing processing steps
        
    Returns:
        Tuple of (refined_answer, new_confidence, updated_processing_steps)
    """
    
    tier3_enabled = user.rag_tier3_enabled
    tier3_threshold = user.rag_tier3_threshold
    
    if not tier3_enabled:
        logger.info("[TIER 3] Disabled - skipping")
        processing_steps.append({
            "step": "tier3_skip",
            "status": "completed",
            "message": "TIER 3 disabled",
            "result": "Using TIER 2 answer"
        })
        return initial_answer, confidence, processing_steps
    
    # TIER 3 always executes when enabled - no confidence check
    logger.info(f"[TIER 3] Starting (always enabled) - current confidence: {confidence:.2%}")
    
    processing_steps.append({
        "step": "tier3_critique",
        "status": "in_progress",
        "message": "TIER 3: LLM self-critique..."
    })
    
    try:
        llm_router = LLMRouter()
        preferred_model = getattr(user, 'preferred_llm_model', 'gpt-4o')
        
        # Convert string to LLMModel enum
        try:
            model_enum = LLMModel(preferred_model)
        except ValueError:
            logger.warning(f"[TIER 3] Invalid model '{preferred_model}', using GPT-4o")
            model_enum = LLMModel.GPT_4O
        
        # Step 1: Self-Critique
        critique_prompt = f"""You are a quality assessment expert. Evaluate this AI-generated answer.

ORIGINAL QUESTION:
{query_text}

ANSWER TO EVALUATE:
{initial_answer}

AVAILABLE CONTEXT:
{context[:2000]}...

Evaluate the answer on these criteria:
1. **Completeness**: Does it fully answer the question? (0-100)
2. **Accuracy**: Is the information correct based on context? (0-100)
3. **Relevance**: Does it address the exact question? (0-100)
4. **Clarity**: Is it well-structured and clear? (0-100)

Provide your evaluation in JSON format:
{{
    "completeness_score": <0-100>,
    "accuracy_score": <0-100>,
    "relevance_score": <0-100>,
    "clarity_score": <0-100>,
    "overall_score": <average of above>,
    "issues": ["list of specific problems"],
    "missing_information": ["what key points are missing"],
    "suggestion": "how to improve the answer"
}}

Be critical - only scores >80 are acceptable."""

        critique_messages = [
            {"role": "system", "content": "You are a quality assessment expert. Provide honest, critical evaluations."},
            {"role": "user", "content": critique_prompt}
        ]
        
        critique_response = llm_router.generate(
            model=model_enum,
            messages=critique_messages,
            temperature=0.1,
            max_tokens=1000
        )
        
        critique_text = critique_response['message']['content']
        
        # Parse critique (try to extract JSON)
        try:
            # Find JSON in response
            import re
            json_match = re.search(r'\{[\s\S]*\}', critique_text)
            if json_match:
                critique_data = json.loads(json_match.group())
            else:
                # Fallback if no JSON found
                critique_data = {
                    "overall_score": 75,
                    "issues": ["Unable to parse critique"],
                    "suggestion": "Regenerate with better context"
                }
        except json.JSONDecodeError:
            logger.warning("[TIER 3] Failed to parse critique JSON")
            critique_data = {
                "overall_score": 75,
                "issues": ["Critique parsing failed"],
                "suggestion": critique_text[:200]
            }
        
        overall_score = critique_data.get('overall_score', 75)
        
        processing_steps[-1]["status"] = "completed"
        processing_steps[-1]["result"] = f"Quality score: {overall_score}/100"
        processing_steps[-1]["details"] = critique_data
        
        logger.info(f"[TIER 3] Self-critique score: {overall_score}/100")
        
        # Step 2: Query Reformulation (always executed)
        processing_steps.append({
            "step": "tier3_reformulation",
            "status": "in_progress",
            "message": "TIER 3: Query reformulation..."
        })
        
        reformulation_prompt = f"""Reformulate this query to find ACTUAL DATA in company documents.

ORIGINAL QUERY:
{query_text}

CRITICAL RULES - READ CAREFULLY:
1. We are searching company DOCUMENTS for ACTUAL DATA (numbers, percentages, statistics)
2. DO NOT ask about "what is required" or "what should be disclosed" - we already know that!
3. Instead, ask about ACTUAL VALUES and SPECIFIC DATA in documents
4. Focus on finding: numbers, percentages, ratios, counts, trends

BAD REFORMULATION (asking about requirements):
"What diversity metrics are required under ESRS S1-9?"

GOOD REFORMULATION (asking for actual data):
"What are the actual percentages of women in workforce, management, and leadership positions?"

Generate 3 queries that ask for ACTUAL DATA VALUES, not ESRS requirements:

Return JSON:
{{
    "reformulated_queries": ["query asking for actual data 1", "query asking for actual data 2", "query asking for actual data 3"],
    "reasoning": "why these find actual data values"
}}"""

        reformulation_messages = [
            {"role": "system", "content": "You reformulate queries to find ACTUAL DATA VALUES in company documents. Never ask about standards or requirements - only ask for actual numbers and statistics."},
            {"role": "user", "content": reformulation_prompt}
        ]
        
        reformulation_response = llm_router.generate(
            model=model_enum,
            messages=reformulation_messages,
            temperature=0.3,
            max_tokens=500
        )
        
        reformulation_text = reformulation_response['message']['content']
        
        reformulated_query = query_text  # Default fallback
        try:
            import re
            json_match = re.search(r'\{[\s\S]*\}', reformulation_text)
            if json_match:
                reformulation_data = json.loads(json_match.group())
                reformulated_queries = reformulation_data.get('reformulated_queries', [query_text])
                reformulated_query = reformulated_queries[0] if reformulated_queries else query_text
            else:
                reformulated_query = query_text
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"[TIER 3] Failed to parse reformulation: {e}")
            reformulated_query = query_text
        
        processing_steps[-1]["status"] = "completed"
        processing_steps[-1]["result"] = f"Reformulated: '{reformulated_query[:80]}...'"
        
        logger.info(f"[TIER 3] Query reformulated: {reformulated_query}")
        
        # Step 3: Reranking with LLM (cross-encoder simulation)
        processing_steps.append({
            "step": "tier3_reranking",
            "status": "in_progress",
            "message": "TIER 3: LLM-based reranking..."
        })
        
        # Take top 5 chunks and rerank them
        top_5_chunks = expanded_chunks[:5]
        reranking_prompt = f"""Rerank these document chunks by relevance to the question.

QUESTION: {reformulated_query}

CHUNKS:
"""
        for i, (chunk, _, _, _, _) in enumerate(top_5_chunks):
            reranking_prompt += f"\n[{i+1}] {chunk.content[:300]}...\n"
        
        reranking_prompt += """
Return the chunks in order of relevance (most relevant first) as JSON:
{
    "ranking": [3, 1, 5, 2, 4],  // indices in order of relevance
    "reasoning": "why this order"
}"""

        reranking_messages = [
            {"role": "system", "content": "You are a document relevance expert. Rerank by relevance to the question."},
            {"role": "user", "content": reranking_prompt}
        ]
        
        reranking_response = llm_router.generate(
            model=model_enum,
            messages=reranking_messages,
            temperature=0.1,
            max_tokens=300
        )
        
        reranking_text = reranking_response['message']['content']
        
        try:
            import re
            json_match = re.search(r'\{[\s\S]*\}', reranking_text)
            if json_match:
                reranking_data = json.loads(json_match.group())
                new_order = reranking_data.get('ranking', list(range(1, len(top_5_chunks) + 1)))
                # Reorder chunks
                reranked_chunks = [top_5_chunks[idx - 1] for idx in new_order if 1 <= idx <= len(top_5_chunks)]
            else:
                reranked_chunks = top_5_chunks
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"[TIER 3] Failed to parse reranking: {e}")
            reranked_chunks = top_5_chunks
        
        processing_steps[-1]["status"] = "completed"
        processing_steps[-1]["result"] = f"Reranked {len(reranked_chunks)} chunks"
        
        # Step 4: Always regenerate answer with FULL original context (not just reranked 5)
        # The reranking was just to identify most relevant chunks, but we use ALL chunks for answer
        processing_steps.append({
            "step": "tier3_regeneration",
            "status": "in_progress",
            "message": "TIER 3: Regenerating answer with full context..."
        })
        
        # Use the ORIGINAL context passed in, not just reranked chunks!
        # This ensures we don't lose important data that was in other chunks
        
        # Use ORIGINAL query_text, not reformulated - to keep answer on topic!
        regeneration_prompt = f"""Write a comprehensive answer for this ESRS disclosure requirement using the provided company documents.

DISCLOSURE REQUIREMENT: {query_text}

COMPANY DOCUMENTS:
{context}

INSTRUCTIONS:
1. Write the answer as if you are writing the actual sustainability report section
2. Include ALL relevant data, numbers, percentages, and statistics from the documents
3. Present numerical data in tables or structured format when appropriate
4. Cover all aspects of the disclosure requirement that are supported by the documents
5. If certain required information is not found in documents, clearly note what is missing
6. Be thorough and professional - this will be used in the actual report

Write a complete, well-structured answer:"""

        regeneration_messages = [
            {"role": "system", "content": "You are an expert sustainability report writer. Write comprehensive answers for ESRS disclosure requirements using the provided company documents. Include all relevant data and statistics."},
            {"role": "user", "content": regeneration_prompt}
        ]
        
        regeneration_response = llm_router.generate(
            model=model_enum,
            messages=regeneration_messages,
            temperature=0.2,
            max_tokens=2000
        )
        
        refined_answer = regeneration_response['message']['content']
        new_confidence = min(confidence + 0.15, 0.95)  # Boost confidence after TIER 3 refinement
        
        processing_steps[-1]["status"] = "completed"
        processing_steps[-1]["result"] = f"Regenerated (confidence: {new_confidence:.1%})"
        
        logger.info(f"[TIER 3] Answer regenerated - new confidence: {new_confidence:.2%}")
        logger.info(f"[TIER 3] Complete - final confidence: {new_confidence:.2%}")
        
        return refined_answer, new_confidence, processing_steps
        
    except Exception as e:
        logger.error(f"[TIER 3] Error: {e}", exc_info=True)
        processing_steps.append({
            "step": "tier3_error",
            "status": "error",
            "message": f"TIER 3 error: {str(e)}",
            "result": "Using TIER 2 answer"
        })
        return initial_answer, confidence, processing_steps
