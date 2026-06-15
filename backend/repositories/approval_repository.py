from backend.database import SessionLocal

from backend.models.approval import (
    ApprovalRequest,
    ApprovalDecision,
    ExecutionRecord
)


class ApprovalRepository:


    def get_pending_approvals(
        self
):

    db = SessionLocal()

    try:

        result = db.execute(
            text(
                """
                SELECT
                    id,
                    action_type,
                    status
                FROM approval_requests
                WHERE status = 'pending'
                ORDER BY requested_at
                """
            )
        )

        return [
            dict(row._mapping)
            for row in result
        ]

    finally:

        db.close()

    def create_request(self, data):

        db = SessionLocal()

        try:

            approval = ApprovalRequest(
                action_type=data["action_type"],
                summary=data["summary"],
                category=data.get("category"),
                confidence=data.get("confidence")
            )

            db.add(approval)

            db.commit()

            db.refresh(approval)

            return {
                "id": str(approval.id),
                "status": approval.status,
                "action_type": approval.action_type,
                "summary": approval.summary
            }

        finally:

            db.close()

    def get_request(self, approval_id):

        db = SessionLocal()

        try:

            approval = (
                db.query(ApprovalRequest)
                .filter(
                    ApprovalRequest.id == approval_id
                )
                .first()
            )

            if approval is None:

                return None

            return {
                "id": str(approval.id),
                "status": approval.status,
                "action_type": approval.action_type,
                "summary": approval.summary
            }

        finally:

            db.close()

    def get_by_id(self, approval_id):

        db = SessionLocal()

        try:

            approval = (
                db.query(ApprovalRequest)
                .filter(
                    ApprovalRequest.id == approval_id
                )
                .first()
            )

            if approval is None:

                return None

            return {
                "id": str(approval.id),
                "status": approval.status,
                "current_state": approval.current_state,
                "execution_status": approval.execution_status,
                "action_type": approval.action_type,
                "summary": approval.summary
            }

        finally:

            db.close()

    def approve_request(
        self,
        approval_id,
        reason=None
    ):

        db = SessionLocal()

        try:

            approval = (
                db.query(ApprovalRequest)
                .filter(
                    ApprovalRequest.id == approval_id
                )
                .first()
            )

            if approval is None:

                raise Exception(
                    "Approval request not found"
                )

            approval.status = "approved"
            approval.current_state = "approved"

            db.add(
                ApprovalDecision(
                    approval_request_id=approval.id,
                    decision_type="approve",
                    decision_reason=reason
                )
            )

            db.commit()

            db.refresh(approval)

            return {
                "id": str(approval.id),
                "status": approval.status
            }

        finally:

            db.close()

    def reject_request(
        self,
        approval_id,
        reason=None
    ):

        db = SessionLocal()

        try:

            approval = (
                db.query(ApprovalRequest)
                .filter(
                    ApprovalRequest.id == approval_id
                )
                .first()
            )

            if approval is None:

                raise Exception(
                    "Approval request not found"
                )

            approval.status = "rejected"
            approval.current_state = "rejected"

            db.add(
                ApprovalDecision(
                    approval_request_id=approval.id,
                    decision_type="reject",
                    decision_reason=reason
                )
            )

            db.commit()

            db.refresh(approval)

            return {
                "id": str(approval.id),
                "status": approval.status
            }

        finally:

            db.close()

    def create_execution_record(
        self,
        approval_id,
        status,
        result=None
    ):

        db = SessionLocal()

        try:

            approval = (
                db.query(ApprovalRequest)
                .filter(
                    ApprovalRequest.id == approval_id
                )
                .first()
            )

            if approval is None:

                raise Exception(
                    "Approval request not found"
                )

            record = ExecutionRecord(
                approval_request_id=approval_id,
                execution_status=status,
                execution_result=result
            )

            db.add(record)

            approval.execution_status = status

            db.commit()

            db.refresh(record)

            return {
                "id": str(record.id),
                "status": record.execution_status
            }

        finally:

            db.close()
