"""
Havilah OS — Workflow Service

Orchestrates multi-step business processes.
Workflows: sequential, parallel, conditional.
"""

from backend.repositories.workflow_repository import WorkflowRepository
from backend.repositories.event_repository import EventRepository
from backend.events import (
    WORKFLOW_CREATED,
    WORKFLOW_STARTED,
    WORKFLOW_STEP_STARTED,
    WORKFLOW_STEP_COMPLETED,
    WORKFLOW_COMPLETED,
)


class WorkflowService:

    def __init__(self):
        self.repository = WorkflowRepository()
        self.event_repository = EventRepository()

    def create_workflow(self, data: dict):
        workflow = self.repository.create(data)

        self.event_repository.save(
            aggregate_type="workflow",
            aggregate_id=workflow["id"],
            event_type=WORKFLOW_CREATED,
            payload={"title": workflow["title"], "type": data.get("workflow_type", "sequential")},
        )

        return workflow

    def add_step(self, workflow_id, title, step_order, **kwargs):
        step = self.repository.add_step(workflow_id, title, step_order, **kwargs)
        return step

    def add_transition(self, workflow_id, from_step_id, to_step_id, **kwargs):
        transition = self.repository.add_transition(workflow_id, from_step_id, to_step_id, **kwargs)
        return transition

    def start_workflow(self, workflow_id):
        workflow = self.repository.get_by_id(workflow_id)
        if workflow is None:
            raise ValueError("Workflow not found")
        if workflow["status"] != "draft":
            raise ValueError(f"Cannot start — workflow is in '{workflow['status']}' state")

        self.repository.update_workflow_status(workflow_id, "active", current_step_order=0)
        steps = self.repository.get_workflow_steps(workflow_id)

        # Start first step
        if steps:
            self.repository.update_step_status(steps[0]["id"], "in_progress")
            self.event_repository.save(
                aggregate_type="workflow",
                aggregate_id=workflow_id,
                event_type=WORKFLOW_STEP_STARTED,
                payload={"step_id": steps[0]["id"], "step_order": 0},
            )

        self.event_repository.save(
            aggregate_type="workflow",
            aggregate_id=workflow_id,
            event_type=WORKFLOW_STARTED,
            payload={"workflow_id": workflow_id},
        )

        return {"id": workflow_id, "status": "active"}

    def complete_step(self, workflow_id, step_id):
        workflow = self.repository.get_by_id(workflow_id)
        if workflow is None:
            raise ValueError("Workflow not found")

        steps = self.repository.get_workflow_steps(workflow_id)
        current_order = workflow["current_step_order"]

        self.repository.update_step_status(step_id, "completed")
        self.event_repository.save(
            aggregate_type="workflow",
            aggregate_id=workflow_id,
            event_type=WORKFLOW_STEP_COMPLETED,
            payload={"step_id": step_id, "step_order": current_order},
        )

        # Advance to next step
        next_order = current_order + 1
        if next_order < len(steps):
            next_step = steps[next_order]
            self.repository.update_step_status(next_step["id"], "in_progress")
            self.repository.update_workflow_status(workflow_id, "active", current_step_order=next_order)
            self.event_repository.save(
                aggregate_type="workflow",
                aggregate_id=workflow_id,
                event_type=WORKFLOW_STEP_STARTED,
                payload={"step_id": next_step["id"], "step_order": next_order},
            )
        else:
            # All steps done — complete workflow
            self.repository.update_workflow_status(workflow_id, "completed", current_step_order=next_order)
            self.event_repository.save(
                aggregate_type="workflow",
                aggregate_id=workflow_id,
                event_type=WORKFLOW_COMPLETED,
                payload={"workflow_id": workflow_id},
            )

        return {"workflow_id": workflow_id, "current_step_order": next_order}

    def get_workflow(self, workflow_id):
        workflow = self.repository.get_by_id(workflow_id)
        if workflow is None:
            return None
        steps = self.repository.get_workflow_steps(workflow_id)
        return {"workflow": workflow, "steps": steps}
