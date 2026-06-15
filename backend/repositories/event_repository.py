import json

from backend.database import SessionLocal

from sqlalchemy import text


class EventRepository:

    def save(
        self,
        aggregate_type,
        aggregate_id,
        event_type,
        payload
    ):

        db = SessionLocal()

        try:

            db.execute(
                text("""
                    INSERT INTO domain_events (
                        aggregate_type,
                        aggregate_id,
                        event_type,
                        payload
                    )
                    VALUES (
                        :aggregate_type,
                        :aggregate_id,
                        :event_type,
                        CAST(:payload AS JSONB)
                    )
                """),
                {
                    "aggregate_type": aggregate_type,
                    "aggregate_id": str(aggregate_id),
                    "event_type": event_type,
                    "payload": json.dumps(payload)
                }
            )

            db.commit()

        finally:
            db.close()
