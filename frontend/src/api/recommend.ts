// API types and functions

export interface Recommendation {
  item_id: string;
  title: string;
  text: string;
  score: number;
}

export interface LatencyBreakdown {
  candidate_generation_ms: number;
  embedding_ms: number;
  vector_search_ms: number;
  reranking_ms: number;
  total_ms: number;
}

export interface DebugInfo {
  synthetic_candidates: string[];
  num_retrieved: number;
  rerank_model_used: string;
  llm_model_used: string;
}

export interface RecommendResponse {
  recommendations: Recommendation[];
  latency: LatencyBreakdown;
  debug: DebugInfo;
}

export interface ModelsResponse {
  llm_models: string[];
  rerank_models: string[];
}

// Configure this to your Cloud Run URL
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';

export async function getModels(): Promise<ModelsResponse> {
  const response = await fetch(`${API_BASE_URL}/models`);
  if (!response.ok) {
    throw new Error(`Failed to fetch models: ${response.statusText}`);
  }
  return response.json();
}

export async function getRecommendations(
  userContext: string,
  llmModel: string,
  rerankModel: string
): Promise<RecommendResponse> {
  const response = await fetch(`${API_BASE_URL}/recommend`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      user_context: userContext,
      llm_model: llmModel,
      rerank_model: rerankModel,
    }),
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || 'Failed to get recommendations');
  }
  
  return response.json();
}
