"""
Configuration for the recommender system.
Values are hardcoded here but can be loaded from a YAML file.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Keys
    openrouter_api_key: str = ""
    zeroentropy_api_key: str = ""
    
    # Data directory (contains embeddings.npy and catalogue.json)
    data_dir: str = "/app/data"
    
    # Embedding model (must match what was used for catalogue)
    embedding_model: str = "openai/text-embedding-3-small"
    embedding_dimensions: int = 1536
    
    # Recommender config
    system_prompt: str = "You are a career guidance assistant to suggest future pathways for youth."
    item_type: str = "job"
    num_synthetic: int = 3       # Number of synthetic candidates to generate
    num_candidates: int = 50     # Number of items to retrieve for reranking
    num_results: int = 5         # Final recommendations to return
    
    # Available LLM models for frontend dropdown
    available_models: list[str] = [
        "openai/gpt-4o-mini",
        "anthropic/claude-3-haiku",
        "meta-llama/llama-3.1-70b-instruct"
    ]
    
    # Reranking options (zerank-* uses ZeroEntropy, others are LLM model names)
    rerank_models: list[str] = ["zerank-2", "openai/gpt-4o-mini", "anthropic/claude-3-haiku"]
    
    class Config:
        env_file = ".env"


settings = Settings()
