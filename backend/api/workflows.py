"""
Havilah OS — Workflows API

Orchestrate multi-step business processes.
Workflows: sequential, parallel, conditional.
All endpoints require authentication.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from backend.api.deps import get_workflow_service
from backend.api.middleware import RequirePermission
from backend.schemas.schemas import (
    WorkflowCreate,
    WorkflowStepCreate,
    WorkflowTransitionCreate,
    WorkflowResponse,
)
from backend.services.workflow_service import WorkflowService

router = APIRouter(prefix="/api/workflows", tags=["Workflows"])


@router.post("/", response_model=WorkflowResponse, status_code=201)
def create_workflow(
    payload: WorkflowCreate,
    user: dict = Depends(RequirePermission("workflow:create")),
    service: WorkflowService = Depends(get_workflow_service),
):
    """Create a new workflow. Requires workflow:create permission."""
    return service.create_workflow(payload.model_dump())


@router.get("/{workflow_id}")
def get_workflow(
    workflow_id: UUID,
    user: dict = Depends(RequirePermission("workflow:read")),
    service: WorkflowService = Depends(get_workflow_service),
):
    """Get a workflow with its steps."""
    result = service.get_workflow(workflow_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return result


@router.post("/{workflow_id}/start")
def start_workflow(
    workflow_id: UUID,
    user: dict = Depends(RequirePermission("workflow:start")),
    service: WorkflowService = Depends(get_workflow_service),
):
    """Start a draft workflow. Requires workflow:start permission."""
    try:
        return service.start_workflow(workflow_id)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/{workflow_id}/steps")
def add_step(
    workflow_id: UUID,
    payload: WorkflowStepCreate,
    user: dict = Depends(RequirePermission("workflow:add_step")),
    service: WorkflowService = Depends(get_workflow_service),
):
    """Add a step to a workflow. Requires workflow:add_step permission."""
    return service.add_step(
        workflow_id,
        payload.title,
        payload.step_order,
        step_type=payload.step_type,
        requires_approval=payload.requires_approval,
        task_template=payload.task_template,
    )


@router.post("/{workflow_id}/transitions")
def add_transition(
    workflow_id: UUID,
    payload: WorkflowTransitionCreate,
    user: dict = Depends(RequirePermission("workflow:add_transition")),
    service: WorkflowService = Depends(get_workflow_service),
):
    """Add a transition between workflow steps."""
    return service.add_transition(
        workflow_id,
        payload.from_step_id,
        payload.to_step_id,
        transition_type=payload.transition_type,
        condition=payload.condition,
    )


@router.post("/{workflow_id}/steps/{step_id}/complete")
def complete_step(
    workflow_id: UUID,
    step_id: UUID,
    user: dict = Depends(RequirePermission("workflow:advance_step")),
    service: WorkflowService = Depends(get_workflow_service),
):
    """Complete a workflow step and advance to the next."""
    try:
        return service.complete_step(workflow_id, step_id)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
