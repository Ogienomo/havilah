"""
Havilah OS — LLM Provider

Thin wrapper around OpenAI's ChatCompletion API.
All LLM calls in Hermes go through this module — never call OpenAI directly.

Features:
- Centralized model configuration
- Token usage tracking
- Retry logic with exponential backoff
- Structured output support (function calling / JSON mode)
- Conversation history management
"""

import logging
import time
from typing import Optional

from openai import OpenAI

from backend.config.settings import get_settings

logger = logging.getLogger("havilah.llm")

# ── System Prompts per Agent Type ───────────────────────────────

SYSTEM_PROMPTS = {
    "planner": (
        "You are the Planner Agent of Havilah OS — AI Executive Operating System for Havilah Learning Hub.\n"
        "Decompose the instruction into 3-6 precise, executable steps. Be specific and actionable.\n"
        "Rules:\n"
        "- NEVER include steps like 'gather more information', 'clarify requirements', or 'seek context'\n"
        "- Assign research agent for information synthesis; writing agent for drafts; executive agent for analysis/recommendations\n"
        "- Do NOT assign steps to the planner agent — planner only plans, never executes\n"
        "- Steps that send, publish, notify, pay, or modify external systems MUST have approval_required=true\n"
        "- Internal steps (analyse, draft, summarise, review) use approval_required=false\n"
        "Output valid JSON only. Be decisive."
    ),
    "executive": (
        "You are the Executive Agent of Havilah OS serving Havilah Learning Hub leadership.\n"
        "Produce decision-ready output immediately. No preamble, no 'I would suggest', no meta-commentary.\n"
        "Format: clear headers, concise bullet points, bold key insights.\n"
        "Deliver concrete analysis, prioritised recommendations, or executive summaries based on what is asked.\n"
        "Be authoritative and direct. A C-level executive reads this."
    ),
    "research": (
        "You are the Research Agent of Havilah OS.\n"
        "Research the topic thoroughly and produce a well-structured, substantive report NOW.\n"
        "DO NOT explain how to research, ask for clarification, or describe your methodology.\n"
        "DO: produce actual findings, ranked options, comparisons, data, and analysis on the given topic.\n"
        "Structure: ## Overview → ## Key Findings (numbered, specific) → ## Analysis → ## Recommendation.\n"
        "Use your full knowledge base. Produce genuinely useful, specific output."
    ),
    "writing": (
        "You are the Writing Agent of Havilah OS.\n"
        "Draft the requested content immediately — do NOT describe what you will write, just write it.\n"
        "Start with [DRAFT] on the first line. Match tone: professional for clients, warm for team, formal for board.\n"
        "Produce complete, polished, ready-to-review output.\n"
        "Never send externally — all outbound communications require human approval."
    ),
    "meeting": (
        "You are the Meeting Agent of Havilah OS.\n"
        "Produce structured, actionable meeting output: agendas, summaries, decisions, action items.\n"
        "Be concrete: named owners, specific deadlines, measurable outcomes.\n"
        "Format with clear sections and numbered action items."
    ),
    "reviewer": (
        "You are the Reviewer Agent of Havilah OS — the quality gate.\n"
        "Review the previous step's output and produce:\n"
        "**Quality Score:** X/10\n"
        "**Strengths:** (specific)\n"
        "**Issues Found:** (specific, if any)\n"
        "**Improvements:** (actionable)\n"
        "**Verdict:** APPROVED or NEEDS REVISION\n"
        "Be direct. No vague feedback. This gates external delivery."
    ),
    "critic": (
        "You are the Critic Agent of Havilah OS — the devil's advocate.\n"
        "Identify specific risks, failure modes, and blind spots in the plan or output.\n"
        "Format: 3-5 critiques with **Severity** (Critical/High/Medium) and **Mitigation**.\n"
        "Challenge assumptions. Be incisive. Your job is to prevent bad decisions, not to block progress."
    ),
    "memory": (
        "You are the Memory Agent of Havilah OS.\n"
        "Extract institutional knowledge worth capturing from the given context.\n"
        "List each item as: **Title** | **Type** (profile/client/project/communication/operational/research) | **Importance** (low/medium/high/critical) | **Summary**.\n"
        "Only capture novel, reusable information. Skip generic facts."
    ),
    "learning": (
        "You are the Learning Agent of Havilah OS.\n"
        "Extract operational insights and process improvements from the given context.\n"
        "Identify: what worked, what failed, process optimisations, and reusable templates.\n"
        "Format: concise bullet points. Each point must be actionable."
    ),
    "approval": (
        "You are the Approval Agent of Havilah OS.\n"
        "Prepare a concise approval briefing (under 200 words) for the human decision-maker.\n"
        "Include: **What** is being requested | **Why** it is needed | **Risk** level and key factors | **Recommendation**.\n"
        "NEVER make the approval decision yourself — humans decide. Present facts clearly."
    ),
}

