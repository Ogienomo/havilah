"""
Havilah OS — Project Health Service

Recalculates project health based on task completion rates,
milestone progress, and approval pipeline status.
"""

from datetime import datetime, timezone

from sqlalchemy import text

from backend.repositories.base import get_session
from backend.repositories.project_repository import ProjectRepository
from backend.repositories.event_repository import EventRepository


class ProjectHealthService:

    def __init__(self):
        self.repository = ProjectRepository()
        self.event_repository = EventRepository()

    def recalculate(self, project_id):
        """Recalculate project health metrics and update status if needed."""
        with get_session() as db:
            # ── Task completion ratio ────────────────────────────
            task_result = db.execute(
                text("""
                    SELECT
                        COUNT(*) AS total,
                        COUNT(*) FILTER (WHERE status = 'completed') AS completed,
                        COUNT(*) FILTER (WHERE status IN ('blocked', 'overdue')) AS blocked,
                        COUNT(*) FILTER (WHERE due_date < NOW() AND status NOT IN ('completed', 'cancelled')) AS overdue
                    FROM tasks
                    WHERE project_id = CAST(:pid AS UUID)
                """),
                {"pid": str(project_id)},
            )
            task_row = task_result.mappings().first()

            total_tasks = task_row["total"] if task_row else 0
            completed_tasks = task_row["completed"] if task_row else 0
            blocked_tasks = task_row["blocked"] if task_row else 0
            overdue_tasks = task_row["overdue"] if task_row else 0

            # ── Compute health score ─────────────────────────────
            if total_tasks == 0:
                health_score = 1.0
            else:
                completion_ratio = completed_tasks / total_tasks
                blocked_penalty = (blocked_tasks / total_tasks) * 0.3
                overdue_penalty = (overdue_tasks / total_tasks) * 0.2
                health_score = max(0.0, min(1.0, completion_ratio - blocked_penalty - overdue_penalty))

            # ── Determine health status ──────────────────────────
            if health_score >= 0.8:
                health_status = "on_track"
            elif health_score >= 0.6:
                health_status = "at_risk"
            elif health_score >= 0.4:
                health_status = "off_track"
            else:
                health_status = "critical"

            # ── Update project ───────────────────────────────────
            project = db.execute(
                text("""
                    UPDATE projects
                    SET health_score = :score,
                        updated_at = NOW()
                    WHERE id = CAST(:pid AS UUID)
                    RETURNING id, status
                """),
                {"score": health_score, "pid": str(project_id)},
            )
            row = project.mappings().first()

        self.event_repository.save(
            aggregate_type="project",
            aggregate_id=str(project_id),
            event_type="ProjectHealthRecalculated",
            payload={
                "health_score": round(health_score, 2),
                "health_status": health_status,
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "blocked_tasks": blocked_tasks,
                "overdue_tasks": overdue_tasks,
            },
        )

        return {
            "id": str(project_id),
            "status": row["status"] if row else None,
            "health_score": round(health_score, 2),
            "health_status": health_status,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
        }
