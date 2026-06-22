"""
Havilah OS — Task Planner

Decomposes natural language instructions into structured execution plans.
Each plan is a sequence of steps that specify:
- Which agent should handle it
- What action to perform
- Whether approval is required before execution
- Expected output type

The planner NEVER executes — it only creates the plan.
The orchestrator executes the plan step by step.
"""

import logging
from typing import Optional
from datetime import datetime, timezone

from backend.hermes.llm_provider import LLMProvider
from backend.hermes.agent_registry import AgentRegistry

logger = logging.getLogger("havilah.planner")


# ── Plan Step Schema ────────────────────────────────────────────

PLAN_STEP_SCHEMA = {
    "type": "object",
    "properties": {
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "step_number": {"type": "integer", "description": "1-based step number"},
                    "agent": {
                        "type": "string",
                        "enum": ["planner", "executive", "research", "writing", "meeting",
                                 "reviewer", "critic", "memory", "learning", "approval"],
                        "description": "Which specialized agent handles this step",
                    },
                    "action": {"type": "string", "description": "What the agent should do"},
                    "approval_required": {"type": "boolean", "description": "Whether human approval is needed before executing this step's external effects"},
                    "approval_category": {
                        "type": "string",
                        "enum": ["communication", "financial", "project", "strategic", "administrative"],
                        "description": "Category of approval if approval_required is true",
                    },
                    "expected_output": {"type": "string", "description": "What this step should produce"},
                    "depends_on": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Step numbers this step depends on (0 = no dependency)",
                    },
                    "risk_level": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "description": "Assessed risk level of this step",
                    },
                },
                "required": ["step_number", "agent", "action", "approval_required", "expected_output", "risk_level"],
            },
        },
        "summary": {"type": "string", "description": "Brief summary of the overall plan"},
        "requires_any_approval": {"type": "boolean", "description": "Whether any step requires approval"},
    },
    "required": ["steps", "summary", "requires_any_approval"],
}


