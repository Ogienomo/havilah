from backend.repositories.task_repository import (
    TaskRepository
)

from backend.repositories.event_repository import (
    EventRepository
)

from backend.events.task_events import (
    TASK_CREATED,
    TASK_APPROVAL_LINKED,
    TASK_STATUS_CHANGED
)

from backend.services.project_health_service import (
    ProjectHealthService
)


class TaskService:

    def __init__(self):

        self.repository = (
            TaskRepository()
        )

        self.event_repository = (
            EventRepository()
        )

        self.project_health_service = (
            ProjectHealthService()
        )

    def _recalculate_project_health(
        self,
        task_id
    ):

        task = (
            self.repository.get_by_id(
                task_id
            )
        )

        if task is None:

            return

        project_id = task.get(
            "project_id"
        )

        if project_id:

            self.project_health_service.recalculate(
                project_id
            )

    def create_task(
        self,
        data
    ):

        task = (
            self.repository.create(
                data
            )
        )

        self.event_repository.save(
            aggregate_type="task",
            aggregate_id=task["id"],
            event_type=TASK_CREATED,
            payload={
                "title":
                    task["title"]
            }
        )

        print(
            f"EVENT -> "
            f"{TASK_CREATED}"
        )

        self._recalculate_project_health(
            task["id"]
        )

        return task

    def change_status(
        self,
        task_id,
        status
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

        result = (
            self.repository.update_status(
                task_id,
                status
            )
        )

        self.event_repository.save(
            aggregate_type="task",
            aggregate_id=task_id,
            event_type=TASK_STATUS_CHANGED,
            payload={
                "status": status
            }
        )

        print(
            f"EVENT -> "
            f"{TASK_STATUS_CHANGED}"
        )

        self._recalculate_project_health(
            task_id
        )

        return result

    def link_approval(
        self,
        task_id,
        approval_id
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

        result = (
            self.repository.link_approval(
                task_id,
                approval_id
            )
        )

        self.event_repository.save(
            aggregate_type="task",
            aggregate_id=task_id,
            event_type=
                TASK_APPROVAL_LINKED,
            payload={
                "approval_id":
                    approval_id
            }
        )

        print(
            f"EVENT -> "
            f"{TASK_APPROVAL_LINKED}"
        )

        return result
