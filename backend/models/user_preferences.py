"""
Havilah OS — UserPreferences Model

Stores per-user settings that need to persist across sessions and devices,
such as the auto_approve toggle for Hermes runs.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID

from backend.models.mixins import Base


class UserPreferences(Base):
    __tablename__ = "user_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
    auto_approve = Column(Boolean, nullable=False, default=False)
    preferences = Column(JSON, nullable=True, default=dict)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
