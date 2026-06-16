"""
Havilah OS — Workflow Repository
"""

from sqlalchemy import text
from backend.models.workflow import Workflow, WorkflowStep, WorkflowTransition
from backend.repositories.base import get_session


class WorkflowRepository:

    def create(self, data: dict) -> dict:
        with get_session() as db:
            workflow = Workflow(
                title=data["title"],
                description=data.get("description"),
                workflow_type=data.get("workflow_type", "sequential"),
                project_id=data.get("project_id"),
                auto_advance=data.get("auto_advance", False),
            )
            db.add(workflow)
            db.flush()
            return {"id": str(workflow.id), "title": workflow.title, "status": workflow.status}

    def add_step(self, workflow_id, title, step_order, **kwargs) -> dict:
        with get_session() as db:
            step = WorkflowStep(
                workflow_id=workflow_id,
                title=title,
                step_order=step_order,
                step_type=kwargs.get("step_type", "task"),
                requires_approval=kwargs.get("requires_approval", False),
                task_template=kwargs.get("task_template"),
            )
            db.add(step)
            db.flush()
            return {"id": str(step.id), "title": step.title, "order": step.step_order}

    def add_transition(self, workflow_id, from_step_id, to_step_id, **kwargs) -> dict:
        with get_session() as db:
            transition = WorkflowTransition(
                workflow_id=workflow_id,
                from_step_id=from_step_id,
                to_step_id=to_step_id,
                transition_type=kwargs.get("transition_type", "on_complete"),
                condition=kwargs.get("condition"),
            )
            db.add(transition)
            db.flush()
            return {"id": str(transition.id)}

    def get_by_id(self, workflow_id):
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT id, title, description, workflow_type, status, current_step_order, project_id
                    FROM workflows
                    WHERE id = CAST(:wid AS UUID)
                """),
                {"wid": str(workflow_id)},
            )
            row = result.fetchone()
            return dict(row._mapping) if row else None

    def get_workflow_steps(self, workflow_id):
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT id, title, step_order, step_type, status, requires_approval, completed_at
                    FROM workflow_steps
                    WHERE workflow_id = CAST(:wid AS UUID)
                    ORDER BY step_order
                """),
                {"wid": str(workflow_id)},
            )
            return [dict(row._mapping) for row in result]

    def update_step_status(self, step_id, status: str):
        with get_session() as db:
            db.execute(
                text("""
                    UPDATE workflow_steps SET status = :status, updated_at = NOW()
                    WHERE id = CAST(:sid AS UUID)
                """),
                {"status": status, "sid": str(step_id)},
            )

    def update_workflow_status(self, workflow_id, status: str, current_step_order=None):
        with get_session() as db:
            if current_step_order is not None:
                db.execute(
                    text("""
                        UPDATE workflows SET status = :status, current_step_order = :step_order, updated_at = NOW()
                        WHERE id = CAST(:wid AS UUID)
                    """),
                    {"status": status, "step_order": current_step_order, "wid": str(workflow_id)},
                )
            else:
                db.execute(
                    text("""
                        UPDATE workflows SET status = :status, updated_at = NOW()
                        WHERE id = CAST(:wid AS UUID)
                    """),
                    {"status": status, "wid": str(workflow_id)},
                )
