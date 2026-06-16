"""
Havilah OS — Analytics Service

Measures performance and provides insight across all bounded contexts.
"""

from backend.repositories.analytics_repository import AnalyticsRepository


class AnalyticsService:

    def __init__(self):
        self.repository = AnalyticsRepository()

    # ── Approval Analytics ────────────────────────────────────

    def approval_counts(self):
        return self.repository.approval_counts_by_status()

    def average_approval_time(self):
        return self.repository.average_approval_time_hours()

    def average_execution_time(self):
        return self.repository.average_execution_time_seconds()

    def approval_bottlenecks(self, limit=10):
        return self.repository.approval_bottlenecks(limit)

    # ── Project Analytics ─────────────────────────────────────

    def project_completion_rate(self):
        return self.repository.project_completion_rate()

    # ── Task Analytics ────────────────────────────────────────

    def task_counts(self):
        return self.repository.task_counts_by_status()

    def overdue_tasks(self):
        return self.repository.overdue_tasks()

    # ── Agent Analytics ───────────────────────────────────────

    def agent_success_rate(self):
        return self.repository.agent_success_rate()

    def average_agent_duration(self):
        return self.repository.average_agent_duration_ms()

    # ── Memory Analytics ──────────────────────────────────────

    def memory_counts(self):
        return self.repository.memory_counts_by_type()

    # ── Executive Dashboard ───────────────────────────────────

    def executive_summary(self):
        return self.repository.executive_summary()

    def full_dashboard(self):
        return {
            "executive_summary": self.executive_summary(),
            "approval_counts": self.approval_counts(),
            "project_completion_rate": self.project_completion_rate(),
            "task_counts": self.task_counts(),
            "overdue_tasks": self.overdue_tasks(),
            "agent_success_rate": self.agent_success_rate(),
            "memory_counts": self.memory_counts(),
        }
