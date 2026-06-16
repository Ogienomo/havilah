"""
Havilah OS — Task Repository (FIXED)

Fixes from original:
  1. Uses context manager
  2. Consistent indentation
  3. Proper UUID casting
  4. Added get_task_events() method (was missing, causing crash in task_timeline_service)
"""

from sqlalchemy import text
from backend.models.task import Task
from backend.repositories.base import get_session


class TaskRepository:

    def get_tasks_by_status(self, status: str):
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT id, title, status, priority, project_id, due_date, created_at
                    FROM tasks
                    WHERE status = :status
                    ORDER BY priority DESC, updated_at DESC
                """),
                {"status": status},
            )
            return [dict(row._mapping) for row in result]

    def create(self, data: dict) -> dict:
        with get_session() as db:
            task = Task(
                project_id=data.get("project_id"),
                parent_task_id=data.get("parent_task_id"),
                workflow_step_id=data.get("workflow_step_id"),
                title=data["title"],
                description=data.get("description"),
                priority=data.get("priority", "medium"),
            )
            db.add(task)
            db.flush()
            return {
                "id": str(task.id),
                "title": task.title,
                "status": task.status,
                "priority": task.priority,
            }

    def get_by_id(self, task_id):
        with get_session() as db:
            task = db.query(Task).filter(Task.id == task_id).first()
            if task is None:
                return None
            return {
                "id": str(task.id),
                "project_id": str(task.project_id) if task.project_id else None,
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "priority": task.priority,
            }

    def update_status(self, task_id, status: str):
        with get_session() as db:
            task = db.query(Task).filter(Task.id == task_id).first()
            if task is None:
                raise ValueError("Task not found")
            task.status = status
            db.flush()
            return {"id": str(task.id), "status": task.status}

    def link_approval(self, task_id, approval_id):
        with get_session() as db:
            db.execute(
                text("""
                    UPDATE approval_requests
                    SET related_task_id = CAST(:task_id AS UUID), updated_at = NOW()
                    WHERE id = CAST(:approval_id AS UUID)
                """),
                {"task_id": str(task_id), "approval_id": str(approval_id)},
            )

    def get_task_approvals(self, task_id):
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT id, action_type, status, execution_status, risk_level, created_at
                    FROM approval_requests
                    WHERE related_task_id = CAST(:task_id AS UUID)
                    ORDER BY created_at
                """),
                {"task_id": str(task_id)},
            )
            return [dict(row._mapping) for row in result]

    def get_task_events(self, task_id):
        """NEW — was missing, causing AttributeError in task_timeline_service."""
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT event_type, payload, created_at
                    FROM domain_events
                    WHERE aggregate_id = CAST(:task_id AS UUID)
                    ORDER BY created_at
                """),
                {"task_id": str(task_id)},
            )
            return [dict(row._mapping) for row in result]

    def get_tasks_by_project(self, project_id):
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
