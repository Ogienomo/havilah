"""
Havilah OS — HermesRun Model

Persists orchestration run state so pending approvals survive restarts.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID

from backend.models.mixins import Base


class HermesRun(Base):
    __tablename__ = "hermes_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instruction = Column(Text, nullable=False)
    source = Column(String(50), nullable=False, default="api")
    status = Column(String(50), nullable=False, default="pending", index=True)
    plan = Column(JSON, nullable=True)
    results = Column(JSON, nullable=True, default=list)
    context = Column(JSON, nullable=True, default=dict)
    error = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)
