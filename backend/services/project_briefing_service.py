from backend.repositories.project_repository import (
    ProjectRepository
)

from backend.repositories.timeline_repository import (
    TimelineRepository
)

from backend.repositories.event_repository import (
    EventRepository
)

from backend.events.project_events import (
    PROJECT_BRIEFING_GENERATED
)


class ProjectBriefingService:

    def __init__(self):

        self.repository = (
            ProjectRepository()
        )

        self.timeline_repository = (
            TimelineRepository()
        )

        self.event_repository = (
            EventRepository()
        )

    def generate_briefing(
        self,
        project_id
    ):

        project = (
            self.repository.get_by_id(
                project_id
            )
        )

        if project is None:

            raise Exception(
                "Project not found"
            )

        tasks = (
            self.repository
            .get_project_tasks(
                project_id
            )
        )

        for task in tasks:

            task[
                "approvals"
            ] = (
                self.repository
                .get_task_approvals(
                    task["id"]
                )
            )

        events = (
            self.timeline_repository
            .get_business_events_for_aggregate(
                project_id
            )
        )

        self.event_repository.save(
            aggregate_type="project",
            aggregate_id=project_id,
            event_type=
                PROJECT_BRIEFING_GENERATED,
            payload={
                "project_id":
                    project_id
            }
        )

        print(
            f"EVENT -> "
            f"{PROJECT_BRIEFING_GENERATED}"
        )

        return {
            "project":
                project,
            "tasks":
                tasks,
            "events":
                events
        }
