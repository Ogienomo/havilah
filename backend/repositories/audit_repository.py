"""
Havilah OS — Audit Engine v2

Cross-domain audit: Who changed what? When? Why?

Answers:
  - Who changed this approval status?
  - What events happened on this project?
  - When was this memory last updated?
  - Why was this action taken?
"""

from sqlalchemy import text
from backend.repositories.base import get_session


class AuditRepository:

    def get_entity_audit_trail(self, entity_type: str, entity_id: str, limit=100):
        """Full audit trail for any entity across all domain events."""
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT id, event_type, event_category, actor_type, actor_id,
                           payload, correlation_id, causation_id, created_at
                    FROM domain_events
                    WHERE aggregate_type = :entity_type
                      AND aggregate_id = CAST(:entity_id AS UUID)
                    ORDER BY created_at
                    LIMIT :limit
                """),
                {"entity_type": entity_type, "entity_id": str(entity_id), "limit": limit},
            )
            return [dict(row._mapping) for row in result]

    def get_actor_actions(self, actor_id: str, limit=100):
        """What did a specific actor (human/agent) do?"""
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT id, aggregate_type, aggregate_id, event_type, payload, created_at
                    FROM domain_events
                    WHERE actor_id = CAST(:actor_id AS UUID)
                    ORDER BY created_at DESC
                    LIMIT :limit
                """),
                {"actor_id": str(actor_id), "limit": limit},
            )
            return [dict(row._mapping) for row in result]

    def get_correlation_chain(self, correlation_id: str):
        """Follow a chain of related events (e.g., a full workflow execution)."""
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT id, aggregate_type, aggregate_id, event_type, actor_type,
                           payload, causation_id, created_at
                    FROM domain_events
                    WHERE correlation_id = CAST(:correlation_id AS UUID)
                    ORDER BY created_at
                """),
                {"correlation_id": str(correlation_id)},
            )
            return [dict(row._mapping) for row in result]

    def get_approval_audit(self, approval_id: str):
        """Full audit for an approval: events + decisions + execution."""
        with get_session() as db:
            events = db.execute(
                text("""
                    SELECT event_type, actor_type, old_status, new_status, note, created_at
                    FROM approval_events
                    WHERE approval_request_id = CAST(:approval_id AS UUID)
                    ORDER BY created_at
                """),
                {"approval_id": str(approval_id)},
            )
            decisions = db.execute(
                text("""
                    SELECT decision_type, decision_reason, decided_by, decided_at
                    FROM approval_decisions
                    WHERE approval_request_id = CAST(:approval_id AS UUID)
                    ORDER BY decided_at
                """),
                {"approval_id": str(approval_id)},
            )
            executions = db.execute(
                text("""
                    SELECT execution_status, result_payload, started_at, completed_at
                    FROM execution_records
                    WHERE approval_request_id = CAST(:approval_id AS UUID)
                    ORDER BY created_at
                """),
                {"approval_id": str(approval_id)},
            )
            return {
                "events": [dict(r._mapping) for r in events],
                "decisions": [dict(r._mapping) for r in decisions],
                "executions": [dict(r._mapping) for r in executions],
            }

    def get_recent_changes(self, limit=50, aggregate_type=None):
        """What changed recently across the system?"""
        with get_session() as db:
            if aggregate_type:
                result = db.execute(
                    text("""
                        SELECT aggregate_type, aggregate_id, event_type, actor_type, payload, created_at
                        FROM domain_events
                        WHERE aggregate_type = :aggregate_type
                        ORDER BY created_at DESC
                        LIMIT :limit
                    """),
                    {"aggregate_type": aggregate_type, "limit": limit},
                )
            else:
                result = db.execute(
                    text("""
                        SELECT aggregate_type, aggregate_id, event_type, actor_type, payload, created_at
                        FROM domain_events
                        ORDER BY created_at DESC
                        LIMIT :limit
                    """),
                    {"limit": limit},
                )
            return [dict(row._mapping) for row in result]
