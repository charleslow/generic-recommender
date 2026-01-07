"""
Embed items from a catalogue JSONL file using OpenRouter's embedding API.

Usage:
    python scripts/embed_catalogue.py

Requires:
    - OPENROUTER_API_KEY environment variable
    - user_inputs/catalogue.jsonl file

Outputs:
    - user_inputs/embeddings.npy (numpy array of embeddings)
    - user_inputs/catalogue.json (catalogue with metadata)
"""
import json
import os
import time
from pathlib import Path

import numpy as np
from openai import OpenAI

# Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
EMBEDDING_MODEL = "openai/text-embedding-3-small"
BATCH_SIZE = 100  # OpenRouter batch limit
INPUT_FILE = Path("user_inputs/catalogue.jsonl")
OUTPUT_EMBEDDINGS = Path("user_inputs/embeddings.npy")
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
    
    return items


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts using OpenRouter."""
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
    )
    
    embeddings_data = sorted(response.data, key=lambda x: x.index)
    return [item.embedding for item in embeddings_data]


def main():
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY environment variable not set")
    
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Catalogue file not found: {INPUT_FILE}")
    
    print(f"Loading catalogue from {INPUT_FILE}...")
    catalogue = load_catalogue(INPUT_FILE)
    print(f"Loaded {len(catalogue)} items")
    
    # Prepare texts for embedding
    texts = [item["text"] for item in catalogue]
    
    # Embed in batches
    all_embeddings = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        print(f"Embedding batch {i // BATCH_SIZE + 1}/{(len(texts) - 1) // BATCH_SIZE + 1} ({len(batch)} items)...")
        
        embeddings = embed_batch(batch)
        all_embeddings.extend(embeddings)
        
        # Rate limiting
        if i + BATCH_SIZE < len(texts):
            time.sleep(0.5)
    
    # Convert to numpy array
    embeddings_array = np.array(all_embeddings, dtype=np.float32)
    print(f"Embeddings shape: {embeddings_array.shape}")
    
    # Save embeddings
    np.save(OUTPUT_EMBEDDINGS, embeddings_array)
    print(f"Saved embeddings to {OUTPUT_EMBEDDINGS}")
    
    # Save catalogue (without embeddings, just metadata)
    with open(OUTPUT_CATALOGUE, "w") as f:
        json.dump(catalogue, f, indent=2)
    print(f"Saved catalogue metadata to {OUTPUT_CATALOGUE}")
    
    print("\nDone! Now copy files to backend/data/ before deploying.")


if __name__ == "__main__":
    main()
