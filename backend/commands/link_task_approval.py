from backend.services.task_service import (
    TaskService
)

service = TaskService()

result = service.link_approval(
    "385e9a92-d1c1-4aac-87cb-d92567303299",
    "6d02c087-b00a-427b-af2e-18b2472f7a84"
)

print()

print(
    "TASK LINKED"
)

print(
    result
)
