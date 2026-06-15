from backend.services.briefing_service import (
    BriefingService
)

service = BriefingService()

briefing = (
    service.generate_executive_briefing()
)

print()

print("EXECUTIVE BRIEFING")

print()

print(
    "Memory Records:",
    briefing["memory_count"]
)

print(
    "Projects:",
    briefing["project_count"]
)

print(
    "Tasks:",
    briefing["task_count"]
)

print(
    "Approvals:",
    briefing["approval_count"]
)

print(
    "Executions:",
    briefing["execution_count"]
)

print()

print("PROJECT STATUS BREAKDOWN")

for item in briefing["project_status_breakdown"]:

    print(
        item["status"],
        item["total"]
    )

print()

print("TASK STATUS BREAKDOWN")

for item in briefing["task_status_breakdown"]:

    print(
        item["status"],
        item["total"]
    )

print()

print("RECENT EVENTS")

for event in briefing["recent_events"]:

    print()

    print(
        event["event_type"]
    )

    print(
        event["aggregate_type"]
    )

    print(
        event["created_at"]
    )
