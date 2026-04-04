"""
database.py — Database connection and session management.

SQLAlchemy engine + session factory.
All models import Base from here.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Create engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,       # Check connection before using
    pool_size=10,             # Max 10 connections in pool
    max_overflow=20,          # 20 extra connections if needed
    echo=False,               # Set True to see SQL queries in logs
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base class for all models
Base = declarative_base()


def get_db():
    """
    FastAPI dependency — yields a DB session per request.
    Automatically closes session after request completes.

    Usage in endpoint:
        def my_route(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables in database. Called on app startup."""
    from models import Company, AnalysisRecord  # noqa: F401
    Base.metadata.create_all(bind=engine)