"""
Havilah OS Configuration Module

All credentials and environment-specific settings are loaded from
environment variables with sensible defaults for local development.
Never hardcode secrets in source code.
"""

import os
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger("havilah.config")

_INSECURE_PLACEHOLDERS = {"change-me-in-production", "change-me-verify-token", ""}


def _require_secret(value: str, name: str, environment: str) -> str:
    """Raise in production if a secret is missing or uses a placeholder value."""
    if environment == "production" and value in _INSECURE_PLACEHOLDERS:
        raise ValueError(
            f"[Havilah] FATAL: {name} must be set to a real secret in production. "
            f"Set the {name} environment variable."
        )
    if value in _INSECURE_PLACEHOLDERS:
        logger.warning(
            f"[Havilah] WARNING: {name} is using an insecure placeholder. "
            "Set a real value before deploying to production."
        )
    return value


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""

    # ── Database ──────────────────────────────────────────────
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "havilah"
    DB_USER: str = "havilah_app"
    DB_PASSWORD: str = ""
    DB_ECHO: bool = False  # Set True for SQL logging in dev

    # ── Application ───────────────────────────────────────────
    APP_NAME: str = "Havilah OS"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development | staging | production

    # ── Security ──────────────────────────────────────────────
    SECRET_KEY: str = ""
    API_KEY_SALT: str = ""

    # ── OpenAI / LLM ─────────────────────────────────────────
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_MAX_TOKENS: int = 4096
    OPENAI_TEMPERATURE: float = 0.7
    OPENAI_BASE_URL: str = ""  # Optional: custom endpoint/proxy for region-restricted access
    HERMES_ENABLED: bool = True  # Master switch for Hermes orchestration

    # ── CORS ────────────────────────────────────────────────
    # Comma-separated list of allowed CORS origins for the dashboard.
    # Example: "https://havilah.vercel.app,https://dashboard.havilah.os"
    # If empty, falls back to environment-based defaults (see core/security.py).
    CORS_ORIGINS: str = ""

    # ── WhatsApp Business API ─────────────────────────────────
    WHATSAPP_VERIFY_TOKEN: str = ""
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_BUSINESS_ACCOUNT_ID: str = ""
    WHATSAPP_API_VERSION: str = "v21.0"
    WHATSAPP_WEBHOOK_URL: str = "/api/whatsapp/webhook"
    WHATSAPP_ENABLED: bool = False  # Enable/disable WhatsApp integration

    # ── Telegram Bot API ──────────────────────────────────────
    # Get token from @BotFather → /newbot
    TELEGRAM_BOT_TOKEN: str = ""
    # Optional shared secret — Telegram will send it back in the
    # X-Telegram-Bot-Api-Secret-Token header on every webhook call.
    # Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
    TELEGRAM_WEBHOOK_SECRET: str = ""
    TELEGRAM_ENABLED: bool = False  # Master switch — set true once token is configured

    # ── Derived ───────────────────────────────────────────────
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg2://"
            f"{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://"
            f"{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


def get_settings() -> Settings:
    """Build Settings from environment variables."""
    env = os.getenv("HAVILAH_ENV", "development")

    db_password = _require_secret(
        os.getenv("HAVILAH_DB_PASSWORD", ""), "HAVILAH_DB_PASSWORD", env
    )
    secret_key = _require_secret(
        os.getenv("HAVILAH_SECRET_KEY", ""), "HAVILAH_SECRET_KEY", env
    )
    api_key_salt = _require_secret(
        os.getenv("HAVILAH_API_KEY_SALT", ""), "HAVILAH_API_KEY_SALT", env
    )
    # Only validate WhatsApp verify token if WhatsApp is enabled
    whatsapp_enabled = os.getenv("HAVILAH_WHATSAPP_ENABLED", "false").lower() == "true"
    whatsapp_verify_token = os.getenv("HAVILAH_WHATSAPP_VERIFY_TOKEN", "")
    if whatsapp_enabled:
        _require_secret(whatsapp_verify_token, "HAVILAH_WHATSAPP_VERIFY_TOKEN", env)

    return Settings(
        DB_HOST=os.getenv("HAVILAH_DB_HOST", "localhost"),
        DB_PORT=int(os.getenv("HAVILAH_DB_PORT", "5432")),
        DB_NAME=os.getenv("HAVILAH_DB_NAME", "havilah"),
        DB_USER=os.getenv("HAVILAH_DB_USER", "havilah_app"),
        DB_PASSWORD=db_password,
        DB_ECHO=os.getenv("HAVILAH_DB_ECHO", "false").lower() == "true",
        APP_NAME=os.getenv("HAVILAH_APP_NAME", "Havilah OS"),
        APP_VERSION=os.getenv("HAVILAH_APP_VERSION", "0.1.0"),
        DEBUG=os.getenv("HAVILAH_DEBUG", "false").lower() == "true",
        ENVIRONMENT=env,
        SECRET_KEY=secret_key,
        API_KEY_SALT=api_key_salt,
        OPENAI_API_KEY=os.getenv("HAVILAH_OPENAI_API_KEY", ""),
        OPENAI_MODEL=os.getenv("HAVILAH_OPENAI_MODEL", "gpt-4o"),
        OPENAI_MAX_TOKENS=int(os.getenv("HAVILAH_OPENAI_MAX_TOKENS", "4096")),
        OPENAI_TEMPERATURE=float(os.getenv("HAVILAH_OPENAI_TEMPERATURE", "0.7")),
        OPENAI_BASE_URL=os.getenv("HAVILAH_OPENAI_BASE_URL", ""),
        HERMES_ENABLED=os.getenv("HAVILAH_HERMES_ENABLED", "true").lower() == "true",
        CORS_ORIGINS=os.getenv("HAVILAH_CORS_ORIGINS", ""),
        WHATSAPP_VERIFY_TOKEN=whatsapp_verify_token,
        WHATSAPP_ACCESS_TOKEN=os.getenv("HAVILAH_WHATSAPP_ACCESS_TOKEN", ""),
        WHATSAPP_PHONE_NUMBER_ID=os.getenv("HAVILAH_WHATSAPP_PHONE_NUMBER_ID", ""),
        WHATSAPP_BUSINESS_ACCOUNT_ID=os.getenv("HAVILAH_WHATSAPP_BUSINESS_ACCOUNT_ID", ""),
        WHATSAPP_API_VERSION=os.getenv("HAVILAH_WHATSAPP_API_VERSION", "v21.0"),
        WHATSAPP_WEBHOOK_URL=os.getenv("HAVILAH_WHATSAPP_WEBHOOK_URL", "/api/whatsapp/webhook"),
        WHATSAPP_ENABLED=whatsapp_enabled,
        TELEGRAM_BOT_TOKEN=os.getenv("HAVILAH_TELEGRAM_BOT_TOKEN", ""),
        TELEGRAM_WEBHOOK_SECRET=os.getenv("HAVILAH_TELEGRAM_WEBHOOK_SECRET", ""),
        TELEGRAM_ENABLED=os.getenv("HAVILAH_TELEGRAM_ENABLED", "false").lower() == "true",
    )
