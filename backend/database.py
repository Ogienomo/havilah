"""
Havilah OS Database Module

Central database engine, session factory, and base model class.
All models import Base from this module — never declare their own.
"""

import os

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

# Build connect_args: Railway/Supabase/Render Postgres requires SSL.
# Honor PGSSLMODE env var (libpq convention) if set, else default to "require"
# for production deployments.
ssl_mode = os.getenv("PGSSLMODE", "require" if _settings.ENVIRONMENT == "production" else "prefer")
# PGCONNECT_TIMEOUT (libpq) caps how long a connection attempt can hang.
connect_timeout = int(os.getenv("PGCONNECT_TIMEOUT", "10"))

engine = create_engine(
    _settings.DATABASE_URL,
    echo=_settings.DB_ECHO,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    connect_args={
        "sslmode": ssl_mode,
        "connect_timeout": connect_timeout,
        "application_name": "havilah-backend",
    },
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
