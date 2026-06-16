"""
Havilah OS — Approval & Governance Domain Model

Entities: ApprovalRequest, ApprovalDecision, ApprovalEvent, ExecutionRecord, ApprovalPolicy
Part of the Approval bounded context — the soul of Havilah OS.

State Machine (current_state is the ONE source of truth):
  draft → proposed → queued_for_review → awaiting_approval → approved → executing → executed
                                                               ↘ rejected
                                                                ↘ expired

Rule: NOTHING external bypasses the Approval Ledger. Ever.
"""

from sqlalchemy import Column, Text, ForeignKey, Numeric, Boolean, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from backend.database import Base
from backend.models.mixins import UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin


# ── State Machine Constants ──────────────────────────────────
APPROVAL_STATES = {
    "draft",
    "proposed",
    "queued_for_review",
    "awaiting_approval",
    "approved",
    "rejected",
    "expired",
    "executing",
    "executed",
    "failed",
}

# High-level status groupings derived from current_state
PENDING_STATES = {"draft", "proposed", "queued_for_review", "awaiting_approval"}
ACTIVE_STATES = {"approved", "executing"}
TERMINAL_STATES = {"executed", "rejected", "expired", "failed"}


class ApprovalRequest(UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin, Base):
    __tablename__ = "approval_requests"

    action_type = Column(Text, nullable=False)  # send_message, publish_content, share_file, schedule_meeting
    channel = Column(Text, nullable=False, default="internal")  # email, whatsapp, linkedin, internal
    intent_summary = Column(Text, nullable=False)
    intent_detail = Column(Text)
    draft_payload = Column(JSONB, nullable=False, default=dict)
    related_project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    related_contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=True)
    related_task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    risk_level = Column(Text, nullable=False, default="medium")  # low, medium, high, critical
    confidence = Column(Numeric(3, 2))
    approval_required = Column(Boolean, nullable=False, default=True)
    current_state = Column(Text, nullable=False, default="draft")  # ONE source of truth — state machine
    approver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    decision_note = Column(Text)
    execution_status = Column(Text, nullable=False, default="not_started")  # not_started, in_progress, completed, failed
    rollback_possible = Column(Boolean, nullable=False, default=False)
    risk_assessment_id = Column(UUID(as_uuid=True), ForeignKey("risk_assessments.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    expired_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # ── Derived Status Properties ─────────────────────────────
    @property
    def status(self) -> str:
        """High-level status derived from current_state for API consumers."""
        if self.current_state in PENDING_STATES:
            return "pending"
        if self.current_state in ACTIVE_STATES:
            return self.current_state
        return self.current_state  # terminal states pass through

    # ── Relationships ─────────────────────────────────────────
    project = relationship("Project", foreign_keys=[related_project_id], back_populates="approvals")
    task = relationship("Task", foreign_keys=[related_task_id], back_populates="approvals")
    contact = relationship("Contact", foreign_keys=[related_contact_id])
    organization = relationship("Organization", foreign_keys=[organization_id])
    decisions = relationship("ApprovalDecision", back_populates="approval_request", lazy="selectin", order_by="ApprovalDecision.decided_at.desc()")
    events = relationship("ApprovalEvent", back_populates="approval_request", lazy="selectin", order_by="ApprovalEvent.created_at")
    execution_records = relationship("ExecutionRecord", back_populates="approval_request", lazy="selectin")
    risk_assessment = relationship("RiskAssessment", back_populates="approval_requests")
    communications = relationship("CommunicationHistory", back_populates="approval")


class ApprovalDecision(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "approval_decisions"

    approval_request_id = Column(UUID(as_uuid=True), ForeignKey("approval_requests.id"), nullable=False)
    decision_type = Column(Text, nullable=False)  # approve, reject, escalate, defer
    decision_reason = Column(Text)
    decided_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=False)
    escalated_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # who receives the escalation

    # ── Relationships ─────────────────────────────────────────
    approval_request = relationship("ApprovalRequest", back_populates="decisions")


class ApprovalEvent(UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin, Base):
    __tablename__ = "approval_events"

    approval_request_id = Column(UUID(as_uuid=True), ForeignKey("approval_requests.id"), nullable=False)
    event_type = Column(Text, nullable=False)  # created, risk_assessed, approved, rejected, execution_started, execution_completed, execution_failed, expired
    actor_type = Column(Text, nullable=False)  # human, system, agent
    actor_id = Column(UUID(as_uuid=True))
    old_state = Column(Text)
    new_state = Column(Text)
    note = Column(Text)

    # ── Relationships ─────────────────────────────────────────
    approval_request = relationship("ApprovalRequest", back_populates="events")


class ExecutionRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "execution_records"

    approval_request_id = Column(UUID(as_uuid=True), ForeignKey("approval_requests.id"), nullable=False)
    attempt_number = Column(Integer, nullable=False, default=1)
    execution_channel = Column(Text, nullable=False)  # email, whatsapp, linkedin, api, file
    execution_status = Column(Text, nullable=False, default="pending")  # pending, in_progress, completed, failed, rolled_back
    external_reference = Column(Text)  # ID from the external system
    error_code = Column(Text)
    error_message = Column(Text)
    result_payload = Column(JSONB)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # ── Relationships ─────────────────────────────────────────
    approval_request = relationship("ApprovalRequest", back_populates="execution_records")


class ApprovalPolicy(UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin, Base):
    """Defines when approval is required, who can approve, and escalation rules."""
    __tablename__ = "approval_policies"

    name = Column(Text, nullable=False, unique=True)
    description = Column(Text)
    category = Column(Text, nullable=False)  # communication, financial, project, strategic, administrative
    risk_threshold = Column(Text, nullable=False, default="medium")  # minimum risk level that triggers this policy
    approval_mode = Column(Text, nullable=False, default="manual")  # manual, smart, autonomous (autonomous disabled in v1)
    auto_approve_below_threshold = Column(Boolean, nullable=False, default=False)
    required_approver_role = Column(Text)  # e.g. "admin", "founder"
    expiration_hours = Column(Integer)  # how long before request expires
    escalation_policy = Column(JSONB, default=dict)  # {"escalate_after_hours": 24, "escalate_to_role": "admin"}
    is_active = Column(Boolean, nullable=False, default=True)
    priority = Column(Integer, nullable=False, default=0)  # higher = evaluated first
