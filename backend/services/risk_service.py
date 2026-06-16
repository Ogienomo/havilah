"""
Havilah OS — Risk Assessment Service

Calculates risk levels for approval requests.
Risk Levels: low, medium, high, critical
"""

from backend.repositories.risk_repository import RiskRepository
from backend.repositories.event_repository import EventRepository
from backend.events import RISK_CALCULATED, RISK_ESCALATED


class RiskService:

    def __init__(self):
        self.repository = RiskRepository()
        self.event_repository = EventRepository()

    def calculate_risk(self, approval_id, action_type: str, channel: str, **kwargs):
        assessment = self.repository.calculate_risk(approval_id, action_type, channel, **kwargs)

        self.event_repository.save(
            aggregate_type="risk_assessment",
            aggregate_id=assessment["id"],
            event_type=RISK_CALCULATED,
            payload={
                "approval_id": str(approval_id),
                "risk_level": assessment["risk_level"],
                "risk_score": assessment["risk_score"],
                "approval_required": assessment["approval_required"],
            },
        )

        if assessment["escalation_required"]:
            self.event_repository.save(
                aggregate_type="risk_assessment",
                aggregate_id=assessment["id"],
                event_type=RISK_ESCALATED,
                payload={
                    "approval_id": str(approval_id),
                    "risk_level": assessment["risk_level"],
                    "risk_score": assessment["risk_score"],
                },
            )

        return assessment

    def get_assessment(self, risk_id):
        return self.repository.get_by_id(risk_id)
