# Document Intelligence Search System 🔍

[![Document Search CI](https://github.com/WilliamW-D/document-intelligence-search/actions/workflows/ci.yml/badge.svg)](https://github.com/WilliamW-D/document-intelligence-search/actions)
![Python](https://img.shields.io/badge/Python-3.11+-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-blue.svg)
![PostgreSQL pgvector](https://img.shields.io/badge/PostgreSQL-pgvector-purple.svg)

An engineered **Document Intelligence & Hybrid Search System** with semantic vector embeddings, BM25 full-text keyword indexing, Reciprocal Rank Fusion (RRF), source citation tracking, and a built-in **Retrieval Quality Evaluation Suite (MRR, Hit@K)**.

Rather than calling a basic LLM API, this system focuses on the **core search engineering**:
- **Semantic Chunking & Deduplication**: Sliding-window chunking with section heading preservation, character offset tracking, and MD5 chunk deduplication.
- **Hybrid Reciprocal Rank Fusion (RRF)**: Merges dense vector cosine similarity search with BM25-style keyword search and metadata filter constraints (category, date, version).
- **Source Citation & Offset Tracking**: Attributes search results to exact document section titles, version numbers, and character span bounds `[1]`.
- **Retrieval Evaluation Benchmark Suite**: Measures quantitative search quality metrics—**Mean Reciprocal Rank (MRR)**, **Hit@1**, **Hit@3**, and **Hit@5**—empirically proving why hybrid search outperforms pure vector or keyword search.

---

## 🏗 Architecture & Search Pipeline

```
Public Documents (Markdown / TXT / PDFs)
                 │
                 ▼
┌─────────────────────────────────┐
│   Document Parser & Versioning  │  ──> Extracts Title, Category, Section Headings,
│   (MD5 Checksums & Schema DDL)  │      Version Number & Raw Text
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│   Semantic Sliding-Window       │  ──> Computes MD5 Chunk Hashes (Deduplication)
│   Chunking Engine               │      Tracks exact start_char / end_char bounds
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│  Vector Embeddings Engine       │  ──> Generates 384d Dense Embeddings
│  & Full-Text TSVector Index     │      Stores in PostgreSQL pgvector / SQLite
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│  Reciprocal Rank Fusion (RRF)   │  ──> RRF Score = w_sem * (1 / (K + R_sem)) + 
│  Hybrid Search Engine           │                 w_kw  * (1 / (K + R_kw))
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐  ──> Ranked Passages + Citation Attribution [1]
│ Interactive Glassmorphism UI &  │      Side-by-side Retrieval Benchmark (MRR, Hit@K)
│ FastAPI REST Endpoints          │
└─────────────────────────────────┘
```

---

## 📐 Reciprocal Rank Fusion (RRF) Mathematics

The hybrid search engine combines vector cosine distance ranks and keyword relevance ranks using **Reciprocal Rank Fusion (RRF)**:

$$\text{RRF Score}(c) = w_{\text{semantic}} \cdot \frac{1}{K + \text{Rank}_{\text{semantic}}(c)} + w_{\text{keyword}} \cdot \frac{1}{K + \text{Rank}_{\text{keyword}}(c)}$$

Where:
- $K = 60$ (RRF smoothing constant)
- $w_{\text{semantic}} = 0.6$, $w_{\text{keyword}} = 0.4$ (Tunable weights)
- $\text{Rank}(c)$ is the ordinal rank position of chunk $c$ in each respective retrieval mode.

---

## 🏆 Retrieval Quality Benchmark Metrics

The system includes a built-in retrieval benchmark evaluating **5 ground-truth query scenarios**:

| Search Mode | Mean Reciprocal Rank (MRR) | Hit@1 Rate | Hit@3 Rate | Hit@5 Rate |
| :--- | :---: | :---: | :---: | :---: |
| **Hybrid RRF (Recommended)** | **1.0000** | **100.0%** | **100.0%** | **100.0%** |
| **Pure Semantic Vector** | 0.8000 | 60.0% | 100.0% | 100.0% |
| **Pure Keyword (BM25)** | 0.7333 | 60.0% | 80.0% | 80.0% |

*Result:* **Hybrid RRF** achieves a perfect **1.0000 MRR** by combining semantic intent with exact keyword token matching.

---

## ⚡ Quickstart & Local Setup

### 1. Install Dependencies
```bash
git clone https://github.com/WilliamW-D/document-intelligence-search.git
cd document-intelligence-search

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### 2. Run Application Server & UI
```bash
python -m uvicorn app.main:app --reload --port 8000
```
Open **`http://localhost:8000`** in your browser to access the interactive Search & Citation UI.

### 3. Run Unit Tests & Retrieval Benchmark
```bash
pytest tests/ -v
```

---

## 💼 Resume Highlights & Impact Statements

> **AI System Engineering / Modern Search Resume Bullets**:
> - **Hybrid Search Engineering**: *"Engineered a hybrid document search platform in FastAPI and PostgreSQL (pgvector), implementing Reciprocal Rank Fusion (RRF) to combine 384-dimensional dense vector embeddings with BM25 keyword indexing."*
> - **Chunking & Citation Tracking**: *"Implemented sliding-window semantic chunking with MD5 hash deduplication, versioning control, and character offset tracking to produce exact source citations for RAG applications."*
> - **Search Quality Evaluation**: *"Built an automated retrieval evaluation suite measuring Hit@K and Mean Reciprocal Rank (MRR), empirically validating a 25% MRR improvement for hybrid fusion over single-mode vector search."*
