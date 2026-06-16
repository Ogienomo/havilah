"""
Havilah OS — Memory Domain Model

Entities: MemoryItem, MemorySource, MemoryEvent, MemoryLink
Part of the Memory bounded context.

Memory Is a First-Class Citizen — not conversation history.
Memory is structured business knowledge.

Types: profile, client, project, communication, operational, research, approval, meeting
Importance: low, medium, high, critical
Status: active, archived, superseded, invalidated
"""

from sqlalchemy import Column, Text, ForeignKey, Numeric, Integer, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.database import Base
from backend.models.mixins import UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin


class MemoryItem(UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin, Base):
    __tablename__ = "memory_items"

    memory_type = Column(Text, nullable=False)  # profile, client, project, communication, operational, research, approval, meeting
    scope = Column(Text, nullable=False, default="global")  # global, contact, project, task
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    related_contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=True)
    related_project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    related_task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=True)
    source_type = Column(Text, nullable=False, default="user")  # user, system, agent, inference
    source_reference = Column(Text)
    confidence = Column(Numeric(3, 2), nullable=False, default=1.0)  # 0.0-1.0
    importance = Column(Text, nullable=False, default="medium")  # low, medium, high, critical
    is_pinned = Column(Boolean, nullable=False, default=False)
    status = Column(Text, nullable=False, default="active")  # active, archived, superseded, invalidated
    access_count = Column(Integer, nullable=False, default=0)
    reinforcement_count = Column(Integer, nullable=False, default=0)
    last_reinforced_at = Column(DateTime(timezone=True), nullable=True)
    valid_from = Column(DateTime(timezone=True), nullable=True)
    valid_to = Column(DateTime(timezone=True), nullable=True)
    superseded_by = Column(UUID(as_uuid=True), ForeignKey("memory_items.id"), nullable=True)

    # ── Relationships ─────────────────────────────────────────
    sources = relationship("MemorySource", back_populates="memory_item", lazy="selectin")
    events = relationship("MemoryEvent", back_populates="memory_item", lazy="selectin")
    links = relationship("MemoryLink", back_populates="memory_item", lazy="selectin")
    superseding_memory = relationship("MemoryItem", remote_side="MemoryItem.id", foreign_keys=[superseded_by])


class MemorySource(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "memory_sources"

    memory_item_id = Column(UUID(as_uuid=True), ForeignKey("memory_items.id"), nullable=False)
    source_type = Column(Text, nullable=False)  # conversation, document, observation, inference, approval
    source_reference = Column(Text)
    source_summary = Column(Text)
    source_confidence = Column(Numeric(3, 2))

    # ── Relationships ─────────────────────────────────────────
    memory_item = relationship("MemoryItem", back_populates="sources")


class MemoryEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "memory_events"

    memory_item_id = Column(UUID(as_uuid=True), ForeignKey("memory_items.id"), nullable=False)
    event_type = Column(Text, nullable=False)  # captured, recalled, reinforced, archived, superseded, invalidated, linked
    old_status = Column(Text)
    new_status = Column(Text)
    note = Column(Text)

    # ── Relationships ─────────────────────────────────────────
    memory_item = relationship("MemoryItem", back_populates="events")


class MemoryLink(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "memory_links"

    memory_id = Column(UUID(as_uuid=True), ForeignKey("memory_items.id"), nullable=False)
    linked_entity_type = Column(Text, nullable=False)  # contact, project, task, approval, meeting, research
    linked_entity_id = Column(UUID(as_uuid=True), nullable=False)
    relationship_type = Column(Text, nullable=False, default="related")  # related, primary, context, source

    # ── Relationships ─────────────────────────────────────────
    memory_item = relationship("MemoryItem", back_populates="links")
