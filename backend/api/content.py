"""
Havilah OS — Content API

Content is always drafted by AI, reviewed by humans, published with approval.
ContentDraft -> ContentVersion -> ContentComment
All endpoints require authentication.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from backend.api.deps import get_content_service
from backend.api.middleware import RequirePermission
from backend.schemas.schemas import (
    ContentDraftCreate,
    ContentVersionCreate,
    ContentCommentCreate,
    ContentStatusUpdate,
    ContentDraftResponse,
)
from backend.services.content_service import ContentService

router = APIRouter(prefix="/api/content", tags=["Content"])


@router.post("/drafts", response_model=ContentDraftResponse, status_code=201)
def create_draft(
    payload: ContentDraftCreate,
    user: dict = Depends(RequirePermission("content:create")),
    service: ContentService = Depends(get_content_service),
):
    """Create a new content draft with initial version."""
    return service.create_draft(payload.model_dump())


@router.get("/drafts", response_model=list[ContentDraftResponse])
def list_drafts(
    project_id: UUID | None = None,
    status: str | None = None,
    content_type: str | None = None,
    user: dict = Depends(RequirePermission("content:read")),
    service: ContentService = Depends(get_content_service),
):
    """List content drafts with optional filters."""
    return service.list_drafts(
        project_id=project_id,
        status=status,
        content_type=content_type,
    )


@router.get("/drafts/{draft_id}")
def get_draft(
    draft_id: UUID,
    user: dict = Depends(RequirePermission("content:read")),
    service: ContentService = Depends(get_content_service),
):
    """Get a content draft by ID."""
    draft = service.get_draft(draft_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="Content draft not found")
    return draft


@router.patch("/drafts/{draft_id}/status")
def update_draft_status(
    draft_id: UUID,
    payload: ContentStatusUpdate,
    user: dict = Depends(RequirePermission("content:update_status")),
    service: ContentService = Depends(get_content_service),
):
    """Update a content draft's status."""
    return service.update_draft_status(draft_id, payload.status)


@router.post("/drafts/{draft_id}/versions", status_code=201)
def add_version(
    draft_id: UUID,
    payload: ContentVersionCreate,
    user: dict = Depends(RequirePermission("content:add_version")),
    service: ContentService = Depends(get_content_service),
):
    """Add a new version to a content draft."""
    return service.add_version(draft_id, payload.model_dump())


@router.get("/drafts/{draft_id}/versions")
def get_versions(
    draft_id: UUID,
    user: dict = Depends(RequirePermission("content:read")),
    service: ContentService = Depends(get_content_service),
):
    """Get all versions of a content draft."""
    return service.get_versions(draft_id)


@router.get("/drafts/{draft_id}/current")
def get_current_version(
    draft_id: UUID,
    user: dict = Depends(RequirePermission("content:read")),
    service: ContentService = Depends(get_content_service),
):
    """Get the current (latest) version of a content draft."""
    version = service.get_current_version(draft_id)
    if version is None:
        raise HTTPException(status_code=404, detail="No current version found")
    return version


@router.post("/drafts/{draft_id}/comments", status_code=201)
def add_comment(
    draft_id: UUID,
    payload: ContentCommentCreate,
    user: dict = Depends(RequirePermission("content:add_comment")),
    service: ContentService = Depends(get_content_service),
):
    """Add a comment to a content draft."""
    return service.add_comment(draft_id, payload.model_dump())
