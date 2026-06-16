"""
Havilah OS — Meeting Domain Model

Entities: Meeting, AgendaItem, MeetingDecision, MeetingActionItem
Part of the Meeting bounded context.

Meetings are structured workflows, not casual chats.
"""

from sqlalchemy import Column, Text, ForeignKey, Integer, Date, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from backend.database import Base
from backend.models.mixins import UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin


class Meeting(UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin, Base):
    __tablename__ = "meetings"

    title = Column(Text, nullable=False)
    meeting_type = Column(Text, nullable=False, default="internal")  # internal, client, strategy, review, standup
    status = Column(Text, nullable=False, default="scheduled")  # scheduled, in_progress, completed, cancelled
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_minutes = Column(Integer)
    transcript = Column(Text)
    summary = Column(Text)
    organizer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    participants = Column(JSONB, default=list)  # [{name, role, contact_id}]

    # ── Relationships ─────────────────────────────────────────
    agenda_items = relationship("AgendaItem", back_populates="meeting", lazy="selectin")
    decisions = relationship("MeetingDecision", back_populates="meeting", lazy="selectin")
    action_items = relationship("MeetingActionItem", back_populates="meeting", lazy="selectin")


class AgendaItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "agenda_items"

    meeting_id = Column(UUID(as_uuid=True), ForeignKey("meetings.id"), nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text)
    order_index = Column(Integer, nullable=False, default=0)
    duration_minutes = Column(Integer)
    status = Column(Text, nullable=False, default="pending")  # pending, discussed, deferred, skipped
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # ── Relationships ─────────────────────────────────────────
    meeting = relationship("Meeting", back_populates="agenda_items")


class MeetingDecision(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "meeting_decisions"

    meeting_id = Column(UUID(as_uuid=True), ForeignKey("meetings.id"), nullable=False)
    decision_text = Column(Text, nullable=False)
    decided_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    rationale = Column(Text)

    # ── Relationships ─────────────────────────────────────────
    meeting = relationship("Meeting", back_populates="decisions")


class MeetingActionItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "meeting_action_items"

    meeting_id = Column(UUID(as_uuid=True), ForeignKey("meetings.id"), nullable=False)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=True)
    description = Column(Text, nullable=False)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    due_date = Column(Date, nullable=True)
    status = Column(Text, nullable=False, default="pending")  # pending, in_progress, completed

    # ── Relationships ─────────────────────────────────────────
    meeting = relationship("Meeting", back_populates="action_items")
    task = relationship("Task")
