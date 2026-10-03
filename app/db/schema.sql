-- Document Intelligence Search Database Schema
-- Target: PostgreSQL 14+ with pgvector extension

-- 1. Enable vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Master Documents Table
DROP TABLE IF EXISTS chunks CASCADE;
DROP TABLE IF EXISTS document_versions CASCADE;
DROP TABLE IF EXISTS documents CASCADE;
DROP TABLE IF EXISTS retrieval_evaluations CASCADE;

CREATE TABLE documents (
    document_id SERIAL PRIMARY KEY,
    doc_identifier VARCHAR(100) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    source_url TEXT,
    author VARCHAR(150),
    published_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Document Versioning Table
CREATE TABLE document_versions (
    version_id SERIAL PRIMARY KEY,
    document_id INT NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    version_number INT NOT NULL,
    checksum VARCHAR(64) NOT NULL, -- SHA256 of full document text
    raw_content TEXT NOT NULL,
    chunk_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT idx_doc_version_unique UNIQUE(document_id, version_number)
);

-- 4. Chunks Table (Vector + Full Text Search)
CREATE TABLE chunks (
    chunk_id SERIAL PRIMARY KEY,
    version_id INT NOT NULL REFERENCES document_versions(version_id) ON DELETE CASCADE,
    document_id INT NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    chunk_hash VARCHAR(64) NOT NULL, -- MD5 hash for chunk deduplication
    section_title VARCHAR(255),
    content TEXT NOT NULL,
    start_char INT NOT NULL,
    end_char INT NOT NULL,
    
    -- Hybrid Search Columns:
    -- Vector Cosine Distance Embedding (384 dimensions)
    embedding vector(384),
    
    -- Full Text Search Keyword TSVector
    search_vector tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', COALESCE(section_title, '')), 'A') ||
        setweight(to_tsvector('english', content), 'B')
    ) STORED,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT idx_chunk_hash_unique UNIQUE(version_id, chunk_hash)
);

-- 5. Indexes for High Performance Hybrid Retrieval
CREATE INDEX idx_chunks_doc_id ON chunks(document_id);
CREATE INDEX idx_chunks_version_id ON chunks(version_id);
CREATE INDEX idx_chunks_search_vector ON chunks USING gin(search_vector);
CREATE INDEX idx_chunks_embedding ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- 6. Retrieval Evaluation Results Table
CREATE TABLE retrieval_evaluations (
    eval_id SERIAL PRIMARY KEY,
    query VARCHAR(500) NOT NULL,
    expected_doc_identifier VARCHAR(100) NOT NULL,
    search_mode VARCHAR(50) NOT NULL, -- 'semantic', 'keyword', 'hybrid'
    top_retrieved_docs TEXT NOT NULL, -- JSON array of retrieved doc identifiers
    rank_of_expected INT,
    hit_at_1 BOOLEAN NOT NULL,
    hit_at_3 BOOLEAN NOT NULL,
    hit_at_5 BOOLEAN NOT NULL,
    reciprocal_rank NUMERIC(5,4) NOT NULL,
    evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
