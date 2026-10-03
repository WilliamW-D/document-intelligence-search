"""
Citation Extraction & Attribution Engine.
Formats retrieved search results into structured citations with exact source context,
document identifiers, section locations, and confidence scores.
"""

from typing import List, Dict, Any

class CitationEngine:
    @staticmethod
    def generate_citations(search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract structured citations from ranked search results."""
        citations = []
        for i, res in enumerate(search_results, start=1):
            snippet = res["content"]
            if len(snippet) > 280:
                snippet = snippet[:277] + "..."

            citation_key = f"[{i}]"
            citations.append({
                "citation_key": citation_key,
                "rank": i,
                "doc_identifier": res["doc_identifier"],
                "document_title": res["document_title"],
                "category": res["category"],
                "version_number": res["version_number"],
                "section_title": res["section_title"],
                "char_offset": f"Chars {res['start_char']}-{res['end_char']}",
                "snippet": snippet,
                "relevance_score": res["rrf_score"],
                "semantic_rank": res["semantic_rank"],
                "keyword_rank": res["keyword_rank"]
            })
        return citations
