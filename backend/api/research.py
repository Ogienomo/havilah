"""
Havilah OS — Research API

Research is a work process, not knowledge management.
Jobs produce sources, notes, and outputs.
All endpoints require authentication.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from backend.api.deps import get_research_service
from backend.api.middleware import RequirePermission
from backend.schemas.schemas import (
    ResearchJobCreate,
    ResearchSourceCreate,
    ResearchNoteCreate,
    ResearchOutputCreate,
    ResearchJobResponse,
)
from backend.services.research_service import ResearchService

router = APIRouter(prefix="/api/research", tags=["Research"])


@router.post("/jobs", response_model=ResearchJobResponse, status_code=201)
def create_job(
    payload: ResearchJobCreate,
    user: dict = Depends(RequirePermission("research:create")),
    service: ResearchService = Depends(get_research_service),
):
    """Create a new research job. Requires research:create permission."""
    return service.create_job(payload.model_dump())


@router.get("/jobs", response_model=list[ResearchJobResponse])
def list_jobs(
    project_id: UUID | None = None,
    status: str | None = None,
    user: dict = Depends(RequirePermission("research:read")),
    service: ResearchService = Depends(get_research_service),
):
    """List research jobs with optional filters."""
    return service.list_jobs(project_id=project_id, status=status)


@router.get("/jobs/{job_id}")
def get_job(
    job_id: UUID,
    user: dict = Depends(RequirePermission("research:read")),
    service: ResearchService = Depends(get_research_service),
):
    """Get a research job by ID."""
    job = service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Research job not found")
    return job


@router.patch("/jobs/{job_id}/status")
def update_job_status(
    job_id: UUID,
    status: str,
    user: dict = Depends(RequirePermission("research:update_status")),
    service: ResearchService = Depends(get_research_service),
):
    """Update a research job's status."""
    return service.update_job_status(job_id, status)


@router.post("/jobs/{job_id}/sources", status_code=201)
def add_source(
    job_id: UUID,
    payload: ResearchSourceCreate,
    user: dict = Depends(RequirePermission("research:add_source")),
    service: ResearchService = Depends(get_research_service),
):
    """Add a source to a research job."""
    return service.add_source(job_id, payload.model_dump())


@router.get("/jobs/{job_id}/sources")
def get_sources(
    job_id: UUID,
    user: dict = Depends(RequirePermission("research:read")),
    service: ResearchService = Depends(get_research_service),
):
    """Get all sources for a research job."""
    return service.get_sources(job_id)


@router.post("/jobs/{job_id}/notes", status_code=201)
def add_note(
    job_id: UUID,
    payload: ResearchNoteCreate,
    user: dict = Depends(RequirePermission("research:add_note")),
    service: ResearchService = Depends(get_research_service),
):
    """Add a note to a research job."""
    return service.add_note(job_id, payload.model_dump())


@router.get("/jobs/{job_id}/notes")
def get_notes(
    job_id: UUID,
    user: dict = Depends(RequirePermission("research:read")),
    service: ResearchService = Depends(get_research_service),
):
    """Get all notes for a research job."""
    return service.get_notes(job_id)


@router.post("/jobs/{job_id}/outputs", status_code=201)
def add_output(
    job_id: UUID,
    payload: ResearchOutputCreate,
    user: dict = Depends(RequirePermission("research:add_output")),
    service: ResearchService = Depends(get_research_service),
):
    """Add an output to a research job."""
    return service.add_output(job_id, payload.model_dump())


@router.get("/jobs/{job_id}/outputs")
def get_outputs(
    job_id: UUID,
    user: dict = Depends(RequirePermission("research:read")),
    service: ResearchService = Depends(get_research_service),
):
    """Get all outputs for a research job."""
    return service.get_outputs(job_id)
