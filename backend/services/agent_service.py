"""
Havilah OS — Agent Runtime Service

No agent can approve external execution — ever.
Agents think, draft, recommend, prepare. Humans decide.
"""

from backend.repositories.agent_repository import AgentRepository
from backend.repositories.event_repository import EventRepository
from backend.events import (
    AGENT_ASSIGNED,
    AGENT_STARTED,
    AGENT_COMPLETED,
    AGENT_FAILED,
)


class AgentService:

    def __init__(self):
        self.repository = AgentRepository()
        self.event_repository = EventRepository()

    def register_agent(self, data: dict):
        return self.repository.register_agent(data)

    def get_agent(self, agent_id):
        return self.repository.get_agent(agent_id)

    def get_agent_by_name(self, name: str):
        return self.repository.get_agent_by_name(name)

    def assign_run(self, agent_id, input_context: dict, **kwargs):
        run = self.repository.create_run(agent_id, input_context, **kwargs)

        self.event_repository.save(
            aggregate_type="agent",
            aggregate_id=str(agent_id),
            event_type=AGENT_ASSIGNED,
            payload={"run_id": run["id"], "agent_id": str(agent_id)},
        )

        return run

    def start_run(self, run_id, agent_id):
        self.repository.update_run_status(run_id, "running")

        self.event_repository.save(
            aggregate_type="agent",
            aggregate_id=str(agent_id),
            event_type=AGENT_STARTED,
            payload={"run_id": run_id},
        )

        return {"run_id": run_id, "status": "running"}

    def complete_run(self, run_id, agent_id, results: list, **kwargs):
        self.repository.update_run_status(run_id, "completed", **kwargs)

        for result_data in results:
            self.repository.save_result(run_id, result_data)

        self.event_repository.save(
            aggregate_type="agent",
            aggregate_id=str(agent_id),
            event_type=AGENT_COMPLETED,
            payload={"run_id": run_id, "result_count": len(results)},
        )

        return {"run_id": run_id, "status": "completed", "results": len(results)}

    def fail_run(self, run_id, agent_id, error_message, **kwargs):
        self.repository.update_run_status(run_id, "failed", error_message=error_message, **kwargs)

        self.event_repository.save(
            aggregate_type="agent",
            aggregate_id=str(agent_id),
            event_type=AGENT_FAILED,
            payload={"run_id": run_id, "error": error_message},
        )

        return {"run_id": run_id, "status": "failed"}

    def get_run_results(self, run_id):
        return self.repository.get_run_results(run_id)
