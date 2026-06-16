"""
Havilah OS — Analytics API

Executive dashboard, approval analytics, project metrics, task stats,
agent performance, and memory insights.
All endpoints require authentication. Read-only for all roles.
"""

from fastapi import APIRouter, Depends

from backend.api.deps import get_analytics_service
from backend.api.middleware import RequirePermission
from backend.schemas.schemas import ExecutiveDashboardResponse
from backend.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/dashboard", response_model=ExecutiveDashboardResponse)
def executive_dashboard(
    user: dict = Depends(RequirePermission("analytics:dashboard")),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Full executive dashboard with all metrics."""
    return service.full_dashboard()


@router.get("/summary")
def executive_summary(
    user: dict = Depends(RequirePermission("analytics:read")),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """High-level executive summary."""
    return service.executive_summary()


# ── Approval Analytics ────────────────────────────────────────

@router.get("/approvals/counts")
def approval_counts(
    user: dict = Depends(RequirePermission("analytics:read")),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Approval counts by status."""
    return service.approval_counts()


@router.get("/approvals/average-time")
def average_approval_time(
    user: dict = Depends(RequirePermission("analytics:read")),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Average time from request to decision."""
    return {"average_hours": service.average_approval_time()}


@router.get("/approvals/execution-time")
def average_execution_time(
    user: dict = Depends(RequirePermission("analytics:read")),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Average execution time."""
    return {"average_seconds": service.average_execution_time()}


@router.get("/approvals/bottlenecks")
def approval_bottlenecks(
    limit: int = 10,
    user: dict = Depends(RequirePermission("analytics:read")),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Identify approval bottlenecks."""
    return service.approval_bottlenecks(limit)


# ── Project Analytics ─────────────────────────────────────────

@router.get("/projects/completion-rate")
def project_completion_rate(
    user: dict = Depends(RequirePermission("analytics:read")),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Project completion rate."""
    return service.project_completion_rate()


# ── Task Analytics ────────────────────────────────────────────

@router.get("/tasks/counts")
def task_counts(
    user: dict = Depends(RequirePermission("analytics:read")),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Task counts by status."""
    return service.task_counts()


@router.get("/tasks/overdue")
def overdue_tasks(
    user: dict = Depends(RequirePermission("analytics:read")),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """List overdue tasks."""
    return service.overdue_tasks()


# ── Agent Analytics ───────────────────────────────────────────

@router.get("/agents/success-rate")
def agent_success_rate(
    user: dict = Depends(RequirePermission("analytics:read")),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Agent run success rate."""
    return service.agent_success_rate()


@router.get("/agents/average-duration")
def average_agent_duration(
    user: dict = Depends(RequirePermission("analytics:read")),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Average agent run duration in milliseconds."""
    return {"average_ms": service.average_agent_duration()}


# ── Memory Analytics ──────────────────────────────────────────

@router.get("/memory/counts")
def memory_counts(
    user: dict = Depends(RequirePermission("analytics:read")),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Memory counts by type."""
    return service.memory_counts()
