"""
Configuration for the recommender system.
Values are hardcoded here but can be loaded from a YAML file.
"""
from pydantic_settings import BaseSettings

MODELS = [
        # openai
        "openai/gpt-4o-mini",
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "openai/gpt-5-nano",
        # deepseek
        "deepseek/deepseek-chat",
        "deepseek/deepseek-r1-0528-qwen3-8b",
        "deepseek/deepseek-r1-distill-qwen-32b",
        # gemini
        "google/gemini-2.5-flash-lite",
        # qwen
        "qwen/qwen3-next-80b-a3b-instruct",
        "qwen/qwen3-coder:free",
    ]

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
    available_models: list[str] = MODELS
    
    # Reranking options (zerank-* uses ZeroEntropy, others are LLM model names)
    rerank_models: list[str] = [
        "zerank-2", *MODELS
    ]
    
    class Config:
        env_file = ".env"


settings = Settings()
