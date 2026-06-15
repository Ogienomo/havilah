from backend.services.briefing_service import (
    BriefingService
)

CONTACT_ID = (
    "31a93590-cdf4-40a6-9aef-ce979e137f02"
)

service = BriefingService()

briefing = (
    service.generate_contact_briefing(
        CONTACT_ID
    )
)

print()
print("CONTACT BRIEFING")
print()

contact = briefing["contact"]

print(
    f"Name: "
    f"{contact['first_name']} "
    f"{contact['last_name']}"
)

print(
    f"Relationship: "
    f"{contact['relationship_type']}"
)

print()

print("KNOWN MEMORIES")

for memory in briefing["memories"]:

    print()

    print(
        f"- {memory['title']}"
    )

    print(
        f"  {memory['content']}"
    )

    print(
        f"  Importance: "
        f"{memory['importance']}"
    )
