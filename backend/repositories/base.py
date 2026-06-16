"""
Havilah OS — Base Repository

Provides the get_session context manager that ALL repositories use.
Eliminates the manual try/finally db.close() anti-pattern.
"""

from contextlib import contextmanager
from typing import Generator

from backend.database import SessionLocal


@contextmanager
def get_session() -> Generator:
    """Context manager for database sessions. Auto-commits on success, auto-rolls-back on exception."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# Allowed table names for safe dynamic SQL (fixes SQL injection vulnerability)
SAFE_TABLE_NAMES = frozenset({
    "approval_requests",
    "approval_decisions",
    "approval_events",
    "approval_policies",
    "execution_records",
    "contacts",
    "contact_preferences",
    "interactions",
    "communication_history",
    "relationship_scores",
    "projects",
    "milestones",
    "deliverables",
    "project_links",
    "tasks",
    "task_dependencies",
    "memory_items",
    "memory_sources",
    "memory_events",
    "memory_links",
    "knowledge_artifacts",
    "knowledge_versions",
    "research_jobs",
    "research_sources",
    "research_notes",
    "research_outputs",
    "content_drafts",
    "content_versions",
    "content_comments",
    "meetings",
    "agenda_items",
    "meeting_decisions",
    "meeting_action_items",
    "workflows",
    "workflow_steps",
    "workflow_transitions",
    "agents",
    "agent_runs",
    "agent_results",
    "notifications",
    "notification_deliveries",
    "domain_events",
    "risk_assessments",
    "organizations",
    "departments",
    "stakeholders",
    "users",
    "roles",
    "permissions",
    "user_roles",
    "role_permissions",
    "whatsapp_sessions",
    "whatsapp_messages",
    "whatsapp_templates",
    "whatsapp_approval_votes",
})
