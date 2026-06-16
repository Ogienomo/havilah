"""
Havilah OS — Approvals API

The governance backbone. NOTHING external bypasses the Approval Ledger.
7+2 state machine: draft -> proposed -> queued_for_review -> awaiting_approval
-> approved -> executing -> executed (with rejected/expired branches)

CRITICAL: approve, reject, escalate, and execute are HUMAN-ONLY.
AI agents can NEVER perform these actions — this is non-negotiable.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from backend.api.deps import get_approval_service, get_risk_service
from backend.api.middleware import RequirePermission
from backend.schemas.schemas import (
    ApprovalRequestCreate,
    ApprovalDecisionInput,
    ApprovalEscalateInput,
    ApprovalExecutionInput,
    ApprovalResponse,
)
from backend.services.approval_service import ApprovalService
from backend.services.risk_service import RiskService

router = APIRouter(prefix="/api/approvals", tags=["Approvals"])


@router.post("/", response_model=ApprovalResponse, status_code=201)
def request_approval(
    payload: ApprovalRequestCreate,
    user: dict = Depends(RequirePermission("approval:create")),
    service: ApprovalService = Depends(get_approval_service),
):
    """Submit a new approval request. Starts in 'draft' state.
    Both humans and agents can create approval requests."""
    return service.request_approval(payload.model_dump())


@router.get("/", response_model=list[ApprovalResponse])
def list_pending_approvals(
    user: dict = Depends(RequirePermission("approval:read")),
    service: ApprovalService = Depends(get_approval_service),
):
    """List all pending approval requests."""
    return service.repository.get_pending_approvals()


@router.get("/{approval_id}", response_model=ApprovalResponse)
def get_approval(
    approval_id: UUID,
    user: dict = Depends(RequirePermission("approval:read")),
    service: ApprovalService = Depends(get_approval_service),
):
    """Get an approval request by ID."""
    approval = service.repository.get_by_id(approval_id)
    if approval is None:
        raise HTTPException(status_code=404, detail="Approval request not found")
    return approval


@router.post("/{approval_id}/approve")
def approve_request(
    approval_id: UUID,
    payload: ApprovalDecisionInput,
    user: dict = Depends(RequirePermission("approval:approve")),
    service: ApprovalService = Depends(get_approval_service),
):
    """Approve a pending request. HUMANS ONLY — agents can NEVER approve.
    This is a core architectural principle: AI thinks, humans decide."""
    try:
        return service.approve_request(
            approval_id,
            reason=payload.reason,
            approver_id=payload.approver_id or user.get("id"),
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/{approval_id}/reject")
def reject_request(
    approval_id: UUID,
    payload: ApprovalDecisionInput,
    user: dict = Depends(RequirePermission("approval:reject")),
    service: ApprovalService = Depends(get_approval_service),
):
    """Reject a pending request. HUMANS ONLY — agents can NEVER reject."""
    try:
        return service.reject_request(
            approval_id,
            reason=payload.reason,
            decided_by=payload.approver_id or user.get("id"),
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/{approval_id}/escalate")
def escalate_request(
    approval_id: UUID,
    payload: ApprovalEscalateInput,
    user: dict = Depends(RequirePermission("approval:escalate")),
    service: ApprovalService = Depends(get_approval_service),
):
    """Escalate an approval to a higher authority. HUMANS ONLY."""
    return service.escalate_request(
        approval_id,
        escalated_to=payload.escalated_to,
        reason=payload.reason,
        decided_by=payload.decided_by or user.get("id"),
    )


@router.post("/{approval_id}/execute")
def execute_action(
    approval_id: UUID,
    payload: ApprovalExecutionInput,
    user: dict = Depends(RequirePermission("approval:execute")),
    service: ApprovalService = Depends(get_approval_service),
):
    """Execute an approved action. HUMANS ONLY — agents can NEVER execute.
    Only approved requests can be executed. This is the final gate."""
    try:
        return service.execute_action(approval_id, payload.result)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/{approval_id}/risk-assessment")
def calculate_risk(
    approval_id: UUID,
    action_type: str,
    channel: str,
    external_audience: bool = False,
    irreversible: bool = False,
    user: dict = Depends(RequirePermission("approval:assess_risk")),
    risk_service: RiskService = Depends(get_risk_service),
):
    """Calculate risk assessment for an approval request.
    Both humans and agents can assess risk."""
    return risk_service.calculate_risk(
        approval_id,
        action_type,
        channel,
        external_audience=external_audience,
        irreversible=irreversible,
    )


@router.get("/project/{project_id}")
def get_approvals_by_project(
    project_id: UUID,
    user: dict = Depends(RequirePermission("approval:read")),
    service: ApprovalService = Depends(get_approval_service),
):
    """Get all approvals linked to a project."""
    return service.repository.get_approvals_by_project(project_id)


@router.get("/task/{task_id}")
def get_approvals_by_task(
    task_id: UUID,
    user: dict = Depends(RequirePermission("approval:read")),
    service: ApprovalService = Depends(get_approval_service),
):
    """Get all approvals linked to a task."""
    return service.repository.get_approvals_by_task(task_id)
