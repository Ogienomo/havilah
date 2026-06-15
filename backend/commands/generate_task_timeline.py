from backend.services.task_timeline_service import (
    TaskTimelineService
)

service = (
    TaskTimelineService()
)

timeline = (
    service.generate_timeline(
        "385e9a92-d1c1-4aac-87cb-d92567303299"
    )
)

print()

print("TASK TIMELINE")

print()

for event in timeline["events"]:

    print(
        event["event_type"]
    )

    print(
        event["created_at"]
    )

    print(
        "-" * 40
    )
