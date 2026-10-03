"""
Unit tests for semantic chunker and document parser.
"""

import pytest
from app.ingestion.parser import DocumentParser
from app.ingestion.chunker import SemanticChunker

def test_document_parser():
    raw = "# Policy Guide\nCategory: Compliance\n\n## Section A\nThis is test paragraph content for compliance."
    parsed = DocumentParser.parse_markdown_or_text(raw, "policy.md")
    assert parsed["title"] == "Policy Guide"
    assert parsed["category"] == "Compliance"
    assert len(parsed["sections"]) > 0

def test_semantic_chunker():
    raw = "Section Title\n" + "Word " * 200
    parsed = DocumentParser.parse_markdown_or_text(raw, "test.md")
    chunker = SemanticChunker(chunk_size=100, overlap=20)
    chunks = chunker.chunk_document(parsed)
    assert len(chunks) > 1
    for c in chunks:
        assert "chunk_hash" in c
        assert "start_char" in c
        assert "end_char" in c