class TaskPlanner:
    """
    Decomposes natural language instructions into execution plans.

    The planner uses the LLM to:
    1. Understand the user's intent
    2. Break it into steps
    3. Assign the right agent to each step
    4. Determine approval requirements
    5. Assess risk levels

    All external actions MUST have approval_required=true.
    Internal actions (reading, analyzing, drafting) may skip approval.
    """

    def __init__(self):
        self.llm = LLMProvider()
        self.registry = AgentRegistry()

    def plan(self, instruction: str, context: Optional[dict] = None) -> dict:
        """
        Create an execution plan from a natural language instruction.

        Args:
            instruction: What the user wants done (e.g., "Draft a project update email to Client X")
            context: Optional additional context (current projects, recent memory, etc.)

        Returns:
            {
                "plan_id": str,
                "instruction": str,
                "summary": str,
                "steps": [...],
                "requires_any_approval": bool,
                "created_at": str,
            }
        """
        import uuid

        # Build context section
        context_section = ""
        if context:
            context_section = f"\n\nAdditional context:\n"
            for key, value in context.items():
                context_section += f"- {key}: {value}\n"

        # Build agent capabilities section
        agent_section = "Available agents and their roles:\n"
        for agent in self.registry.list_all():
            agent_section += f"- {agent.name}: {agent.description}\n"
            agent_section += f"  Capabilities: {', '.join(agent.capabilities)}\n"

        prompt = f"""Create a MINIMAL execution plan for this instruction.

INSTRUCTION: {instruction}
{context_section}

{agent_section}

RULES — READ CAREFULLY:
0. MINIMIZE STEPS (most important rule):
   - Research, analysis, drafting, writing, summarizing → EXACTLY 1 STEP
   - Only add a second step if the task genuinely requires a DIFFERENT capability (e.g. draft THEN send)
   - Maximum 3 steps total. If you are considering more, consolidate into fewer steps.
   - Do NOT add memory, planning, or reviewer steps for internal tasks — they waste time.
1. External actions (sending messages, payments, publishing) MUST have approval_required=true
2. Internal actions (analysis, drafting, research, summarizing) have approval_required=false, risk_level=low
3. Choose the SINGLE BEST agent per step — do not split what one agent can do
4. Assess risk honestly: read-only=low, draft=low, external send=high, financial=critical

Output a JSON plan following the schema."""

        logger.info(f"Planning instruction: {instruction[:100]}...")

        result = self.llm.chat_json(
            messages=[{"role": "user", "content": prompt}],
            agent_type="planner",
        )

        plan_data = result["data"]

        # Validate and normalize the plan
        if "steps" not in plan_data:
            # If the LLM didn't follow the schema perfectly, create a minimal plan
            logger.warning("LLM plan did not include 'steps', creating default plan")
            plan_data = self._create_fallback_plan(instruction)

        steps = plan_data["steps"]

        # Hard cap: never more than 3 steps regardless of what the LLM planned
        MAX_STEPS = 3
        if len(steps) > MAX_STEPS:
            logger.warning(f"Plan had {len(steps)} steps — truncated to {MAX_STEPS}")
            steps = steps[:MAX_STEPS]
            for i, s in enumerate(steps):
                s["step_number"] = i + 1

        # Validate risk_level and enforce approval_required for external actions
        for step in steps:
            step["risk_level"] = self._validate_risk_level(step.get("risk_level", "medium"))
            if self._is_external_action(step.get("action", "")) and not step.get("approval_required"):
                step["approval_required"] = True
                step["risk_level"] = max(
                    ["low", "medium", "high"],
                    key=["low", "medium", "high"].index,
                ) if step["risk_level"] == "low" else step["risk_level"]
                logger.warning(
                    f"Forced approval_required=true on step {step.get('step_number')} "
                    f"— detected external action: {step.get('action', '')[:80]}"
                )

        # Enrich with metadata
        plan = {
            "plan_id": str(uuid.uuid4()),
            "instruction": instruction,
            "summary": plan_data.get("summary", instruction),
            "steps": steps,
            "requires_any_approval": plan_data.get("requires_any_approval", True),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "token_usage": result.get("tokens", {}),
        }

        # Safety check: if ANY step has approval_required, set the flag
        for step in plan["steps"]:
            if step.get("approval_required", False):
                plan["requires_any_approval"] = True

        logger.info(
            f"Plan created: {len(plan['steps'])} steps, "
            f"approval_required={plan['requires_any_approval']}"
        )

        return plan

    def _create_fallback_plan(self, instruction: str) -> dict:
        """
        Create a simple fallback plan when the LLM output is malformed.
        Routes through executive agent for analysis, then asks for human direction.
        """
        return {
            "steps": [
                {
                    "step_number": 1,
                    "agent": "executive",
                    "action": f"Analyze the request and provide a structured recommendation: {instruction}",
                    "approval_required": False,
                    "expected_output": "Structured analysis and recommendation",
                    "depends_on": [],
                    "risk_level": "low",
                },
                {
                    "step_number": 2,
                    "agent": "memory",
                    "action": "Capture any relevant context from institutional memory that relates to this request",
                    "approval_required": False,
                    "expected_output": "Relevant memory items and context",
                    "depends_on": [1],
                    "risk_level": "low",
                },
            ],
            "summary": f"Analyze and prepare recommendation for: {instruction}",
            "requires_any_approval": False,
        }

    # ── Internal helpers ──────────────────────────────────────────────

    # Words that ALWAYS mean external action (high confidence)
    _EXTERNAL_ACTION_KEYWORDS = frozenset({
        "send", "email", "publish", "post", "delete", "pay", "payment",
        "invoice", "notify", "message", "execute", "deploy", "submit",
        "upload", "transfer", "share", "broadcast", "announce", "release",
        "push", "dispatch",
    })

    # Words that CAN be external but are often internal — only flag when
    # paired with an external target (e.g. "schedule a meeting" = external,
    # but "schedule a review" = internal)
    _AMBIGUOUS_KEYWORDS = frozenset({
        "create", "update", "schedule", "book",
    })

    # When an ambiguous verb is paired with these nouns, it's INTERNAL
    _INTERNAL_NOUNS_AFTER_AMBIGUOUS = frozenset({
        "summary", "summaries", "draft", "drafts", "memo", "report", "reports",
        "analysis", "analyses", "review", "reviews", "brief", "briefs",
        "outline", "plan", "plans", "strategy", "recommendation", "recommendations",
        "checklist", "template", "note", "notes", "document", "documentation",
        "comparison", "evaluation", "assessment", "breakdown", "list",
    })

    # When an ambiguous verb is paired with these nouns, it's EXTERNAL
    _EXTERNAL_NOUNS_AFTER_AMBIGUOUS = frozenset({
        "meeting", "meetings", "event", "events", "appointment", "calendar",
        "email", "message", "notification", "post", "campaign", "announcement",
        "task", "ticket", "invoice", "payment", "order",
    })

    _VALID_RISK_LEVELS = frozenset({"low", "medium", "high", "critical"})

    def _is_external_action(self, action: str) -> bool:
        """
        Determine if an action touches external systems.

        Conservative: only flag when we're confident. Internal text generation
        (drafts, summaries, analysis) should NEVER be flagged as external.
        """
        if not action:
            return False

        words = action.lower().split()
        word_set = set(words)

        # High-confidence external keywords
        if word_set & self._EXTERNAL_ACTION_KEYWORDS:
            return True

        # Check ambiguous verbs + their object
        ambiguous_hit = word_set & self._AMBIGUOUS_KEYWORDS
        if ambiguous_hit:
            # Look at the noun immediately after the ambiguous verb
            for i, w in enumerate(words):
                if w in self._AMBIGUOUS_KEYWORDS and i + 1 < len(words):
                    next_word = words[i + 1].rstrip(",.;:")
                    # Strip articles
                    while next_word in {"a", "an", "the", "some", "our", "my", "this", "that"} and i + 2 < len(words):
                        i += 1
                        next_word = words[i + 1].rstrip(",.;:")
                    if next_word in self._EXTERNAL_NOUNS_AFTER_AMBIGUOUS:
                        return True
                    if next_word in self._INTERNAL_NOUNS_AFTER_AMBIGUOUS:
                        continue  # internal, don't flag
                    # Unknown noun — be permissive (don't flag)

        return False

    def _validate_risk_level(self, risk_level: str) -> str:
        if risk_level not in self._VALID_RISK_LEVELS:
            logger.warning(f"Unknown risk_level '{risk_level}', defaulting to 'medium'")
            return "medium"
        return risk_level

    def replan_step(self, step: dict, reason: str) -> dict:
        """
        Replan a single step that failed or needs modification.

        Args:
            step: The original step that needs replanning
            reason: Why replanning is needed

        Returns:
            Updated step dict
        """
        prompt = f"""The following plan step needs to be revised:

ORIGINAL STEP: {step.get('action', 'Unknown')}
AGENT: {step.get('agent', 'Unknown')}
REASON FOR REPLAN: {reason}

Please provide a revised step in the same JSON format, with an updated action and possibly a different agent.
Only change what's necessary — keep the same step_number."""

        result = self.llm.chat_json(
            messages=[{"role": "user", "content": prompt}],
            agent_type="planner",
        )

        revised = result["data"]
        # Preserve step_number from original
        revised["step_number"] = step.get("step_number", 1)
        return revised
