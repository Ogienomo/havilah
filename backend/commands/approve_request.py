from backend.services.approval_service import (
    ApprovalService
)

service = ApprovalService()

approval = service.approve_request(
    "6d02c087-b00a-427b-af2e-18b2472f7a84",
    "Approved by Praise"
)

print()
print("APPROVAL APPROVED")
print(approval["id"])
print(approval["status"])
