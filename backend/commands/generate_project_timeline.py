from backend.services.project_timeline_service import (
    ProjectTimelineService
)

PROJECT_ID = (
    "387d214b-4f9f-4011-9446-30cb7156d07a"
)

service = (
    ProjectTimelineService()
)

timeline = (
    service.generate_project_timeline(
        PROJECT_ID
    )
)

print()
print(
    "PROJECT TIMELINE"
)

print()
print(
    "PROJECT EVENTS"
)

for event in timeline[
    "project_events"
]:

    print()

    print(
        event["event_type"]
    )

    print(
        event["created_at"]
    )

    print(
        "-" * 40
    )

print()
print(
    "APPROVAL TIMELINES"
)

for approval_data in timeline[
    "approval_timelines"
]:

    approval = (
        approval_data[
            "approval"
        ]
    )

    print()

    print(
        "=" * 50
    )

    print(
        approval[
            "action_type"
        ]
    )

    print(
        "=" * 50
    )

    for event in approval_data[
        "events"
    ]:

        print()

        print(
            event[
                "event_type"
            ]
        )

        print(
            event[
                "created_at"
            ]
        )

        print(
            "-" * 40
        )
