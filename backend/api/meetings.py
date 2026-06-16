"""
Havilah OS — Meetings API

Meetings are structured workflows, not casual chats.
Every meeting produces decisions and action items.
All endpoints require authentication.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from backend.api.deps import get_meeting_service
from backend.api.middleware import RequirePermission
from backend.schemas.schemas import (
    MeetingCreate,
    MeetingComplete,
    AgendaItemCreate,
    MeetingDecisionCreate,
    MeetingActionItemCreate,
    MeetingResponse,
)
from backend.services.meeting_service import MeetingService

router = APIRouter(prefix="/api/meetings", tags=["Meetings"])


@router.post("/", response_model=MeetingResponse, status_code=201)
def create_meeting(
    payload: MeetingCreate,
    user: dict = Depends(RequirePermission("meeting:create")),
    service: MeetingService = Depends(get_meeting_service),
):
    """Create a new meeting. Requires meeting:create permission."""
    return service.create_meeting(payload.model_dump())


@router.get("/", response_model=list[MeetingResponse])
def list_meetings(
    project_id: UUID | None = None,
    status: str | None = None,
    user: dict = Depends(RequirePermission("meeting:read")),
    service: MeetingService = Depends(get_meeting_service),
):
    """List meetings, optionally filtered."""
    return service.list_meetings(project_id=project_id, status=status)


@router.get("/{meeting_id}")
def get_meeting(
    meeting_id: UUID,
    user: dict = Depends(RequirePermission("meeting:read")),
    service: MeetingService = Depends(get_meeting_service),
):
    """Get a meeting by ID."""
    meeting = service.get_meeting(meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting


@router.post("/{meeting_id}/complete")
def complete_meeting(
    meeting_id: UUID,
    payload: MeetingComplete,
    user: dict = Depends(RequirePermission("meeting:complete")),
    service: MeetingService = Depends(get_meeting_service),
):
    """Complete a meeting with an optional summary."""
    return service.complete_meeting(meeting_id, summary=payload.summary)


@router.post("/{meeting_id}/agenda")
def add_agenda_item(
    meeting_id: UUID,
    payload: AgendaItemCreate,
    user: dict = Depends(RequirePermission("meeting:add_agenda")),
    service: MeetingService = Depends(get_meeting_service),
):
    """Add an agenda item to a meeting."""
    return service.add_agenda_item(meeting_id, payload.model_dump())


@router.get("/{meeting_id}/agenda")
def get_agenda(
    meeting_id: UUID,
    user: dict = Depends(RequirePermission("meeting:read")),
    service: MeetingService = Depends(get_meeting_service),
):
    """Get all agenda items for a meeting."""
    return service.get_agenda(meeting_id)


@router.post("/{meeting_id}/decisions")
def add_decision(
    meeting_id: UUID,
    payload: MeetingDecisionCreate,
    user: dict = Depends(RequirePermission("meeting:add_decision")),
    service: MeetingService = Depends(get_meeting_service),
):
    """Record a meeting decision."""
    return service.add_decision(meeting_id, payload.model_dump())


@router.get("/{meeting_id}/decisions")
def get_decisions(
    meeting_id: UUID,
    user: dict = Depends(RequirePermission("meeting:read")),
    service: MeetingService = Depends(get_meeting_service),
):
    """Get all decisions from a meeting."""
    return service.get_decisions(meeting_id)


@router.post("/{meeting_id}/action-items")
def add_action_item(
    meeting_id: UUID,
    payload: MeetingActionItemCreate,
    user: dict = Depends(RequirePermission("meeting:add_action_item")),
    service: MeetingService = Depends(get_meeting_service),
):
    """Create an action item from a meeting."""
    return service.add_action_item(meeting_id, payload.model_dump())


@router.get("/{meeting_id}/action-items")
def get_action_items(
    meeting_id: UUID,
    user: dict = Depends(RequirePermission("meeting:read")),
    service: MeetingService = Depends(get_meeting_service),
):
    """Get all action items from a meeting."""
    return service.get_action_items(meeting_id)
