"""
Database Connection Engine & Session Factory.
Supports PostgreSQL (with pgvector) and SQLite file database fallbacks.
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.db.models import Base

def get_db_url_and_engine():
    pg_url = f"postgresql+psycopg2://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    
    try:
        engine = create_engine(pg_url, connect_args={"connect_timeout": 2})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
        print(f"📡 Connected to PostgreSQL Database ({pg_url.split('@')[-1]})")
        return engine, "postgresql"
    except Exception as e:
        print(f"⚠️ PostgreSQL connection unavailable ({e}). Using SQLite file database fallback.")
        data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
        os.makedirs(data_dir, exist_ok=True)
        sqlite_path = os.path.join(data_dir, "doc_search.sqlite")
        sqlite_url = f"sqlite:///{sqlite_path}"
        engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})
        return engine, "sqlite"

engine, DB_DIALECT = get_db_url_and_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database tables."""
    if DB_DIALECT == "postgresql":
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
            if os.path.exists(schema_path):
                with open(schema_path, "r", encoding="utf-8") as f:
                    conn.execute(text(f.read()))
    else:
        Base.metadata.create_all(bind=engine)
    print(f"✅ Database tables initialized successfully ({DB_DIALECT.upper()})")

def get_db():
    """Dependency provider for FastAPI endpoint session injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
