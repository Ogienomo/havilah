"""
Havilah OS — Structured Logging Configuration

Provides structured JSON logging for production and human-readable
logging for development. All log entries include:
- timestamp (ISO 8601)
- level
- logger name
- message
- request_id (if available)
- user_id (if available)
- extra fields (context)

Usage:
    from backend.core.logging_config import get_logger
    logger = get_logger("havilah.approval")
    logger.info("Approval created", extra={"approval_id": "123", "risk_level": "high"})
"""

import logging
import json
import sys
from datetime import datetime, timezone
from typing import Any


class JSONFormatter(logging.Formatter):
    """Structured JSON log formatter for production."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add request context if available
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        if hasattr(record, "role"):
            log_entry["role"] = record.role

        # Add extra fields
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Merge any extra dict fields
        if hasattr(record, "extra_fields"):
            log_entry.update(record.extra_fields)

        return json.dumps(log_entry, default=str)


class DevFormatter(logging.Formatter):
    """Human-readable formatter for development."""

    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")

        prefix = f"{color}{record.levelname:8s}{self.RESET}"
        context = ""
        if hasattr(record, "request_id"):
            context += f" [req:{record.request_id[:8]}]"
        if hasattr(record, "user_id"):
            context += f" [user:{record.user_id[:8]}]"

        msg = f"{timestamp} {prefix} {record.name}{context}: {record.getMessage()}"

        if record.exc_info and record.exc_info[0] is not None:
            msg += "\n" + self.formatException(record.exc_info)

        return msg


def configure_logging(environment: str = "development", level: str = "INFO") -> None:
    """Configure logging based on environment.

    Args:
        environment: 'development' for colored human-readable logs,
                     'production' for structured JSON logs.
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    root_logger = logging.getLogger("havilah")

    # Remove existing handlers
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)

    if environment == "production":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(DevFormatter())

    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    root_logger.info(f"Logging configured: environment={environment}, level={level}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger under the 'havilah' namespace.

    Usage:
        logger = get_logger("havilah.approval")
        logger.info("Approval created", extra={"approval_id": "123"})
    """
    if not name.startswith("havilah"):
        name = f"havilah.{name}"
    return logging.getLogger(name)
