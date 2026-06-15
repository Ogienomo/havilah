from backend.services.project_service import (
    ProjectService
)


service = ProjectService()

project = (
    service.create_project(
        {
            "name":
                "LinkedIn Growth Initiative",

            "description":
                "Jeffery Agadumo personal branding programme",

            "status":
                "active"
        }
    )
)

print()
print("PROJECT CREATED")
print(project["id"])
print(project["name"])
print(project["status"])
