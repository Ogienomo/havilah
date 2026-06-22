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

        AUTO-ROUTES:
        - Simple questions / drafts / summaries → DIRECT mode (1 LLM call, ~3s, no orchestration)
        - Complex multi-step tasks → FULL orchestration (planner → agents → approval)

        This is the main entry point for Hermes.
        """
        import uuid

        run_id = str(uuid.uuid4())
        start_time = datetime.now(timezone.utc)

        logger.info(f"Hermes run {run_id} started: '{instruction[:80]}...' (source={source})")

        # ── AUTO-ROUTE: detect simple requests that don't need orchestration ──
        if self._is_simple_request(instruction):
            logger.info(f"[{run_id}] Direct mode — simple request detected, skipping orchestration")
            return self._process_direct(instruction, run_id, start_time, source, context)

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
            # Include original instruction so _dispatch_agent can surface it to every agent
            plan_context = {**(context or {}), **memory_context, "instruction": instruction}
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

    # ── DIRECT MODE — for simple requests that don't need orchestration ──────

    # Keywords that signal a SIMPLE request (direct answer, no orchestration)
    _SIMPLE_PATTERNS = (
        # Questions
        "what is", "what are", "what's", "who is", "who are",
        "how do", "how does", "how to", "how many", "how much",
        "why is", "why does", "why do", "why are",
        "when is", "when does", "when do",
        "where is", "where are",
        "is it", "are there", "do you", "can you", "could you",
        "explain", "define", "describe", "tell me about",
        # Quick drafting
        "draft a", "write a", "compose a", "create a brief", "summarize",
        "summarise", "rewrite", "polish", "edit this", "improve this",
        "translate", "convert", "format this",
        # Math / calculations
        "calculate", "compute", "solve", "what's the answer",
        # Quick comparisons
        "compare", "difference between", "vs", "versus",
    )

    # Keywords that signal a COMPLEX request (needs orchestration)
    _COMPLEX_PATTERNS = (
        # Multi-step coordination
        "orchestrate", "coordinate", "manage", "workflow", "pipeline",
        # External system actions
        "send an email", "send the email", "schedule a meeting", "book a",
        "publish to", "post to", "notify the team", "deploy",
        "process the payroll", "approve the", "authorise the",
        # Research + deliverable combos
        "research and draft", "analyze and recommend", "review and send",
        "plan and execute", "investigate and report",
        # Explicit approval requests
        "request approval", "get approval",
    )

    def _is_simple_request(self, instruction: str) -> bool:
        """
        Detect whether an instruction is simple enough for Direct mode.

        Simple = single-step question, draft, summary, calculation, or comparison
        that one LLM call can answer well in <5 seconds.

        Complex = multi-step coordination, external system actions, or
        explicit approval workflows.
        """
        instr_lower = instruction.lower().strip()

        # Short instructions (under ~8 words) are almost always simple
        word_count = len(instr_lower.split())

        # If explicitly complex, never route to direct
        for pattern in self._COMPLEX_PATTERNS:
            if pattern in instr_lower:
                return False

        # If explicitly simple, route to direct
        for pattern in self._SIMPLE_PATTERNS:
            if instr_lower.startswith(pattern) or f" {pattern} " in f" {instr_lower} ":
                return True

        # Very short questions (<=6 words) default to direct
        if word_count <= 6 and instr_lower.endswith("?"):
            return True

        # Math expressions
        if any(op in instr_lower for op in ["+", "-", "*", "/", "=", "plus", "minus", "times", "divided"]):
            # But not if it mentions external systems
            if not any(kw in instr_lower for kw in ["email", "send", "schedule", "deploy", "publish"]):
                return True

        # Default: not simple → use full orchestration
        return False

    def _process_direct(
        self,
        instruction: str,
        run_id: str,
        start_time: datetime,
        source: str,
        context: Optional[dict],
    ) -> dict:
        """
        Direct mode — single LLM call, no orchestration.

        For simple questions, drafts, summaries, calculations. Returns the
        answer immediately without going through the planner → agent → approval
        pipeline. Result is wrapped to look like a completed Hermes run so the
        frontend doesn't need to know the difference.
        """
        try:
            # Pull relevant memory as context (fast — no LLM call, just vector search)
            memory_context = ""
            try:
                memories = self.memory_recorder.recall_context(instruction)
                if memories:
                    memory_lines = []
                    for m in memories[:3]:  # Top 3 only
                        title = m.get("title", "")
                        content = m.get("content", "")[:200]
                        if title or content:
                            memory_lines.append(f"- {title}: {content}")
                    if memory_lines:
                        memory_context = "\n\nRELEVANT CONTEXT FROM MEMORY:\n" + "\n".join(memory_lines)
            except Exception as mem_err:
                logger.warning(f"[{run_id}] Memory recall failed (non-blocking): {mem_err}")

            # Single LLM call with a direct-answer system prompt
            direct_prompt = (
                "You are Hermes, the AI Executive Assistant of Havilah OS.\n"
                "Answer the user's request DIRECTLY and COMPLETELY. Right now. No hedging.\n"
                "\n"
                "RULES:\n"
                "1. NEVER say 'I need more context' or 'could you clarify' — make a reasonable assumption and answer.\n"
                "2. NEVER describe what you're going to do — just do it.\n"
                "3. If asked a question, answer it. If asked to draft, draft it. If asked to summarize, summarize.\n"
                "4. Use markdown formatting: headings, bullet points, bold for key insights.\n"
                "5. Be concise but complete. An executive is reading this.\n"
                "6. If you genuinely don't know something, say so and give your best assessment."
            )

            user_content = instruction + memory_context
            messages = [
                {"role": "system", "content": direct_prompt},
                {"role": "user", "content": user_content},
            ]

            logger.info(f"[{run_id}] Direct LLM call starting...")
            result = self.llm.chat(messages=messages)
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()

            output = result["content"]
            tokens = result["tokens"]

            logger.info(f"[{run_id}] Direct mode completed in {elapsed:.1f}s, tokens={tokens.get('total', 0)}")

            # Wrap as a Hermes run result so frontend can render uniformly
            return {
                "run_id": run_id,
                "status": "completed",
                "mode": "direct",  # signal to frontend that this was direct
                "plan": {
                    "summary": f"Direct response to: {instruction}",
                    "steps": [{
                        "step_number": 1,
                        "agent": "executive",
                        "action": instruction,
                        "approval_required": False,
                        "expected_output": "Direct answer",
                        "risk_level": "low",
                    }],
                    "requires_any_approval": False,
                },
                "results": [{
                    "step_number": 1,
                    "agent": "executive",
                    "action": instruction,
                    "status": "success",
                    "output": output,
                    "tokens": tokens,
                    "requires_approval": False,
                }],
                "summary": output,  # full output, no truncation
                "approval_needed": False,
                "approval_id": None,
                "memory_recorded": {"memories_captured": 0, "memories_reinforced": 0},
                "elapsed_seconds": elapsed,
            }

        except Exception as e:
            logger.error(f"[{run_id}] Direct mode failed: {e}")
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            return {
                "run_id": run_id,
                "status": "failed",
                "mode": "direct",
                "error": str(e),
                "plan": None,
                "results": [],
                "summary": f"Direct response failed: {e}",
                "elapsed_seconds": elapsed,
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
                context={**run.get("context", {}), "instruction": run.get("instruction", "")},
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
        """
        # Planner must never be an execution agent — redirect to executive
        if agent_name == "planner":
            logger.warning(f"[{run_id}] Planner assigned as execution step — redirecting to executive")
            agent_name = "executive"

        # Original instruction gives the agent crucial goal context
        original_instruction = (context or {}).get("instruction", action)

        # Build a structured, information-rich user message
        parts = [f"OVERALL GOAL: {original_instruction}"]

        if original_instruction != action:
            parts.append(f"YOUR SPECIFIC TASK: {action}")

        expected = step.get("expected_output", "")
        if expected:
            parts.append(f"EXPECTED DELIVERABLE: {expected}")

        # Provide context from prior steps (last 3 only to stay focused)
        if previous_results:
            ctx_lines = ["CONTEXT FROM PREVIOUS STEPS ALREADY COMPLETED:"]
            for r in previous_results[-3:]:
                out = str(r.get("output", ""))
                if len(out) > 500:
                    out = out[:500] + "…"
                ctx_lines.append(f"• [{r.get('agent', 'agent')}] {out}")
            parts.append("\n".join(ctx_lines))

        parts.append(
            "INSTRUCTION: Produce complete, specific, high-quality output for your task above. "
            "Do NOT ask for clarification. Do NOT describe your process. Deliver the result directly."
        )

        messages = [{"role": "user", "content": "\n\n".join(parts)}]

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
            logger.error(f"[{run_id}] Agent dispatch failed for {agent_name}: {e}")
            # Attempt a minimal fallback with reduced context before giving up
            try:
                fallback_msg = [{"role": "user", "content": (
                    f"Briefly respond to this request in 2-3 sentences: {original_instruction}"
                )}]
                fallback = self.llm.chat(messages=fallback_msg, agent_type="executive")
                return {
                    "step_number": step.get("step_number"),
                    "agent": agent_name,
                    "action": action,
                    "status": "success",
                    "output": fallback["content"],
                    "tokens": fallback.get("tokens"),
                    "requires_approval": False,
                }
            except Exception:
                return {
                    "step_number": step.get("step_number"),
                    "agent": agent_name,
                    "action": action,
                    "status": "failed",
                    "output": f"Unable to complete this step. Please try rephrasing your request.",
                    "error": str(e),
                }

    def _generate_summary(self, instruction: str, results: list[dict], awaiting_approval: bool = False) -> str:
        """
        Generate a clean, human-readable summary — the primary result shown to the user.

        Priority: surface the most substantive agent output rather than dumping all steps.
        """
        if not results:
            return instruction

        if awaiting_approval:
            pending = results[-1]
            out = str(pending.get("output", ""))[:800]
            return (
                f"**Execution paused — human approval required**\n\n"
                f"**Pending action:** {pending.get('action', '')}\n\n"
                f"{out}"
            )

        # Select the most substantive successful result in priority order
        priority_agents = ["research", "writing", "executive", "meeting", "critic", "reviewer", "learning"]
        primary = None
        for agent_name in priority_agents:
            for r in reversed(results):
                if r.get("agent") == agent_name and r.get("status") == "success":
                    primary = r
                    break
            if primary:
                break

        if primary is None:
            primary = next(
                (r for r in reversed(results) if r.get("status") == "success"),
                results[-1],
            )

        return str(primary.get("output", f"Completed: {instruction}"))

    def get_run(self, run_id: str) -> Optional[dict]:
        """Get the status of a run — checks memory cache first, then DB."""
        if run_id in self._active_runs:
            return self._active_runs[run_id]
        # Fall back to DB (handles post-restart lookups)
        return self.run_repo.get(run_id)

    def list_active_runs(self) -> list[dict]:
        """List all active (non-completed) runs from DB."""
        return self.run_repo.list_active()
