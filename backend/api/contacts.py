"""
Havilah OS — Contacts API

CRM endpoints for contact management, interactions, and relationship tracking.
All endpoints require authentication.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from backend.api.deps import get_contact_service
from backend.api.middleware import RequirePermission
from backend.schemas.schemas import ContactCreate, ContactResponse
from backend.services.contact_service import ContactService
from backend.repositories.base import get_session
from backend.models.contact import Contact

router = APIRouter(prefix="/api/contacts", tags=["Contacts"])


@router.post("/", status_code=201)
def create_contact(
    payload: ContactCreate,
    user: dict = Depends(RequirePermission("contact:create")),
    service: ContactService = Depends(get_contact_service),
):
    """Create a new contact. Requires contact:create permission."""
    return service.create_contact(payload.model_dump())


@router.get("/", response_model=list[ContactResponse])
def list_contacts(
    user: dict = Depends(RequirePermission("contact:read")),
):
    """List all contacts."""
    with get_session() as db:
        contacts = db.query(Contact).order_by(Contact.created_at.desc()).all()
        return [
            {
                "id": c.id,
                "full_name": c.full_name,
                "email": c.email,
                "phone": c.phone,
                "organization_id": c.organization_id,
                "role": getattr(c, 'role', None),
                "status": c.status if hasattr(c, 'status') else (c.relationship_status if hasattr(c, 'relationship_status') else "active"),
                "notes": getattr(c, 'notes', None),
                "created_at": c.created_at,
            }
            for c in contacts
        ]


@router.get("/{contact_id}", response_model=ContactResponse)
def get_contact(
    contact_id: UUID,
    user: dict = Depends(RequirePermission("contact:read")),
    service: ContactService = Depends(get_contact_service),
):
    """Get a contact by ID."""
    contact = service.repository.get_by_id(contact_id)
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.post("/{contact_id}/interactions")
def record_interaction(
    contact_id: UUID,
    channel: str,
    interaction_type: str,
    summary: str,
    user: dict = Depends(RequirePermission("contact:add_interaction")),
    service: ContactService = Depends(get_contact_service),
):
    """Record an interaction with a contact."""
    return service.repository.record_interaction(
        contact_id, channel, interaction_type, summary,
    )


@router.post("/{contact_id}/preferences")
def add_preference(
    contact_id: UUID,
    category: str,
    key: str,
    value: str,
    source: str = "explicit",
    user: dict = Depends(RequirePermission("contact:update")),
    service: ContactService = Depends(get_contact_service),
):
    """Add a contact preference."""
    return service.repository.add_preference(contact_id, category, key, value, source)


@router.post("/{contact_id}/relationship-score")
def update_relationship_score(
    contact_id: UUID,
    score: float,
    score_type: str = "overall",
    trend: str = "stable",
    notes: str | None = None,
    user: dict = Depends(RequirePermission("contact:update")),
    service: ContactService = Depends(get_contact_service),
):
    """Update a contact's relationship score."""
    return service.repository.update_relationship_score(
        contact_id, score, score_type, trend, notes,
    )
