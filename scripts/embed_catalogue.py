"""
Embed items from a catalogue JSONL file using multiple embedding models.

Usage:
    python scripts/embed_catalogue.py [--model MODEL_KEY]

    MODEL_KEY options:
        - openai (default): openai/text-embedding-3-small via OpenRouter
        - qwen: qwen/qwen3-embedding-8b via OpenRouter
        - gist: SentenceTransformer avsolatorio/GIST-all-MiniLM-L6-v2 (local)
        - all: Generate embeddings for all models

Requires:
    - OPENROUTER_API_KEY environment variable (for openai and qwen models)
    - user_inputs/catalogue.jsonl file

Outputs:
    - user_inputs/embeddings_<model>.npy (numpy array of embeddings)
    - user_inputs/catalogue.json (catalogue with metadata)
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
from openai import OpenAI

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
from app.config import EMBEDDING_MODELS

# Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BATCH_SIZE = 100  # OpenRouter batch limit
INPUT_FILE = Path("user_inputs/catalogue.jsonl")
OUTPUT_CATALOGUE = Path("user_inputs/catalogue.json")

# OpenRouter client (OpenAI-compatible)
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)


def load_catalogue(filepath: Path) -> list[dict]:
    """Load catalogue from JSONL file."""
    items = []
    with open(filepath, "r") as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line))
    
    # Validate required fields
    for item in items:
        if "item_id" not in item:
            raise ValueError(f"Missing 'item_id' in item: {item}")
        if "title" not in item:
            raise ValueError(f"Missing 'title' in item: {item}")
        if "text" not in item:
            raise ValueError(f"Missing 'text' in item: {item}")
        # Ensure item_id is always a string
        item["item_id"] = str(item["item_id"])
    
    return items


def embed_batch_openrouter(texts: list[str], model: str) -> list[list[float]]:
    """Embed a batch of texts using OpenRouter."""
    response = client.embeddings.create(
        model=model,
        input=texts,
    )
    
    embeddings_data = sorted(response.data, key=lambda x: x.index)
    return [item.embedding for item in embeddings_data]


def embed_with_sentence_transformer(texts: list[str], model_name: str) -> np.ndarray:
    """Embed texts using SentenceTransformer (local model)."""
    from sentence_transformers import SentenceTransformer
    
    print(f"Loading SentenceTransformer model: {model_name}")
    model = SentenceTransformer(model_name)
    
    print(f"Encoding {len(texts)} texts...")
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    return embeddings


def embed_catalogue(texts: list[str], model_key: str) -> np.ndarray:
    """Embed all texts using the specified model."""
    model_config = EMBEDDING_MODELS[model_key]
    model_name = model_config["name"]
    model_type = model_config["type"]
    
    if model_type == "sentence_transformer":
        # Use local SentenceTransformer
        embeddings = embed_with_sentence_transformer(texts, model_name)
        return embeddings.astype(np.float32)
    
    elif model_type == "openrouter":
        # Use OpenRouter API
        if not OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")
        
        all_embeddings = []
        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i:i + BATCH_SIZE]
            print(f"Embedding batch {i // BATCH_SIZE + 1}/{(len(texts) - 1) // BATCH_SIZE + 1} ({len(batch)} items)...")
            
            embeddings = embed_batch_openrouter(batch, model_name)
            all_embeddings.extend(embeddings)
            
            # Rate limiting
            if i + BATCH_SIZE < len(texts):
                time.sleep(0.5)
        
        return np.array(all_embeddings, dtype=np.float32)
    
    else:
        raise ValueError(f"Unknown model type: {model_type}")


def process_model(catalogue: list[dict], model_key: str):
    """Process embeddings for a single model."""
    model_config = EMBEDDING_MODELS[model_key]
    output_file = Path(f"user_inputs/embeddings_{model_key}.npy")
    
    print(f"\n{'='*60}")
    print(f"Processing model: {model_key} ({model_config['name']})")
    print(f"Expected dimensions: {model_config['dimensions']}")
    print(f"{'='*60}")
    
    texts = [item["text"] for item in catalogue]
    
    embeddings_array = embed_catalogue(texts, model_key)
    print(f"Embeddings shape: {embeddings_array.shape}")
    
    # Verify dimensions
    if embeddings_array.shape[1] != model_config["dimensions"]:
        print(f"WARNING: Expected {model_config['dimensions']} dimensions, got {embeddings_array.shape[1]}")
    
    # Save embeddings
    np.save(output_file, embeddings_array)
    print(f"Saved embeddings to {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Embed catalogue items using various embedding models")
    parser.add_argument(
        "--model",
        choices=list(EMBEDDING_MODELS.keys()) + ["all"],
        default="all",
        help="Which embedding model to use (default: all)"
    )
    args = parser.parse_args()
    
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Catalogue file not found: {INPUT_FILE}")
    
    print(f"Loading catalogue from {INPUT_FILE}...")
    catalogue = load_catalogue(INPUT_FILE)
    print(f"Loaded {len(catalogue)} items")
    
    # Determine which models to process
    if args.model == "all":
        models_to_process = list(EMBEDDING_MODELS.keys())
    else:
        models_to_process = [args.model]
    
    # Process each model
    for model_key in models_to_process:
        try:
            process_model(catalogue, model_key)
        except Exception as e:
            print(f"ERROR processing {model_key}: {e}")
            if args.model != "all":
                raise
    
    # Save catalogue (without embeddings, just metadata)
    with open(OUTPUT_CATALOGUE, "w") as f:
        json.dump(catalogue, f, indent=2)
    print(f"\nSaved catalogue metadata to {OUTPUT_CATALOGUE}")
    
    print("\n" + "="*60)
    print("Done! Now copy files to backend/data/ before deploying:")
    print("  cp user_inputs/embeddings_*.npy backend/data/")
    print("  cp user_inputs/catalogue.json backend/data/")
    print("="*60)


if __name__ == "__main__":
    main()
