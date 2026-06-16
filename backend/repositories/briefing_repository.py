"""
Havilah OS — Briefing Repository (FIXED)

Fixes from original:
  1. SQL injection vulnerability: replaced f-string table names with SAFE_TABLE_NAMES allowlist
  2. Uses context manager instead of manual try/finally
"""

from sqlalchemy import text

from backend.repositories.base import get_session, SAFE_TABLE_NAMES


class BriefingRepository:

    # ── Contact Briefing ──────────────────────────────────────

    def get_contact(self, contact_id):
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT id, full_name, first_name, last_name, email, relationship_status, priority_level
                    FROM contacts
                    WHERE id = CAST(:contact_id AS UUID)
                """),
                {"contact_id": str(contact_id)},
            )
            row = result.fetchone()
            return dict(row._mapping) if row else None

    def get_contact_memories(self, contact_id):
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT m.title, m.content, m.importance, m.memory_type, m.confidence
                    FROM memory_items m
                    INNER JOIN memory_links ml ON ml.memory_id = m.id
                    WHERE ml.linked_entity_type = 'contact'
                      AND ml.linked_entity_id = CAST(:contact_id AS UUID)
                      AND m.status = 'active'
                    ORDER BY m.importance DESC, m.created_at DESC
                """),
                {"contact_id": str(contact_id)},
            )
            return [dict(row._mapping) for row in result.fetchall()]

    # ── Approval Briefing ─────────────────────────────────────

    def get_approval(self, approval_id):
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT id, action_type, intent_summary, status, current_state, execution_status, risk_level, confidence
                    FROM approval_requests
                    WHERE id = CAST(:approval_id AS UUID)
                """),
                {"approval_id": str(approval_id)},
            )
            row = result.fetchone()
            return dict(row._mapping) if row else None

    def get_approval_decisions(self, approval_id):
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT decision_type, decision_reason, decided_by, decided_at
                    FROM approval_decisions
                    WHERE approval_request_id = CAST(:approval_id AS UUID)
                    ORDER BY decided_at DESC
                """),
                {"approval_id": str(approval_id)},
            )
            return [dict(row._mapping) for row in result.fetchall()]

    def get_execution_record(self, approval_id):
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT execution_status, result_payload, started_at, completed_at
                    FROM execution_records
                    WHERE approval_request_id = CAST(:approval_id AS UUID)
                    ORDER BY created_at DESC
                    LIMIT 1
                """),
                {"approval_id": str(approval_id)},
            )
            row = result.fetchone()
            return dict(row._mapping) if row else None

    def get_approval_events(self, approval_id):
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT event_type, actor_type, old_status, new_status, note, created_at
                    FROM approval_events
                    WHERE approval_request_id = CAST(:approval_id AS UUID)
                    ORDER BY created_at
                """),
                {"approval_id": str(approval_id)},
            )
            return [dict(row._mapping) for row in result.fetchall()]

    # ── Executive Briefing (FIXED: no more f-string SQL injection) ──

    def _count_rows(self, table_name: str) -> int:
        """Safe count query — validates table name against allowlist."""
        if table_name not in SAFE_TABLE_NAMES:
            raise ValueError(f"Invalid table name: {table_name}")
        with get_session() as db:
            result = db.execute(text(f"SELECT COUNT(*) AS total FROM {table_name}"))
            return result.scalar()

    def _get_status_breakdown(self, table_name: str) -> list:
        """Safe status breakdown — validates table name against allowlist."""
        if table_name not in SAFE_TABLE_NAMES:
            raise ValueError(f"Invalid table name: {table_name}")
        with get_session() as db:
            result = db.execute(
                text(f"SELECT status, COUNT(*) AS count FROM {table_name} GROUP BY status ORDER BY count DESC")
            )
            return [dict(row._mapping) for row in result.fetchall()]

    def get_memory_summary(self) -> int:
        return self._count_rows("memory_items")

    def get_approval_summary(self) -> int:
        return self._count_rows("approval_requests")

    def get_execution_summary(self) -> int:
        return self._count_rows("execution_records")

    def get_project_summary(self) -> int:
        return self._count_rows("projects")

    def get_task_summary(self) -> int:
        return self._count_rows("tasks")

    def get_approval_status_breakdown(self) -> list:
        return self._get_status_breakdown("approval_requests")

    def get_task_status_breakdown(self) -> list:
        return self._get_status_breakdown("tasks")

    def get_project_status_breakdown(self) -> list:
        return self._get_status_breakdown("projects")

    def get_recent_events(self, limit=10):
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT event_type, aggregate_type, payload, created_at
                    FROM domain_events
                    ORDER BY created_at DESC
                    LIMIT :limit
                """),
                {"limit": limit},
            )
            return [dict(row._mapping) for row in result.fetchall()]
