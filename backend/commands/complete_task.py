from backend.services.task_service import (
    TaskService
)

service = TaskService()

result = service.change_status(
    "385e9a92-d1c1-4aac-87cb-d92567303299",
    "completed"
)

print()
print("TASK COMPLETED")
print(result["id"])
print(result["status"])

