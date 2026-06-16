"""
Havilah OS — WhatsApp → Hermes Bridge

Connects incoming WhatsApp messages to the Hermes orchestrator.
Users can give instructions, approve/reject requests, and query status
directly from WhatsApp.

Supported WhatsApp interactions:
- Natural language instructions: "Create a project for Client X"
- Approval responses: "approve" / "reject" + optional reason
- Status queries: "status" / "what's pending?"
- Help: "help" / "what can you do?"

All external actions still go through the Approval Ledger.
WhatsApp is an input channel, not a bypass.
"""

import logging
import re
from typing import Optional

from backend.hermes.orchestrator import HermesOrchestrator
from backend.services.whatsapp_service import WhatsAppService
from backend.services.notification_service import NotificationService
from backend.config.settings import get_settings

logger = logging.getLogger("havilah.whatsapp_bridge")


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


class WhatsAppBridge:
    """
    Bridge between WhatsApp messages and the Hermes orchestrator.

    When a WhatsApp message arrives:
    1. Detect the intent (instruction, approval, status, help)
    2. Route to the appropriate Hermes action
    3. Send the response back via WhatsApp
    """

    def __init__(self):
        self.hermes = HermesOrchestrator()
        self.whatsapp_service = WhatsAppService()
        self.notification_service = NotificationService()
        self.settings = get_settings()

        # Track user sessions: phone_number -> {last_run_id, awaiting_approval_for}
        self._sessions: dict[str, dict] = {}

    def process_incoming_message(
        self,
        phone_number: str,
        message_text: str,
        message_id: Optional[str] = None,
    ) -> dict:
        """
        Process an incoming WhatsApp message.

        Args:
            phone_number: Sender's phone number
            message_text: The message content
            message_id: WhatsApp message ID

        Returns:
            {"intent": str, "response_sent": bool, "result": dict}
        """
        message_text = message_text.strip()
        intent = self._detect_intent(message_text)

        logger.info(f"WhatsApp message from {phone_number}: intent={intent}, text='{message_text[:60]}...'")

        try:
            if intent == "approval":
                result = self._handle_approval(phone_number, message_text)
            elif intent == "rejection":
                result = self._handle_rejection(phone_number, message_text)
            elif intent == "status":
                result = self._handle_status(phone_number)
            elif intent == "help":
                result = self._handle_help()
            else:
                # Default: treat as a new instruction for Hermes
                result = self._handle_instruction(phone_number, message_text)

            # Send response via WhatsApp
            response_text = result.get("response", "Processing complete.")
            self._send_whatsapp_response(phone_number, response_text)

            return {
                "intent": intent,
                "response_sent": True,
                "result": result,
            }

        except Exception as e:
            logger.error(f"WhatsApp bridge error: {e}")
            error_response = f"Sorry, I encountered an error processing your message. Please try again or use the API. Error: {str(e)[:100]}"
            self._send_whatsapp_response(phone_number, error_response)

            return {
                "intent": intent,
                "response_sent": True,
                "result": {"error": str(e)},
            }

    def _detect_intent(self, text: str) -> str:
        """Detect the intent of an incoming message."""
        text_lower = text.lower().strip()

        # Check for approval intent first (higher priority)
        for pattern in APPROVAL_PATTERNS:
            if re.search(pattern, text_lower):
                # But make sure it's not a longer instruction that happens to contain "yes"
                if len(text_lower) < 50:  # Short messages are likely approvals
                    return "approval"

        for pattern in REJECTION_PATTERNS:
            if re.search(pattern, text_lower):
                if len(text_lower) < 50:
                    return "rejection"

        for pattern in STATUS_PATTERNS:
            if re.search(pattern, text_lower):
                return "status"

        for pattern in HELP_PATTERNS:
            if re.search(pattern, text_lower):
                return "help"

        # Default: treat as an instruction
        return "instruction"

    def _handle_instruction(self, phone_number: str, instruction: str) -> dict:
        """Handle a new instruction from WhatsApp."""
        # Process through Hermes
        result = self.hermes.process_instruction(
            instruction=instruction,
            source="whatsapp",
            context={"phone_number": phone_number, "channel": "whatsapp"},
        )

        # Track the session
        self._sessions[phone_number] = {
            "last_run_id": result.get("run_id"),
            "last_instruction": instruction,
            "awaiting_approval": result.get("status") == "awaiting_approval",
            "approval_id": result.get("approval_id"),
        }

        # Format response for WhatsApp
        if result.get("status") == "awaiting_approval":
            response = (
                f"I've analyzed your request and prepared a plan.\n\n"
                f"Summary: {result.get('plan', {}).get('summary', 'N/A')}\n\n"
                f"However, this requires your approval before I can proceed.\n"
                f"Approval ID: {result.get('approval_id', 'N/A')}\n\n"
                f"Reply 'approve' to proceed or 'reject' to cancel."
            )
        elif result.get("status") == "completed":
            summary = result.get("summary", "Done.")
            # Truncate for WhatsApp (4096 char limit)
            if len(summary) > 3500:
                summary = summary[:3500] + "...\n\n(Full results available via API)"
            response = summary
        else:
            response = f"Status: {result.get('status', 'unknown')}\n{result.get('summary', '')}"

        return {"response": response, "hermes_result": result}

    def _handle_approval(self, phone_number: str, message: str) -> dict:
        """Handle an approval response."""
        session = self._sessions.get(phone_number, {})
        run_id = session.get("last_run_id")

        if not run_id:
            return {"response": "No pending approvals found. Send me an instruction to get started!"}

        # Extract reason if provided (everything after the approval keyword)
        reason = None
        for pattern in APPROVAL_PATTERNS:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                after = message[match.end():].strip()
                if after:
                    reason = after
                break

        result = self.hermes.continue_run(run_id, approved=True, reason=reason)

        # Update session
        self._sessions[phone_number] = {
            "last_run_id": run_id,
            "awaiting_approval": result.get("status") == "awaiting_approval",
            "approval_id": result.get("approval_id"),
        }

        if result.get("status") == "completed":
            summary = result.get("summary", "Approved and completed!")
            if len(summary) > 3500:
                summary = summary[:3500] + "..."
            return {"response": f"Approved! Here's the result:\n\n{summary}"}
        elif result.get("status") == "awaiting_approval":
            return {
                "response": (
                    f"First step approved! But another step needs your approval.\n"
                    f"Approval ID: {result.get('approval_id', 'N/A')}\n\n"
                    f"Reply 'approve' or 'reject'."
                )
            }
        else:
            return {"response": f"Approval processed. Status: {result.get('status', 'unknown')}"}

    def _handle_rejection(self, phone_number: str, message: str) -> dict:
        """Handle a rejection response."""
        session = self._sessions.get(phone_number, {})
        run_id = session.get("last_run_id")

        if not run_id:
            return {"response": "No pending approvals to reject."}

        # Extract reason
        reason = None
        for pattern in REJECTION_PATTERNS:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                after = message[match.end():].strip()
                if after:
                    reason = after
                break

        result = self.hermes.continue_run(run_id, approved=False, reason=reason)

        self._sessions[phone_number] = {
            "last_run_id": run_id,
            "awaiting_approval": False,
        }

        return {"response": f"Rejected. Reason: {reason or 'Not specified'}. Execution cancelled."}

    def _handle_status(self, phone_number: str) -> dict:
        """Handle a status query."""
        session = self._sessions.get(phone_number, {})
        active_runs = self.hermes.list_active_runs()

        response_parts = []

        if active_runs:
            response_parts.append(f"Active runs ({len(active_runs)}):")
            for run in active_runs:
                response_parts.append(f"- {run['instruction']}... ({run['status']})")
        else:
            response_parts.append("No active runs.")

        if session.get("awaiting_approval"):
            response_parts.append(
                f"\nYou have a pending approval: {session.get('approval_id', 'N/A')}\n"
                f"Reply 'approve' or 'reject'."
            )

        return {"response": "\n".join(response_parts)}

    def _handle_help(self) -> dict:
        """Handle a help request."""
        return {
            "response": (
                "Havilah OS — Hermes Assistant\n\n"
                "You can:\n"
                "- Give me any instruction (e.g., 'Draft a project update for Client X')\n"
                "- Approve requests: reply 'approve' or 'yes'\n"
                "- Reject requests: reply 'reject' or 'no'\n"
                "- Check status: 'status' or 'pending'\n"
                "- Get help: 'help'\n\n"
                "I will always ask for your approval before taking any external action."
            )
        }

    def _send_whatsapp_response(self, phone_number: str, text: str):
        """Send a response via WhatsApp."""
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context — schedule the coroutine
                asyncio.ensure_future(
                    self.whatsapp_service.send_text_message(
                        phone_number=phone_number,
                        text=text,
                    )
                )
            else:
                loop.run_until_complete(
                    self.whatsapp_service.send_text_message(
                        phone_number=phone_number,
                        text=text,
                    )
                )
        except Exception as e:
            logger.warning(f"Could not send WhatsApp response: {e}")
            # Not critical — the message was processed, just couldn't send back via WhatsApp
