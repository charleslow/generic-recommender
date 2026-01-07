"""Pydantic models for API request/response schemas."""
from pydantic import BaseModel, Field


class RecommendRequest(BaseModel):
    """Request body for /recommend endpoint."""
    user_context: str = Field(..., description="User context for generating recommendations")
    llm_model: str = Field(default="openai/gpt-4o-mini", description="LLM model for candidate generation")
    rerank_model: str = Field(default="zerank-2", description="Reranking model: 'zerank-2' or an LLM model name")


class Recommendation(BaseModel):
    """A single recommendation item."""
    item_id: str
    title: str
    score: float


class LatencyBreakdown(BaseModel):
    """Latency breakdown for each component in milliseconds."""
    candidate_generation_ms: float = Field(..., description="Time for LLM to generate synthetic candidates")
    embedding_ms: float = Field(..., description="Time to embed synthetic candidates")
    vector_search_ms: float = Field(..., description="Time for kNN search in FAISS")
    reranking_ms: float = Field(..., description="Time for reranking (ZeroEntropy or LLM)")
    total_ms: float = Field(..., description="Total end-to-end latency")


class DebugInfo(BaseModel):
    """Debug information for transparency."""
    synthetic_candidates: list[str] = Field(..., description="Generated synthetic candidates")
    num_retrieved: int = Field(..., description="Number of items retrieved from vector search")
    rerank_model_used: str = Field(..., description="Reranking model that was used")
    llm_model_used: str = Field(..., description="LLM model that was used")


class RecommendResponse(BaseModel):
    """Response body for /recommend endpoint."""
    recommendations: list[Recommendation]
    latency: LatencyBreakdown
    debug: DebugInfo


class ModelsResponse(BaseModel):
    """Response for /models endpoint."""
    llm_models: list[str]
    rerank_models: list[str]
