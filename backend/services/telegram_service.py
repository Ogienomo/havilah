"""
Havilah OS — Telegram Bot API Service

Wraps the Telegram Bot API for sending messages and managing webhooks.
This service is intentionally lightweight — it does NOT contain business logic.
Business logic (instruction routing, approval flow) lives in
``backend.hermes.telegram_bridge``.

API docs: https://core.telegram.org/bots/api
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

from backend.config.settings import get_settings

logger = logging.getLogger("havilah.telegram_service")
settings = get_settings()


class TelegramService:
    """Thin wrapper around the Telegram Bot HTTP API."""

    BASE_URL = "https://api.telegram.org"

    def __init__(self) -> None:
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.enabled = bool(self.token) and settings.TELEGRAM_ENABLED

    # ── Webhook management ───────────────────────────────────

    def set_webhook(self, webhook_url: str, secret: Optional[str] = None) -> dict:
        """Tell Telegram to POST updates to ``webhook_url``."""
        if not self.enabled:
            return {"status": "error", "detail": "Telegram not enabled"}
        params: dict[str, Any] = {
            "url": webhook_url,
            "allowed_updates": ["message", "edited_message", "callback_query"],
            "drop_pending_updates": True,
        }
        if secret:
            params["secret_token"] = secret
        return self._call("setWebhook", params)

    def delete_webhook(self) -> dict:
        """Remove the current webhook (switches back to long-polling)."""
        if not self.enabled:
            return {"status": "error", "detail": "Telegram not enabled"}
        return self._call("deleteWebhook", {})

    def get_webhook_info(self) -> dict:
        """Return the current webhook state as Telegram sees it."""
        if not self.enabled:
            return {"status": "error", "detail": "Telegram not enabled"}
        return self._call("getWebhookInfo", {})

    # ── Messaging ────────────────────────────────────────────

    def send_message(
        self,
        chat_id: int | str,
        text: str,
        parse_mode: Optional[str] = "Markdown",
        reply_to_message_id: Optional[int] = None,
        disable_web_page_preview: bool = True,
    ) -> dict:
        """Send a plain text message to a chat."""
        if not self.enabled:
            return {"status": "error", "detail": "Telegram not enabled"}

        # Telegram message cap is 4096 chars. Truncate cleanly.
        if len(text) > 4000:
            text = text[:3990] + "\n\n…(truncated)"

        params: dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": disable_web_page_preview,
        }
        if parse_mode:
            params["parse_mode"] = parse_mode
        if reply_to_message_id:
            params["reply_to_message_id"] = reply_to_message_id

        return self._call("sendMessage", params)

    # ── Internal HTTP helper ─────────────────────────────────

    def _call(self, method: str, params: dict[str, Any]) -> dict:
        """Invoke a Telegram Bot API method."""
        url = f"{self.BASE_URL}/bot{self.token}/{method}"
        try:
            with httpx.Client(timeout=15.0) as client:
                if method in {"setWebhook", "deleteWebhook", "getWebhookInfo"}:
                    resp = client.get(url, params=params)
                else:
                    resp = client.post(url, json=params)
                resp.raise_for_status()
                data = resp.json()
            if not data.get("ok"):
                logger.error(f"Telegram API {method} returned not-ok: {data}")
                return {"status": "error", "detail": data}
            return {"status": "ok", "result": data.get("result", {})}
        except httpx.HTTPError as e:
            logger.error(f"Telegram HTTP {method} failed: {e}")
            return {"status": "error", "detail": str(e)}
        except Exception as e:
            logger.error(f"Telegram {method} unexpected error: {e}")
            return {"status": "error", "detail": str(e)}
