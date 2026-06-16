"""
Havilah OS — Risk Assessment Repository
"""

from sqlalchemy import text
from backend.models.risk import RiskAssessment
from backend.repositories.base import get_session


class RiskRepository:

    def calculate_risk(self, approval_id, action_type: str, channel: str, **kwargs) -> dict:
        """Calculate risk level for an approval request."""
        # Risk scoring logic based on action type and channel
        risk_rules = {
            ("send_message", "whatsapp"): ("low", 20.0, 0.9),
            ("send_message", "email"): ("low", 25.0, 0.85),
            ("send_message", "linkedin"): ("medium", 40.0, 0.8),
            ("publish_content", "linkedin"): ("medium", 50.0, 0.7),
            ("share_file", "email"): ("medium", 45.0, 0.75),
            ("financial_action", "*"): ("critical", 90.0, 0.3),
            ("contract_sign", "*"): ("critical", 95.0, 0.2),
        }

        risk_level, risk_score, confidence = risk_rules.get(
            (action_type, channel),
            ("medium", 50.0, 0.5)  # default: medium risk
        )

        # Check for high-risk overrides
        if kwargs.get("external_audience"):
            risk_score = min(risk_score + 20, 100)
        if kwargs.get("irreversible"):
            risk_score = min(risk_score + 30, 100)

        # Recalculate level based on score
        if risk_score >= 80:
            risk_level = "critical"
        elif risk_score >= 55:
            risk_level = "high"
        elif risk_score >= 30:
            risk_level = "medium"
        else:
            risk_level = "low"

        approval_required = risk_level in ("medium", "high", "critical")
        escalation_required = risk_level in ("high", "critical")

        with get_session() as db:
            assessment = RiskAssessment(
                approval_request_id=approval_id,
                risk_level=risk_level,
                risk_score=risk_score,
                confidence=confidence,
                approval_required=approval_required,
                escalation_required=escalation_required,
                assessed_by="system",
            )
            db.add(assessment)
            db.flush()
            return {
                "id": str(assessment.id),
                "risk_level": assessment.risk_level,
                "risk_score": float(assessment.risk_score),
                "approval_required": assessment.approval_required,
                "escalation_required": assessment.escalation_required,
            }

    def get_by_id(self, risk_id):
        with get_session() as db:
            ra = db.query(RiskAssessment).filter(RiskAssessment.id == risk_id).first()
            if not ra:
                return None
            return {
                "id": str(ra.id),
                "risk_level": ra.risk_level,
                "risk_score": float(ra.risk_score),
                "approval_required": ra.approval_required,
            }
