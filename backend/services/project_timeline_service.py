from backend.repositories.project_timeline_repository import (
    ProjectTimelineRepository
)

from backend.repositories.event_repository import (
    EventRepository
)

from backend.events.project_timeline_events import (
    PROJECT_TIMELINE_GENERATED
)


class ProjectTimelineService:

    def __init__(self):

        self.repository = (
            ProjectTimelineRepository()
        )

        self.event_repository = (
            EventRepository()
        )

    def generate_project_timeline(
        self,
        project_id
    ):

        project_events = (
            self.repository.get_project_events(
                project_id
            )
        )

        approvals = (
            self.repository.get_project_approvals(
                project_id
            )
        )

        approval_timelines = []

        for approval in approvals:

            approval_events = (
                self.repository.get_approval_events(
                    approval["id"]
                )
            )

            approval_timelines.append(
                {
                    "approval": approval,
                    "events": approval_events
                }
            )

        timeline = {
            "project_events":
                project_events,
            "approval_timelines":
                approval_timelines
        }

        self.event_repository.save(
            aggregate_type="project",
            aggregate_id=project_id,
            event_type=PROJECT_TIMELINE_GENERATED,
            payload={
                "project_id":
                    project_id
            }
        )

        print(
            f"EVENT -> "
            f"{PROJECT_TIMELINE_GENERATED}"
        )

        return timeline
