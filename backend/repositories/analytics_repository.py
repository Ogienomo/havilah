"""
Havilah OS — Analytics Repository

Answers:
  - How many approvals?
  - Average execution time?
  - Project completion rate?
  - Agent success rate?
  - Approval bottlenecks?
"""

from sqlalchemy import text
from backend.repositories.base import get_session


class AnalyticsRepository:

    # ── Approval Analytics ────────────────────────────────────

    def approval_counts_by_status(self) -> list:
        with get_session() as db:
            result = db.execute(text("""
                SELECT status, COUNT(*) AS count
                FROM approval_requests
                GROUP BY status
                ORDER BY count DESC
            """))
            return [dict(row._mapping) for row in result]

    def average_approval_time_hours(self) -> float:
        """Average time from request creation to approval (in hours)."""
        with get_session() as db:
            result = db.execute(text("""
                SELECT AVG(EXTRACT(EPOCH FROM (d.decided_at - r.created_at)) / 3600) AS avg_hours
                FROM approval_requests r
                JOIN approval_decisions d ON d.approval_request_id = r.id
                WHERE d.decision_type = 'approve'
            """))
            row = result.fetchone()
            return float(row[0]) if row and row[0] else 0.0

    def average_execution_time_seconds(self) -> float:
        """Average time from execution start to completion (in seconds)."""
        with get_session() as db:
            result = db.execute(text("""
                SELECT AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) AS avg_seconds
                FROM execution_records
                WHERE execution_status = 'completed' AND started_at IS NOT NULL AND completed_at IS NOT NULL
            """))
            row = result.fetchone()
            return float(row[0]) if row and row[0] else 0.0

    def approval_bottlenecks(self, limit=10) -> list:
        """Find approvals that took the longest to get decided."""
        with get_session() as db:
            result = db.execute(text("""
                SELECT r.id, r.action_type, r.status,
                       EXTRACT(EPOCH FROM (MAX(d.decided_at) - r.created_at)) / 3600 AS hours_to_decision
                FROM approval_requests r
                JOIN approval_decisions d ON d.approval_request_id = r.id
                GROUP BY r.id
                ORDER BY hours_to_decision DESC
                LIMIT :limit
            """), {"limit": limit})
            return [dict(row._mapping) for row in result]

    # ── Project Analytics ─────────────────────────────────────

    def project_completion_rate(self) -> dict:
        with get_session() as db:
            result = db.execute(text("""
                SELECT
                    COUNT(*) AS total,
                    COUNT(*) FILTER (WHERE status = 'completed') AS completed,
                    COUNT(*) FILTER (WHERE status = 'active') AS active,
                    COUNT(*) FILTER (WHERE status = 'at_risk') AS at_risk,
                    COUNT(*) FILTER (WHERE status = 'on_hold') AS on_hold
                FROM projects
            """))
            row = result.fetchone()
            data = dict(row._mapping)
            total = data.get("total", 0) or 0
            completed = data.get("completed", 0) or 0
            data["completion_rate"] = round(completed / total * 100, 1) if total > 0 else 0.0
            return data

    # ── Task Analytics ────────────────────────────────────────

    def task_counts_by_status(self) -> list:
        with get_session() as db:
            result = db.execute(text("""
                SELECT status, COUNT(*) AS count
                FROM tasks
                GROUP BY status
                ORDER BY count DESC
            """))
            return [dict(row._mapping) for row in result]

    def overdue_tasks(self) -> list:
        with get_session() as db:
            result = db.execute(text("""
                SELECT id, title, status, due_date, project_id
                FROM tasks
                WHERE due_date IS NOT NULL
                  AND due_date < CURRENT_DATE
                  AND status NOT IN ('completed', 'cancelled')
                ORDER BY due_date
            """))
            return [dict(row._mapping) for row in result]

    # ── Agent Analytics ───────────────────────────────────────

    def agent_success_rate(self) -> list:
        with get_session() as db:
            result = db.execute(text("""
                SELECT a.name AS agent_name,
                       COUNT(r.id) AS total_runs,
                       COUNT(r.id) FILTER (WHERE r.status = 'completed') AS completed,
                       COUNT(r.id) FILTER (WHERE r.status = 'failed') AS failed,
                       ROUND(
                           COUNT(r.id) FILTER (WHERE r.status = 'completed')::numeric /
                           NULLIF(COUNT(r.id), 0) * 100, 1
                       ) AS success_rate
                FROM agents a
                LEFT JOIN agent_runs r ON r.agent_id = a.id
                GROUP BY a.name
                ORDER BY total_runs DESC
            """))
            return [dict(row._mapping) for row in result]

    def average_agent_duration_ms(self) -> dict:
        with get_session() as db:
            result = db.execute(text("""
                SELECT a.name AS agent_name, AVG(r.duration_ms) AS avg_ms
                FROM agents a
                JOIN agent_runs r ON r.agent_id = a.id
                WHERE r.status = 'completed' AND r.duration_ms IS NOT NULL
                GROUP BY a.name
            """))
            return {row[0]: float(row[1]) if row[1] else 0.0 for row in result}

    # ── Memory Analytics ──────────────────────────────────────

    def memory_counts_by_type(self) -> list:
        with get_session() as db:
            result = db.execute(text("""
                SELECT memory_type, COUNT(*) AS count, AVG(confidence) AS avg_confidence
                FROM memory_items
                WHERE status = 'active'
                GROUP BY memory_type
                ORDER BY count DESC
            """))
            return [dict(row._mapping) for row in result]

    # ── Executive Dashboard ───────────────────────────────────

    def executive_summary(self) -> dict:
        with get_session() as db:
            result = db.execute(text("""
                SELECT
                    (SELECT COUNT(*) FROM projects) AS total_projects,
                    (SELECT COUNT(*) FROM tasks WHERE status NOT IN ('completed', 'cancelled')) AS active_tasks,
                    (SELECT COUNT(*) FROM approval_requests WHERE status = 'pending') AS pending_approvals,
                    (SELECT COUNT(*) FROM memory_items WHERE status = 'active') AS active_memories,
                    (SELECT COUNT(*) FROM agents WHERE status = 'active') AS active_agents,
                    (SELECT COUNT(*) FROM workflows WHERE status = 'active') AS active_workflows
            """))
            row = result.fetchone()
            return dict(row._mapping) if row else {}
