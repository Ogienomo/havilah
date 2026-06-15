from backend.services.project_service import (
    ProjectService
)

PROJECT_ID = (
    "387d214b-4f9f-4011-9446-30cb7156d07a"
)

APPROVAL_ID = (
    "3d96361e-2e98-48f1-886d-901d820135dd"
)

service = ProjectService()

result = (
    service.attach_approval(
        PROJECT_ID,
        APPROVAL_ID
    )
)

print()
print("PROJECT LINKED")
print(result)
