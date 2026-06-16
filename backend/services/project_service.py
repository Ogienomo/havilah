from backend.repositories.project_repository import (
    ProjectRepository
)

from backend.repositories.event_repository import (
    EventRepository
)

from backend.events import (
    PROJECT_CREATED,
    PROJECT_STATUS_CHANGED,
    PROJECT_APPROVAL_LINKED,
    PROJECT_BRIEFING_GENERATED,
)


class ProjectService:

    def __init__(self):

        self.repository = (
            ProjectRepository()
        )

        self.event_repository = (
            EventRepository()
        )

    def create_project(
        self,
        data
    ):

        project = (
            self.repository.create(
                data
            )
        )

        self.event_repository.save(
            aggregate_type="project",
            aggregate_id=project["id"],
            event_type=PROJECT_CREATED,
            payload={
                "name":
                    project["name"]
            }
        )

        print(
            f"EVENT -> "
            f"{PROJECT_CREATED}"
        )

        return project

    def change_status(
        self,
        project_id,
        new_status
    ):

        result = (
            self.repository.update_status(
                project_id,
                new_status
            )
        )

        self.event_repository.save(
            aggregate_type="project",
            aggregate_id=project_id,
            event_type=PROJECT_STATUS_CHANGED,
            payload={
                "status":
                    new_status
            }
        )

        print(
            f"EVENT -> "
            f"{PROJECT_STATUS_CHANGED}"
        )

        return result

    def attach_approval(
        self,
        project_id,
        approval_id
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

        result = (
            self.repository.link_approval_to_project(
                project_id,
                approval_id
            )
        )

        self.event_repository.save(
            aggregate_type="project",
            aggregate_id=project_id,
            event_type=PROJECT_APPROVAL_LINKED,
            payload={
                "approval_id":
                    approval_id
            }
        )

        print(
            f"EVENT -> "
            f"{PROJECT_APPROVAL_LINKED}"
        )

        return result

    def generate_project_briefing(
        self,
        project_id
    ):

        project = (
            self.repository.get_by_id(
                project_id
            )
        )

        approvals = (
            self.repository.get_project_approvals(
                project_id
            )
        )

        events = (
            self.repository.get_project_events(
                project_id
            )
        )

        briefing = {
            "project": project,
            "approvals": approvals,
            "events": events
        }

        self.event_repository.save(
            aggregate_type="project",
            aggregate_id=project_id,
            event_type=PROJECT_BRIEFING_GENERATED,
            payload={
                "project_id":
                    project_id
            }
        )

        print(
            f"EVENT -> "
            f"{PROJECT_BRIEFING_GENERATED}"
        )

        return briefing
