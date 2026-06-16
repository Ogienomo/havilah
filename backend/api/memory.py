"""
Havilah OS — Memory API

Structured memory system: Long-term, Working, Semantic, Procedural,
Project, Client, Business, Conversation Memory.
All endpoints require authentication.
"""

from uuid import UUID

from fastapi import APIRouter, Depends

from backend.api.deps import get_memory_service
from backend.api.middleware import RequirePermission
from backend.schemas.schemas import (
    MemoryCapture,
    MemoryLinkInput,
    MemoryReinforceInput,
    MemorySearchInput,
    MemoryResponse,
)
from backend.services.memory_service import MemoryService

router = APIRouter(prefix="/api/memory", tags=["Memory"])


@router.post("/capture", status_code=201)
def capture_memory(
    payload: MemoryCapture,
    user: dict = Depends(RequirePermission("memory:capture")),
    service: MemoryService = Depends(get_memory_service),
):
    """Capture a new memory item. Requires memory:capture permission."""
    memory = service.capture_memory(payload)
    return {
        "id": str(memory.id),
        "memory_type": memory.memory_type,
        "title": memory.title,
        "importance": float(memory.importance) if memory.importance else None,
        "confidence": float(memory.confidence) if memory.confidence else None,
        "status": memory.status,
        "created_at": memory.created_at.isoformat() if memory.created_at else None,
    }


@router.post("/search")
def search_memory(
    payload: MemorySearchInput,
    user: dict = Depends(RequirePermission("memory:search")),
    service: MemoryService = Depends(get_memory_service),
):
    """Search memories by text (ILIKE on title + content)."""
    results = service.recall_memory(payload.search_text)
    return [
        {
            "id": str(m.id),
            "memory_type": m.memory_type,
            "title": m.title,
            "content": m.content,
            "importance": float(m.importance) if m.importance else None,
            "confidence": float(m.confidence) if m.confidence else None,
            "status": m.status,
        }
        for m in results
    ]


@router.post("/link")
def link_memory(
    payload: MemoryLinkInput,
    user: dict = Depends(RequirePermission("memory:link")),
    service: MemoryService = Depends(get_memory_service),
):
    """Link a memory to an entity (contact, project, task, etc.)."""
    return service.link_memory(
        memory_id=payload.entity_id,
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        relationship_type=payload.relationship_type,
    )


@router.post("/reinforce")
def reinforce_memory(
    payload: MemoryReinforceInput,
    user: dict = Depends(RequirePermission("memory:reinforce")),
    service: MemoryService = Depends(get_memory_service),
):
    """Reinforce a memory — increases confidence and reinforcement count."""
    return service.reinforce_memory(payload.memory_id)


@router.get("/type/{memory_type}")
def get_memories_by_type(
    memory_type: str,
    user: dict = Depends(RequirePermission("memory:read")),
    service: MemoryService = Depends(get_memory_service),
):
    """Get all active memories of a specific type."""
    results = service.memory_repository.find_by_type(memory_type)
    return [
        {
            "id": str(m.id),
            "memory_type": m.memory_type,
            "title": m.title,
            "importance": float(m.importance) if m.importance else None,
            "status": m.status,
        }
        for m in results
    ]


@router.get("/entity/{entity_type}/{entity_id}")
def get_memories_by_entity(
    entity_type: str,
    entity_id: UUID,
    user: dict = Depends(RequirePermission("memory:read")),
    service: MemoryService = Depends(get_memory_service),
):
    """Get all memories linked to a specific entity."""
    return service.memory_repository.find_by_entity(entity_type, str(entity_id))
