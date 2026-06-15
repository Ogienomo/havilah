from backend.services.briefing_service import (
    BriefingService
)

APPROVAL_ID = (
    "3d96361e-2e98-48f1-886d-901d820135dd"
)

service = BriefingService()

briefing = (
    service.generate_approval_briefing(
        APPROVAL_ID
    )
)

approval = briefing["approval"]

print()
print("APPROVAL BRIEFING")
print()

print(
    f"Action: "
    f"{approval['action_type']}"
)

print(
    f"Summary: "
    f"{approval['summary']}"
)

print(
    f"Status: "
    f"{approval['status']}"
)

print(
    f"Execution: "
    f"{approval['execution_status']}"
)

print()

print("DECISIONS")

for decision in briefing["decisions"]:

    print()

    print(
        decision["decision_type"]
    )

    print(
        decision["decision_reason"]
    )

print()

print("TIMELINE")

for event in briefing["events"]:

    print(
        event["event_type"]
    )
