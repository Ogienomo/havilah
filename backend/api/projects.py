"""
Havilah OS — Projects API

Endpoints for project lifecycle management.
All endpoints require authentication. Write operations require operator+ role.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from backend.api.deps import get_project_service, get_project_health_service
from backend.api.middleware import RequirePermission
from backend.api.auth import require_auth
from backend.schemas.schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
)
from backend.services.project_service import ProjectService
from backend.services.project_health_service import ProjectHealthService

router = APIRouter(prefix="/api/projects", tags=["Projects"])


@router.post("/", response_model=ProjectResponse, status_code=201)
def create_project(
    payload: ProjectCreate,
    user: dict = Depends(RequirePermission("project:create")),
    service: ProjectService = Depends(get_project_service),
):
    """Create a new project. Requires project:create permission."""
    project = service.create_project(payload.model_dump())
    return project


@router.get("/", response_model=list[ProjectResponse])
def list_projects(
    status: str | None = None,
    user: dict = Depends(RequirePermission("project:read")),
    service: ProjectService = Depends(get_project_service),
):
    """List all projects, optionally filtered by status."""
    if status:
        return service.repository.get_projects_by_status(status)
    return service.repository.get_all()


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: UUID,
    user: dict = Depends(RequirePermission("project:read")),
    service: ProjectService = Depends(get_project_service),
):
    """Get a project by ID."""
    project = service.repository.get_by_id(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/{project_id}/status")
def change_project_status(
    project_id: UUID,
    payload: ProjectUpdate,
    user: dict = Depends(RequirePermission("project:update_status")),
    service: ProjectService = Depends(get_project_service),
):
    """Change project status. Requires project:update_status permission."""
    if payload.status:
        return service.change_status(project_id, payload.status)
    raise HTTPException(status_code=400, detail="No status provided")


@router.post("/{project_id}/approvals/{approval_id}")
def link_approval(
    project_id: UUID,
    approval_id: UUID,
    user: dict = Depends(RequirePermission("project:update")),
    service: ProjectService = Depends(get_project_service),
):
    """Link an approval request to a project."""
    return service.attach_approval(project_id, approval_id)


@router.get("/{project_id}/briefing")
def get_project_briefing(
    project_id: UUID,
    user: dict = Depends(RequirePermission("briefing:read")),
    service: ProjectService = Depends(get_project_service),
):
    """Generate a project briefing with approvals and events."""
    briefing = service.generate_project_briefing(project_id)
    if briefing.get("project") is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return briefing


@router.post("/{project_id}/recalculate-health")
def recalculate_project_health(
    project_id: UUID,
    user: dict = Depends(RequirePermission("project:recalculate_health")),
    health_service: ProjectHealthService = Depends(get_project_health_service),
):
    """Recalculate project health metrics. Requires operator+ role."""
    return health_service.recalculate(project_id)
