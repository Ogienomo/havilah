"""
Havilah OS — WhatsApp Service

Business logic for WhatsApp Business API integration.
Handles:
1. Message sending/receiving via WhatsApp Cloud API
2. Session management (opt-in/out, context tracking)
3. Approval flow through WhatsApp (approve/reject/escalate via buttons)
4. Template management
5. Webhook processing (delivery receipts, read receipts, inbound messages)

Core principle: WhatsApp approval votes are recorded in the Approval Ledger.
No action executes without passing through the 7+2 state machine.
"""

import hashlib
import hmac
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

import httpx

from backend.config.settings import get_settings
from backend.repositories.whatsapp_repository import WhatsAppRepository
from backend.repositories.event_repository import EventRepository
from backend.repositories.approval_repository import ApprovalRepository
from backend.events import (
    WHATSAPP_MESSAGE_RECEIVED,
    WHATSAPP_MESSAGE_SENT,
    WHATSAPP_MESSAGE_DELIVERED,
    WHATSAPP_MESSAGE_READ,
    WHATSAPP_MESSAGE_FAILED,
    WHATSAPP_SESSION_CREATED,
    WHATSAPP_SESSION_OPTED_IN,
    WHATSAPP_SESSION_OPTED_OUT,
    WHATSAPP_APPROVAL_VOTE_RECEIVED,
    WHATSAPP_APPROVAL_VOTE_PROCESSED,
    WHATSAPP_APPROVAL_SENT,
)

settings = get_settings()
logger = logging.getLogger("havilah.whatsapp")


