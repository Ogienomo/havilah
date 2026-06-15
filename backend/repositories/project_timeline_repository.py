from sqlalchemy import text

from backend.database import SessionLocal


class ProjectTimelineRepository:

    def get_project_events(
        self,
        project_id
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
                        CAST(:project_id AS UUID)

                    ORDER BY created_at
                """),
                {
                    "project_id": project_id
                }
            )

            return [
                dict(row._mapping)
                for row in result
            ]

        finally:

            db.close()

    def get_project_approvals(
        self,
        project_id
    ):

        db = SessionLocal()

        try:

            result = db.execute(
                text("""
                    SELECT
                        id,
                        action_type
                    FROM approval_requests
                    WHERE project_id =
                        CAST(:project_id AS UUID)
                """),
                {
                    "project_id": project_id
                }
            )

            return [
                dict(row._mapping)
                for row in result
            ]

        finally:

            db.close()

    def get_approval_events(
        self,
        approval_id
    ):

        db = SessionLocal()

        try:

            result = db.execute(
                text("""
                    SELECT
                        event_type,
                        created_at
                    FROM domain_events
                    WHERE aggregate_id =
                        CAST(:approval_id AS UUID)

                    ORDER BY created_at
                """),
                {
                    "approval_id": approval_id
                }
            )

            return [
                dict(row._mapping)
                for row in result
            ]

        finally:

            db.close()
