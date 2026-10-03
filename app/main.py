"""
FastAPI Main Application for Document Intelligence Search System.
Exposes REST endpoints for document ingestion, hybrid RRF search,
citation generation, document cataloging, and retrieval evaluation.
"""

import os
import sys
import glob
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# Force UTF-8 output encoding for Windows terminal compatibility
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from app.config import settings
from app.db.database import get_db, init_db, DB_DIALECT
from app.db.models import Document, DocumentVersion, Chunk
from app.ingestion.parser import DocumentParser
from app.ingestion.chunker import SemanticChunker
from app.ingestion.embeddings import embedding_engine
from app.search.hybrid_search import HybridSearchEngine
from app.search.citations import CitationEngine
from app.evaluation.evaluator import RetrievalEvaluator

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Engineered Document Intelligence & Hybrid Retrieval System with Citation Tracking"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Schemas
class IngestDocumentRequest(BaseModel):
    doc_identifier: str = Field(..., example="DOC-POL-001")
    title: str = Field(..., example="Enterprise Data Retention Policy")
    category: str = Field(..., example="Policy")
    content: str
    source_url: Optional[str] = None
    author: Optional[str] = "System Admin"

class SearchRequest(BaseModel):
    query: str = Field(..., example="What are the data retention guidelines?")
    category_filter: Optional[str] = "ALL"
    top_k: int = Field(5, ge=1, le=20)
    search_mode: str = Field("hybrid", example="hybrid") # 'hybrid', 'semantic', 'keyword'
    semantic_weight: float = 0.6
    keyword_weight: float = 0.4

@app.on_event("startup")
def startup_event():
    """Initialize database tables and ingest sample documents on startup."""
    init_db()
    db = next(get_db())
    try:
        sample_dir = os.path.join(os.path.dirname(__file__), "..", "data", "sample_documents")
        sample_files = glob.glob(os.path.join(sample_dir, "*.md"))
        
        for file_path in sample_files:
            filename = os.path.basename(file_path)
            doc_id_code = filename.replace(".md", "")
            
            # Check if document already exists
            existing = db.query(Document).filter(Document.doc_identifier == doc_id_code).first()
            if not existing:
                with open(file_path, "r", encoding="utf-8") as f:
                    raw_text = f.read()
                parsed = DocumentParser.parse_markdown_or_text(raw_text, filename)
                
                # Ingest document
                ingest_document_logic(
                    db=db,
                    doc_identifier=doc_id_code,
                    title=parsed["title"],
                    category=parsed["category"],
                    content=raw_text,
                    author="System"
                )
        print("✅ Sample documents parsed, chunked, embedded, and stored.")
    except Exception as e:
        print(f"⚠️ Sample ingestion info: {e}")
    finally:
        db.close()

def ingest_document_logic(db: Session, doc_identifier: str, title: str, category: str, content: str, author: str = "System", source_url: Optional[str] = None):
    """Core logic to parse, chunk, embed, version, deduplicate, and persist document."""
    parsed = DocumentParser.parse_markdown_or_text(content, f"{doc_identifier}.md")
    
    # Check or create Master Document
    doc = db.query(Document).filter(Document.doc_identifier == doc_identifier).first()
    if not doc:
        doc = Document(
            doc_identifier=doc_identifier,
            title=title or parsed["title"],
            category=category or parsed["category"],
            source_url=source_url,
            author=author
        )
        db.add(doc)
        db.flush()

    # Determine Version Number
    latest_version = db.query(DocumentVersion).filter(DocumentVersion.document_id == doc.document_id).order_by(DocumentVersion.version_number.desc()).first()
    version_num = (latest_version.version_number + 1) if latest_version else 1
    
    import hashlib
    checksum = hashlib.sha256(content.encode("utf-8")).hexdigest()
    
    doc_version = DocumentVersion(
        document_id=doc.document_id,
        version_number=version_num,
        checksum=checksum,
        raw_content=content
    )
    db.add(doc_version)
    db.flush()

    # Chunking
    chunker = SemanticChunker()
    chunks_data = chunker.chunk_document(parsed)
    
    # Embedding & Deduplication
    seen_hashes = set()
    created_chunks = 0
    
    for cdata in chunks_data:
        chash = cdata["chunk_hash"]
        if chash in seen_hashes:
            continue
        seen_hashes.add(chash)

        # Generate Embedding Vector
        vec = embedding_engine.embed_text(cdata["content"])
        import json
        
        chunk_obj = Chunk(
            version_id=doc_version.version_id,
            document_id=doc.document_id,
            chunk_index=cdata["chunk_index"],
            chunk_hash=chash,
            section_title=cdata["section_title"],
            content=cdata["content"],
            start_char=cdata["start_char"],
            end_char=cdata["end_char"],
            embedding_json=json.dumps(vec)
        )
        db.add(chunk_obj)
        created_chunks += 1

    doc_version.chunk_count = created_chunks
    db.commit()
    return doc

@app.post("/api/documents/ingest")
def ingest_document(req: IngestDocumentRequest, db: Session = Depends(get_db)):
    """Ingest a new document or new version of an existing document."""
    doc = ingest_document_logic(
        db=db,
        doc_identifier=req.doc_identifier,
        title=req.title,
        category=req.category,
        content=req.content,
        author=req.author,
        source_url=req.source_url
    )
    return {
        "status": "SUCCESS",
        "message": f"Document '{doc.doc_identifier}' ingested successfully.",
        "document_id": doc.document_id
    }

@app.post("/api/search")
def hybrid_search(req: SearchRequest, db: Session = Depends(get_db)):
    """Execute Hybrid RRF Search across document vector embeddings and keyword text index."""
    results = HybridSearchEngine.execute_search(
        db=db,
        query=req.query,
        category_filter=req.category_filter,
        top_k=req.top_k,
        search_mode=req.search_mode,
        semantic_weight=req.semantic_weight,
        keyword_weight=req.keyword_weight
    )
    citations = CitationEngine.generate_citations(results)
    
    return {
        "query": req.query,
        "search_mode": req.search_mode,
        "total_results": len(results),
        "results": results,
        "citations": citations
    }

@app.get("/api/documents")
def list_documents(db: Session = Depends(get_db)):
    """Fetch catalog of all ingested documents, versions, and chunk metrics."""
    docs = db.query(Document).all()
    out = []
    for d in docs:
        versions = db.query(DocumentVersion).filter(DocumentVersion.document_id == d.document_id).all()
        total_chunks = db.query(Chunk).filter(Chunk.document_id == d.document_id).count()
        out.append({
            "document_id": d.document_id,
            "doc_identifier": d.doc_identifier,
            "title": d.title,
            "category": d.category,
            "author": d.author,
            "version_count": len(versions),
            "total_chunks": total_chunks,
            "created_at": d.created_at
        })
    return {"documents": out}

@app.get("/api/evaluation/run")
def run_retrieval_evaluation(db: Session = Depends(get_db)):
    """Run retrieval quality benchmark suite (MRR, Hit@1, Hit@3, Hit@5) across Hybrid vs Semantic vs Keyword search."""
    comparison = RetrievalEvaluator.compare_all_modes(db)
    return comparison

# Mount static frontend
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
