from backend.repositories.task_repository import (
    TaskRepository
)

from backend.repositories.timeline_repository import (
    TimelineRepository
)

from backend.repositories.event_repository import (
    EventRepository
)

from backend.events.task_events import (
    TASK_BRIEFING_GENERATED
)


class TaskBriefingService:

    def __init__(self):

        self.repository = (
            TaskRepository()
        )

        self.timeline_repository = (
            TimelineRepository()
        )

        self.event_repository = (
            EventRepository()
        )

    def generate_briefing(
        self,
        task_id
    ):

        task = (
            self.repository.get_by_id(
                task_id
            )
        )

        if task is None:

            raise Exception(
                "Task not found"
            )

        approvals = (
            self.repository
            .get_task_approvals(
                task_id
            )
        )

        events = (
            self.timeline_repository
            .get_business_events_for_aggregate(
                task_id
            )
        )

        self.event_repository.save(
            aggregate_type="task",
            aggregate_id=task_id,
            event_type=
                TASK_BRIEFING_GENERATED,
            payload={
                "task_id":
                    task_id
            }
        )

        print(
            f"EVENT -> "
            f"{TASK_BRIEFING_GENERATED}"
        )

        return {
            "task":
                task,
            "approvals":
                approvals,
            "events":
                events
        }
