"""
Havilah OS — Agent Repository
"""

from sqlalchemy import text
from backend.models.agent import Agent, AgentRun, AgentResult
from backend.repositories.base import get_session


class AgentRepository:

    def register_agent(self, data: dict) -> dict:
        with get_session() as db:
            agent = Agent(
                name=data["name"],
                display_name=data["display_name"],
                agent_type=data["agent_type"],
                description=data.get("description"),
                capabilities=data.get("capabilities", []),
                tool_access=data.get("tool_access", []),
                approval_scope=data.get("approval_scope", "none"),
                model_config=data.get("model_config", {}),
            )
            db.add(agent)
            db.flush()
            return {"id": str(agent.id), "name": agent.name}

    def get_agent(self, agent_id):
        with get_session() as db:
            agent = db.query(Agent).filter(Agent.id == agent_id).first()
            if not agent:
                return None
            return {
                "id": str(agent.id),
                "name": agent.name,
                "display_name": agent.display_name,
                "agent_type": agent.agent_type,
                "status": agent.status,
                "capabilities": agent.capabilities,
                "approval_scope": agent.approval_scope,
            }

    def get_agent_by_name(self, name: str):
        with get_session() as db:
            agent = db.query(Agent).filter(Agent.name == name).first()
            if not agent:
                return None
            return self.get_agent(agent.id)

    def create_run(self, agent_id, input_context: dict, **kwargs) -> dict:
        with get_session() as db:
            run = AgentRun(
                agent_id=agent_id,
                task_id=kwargs.get("task_id"),
                approval_id=kwargs.get("approval_id"),
                workflow_step_id=kwargs.get("workflow_step_id"),
                input_context=input_context,
                configuration=kwargs.get("configuration", {}),
                status="assigned",
            )
            db.add(run)
            db.flush()
            return {"id": str(run.id), "agent_id": str(agent_id), "status": run.status}

    def update_run_status(self, run_id, status: str, **kwargs):
        with get_session() as db:
            updates = {"status": status}
            if kwargs.get("error_message"):
                updates["error_message"] = kwargs["error_message"]
            if kwargs.get("duration_ms"):
                updates["duration_ms"] = kwargs["duration_ms"]
            if kwargs.get("token_usage"):
                updates["token_usage"] = kwargs["token_usage"]

            set_clauses = ", ".join(f"{k} = :{k}" for k in updates)
            updates["rid"] = str(run_id)
            db.execute(text(f"UPDATE agent_runs SET {set_clauses}, updated_at = NOW() WHERE id = CAST(:rid AS UUID)"), updates)

    def save_result(self, run_id, data: dict) -> dict:
        with get_session() as db:
            result = AgentResult(
                agent_run_id=run_id,
                result_type=data["result_type"],
                title=data["title"],
                content=data["content"],
                confidence=data.get("confidence"),
                quality_score=data.get("quality_score"),
                is_actionable=data.get("is_actionable", False),
                requires_approval=data.get("requires_approval", False),
            )
            db.add(result)
            db.flush()
            return {"id": str(result.id), "type": result.result_type}

    def get_run_results(self, run_id):
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT id, result_type, title, confidence, quality_score, is_actionable, requires_approval
                    FROM agent_results
                    WHERE agent_run_id = CAST(:rid AS UUID)
                    ORDER BY created_at
                """),
                {"rid": str(run_id)},
            )
            return [dict(row._mapping) for row in result]
