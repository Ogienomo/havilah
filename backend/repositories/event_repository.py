"""
Havilah OS — Event Repository (FIXED)

Fixes from original:
  1. Uses context manager
  2. Proper JSON serialization
"""

import json
from sqlalchemy import text
from backend.repositories.base import get_session


class EventRepository:

    def save(self, aggregate_type, aggregate_id, event_type, payload, **kwargs):
        with get_session() as db:
            db.execute(
                text("""
                    INSERT INTO domain_events (
                        aggregate_type, aggregate_id, event_type, event_category,
                        actor_type, actor_id, correlation_id, causation_id, payload
                    )
                    VALUES (
                        :aggregate_type, CAST(:aggregate_id AS UUID), :event_type,
                        :event_category, :actor_type, :actor_id,
                        :correlation_id, :causation_id, CAST(:payload AS JSONB)
                    )
                """),
                {
                    "aggregate_type": aggregate_type,
                    "aggregate_id": str(aggregate_id),
                    "event_type": event_type,
                    "event_category": kwargs.get("event_category", "domain"),
                    "actor_type": kwargs.get("actor_type", "system"),
                    "actor_id": kwargs.get("actor_id"),
                    "correlation_id": str(kwargs["correlation_id"]) if kwargs.get("correlation_id") else None,
                    "causation_id": str(kwargs["causation_id"]) if kwargs.get("causation_id") else None,
                    "payload": json.dumps(payload, default=str),
                },
            )

    def get_events_for_aggregate(self, aggregate_id, limit=100):
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT id, event_type, event_category, actor_type, payload, created_at
                    FROM domain_events
                    WHERE aggregate_id = CAST(:aggregate_id AS UUID)
                    ORDER BY created_at
                    LIMIT :limit
                """),
                {"aggregate_id": str(aggregate_id), "limit": limit},
            )
            return [dict(row._mapping) for row in result]

    def get_events_by_type(self, event_type, limit=100):
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT id, aggregate_type, aggregate_id, event_type, payload, created_at
                    FROM domain_events
                    WHERE event_type = :event_type
                    ORDER BY created_at DESC
                    LIMIT :limit
                """),
                {"event_type": event_type, "limit": limit},
            )
            return [dict(row._mapping) for row in result]

    def get_recent_events(self, limit=50, event_category=None):
        with get_session() as db:
            if event_category:
                result = db.execute(
                    text("""
                        SELECT id, aggregate_type, aggregate_id, event_type, event_category, payload, created_at
                        FROM domain_events
                        WHERE event_category = :event_category
                        ORDER BY created_at DESC
                        LIMIT :limit
                    """),
                    {"event_category": event_category, "limit": limit},
                )
            else:
                result = db.execute(
                    text("""
                        SELECT id, aggregate_type, aggregate_id, event_type, event_category, payload, created_at
                        FROM domain_events
                        ORDER BY created_at DESC
                        LIMIT :limit
                    """),
                    {"limit": limit},
                )
            return [dict(row._mapping) for row in result]
