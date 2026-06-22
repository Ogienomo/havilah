"""
Havilah OS — Hermes Orchestrator

The central orchestration engine. Hermes receives instructions, plans work,
dispatches to specialized agents, routes through the Approval Ledger,
and records everything to Memory.

Orchestration Loop:
    1. RECEIVE instruction (from API, WhatsApp, or scheduled trigger)
    2. RECALL relevant memory context
    3. PLAN the execution (decompose into steps)
    4. EXECUTE steps sequentially:
       a. Dispatch to the right agent
       b. If approval_required → route through ApprovalGate → WAIT for human
       c. Collect the result
    5. RECORD outcomes to Memory
    6. RESPOND to the user

Core principle: AI thinks, drafts, recommends, and prepares — but NEVER
executes externally without human approval.
"""

import logging
from typing import Optional
from datetime import datetime, timezone
from enum import Enum

from backend.hermes.llm_provider import LLMProvider
from backend.hermes.agent_registry import AgentRegistry
from backend.hermes.task_planner import TaskPlanner
from backend.hermes.approval_gate import ApprovalGate
from backend.hermes.memory_recorder import MemoryRecorder
from backend.repositories.hermes_run_repository import HermesRunRepository
from backend.config.settings import get_settings

logger = logging.getLogger("havilah.orchestrator")


