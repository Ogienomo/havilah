"""
Havilah OS — Approval Repository

Uses context manager, proper state machine, and real datetime values.
"""

from datetime import datetime, timezone

from sqlalchemy import text

from backend.models.approval import ApprovalRequest, ApprovalDecision, ApprovalEvent, ExecutionRecord
from backend.repositories.base import get_session

from backend.models.approval import PENDING_STATES, ACTIVE_STATES, TERMINAL_STATES


class ApprovalRepository:

    def get_pending_approvals(self):
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT id, action_type, current_state,
                           intent_summary AS summary, risk_level, confidence
                    FROM approval_requests
                    WHERE current_state IN ('draft', 'proposed', 'queued_for_review', 'awaiting_approval')
                    ORDER BY created_at
                """)
            )
            return [dict(row._mapping) for row in result]

    def create_request(self, data: dict) -> dict:
        with get_session() as db:
            approval = ApprovalRequest(
                action_type=data["action_type"],
                intent_summary=data["summary"],
                channel=data.get("channel", "internal"),
                draft_payload=data.get("draft_payload", {}),
                risk_level=data.get("risk_level", "medium"),
                confidence=data.get("confidence"),
                related_project_id=data.get("project_id"),
                related_contact_id=data.get("contact_id"),
                related_task_id=data.get("task_id"),
                organization_id=data.get("organization_id"),
                created_by=data.get("created_by"),
            )
            db.add(approval)
            db.flush()
            return {
                "id": str(approval.id),
                "current_state": approval.current_state,
                "status": approval.status,
                "action_type": approval.action_type,
                "summary": approval.intent_summary,
            }

    def get_request(self, approval_id):
        with get_session() as db:
            approval = (
                db.query(ApprovalRequest)
                .filter(ApprovalRequest.id == approval_id)
                .first()
            )
            if approval is None:
                return None
            return {
                "id": str(approval.id),
                "current_state": approval.current_state,
                "status": approval.status,
                "action_type": approval.action_type,
                "summary": approval.intent_summary,
            }

    def get_by_id(self, approval_id):
        with get_session() as db:
            approval = (
                db.query(ApprovalRequest)
                .filter(ApprovalRequest.id == approval_id)
                .first()
            )
            if approval is None:
                return None
            return {
                "id": str(approval.id),
                "current_state": approval.current_state,
                "status": approval.status,
                "execution_status": approval.execution_status,
                "action_type": approval.action_type,
                "summary": approval.intent_summary,
                "risk_level": approval.risk_level,
                "confidence": float(approval.confidence) if approval.confidence else None,
            }

    def approve_request(self, approval_id, reason=None, approver_id=None):
        with get_session() as db:
            approval = (
                db.query(ApprovalRequest)
                .filter(ApprovalRequest.id == approval_id)
                .first()
            )
            if approval is None:
                raise ValueError("Approval request not found")

            now = datetime.now(timezone.utc)
            old_state = approval.current_state
            approval.current_state = "approved"
            approval.approver_id = approver_id
            approval.decision_note = reason
            approval.approved_at = now

            db.add(ApprovalDecision(
                approval_request_id=approval.id,
                decision_type="approve",
                decision_reason=reason,
                decided_by=approver_id,
                decided_at=now,
            ))

            db.add(ApprovalEvent(
                approval_request_id=approval.id,
                event_type="approved",
                actor_type="human",
                actor_id=approver_id,
                old_state=old_state,
                new_state="approved",
                note=reason,
            ))
            db.flush()
            return {"id": str(approval.id), "current_state": approval.current_state}

    def reject_request(self, approval_id, reason=None, decided_by=None):
        with get_session() as db:
            approval = (
                db.query(ApprovalRequest)
                .filter(ApprovalRequest.id == approval_id)
                .first()
            )
            if approval is None:
                raise ValueError("Approval request not found")

            now = datetime.now(timezone.utc)
            old_state = approval.current_state
            approval.current_state = "rejected"
            approval.decision_note = reason
            approval.rejected_at = now

            db.add(ApprovalDecision(
                approval_request_id=approval.id,
                decision_type="reject",
                decision_reason=reason,
                decided_by=decided_by,
                decided_at=now,
            ))

            db.add(ApprovalEvent(
                approval_request_id=approval.id,
                event_type="rejected",
                actor_type="human",
                actor_id=decided_by,
                old_state=old_state,
                new_state="rejected",
                note=reason,
            ))
            db.flush()
            return {"id": str(approval.id), "current_state": approval.current_state}

    def escalate_request(self, approval_id, escalated_to, reason=None, decided_by=None):
        """Escalate an approval to a higher authority."""
        with get_session() as db:
            approval = (
                db.query(ApprovalRequest)
                .filter(ApprovalRequest.id == approval_id)
                .first()
            )
            if approval is None:
                raise ValueError("Approval request not found")

            now = datetime.now(timezone.utc)
            old_state = approval.current_state

            db.add(ApprovalDecision(
                approval_request_id=approval.id,
                decision_type="escalate",
                decision_reason=reason,
                decided_by=decided_by,
                decided_at=now,
                escalated_to=escalated_to,
            ))

            db.add(ApprovalEvent(
                approval_request_id=approval.id,
                event_type="escalated",
                actor_type="human",
                actor_id=decided_by,
                old_state=old_state,
                new_state="queued_for_review",
                note=f"Escalated to {escalated_to}: {reason}",
            ))
            db.flush()
            return {"id": str(approval.id), "current_state": approval.current_state}

    def create_execution_record(self, approval_id, status, result=None):
        with get_session() as db:
            approval = (
                db.query(ApprovalRequest)
                .filter(ApprovalRequest.id == approval_id)
                .first()
            )
            if approval is None:
                raise ValueError("Approval request not found")

            now = datetime.now(timezone.utc)
            old_state = approval.current_state

            record = ExecutionRecord(
                approval_request_id=approval_id,
                execution_status=status,
                result_payload=result,
                started_at=now if status == "in_progress" else None,
                completed_at=now if status == "completed" else None,
            )
            db.add(record)

            if status == "in_progress":
                approval.current_state = "executing"
                approval.execution_status = "in_progress"
            elif status == "completed":
                approval.current_state = "executed"
                approval.execution_status = "completed"
                approval.executed_at = now
            elif status == "failed":
                approval.current_state = "failed"
                approval.execution_status = "failed"

            db.add(ApprovalEvent(
                approval_request_id=approval.id,
                event_type=f"execution_{status}",
                actor_type="system",
                old_state=old_state,
                new_state=approval.current_state,
            ))
            db.flush()
            return {"id": str(record.id), "status": record.execution_status}

    def get_approvals_by_project(self, project_id):
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT id, action_type, current_state, execution_status, risk_level, created_at
                    FROM approval_requests
                    WHERE related_project_id = CAST(:project_id AS UUID)
                    ORDER BY created_at
                """),
                {"project_id": str(project_id)},
            )
            return [dict(row._mapping) for row in result]

    def get_approvals_by_task(self, task_id):
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT id, action_type, current_state, execution_status, risk_level, created_at
                    FROM approval_requests
                    WHERE related_task_id = CAST(:task_id AS UUID)
                    ORDER BY created_at
                """),
                {"task_id": str(task_id)},
            )
            return [dict(row._mapping) for row in result]
