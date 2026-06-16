"""
Havilah OS — Organizations API

Manage organizations, departments, and stakeholders.
All endpoints require authentication.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from backend.api.deps import get_organization_service
from backend.api.middleware import RequirePermission
from backend.schemas.schemas import (
    OrganizationCreate,
    OrganizationResponse,
    DepartmentCreate,
    DepartmentResponse,
)
from backend.services.organization_service import OrganizationService

router = APIRouter(prefix="/api/organizations", tags=["Organizations"])


@router.post("/", status_code=201)
def create_organization(
    payload: OrganizationCreate,
    user: dict = Depends(RequirePermission("organization:create")),
    service: OrganizationService = Depends(get_organization_service),
):
    """Create a new organization. Admin or operator only."""
    return service.create_organization(payload.model_dump())


@router.get("/{org_id}")
def get_organization(
    org_id: UUID,
    user: dict = Depends(RequirePermission("organization:read")),
    service: OrganizationService = Depends(get_organization_service),
):
    """Get an organization by ID."""
    org = service.get_organization(org_id)
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


@router.post("/{org_id}/departments", status_code=201)
def add_department(
    org_id: UUID,
    payload: DepartmentCreate,
    user: dict = Depends(RequirePermission("organization:add_department")),
    service: OrganizationService = Depends(get_organization_service),
):
    """Add a department to an organization."""
    return service.add_department(
        org_id,
        payload.name,
        department_type=payload.department_type,
        head_id=payload.head_id,
    )


@router.post("/{org_id}/stakeholders", status_code=201)
def add_stakeholder(
    org_id: UUID,
    stakeholder_type: str,
    contact_id: UUID | None = None,
    influence_level: str = "medium",
    interest_level: str = "medium",
    notes: str | None = None,
    user: dict = Depends(RequirePermission("organization:add_stakeholder")),
    service: OrganizationService = Depends(get_organization_service),
):
    """Add a stakeholder to an organization."""
    return service.add_stakeholder(
        org_id,
        stakeholder_type,
        contact_id=contact_id,
        influence_level=influence_level,
        interest_level=interest_level,
        notes=notes,
    )