class RunStatus(str, Enum):
    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class HermesOrchestrator:
    """
    The central orchestration engine of Havilah OS.

    Hermes is the AI brain that:
    - Receives natural language instructions
    - Plans execution by decomposing into steps
    - Dispatches work to specialized agents (via LLM)
    - Routes external actions through the Approval Ledger
    - Records outcomes to institutional Memory
    - Reports results back to the user

    Hermes NEVER approves or executes externally without human consent.
    """

    def __init__(self):
        settings = get_settings()
        self.llm = LLMProvider()
        self.registry = AgentRegistry()
        self.planner = TaskPlanner()
        self.approval_gate = ApprovalGate()
        self.memory_recorder = MemoryRecorder()
        self.run_repo = HermesRunRepository()

        # In-memory cache for fast lookups (DB is the source of truth)
        self._active_runs: dict[str, dict] = {}

    def process_instruction(
        self,
        instruction: str,
        source: str = "api",
        context: Optional[dict] = None,
    ) -> dict:
        """
        Process a natural language instruction through the full Hermes pipeline.

        This is the main entry point for Hermes.

        Args:
            instruction: What the user wants done
            source: Where the instruction came from ("api", "whatsapp", "scheduled")
            context: Additional context (user info, channel info, etc.)

        Returns:
            {
                "run_id": str,
                "status": str,
                "plan": dict,
                "results": list,
                "summary": str,
                "approval_needed": bool,
                "approval_id": str | None,
                "memory_recorded": dict,
            }
        """
        import uuid

        run_id = str(uuid.uuid4())
        start_time = datetime.now(timezone.utc)

        logger.info(f"Hermes run {run_id} started: '{instruction[:80]}...' (source={source})")

        # Track the run in memory and persist to DB
        run = {
            "run_id": run_id,
            "instruction": instruction,
            "source": source,
            "status": RunStatus.PLANNING,
            "started_at": start_time.isoformat(),
            "context": context or {},
        }
        self._active_runs[run_id] = run
        self.run_repo.create(run_id, instruction, source, context or {})

        try:
            # ── Step 1: RECALL relevant memory ─────────────────────
            logger.info(f"[{run_id}] Recalling memory context...")
            memories = self.memory_recorder.recall_context(instruction)
            memory_context = {}
            if memories:
                memory_context["relevant_memories"] = [
                    {"title": m.get("title", ""), "content": m.get("content", "")[:200]}
                    for m in memories[:5]  # Top 5 most relevant
                ]

            # ── Step 2: PLAN the execution ─────────────────────────
            logger.info(f"[{run_id}] Creating execution plan...")
            plan_context = {**(context or {}), **memory_context}
            plan = self.planner.plan(instruction, context=plan_context)

            run["plan"] = plan
            run["status"] = RunStatus.EXECUTING

            # ── Step 3: EXECUTE the plan steps ─────────────────────
            results = []
            approval_id = None

            for step in plan["steps"]:
                step_num = step.get("step_number", 0)
                agent_name = step.get("agent", "executive")
                action = step.get("action", "")
                requires_approval = step.get("approval_required", False)

                logger.info(f"[{run_id}] Executing step {step_num}: {agent_name} → {action[:60]}...")

                # Dispatch to the agent
                step_result = self._dispatch_agent(
                    run_id=run_id,
                    agent_name=agent_name,
                    action=action,
                    step=step,
                    previous_results=results,
                    context=plan_context,
                )

                # If the step requires approval, route through the gate
                if requires_approval and step_result.get("status") == "success":
                    logger.info(f"[{run_id}] Step {step_num} requires approval — routing to ApprovalGate")

                    approval_result = self.approval_gate.request(
                        step=step,
                        context={"summary": plan.get("summary", ""), "step_result": step_result},
                    )

                    step_result["approval"] = approval_result
                    approval_id = approval_result.get("approval_id")

                    # Mark the run as awaiting approval
                    run["status"] = RunStatus.AWAITING_APPROVAL
                    results.append(step_result)
                    self.run_repo.update_status(run_id, RunStatus.AWAITING_APPROVAL, plan=plan, results=results)

                    logger.info(
                        f"[{run_id}] Awaiting approval {approval_id} for step {step_num}"
                    )

                    return {
                        "run_id": run_id,
                        "status": "awaiting_approval",
                        "plan": plan,
                        "results": results,
                        "summary": self._generate_summary(instruction, results, awaiting_approval=True),
                        "approval_needed": True,
                        "approval_id": approval_id,
                        "pending_step": step_num,
                        "total_steps": len(plan["steps"]),
                        "memory_recorded": {"memories_captured": 0, "memories_reinforced": 0},
                    }

                results.append(step_result)

            # ── Step 4: RECORD outcomes to memory ───────────────────
            logger.info(f"[{run_id}] Recording outcomes to memory...")
            memory_result = self.memory_recorder.record_outcome(
                instruction=instruction,
                plan=plan,
                results=results,
            )

            # ── Step 5: GENERATE summary ────────────────────────────
            summary = self._generate_summary(instruction, results)

            run["status"] = RunStatus.COMPLETED
            run["completed_at"] = datetime.now(timezone.utc).isoformat()
            self.run_repo.update_status(run_id, RunStatus.COMPLETED, plan=plan, results=results)

            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.info(
                f"Hermes run {run_id} completed in {elapsed:.1f}s: "
                f"{len(results)} steps, approval_needed={plan.get('requires_any_approval', False)}"
            )

            return {
                "run_id": run_id,
                "status": "completed",
                "plan": plan,
                "results": results,
                "summary": summary,
                "approval_needed": False,
                "approval_id": None,
                "memory_recorded": memory_result,
                "elapsed_seconds": elapsed,
            }

        except Exception as e:
            logger.error(f"Hermes run {run_id} failed: {e}")
            run["status"] = RunStatus.FAILED
            run["error"] = str(e)
            self.run_repo.update_status(run_id, RunStatus.FAILED, error=str(e))

            return {
                "run_id": run_id,
                "status": "failed",
                "error": str(e),
                "plan": run.get("plan"),
                "results": run.get("results", []),
                "summary": f"Execution failed: {e}",
            }

    def continue_run(self, run_id: str, approved: bool, reason: Optional[str] = None) -> dict:
        """
        Continue a run that was paused for approval.

        Called after a human approves or rejects via the API or WhatsApp.

        Args:
            run_id: The run to continue
            approved: Whether the human approved the pending step
            reason: Optional reason for the decision

        Returns:
            Updated run result dict
        """
        if run_id not in self._active_runs:
            # Try to reload from DB (post-restart recovery)
            db_run = self.run_repo.get(run_id)
            if db_run is None:
                return {"error": f"Run {run_id} not found or expired"}
            self._active_runs[run_id] = db_run

        run = self._active_runs[run_id]
        if run["status"] != RunStatus.AWAITING_APPROVAL:
            return {"error": f"Run {run_id} is not awaiting approval (status={run['status']})"}

        plan = run.get("plan", {})
        results = run.get("results", [])

        # Find the pending step
        pending_step_idx = len(results) - 1
        if pending_step_idx < 0:
            return {"error": "No pending step found"}

        if not approved:
            # Mark the step as rejected and stop
            results[pending_step_idx]["approval"]["decision"] = "rejected"
            results[pending_step_idx]["approval"]["reason"] = reason

            # Record the rejection to memory
            self.memory_recorder.record_outcome(
                instruction=run["instruction"],
                plan=plan,
                results=results,
            )

            run["status"] = RunStatus.CANCELLED
            return {
                "run_id": run_id,
                "status": "cancelled",
                "reason": "Human rejected the approval request",
                "results": results,
                "summary": "Execution cancelled — human rejected the approval request.",
            }

        # Approved! Continue executing remaining steps
        results[pending_step_idx]["approval"]["decision"] = "approved"
        results[pending_step_idx]["approval"]["reason"] = reason

        # Execute remaining steps
        remaining_steps = plan["steps"][pending_step_idx + 1:]
        approval_id = None

        for step in remaining_steps:
            step_num = step.get("step_number", 0)
            agent_name = step.get("agent", "executive")
            action = step.get("action", "")
            requires_approval = step.get("approval_required", False)

            step_result = self._dispatch_agent(
                run_id=run_id,
                agent_name=agent_name,
                action=action,
                step=step,
                previous_results=results,
                context=run.get("context", {}),
            )

            if requires_approval and step_result.get("status") == "success":
                approval_result = self.approval_gate.request(
                    step=step,
                    context={"summary": plan.get("summary", ""), "step_result": step_result},
                )
                step_result["approval"] = approval_result
                approval_id = approval_result.get("approval_id")
                run["status"] = RunStatus.AWAITING_APPROVAL
                results.append(step_result)

                return {
                    "run_id": run_id,
                    "status": "awaiting_approval",
                    "plan": plan,
                    "results": results,
                    "summary": self._generate_summary(run["instruction"], results, awaiting_approval=True),
                    "approval_needed": True,
                    "approval_id": approval_id,
                    "pending_step": step_num,
                    "total_steps": len(plan["steps"]),
                }

            results.append(step_result)

        # All steps completed
        memory_result = self.memory_recorder.record_outcome(
            instruction=run["instruction"],
            plan=plan,
            results=results,
        )

        summary = self._generate_summary(run["instruction"], results)
        run["status"] = RunStatus.COMPLETED

        return {
            "run_id": run_id,
            "status": "completed",
            "plan": plan,
            "results": results,
            "summary": summary,
            "approval_needed": False,
            "approval_id": None,
            "memory_recorded": memory_result,
        }

    def _dispatch_agent(
        self,
        run_id: str,
        agent_name: str,
        action: str,
        step: dict,
        previous_results: list[dict],
        context: dict,
    ) -> dict:
        """
        Dispatch a step to a specialized agent via LLM.

        The agent receives:
        - The action to perform
        - Context from previous steps
        - Its system prompt (role-specific)

        The agent returns:
        - The output (analysis, draft, recommendation, etc.)
        - Whether it requires human review
        - Confidence level
        """
        # Build conversation with previous results as context
        messages = []

        # Include previous step results as context
        if previous_results:
            prev_summary = "Previous step results:\n"
            for i, r in enumerate(previous_results):
                output = r.get("output", "No output")
                if isinstance(output, str) and len(output) > 300:
                    output = output[:300] + "..."
                prev_summary += f"Step {i+1}: {output}\n"
            messages.append({"role": "assistant", "content": prev_summary})

        # The actual instruction for this step
        messages.append({"role": "user", "content": action})

        # Get agent-specific overrides
        agent_def = self.registry.get(agent_name)
        model_overrides = agent_def.model_overrides if agent_def else {}

        try:
            result = self.llm.chat(
                messages=messages,
                agent_type=agent_name,
                **model_overrides,
            )

            return {
                "step_number": step.get("step_number"),
                "agent": agent_name,
                "action": action,
                "status": "success",
                "output": result["content"],
                "tokens": result["tokens"],
                "requires_approval": step.get("approval_required", False),
            }

        except Exception as e:
            logger.error(f"Agent dispatch failed for {agent_name}: {e}")
            return {
                "step_number": step.get("step_number"),
                "agent": agent_name,
                "action": action,
                "status": "failed",
                "output": f"Agent error: {e}",
                "error": str(e),
            }

    def _generate_summary(self, instruction: str, results: list[dict], awaiting_approval: bool = False) -> str:
        """Generate a human-readable summary of the orchestration results."""
        if awaiting_approval:
            summary = f"Processed: {instruction}\n\nExecution paused — human approval required.\n\n"
        else:
            summary = f"Processed: {instruction}\n\n"

        for i, r in enumerate(results):
            agent = r.get("agent", "unknown")
            status = r.get("status", "unknown")
            output = r.get("output", "No output")
            if isinstance(output, str) and len(output) > 200:
                output = output[:200] + "..."
            summary += f"{i+1}. [{agent}] ({status}): {output}\n"

            if r.get("approval"):
                approval_status = r["approval"].get("status", "unknown")
                summary += f"   Approval: {approval_status}\n"

        return summary

    def get_run(self, run_id: str) -> Optional[dict]:
        """Get the status of a run — checks memory cache first, then DB."""
        if run_id in self._active_runs:
            return self._active_runs[run_id]
        # Fall back to DB (handles post-restart lookups)
        return self.run_repo.get(run_id)

    def list_active_runs(self) -> list[dict]:
        """List all active (non-completed) runs from DB."""
        return self.run_repo.list_active()
