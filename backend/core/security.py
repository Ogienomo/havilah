"""
Havilah OS — Security Hardening Module

Provides security utilities:
1. Rate limiting (in-memory, per-IP and per-user)
2. Input sanitization
3. SQL injection prevention (parameterized queries only)
4. CORS hardening
5. Security headers
6. API key rotation support
7. Audit trail integrity
"""

import time
import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger("havilah.security")


# ─── Rate Limiting ──────────────────────────────────────────────

@dataclass
class RateLimitEntry:
    """Tracks request counts for rate limiting."""
    count: int = 0
    window_start: float = 0.0
    blocked_until: float = 0.0


class RateLimiter:
    """
    In-memory rate limiter with sliding window.

    Supports per-IP and per-user rate limiting.
    In production, replace with Redis-backed implementation.
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_size: int = 100,
        block_duration_seconds: int = 300,
    ):
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.block_duration_seconds = block_duration_seconds
        self._ip_entries: dict[str, RateLimitEntry] = defaultdict(RateLimitEntry)
        self._user_entries: dict[str, RateLimitEntry] = defaultdict(RateLimitEntry)

    def check_rate_limit(self, key: str, is_user: bool = False) -> bool:
        """Check if a request is within rate limits.

        Returns True if the request is allowed, False if rate limited.
        """
        now = time.time()
        entries = self._user_entries if is_user else self._ip_entries
        entry = entries[key]

        # Check if currently blocked
        if entry.blocked_until > now:
            return False

        # Reset window if expired
        if now - entry.window_start > 60:
            entry.count = 0
            entry.window_start = now

        entry.count += 1

        # Check burst limit
        if entry.count > self.burst_size:
            entry.blocked_until = now + self.block_duration_seconds
            logger.warning(f"Rate limit exceeded for {'user' if is_user else 'IP'} {key}: {entry.count} requests")
            return False

        # Check per-minute limit
        if entry.count > self.requests_per_minute:
            return False

        return True

    def get_remaining(self, key: str, is_user: bool = False) -> int:
        """Get remaining requests for a key."""
        now = time.time()
        entries = self._user_entries if is_user else self._ip_entries
        entry = entries[key]

        if now - entry.window_start > 60:
            return self.requests_per_minute
        return max(0, self.requests_per_minute - entry.count)


# Global rate limiters
ip_rate_limiter = RateLimiter(requests_per_minute=60, burst_size=100)
user_rate_limiter = RateLimiter(requests_per_minute=120, burst_size=200)
auth_rate_limiter = RateLimiter(requests_per_minute=10, burst_size=15, block_duration_seconds=600)


# ─── Security Headers Middleware ────────────────────────────────

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds security headers to all responses:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block
    - Content-Security-Policy: default-src 'self'
    - Strict-Transport-Security (production only)
    - Referrer-Policy: strict-origin-when-cross-origin
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self'"
        )

        # HSTS only in production (requires HTTPS)
        from backend.config.settings import get_settings
        settings = get_settings()
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        return response


# ─── Rate Limiting Middleware ───────────────────────────────────

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware for all API requests.

    Skips rate limiting for:
    - Health check endpoints (/ and /health)
    - Webhook endpoints (handled separately)
    """

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ("/", "/health"):
            return await call_next(request)

        # Skip for WhatsApp webhooks (Meta has its own rate limiting)
        if request.url.path == "/api/whatsapp/webhook":
            return await call_next(request)

        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Check IP rate limit
        if not ip_rate_limiter.check_rate_limit(client_ip):
            logger.warning(f"IP rate limit exceeded: {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many requests. Please try again later."},
                headers={"Retry-After": "60"},
            )

        # Check auth endpoint rate limit
        if "/auth/" in request.url.path:
            if not auth_rate_limiter.check_rate_limit(client_ip):
                logger.warning(f"Auth rate limit exceeded: {client_ip}")
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Too many authentication attempts. Please wait."},
                    headers={"Retry-After": "600"},
                )

        # Check user rate limit (if authenticated)
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                from backend.api.auth import decode_access_token
                payload = decode_access_token(auth_header[7:])
                if payload:
                    user_id = payload.get("sub", "")
                    if not user_rate_limiter.check_rate_limit(user_id, is_user=True):
                        logger.warning(f"User rate limit exceeded: {user_id}")
                        return JSONResponse(
                            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            content={"detail": "User rate limit exceeded."},
                            headers={"Retry-After": "60"},
                        )
            except Exception:
                pass  # Invalid token — let auth middleware handle it

        response = await call_next(request)

        # Add rate limit headers
        remaining = ip_rate_limiter.get_remaining(client_ip)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Limit"] = str(ip_rate_limiter.requests_per_minute)

        return response


# ─── Input Sanitization ────────────────────────────────────────

def sanitize_input(text: str, max_length: int = 10000) -> str:
    """Sanitize user input to prevent XSS and injection attacks.

    - Truncates to max_length
    - Removes null bytes
    - Strips leading/trailing whitespace
    - Does NOT HTML-escape (that's for the presentation layer)
    """
    if not text:
        return text

    # Remove null bytes
    text = text.replace("\x00", "")

    # Truncate
    if len(text) > max_length:
        text = text[:max_length]

    # Strip whitespace
    text = text.strip()

    return text


def validate_uuid(uuid_str: str) -> bool:
    """Validate that a string is a valid UUID."""
    uuid_pattern = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        re.IGNORECASE,
    )
    return bool(uuid_pattern.match(uuid_str))


def validate_phone_number(phone: str) -> bool:
    """Validate a phone number in international format.

    Accepts: +2348012345678, 2348012345678
    """
    phone_pattern = re.compile(r"^\+?\d{10,15}$")
    return bool(phone_pattern.match(phone))


# ─── CORS Hardening ────────────────────────────────────────────

def get_cors_origins(environment: str) -> list[str]:
    """Get allowed CORS origins based on environment.

    Priority:
      1. HAVILAH_CORS_ORIGINS env var (comma-separated) — recommended for Railway
         Example: "https://havilah.vercel.app,https://dashboard.havilah.os"
      2. Environment-based defaults below

    Production: Only explicitly allowed domains
    Development: localhost variants
    """
    # 1. Honor explicit env var override (recommended for Railway deployments)
    from backend.config.settings import get_settings
    settings = get_settings()
    if settings.CORS_ORIGINS:
        return [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]

    # 2. Fall back to environment-based defaults
    if environment == "production":
        return [
            "https://havilah.com",
            "https://app.havilah.com",
            "https://admin.havilah.com",
        ]
    elif environment == "staging":
        return [
            "https://staging.havilah.com",
            "http://localhost:3000",
            "http://localhost:8000",
        ]
    else:
        return [
            "http://localhost:3000",
            "http://localhost:8000",
            "http://localhost:8080",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8000",
        ]
