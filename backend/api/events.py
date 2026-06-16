"""
Havilah OS — Domain Events API

Event sourcing: everything is an event.
Query events by aggregate, type, or recency.
All endpoints require authentication.
"""

from uuid import UUID

from fastapi import APIRouter, Depends

from backend.api.deps import get_audit_service
from backend.api.middleware import RequirePermission
from backend.services.audit_service import AuditService

router = APIRouter(prefix="/api/events", tags=["Events"])


@router.get("/recent")
def get_recent_events(
    limit: int = 50,
    aggregate_type: str | None = None,
    user: dict = Depends(RequirePermission("event:read")),
    service: AuditService = Depends(get_audit_service),
):
    """Get recent domain events."""
    return service.get_recent_changes(limit=limit, aggregate_type=aggregate_type)


@router.get("/aggregate/{aggregate_id}")
def get_aggregate_events(
    aggregate_id: UUID,
    limit: int = 100,
    user: dict = Depends(RequirePermission("event:read")),
    service: AuditService = Depends(get_audit_service),
):
    """Get all events for a specific aggregate."""
    return service.get_entity_audit_trail("any", str(aggregate_id), limit)


@router.get("/actor/{actor_id}")
def get_actor_actions(
    actor_id: str,
    limit: int = 100,
    user: dict = Depends(RequirePermission("event:read")),
    service: AuditService = Depends(get_audit_service),
):
    """Get all actions by a specific actor."""
    return service.get_actor_actions(actor_id, limit)


@router.get("/correlation/{correlation_id}")
def get_correlation_chain(
    correlation_id: str,
    user: dict = Depends(RequirePermission("event:read")),
    service: AuditService = Depends(get_audit_service),
):
    """Get all events in a correlation chain."""
    return service.get_correlation_chain(correlation_id)


@router.get("/approval/{approval_id}")
def get_approval_audit(
    approval_id: str,
    user: dict = Depends(RequirePermission("event:read")),
    service: AuditService = Depends(get_audit_service),
):
    """Get the full audit trail for an approval."""
    return service.get_approval_audit(approval_id)
