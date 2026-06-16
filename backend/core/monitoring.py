"""
Havilah OS — Monitoring & Health Checks

Provides system health monitoring, metrics collection, and
readiness/liveness probes for container orchestration.

Health check categories:
1. Database connectivity
2. WhatsApp API connectivity
3. System resource usage
4. Application metrics (active sessions, pending approvals, etc.)
"""

import time
import psutil
import logging
from datetime import datetime, timezone
from typing import Optional

from backend.config.settings import get_settings
from backend.repositories.base import get_session

logger = logging.getLogger("havilah.monitoring")


class HealthChecker:
    """System health checker for Havilah OS."""

    def __init__(self):
        self.settings = get_settings()
        self._start_time = time.time()

    def check_database(self) -> dict:
        """Check database connectivity and response time."""
        try:
            start = time.perf_counter()
            with get_session() as db:
                db.execute("SELECT 1")
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            return {
                "status": "healthy",
                "latency_ms": latency_ms,
                "type": "postgresql",
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "type": "postgresql",
            }

    def check_whatsapp(self) -> dict:
        """Check WhatsApp API connectivity."""
        if not self.settings.WHATSAPP_ENABLED:
            return {
                "status": "disabled",
                "message": "WhatsApp integration is disabled",
            }

        if not self.settings.WHATSAPP_ACCESS_TOKEN:
            return {
                "status": "misconfigured",
                "message": "WhatsApp access token not configured",
            }

        return {
            "status": "configured",
            "api_version": self.settings.WHATSAPP_API_VERSION,
            "phone_number_id_set": bool(self.settings.WHATSAPP_PHONE_NUMBER_ID),
        }

    def check_system_resources(self) -> dict:
        """Check system resource usage."""
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            cpu_percent = psutil.cpu_percent(interval=0.1)

            return {
                "status": "healthy" if memory.percent < 90 else "warning",
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_gb": round(memory.used / (1024**3), 2),
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_used_gb": round(disk.used / (1024**3), 2),
                "disk_total_gb": round(disk.total / (1024**3), 2),
                "uptime_seconds": round(time.time() - self._start_time, 0),
            }
        except Exception as e:
            return {"status": "unknown", "error": str(e)}

    def check_application_metrics(self) -> dict:
        """Check application-level metrics."""
        try:
            with get_session() as db:
                from backend.models.user import User
                from backend.models.approval import ApprovalRequest
                from backend.models.whatsapp import WhatsAppSession

                user_count = db.query(User).count()
                pending_approvals = db.query(ApprovalRequest).filter(
                    ApprovalRequest.current_state.in_(
                        ["draft", "proposed", "queued_for_review", "awaiting_approval"]
                    )
                ).count()
                active_whatsapp_sessions = db.query(WhatsAppSession).filter(
                    WhatsAppSession.status == "active"
                ).count()

                return {
                    "status": "healthy",
                    "user_count": user_count,
                    "pending_approvals": pending_approvals,
                    "active_whatsapp_sessions": active_whatsapp_sessions,
                }
        except Exception as e:
            return {"status": "unknown", "error": str(e)}

    def full_health_check(self) -> dict:
        """Run all health checks and return a comprehensive report."""
        checks = {
            "database": self.check_database(),
            "whatsapp": self.check_whatsapp(),
            "system": self.check_system_resources(),
            "application": self.check_application_metrics(),
        }

        # Determine overall status
        statuses = [v.get("status") for v in checks.values()]
        if any(s == "unhealthy" for s in statuses):
            overall = "unhealthy"
        elif any(s in ("warning", "misconfigured") for s in statuses):
            overall = "degraded"
        else:
            overall = "healthy"

        return {
            "status": overall,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": self.settings.APP_VERSION,
            "environment": self.settings.ENVIRONMENT,
            "checks": checks,
        }


class MetricsCollector:
    """
    Lightweight in-process metrics collector.

    Tracks:
    - Request counts by endpoint and method
    - Response times by endpoint
    - Error rates
    - Approval flow metrics
    - WhatsApp message metrics
    """

    def __init__(self):
        self._request_counts: dict[str, int] = {}
        self._response_times: dict[str, list[float]] = {}
        self._error_counts: dict[str, int] = {}
        self._approval_metrics: dict[str, int] = {
            "created": 0,
            "approved": 0,
            "rejected": 0,
            "escalated": 0,
            "executed": 0,
            "failed": 0,
        }
        self._whatsapp_metrics: dict[str, int] = {
            "messages_sent": 0,
            "messages_received": 0,
            "messages_delivered": 0,
            "approval_votes": 0,
        }
        self._start_time = time.time()

    def record_request(self, method: str, path: str, duration_ms: float, status_code: int) -> None:
        """Record an API request."""
        key = f"{method} {path}"
        self._request_counts[key] = self._request_counts.get(key, 0) + 1

        if key not in self._response_times:
            self._response_times[key] = []
        self._response_times[key].append(duration_ms)
        # Keep only last 1000 entries per endpoint
        if len(self._response_times[key]) > 1000:
            self._response_times[key] = self._response_times[key][-500:]

        if status_code >= 400:
            error_key = f"{status_code} {path}"
            self._error_counts[error_key] = self._error_counts.get(error_key, 0) + 1

    def record_approval_event(self, event_type: str) -> None:
        """Record an approval state transition."""
        if event_type in self._approval_metrics:
            self._approval_metrics[event_type] += 1

    def record_whatsapp_event(self, event_type: str) -> None:
        """Record a WhatsApp event."""
        if event_type in self._whatsapp_metrics:
            self._whatsapp_metrics[event_type] += 1

    def get_metrics(self) -> dict:
        """Get current metrics snapshot."""
        # Calculate average response times
        avg_response_times = {}
        p95_response_times = {}
        for key, times in self._response_times.items():
            if times:
                avg_response_times[key] = round(sum(times) / len(times), 2)
                sorted_times = sorted(times)
                p95_idx = int(len(sorted_times) * 0.95)
                p95_response_times[key] = round(sorted_times[min(p95_idx, len(sorted_times) - 1)], 2)

        return {
            "uptime_seconds": round(time.time() - self._start_time, 0),
            "total_requests": sum(self._request_counts.values()),
            "request_counts": dict(sorted(self._request_counts.items(), key=lambda x: -x[1])[:20]),
            "avg_response_times_ms": avg_response_times,
            "p95_response_times_ms": p95_response_times,
            "error_counts": dict(sorted(self._error_counts.items(), key=lambda x: -x[1])[:10]),
            "approval_metrics": self._approval_metrics,
            "whatsapp_metrics": self._whatsapp_metrics,
        }


# Global metrics collector singleton
metrics = MetricsCollector()


def get_metrics() -> MetricsCollector:
    """Get the global metrics collector."""
    return metrics
