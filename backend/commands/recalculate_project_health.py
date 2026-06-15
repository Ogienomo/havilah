from backend.services.project_health_service import (
    ProjectHealthService
)

service = (
    ProjectHealthService()
)

result = (
    service.recalculate(
        "387d214b-4f9f-4011-9446-30cb7156d07a"
    )
)

print()
print(
    "PROJECT HEALTH UPDATED"
)

print(result["id"])
print(result["status"])
