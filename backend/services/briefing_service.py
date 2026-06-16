"""
Havilah OS — Briefing Service (FIXED)

Fixed: SQL injection in _count_rows and _get_status_breakdown
by using SAFE_TABLE_NAMES allowlist.
"""

from sqlalchemy import text

from backend.repositories.base import get_session, SAFE_TABLE_NAMES
from backend.repositories.briefing_repository import BriefingRepository
from backend.repositories.event_repository import EventRepository
from backend.events import (
    CONTACT_BRIEFING_GENERATED,
    APPROVAL_BRIEFING_GENERATED,
)


class BriefingService:

    def __init__(self):
        self.repository = BriefingRepository()
        self.event_repository = EventRepository()

    def _count_rows(self, table_name: str):
        if table_name not in SAFE_TABLE_NAMES:
            raise ValueError(f"Invalid table name: {table_name}")
        with get_session() as db:
            result = db.execute(text(f"SELECT COUNT(*) AS total FROM {table_name}"))
            row = result.mappings().first()
            return int(row["total"]) if row else 0

    def _get_status_breakdown(self, table_name: str):
        if table_name not in SAFE_TABLE_NAMES:
            raise ValueError(f"Invalid table name: {table_name}")
        with get_session() as db:
            result = db.execute(
                text(f"SELECT status, COUNT(*) AS total FROM {table_name} GROUP BY status ORDER BY status")
            )
            return [dict(row._mapping) for row in result]

    def _get_recent_events(self, limit=10):
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT aggregate_type, aggregate_id, event_type, payload, created_at
                    FROM domain_events
                    ORDER BY created_at DESC
                    LIMIT :limit
                """),
                {"limit": limit},
            )
            return [dict(row._mapping) for row in result]

    # ── CONTACT BRIEFING ──────────────────────────────────────

    def generate_contact_briefing(self, contact_id):
        contact = self.repository.get_contact(contact_id)
        if contact is None:
            raise ValueError("Contact not found")

        memories = self.repository.get_contact_memories(contact_id)

        self.event_repository.save(
            aggregate_type="contact",
            aggregate_id=contact_id,
            event_type=CONTACT_BRIEFING_GENERATED,
            payload={"contact_id": contact_id},
        )

        return {"contact": contact, "memories": memories}

    # ── APPROVAL BRIEFING ─────────────────────────────────────

    def generate_approval_briefing(self, approval_id):
        approval = self.repository.get_approval(approval_id)
        if approval is None:
            raise ValueError("Approval not found")

        decisions = self.repository.get_approval_decisions(approval_id)
        execution = self.repository.get_execution_record(approval_id)
        events = self.repository.get_approval_events(approval_id)

        self.event_repository.save(
            aggregate_type="approval_request",
            aggregate_id=approval_id,
            event_type=APPROVAL_BRIEFING_GENERATED,
            payload={"approval_id": approval_id},
        )

        return {
            "approval": approval,
            "decisions": decisions,
            "execution": execution,
            "events": events,
        }

    # ── EXECUTIVE BRIEFING ────────────────────────────────────

    def generate_executive_briefing(self):
        return {
            "memory_count": self._count_rows("memory_items"),
            "project_count": self._count_rows("projects"),
            "task_count": self._count_rows("tasks"),
            "approval_count": self._count_rows("approval_requests"),
            "execution_count": self._count_rows("execution_records"),
            "project_status_breakdown": self._get_status_breakdown("projects"),
            "task_status_breakdown": self._get_status_breakdown("tasks"),
            "recent_events": self._get_recent_events(10),
        }
