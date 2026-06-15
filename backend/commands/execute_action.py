from backend.services.approval_service import (
    ApprovalService
)

service = ApprovalService()

result = service.execute_action(
    "6d02c087-b00a-427b-af2e-18b2472f7a84",
    {
        "action": "send_linkedin_message",
        "target": "Jeffery Agadumo",
        "outcome": "simulated_success"
    }
)

print()
print("EXECUTION COMPLETED")
print(result["id"])
print(result["status"])
