"""
Havilah OS — Risk API

Risk assessment for approval requests.
Risk Levels: low, medium, high, critical
All endpoints require authentication.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from backend.api.deps import get_risk_service
from backend.api.middleware import RequirePermission
from backend.schemas.schemas import RiskCalculateInput, RiskResponse
from backend.services.risk_service import RiskService

router = APIRouter(prefix="/api/risk", tags=["Risk"])


@router.post("/calculate")
def calculate_risk(
    payload: RiskCalculateInput,
    user: dict = Depends(RequirePermission("risk:calculate")),
    service: RiskService = Depends(get_risk_service),
):
    """Calculate risk for an approval request.
    Both humans and agents can calculate risk."""
    return service.calculate_risk(
        approval_id=payload.approval_id,
        action_type=payload.action_type,
        channel=payload.channel,
        external_audience=payload.external_audience,
        irreversible=payload.irreversible,
    )


@router.get("/{risk_id}")
def get_risk_assessment(
    risk_id: UUID,
    user: dict = Depends(RequirePermission("risk:read")),
    service: RiskService = Depends(get_risk_service),
):
    """Get a risk assessment by ID."""
    assessment = service.get_assessment(risk_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Risk assessment not found")
    return assessment
