"""
Havilah OS — Workflow Engine Domain Model

Entities: Workflow, WorkflowStep, WorkflowTransition

Workflows orchestrate multi-step business processes.
Example: LinkedIn Growth Initiative → Task 1 → Task 2 → Task 3

Events: WorkflowCreated, WorkflowStarted, WorkflowStepStarted, WorkflowStepCompleted, WorkflowCompleted
"""

from sqlalchemy import Column, Text, ForeignKey, Integer, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from backend.database import Base
from backend.models.mixins import UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin


class Workflow(UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin, Base):
    __tablename__ = "workflows"

    title = Column(Text, nullable=False)
    description = Column(Text)
    workflow_type = Column(Text, nullable=False, default="sequential")  # sequential, parallel, conditional
    status = Column(Text, nullable=False, default="draft")  # draft, active, paused, completed, cancelled
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    current_step_order = Column(Integer, nullable=False, default=0)
    auto_advance = Column(Boolean, nullable=False, default=False)  # auto-advance on step completion
    trigger_rules = Column(JSONB, default=dict)  # conditions for auto-start

    # ── Relationships ─────────────────────────────────────────
    project = relationship("Project", back_populates="workflows")
    steps = relationship("WorkflowStep", back_populates="workflow", lazy="selectin", order_by="WorkflowStep.step_order")
    transitions = relationship("WorkflowTransition", back_populates="workflow", lazy="selectin")


class WorkflowStep(UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin, Base):
    __tablename__ = "workflow_steps"

    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text)
    step_order = Column(Integer, nullable=False, default=0)
    step_type = Column(Text, nullable=False, default="task")  # task, approval, review, notification, agent_action
    status = Column(Text, nullable=False, default="pending")  # pending, in_progress, completed, skipped, failed
    task_template = Column(JSONB, default=dict)  # template for creating task when step starts
    approval_template = Column(JSONB, default=dict)  # template for creating approval when step starts
    agent_action = Column(JSONB, default=dict)  # agent configuration for agent_action steps
    requires_approval = Column(Boolean, nullable=False, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # ── Relationships ─────────────────────────────────────────
    workflow = relationship("Workflow", back_populates="steps")
    tasks = relationship("Task", back_populates="workflow_step")
    transitions_from = relationship("WorkflowTransition", foreign_keys="WorkflowTransition.from_step_id", back_populates="from_step")
    transitions_to = relationship("WorkflowTransition", foreign_keys="WorkflowTransition.to_step_id", back_populates="to_step")


class WorkflowTransition(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "workflow_transitions"

    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False)
    from_step_id = Column(UUID(as_uuid=True), ForeignKey("workflow_steps.id"), nullable=True)  # None = start
    to_step_id = Column(UUID(as_uuid=True), ForeignKey("workflow_steps.id"), nullable=True)  # None = end
    condition = Column(JSONB, default=dict)  # {"field": "status", "operator": "eq", "value": "completed"}
    transition_type = Column(Text, nullable=False, default="on_complete")  # on_complete, on_approval, on_condition, manual

    # ── Relationships ─────────────────────────────────────────
    workflow = relationship("Workflow", back_populates="transitions")
    from_step = relationship("WorkflowStep", foreign_keys=[from_step_id], back_populates="transitions_from")
    to_step = relationship("WorkflowStep", foreign_keys=[to_step_id], back_populates="transitions_to")
