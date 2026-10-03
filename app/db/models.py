"""
SQLAlchemy ORM Models for Document Intelligence Search System.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Text, DateTime, Date, Boolean, ForeignKey, Float
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"

    document_id = Column(Integer, primary_key=True, index=True)
    doc_identifier = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    source_url = Column(Text, nullable=True)
    author = Column(String(150), nullable=True)
    published_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    version_id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.document_id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False)
    checksum = Column(String(64), nullable=False)
    raw_content = Column(Text, nullable=False)
    chunk_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="versions")
    chunks = relationship("Chunk", back_populates="version", cascade="all, delete-orphan")


class Chunk(Base):
    __tablename__ = "chunks"

    chunk_id = Column(Integer, primary_key=True, index=True)
    version_id = Column(Integer, ForeignKey("document_versions.version_id", ondelete="CASCADE"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.document_id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_hash = Column(String(64), nullable=False, index=True)
    section_title = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    start_char = Column(Integer, nullable=False)
    end_char = Column(Integer, nullable=False)
    
    # Store JSON representation of embedding vector for SQLite / standard SQL
    embedding_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="chunks")
    version = relationship("DocumentVersion", back_populates="chunks")


class RetrievalEvaluation(Base):
    __tablename__ = "retrieval_evaluations"

    eval_id = Column(Integer, primary_key=True, index=True)
    query = Column(String(500), nullable=False)
    expected_doc_identifier = Column(String(100), nullable=False)
    search_mode = Column(String(50), nullable=False)
    top_retrieved_docs = Column(Text, nullable=False) # JSON array
    rank_of_expected = Column(Integer, nullable=True)
    hit_at_1 = Column(Boolean, nullable=False)
    hit_at_3 = Column(Boolean, nullable=False)
    hit_at_5 = Column(Boolean, nullable=False)
    reciprocal_rank = Column(Float, nullable=False)
    evaluated_at = Column(DateTime, default=datetime.utcnow)
