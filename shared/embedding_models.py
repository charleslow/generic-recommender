"""
Shared embedding model configurations.

Used by both:
- scripts/embed_catalogue.py (offline pre-computation)
- backend/app/ (inference-time embedding)
"""

EMBEDDING_MODELS = {
    "openai": {
        "name": "openai/text-embedding-3-small",
        "type": "openrouter",  # Uses OpenRouter API
        "dimensions": 1536,
        "display_name": "OpenAI text-embedding-3-small",
    },
    "qwen": {
        "name": "qwen/qwen3-embedding-8b",
        "type": "openrouter",  # Uses OpenRouter API
        "dimensions": 4096,  # Qwen3-embedding-8b outputs 4096 dimensions
        "display_name": "Qwen3 Embedding 8B",
    },
    "gist": {
        "name": "avsolatorio/GIST-all-MiniLM-L6-v2",
        "type": "sentence_transformer",  # Local SentenceTransformer model
        "dimensions": 384,
        "display_name": "GIST-MiniLM-L6 (local)",
    },
}
