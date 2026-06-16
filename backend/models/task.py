"""
Havilah OS — Task Execution Domain Model

Entities: Task, TaskDependency
Part of the Task bounded context.
"""

import uuid

from sqlalchemy import Column, Text, ForeignKey, Boolean, Integer, Date, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.database import Base
from backend.models.mixins import UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin


class Task(UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin, Base):
    __tablename__ = "tasks"

    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    parent_task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=True)
    workflow_step_id = Column(UUID(as_uuid=True), ForeignKey("workflow_steps.id"), nullable=True)
    title = Column(Text, nullable=False)
    description = Column(Text)
    status = Column(Text, nullable=False, default="pending")  # pending, in_progress, completed, blocked, cancelled
    priority = Column(Text, nullable=False, default="medium")  # low, medium, high, critical
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    assigned_to = Column(UUID(as_uuid=True), nullable=True)  # FK to agent_runs.id or users.id
    due_date = Column(Date, nullable=True)
    block_reason = Column(Text)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # ── Relationships ─────────────────────────────────────────
    project = relationship("Project", back_populates="tasks")
    parent_task = relationship("Task", remote_side="Task.id", back_populates="subtasks")
    subtasks = relationship("Task", back_populates="parent_task", lazy="selectin")
    workflow_step = relationship("WorkflowStep", back_populates="tasks")
    approvals = relationship("ApprovalRequest", back_populates="task", lazy="selectin")
    # Task dependencies where this task blocks others
    blocking = relationship("TaskDependency", foreign_keys="TaskDependency.blocking_task_id", back_populates="blocking_task")
    # Task dependencies where this task is blocked by others
    blocked_by = relationship("TaskDependency", foreign_keys="TaskDependency.blocked_task_id", back_populates="blocked_task")


class TaskDependency(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "task_dependencies"

    blocking_task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    blocked_task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    dependency_type = Column(Text, nullable=False, default="finish_to_start")  # finish_to_start, start_to_start, finish_to_finish

    # ── Relationships ─────────────────────────────────────────
    blocking_task = relationship("Task", foreign_keys=[blocking_task_id], back_populates="blocking")
    blocked_task = relationship("Task", foreign_keys=[blocked_task_id], back_populates="blocked_by")
