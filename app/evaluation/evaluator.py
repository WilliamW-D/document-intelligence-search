"""
Retrieval Evaluation Suite.
Measures search retrieval quality metrics (Hit@1, Hit@3, Hit@5, Mean Reciprocal Rank MRR)
across Hybrid, Pure Semantic, and Pure Keyword retrieval modes against a ground-truth dataset.
"""

import json
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.search.hybrid_search import HybridSearchEngine
from app.db.models import RetrievalEvaluation

# Ground-Truth Benchmark Evaluation Questions & Target Expected Documents
EVALUATION_BENCHMARKS = [
    {
        "query": "What are the data retention and archival guidelines?",
        "expected_doc_identifier": "DOC-POL-001",
        "description": "Data retention policy lookup"
    },
    {
        "query": "How are security vulnerabilities handled in software releases?",
        "expected_doc_identifier": "DOC-SEC-002",
        "description": "Security incident response lookup"
    },
    {
        "query": "What is the maximum allowed business expense for travel meals?",
        "expected_doc_identifier": "DOC-FIN-003",
        "description": "Financial travel expense policy lookup"
    },
    {
        "query": "SLA incident response timeline and resolution thresholds",
        "expected_doc_identifier": "DOC-OPS-004",
        "description": "SLA operational procedure lookup"
    },
    {
        "query": "Remote work cybersecurity requirements and VPN usage",
        "expected_doc_identifier": "DOC-SEC-002",
        "description": "Cybersecurity VPN policy lookup"
    }
]

class RetrievalEvaluator:
    @classmethod
    def evaluate_benchmark(cls, db: Session, search_mode: str = "hybrid") -> Dict[str, Any]:
        """Run evaluation benchmark for a given search mode and compute metrics."""
        eval_results = []
        reciprocal_ranks = []
        hits_at_1 = 0
        hits_at_3 = 0
        hits_at_5 = 0

        for bench in EVALUATION_BENCHMARKS:
            query = bench["query"]
            expected_id = bench["expected_doc_identifier"]

            search_results = HybridSearchEngine.execute_search(
                db=db,
                query=query,
                top_k=5,
                search_mode=search_mode
            )

            retrieved_doc_ids = [r["doc_identifier"] for r in search_results]

            rank = None
            if expected_id in retrieved_doc_ids:
                rank = retrieved_doc_ids.index(expected_id) + 1

            hit_1 = rank == 1
            hit_3 = rank is not None and rank <= 3
            hit_5 = rank is not None and rank <= 5
            rr = (1.0 / rank) if rank else 0.0

            if hit_1: hits_at_1 += 1
            if hit_3: hits_at_3 += 1
            if hit_5: hits_at_5 += 1
            reciprocal_ranks.append(rr)

            eval_entry = {
                "query": query,
                "expected_doc_identifier": expected_id,
                "search_mode": search_mode,
                "retrieved_doc_identifiers": retrieved_doc_ids,
                "rank": rank,
                "hit_at_1": hit_1,
                "hit_at_3": hit_3,
                "hit_at_5": hit_5,
                "reciprocal_rank": round(rr, 4)
            }
            eval_results.append(eval_entry)

            # Record in DB
            db_record = RetrievalEvaluation(
                query=query,
                expected_doc_identifier=expected_id,
                search_mode=search_mode,
                top_retrieved_docs=json.dumps(retrieved_doc_ids),
                rank_of_expected=rank,
                hit_at_1=hit_1,
                hit_at_3=hit_3,
                hit_at_5=hit_5,
                reciprocal_rank=rr
            )
            db.add(db_record)

        db.commit()

        total_q = len(EVALUATION_BENCHMARKS)
        mrr = round(sum(reciprocal_ranks) / max(total_q, 1), 4)

        summary = {
            "search_mode": search_mode,
            "total_queries_evaluated": total_q,
            "mrr": mrr,
            "hit_at_1_rate": round(100.0 * hits_at_1 / total_q, 2),
            "hit_at_3_rate": round(100.0 * hits_at_3 / total_q, 2),
            "hit_at_5_rate": round(100.0 * hits_at_5 / total_q, 2),
            "query_evaluations": eval_results
        }

        return summary

    @classmethod
    def compare_all_modes(cls, db: Session) -> Dict[str, Any]:
        """Run side-by-side evaluation comparison across Hybrid, Semantic, and Keyword search."""
        hybrid_res = cls.evaluate_benchmark(db, "hybrid")
        semantic_res = cls.evaluate_benchmark(db, "semantic")
        keyword_res = cls.evaluate_benchmark(db, "keyword")

        return {
            "hybrid": hybrid_res,
            "semantic": semantic_res,
            "keyword": keyword_res,
            "comparison_summary": [
                {
                    "mode": "Hybrid (RRF)",
                    "mrr": hybrid_res["mrr"],
                    "hit_at_1": f"{hybrid_res['hit_at_1_rate']}%",
                    "hit_at_3": f"{hybrid_res['hit_at_3_rate']}%",
                    "hit_at_5": f"{hybrid_res['hit_at_5_rate']}%"
                },
                {
                    "mode": "Pure Semantic",
                    "mrr": semantic_res["mrr"],
                    "hit_at_1": f"{semantic_res['hit_at_1_rate']}%",
                    "hit_at_3": f"{semantic_res['hit_at_3_rate']}%",
                    "hit_at_5": f"{semantic_res['hit_at_5_rate']}%"
                },
                {
                    "mode": "Pure Keyword",
                    "mrr": keyword_res["mrr"],
                    "hit_at_1": f"{keyword_res['hit_at_1_rate']}%",
                    "hit_at_3": f"{keyword_res['hit_at_3_rate']}%",
                    "hit_at_5": f"{keyword_res['hit_at_5_rate']}%"
                }
            ]
        }
