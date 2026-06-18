"""
Havilah OS — Telegram Bot API Router

Endpoints:
- GET  /api/telegram/health       — public status check
- POST /api/telegram/webhook      — Telegram updates (no auth, secret-token verified)
- POST /api/telegram/send         — send a message (auth required)
- GET  /api/telegram/webhook-info — admin: view Telegram's view of our webhook
- POST /api/telegram/setup-webhook — admin: (re)register the webhook with Telegram
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from pydantic import BaseModel, Field

from backend.api.auth import require_auth, require_admin
from backend.api.middleware import RequirePermission
from backend.config.settings import get_settings
from backend.services.telegram_service import TelegramService

logger = logging.getLogger("havilah.telegram")
settings = get_settings()

router = APIRouter(prefix="/api/telegram", tags=["Telegram"])


# ── Pydantic Schemas ──────────────────────────────────────────

class SendMessageRequest(BaseModel):
    chat_id: int | str = Field(..., description="Telegram chat_id to send to")
    text: str = Field(..., min_length=1, max_length=4096)


class SetupWebhookRequest(BaseModel):
    public_url: str = Field(
        ...,
        description="Public HTTPS URL Telegram can reach, e.g. https://havilah-production.up.railway.app/api/telegram/webhook",
    )
    secret_token: Optional[str] = Field(
        default=None,
        description="Optional shared secret Telegram will send in X-Telegram-Bot-Api-Secret-Token header",
    )


# ── Public Endpoints ──────────────────────────────────────────

@router.get("/health")
def telegram_health():
    """Public health endpoint — does NOT require auth."""
    return {
        "enabled": settings.TELEGRAM_ENABLED,
        "bot_token_configured": bool(settings.TELEGRAM_BOT_TOKEN),
        "webhook_secret_configured": bool(settings.TELEGRAM_WEBHOOK_SECRET),
    }


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: Optional[str] = Header(default=None, alias="X-Telegram-Bot-Api-Secret-Token"),
):
    """
    Receive Telegram updates (messages, edited messages, callback queries).
    """
    payload: dict[str, Any] = await request.json()

    # Verify secret token if configured
    if settings.TELEGRAM_WEBHOOK_SECRET:
        if x_telegram_bot_api_secret_token != settings.TELEGRAM_WEBHOOK_SECRET:
            logger.warning(
                f"Telegram webhook rejected: bad secret token "
                f"(got: {bool(x_telegram_bot_api_secret_token)})"
            )
            raise HTTPException(status_code=403, detail="Invalid secret token")

    update_id = payload.get("update_id")
    logger.info(f"Telegram webhook update_id={update_id}")

    # Route to bridge (best-effort, never block the response)
    if settings.HERMES_ENABLED and settings.OPENAI_API_KEY:
        try:
            _route_to_hermes(payload)
        except Exception as e:
            logger.warning(f"Telegram→Hermes routing failed: {e}")

    return {"status": "received"}


def _route_to_hermes(payload: dict[str, Any]) -> None:
    """Pull the message out of a Telegram update and hand it to the bridge."""
    from backend.hermes.telegram_bridge import TelegramBridge

    bridge = TelegramBridge()

    message = payload.get("message") or payload.get("edited_message") or payload.get("channel_post")
    if not message:
        return

    chat = message.get("chat", {})
    chat_id = chat.get("id")
    text = message.get("text", "")
    sender = message.get("from", {}).get("first_name") or message.get("from", {}).get("username")
    message_id = message.get("message_id")

    if chat_id is None or not text:
        return

    # Ignore messages from the bot itself
    from_user = message.get("from", {})
    if from_user.get("is_bot"):
        return

    bridge.process_incoming_message(
        chat_id=chat_id,
        text=text,
        sender_name=sender,
        message_id=message_id,
    )


# ── Authenticated Endpoints ───────────────────────────────────

@router.post("/send")
async def send_message(
    payload: SendMessageRequest,
    user: dict = Depends(RequirePermission("telegram:send_message")),
):
    """Send a message to a Telegram chat (admin/operator only)."""
    service = TelegramService()
    result = service.send_message(chat_id=payload.chat_id, text=payload.text)
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("detail"))
    return result


@router.get("/webhook-info")
def webhook_info(user: dict = Depends(require_admin)):
    """Admin: see Telegram's view of our webhook."""
    service = TelegramService()
    return service.get_webhook_info()


@router.post("/setup-webhook")
def setup_webhook(
    payload: SetupWebhookRequest,
    user: dict = Depends(require_admin),
):
    """Admin: (re)register the webhook URL with Telegram."""
    service = TelegramService()
    result = service.set_webhook(
        webhook_url=payload.public_url,
        secret=payload.secret_token or settings.TELEGRAM_WEBHOOK_SECRET or None,
    )
    if result.get("status") == "error":
        raise HTTPException(status_code=502, detail=result.get("detail"))
    return {"status": "ok", "webhook_url": payload.public_url, "telegram_response": result.get("result")}
