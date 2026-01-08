"""
Shared embedding model configurations.

Used by both:
- scripts/embed_catalogue.py (offline pre-computation)
- backend/app/ (inference-time embedding)
"""

EMBEDDING_MODELS = {
    "gist": {
        "name": "avsolatorio/GIST-all-MiniLM-L6-v2",
        "type": "sentence_transformer",  # Local SentenceTransformer model
        "dimensions": 384,
        "display_name": "GIST-MiniLM-L6 (local)",
    },
}
