"""
Havilah OS — Tasks API

Endpoints for task management, status transitions, and approval linking.
All endpoints require authentication.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from backend.api.deps import get_task_service
from backend.api.middleware import RequirePermission
from backend.schemas.schemas import (
    TaskCreate,
    TaskStatusUpdate,
    TaskResponse,
)
from backend.services.task_service import TaskService

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


@router.post("/", response_model=TaskResponse, status_code=201)
def create_task(
    payload: TaskCreate,
    user: dict = Depends(RequirePermission("task:create")),
    service: TaskService = Depends(get_task_service),
):
    """Create a new task. Requires task:create permission."""
    return service.create_task(payload.model_dump())


@router.get("/", response_model=list[TaskResponse])
def list_tasks(
    status: str | None = None,
    project_id: UUID | None = None,
    user: dict = Depends(RequirePermission("task:read")),
    service: TaskService = Depends(get_task_service),
):
    """List tasks, optionally filtered by status or project."""
    if status:
        return service.repository.get_tasks_by_status(status)
    if project_id:
        return service.repository.get_tasks_by_project(project_id)
    return service.repository.get_tasks_by_status("active")


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: UUID,
    user: dict = Depends(RequirePermission("task:read")),
    service: TaskService = Depends(get_task_service),
):
    """Get a task by ID."""
    task = service.repository.get_by_id(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.patch("/{task_id}/status")
def change_task_status(
    task_id: UUID,
    payload: TaskStatusUpdate,
    user: dict = Depends(RequirePermission("task:update_status")),
    service: TaskService = Depends(get_task_service),
):
    """Change task status (e.g. active -> completed). Requires task:update_status."""
    return service.change_status(task_id, payload.status)


@router.post("/{task_id}/approvals/{approval_id}")
def link_approval(
    task_id: UUID,
    approval_id: UUID,
    user: dict = Depends(RequirePermission("task:update")),
    service: TaskService = Depends(get_task_service),
):
    """Link an approval request to a task."""
    return service.link_approval(task_id, approval_id)


@router.get("/{task_id}/approvals")
def get_task_approvals(
    task_id: UUID,
    user: dict = Depends(RequirePermission("approval:read")),
    service: TaskService = Depends(get_task_service),
):
    """Get all approvals linked to a task."""
    return service.repository.get_task_approvals(task_id)


@router.get("/{task_id}/events")
def get_task_events(
    task_id: UUID,
    user: dict = Depends(RequirePermission("event:read")),
    service: TaskService = Depends(get_task_service),
):
    """Get domain events for a task."""
    return service.repository.get_task_events(task_id)
