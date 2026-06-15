from backend.services.project_dashboard_service import (
    ProjectDashboardService
)

service = ProjectDashboardService()

dashboard = (
    service.generate_dashboard(
        "387d214b-4f9f-4011-9446-30cb7156d07a"
    )
)

print()

print("PROJECT DASHBOARD")
print()

print(
    dashboard["project"]["name"]
)

print(
    "Status:",
    dashboard["project"]["status"]
)

print()

print("METRICS")
print()

print(
    "Tasks Total:",
    dashboard["metrics"]["task_total"]
)

print(
    "Tasks Completed:",
    dashboard["metrics"]["task_completed"]
)

print(
    "Tasks In Progress:",
    dashboard["metrics"]["task_in_progress"]
)

print(
    "Tasks Pending:",
    dashboard["metrics"]["task_pending"]
)

print(
    "Tasks Blocked:",
    dashboard["metrics"]["task_blocked"]
)

print()

print(
    "Approvals Total:",
    dashboard["metrics"]["approval_total"]
)

print(
    "Approved Approvals:",
    dashboard["metrics"]["approved_count"]
)

print(
    "Completed Executions:",
    dashboard["metrics"]["completed_execution_count"]
)

print()

print("TASKS")
print()

for task in dashboard["tasks"]:

    print(
        task["title"]
    )

    print(
        task["status"]
    )

    print()

    print("APPROVALS")

    print()

    for approval in task.get("approvals", []):

        print(
            approval["action_type"]
        )

        print(
            approval["status"]
        )

        print(
            approval["execution_status"]
        )

        print()

print("PROJECT EVENTS")
print()

for event in dashboard["events"]:

    print(
        event["event_type"]
    )
