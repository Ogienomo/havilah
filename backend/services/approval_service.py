from backend.repositories.approval_repository import (
    ApprovalRepository
)

from backend.repositories.event_repository import (
    EventRepository
)

from backend.events.approval_events import (
    APPROVAL_REQUESTED,
    APPROVAL_APPROVED,
    APPROVAL_REJECTED,
    EXECUTION_STARTED,
    EXECUTION_COMPLETED
)


class ApprovalService:

    def __init__(self):

        self.repository = ApprovalRepository()

        self.event_repository = EventRepository()

    # --------------------------------------------------
    # REQUEST APPROVAL
    # --------------------------------------------------

    def request_approval(
        self,
        data
    ):

        approval = (
            self.repository.create_request(
                data
            )
        )

        self.event_repository.save(
            aggregate_type="approval_request",
            aggregate_id=approval["id"],
            event_type=APPROVAL_REQUESTED,
            payload={
                "action_type":
                    approval["action_type"],
                "summary":
                    approval["summary"]
            }
        )

        print(
            f"EVENT -> "
            f"{APPROVAL_REQUESTED}"
        )

        return approval

    # --------------------------------------------------
    # APPROVE
    # --------------------------------------------------

    def approve_request(
        self,
        approval_id,
        reason
    ):

        approval = (
            self.repository.get_by_id(
                approval_id
            )
        )

        if approval is None:

            raise Exception(
                "Approval request not found"
            )

        if approval["status"] == "approved":

            raise Exception(
                "Approval already approved"
            )

        if approval["status"] == "rejected":

            raise Exception(
                "Rejected approvals cannot be approved"
            )

        if approval["execution_status"] == "completed":

            raise Exception(
                "Executed approvals cannot be approved"
            )

        result = (
            self.repository.approve_request(
                approval_id,
                reason
            )
        )

        self.event_repository.save(
            aggregate_type="approval_request",
            aggregate_id=approval_id,
            event_type=APPROVAL_APPROVED,
            payload={
                "approval_id":
                    approval_id
            }
        )

        print(
            f"EVENT -> "
            f"{APPROVAL_APPROVED}"
        )

        return result

    # --------------------------------------------------
    # REJECT
    # --------------------------------------------------

    def reject_request(
        self,
        approval_id,
        reason
    ):

        approval = (
            self.repository.get_by_id(
                approval_id
            )
        )

        if approval is None:

            raise Exception(
                "Approval request not found"
            )

        if approval["status"] == "rejected":

            raise Exception(
                "Approval already rejected"
            )

        if approval["status"] == "approved":

            raise Exception(
                "Approved requests cannot be rejected"
            )

        if approval["execution_status"] == "completed":

            raise Exception(
                "Executed approvals cannot be rejected"
            )

        result = (
            self.repository.reject_request(
                approval_id,
                reason
            )
        )

        self.event_repository.save(
            aggregate_type="approval_request",
            aggregate_id=approval_id,
            event_type=APPROVAL_REJECTED,
            payload={
                "approval_id":
                    approval_id
            }
        )

        print(
            f"EVENT -> "
            f"{APPROVAL_REJECTED}"
        )

        return result

    # --------------------------------------------------
    # EXECUTE
    # --------------------------------------------------

    def execute_action(
        self,
        approval_id,
        execution_result
    ):

        approval = (
            self.repository.get_by_id(
                approval_id
            )
        )

        if approval is None:

            raise Exception(
                "Approval request not found"
            )

        if approval["status"] != "approved":

            raise Exception(
                "Only approved requests can execute"
            )

        if approval["execution_status"] == "completed":

            raise Exception(
                "Request already executed"
            )

        self.event_repository.save(
            aggregate_type="approval_request",
            aggregate_id=approval_id,
            event_type=EXECUTION_STARTED,
            payload={
                "approval_id":
                    approval_id
            }
        )

        print(
            f"EVENT -> "
            f"{EXECUTION_STARTED}"
        )

        execution = (
            self.repository.create_execution_record(
                approval_id,
                "completed",
                execution_result
            )
        )

        self.event_repository.save(
            aggregate_type="approval_request",
            aggregate_id=approval_id,
            event_type=EXECUTION_COMPLETED,
            payload={
                "approval_id":
                    approval_id
            }
        )

        print(
            f"EVENT -> "
            f"{EXECUTION_COMPLETED}"
        )

        return execution
