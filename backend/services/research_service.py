"""
Havilah OS — Research Service

Research ≠ Knowledge Management — research is a work process.
Jobs produce sources, notes, and outputs.
"""

from backend.repositories.base import get_session
from backend.repositories.event_repository import EventRepository
from backend.models.research import ResearchJob, ResearchSource, ResearchNote, ResearchOutput

from sqlalchemy import text


class ResearchService:

    def __init__(self):
        self.event_repository = EventRepository()

    def create_job(self, data: dict) -> dict:
        with get_session() as db:
            job = ResearchJob(
                project_id=data.get("project_id"),
                title=data["title"],
                research_question=data["research_question"],
                priority=data.get("priority", "medium"),
                owner_id=data.get("owner_id"),
            )
            db.add(job)
            db.flush()

            self.event_repository.save(
                aggregate_type="research_job",
                aggregate_id=str(job.id),
                event_type="ResearchJobCreated",
                payload={"title": job.title, "priority": job.priority},
            )

            return {"id": str(job.id), "title": job.title, "status": job.status}

    def get_job(self, job_id) -> dict | None:
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT id, project_id, title, research_question, status, priority,
                           owner_id, summary, confidence
                    FROM research_jobs
                    WHERE id = CAST(:jid AS UUID)
                """),
                {"jid": str(job_id)},
            )
            row = result.mappings().first()
            if not row:
                return None
            return dict(row)

    def list_jobs(self, project_id=None, status=None, limit=50):
        with get_session() as db:
            conditions = []
            params = {"limit": limit}
            if project_id:
                conditions.append("project_id = CAST(:pid AS UUID)")
                params["pid"] = str(project_id)
            if status:
                conditions.append("status = :status")
                params["status"] = status

            where = "WHERE " + " AND ".join(conditions) if conditions else ""
            result = db.execute(
                text(f"""
                    SELECT id, title, research_question, status, priority
                    FROM research_jobs {where}
                    ORDER BY priority DESC, created_at DESC
                    LIMIT :limit
                """),
                params,
            )
            return [dict(row) for row in result.mappings().all()]

    def update_job_status(self, job_id, status: str):
        with get_session() as db:
            db.execute(
                text("""
                    UPDATE research_jobs SET status = :status, updated_at = NOW()
                    WHERE id = CAST(:jid AS UUID)
                """),
                {"jid": str(job_id), "status": status},
            )

        self.event_repository.save(
            aggregate_type="research_job",
            aggregate_id=str(job_id),
            event_type="ResearchJobStatusChanged",
            payload={"status": status},
        )

        return {"id": str(job_id), "status": status}

    def add_source(self, job_id, data: dict) -> dict:
        with get_session() as db:
            source = ResearchSource(
                research_job_id=job_id,
                source_title=data["source_title"],
                source_type=data["source_type"],
                source_reference=data.get("source_reference"),
                source_url=data.get("source_url"),
                source_summary=data.get("source_summary"),
                reliability_score=data.get("reliability_score"),
            )
            db.add(source)
            db.flush()
            return {"id": str(source.id), "source_title": source.source_title, "source_type": source.source_type}

    def add_note(self, job_id, data: dict) -> dict:
        with get_session() as db:
            note = ResearchNote(
                research_job_id=job_id,
                source_id=data.get("source_id"),
                note_text=data["note_text"],
                note_type=data.get("note_type", "observation"),
            )
            db.add(note)
            db.flush()
            return {"id": str(note.id), "note_type": note.note_type}

    def add_output(self, job_id, data: dict) -> dict:
        with get_session() as db:
            output = ResearchOutput(
                research_job_id=job_id,
                output_type=data["output_type"],
                title=data["title"],
                content=data["content"],
                confidence=data.get("confidence"),
                status=data.get("status", "draft"),
            )
            db.add(output)
            db.flush()

            self.event_repository.save(
                aggregate_type="research_job",
                aggregate_id=str(job_id),
                event_type="ResearchOutputCreated",
                payload={"output_id": str(output.id), "output_type": output.output_type},
            )

            return {"id": str(output.id), "title": output.title, "output_type": output.output_type}

    def get_sources(self, job_id):
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT id, source_title, source_type, source_url, reliability_score
                    FROM research_sources
                    WHERE research_job_id = CAST(:jid AS UUID)
                    ORDER BY created_at
                """),
                {"jid": str(job_id)},
            )
            return [dict(row) for row in result.mappings().all()]

    def get_notes(self, job_id):
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT id, note_text, note_type, source_id
                    FROM research_notes
                    WHERE research_job_id = CAST(:jid AS UUID)
                    ORDER BY created_at
                """),
                {"jid": str(job_id)},
            )
            return [dict(row) for row in result.mappings().all()]

    def get_outputs(self, job_id):
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT id, output_type, title, confidence, status
                    FROM research_outputs
                    WHERE research_job_id = CAST(:jid AS UUID)
                    ORDER BY created_at
                """),
                {"jid": str(job_id)},
            )
            return [dict(row) for row in result.mappings().all()]
