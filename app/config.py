"""
Configuration settings for Document Intelligence Search System.
"""

import os

class Settings:
    PROJECT_NAME: str = "Document Intelligence Search System"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # Vector Embedding Specs
    EMBEDDING_DIM: int = 384
    DEFAULT_CHUNK_SIZE: int = 500
    DEFAULT_CHUNK_OVERLAP: int = 100
    
    # RRF Hybrid Search Weights
    RRF_K_CONSTANT: int = 60
    DEFAULT_SEMANTIC_WEIGHT: float = 0.6
    DEFAULT_KEYWORD_WEIGHT: float = 0.4
    
    # Database Settings
    POSTGRES_USER: str = os.environ.get("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.environ.get("POSTGRES_PASSWORD", "postgres")
    POSTGRES_HOST: str = os.environ.get("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.environ.get("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.environ.get("POSTGRES_DB", "doc_search_db")

settings = Settings()