# Default system prompt for general-purpose calls
DEFAULT_SYSTEM_PROMPT = (
    "You are Hermes, the AI orchestration engine of Havilah OS.\n"
    "You help manage projects, tasks, approvals, contacts, and organizational operations.\n"
    "You think, draft, recommend, and prepare — but NEVER execute externally without human approval.\n"
    "Be concise, structured, and action-oriented in your responses."
)


class LLMProvider:
    """
    Centralized LLM access for all Hermes agents.

    All calls go through this class. Never use the OpenAI client directly.
    """

    def __init__(self):
        settings = get_settings()
        kwargs = {"api_key": settings.OPENAI_API_KEY}
        if settings.OPENAI_BASE_URL:
            kwargs["base_url"] = settings.OPENAI_BASE_URL
        self.client = OpenAI(**kwargs)
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.temperature = settings.OPENAI_TEMPERATURE
        self._total_tokens_used = 0
        self._call_count = 0

    def chat(
        self,
        messages: list[dict],
        agent_type: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[dict] = None,
    ) -> dict:
        """
        Send a chat completion request.

        Args:
            messages: List of {"role": "user/assistant/system", "content": "..."}
            agent_type: If set, prepends the agent's system prompt
            model: Override default model
            temperature: Override default temperature
            max_tokens: Override default max tokens
            response_format: e.g. {"type": "json_object"} for structured output

        Returns:
            {"content": str, "tokens": {"prompt": int, "completion": int, "total": int}}
        """
        # Prepend system prompt if agent_type specified
        final_messages = []
        if agent_type and agent_type in SYSTEM_PROMPTS:
            final_messages.append({"role": "system", "content": SYSTEM_PROMPTS[agent_type]})
        elif not any(m.get("role") == "system" for m in messages):
            final_messages.append({"role": "system", "content": DEFAULT_SYSTEM_PROMPT})

        final_messages.extend(messages)

        kwargs = {
            "model": model or self.model,
            "messages": final_messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens or self.max_tokens,
        }

        if response_format:
            kwargs["response_format"] = response_format

        # Retry logic: 3 attempts with exponential backoff
        last_error = None
        for attempt in range(3):
            try:
                start = time.perf_counter()
                response = self.client.chat.completions.create(**kwargs)
                elapsed_ms = round((time.perf_counter() - start) * 1000)

                content = response.choices[0].message.content or ""
                usage = response.usage

                token_info = {
                    "prompt": usage.prompt_tokens if usage else 0,
                    "completion": usage.completion_tokens if usage else 0,
                    "total": usage.total_tokens if usage else 0,
                }

                self._total_tokens_used += token_info["total"]
                self._call_count += 1

                logger.info(
                    f"LLM call #{self._call_count}: model={kwargs['model']}, "
                    f"tokens={token_info['total']}, elapsed={elapsed_ms}ms, "
                    f"agent={agent_type or 'general'}"
                )

                return {
                    "content": content,
                    "tokens": token_info,
                    "elapsed_ms": elapsed_ms,
                }

            except Exception as e:
                last_error = e
                wait = (2 ** attempt) + 0.5
                logger.warning(f"LLM call failed (attempt {attempt + 1}/3): {e}. Retrying in {wait}s...")
                time.sleep(wait)

        logger.error(f"LLM call failed after 3 attempts: {last_error}")
        raise RuntimeError(f"LLM call failed after 3 retries: {last_error}")

    def chat_json(
        self,
        messages: list[dict],
        agent_type: Optional[str] = None,
        **kwargs,
    ) -> dict:
        """
        Chat with JSON output mode. Returns parsed JSON dict.
        The agent prompt must instruct the model to output JSON.
        """
        result = self.chat(
            messages=messages,
            agent_type=agent_type,
            response_format={"type": "json_object"},
            **kwargs,
        )

        import json
        try:
            return {
                "data": json.loads(result["content"]),
                "tokens": result["tokens"],
            }
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON output: {e}")
            # Return raw content in a wrapper
            return {
                "data": {"raw_content": result["content"], "parse_error": str(e)},
                "tokens": result["tokens"],
            }

    @property
    def usage_stats(self) -> dict:
        """Return cumulative token usage statistics."""
        return {
            "total_tokens": self._total_tokens_used,
            "total_calls": self._call_count,
        }
