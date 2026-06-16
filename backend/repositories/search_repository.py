"""
Havilah OS — Search Repository

Cross-entity search for: Projects, Tasks, Approvals, Contacts, Memory.
"""

from sqlalchemy import text
from backend.repositories.base import get_session


class SearchRepository:

    def search_projects(self, query: str, limit=20):
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT id, title, status, priority, created_at
                    FROM projects
                    WHERE title ILIKE :q OR objective ILIKE :q
                    ORDER BY updated_at DESC
                    LIMIT :limit
                """),
                {"q": f"%{query}%", "limit": limit},
            )
            return [dict(row._mapping) for row in result]

    def search_tasks(self, query: str, limit=20):
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT id, title, status, priority, project_id, created_at
                    FROM tasks
                    WHERE title ILIKE :q OR description ILIKE :q
                    ORDER BY updated_at DESC
                    LIMIT :limit
                """),
                {"q": f"%{query}%", "limit": limit},
            )
            return [dict(row._mapping) for row in result]

    def search_approvals(self, query: str, limit=20):
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT id, action_type, status, risk_level, created_at
                    FROM approval_requests
                    WHERE intent_summary ILIKE :q OR action_type ILIKE :q
                    ORDER BY created_at DESC
                    LIMIT :limit
                """),
                {"q": f"%{query}%", "limit": limit},
            )
            return [dict(row._mapping) for row in result]

    def search_contacts(self, query: str, limit=20):
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT id, full_name, email, relationship_status, priority_level
                    FROM contacts
                    WHERE full_name ILIKE :q OR email ILIKE :q OR phone ILIKE :q
                    ORDER BY priority_level DESC
                    LIMIT :limit
                """),
                {"q": f"%{query}%", "limit": limit},
            )
            return [dict(row._mapping) for row in result]

    def search_memory(self, query: str, limit=20):
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT id, title, content, memory_type, importance, confidence
                    FROM memory_items
                    WHERE (title ILIKE :q OR content ILIKE :q) AND status = 'active'
                    ORDER BY importance DESC, confidence DESC
                    LIMIT :limit
                """),
                {"q": f"%{query}%", "limit": limit},
            )
            return [dict(row._mapping) for row in result]

    def search_all(self, query: str, limit_per_type=5):
        """Cross-entity search returning results from all domains."""
        return {
            "projects": self.search_projects(query, limit_per_type),
            "tasks": self.search_tasks(query, limit_per_type),
            "approvals": self.search_approvals(query, limit_per_type),
            "contacts": self.search_contacts(query, limit_per_type),
            "memory": self.search_memory(query, limit_per_type),
        }
