"""Vector search service using FAISS."""
import json
from pathlib import Path

import faiss
import numpy as np

from app.config import settings


class VectorSearchService:
    """Service for vector similarity search using FAISS."""
    
    def __init__(self):
        self.index: faiss.IndexFlatIP | None = None
        self.catalogue: list[dict] = []
        self.id_to_idx: dict[str, int] = {}
        self._initialized = False
    
    async def initialize(self):
        """Load embeddings from local data files and build FAISS index."""
        if self._initialized:
            return
        
        # Load from local data directory (bundled with container)
        data_dir = Path(settings.data_dir)
        
        # Load embeddings
        embeddings_path = data_dir / "embeddings.npy"
        embeddings = np.load(embeddings_path).astype(np.float32)
        
        # Load catalogue metadata
        catalogue_path = data_dir / "catalogue.json"
        with open(catalogue_path, "r") as f:
            self.catalogue = json.load(f)
        
        # Build index mapping
        self.id_to_idx = {item["item_id"]: i for i, item in enumerate(self.catalogue)}
        
        # Build FAISS index (Inner Product for cosine similarity with normalized vectors)
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        
        self.index = faiss.IndexFlatIP(settings.embedding_dimensions)
        self.index.add(embeddings)
        
        self._initialized = True
        print(f"Loaded {len(self.catalogue)} items into FAISS index")
    
    def search(
        self,
        query_embeddings: list[list[float]],
        k: int = 10,
    ) -> list[dict]:
        """
        Search for nearest neighbors for multiple query embeddings.
        Merges results by summing scores.
        
        Args:
            query_embeddings: List of embedding vectors
            k: Number of neighbors per query
        
        Returns:
            List of items sorted by aggregated score
        """
        if not self._initialized:
            raise RuntimeError("VectorSearchService not initialized. Call initialize() first.")
        
        # Convert to numpy and normalize
        queries = np.array(query_embeddings, dtype=np.float32)
        faiss.normalize_L2(queries)
        
        # Search for each query
        scores, indices = self.index.search(queries, k)
        
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
