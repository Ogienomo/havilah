"""
Havilah OS — Notification Domain Model

Entities: Notification, NotificationDelivery

Events should generate notifications:
  - Approval Needed
  - Task Overdue
  - Project Completed
  - Agent Completed / Failed

Events: NotificationCreated, NotificationDelivered
"""

from sqlalchemy import Column, Text, ForeignKey, Integer, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from backend.database import Base
from backend.models.mixins import UUIDPrimaryKeyMixin, TimestampMixin


class Notification(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "notifications"

    notification_type = Column(Text, nullable=False)  # approval_needed, task_overdue, project_completed, agent_completed, agent_failed, system_alert
    title = Column(Text, nullable=False)
    message = Column(Text, nullable=False)
    priority = Column(Text, nullable=False, default="medium")  # low, medium, high, urgent
    status = Column(Text, nullable=False, default="pending")  # pending, sent, delivered, read, dismissed
    category = Column(Text, nullable=False, default="operational")  # operational, approval, alert, system
    recipient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    related_entity_type = Column(Text)  # approval, task, project, agent_run
    related_entity_id = Column(UUID(as_uuid=True))
    action_url = Column(Text)  # deep link for action
    action_required = Column(Boolean, nullable=False, default=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)

    # ── Relationships ─────────────────────────────────────────
    deliveries = relationship("NotificationDelivery", back_populates="notification", lazy="selectin")


class NotificationDelivery(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "notification_deliveries"

    notification_id = Column(UUID(as_uuid=True), ForeignKey("notifications.id"), nullable=False)
    channel = Column(Text, nullable=False)  # in_app, email, whatsapp, push, sms
    status = Column(Text, nullable=False, default="pending")  # pending, sent, delivered, failed
    external_id = Column(Text)  # ID from delivery service
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text)

    # ── Relationships ─────────────────────────────────────────
    notification = relationship("Notification", back_populates="deliveries")
