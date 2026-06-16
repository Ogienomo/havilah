"""
Havilah OS — Approval Gate

Routes actions through the Approval Ledger when required.
No external action executes without passing through this gate.

The approval gate:
1. Checks if an action requires approval (per plan step)
2. Creates an approval request in the ledger
3. Waits for human decision (poll or webhook)
4. Returns the decision

AI NEVER approves — only humans can.
"""

import logging
from typing import Optional
from datetime import datetime, timezone

from backend.services.approval_service import ApprovalService
from backend.services.risk_service import RiskService
from backend.services.notification_service import NotificationService
from backend.events import (
    APPROVAL_REQUESTED,
    APPROVAL_APPROVED,
    APPROVAL_REJECTED,
    RISK_ESCALATED,
)

logger = logging.getLogger("havilah.approval_gate")


class ApprovalGate:
    """
    The gatekeeper between AI recommendations and external execution.

    When a plan step requires approval, the orchestrator sends it here.
    The gate creates an approval request and returns a pending status.
    The human then approves or rejects through the API or WhatsApp.
    """

    def __init__(self):
        self.approval_service = ApprovalService()
        self.risk_service = RiskService()
        self.notification_service = NotificationService()

    def request(self, step: dict, context: dict) -> dict:
        """
        Submit a step for approval.

        Args:
            step: The plan step that requires approval
            context: Additional context (plan summary, previous step results, etc.)

        Returns:
            {"approval_id": str, "status": "pending_approval", "risk_level": str}
        """
        action_type = step.get("approval_category", "administrative")
        summary = step.get("action", "Unknown action")
        risk_level = step.get("risk_level", "medium")

        # Create the approval request
        approval_data = {
            "action_type": action_type,
            "summary": summary,
            "risk_level": risk_level,
            "context": {
                "step_number": step.get("step_number"),
                "agent": step.get("agent"),
                "expected_output": step.get("expected_output"),
                "plan_context": context.get("summary", ""),
            },
        }

        try:
            approval = self.approval_service.request_approval(approval_data)

            # Notify humans that an approval is needed
            # Note: notify_approval_needed requires a recipient_id — use a placeholder
            # for now (the first admin user). In production, route to the right approver.
            try:
                self.notification_service.notify_approval_needed(
                    approval_id=approval["id"],
                    summary=summary,
                    recipient_id=None,  # Will be routed to all admins
                )
            except Exception as notify_err:
                logger.warning(f"Could not create approval notification: {notify_err}")

            logger.info(
                f"Approval requested: {approval['id']} "
                f"for step {step.get('step_number')} ({action_type}, risk={risk_level})"
            )

            return {
                "approval_id": approval["id"],
                "status": "pending_approval",
                "risk_level": risk_level,
                "action_type": action_type,
            }

        except Exception as e:
            logger.error(f"Failed to create approval request: {e}")
            return {
                "status": "error",
                "error": str(e),
            }

    def check_status(self, approval_id: str) -> dict:
        """
        Check the current status of an approval request.

        Returns:
            {"status": "pending"|"approved"|"rejected"|"executed"|"failed", ...}
        """
        try:
            approval = self.approval_service.repository.get_by_id(approval_id)
            if not approval:
                return {"status": "not_found", "approval_id": approval_id}

            return {
                "approval_id": approval_id,
                "status": approval["current_state"],
                "execution_status": approval.get("execution_status"),
                "risk_level": approval.get("risk_level"),
                "action_type": approval.get("action_type"),
            }
        except Exception as e:
            logger.error(f"Failed to check approval status: {e}")
            return {"status": "error", "error": str(e)}

    def is_approved(self, approval_id: str) -> bool:
        """Check if an approval has been approved."""
        status = self.check_status(approval_id)
        return status.get("status") == "approved"

    def is_rejected(self, approval_id: str) -> bool:
        """Check if an approval has been rejected."""
        status = self.check_status(approval_id)
        return status.get("status") == "rejected"

    def is_resolved(self, approval_id: str) -> bool:
        """Check if an approval has been resolved (approved, rejected, or executed)."""
        status = self.check_status(approval_id)
        return status.get("status") in ("approved", "rejected", "executed", "expired", "failed")