class WhatsAppService:
    """
    WhatsApp Business API integration service.

    Uses the WhatsApp Cloud API (Meta Graph API v21.0).
    All outbound messages go through the Approval Ledger if they are external.
    """

    WHATSAPP_API_BASE = "https://graph.facebook.com"

    def __init__(self):
        self.repository = WhatsAppRepository()
        self.event_repository = EventRepository()
        self.approval_repository = ApprovalRepository()

    # ── WhatsApp API Client ──────────────────────────────────────

    def _get_api_url(self, endpoint: str) -> str:
        """Build the full WhatsApp API URL."""
        return (
            f"{self.WHATSAPP_API_BASE}/{settings.WHATSAPP_API_VERSION}"
            f"/{settings.WHATSAPP_PHONE_NUMBER_ID}/{endpoint}"
        )

    def _get_headers(self) -> dict:
        """Get authenticated headers for WhatsApp API calls."""
        return {
            "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }

    async def _call_whatsapp_api(self, endpoint: str, payload: dict) -> dict:
        """Make an authenticated call to the WhatsApp Cloud API."""
        if not settings.WHATSAPP_ENABLED:
            logger.warning("WhatsApp integration is disabled — skipping API call")
            return {"status": "disabled", "message": "WhatsApp integration is disabled"}

        url = self._get_api_url(endpoint)
        headers = self._get_headers()

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                response_data = response.json()

                if response.status_code >= 400:
                    logger.error(f"WhatsApp API error: {response.status_code} - {response_data}")
                    return {"status": "error", "code": response.status_code, "detail": response_data}

                return response_data
            except httpx.TimeoutException:
                logger.error("WhatsApp API timeout")
                return {"status": "error", "detail": "Request timed out"}
            except Exception as e:
                logger.error(f"WhatsApp API exception: {e}")
                return {"status": "error", "detail": str(e)}

    # ── Message Sending ──────────────────────────────────────────

    async def send_text_message(self, phone_number: str, text: str,
                                related_entity_type: str = None,
                                related_entity_id: str = None) -> dict:
        """Send a plain text message via WhatsApp."""
        # Get or create session
        session = self.repository.get_or_create_session(phone_number)

        if not session.get("opted_in"):
            logger.warning(f"Cannot send message to {phone_number} — user has not opted in")
            return {"status": "error", "detail": "User has not opted in to WhatsApp notifications"}

        # Record message in database
        message = self.repository.create_message(
            session_id=session["id"],
            direction="outbound",
            message_type="text",
            content_body=text,
            recipient_phone=phone_number,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
        )

        # Send via WhatsApp API
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_number,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }

        result = await self._call_whatsapp_api("messages", payload)

        # Update message with WhatsApp ID
        if result.get("messages"):
            whatsapp_msg_id = result["messages"][0].get("id")
            self.repository.update_message_status(
                message["id"], "sent",
                whatsapp_message_id=whatsapp_msg_id,
            )
            message["status"] = "sent"
            message["whatsapp_message_id"] = whatsapp_msg_id

            # Log event
            self.event_repository.save(
                aggregate_type="whatsapp_message",
                aggregate_id=message["id"],
                event_type=WHATSAPP_MESSAGE_SENT,
                payload={"phone": phone_number, "direction": "outbound", "type": "text"},
            )

        return message

    async def send_interactive_message(self, phone_number: str, body_text: str,
                                       buttons: list[dict],
                                       header_text: str = None,
                                       footer_text: str = None,
                                       related_entity_type: str = None,
                                       related_entity_id: str = None,
                                       approval_id: str = None) -> dict:
        """Send an interactive message with buttons via WhatsApp.

        Buttons format: [{"id": "approve", "title": "Approve"}, {"id": "reject", "title": "Reject"}]
        Max 3 buttons per WhatsApp interactive message.
        """
        session = self.repository.get_or_create_session(phone_number)

        if not session.get("opted_in"):
            return {"status": "error", "detail": "User has not opted in"}

        # Build interactive payload
        interactive = {
            "type": "button",
            "body": {"text": body_text},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": b["id"], "title": b["title"]}}
                    for b in buttons[:3]  # WhatsApp max 3 buttons
                ]
            }
        }
        if header_text:
            interactive["header"] = {"type": "text", "text": header_text}
        if footer_text:
            interactive["footer"] = {"text": footer_text}

        # Record message
        message = self.repository.create_message(
            session_id=session["id"],
            direction="outbound",
            message_type="interactive",
            content_body=body_text,
            interactive_type="button",
            interactive_payload={"buttons": buttons},
            recipient_phone=phone_number,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            approval_id=approval_id,
        )

        # Send via API
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_number,
            "type": "interactive",
            "interactive": interactive,
        }

        result = await self._call_whatsapp_api("messages", payload)

        if result.get("messages"):
            whatsapp_msg_id = result["messages"][0].get("id")
            self.repository.update_message_status(
                message["id"], "sent",
                whatsapp_message_id=whatsapp_msg_id,
            )
            message["status"] = "sent"
            message["whatsapp_message_id"] = whatsapp_msg_id

            self.event_repository.save(
                aggregate_type="whatsapp_message",
                aggregate_id=message["id"],
                event_type=WHATSAPP_MESSAGE_SENT,
                payload={"phone": phone_number, "direction": "outbound", "type": "interactive"},
            )

        return message

    async def send_template_message(self, phone_number: str, template_name: str,
                                    parameters: list[str] = None,
                                    language: str = "en",
                                    related_entity_type: str = None,
                                    related_entity_id: str = None,
                                    approval_id: str = None) -> dict:
        """Send a template message via WhatsApp."""
        session = self.repository.get_or_create_session(phone_number)

        if not session.get("opted_in"):
            return {"status": "error", "detail": "User has not opted in"}

        # Record message
        message = self.repository.create_message(
            session_id=session["id"],
            direction="outbound",
            message_type="template",
            template_name=template_name,
            template_parameters={"parameters": parameters or []},
            recipient_phone=phone_number,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            approval_id=approval_id,
        )

        # Build template component
        components = []
        if parameters:
            components.append({
                "type": "body",
                "parameters": [{"type": "text", "text": p} for p in parameters],
            })

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_number,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language},
                "components": components,
            },
        }

        result = await self._call_whatsapp_api("messages", payload)

        if result.get("messages"):
            whatsapp_msg_id = result["messages"][0].get("id")
            self.repository.update_message_status(
                message["id"], "sent",
                whatsapp_message_id=whatsapp_msg_id,
            )
            # Increment template usage
            tmpl = self.repository.get_template(template_name, language)
            if tmpl:
                self.repository.increment_template_use(tmpl["id"])

            self.event_repository.save(
                aggregate_type="whatsapp_message",
                aggregate_id=message["id"],
                event_type=WHATSAPP_MESSAGE_SENT,
                payload={"phone": phone_number, "template": template_name},
            )

        return message

    # ── Approval Flow via WhatsApp ──────────────────────────────

    async def send_approval_request(self, approval_id: str, phone_number: str) -> dict:
        """Send an approval request to a user via WhatsApp with Approve/Reject/Escalate buttons.

        This is the core of the WhatsApp approval flow:
        1. AI proposes an action → ApprovalRequest is created
        2. Approval request is sent to the decision-maker via WhatsApp
        3. Decision-maker responds via WhatsApp button (approve/reject/escalate)
        4. Vote is recorded and processed through the 7+2 state machine
        """
        # Get approval details
        approval = self.approval_repository.get_by_id(approval_id)
        if not approval:
            return {"status": "error", "detail": "Approval request not found"}

        action_type = approval.get("action_type", "Unknown Action")
        risk_level = approval.get("risk_level", "medium").upper()
        summary = approval.get("intent_summary", "No summary provided")
        channel = approval.get("channel", "internal")

        # Build the approval message
        header = f"Approval Required — {risk_level} Risk"
        body = (
            f"Action: {action_type}\n"
            f"Channel: {channel}\n"
            f"Risk Level: {risk_level}\n\n"
            f"{summary}\n\n"
            f"Approval ID: {approval_id[:8]}..."
        )
        footer = "Havilah OS — AI proposes, Human disposes"

        # Determine buttons based on risk level
        buttons = [
            {"id": f"approve:{approval_id}", "title": "Approve"},
            {"id": f"reject:{approval_id}", "title": "Reject"},
        ]
        if risk_level in ("HIGH", "CRITICAL"):
            buttons.append({"id": f"escalate:{approval_id}", "title": "Escalate"})

        result = await self.send_interactive_message(
            phone_number=phone_number,
            body_text=body,
            buttons=buttons,
            header_text=header,
            footer_text=footer,
            related_entity_type="approval",
            related_entity_id=approval_id,
            approval_id=approval_id,
        )

        # Log the approval sent event
        self.event_repository.save(
            aggregate_type="approval",
            aggregate_id=approval_id,
            event_type=WHATSAPP_APPROVAL_SENT,
            payload={"phone": phone_number, "risk_level": risk_level},
        )

        return result

    def process_approval_vote(self, session_id: str, approval_id: str,
                              vote: str, vote_source: str = "whatsapp_button",
                              confidence: float = None, reason: str = None,
                              message_id: str = None) -> dict:
        """Process an approval vote received via WhatsApp.

        Validates the vote and applies it to the approval state machine.
        CRITICAL: Only HUMAN users can approve/reject — never AI agents.
        """
        # Verify the approval exists and is in a votable state
        approval = self.approval_repository.get_by_id(approval_id)
        if not approval:
            return {"status": "error", "detail": "Approval request not found"}

        current_state = approval.get("current_state", "")
        if current_state not in ("awaiting_approval", "queued_for_review", "proposed"):
            return {
                "status": "error",
                "detail": f"Approval is in state '{current_state}' — cannot accept votes",
            }

        # Validate vote type
        valid_votes = {"approve", "reject", "escalate", "defer"}
        if vote not in valid_votes:
            return {"status": "error", "detail": f"Invalid vote: {vote}. Must be one of {valid_votes}"}

        # Record the vote
        vote_record = self.repository.create_approval_vote(
            session_id=session_id,
            approval_id=approval_id,
            vote=vote,
            vote_source=vote_source,
            confidence=confidence,
            reason=reason,
            message_id=message_id,
        )

        # Apply the vote to the approval state machine
        try:
            if vote == "approve":
                self.approval_repository.approve(approval_id, decided_by=None, reason=reason or "Approved via WhatsApp")
            elif vote == "reject":
                self.approval_repository.reject(approval_id, decided_by=None, reason=reason or "Rejected via WhatsApp")
            elif vote == "escalate":
                self.approval_repository.escalate(approval_id, reason=reason or "Escalated via WhatsApp")
            elif vote == "defer":
                # Defer just keeps the approval in current state
                pass

            # Mark vote as processed
            self.repository.mark_vote_processed(vote_record["id"])

            self.event_repository.save(
                aggregate_type="whatsapp_approval_vote",
                aggregate_id=vote_record["id"],
                event_type=WHATSAPP_APPROVAL_VOTE_PROCESSED,
                payload={"approval_id": approval_id, "vote": vote, "source": vote_source},
            )

            return {"status": "success", "vote": vote, "approval_id": approval_id}

        except Exception as e:
            self.repository.mark_vote_processed(vote_record["id"], error_message=str(e))
            return {"status": "error", "detail": str(e)}

    # ── Webhook Processing ──────────────────────────────────────

    def verify_webhook(self, mode: str, token: str, challenge: str) -> str | None:
        """Verify WhatsApp webhook subscription.

        Meta sends a GET request with hub.mode, hub.verify_token, and hub.challenge.
        We must verify the token and return the challenge.
        """
        if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
            logger.info("WhatsApp webhook verified successfully")
            return challenge
        logger.warning("WhatsApp webhook verification failed")
        return None

    async def process_webhook(self, payload: dict) -> dict:
        """Process incoming webhook payload from WhatsApp.

        Handles:
        - Inbound text messages
        - Interactive button responses (approval votes)
        - Message status updates (sent, delivered, read, failed)
        - Opt-in/opt-out signals
        """
        results = []

        try:
            entry_list = payload.get("entry", [])
            for entry in entry_list:
                changes = entry.get("changes", [])
                for change in changes:
                    value = change.get("value", "")

                    # Process messages
                    messages = value.get("messages", [])
                    for msg in messages:
                        result = await self._process_inbound_message(msg)
                        results.append(result)

                    # Process status updates
                    statuses = value.get("statuses", [])
                    for status_update in statuses:
                        result = self._process_status_update(status_update)
                        results.append(result)

        except Exception as e:
            logger.error(f"Error processing WhatsApp webhook: {e}")
            return {"status": "error", "detail": str(e)}

        return {"status": "processed", "results": results}

    async def _process_inbound_message(self, msg: dict) -> dict:
        """Process a single inbound WhatsApp message."""
        phone_number = msg.get("from", "")
        whatsapp_msg_id = msg.get("id", "")
        msg_type = msg.get("type", "text")
        timestamp = msg.get("timestamp", "")

        # Get or create session
        session = self.repository.get_or_create_session(phone_number)

        # Handle different message types
        content_body = None
        interactive_payload = None
        related_entity_type = None
        related_entity_id = None
        approval_id = None

        if msg_type == "text":
            content_body = msg.get("text", {}).get("body", "")

            # Check if this is a natural language approval vote
            vote_result = self._parse_text_vote(content_body)
            if vote_result:
                # This text message is an approval vote
                approval_id = vote_result.get("approval_id")
                if approval_id:
                    self.process_approval_vote(
                        session_id=session["id"],
                        approval_id=approval_id,
                        vote=vote_result["vote"],
                        vote_source="whatsapp_text",
                        confidence=vote_result.get("confidence", 0.7),
                        reason=content_body,
                    )

        elif msg_type == "interactive":
            interactive = msg.get("interactive", {})
            interactive_type = interactive.get("type", "")

            if interactive_type == "button_reply":
                button_id = interactive.get("button_reply", {}).get("id", "")
                button_title = interactive.get("button_reply", {}).get("title", "")
                content_body = f"[Button: {button_title}]"
                interactive_payload = {"button_id": button_id, "button_title": button_title}

                # Parse approval vote from button
                vote_result = self._parse_button_vote(button_id)
                if vote_result:
                    approval_id = vote_result.get("approval_id")
                    if approval_id:
                        self.process_approval_vote(
                            session_id=session["id"],
                            approval_id=approval_id,
                            vote=vote_result["vote"],
                            vote_source="whatsapp_button",
                            confidence=1.0,  # Button votes have high confidence
                        )

            elif interactive_type == "list_reply":
                list_id = interactive.get("list_reply", {}).get("id", "")
                list_title = interactive.get("list_reply", {}).get("title", "")
                content_body = f"[List: {list_title}]"
                interactive_payload = {"list_id": list_id, "list_title": list_title}

        # Record the inbound message
        message = self.repository.create_message(
            session_id=session["id"],
            direction="inbound",
            message_type=msg_type,
            content_body=content_body,
            interactive_type=interactive_payload and "button",
            interactive_payload=interactive_payload,
            whatsapp_message_id=whatsapp_msg_id,
            sender_phone=phone_number,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            approval_id=approval_id,
        )

        # Log event
        self.event_repository.save(
            aggregate_type="whatsapp_message",
            aggregate_id=message["id"],
            event_type=WHATSAPP_MESSAGE_RECEIVED,
            payload={"phone": phone_number, "type": msg_type},
        )

        return message

    def _process_status_update(self, status_update: dict) -> dict:
        """Process a message status update from WhatsApp."""
        whatsapp_msg_id = status_update.get("id", "")
        status = status_update.get("status", "")
        timestamp = status_update.get("timestamp", "")
        error_code = None
        error_message = None

        if status == "failed":
            errors = status_update.get("errors", [])
            if errors:
                error_code = str(errors[0].get("code", ""))
                error_message = errors[0].get("message", "")

        # Find and update the message
        msg = self.repository.get_message_by_whatsapp_id(whatsapp_msg_id)
        if not msg:
            return {"status": "ignored", "detail": f"Message {whatsapp_msg_id} not found"}

        now = datetime.now(timezone.utc)
        update_kwargs = {"status": status}
        if status == "delivered":
            update_kwargs["delivered_at"] = now
            event_type = WHATSAPP_MESSAGE_DELIVERED
        elif status == "read":
            update_kwargs["read_at"] = now
            event_type = WHATSAPP_MESSAGE_READ
        elif status == "failed":
            update_kwargs["error_code"] = error_code
            update_kwargs["error_message"] = error_message
            event_type = WHATSAPP_MESSAGE_FAILED
        else:
            event_type = WHATSAPP_MESSAGE_SENT

        self.repository.update_message_status(msg["id"], status, **update_kwargs)

        self.event_repository.save(
            aggregate_type="whatsapp_message",
            aggregate_id=msg["id"],
            event_type=event_type,
            payload={"status": status, "whatsapp_id": whatsapp_msg_id},
        )

        return {"status": "updated", "message_id": msg["id"], "new_status": status}

    # ── Vote Parsing ────────────────────────────────────────────

    def _parse_button_vote(self, button_id: str) -> dict | None:
        """Parse a button response into an approval vote.

        Button ID format: "approve:{approval_id}" or "reject:{approval_id}"
        """
        parts = button_id.split(":", 1)
        if len(parts) == 2 and parts[0] in ("approve", "reject", "escalate", "defer"):
            return {"vote": parts[0], "approval_id": parts[1]}
        return None

    def _parse_text_vote(self, text: str) -> dict | None:
        """Parse a natural language text message into an approval vote.

        Supports patterns like:
        - "approve abc123"
        - "reject the proposal"
        - "yes approve"
        - "no reject it"

        NOTE: Text votes have lower confidence than button votes.
        NLP parsing should be replaced with proper intent detection in production.
        """
        text_lower = text.lower().strip()
        vote = None

        # Check for vote keywords
        if any(kw in text_lower for kw in ("approve", "yes", "confirm", "go ahead", "proceed")):
            vote = "approve"
        elif any(kw in text_lower for kw in ("reject", "no", "deny", "decline", "cancel")):
            vote = "reject"
        elif any(kw in text_lower for kw in ("escalate", "escalation", "escalate it")):
            vote = "escalate"

        if not vote:
            return None

        # Try to extract approval ID from text (UUID pattern)
        import re
        uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        match = re.search(uuid_pattern, text_lower)
        approval_id = match.group(0) if match else None

        if not approval_id:
            # Look for short ID (first 8 chars)
            short_id_pattern = r'\b[0-9a-f]{8}\b'
            match = re.search(short_id_pattern, text_lower)
            if match:
                # Find matching approval by prefix
                # This is a fallback — in production, use proper intent parsing
                approval_id = None

        return {
            "vote": vote,
            "approval_id": approval_id,
            "confidence": 0.6,  # Text votes are less confident than button votes
        }

    # ── Session Management ──────────────────────────────────────

    def get_session(self, session_id: str) -> dict | None:
        return self.repository.get_session_by_id(session_id)

    def get_session_by_phone(self, phone_number: str) -> dict | None:
        return self.repository.get_session_by_phone(phone_number)

    def list_sessions(self, status: str = None, limit: int = 50, offset: int = 0) -> list[dict]:
        return self.repository.list_sessions(status, limit, offset)

    def opt_in(self, session_id: str) -> dict | None:
        result = self.repository.opt_in_session(session_id)
        if result:
            self.event_repository.save(
                aggregate_type="whatsapp_session",
                aggregate_id=session_id,
                event_type=WHATSAPP_SESSION_OPTED_IN,
                payload={"phone": result.get("phone_number")},
            )
        return result

    def opt_out(self, session_id: str) -> dict | None:
        result = self.repository.opt_out_session(session_id)
        if result:
            self.event_repository.save(
                aggregate_type="whatsapp_session",
                aggregate_id=session_id,
                event_type=WHATSAPP_SESSION_OPTED_OUT,
                payload={"phone": result.get("phone_number")},
            )
        return result

    # ── Template Management ──────────────────────────────────────

    def create_template(self, name: str, category: str, language: str,
                        body_text: str, **kwargs) -> dict:
        return self.repository.create_template(name, category, language, body_text, **kwargs)

    def list_templates(self, status: str = None, limit: int = 50) -> list[dict]:
        return self.repository.list_templates(status, limit)

    def get_template(self, name: str, language: str = "en") -> dict | None:
        return self.repository.get_template(name, language)

    # ── Message History ──────────────────────────────────────────

    def get_session_messages(self, session_id: str, limit: int = 50, offset: int = 0) -> list[dict]:
        return self.repository.get_session_messages(session_id, limit, offset)

    def get_approval_messages(self, approval_id: str) -> list[dict]:
        return self.repository.get_pending_approval_messages(approval_id)

    def get_approval_votes(self, approval_id: str) -> list[dict]:
        return self.repository.get_approval_votes(approval_id)

    # ── Seed Default Templates ──────────────────────────────────

    def seed_default_templates(self):
        """Seed the database with default WhatsApp templates."""
        templates = [
            {
                "name": "approval_request",
                "category": "UTILITY",
                "language": "en",
                "body_text": "You have a new approval request: {{1}}. Risk level: {{2}}. Please review and respond.",
                "header_type": "text",
                "header_text": "Approval Required",
                "footer_text": "Havilah OS",
                "button_type": "quick_reply",
                "button_payload": [
                    {"type": "reply", "id": "approve", "title": "Approve"},
                    {"type": "reply", "id": "reject", "title": "Reject"},
                ],
            },
            {
                "name": "approval_reminder",
                "category": "UTILITY",
                "language": "en",
                "body_text": "Reminder: Approval pending for '{{1}}'. Risk: {{2}}. Please respond.",
                "header_type": "text",
                "header_text": "Approval Reminder",
                "footer_text": "Havilah OS",
            },
            {
                "name": "briefing_summary",
                "category": "UTILITY",
                "language": "en",
                "body_text": "Your morning briefing: {{1}} projects active, {{2}} tasks pending, {{3}} approvals awaiting. Summary: {{4}}",
                "header_type": "text",
                "header_text": "Morning Briefing",
                "footer_text": "Havilah OS",
            },
            {
                "name": "task_overdue",
                "category": "UTILITY",
                "language": "en",
                "body_text": "Task '{{1}}' is overdue. Due date: {{2}}. Priority: {{3}}.",
                "header_type": "text",
                "header_text": "Task Overdue",
                "footer_text": "Havilah OS",
            },
            {
                "name": "execution_result",
                "category": "UTILITY",
                "language": "en",
                "body_text": "Action '{{1}}' has been {{2}}. {{3}}",
                "header_type": "text",
                "header_text": "Execution Result",
                "footer_text": "Havilah OS",
            },
            {
                "name": "opt_in_confirmation",
                "category": "UTILITY",
                "language": "en",
                "body_text": "You have been opted in to Havilah OS WhatsApp notifications. Reply STOP to opt out anytime.",
                "header_type": "text",
                "header_text": "Havilah OS",
                "footer_text": "Reply STOP to unsubscribe",
            },
        ]

        for tmpl in templates:
            existing = self.repository.get_template(tmpl["name"], tmpl["language"])
            if not existing:
                self.repository.create_template(**tmpl)
                logger.info(f"Created WhatsApp template: {tmpl['name']}")
