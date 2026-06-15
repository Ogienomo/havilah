from backend.services.task_service import (
    TaskService
)

service = TaskService()

task = service.create_task(
    {
        "project_id":
        "387d214b-4f9f-4011-9446-30cb7156d07a",

        "title":
        "Rewrite LinkedIn Headline",

        "description":
        "Improve profile positioning"
    }
)

print()

print("TASK CREATED")

print(task["id"])

print(task["title"])

print(task["status"])
