from backend.services.timeline_service import (
    TimelineService
)


APPROVAL_ID = (
    "3d96361e-2e98-48f1-886d-901d820135dd"
)


service = TimelineService()

events = (
    service.generate_approval_timeline(
        APPROVAL_ID
    )
)

print()

print(
    "APPROVAL TIMELINE"
)

print()

for event in events:

    print(
        event["event_type"]
    )

    print(
        event["created_at"]
    )

    print("-" * 40)
