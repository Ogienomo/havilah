"""
Havilah OS — Risk Assessment Domain Model

Entity: RiskAssessment
Calculates risk levels for approval requests.

Risk Levels: low, medium, high, critical
Triggers: RiskCalculated, RiskEscalated
"""

from sqlalchemy import Column, Text, ForeignKey, Numeric, Boolean, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from backend.database import Base
from backend.models.mixins import UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin


class RiskAssessment(UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin, Base):
    __tablename__ = "risk_assessments"

    approval_request_id = Column(UUID(as_uuid=True), ForeignKey("approval_requests.id"), nullable=True)
    risk_level = Column(Text, nullable=False, default="medium")  # low, medium, high, critical
    risk_score = Column(Numeric(5, 2), nullable=False, default=50.0)  # 0-100
    confidence = Column(Numeric(3, 2), nullable=False, default=0.5)  # 0.0-1.0
    approval_required = Column(Boolean, nullable=False, default=True)
    escalation_required = Column(Boolean, nullable=False, default=False)
    risk_factors = Column(JSONB, nullable=False, default=list)  # [{"factor": "external_audience", "weight": 0.8}, ...]
    mitigation_suggestions = Column(JSONB, nullable=False, default=list)  # ["Requires human review", ...]
    assessed_by = Column(Text, nullable=False, default="system")  # system, human, agent
    assessed_at = Column(DateTime(timezone=True), nullable=True)

    # ── Relationships ─────────────────────────────────────────
    approval_requests = relationship("ApprovalRequest", foreign_keys="ApprovalRequest.risk_assessment_id", back_populates="risk_assessment")
