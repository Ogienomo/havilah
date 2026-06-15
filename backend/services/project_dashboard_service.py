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
    PROJECT_DASHBOARD_GENERATED
)


class ProjectDashboardService:

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

    def generate_dashboard(
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
            self.repository.get_project_tasks(
                project_id
            )
        )

        approvals = (
            self.repository.get_project_approvals(
                project_id
            )
        )

        events = (
            self.timeline_repository
            .get_business_events_for_aggregate(
                project_id
            )
        )

        task_total = len(tasks)

        task_completed = sum(
            1 for task in tasks
            if task["status"] == "completed"
        )

        task_in_progress = sum(
            1 for task in tasks
            if task["status"] == "in_progress"
        )

        task_pending = sum(
            1 for task in tasks
            if task["status"] == "pending"
        )

        task_blocked = sum(
            1 for task in tasks
            if task["status"] == "blocked"
        )

        approval_total = len(approvals)

        approved_count = sum(
            1 for approval in approvals
            if approval["status"] == "approved"
        )

        completed_execution_count = sum(
            1 for approval in approvals
            if approval["execution_status"] == "completed"
        )

        dashboard = {
            "project": project,
            "tasks": tasks,
            "approvals": approvals,
            "events": events,
            "metrics": {
                "task_total": task_total,
                "task_completed": task_completed,
                "task_in_progress": task_in_progress,
                "task_pending": task_pending,
                "task_blocked": task_blocked,
                "approval_total": approval_total,
                "approved_count": approved_count,
                "completed_execution_count": completed_execution_count
            }
        }

        self.event_repository.save(
            aggregate_type="project",
            aggregate_id=project_id,
            event_type=PROJECT_DASHBOARD_GENERATED,
            payload={
                "project_id": project_id
            }
        )

        print(
            f"EVENT -> {PROJECT_DASHBOARD_GENERATED}"
        )

        return dashboard
