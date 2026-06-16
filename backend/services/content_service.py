"""
Havilah OS — Content Service

ContentDraft → ContentVersion → ContentComment
Content is always drafted by AI, reviewed by humans, published with approval.
"""

from backend.repositories.base import get_session
from backend.repositories.event_repository import EventRepository
from backend.models.content import ContentDraft, ContentVersion, ContentComment

from sqlalchemy import text


class ContentService:

    def __init__(self):
        self.event_repository = EventRepository()

    def create_draft(self, data: dict) -> dict:
        with get_session() as db:
            draft = ContentDraft(
                title=data["title"],
                content_type=data.get("content_type", "article"),
                project_id=data.get("project_id"),
                created_by=data.get("created_by"),
                source_agent_run_id=data.get("source_agent_run_id"),
            )
            db.add(draft)
            db.flush()

            # Create initial version
            version = ContentVersion(
                content_draft_id=draft.id,
                version_number=1,
                content=data.get("content", ""),
                is_current=True,
                created_by=data.get("created_by"),
            )
            db.add(version)
            db.flush()

            self.event_repository.save(
                aggregate_type="content_draft",
                aggregate_id=str(draft.id),
                event_type="ContentDraftCreated",
                payload={"title": draft.title, "content_type": draft.content_type},
            )

            return {
                "id": str(draft.id),
                "title": draft.title,
                "status": draft.status,
                "version_id": str(version.id),
            }

    def get_draft(self, draft_id) -> dict | None:
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT id, title, content_type, project_id, status, created_by
                    FROM content_drafts
                    WHERE id = CAST(:did AS UUID)
                """),
                {"did": str(draft_id)},
            )
            row = result.mappings().first()
            if not row:
                return None
            return dict(row)

    def list_drafts(self, project_id=None, status=None, content_type=None, limit=50):
        with get_session() as db:
            conditions = []
            params = {"limit": limit}
            if project_id:
                conditions.append("project_id = CAST(:pid AS UUID)")
                params["pid"] = str(project_id)
            if status:
                conditions.append("status = :status")
                params["status"] = status
            if content_type:
                conditions.append("content_type = :ctype")
                params["ctype"] = content_type

            where = "WHERE " + " AND ".join(conditions) if conditions else ""
            result = db.execute(
                text(f"""
                    SELECT id, title, content_type, status, created_at
                    FROM content_drafts {where}
                    ORDER BY updated_at DESC
                    LIMIT :limit
                """),
                params,
            )
            return [dict(row) for row in result.mappings().all()]

    def add_version(self, draft_id, data: dict) -> dict:
        with get_session() as db:
            # Mark existing current version as non-current
            db.execute(
                text("""
                    UPDATE content_versions SET is_current = false, updated_at = NOW()
                    WHERE content_draft_id = CAST(:did AS UUID) AND is_current = true
                """),
                {"did": str(draft_id)},
            )

            # Get next version number
            result = db.execute(
                text("""
                    SELECT COALESCE(MAX(version_number), 0) + 1 AS next_version
                    FROM content_versions
                    WHERE content_draft_id = CAST(:did AS UUID)
                """),
                {"did": str(draft_id)},
            )
            next_version = result.scalar()

            version = ContentVersion(
                content_draft_id=draft_id,
                version_number=next_version,
                content=data["content"],
                is_current=True,
                created_by=data.get("created_by"),
            )
            db.add(version)
            db.flush()

            self.event_repository.save(
                aggregate_type="content_draft",
                aggregate_id=str(draft_id),
                event_type="ContentVersionAdded",
                payload={"version_id": str(version.id), "version_number": next_version},
            )

            return {"id": str(version.id), "version_number": next_version, "is_current": True}

    def get_versions(self, draft_id):
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT id, version_number, is_current, created_by, created_at
                    FROM content_versions
                    WHERE content_draft_id = CAST(:did AS UUID)
                    ORDER BY version_number
                """),
                {"did": str(draft_id)},
            )
            return [dict(row) for row in result.mappings().all()]

    def get_current_version(self, draft_id):
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT id, version_number, content, is_current
                    FROM content_versions
                    WHERE content_draft_id = CAST(:did AS UUID) AND is_current = true
                    ORDER BY version_number DESC
                    LIMIT 1
                """),
                {"did": str(draft_id)},
            )
            row = result.mappings().first()
            return dict(row) if row else None

    def add_comment(self, draft_id, data: dict) -> dict:
        with get_session() as db:
            comment = ContentComment(
                content_draft_id=draft_id,
                version_id=data.get("version_id"),
                comment_text=data["comment_text"],
                author_id=data.get("author_id"),
                resolved=data.get("resolved", False),
            )
            db.add(comment)
            db.flush()
            return {"id": str(comment.id), "comment_text": comment.comment_text, "resolved": comment.resolved}

    def update_draft_status(self, draft_id, status: str):
        with get_session() as db:
            db.execute(
                text("""
                    UPDATE content_drafts SET status = :status, updated_at = NOW()
                    WHERE id = CAST(:did AS UUID)
                """),
                {"did": str(draft_id), "status": status},
            )

        self.event_repository.save(
            aggregate_type="content_draft",
            aggregate_id=str(draft_id),
            event_type="ContentDraftStatusChanged",
            payload={"status": status},
        )

        return {"id": str(draft_id), "status": status}
