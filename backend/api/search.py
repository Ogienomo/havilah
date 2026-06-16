"""
Havilah OS — Search API

Cross-entity search across Projects, Tasks, Approvals, Contacts, and Memory.
All endpoints require authentication.
"""

from fastapi import APIRouter, Depends

from backend.api.middleware import RequirePermission
from backend.repositories.search_repository import SearchRepository

router = APIRouter(prefix="/api/search", tags=["Search"])


@router.get("/")
def search_all(
    q: str,
    limit: int = 5,
    user: dict = Depends(RequirePermission("search:read")),
):
    """Cross-entity search across all domains."""
    repo = SearchRepository()
    return repo.search_all(query=q, limit_per_type=limit)


@router.get("/projects")
def search_projects(
    q: str,
    limit: int = 20,
    user: dict = Depends(RequirePermission("search:read")),
):
    """Search projects by title or objective."""
    return SearchRepository().search_projects(q, limit)


@router.get("/tasks")
def search_tasks(
    q: str,
    limit: int = 20,
    user: dict = Depends(RequirePermission("search:read")),
):
    """Search tasks by title or description."""
    return SearchRepository().search_tasks(q, limit)


@router.get("/approvals")
def search_approvals(
    q: str,
    limit: int = 20,
    user: dict = Depends(RequirePermission("search:read")),
):
    """Search approvals by summary or action type."""
    return SearchRepository().search_approvals(q, limit)


@router.get("/contacts")
def search_contacts(
    q: str,
    limit: int = 20,
    user: dict = Depends(RequirePermission("search:read")),
):
    """Search contacts by name, email, or phone."""
    return SearchRepository().search_contacts(q, limit)


@router.get("/memory")
def search_memory(
    q: str,
    limit: int = 20,
    user: dict = Depends(RequirePermission("search:read")),
):
    """Search memory by title or content."""
    return SearchRepository().search_memory(q, limit)
