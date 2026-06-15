from sqlalchemy import text

from backend.database import SessionLocal


class BriefingRepository:

    # --------------------------------------------------
    # CONTACT BRIEFING
    # --------------------------------------------------

    def get_contact(
        self,
        contact_id
    ):

        db = SessionLocal()

        try:

            result = db.execute(
                text("""
                    SELECT
                        id,
                        first_name,
                        last_name,
                        relationship_type
                    FROM contacts
                    WHERE id = :contact_id
                """),
                {
                    "contact_id": contact_id
                }
            )

            row = result.fetchone()

            if row is None:
                return None

            return dict(
                row._mapping
            )

        finally:

            db.close()

    def get_contact_memories(
        self,
        contact_id
    ):

        db = SessionLocal()

        try:

            result = db.execute(
                text("""
                    SELECT
                        m.title,
                        m.content,
                        m.importance
                    FROM memory_items m

                    INNER JOIN memory_links ml
                        ON ml.memory_id = m.id

                    WHERE
                        ml.linked_entity_type = 'contact'
                        AND ml.linked_entity_id = :contact_id
                """),
                {
                    "contact_id": contact_id
                }
            )

            return [
                dict(row._mapping)
                for row in result.fetchall()
            ]

        finally:

            db.close()

    # --------------------------------------------------
    # APPROVAL BRIEFING
    # --------------------------------------------------

    def get_approval(
        self,
        approval_id
    ):

        db = SessionLocal()

        try:

            result = db.execute(
                text("""
                    SELECT
                        id,
                        action_type,
                        summary,
                        status,
                        current_state,
                        execution_status
                    FROM approval_requests
                    WHERE id = :approval_id
                """),
                {
                    "approval_id": approval_id
                }
            )

            row = result.fetchone()

            if row is None:
                return None

            return dict(
                row._mapping
            )

        finally:

            db.close()

    def get_approval_decisions(
        self,
        approval_id
    ):

        db = SessionLocal()

        try:

            result = db.execute(
                text("""
                    SELECT
                        decision_type,
                        decision_reason,
                        decided_at
                    FROM approval_decisions
                    WHERE approval_request_id = :approval_id
                    ORDER BY decided_at DESC
                """),
                {
                    "approval_id": approval_id
                }
            )

            return [
                dict(row._mapping)
                for row in result.fetchall()
            ]

        finally:

            db.close()

    def get_execution_record(
        self,
        approval_id
    ):

        db = SessionLocal()

        try:

            result = db.execute(
                text("""
                    SELECT
                        execution_status,
                        execution_result
                    FROM execution_records
                    WHERE approval_request_id = :approval_id
                    LIMIT 1
                """),
                {
                    "approval_id": approval_id
                }
            )

            row = result.fetchone()

            if row is None:
                return None

            return dict(
                row._mapping
            )

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
                    WHERE aggregate_id = CAST(:approval_id AS UUID)
                    ORDER BY created_at
                """),
                {
                    "approval_id": approval_id
                }
            )

            return [
                dict(row._mapping)
                for row in result.fetchall()
            ]

        finally:

            db.close()

    # --------------------------------------------------
    # EXECUTIVE BRIEFING
    # --------------------------------------------------

    def get_memory_summary(self):

        db = SessionLocal()

        try:

            result = db.execute(
                text("""
                    SELECT COUNT(*) AS total
                    FROM memory_items
                """)
            )

            return result.scalar()

        finally:

            db.close()

    def get_approval_summary(self):

        db = SessionLocal()

        try:

            result = db.execute(
                text("""
                    SELECT COUNT(*) AS total
                    FROM approval_requests
                """)
            )

            return result.scalar()

        finally:

            db.close()

    def get_execution_summary(self):

        db = SessionLocal()

        try:

            result = db.execute(
                text("""
                    SELECT COUNT(*) AS total
                    FROM execution_records
                """)
            )

            return result.scalar()

        finally:

            db.close()

    def get_recent_events(
        self,
        limit=10
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
                    ORDER BY created_at DESC
                    LIMIT :limit
                """),
                {
                    "limit": limit
                }
            )

            return [
                dict(row._mapping)
                for row in result.fetchall()
            ]

        finally:

            db.close()
