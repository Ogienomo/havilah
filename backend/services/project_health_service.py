from backend.repositories.project_repository import (
    ProjectRepository
)

from backend.repositories.event_repository import (
    EventRepository
)

from backend.events.project_events import (
    PROJECT_STATUS_CHANGED
)


class ProjectHealthService:

    def __init__(self):

        self.repository = (
            ProjectRepository()
        )

        self.event_repository = (
            EventRepository()
        )

    def recalculate(
        self,
        project_id
    ):

        tasks = (
            self.repository
            .get_project_tasks(
                project_id
            )
        )

        if not tasks:

            return

        statuses = [
            task["status"]
            for task in tasks
        ]

        if all(
            status == "completed"
            for status in statuses
        ):

            project_status = (
                "completed"
            )

        elif any(
            status == "blocked"
            for status in statuses
        ):

            project_status = (
                "at_risk"
            )

        else:

            project_status = (
                "active"
            )

        result = (
            self.repository
            .update_status(
                project_id,
                project_status
            )
        )

        self.event_repository.save(
            aggregate_type="project",
            aggregate_id=project_id,
            event_type=
                PROJECT_STATUS_CHANGED,
            payload={
                "status":
                    project_status
            }
        )

        print(
            f"EVENT -> "
            f"{PROJECT_STATUS_CHANGED}"
        )

        return result
