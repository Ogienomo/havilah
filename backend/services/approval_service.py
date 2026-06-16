"""
Havilah OS — Approval Service

The governance backbone. NOTHING external bypasses the Approval Ledger.
Uses current_state as the ONE source of truth for the approval state machine.
"""

from backend.repositories.approval_repository import ApprovalRepository
from backend.repositories.event_repository import EventRepository
from backend.events import (
    APPROVAL_REQUESTED,
    APPROVAL_APPROVED,
    APPROVAL_REJECTED,
    EXECUTION_STARTED,
    EXECUTION_COMPLETED,
    EXECUTION_FAILED,
    RISK_CALCULATED,
    RISK_ESCALATED,
)
from backend.models.approval import PENDING_STATES


class ApprovalService:

    def __init__(self):
        self.repository = ApprovalRepository()
        self.event_repository = EventRepository()

    # ── REQUEST ───────────────────────────────────────────────

    def request_approval(self, data):
        approval = self.repository.create_request(data)

        self.event_repository.save(
            aggregate_type="approval_request",
            aggregate_id=approval["id"],
            event_type=APPROVAL_REQUESTED,
            payload={
                "action_type": approval["action_type"],
                "summary": approval["summary"],
            },
        )

        return approval

    # ── APPROVE ───────────────────────────────────────────────

    def approve_request(self, approval_id, reason=None, approver_id=None):
        approval = self.repository.get_by_id(approval_id)
        if approval is None:
            raise ValueError("Approval request not found")

        if approval["current_state"] not in PENDING_STATES:
            raise ValueError(
                f"Cannot approve — current state is '{approval['current_state']}', "
                f"expected a pending state"
            )

        if approval["execution_status"] == "completed":
            raise ValueError("Executed approvals cannot be modified")

        result = self.repository.approve_request(approval_id, reason, approver_id)

        self.event_repository.save(
            aggregate_type="approval_request",
            aggregate_id=approval_id,
            event_type=APPROVAL_APPROVED,
            payload={"approval_id": approval_id, "approver_id": str(approver_id) if approver_id else None},
        )

        return result

    # ── REJECT ────────────────────────────────────────────────

    def reject_request(self, approval_id, reason=None, decided_by=None):
        approval = self.repository.get_by_id(approval_id)
        if approval is None:
            raise ValueError("Approval request not found")

        if approval["current_state"] not in PENDING_STATES:
            raise ValueError(
                f"Cannot reject — current state is '{approval['current_state']}', "
                f"expected a pending state"
            )

        result = self.repository.reject_request(approval_id, reason, decided_by)

        self.event_repository.save(
            aggregate_type="approval_request",
            aggregate_id=approval_id,
            event_type=APPROVAL_REJECTED,
            payload={"approval_id": approval_id},
        )

        return result

    # ── ESCALATE ──────────────────────────────────────────────

    def escalate_request(self, approval_id, escalated_to, reason=None, decided_by=None):
        result = self.repository.escalate_request(approval_id, escalated_to, reason, decided_by)

        self.event_repository.save(
            aggregate_type="approval_request",
            aggregate_id=approval_id,
            event_type=RISK_ESCALATED,
            payload={"approval_id": approval_id, "escalated_to": str(escalated_to)},
        )

        return result

    # ── EXECUTE ───────────────────────────────────────────────

    def execute_action(self, approval_id, execution_result):
        approval = self.repository.get_by_id(approval_id)
        if approval is None:
            raise ValueError("Approval request not found")

        if approval["current_state"] != "approved":
            raise ValueError("Only approved requests can execute")

        if approval["execution_status"] == "completed":
            raise ValueError("Request already executed")

        # Start execution
        self.event_repository.save(
            aggregate_type="approval_request",
            aggregate_id=approval_id,
            event_type=EXECUTION_STARTED,
            payload={"approval_id": approval_id},
        )

        execution = self.repository.create_execution_record(
            approval_id, "completed", execution_result
        )

        self.event_repository.save(
            aggregate_type="approval_request",
            aggregate_id=approval_id,
            event_type=EXECUTION_COMPLETED,
            payload={"approval_id": approval_id},
        )

        return execution
