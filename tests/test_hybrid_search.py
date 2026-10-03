"""
Unit tests for hybrid search engine and RRF scoring logic.
"""

import pytest
from app.search.hybrid_search import HybridSearchEngine

def test_cosine_similarity():
    vec_a = [1.0, 0.0, 0.5]
    vec_b = [1.0, 0.0, 0.5]
    sim = HybridSearchEngine.cosine_similarity(vec_a, vec_b)
    assert abs(sim - 1.0) < 1e-4

def test_keyword_score():
    score = HybridSearchEngine.keyword_score("travel meals policy", "The travel meals policy permits up to $75 per day", "Expense Policy")
    assert score > 0.0
