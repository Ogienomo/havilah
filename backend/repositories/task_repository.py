from sqlalchemy import text

from backend.database import (
    SessionLocal
)

from backend.models.task import (
    Task
)


class TaskRepository:

   def get_tasks_by_status(
       self,
       status
):

    db = SessionLocal()

    try:

        result = db.execute(
            text(
                """
                SELECT
                    id,
                    title,
                    status
                FROM tasks
                WHERE status = :status
                ORDER BY updated_at DESC
                """
            ),
            {
                "status": status
            }
        )

        return [
            dict(row._mapping)
            for row in result
        ]

    finally:

        db.close()

    def create(
        self,
        data
    ):

        db = SessionLocal()

        try:

            task = Task(
                project_id=data["project_id"],
                title=data["title"],
                description=data.get("description")
            )

            db.add(task)

            db.commit()

            db.refresh(task)

            return {
                "id": str(task.id),
                "title": task.title,
                "status": task.status
            }

        finally:

            db.close()

    def get_by_id(
        self,
        task_id
    ):

        db = SessionLocal()

        try:

            task = (
                db.query(Task)
                .filter(
                    Task.id == task_id
                )
                .first()
            )

            if task is None:

                return None

            return {
                "id": str(task.id),
                "project_id": str(task.project_id),
                "title": task.title,
                "description": task.description,
                "status": task.status
            }

        finally:

            db.close()

    def update_status(
        self,
        task_id,
        status
    ):

        db = SessionLocal()

        try:

            task = (
                db.query(Task)
                .filter(
                    Task.id == task_id
                )
                .first()
            )

            if task is None:

                raise Exception(
                    "Task not found"
                )

            task.status = status

            db.commit()

            db.refresh(task)

            return {
                "id": str(task.id),
                "status": task.status
            }

        finally:

            db.close()

    def link_approval(
        self,
        task_id,
        approval_id
    ):

        db = SessionLocal()

        try:

            db.execute(
                text(
                    """
                    UPDATE approval_requests
                    SET task_id =
                        CAST(:task_id AS UUID)
                    WHERE id =
                        CAST(:approval_id AS UUID)
                    """
                ),
                {
                    "task_id": task_id,
                    "approval_id": approval_id
                }
            )

            db.commit()

            return {
                "task_id": task_id,
                "approval_id": approval_id
            }

        finally:

            db.close()

    def get_task_approvals(
        self,
        task_id
    ):

        db = SessionLocal()

        try:

            result = db.execute(
                text(
                    """
                    SELECT
                        id,
                        action_type,
                        status,
                        execution_status
                    FROM approval_requests
                    WHERE task_id =
                        CAST(:task_id AS UUID)
                    ORDER BY requested_at
                    """
                ),
                {
                    "task_id": task_id
                }
            )

            return [
                dict(row._mapping)
                for row in result
            ]

        finally:

            db.close()
