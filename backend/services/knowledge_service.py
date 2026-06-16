"""
Havilah OS — Knowledge Service

Knowledge ≠ Memory:
  - Knowledge is approved canonical truth (policies, SOPs, templates)
  - Memory is contextual recall (preferences, observations, history)

Artifact Lifecycle: draft → review → approved → published → deprecated → archived
"""

from backend.repositories.base import get_session
from backend.repositories.event_repository import EventRepository
from backend.models.knowledge import KnowledgeArtifact, KnowledgeVersion

from sqlalchemy import text


class KnowledgeService:

    def __init__(self):
        self.event_repository = EventRepository()

    def create_artifact(self, data: dict) -> dict:
        with get_session() as db:
            artifact = KnowledgeArtifact(
                title=data["title"],
                knowledge_type=data["knowledge_type"],
                category=data.get("category", "operations"),
                summary=data.get("summary"),
                owner_id=data.get("owner_id"),
            )
            db.add(artifact)
            db.flush()

            self.event_repository.save(
                aggregate_type="knowledge_artifact",
                aggregate_id=str(artifact.id),
                event_type="KnowledgeArtifactCreated",
                payload={"title": artifact.title, "knowledge_type": artifact.knowledge_type},
            )

            return {"id": str(artifact.id), "title": artifact.title, "status": artifact.status}

    def get_artifact(self, artifact_id) -> dict | None:
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT id, title, knowledge_type, category, summary, status, owner_id,
                           canonical_version_id
                    FROM knowledge_artifacts
                    WHERE id = CAST(:aid AS UUID)
                """),
                {"aid": str(artifact_id)},
            )
            row = result.mappings().first()
            if not row:
                return None
            return dict(row)

    def list_artifacts(self, category=None, knowledge_type=None, status=None, limit=50):
        with get_session() as db:
            conditions = []
            params = {"limit": limit}
            if category:
                conditions.append("category = :category")
                params["category"] = category
            if knowledge_type:
                conditions.append("knowledge_type = :ktype")
                params["ktype"] = knowledge_type
            if status:
                conditions.append("status = :status")
                params["status"] = status

            where = "WHERE " + " AND ".join(conditions) if conditions else ""
            result = db.execute(
                text(f"""
                    SELECT id, title, knowledge_type, category, status
                    FROM knowledge_artifacts {where}
                    ORDER BY updated_at DESC
                    LIMIT :limit
                """),
                params,
            )
            return [dict(row) for row in result.mappings().all()]

    def add_version(self, artifact_id, data: dict) -> dict:
        with get_session() as db:
            version = KnowledgeVersion(
                knowledge_artifact_id=artifact_id,
                version_label=data["version_label"],
                content=data["content"],
                change_note=data.get("change_note"),
                version_status=data.get("version_status", "draft"),
                created_by=data.get("created_by"),
            )
            db.add(version)
            db.flush()

            self.event_repository.save(
                aggregate_type="knowledge_artifact",
                aggregate_id=str(artifact_id),
                event_type="KnowledgeVersionCreated",
                payload={"version_id": str(version.id), "label": version.version_label},
            )

            return {"id": str(version.id), "version_label": version.version_label, "status": version.version_status}

    def approve_version(self, artifact_id, version_id, approved_by):
        with get_session() as db:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)

            db.execute(
                text("""
                    UPDATE knowledge_versions
                    SET version_status = 'approved', approved_by = CAST(:ab AS UUID), approved_at = :now, updated_at = :now
                    WHERE id = CAST(:vid AS UUID)
                """),
                {"vid": str(version_id), "ab": str(approved_by), "now": now},
            )
            # Set as canonical version
            db.execute(
                text("""
                    UPDATE knowledge_artifacts
                    SET canonical_version_id = CAST(:vid AS UUID), status = 'approved', updated_at = :now
                    WHERE id = CAST(:aid AS UUID)
                """),
                {"vid": str(version_id), "aid": str(artifact_id), "now": now},
            )

        self.event_repository.save(
            aggregate_type="knowledge_artifact",
            aggregate_id=str(artifact_id),
            event_type="KnowledgeVersionApproved",
            payload={"version_id": str(version_id), "approved_by": str(approved_by)},
        )

        return {"version_id": str(version_id), "status": "approved"}

    def publish_artifact(self, artifact_id):
        with get_session() as db:
            db.execute(
                text("""
                    UPDATE knowledge_artifacts SET status = 'published', updated_at = NOW()
                    WHERE id = CAST(:aid AS UUID)
                """),
                {"aid": str(artifact_id)},
            )

        self.event_repository.save(
            aggregate_type="knowledge_artifact",
            aggregate_id=str(artifact_id),
            event_type="KnowledgeArtifactPublished",
            payload={"artifact_id": str(artifact_id)},
        )

        return {"artifact_id": str(artifact_id), "status": "published"}

    def get_versions(self, artifact_id):
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT id, version_label, version_status, created_by, approved_by, approved_at
                    FROM knowledge_versions
                    WHERE knowledge_artifact_id = CAST(:aid AS UUID)
                    ORDER BY created_at DESC
                """),
                {"aid": str(artifact_id)},
            )
            return [dict(row) for row in result.mappings().all()]

    def deprecate_artifact(self, artifact_id):
        with get_session() as db:
            db.execute(
                text("""
                    UPDATE knowledge_artifacts SET status = 'deprecated', updated_at = NOW()
                    WHERE id = CAST(:aid AS UUID)
                """),
                {"aid": str(artifact_id)},
            )

        self.event_repository.save(
            aggregate_type="knowledge_artifact",
            aggregate_id=str(artifact_id),
            event_type="KnowledgeArtifactDeprecated",
            payload={"artifact_id": str(artifact_id)},
        )

        return {"artifact_id": str(artifact_id), "status": "deprecated"}
