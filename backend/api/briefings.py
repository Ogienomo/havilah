"""
Havilah OS — Briefings API

Executive briefings, contact briefings, and approval briefings.
AI generates insights; humans consume and decide.
All endpoints require authentication.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from backend.api.deps import get_briefing_service
from backend.api.middleware import RequirePermission
from backend.services.briefing_service import BriefingService

router = APIRouter(prefix="/api/briefings", tags=["Briefings"])


@router.get("/executive")
def executive_briefing(
    user: dict = Depends(RequirePermission("briefing:read")),
    service: BriefingService = Depends(get_briefing_service),
):
    """Generate an executive briefing with system-wide metrics."""
    return service.generate_executive_briefing()


@router.get("/contact/{contact_id}")
def contact_briefing(
    contact_id: UUID,
    user: dict = Depends(RequirePermission("briefing:read")),
    service: BriefingService = Depends(get_briefing_service),
):
    """Generate a briefing for a specific contact."""
    try:
        return service.generate_contact_briefing(contact_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/approval/{approval_id}")
def approval_briefing(
    approval_id: UUID,
    user: dict = Depends(RequirePermission("briefing:read")),
    service: BriefingService = Depends(get_briefing_service),
):
    """Generate a briefing for a specific approval request."""
    try:
        return service.generate_approval_briefing(approval_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
