"""
Hybrid Search Engine utilizing Reciprocal Rank Fusion (RRF).
Combines Dense Vector Cosine Similarity Search and Full-Text Keyword Search
with metadata filtering (category, date, version).
"""

import json
import numpy as np
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.config import settings
from app.db.models import Chunk, Document, DocumentVersion
from app.ingestion.embeddings import embedding_engine

class HybridSearchEngine:
    @staticmethod
    def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Compute cosine similarity between two 384d dense vectors."""
        a = np.array(vec_a, dtype=np.float32)
        b = np.array(vec_b, dtype=np.float32)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    @staticmethod
    def keyword_score(query: str, text_content: str, section_title: Optional[str] = None) -> float:
        """Calculate BM25-style keyword relevance score."""
        q_tokens = set(query.lower().split())
        if not q_tokens:
            return 0.0
            
        content_lower = text_content.lower()
        title_lower = (section_title or "").lower()
        
        score = 0.0
        for token in q_tokens:
            count = content_lower.count(token)
            if count > 0:
                score += 1.0 + np.log(count)
            if token in title_lower:
                score += 2.5 # Title weight boost
                
        return score

    @classmethod
    def execute_search(
        cls,
        db: Session,
        query: str,
        category_filter: Optional[str] = None,
        top_k: int = 5,
        search_mode: str = "hybrid", # 'hybrid', 'semantic', 'keyword'
        semantic_weight: float = settings.DEFAULT_SEMANTIC_WEIGHT,
        keyword_weight: float = settings.DEFAULT_KEYWORD_WEIGHT,
        rrf_k: int = settings.RRF_K_CONSTANT
    ) -> List[Dict[str, Any]]:
        """Execute hybrid RRF search across document chunks."""
        # Query embedding
        query_vec = embedding_engine.embed_text(query)
        
        # Fetch chunk candidates with joined document metadata
        query_builder = db.query(Chunk, Document, DocumentVersion).join(
            Document, Chunk.document_id == Document.document_id
        ).join(
            DocumentVersion, Chunk.version_id == DocumentVersion.version_id
        )

        if category_filter and category_filter.upper() != "ALL":
            query_builder = query_builder.filter(Document.category == category_filter)

        candidates = query_builder.all()
        if not candidates:
            return []

        # 1. Compute Semantic Scores & Rank
        semantic_scored = []
        for chunk, doc, version in candidates:
            chunk_vec = json.loads(chunk.embedding_json) if chunk.embedding_json else []
            sim = cls.cosine_similarity(query_vec, chunk_vec) if chunk_vec else 0.0
            semantic_scored.append((chunk, doc, version, sim))

        semantic_ranked = sorted(semantic_scored, key=lambda x: x[3], reverse=True)
        semantic_rank_map = {item[0].chunk_id: rank + 1 for rank, item in enumerate(semantic_ranked)}

        # 2. Compute Keyword Scores & Rank
        keyword_scored = []
        for chunk, doc, version in candidates:
            kw_score = cls.keyword_score(query, chunk.content, chunk.section_title)
            keyword_scored.append((chunk, doc, version, kw_score))

        keyword_ranked = sorted(keyword_scored, key=lambda x: x[3], reverse=True)
        keyword_rank_map = {item[0].chunk_id: rank + 1 for rank, item in enumerate(keyword_ranked)}

        # 3. Compute Reciprocal Rank Fusion (RRF) Score
        results = []
        for chunk, doc, version, sim_score in semantic_ranked:
            c_id = chunk.chunk_id
            r_sem = semantic_rank_map[c_id]
            r_kw = keyword_rank_map[c_id]
            kw_score = next(item[3] for item in keyword_scored if item[0].chunk_id == c_id)

            if search_mode == "semantic":
                final_score = sim_score
            elif search_mode == "keyword":
                final_score = kw_score
            else:
                # Hybrid RRF Formula
                rrf_sem = 1.0 / (rrf_k + r_sem)
                rrf_kw = 1.0 / (rrf_k + r_kw)
                final_score = (semantic_weight * rrf_sem) + (keyword_weight * rrf_kw)

            results.append({
                "chunk_id": chunk.chunk_id,
                "document_id": doc.document_id,
                "doc_identifier": doc.doc_identifier,
                "document_title": doc.title,
                "category": doc.category,
                "version_number": version.version_number,
                "section_title": chunk.section_title,
                "content": chunk.content,
                "start_char": chunk.start_char,
                "end_char": chunk.end_char,
                "semantic_score": round(sim_score, 4),
                "keyword_score": round(kw_score, 4),
                "rrf_score": round(final_score, 6),
                "semantic_rank": r_sem,
                "keyword_rank": r_kw
            })

        # Sort by final search score
        sorted_results = sorted(results, key=lambda x: x["rrf_score"], reverse=True)
        return sorted_results[:top_k]
