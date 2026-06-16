"""
Havilah OS — Shared Model Mixins

Provides reusable column definitions that every table inherits,
following the SAS convention: id, created_at, updated_at, metadata.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, Text, DateTime, text
from sqlalchemy.dialects.postgresql import UUID, JSONB

from backend.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    """Adds created_at and updated_at columns with server defaults."""
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        default=utcnow,
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        default=utcnow,
        onupdate=utcnow,
    )


class UUIDPrimaryKeyMixin:
    """Adds a UUID primary key with server-side generation."""
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        default=uuid.uuid4,
    )


class MetadataMixin:
    """Adds a flexible JSONB metadata column."""
    metadata_ = Column(
        "metadata",
        JSONB,
        nullable=True,
        default=dict,
    )
