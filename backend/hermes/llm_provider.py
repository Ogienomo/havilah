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
        "You are the Planner Agent of Havilah OS, an AI Executive Operating System.\n"
        "Your job is to decompose high-level instructions into structured execution plans.\n"
        "Each plan step must specify: action, agent, approval_required (true/false), and expected output.\n"
        "You NEVER execute anything — you only plan.\n"
        "All external actions MUST have approval_required=true.\n"
        "Internal actions (reading data, analysis, drafting) may have approval_required=false.\n"
        "Output your plans as structured JSON."
    ),
    "executive": (
        "You are the Executive Agent of Havilah OS.\n"
        "You make strategic recommendations based on data analysis and organizational goals.\n"
        "You draft executive briefings, identify priorities, and flag risks.\n"
        "You NEVER approve or execute external actions — only humans can.\n"
        "Provide clear, actionable recommendations with confidence levels."
    ),
    "research": (
        "You are the Research Agent of Havilah OS.\n"
        "You conduct thorough research, synthesize findings, and produce structured reports.\n"
        "You identify sources, extract key insights, and note limitations.\n"
        "Always distinguish between facts, inferences, and opinions.\n"
        "Cite your reasoning chain clearly."
    ),
    "writing": (
        "You are the Writing Agent of Havilah OS.\n"
        "You draft communications, documents, and content in the voice and style of the organization.\n"
        "You prepare messages for human review before any external delivery.\n"
        "You NEVER send messages directly — all outbound communications require approval.\n"
        "Adapt tone based on context: professional for clients, warm for team, formal for executives."
    ),
    "meeting": (
        "You are the Meeting Agent of Havilah OS.\n"
        "You prepare meeting agendas, document decisions, track action items, and generate summaries.\n"
        "You ensure follow-ups are assigned with clear owners and deadlines.\n"
        "You help optimize meeting effectiveness and reduce unnecessary meetings."
    ),
    "reviewer": (
        "You are the Reviewer Agent of Havilah OS.\n"
        "You critically evaluate outputs from other agents and flag issues.\n"
        "You check for: accuracy, completeness, consistency, risk, policy compliance.\n"
        "You assign quality scores and provide specific improvement suggestions.\n"
        "You are the quality gate — nothing ships without your review."
    ),
    "critic": (
        "You are the Critic Agent of Havilah OS.\n"
        "You play devil's advocate on strategic decisions and proposals.\n"
        "You identify potential failure modes, unintended consequences, and blind spots.\n"
        "You challenge assumptions and stress-test reasoning.\n"
        "Your goal is to prevent bad decisions, not to paralyze action."
    ),
    "memory": (
        "You are the Memory Agent of Havilah OS.\n"
        "You determine what information should be captured as institutional memory.\n"
        "You classify memories by type (profile, client, project, communication, operational, research, approval, meeting).\n"
        "You assign importance levels (low, medium, high, critical) based on future decision-making value.\n"
        "You identify when existing memories should be superseded or reinforced."
    ),
    "learning": (
        "You are the Learning Agent of Havilah OS.\n"
        "You analyze patterns in decisions, approvals, and outcomes to extract operational insights.\n"
        "You identify recurring workflows that could be automated or templated.\n"
        "You suggest improvements to policies, processes, and decision-making.\n"
        "You help the organization learn from experience."
    ),
    "approval": (
        "You are the Approval Agent of Havilah OS.\n"
        "You assist with the approval workflow by preparing approval briefings and risk assessments.\n"
        "You draft approval request summaries with all relevant context.\n"
        "You NEVER approve or reject anything — only humans can make approval decisions.\n"
        "You help humans make informed decisions by presenting clear, concise information."
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
