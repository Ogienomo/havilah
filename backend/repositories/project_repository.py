from sqlalchemy import text

from backend.database import SessionLocal

from backend.models.project import Project


class ProjectRepository:

   def get_projects_by_status(
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
                    name,
                    status
                FROM projects
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

    def create(self, data):

        db = SessionLocal()

        try:

            project = Project(
                name=data["name"],
                description=data.get("description"),
                status=data.get("status", "active")
            )

            db.add(project)

            db.commit()

            db.refresh(project)

            return {
                "id": str(project.id),
                "name": project.name,
                "description": project.description,
                "status": project.status
            }

        finally:

            db.close()

    def get_by_id(self, project_id):

        db = SessionLocal()

        try:

            project = (
                db.query(Project)
                .filter(Project.id == project_id)
                .first()
            )

            if project is None:
                return None

            return {
                "id": str(project.id),
                "name": project.name,
                "description": project.description,
                "status": project.status,
                "created_at": project.created_at,
                "updated_at": project.updated_at
            }

        finally:

            db.close()

    def get_all(self):

        db = SessionLocal()

        try:

            projects = (
                db.query(Project)
                .order_by(Project.created_at)
                .all()
            )

            return [
                {
                    "id": str(project.id),
                    "name": project.name,
                    "status": project.status
                }
                for project in projects
            ]

        finally:

            db.close()

    def update_status(self, project_id, status):

        db = SessionLocal()

        try:

            project = (
                db.query(Project)
                .filter(Project.id == project_id)
                .first()
            )

            if project is None:
                raise Exception("Project not found")

            project.status = status

            db.commit()

            db.refresh(project)

            return {
                "id": str(project.id),
                "status": project.status
            }

        finally:

            db.close()

    def link_approval_to_project(self, project_id, approval_id):

        db = SessionLocal()

        try:

            db.execute(
                text(
                    """
                    UPDATE approval_requests
                    SET project_id = CAST(:project_id AS UUID)
                    WHERE id = CAST(:approval_id AS UUID)
                    """
                ),
                {
                    "project_id": project_id,
                    "approval_id": approval_id
                }
            )

            db.commit()

            return {
                "project_id": project_id,
                "approval_id": approval_id
            }

        finally:

            db.close()

    def get_project_approvals(self, project_id):

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
                    WHERE project_id = CAST(:project_id AS UUID)
                    ORDER BY requested_at
                    """
                ),
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

    def get_project_tasks(self, project_id):

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
                    WHERE project_id = CAST(:project_id AS UUID)
                    ORDER BY created_at
                    """
                ),
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

    def get_task_approvals(self, task_id):

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
                    WHERE task_id = CAST(:task_id AS UUID)
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

    def get_project_events(self, project_id):

        db = SessionLocal()

        try:

            result = db.execute(
                text(
                    """
                    SELECT
                        event_type,
                        created_at
                    FROM domain_events
                    WHERE aggregate_id = CAST(:project_id AS UUID)
                    ORDER BY created_at
                    """
                ),
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
