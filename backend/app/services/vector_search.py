"""Vector search service using FAISS with multiple embedding model support."""
import json
from pathlib import Path

import faiss
import numpy as np
from app.config import EMBEDDING_MODELS, settings


class VectorSearchService:
    """Service for vector similarity search using FAISS with multiple embedding indexes."""
    
    def __init__(self):
        # One index per embedding model
        self.indexes: dict[str, faiss.IndexFlatIP] = {}
        self.catalogue: list[dict] = []
        self.id_to_idx: dict[str, int] = {}
        self._initialized = False
    
    async def initialize(self):
        """Load embeddings from local data files and build FAISS indexes for all models."""
        if self._initialized:
            return
        
        # Load from local data directory (bundled with container)
        data_dir = Path(settings.data_dir)
        
        # Load catalogue metadata (shared across all models)
        catalogue_path = data_dir / "catalogue.json"
        with open(catalogue_path, "r") as f:
            self.catalogue = json.load(f)
        
        # Ensure item_id is always a string
        for item in self.catalogue:
            item["item_id"] = str(item["item_id"])
        
        # Build index mapping
        self.id_to_idx = {item["item_id"]: i for i, item in enumerate(self.catalogue)}
        
        # Load embeddings and build FAISS index for each available model
        for model_key in settings.available_embedding_models:
            embeddings_path = data_dir / f"embeddings_{model_key}.npy"
            
            if not embeddings_path.exists():
                print(f"Warning: Embeddings file not found for model '{model_key}': {embeddings_path}")
                continue
            
            embeddings = np.load(embeddings_path).astype(np.float32)
            
            # Normalize embeddings for cosine similarity (Inner Product)
            faiss.normalize_L2(embeddings)
            
            # Get embedding dimensions from config
            dimensions = EMBEDDING_MODELS[model_key]["dimensions"]
            
            # Build FAISS index
            index = faiss.IndexFlatIP(dimensions)
            index.add(embeddings)
            self.indexes[model_key] = index
            
            print(f"Loaded {len(self.catalogue)} items into FAISS index for model '{model_key}' (dim={dimensions})")
        
        if not self.indexes:
            raise RuntimeError("No embedding indexes could be loaded. Check that embeddings_*.npy files exist.")
        
        self._initialized = True
        print(f"VectorSearchService initialized with {len(self.indexes)} embedding model(s): {list(self.indexes.keys())}")
    
    def search(
        self,
        query_embeddings: list[list[float]],
        embedding_model: str,
        k: int = 10,
    ) -> list[dict]:
        """
        Search for nearest neighbors for multiple query embeddings using the specified embedding model's index.
        Merges results by summing scores.
        
        Args:
            query_embeddings: List of embedding vectors
            embedding_model: Key of the embedding model to use (e.g., 'openai', 'qwen', 'gist')
            k: Number of neighbors per query
        
        Returns:
            List of items sorted by aggregated score
        """
        if not self._initialized:
            raise RuntimeError("VectorSearchService not initialized. Call initialize() first.")
        
        if embedding_model not in self.indexes:
            available = list(self.indexes.keys())
            raise ValueError(f"Embedding model '{embedding_model}' not available. Available: {available}")
        
        index = self.indexes[embedding_model]
        
        # Convert to numpy and normalize
        queries = np.array(query_embeddings, dtype=np.float32)
        faiss.normalize_L2(queries)
        
        # Search for each query
        scores, indices = index.search(queries, k)
        
        # Aggregate scores across all queries
        score_map: dict[int, float] = {}
        for query_scores, query_indices in zip(scores, indices):
            for score, idx in zip(query_scores, query_indices):
                if idx >= 0:  # FAISS returns -1 for missing results
                    score_map[idx] = score_map.get(idx, 0.0) + float(score)
        
        # Sort by aggregated score
        sorted_items = sorted(score_map.items(), key=lambda x: x[1], reverse=True)
        
        # Build result list
        results = []
        for idx, score in sorted_items[:settings.num_candidates]:
            item = self.catalogue[idx].copy()
            item["score"] = score
            results.append(item)
        
        return results
    
    def get_item(self, item_id: str) -> dict | None:
        """Get a single item by ID."""
        if item_id in self.id_to_idx:
            return self.catalogue[self.id_to_idx[item_id]]
        return None


# Global singleton
vector_service = VectorSearchService()
