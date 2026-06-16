"""
Havilah OS — Knowledge API

Knowledge is approved canonical truth (policies, SOPs, templates).
Artifact Lifecycle: draft -> review -> approved -> published -> deprecated -> archived
Approve and publish are HUMAN-ONLY — agents can NEVER approve knowledge.
All endpoints require authentication.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from backend.api.deps import get_knowledge_service
from backend.api.middleware import RequirePermission
from backend.schemas.schemas import (
    KnowledgeArtifactCreate,
    KnowledgeVersionCreate,
    KnowledgeVersionApprove,
    KnowledgeResponse,
)
from backend.services.knowledge_service import KnowledgeService

router = APIRouter(prefix="/api/knowledge", tags=["Knowledge"])


@router.post("/", response_model=KnowledgeResponse, status_code=201)
def create_artifact(
    payload: KnowledgeArtifactCreate,
    user: dict = Depends(RequirePermission("knowledge:create")),
    service: KnowledgeService = Depends(get_knowledge_service),
):
    """Create a new knowledge artifact. Agents can draft artifacts."""
    return service.create_artifact(payload.model_dump())


@router.get("/", response_model=list[KnowledgeResponse])
def list_artifacts(
    category: str | None = None,
    knowledge_type: str | None = None,
    status: str | None = None,
    user: dict = Depends(RequirePermission("knowledge:read")),
    service: KnowledgeService = Depends(get_knowledge_service),
):
    """List knowledge artifacts with optional filters."""
    return service.list_artifacts(
        category=category,
        knowledge_type=knowledge_type,
        status=status,
    )


@router.get("/{artifact_id}")
def get_artifact(
    artifact_id: UUID,
    user: dict = Depends(RequirePermission("knowledge:read")),
    service: KnowledgeService = Depends(get_knowledge_service),
):
    """Get a knowledge artifact by ID."""
    artifact = service.get_artifact(artifact_id)
    if artifact is None:
        raise HTTPException(status_code=404, detail="Knowledge artifact not found")
    return artifact


@router.post("/{artifact_id}/versions", status_code=201)
def add_version(
    artifact_id: UUID,
    payload: KnowledgeVersionCreate,
    user: dict = Depends(RequirePermission("knowledge:add_version")),
    service: KnowledgeService = Depends(get_knowledge_service),
):
    """Add a new version to a knowledge artifact."""
    return service.add_version(artifact_id, payload.model_dump())


@router.get("/{artifact_id}/versions")
def get_versions(
    artifact_id: UUID,
    user: dict = Depends(RequirePermission("knowledge:read")),
    service: KnowledgeService = Depends(get_knowledge_service),
):
    """Get all versions of a knowledge artifact."""
    return service.get_versions(artifact_id)


@router.post("/{artifact_id}/versions/{version_id}/approve")
def approve_version(
    artifact_id: UUID,
    version_id: UUID,
    payload: KnowledgeVersionApprove,
    user: dict = Depends(RequirePermission("knowledge:approve_version")),
    service: KnowledgeService = Depends(get_knowledge_service),
):
    """Approve a knowledge version. HUMANS ONLY — agents can NEVER approve knowledge.
    This ensures all canonical knowledge has human sign-off."""
    return service.approve_version(artifact_id, version_id, payload.approved_by)


@router.post("/{artifact_id}/publish")
def publish_artifact(
    artifact_id: UUID,
    user: dict = Depends(RequirePermission("knowledge:publish")),
    service: KnowledgeService = Depends(get_knowledge_service),
):
    """Publish an approved knowledge artifact. HUMANS ONLY."""
    return service.publish_artifact(artifact_id)


@router.post("/{artifact_id}/deprecate")
def deprecate_artifact(
    artifact_id: UUID,
    user: dict = Depends(RequirePermission("knowledge:deprecate")),
    service: KnowledgeService = Depends(get_knowledge_service),
):
    """Deprecate a published knowledge artifact."""
    return service.deprecate_artifact(artifact_id)
