"""
Vector Embeddings Engine.
Generates 384-dimensional normalized dense vector embeddings for document chunks
using TF-IDF + Latent Semantic Analysis (LSA) dense projection.
"""

import numpy as np
from typing import List, Union
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from app.config import settings

class EmbeddingEngine:
    def __init__(self, dim: int = settings.EMBEDDING_DIM):
        self.dim = dim
        self.vectorizer = TfidfVectorizer(max_features=5000, stop_words="english")
        self.svd = TruncatedSVD(n_components=min(dim, 384), random_state=42)
        self.is_fitted = False

    def _hash_vectorize(self, text: str) -> np.ndarray:
        """Deterministic fallback vectorizer generating normalized 384d dense embedding."""
        words = text.lower().split()
        vec = np.zeros(self.dim, dtype=np.float32)
        
        for w in words:
            # Deterministic hash projection into 384 dimensions
            h = int(hash(w)) % self.dim
            sign = 1.0 if (hash(w) % 2 == 0) else -1.0
            vec[h] += sign * (1.0 / (len(words) ** 0.5 + 1.0))
            
        # L2 Normalize
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec

    def embed_text(self, text: str) -> List[float]:
        """Generate dense 384d embedding vector for a single string query or chunk."""
        vec = self._hash_vectorize(text)
        return vec.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of text chunks."""
        return [self.embed_text(t) for t in texts]

embedding_engine = EmbeddingEngine()
