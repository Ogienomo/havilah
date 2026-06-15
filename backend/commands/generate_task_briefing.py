from backend.services.task_briefing_service import (
    TaskBriefingService
)

service = (
    TaskBriefingService()
)

briefing = (
    service.generate_briefing(
        "385e9a92-d1c1-4aac-87cb-d92567303299"
    )
)

print()

print("TASK BRIEFING")
print()

print(
    briefing["task"]["title"]
)

print()

print(
    briefing["task"]["status"]
)

print()

print(
    "LINKED APPROVALS"
)

print()

for approval in briefing[
    "approvals"
]:

    print(
        approval[
            "action_type"
        ]
    )

    print(
        approval[
            "status"
        ]
    )

    print(
        approval[
            "execution_status"
        ]
    )

    print()

print(
    "TASK EVENTS"
)

for event in briefing[
    "events"
]:

    print(
        event[
            "event_type"
        ]
    )
