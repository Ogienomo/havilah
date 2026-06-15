from sqlalchemy import text

from backend.database import SessionLocal


class TimelineRepository:

    EXCLUDED_EVENTS = [
        "ContactBriefingGenerated",
        "ApprovalBriefingGenerated",
        "ExecutiveBriefingGenerated",
        "ApprovalTimelineGenerated",
        "ContactTimelineGenerated",
        "TimelineGenerated"
    ]

    # ----------------------------------
    # FULL AUDIT TIMELINE
    # ----------------------------------

    def get_events_for_aggregate(
        self,
        aggregate_id
    ):

        db = SessionLocal()

        try:

            result = db.execute(
                text("""
                    SELECT
                        event_type,
                        payload,
                        created_at
                    FROM domain_events
                    WHERE aggregate_id =
                        CAST(:aggregate_id AS UUID)
                    ORDER BY created_at
                """),
                {
                    "aggregate_id": aggregate_id
                }
            )

            return [
                dict(row._mapping)
                for row in result
            ]

        finally:

            db.close()

    # ----------------------------------
    # BUSINESS TIMELINE
    # ----------------------------------

    def get_business_events_for_aggregate(
        self,
        aggregate_id
    ):

        db = SessionLocal()

        try:

            result = db.execute(
                text("""
                    SELECT
                        event_type,
                        payload,
                        created_at
                    FROM domain_events
                    WHERE aggregate_id =
                        CAST(:aggregate_id AS UUID)

                    AND event_type NOT IN (
                        'ContactBriefingGenerated',
                        'ApprovalBriefingGenerated',
                        'ExecutiveBriefingGenerated',
                        'ApprovalTimelineGenerated',
                        'ContactTimelineGenerated',
                        'TimelineGenerated'
                    )

                    ORDER BY created_at
                """),
                {
                    "aggregate_id": aggregate_id
                }
            )

            return [
                dict(row._mapping)
                for row in result
            ]

        finally:

            db.close()
