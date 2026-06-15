from backend.services.approval_service import (
    ApprovalService
)

service = ApprovalService()

approval = service.request_approval(
    {
        "action_type":
            "send_linkedin_message",

        "summary":
            "Send LinkedIn outreach to Jeffery",

        "category":
            "communication",

        "confidence":
            0.90
    }
)

print()
print("APPROVAL CREATED")
print(approval["id"])
print(approval["status"])
