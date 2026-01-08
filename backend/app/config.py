"""Configuration for the recommender system."""
from pydantic_settings import BaseSettings

# Embedding model configurations
EMBEDDING_MODELS = {
    "gist": {
        "name": "avsolatorio/GIST-all-MiniLM-L6-v2",
        "type": "sentence_transformer",  # Local SentenceTransformer model
        "dimensions": 384,
        "display_name": "GIST-MiniLM-L6 (local)",
    },
}

# OpenRouter models (prefixed with "openrouter/")
OPENROUTER_MODELS = [
    "openrouter/openai/gpt-4o-mini",
    "openrouter/bytedance-seed/seed-1.6-flash",
    "openrouter/deepseek/deepseek-chat",
    "openrouter/deepseek/deepseek-r1-0528-qwen3-8b",
    "openrouter/google/gemini-2.5-flash-lite",
    "openrouter/qwen/qwen3-coder-flash",
    "openrouter/qwen/qwen3-next-80b-a3b-instruct",
]

# Groq models (prefixed with "groq/")
GROQ_MODELS = [
    "groq/llama-3.3-70b-versatile",
    "groq/llama-3.1-8b-instant",
    "groq/openai/gpt-oss-120b",
    "groq/openai/gpt-oss-20b",
]

# Combined list of all models
MODELS = OPENROUTER_MODELS + GROQ_MODELS

class Settings(BaseSettings):
    # API Keys
    openrouter_api_key: str = ""
    groq_api_key: str = ""
    zeroentropy_api_key: str = ""
    
    # Data directory (contains embeddings_*.npy and catalogue.json)
    data_dir: str = "/app/data"
    
    # Default embedding model (must be a key in EMBEDDING_MODELS)
    default_embedding_model: str = "openai"
    
    # Available embedding models (keys from EMBEDDING_MODELS)
    available_embedding_models: list[str] = list(EMBEDDING_MODELS.keys())
    
    # Recommender config
    system_prompt: str = "You are a career coach. You recommend articles that best suit the career seeker."
    num_synthetic: int = 3       # Number of synthetic candidates to generate
    k_per_query: int = 10        # Number of items to retrieve per query embedding
    num_candidates: int = 20     # Number of items to retrieve for reranking
    num_results: int = 5         # Final recommendations to return
    
    # Available LLM models for frontend dropdown
    available_models: list[str] = MODELS
    
    # Reranking options (zerank-* uses ZeroEntropy, others are LLM model names)
    rerank_models: list[str] = [
        "zerank-2", *MODELS
    ]
    
    class Config:
        env_file = ".env"


settings = Settings()
