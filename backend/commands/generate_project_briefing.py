from backend.services.project_briefing_service import (
    ProjectBriefingService
)

service = (
    ProjectBriefingService()
)

briefing = (
    service.generate_briefing(
        "387d214b-4f9f-4011-9446-30cb7156d07a"
    )
)

print()

print(
    "PROJECT BRIEFING"
)

print()

print(
    briefing["project"]["name"]
)

print(
    briefing["project"]["status"]
)

print()

print(
    "TASKS"
)

print()

for task in briefing["tasks"]:

    print(
        task["title"]
    )

    print(
        task["status"]
    )

    print()

    print(
        "APPROVALS"
    )

    print()

    for approval in task[
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
    "PROJECT EVENTS"
)

print()

for event in briefing[
    "events"
]:

    print(
        event[
            "event_type"
        ]
    )
