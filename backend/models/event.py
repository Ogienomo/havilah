"""
Havilah OS — Domain Event Model

The central append-only event log for the entire system.
Every significant state change produces an event.

Everything Is Traceable — every decision, prompt, tool call, approval, execution.
"""

from sqlalchemy import Column, Text, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB

from backend.database import Base
from backend.models.mixins import UUIDPrimaryKeyMixin, TimestampMixin


class DomainEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "domain_events"

    aggregate_type = Column(Text, nullable=False)  # approval, project, task, memory, workflow, agent, etc.
    aggregate_id = Column(UUID(as_uuid=True), nullable=False)
    event_type = Column(Text, nullable=False)  # e.g. ApprovalRequested, TaskCreated
    event_category = Column(Text, nullable=False, default="domain")  # domain, workflow, agent, system, audit
    actor_type = Column(Text, nullable=False, default="system")  # human, system, agent
    actor_id = Column(UUID(as_uuid=True), nullable=True)
    correlation_id = Column(UUID(as_uuid=True), nullable=True)  # links related events in a workflow
    causation_id = Column(UUID(as_uuid=True), nullable=True)  # what event caused this event
    payload = Column(JSONB, nullable=False, default=dict)
    version = Column(Integer, nullable=False, default=1)  # event schema version for replay safety
