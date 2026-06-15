from backend.repositories.task_repository import (
    TaskRepository
)

from backend.repositories.event_repository import (
    EventRepository
)

from backend.events.task_events import (
    TASK_TIMELINE_GENERATED
)


class TaskTimelineService:

    def __init__(self):

        self.repository = (
            TaskRepository()
        )

        self.event_repository = (
            EventRepository()
        )

    def generate_timeline(
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

        events = (
            self.repository.get_task_events(
                task_id
            )
        )

        self.event_repository.save(
            aggregate_type="task",
            aggregate_id=task_id,
            event_type=
                TASK_TIMELINE_GENERATED,
            payload={
                "task_id":
                    task_id
            }
        )

        print(
            f"EVENT -> "
            f"{TASK_TIMELINE_GENERATED}"
        )

        return {
            "task": task,
            "events": events
        }
