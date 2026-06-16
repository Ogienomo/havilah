"""
Havilah OS — WhatsApp API

Endpoints for WhatsApp Business API integration:
- Webhook (GET/POST) for Meta verification and incoming messages
- Message sending
- Session management
- Template management
- Approval flow via WhatsApp

Core principle: WhatsApp approval votes are recorded in the Approval Ledger.
No action executes without passing through the 7+2 state machine.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from backend.api.auth import require_auth, require_admin
from backend.api.middleware import RequirePermission
from backend.config.settings import get_settings
from backend.services.whatsapp_service import WhatsAppService

logger = logging.getLogger("havilah.whatsapp")
settings = get_settings()

router = APIRouter(prefix="/api/whatsapp", tags=["WhatsApp"])


# ── Pydantic Schemas ──────────────────────────────────────────

class SendMessageRequest(BaseModel):
    phone_number: str = Field(..., min_length=1, description="Recipient phone number in international format")
    message: str = Field(..., min_length=1, max_length=4096, description="Message text")

class SendTemplateRequest(BaseModel):
    phone_number: str = Field(..., min_length=1)
    template_name: str = Field(..., min_length=1)
    parameters: Optional[list[str]] = None
    language: str = "en"

class SendApprovalRequest(BaseModel):
    approval_id: str = Field(..., min_length=1, description="ID of the approval request to send")
    phone_number: str = Field(..., min_length=1, description="Recipient phone number")

class InteractiveButton(BaseModel):
    id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=20)

class SendInteractiveRequest(BaseModel):
    phone_number: str = Field(..., min_length=1)
    body_text: str = Field(..., min_length=1, max_length=1024)
    buttons: list[InteractiveButton] = Field(..., min_length=1, max_length=3)
    header_text: Optional[str] = None
    footer_text: Optional[str] = None
    approval_id: Optional[str] = None

class OptInRequest(BaseModel):
    session_id: str = Field(..., min_length=1)

class OptOutRequest(BaseModel):
    session_id: str = Field(..., min_length=1)

class CreateTemplateRequest(BaseModel):
    name: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)  # AUTHENTICATION, MARKETING, UTILITY
    language: str = "en"
    body_text: str = Field(..., min_length=1)
    header_type: Optional[str] = None
    header_text: Optional[str] = None
    footer_text: Optional[str] = None
    button_type: Optional[str] = None
    button_payload: Optional[list[dict]] = None


# ── Webhook Endpoints ─────────────────────────────────────────
# These are called by Meta's WhatsApp Business API servers.
# They must NOT require authentication.

@router.get("/webhook")
def webhook_verification(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """
    WhatsApp webhook verification (GET).
    Meta sends this when subscribing to the webhook.
    Must respond with the challenge string.
    """
    service = WhatsAppService()
    result = service.verify_webhook(hub_mode, hub_verify_token, hub_challenge)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Webhook verification failed",
        )
    return int(result)  # Meta expects the challenge as a number


@router.post("/webhook")
async def webhook_receiver(request: Request):
    """
    WhatsApp webhook receiver (POST).
    Receives all events from WhatsApp: messages, status updates, errors.

    Incoming text messages are ALSO routed through the Hermes bridge
    so users can give natural language instructions via WhatsApp.
    """
    payload = await request.json()

    # Log the raw payload for debugging (strip sensitive data in production)
    logger.info(f"WhatsApp webhook received: {str(payload)[:500]}")

    service = WhatsAppService()
    result = await service.process_webhook(payload)

    # ── Route inbound text messages through Hermes bridge ────
    # This lets users control Hermes directly from WhatsApp:
    # "Create a project for X" / "approve" / "status" / "help"
    if settings.HERMES_ENABLED and settings.OPENAI_API_KEY:
        try:
            await _route_to_hermes(payload)
        except Exception as e:
            logger.warning(f"Hermes bridge routing failed: {e}")

    # Meta expects a 200 OK response quickly
    return {"status": "received", "detail": result}


async def _route_to_hermes(payload: dict):
    """Extract inbound text messages and route them to the Hermes WhatsApp bridge."""
    from backend.hermes.whatsapp_bridge import WhatsAppBridge

    bridge = WhatsAppBridge()

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            messages = value.get("messages", [])
            for msg in messages:
                if msg.get("type") != "text":
                    continue

                phone_number = msg.get("from", "")
                text_body = msg.get("text", {}).get("body", "")
                message_id = msg.get("id")

                if not phone_number or not text_body:
                    continue

                # Skip messages from the bot itself
                contacts = value.get("contacts", [])
                if contacts:
                    wa_id = contacts[0].get("wa_id", "")
                    if wa_id == settings.WHATSAPP_PHONE_NUMBER_ID:
                        continue

                logger.info(f"Routing WhatsApp message to Hermes: '{text_body[:60]}'")
                bridge.process_incoming_message(
                    phone_number=phone_number,
                    message_text=text_body,
                    message_id=message_id,
                )


# ── Message Sending ──────────────────────────────────────────

@router.post("/send/text")
async def send_text_message(
    payload: SendMessageRequest,
    user: dict = Depends(RequirePermission("whatsapp:send_message")),
):
    """Send a text message via WhatsApp."""
    service = WhatsAppService()
    result = await service.send_text_message(
        phone_number=payload.phone_number,
        text=payload.message,
    )
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("detail"))
    return result


@router.post("/send/template")
async def send_template_message(
    payload: SendTemplateRequest,
    user: dict = Depends(RequirePermission("whatsapp:send_message")),
):
    """Send a template message via WhatsApp."""
    service = WhatsAppService()
    result = await service.send_template_message(
        phone_number=payload.phone_number,
        template_name=payload.template_name,
        parameters=payload.parameters,
        language=payload.language,
    )
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("detail"))
    return result


@router.post("/send/interactive")
async def send_interactive_message(
    payload: SendInteractiveRequest,
    user: dict = Depends(RequirePermission("whatsapp:send_message")),
):
    """Send an interactive message with buttons via WhatsApp."""
    service = WhatsAppService()
    result = await service.send_interactive_message(
        phone_number=payload.phone_number,
        body_text=payload.body_text,
        buttons=[b.model_dump() for b in payload.buttons],
        header_text=payload.header_text,
        footer_text=payload.footer_text,
        approval_id=payload.approval_id,
    )
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("detail"))
    return result


# ── Approval Flow ────────────────────────────────────────────

@router.post("/send/approval")
async def send_approval_request(
    payload: SendApprovalRequest,
    user: dict = Depends(RequirePermission("whatsapp:send_approval")),
):
    """
    Send an approval request to a WhatsApp user with Approve/Reject/Escalate buttons.

    This is the primary entry point for the WhatsApp approval flow.
    The approval request must already exist in the Approval Ledger.
    The message sent includes interactive buttons that the user can tap to respond.
    """
    service = WhatsAppService()
    result = await service.send_approval_request(
        approval_id=payload.approval_id,
        phone_number=payload.phone_number,
    )
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("detail"))
    return result


@router.get("/approval/{approval_id}/votes")
def get_approval_votes(
    approval_id: str,
    user: dict = Depends(RequirePermission("whatsapp:read_messages")),
):
    """Get all WhatsApp votes for an approval request."""
    service = WhatsAppService()
    return service.get_approval_votes(approval_id)


@router.get("/approval/{approval_id}/messages")
def get_approval_messages(
    approval_id: str,
    user: dict = Depends(RequirePermission("whatsapp:read_messages")),
):
    """Get all WhatsApp messages related to an approval request."""
    service = WhatsAppService()
    return service.get_approval_messages(approval_id)


# ── Session Management ──────────────────────────────────────

@router.get("/sessions")
def list_sessions(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: dict = Depends(RequirePermission("whatsapp:manage_sessions")),
):
    """List WhatsApp sessions."""
    service = WhatsAppService()
    return service.list_sessions(status=status_filter, limit=limit, offset=offset)


@router.get("/sessions/{session_id}")
def get_session(
    session_id: str,
    user: dict = Depends(RequirePermission("whatsapp:manage_sessions")),
):
    """Get a WhatsApp session by ID."""
    service = WhatsAppService()
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/sessions/phone/{phone_number}")
def get_session_by_phone(
    phone_number: str,
    user: dict = Depends(RequirePermission("whatsapp:manage_sessions")),
):
    """Get a WhatsApp session by phone number."""
    service = WhatsAppService()
    session = service.get_session_by_phone(phone_number)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/sessions/opt-in")
def opt_in(
    payload: OptInRequest,
    user: dict = Depends(RequirePermission("whatsapp:manage_sessions")),
):
    """Opt a session in to WhatsApp notifications."""
    service = WhatsAppService()
    result = service.opt_in(payload.session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")
    return result


@router.post("/sessions/opt-out")
def opt_out(
    payload: OptOutRequest,
    user: dict = Depends(RequirePermission("whatsapp:manage_sessions")),
):
    """Opt a session out of WhatsApp notifications."""
    service = WhatsAppService()
    result = service.opt_out(payload.session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")
    return result


@router.get("/sessions/{session_id}/messages")
def get_session_messages(
    session_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: dict = Depends(RequirePermission("whatsapp:read_messages")),
):
    """Get messages for a WhatsApp session."""
    service = WhatsAppService()
    return service.get_session_messages(session_id, limit=limit, offset=offset)


# ── Template Management ─────────────────────────────────────

@router.get("/templates")
def list_templates(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    user: dict = Depends(RequirePermission("whatsapp:manage_templates")),
):
    """List WhatsApp message templates."""
    service = WhatsAppService()
    return service.list_templates(status=status_filter, limit=limit)


@router.post("/templates")
def create_template(
    payload: CreateTemplateRequest,
    user: dict = Depends(RequirePermission("whatsapp:manage_templates")),
):
    """Create a new WhatsApp message template."""
    service = WhatsAppService()
    return service.create_template(
        name=payload.name,
        category=payload.category,
        language=payload.language,
        body_text=payload.body_text,
        header_type=payload.header_type,
        header_text=payload.header_text,
        footer_text=payload.footer_text,
        button_type=payload.button_type,
        button_payload=payload.button_payload,
    )


@router.get("/templates/{name}")
def get_template(
    name: str,
    language: str = Query("en"),
    user: dict = Depends(RequirePermission("whatsapp:manage_templates")),
):
    """Get a WhatsApp template by name."""
    service = WhatsAppService()
    template = service.get_template(name, language)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


# ── System Endpoints ─────────────────────────────────────────

@router.get("/status")
def whatsapp_status(user: dict = Depends(require_auth)):
    """Get WhatsApp integration status."""
    return {
        "enabled": settings.WHATSAPP_ENABLED,
        "api_version": settings.WHATSAPP_API_VERSION,
        "phone_number_id_configured": bool(settings.WHATSAPP_PHONE_NUMBER_ID),
        "access_token_configured": bool(settings.WHATSAPP_ACCESS_TOKEN),
        "webhook_url": settings.WHATSAPP_WEBHOOK_URL,
    }


@router.post("/seed-templates")
def seed_templates(user: dict = Depends(require_admin)):
    """Seed default WhatsApp templates (admin only)."""
    service = WhatsAppService()
    service.seed_default_templates()
    return {"status": "success", "message": "Default templates seeded"}
