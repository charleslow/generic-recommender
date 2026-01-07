"""Recommendation API router."""
import time

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models import (
    DebugInfo,
    LatencyBreakdown,
    ModelsResponse,
    Recommendation,
    RecommendRequest,
    RecommendResponse,
)
from app.services import embed_texts, generate_synthetic_candidates, rerank_items
from app.services.vector_search import vector_service

router = APIRouter()


@router.post("/recommend", response_model=RecommendResponse)
async def get_recommendations(request: RecommendRequest):
    """
    Get recommendations for a user context.
    
    1. Generate synthetic candidates using LLM
    2. Embed candidates
    3. Search vector DB for similar items
    4. Rerank results
    5. Return top recommendations with latency breakdown
    """
    total_start = time.perf_counter()
    
    # Validate inputs
    if request.llm_model not in settings.available_models:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model. Available: {settings.available_models}"
        )
    if request.rerank_model not in settings.rerank_models:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid rerank model. Available: {settings.rerank_models}"
        )
    
    # 1. Generate synthetic candidates
    t0 = time.perf_counter()
    try:
        synthetic_candidates = await generate_synthetic_candidates(
            user_context=request.user_context,
            model=request.llm_model,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Candidate generation failed: {str(e)}")
    candidate_gen_ms = (time.perf_counter() - t0) * 1000
    
    # 2. Embed synthetic candidates
    t0 = time.perf_counter()
    try:
        candidate_embeddings = await embed_texts(synthetic_candidates)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding failed: {str(e)}")
    embedding_ms = (time.perf_counter() - t0) * 1000
    
    # 3. Vector search
    t0 = time.perf_counter()
    try:
        retrieved_items = vector_service.search(
            query_embeddings=candidate_embeddings,
            k=10,  # k per query, will aggregate
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vector search failed: {str(e)}")
    vector_search_ms = (time.perf_counter() - t0) * 1000
    
    # 4. Rerank
    t0 = time.perf_counter()
    try:
        ranked_items = await rerank_items(
            user_context=request.user_context,
            items=retrieved_items,
            rerank_model=request.rerank_model,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reranking failed: {str(e)}")
    reranking_ms = (time.perf_counter() - t0) * 1000
    
    total_ms = (time.perf_counter() - total_start) * 1000
    
    # Build response (limit to configured num_results)
    recommendations = [
        Recommendation(
            item_id=item["item_id"],
            title=item["title"],
            score=item["score"],
        )
        for item in ranked_items[:settings.num_results]
    ]
    
    latency = LatencyBreakdown(
        candidate_generation_ms=round(candidate_gen_ms, 2),
        embedding_ms=round(embedding_ms, 2),
        vector_search_ms=round(vector_search_ms, 2),
        reranking_ms=round(reranking_ms, 2),
        total_ms=round(total_ms, 2),
    )
    
    debug = DebugInfo(
        synthetic_candidates=synthetic_candidates,
        num_retrieved=len(retrieved_items),
        rerank_model_used=request.rerank_model,
        llm_model_used=request.llm_model,
    )
    
    return RecommendResponse(
        recommendations=recommendations,
        latency=latency,
        debug=debug,
    )


@router.get("/models", response_model=ModelsResponse)
async def get_available_models():
    """Get available LLM models and reranking models."""
    return ModelsResponse(
        llm_models=settings.available_models,
        rerank_models=settings.rerank_models,
    )


@router.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run."""
    return {"status": "healthy", "index_loaded": vector_service._initialized}
