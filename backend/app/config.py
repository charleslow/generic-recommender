"""
Configuration for the recommender system.
Values are hardcoded here but can be loaded from a YAML file.
"""
import sys
from pathlib import Path

from pydantic_settings import BaseSettings

# Add project root to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from shared.embedding_models import EMBEDDING_MODELS

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
    
    # Data directory (contains embeddings_*.npy and catalogue.json)
    data_dir: str = "/app/data"
    
    # Default embedding model (must be a key in EMBEDDING_MODELS)
    default_embedding_model: str = "openai"
    
    # Available embedding models (keys from EMBEDDING_MODELS)
    available_embedding_models: list[str] = list(EMBEDDING_MODELS.keys())
    
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
