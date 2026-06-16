"""
Havilah OS — Project Repository (FIXED)

Fixes from original:
  1. Uses context manager
  2. Consistent indentation (fixed the mixed-indent bug)
  3. Proper UUID casting in all raw SQL
"""

from sqlalchemy import text
from backend.models.project import Project
from backend.repositories.base import get_session


class ProjectRepository:

    def get_projects_by_status(self, status: str):
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT id, title, status, priority, created_at
                    FROM projects
                    WHERE status = :status
                    ORDER BY updated_at DESC
                """),
                {"status": status},
            )
            return [dict(row._mapping) for row in result]

    def create(self, data: dict) -> dict:
        with get_session() as db:
            project = Project(
                title=data["name"],
                objective=data.get("description"),
                project_type=data.get("project_type"),
                priority=data.get("priority", "medium"),
                status=data.get("status", "active"),
                client_contact_id=data.get("client_contact_id"),
                organization_id=data.get("organization_id"),
            )
            db.add(project)
            db.flush()
            return {
                "id": str(project.id),
                "title": project.title,
                "status": project.status,
                "priority": project.priority,
            }

    def get_by_id(self, project_id):
        with get_session() as db:
            project = db.query(Project).filter(Project.id == project_id).first()
            if project is None:
                return None
            return {
                "id": str(project.id),
                "title": project.title,
                "objective": project.objective,
                "status": project.status,
                "priority": project.priority,
                "created_at": project.created_at,
                "updated_at": project.updated_at,
            }

    def get_all(self):
        with get_session() as db:
            projects = db.query(Project).order_by(Project.created_at.desc()).all()
            return [
                {"id": str(p.id), "title": p.title, "status": p.status, "priority": p.priority}
                for p in projects
            ]

    def update_status(self, project_id, status: str):
        with get_session() as db:
            project = db.query(Project).filter(Project.id == project_id).first()
            if project is None:
                raise ValueError("Project not found")
            project.status = status
            db.flush()
            return {"id": str(project.id), "status": project.status}

    def link_approval_to_project(self, project_id, approval_id):
        with get_session() as db:
            db.execute(
                text("""
                    UPDATE approval_requests
                    SET related_project_id = CAST(:project_id AS UUID), updated_at = NOW()
                    WHERE id = CAST(:approval_id AS UUID)
                """),
                {"project_id": str(project_id), "approval_id": str(approval_id)},
            )

    def get_project_approvals(self, project_id):
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT id, action_type, status, execution_status, risk_level, created_at
                    FROM approval_requests
                    WHERE related_project_id = CAST(:project_id AS UUID)
                    ORDER BY created_at
                """),
                {"project_id": str(project_id)},
            )
            return [dict(row._mapping) for row in result]

    def get_project_tasks(self, project_id):
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT id, title, status, priority, due_date, created_at
                    FROM tasks
                    WHERE project_id = CAST(:project_id AS UUID)
                    ORDER BY priority DESC, created_at
                """),
                {"project_id": str(project_id)},
            )
            return [dict(row._mapping) for row in result]

    def get_project_events(self, project_id):
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT event_type, payload, created_at
                    FROM domain_events
                    WHERE aggregate_id = CAST(:project_id AS UUID)
                    ORDER BY created_at
                """),
                {"project_id": str(project_id)},
            )
            return [dict(row._mapping) for row in result]
