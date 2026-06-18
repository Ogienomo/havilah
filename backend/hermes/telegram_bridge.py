"""
Havilah OS — Telegram → Hermes Bridge

Mirrors ``backend.hermes.whatsapp_bridge`` but for Telegram.

When a Telegram message arrives:
1. Detect the intent (instruction, approval, rejection, status, help)
2. Route to the appropriate Hermes action
3. Send the response back via Telegram
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from backend.hermes.orchestrator import HermesOrchestrator
from backend.services.telegram_service import TelegramService
from backend.config.settings import get_settings

logger = logging.getLogger("havilah.telegram_bridge")


# ── Intent Detection ────────────────────────────────────────────

APPROVAL_PATTERNS = [
    r"\b(approve|approved|yes|confirm|ok|go ahead|proceed|grant)\b",
]

REJECTION_PATTERNS = [
    r"\b(reject|rejected|no|deny|denied|decline|declined|stop|cancel|veto)\b",
]

STATUS_PATTERNS = [
    r"\b(status|pending|what'?s pending|what'?s waiting|approvals|queue)\b",
]

HELP_PATTERNS = [
    r"\b(help|what can you do|commands|how to|instructions)\b",
]


class TelegramBridge:
    """
    Bridge between Telegram messages and the Hermes orchestrator.

    One bridge instance per process — sessions are tracked in-memory
    keyed by Telegram chat_id.
    """

    def __init__(self) -> None:
        self.hermes = HermesOrchestrator()
        self.telegram = TelegramService()
        self.settings = get_settings()

        # chat_id -> {last_run_id, last_instruction, awaiting_approval, approval_id}
        self._sessions: dict[int | str, dict] = {}

    # ── Public entry point ───────────────────────────────────

    def process_incoming_message(
        self,
        chat_id: int | str,
        text: str,
        sender_name: Optional[str] = None,
        message_id: Optional[int] = None,
    ) -> dict:
        """Process a single inbound Telegram message."""
        if not text:
            return {"intent": "empty", "response_sent": False, "result": {}}

        text = text.strip()
        intent = self._detect_intent(text)
        logger.info(
            f"Telegram message from chat_id={chat_id} ({sender_name}): "
            f"intent={intent}, text='{text[:60]}…'"
        )

        try:
            if intent == "approval":
                result = self._handle_approval(chat_id, text)
            elif intent == "rejection":
                result = self._handle_rejection(chat_id, text)
            elif intent == "status":
                result = self._handle_status(chat_id)
            elif intent == "help":
                result = self._handle_help()
            else:
                result = self._handle_instruction(chat_id, text)

            response_text = result.get("response", "Processing complete.")
            self.telegram.send_message(
                chat_id=chat_id,
                text=response_text,
                reply_to_message_id=message_id,
            )
            return {
                "intent": intent,
                "response_sent": True,
                "result": result,
            }
        except Exception as e:
            logger.error(f"Telegram bridge error: {e}", exc_info=True)
            error_text = (
                "I hit an error processing that. Please try again, "
                f"or rephrase. Error: {str(e)[:120]}"
            )
            self.telegram.send_message(chat_id=chat_id, text=error_text)
            return {
                "intent": intent,
                "response_sent": True,
                "result": {"error": str(e)},
            }

    # ── Intent detection ─────────────────────────────────────

    def _detect_intent(self, text: str) -> str:
        text_lower = text.lower().strip()
        if len(text_lower) < 50:
            for pattern in APPROVAL_PATTERNS:
                if re.search(pattern, text_lower):
                    return "approval"
            for pattern in REJECTION_PATTERNS:
                if re.search(pattern, text_lower):
                    return "rejection"
        for pattern in STATUS_PATTERNS:
            if re.search(pattern, text_lower):
                return "status"
        for pattern in HELP_PATTERNS:
            if re.search(pattern, text_lower):
                return "help"
        return "instruction"

    # ── Handlers ─────────────────────────────────────────────

    def _handle_instruction(self, chat_id: int | str, instruction: str) -> dict:
        """Forward a natural-language instruction to Hermes."""
        result = self.hermes.process_instruction(
            instruction=instruction,
            source="telegram",
            context={
                "chat_id": chat_id,
                "channel": "telegram",
                "sender": "telegram_user",
            },
        )

        self._sessions[chat_id] = {
            "last_run_id": result.get("run_id"),
            "last_instruction": instruction,
            "awaiting_approval": result.get("status") == "awaiting_approval",
            "approval_id": result.get("approval_id"),
        }

        if result.get("status") == "awaiting_approval":
            plan_summary = result.get("plan", {}).get("summary", "N/A")
            approval_id = result.get("approval_id", "N/A")
            response = (
                "*Plan prepared — needs your approval*\n\n"
                f"{plan_summary}\n\n"
                f"Approval ID: `{approval_id}`\n\n"
                "Reply `approve` to proceed or `reject` to cancel."
            )
        elif result.get("status") == "completed":
            summary = result.get("summary", "Done.")
            if len(summary) > 3500:
                summary = summary[:3500] + "…\n\n(Full results available via API)"
            response = f"*Done*\n\n{summary}"
        else:
            response = (
                f"Status: *{result.get('status', 'unknown')}*\n"
                f"{result.get('summary', '')}"
            )
        return {"response": response, "hermes_result": result}

    def _handle_approval(self, chat_id: int | str, message: str) -> dict:
        session = self._sessions.get(chat_id, {})
        run_id = session.get("last_run_id")
        if not run_id:
            return {
                "response": (
                    "I don't have a pending approval for you. "
                    "Send me an instruction first — e.g. "
                    "_Create a project for Q3 marketing audit_."
                )
            }
        reason = None
        for pattern in APPROVAL_PATTERNS:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                tail = message[match.end():].strip(" :,-")
                if tail:
                    reason = tail
                break
        result = self.hermes.continue_run(run_id=run_id, approved=True, reason=reason)
        session.pop("awaiting_approval", None)
        session.pop("approval_id", None)
        return {
            "response": f"*Approved*\n\n{result.get('summary', 'Continuing.')}",
            "hermes_result": result,
        }

    def _handle_rejection(self, chat_id: int | str, message: str) -> dict:
        session = self._sessions.get(chat_id, {})
        run_id = session.get("last_run_id")
        if not run_id:
            return {"response": "Nothing to reject — no pending approval."}
        reason = None
        for pattern in REJECTION_PATTERNS:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                tail = message[match.end():].strip(" :,-")
                if tail:
                    reason = tail
                break
        result = self.hermes.continue_run(run_id=run_id, approved=False, reason=reason)
        session.pop("awaiting_approval", None)
        session.pop("approval_id", None)
        return {
            "response": f"*Rejected*\n\n{result.get('summary', 'Cancelled.')}",
            "hermes_result": result,
        }

    def _handle_status(self, chat_id: int | str) -> dict:
        active = self.hermes.list_active_runs()
        if not active:
            return {"response": "No active Hermes runs. Everything is idle."}
        lines = [f"*{len(active)} active run(s):*\n"]
        for run in active[:10]:
            lines.append(
                f"• `{str(run.get('run_id', '?'))[:8]}` — {run.get('status', '?')}\n"
                f"  _{run.get('instruction', '')[:60]}…_"
            )
        return {"response": "\n".join(lines)}

    def _handle_help(self) -> dict:
        return {
            "response": (
                "*Havilah OS — Hermes via Telegram*\n\n"
                "I'm your AI Executive Operating System. "
                "I plan, draft, and recommend — but you approve before anything executes.\n\n"
                "*Commands:*\n"
                "• Send any natural-language instruction → I'll route it through 10 agents\n"
                "• `status` — show active Hermes runs\n"
                "• `approve` — approve the most recent pending plan\n"
                "• `reject` — reject the most recent pending plan\n"
                "• `help` — show this message\n\n"
                "*Examples:*\n"
                "_Create a project for Q3 competitive audit_\n"
                "_Generate an executive briefing for next week_\n"
                "_Research the top 5 AI coding tools in 2026_"
            )
        }
