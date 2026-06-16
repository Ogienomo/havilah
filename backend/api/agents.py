"""
Havilah OS — Agents API

No agent can approve external execution — ever.
Agents think, draft, recommend, prepare. Humans decide.
All endpoints require authentication.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from backend.api.deps import get_agent_service
from backend.api.middleware import RequirePermission
from backend.schemas.schemas import (
    AgentRegister,
    AgentRunCreate,
    AgentRunComplete,
    AgentRunFail,
    AgentResponse,
)
from backend.services.agent_service import AgentService

router = APIRouter(prefix="/api/agents", tags=["Agents"])


@router.post("/", response_model=AgentResponse, status_code=201)
def register_agent(
    payload: AgentRegister,
    user: dict = Depends(RequirePermission("agent:register")),
    service: AgentService = Depends(get_agent_service),
):
    """Register a new AI agent. Admin only."""
    return service.register_agent(payload.model_dump())


@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(
    agent_id: UUID,
    user: dict = Depends(RequirePermission("agent:read")),
    service: AgentService = Depends(get_agent_service),
):
    """Get an agent by ID."""
    agent = service.get_agent(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.get("/name/{name}", response_model=AgentResponse)
def get_agent_by_name(
    name: str,
    user: dict = Depends(RequirePermission("agent:read")),
    service: AgentService = Depends(get_agent_service),
):
    """Get an agent by name (e.g. 'planner', 'executive')."""
    agent = service.get_agent_by_name(name)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.post("/runs", status_code=201)
def create_agent_run(
    payload: AgentRunCreate,
    user: dict = Depends(RequirePermission("agent:run")),
    service: AgentService = Depends(get_agent_service),
):
    """Assign a new agent run. Requires agent:run permission."""
    return service.assign_run(
        payload.agent_id,
        payload.input_context,
        task_id=payload.task_id,
        approval_id=payload.approval_id,
        workflow_step_id=payload.workflow_step_id,
        configuration=payload.configuration,
    )


@router.post("/runs/{run_id}/start")
def start_agent_run(
    run_id: UUID,
    agent_id: UUID,
    user: dict = Depends(RequirePermission("agent:run")),
    service: AgentService = Depends(get_agent_service),
):
    """Start an assigned agent run."""
    return service.start_run(run_id, agent_id)


@router.post("/runs/{run_id}/complete")
def complete_agent_run(
    run_id: UUID,
    agent_id: UUID,
    payload: AgentRunComplete,
    user: dict = Depends(RequirePermission("agent:complete_run")),
    service: AgentService = Depends(get_agent_service),
):
    """Complete an agent run with results."""
    return service.complete_run(
        run_id,
        agent_id,
        payload.results,
        duration_ms=payload.duration_ms,
        token_usage=payload.token_usage,
    )


@router.post("/runs/{run_id}/fail")
def fail_agent_run(
    run_id: UUID,
    agent_id: UUID,
    payload: AgentRunFail,
    user: dict = Depends(RequirePermission("agent:fail_run")),
    service: AgentService = Depends(get_agent_service),
):
    """Mark an agent run as failed."""
    return service.fail_run(
        run_id,
        agent_id,
        payload.error_message,
        duration_ms=payload.duration_ms,
    )


@router.get("/runs/{run_id}/results")
def get_run_results(
    run_id: UUID,
    user: dict = Depends(RequirePermission("agent:read")),
    service: AgentService = Depends(get_agent_service),
):
    """Get all results from an agent run."""
    return service.get_run_results(run_id)
