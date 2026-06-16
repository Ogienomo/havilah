"""
Havilah OS Database Module

Central database engine, session factory, and base model class.
All models import Base from this module — never declare their own.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    sessionmaker,
    MappedAsDataclass,
)
from typing import Generator

from backend.config.settings import get_settings


# ── Declarative Base (single source of truth) ────────────────
class Base(DeclarativeBase):
    """Shared declarative base for all Havilah OS ORM models."""
    pass


# ── Engine & Session Factory ─────────────────────────────────
_settings = get_settings()

engine = create_engine(
    _settings.DATABASE_URL,
    echo=_settings.DB_ECHO,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator:
    """Dependency injection helper — yields a DB session and guarantees close."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
