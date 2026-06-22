"""
Havilah OS — Hermes Run Repository

Persists orchestration run state to the database so pending approvals
and active runs survive application restarts.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import text
from backend.models.hermes_run import HermesRun
from backend.repositories.base import get_session

logger = logging.getLogger("havilah.hermes_run_repo")


class HermesRunRepository:

    def create(self, run_id: str, instruction: str, source: str, context: dict) -> None:
        try:
            with get_session() as db:
                run = HermesRun(
                    id=run_id,
                    instruction=instruction,
                    source=source,
                    status="planning",
                    context=context or {},
                    results=[],
                )
                db.add(run)
                db.flush()
        except Exception as e:
            logger.error(f"Failed to persist run {run_id}: {e}")

    def update_status(self, run_id: str, status: str, plan: Optional[dict] = None,
                      results: Optional[list] = None, error: Optional[str] = None) -> None:
        try:
            with get_session() as db:
                run = db.query(HermesRun).filter(HermesRun.id == run_id).first()
                if run is None:
                    return
                run.status = status
                if plan is not None:
                    run.plan = plan
                if results is not None:
                    run.results = results
                if error is not None:
                    run.error = error
                if status in ("completed", "failed", "cancelled"):
                    run.completed_at = datetime.now(timezone.utc)
                db.flush()
        except Exception as e:
            logger.error(f"Failed to update run {run_id} status: {e}")

    def get(self, run_id: str) -> Optional[dict]:
        try:
            with get_session() as db:
                run = db.query(HermesRun).filter(HermesRun.id == run_id).first()
                if run is None:
                    return None
                return {
                    "run_id": str(run.id),
                    "instruction": run.instruction,
                    "source": run.source,
                    "status": run.status,
                    "plan": run.plan,
                    "results": run.results or [],
                    "context": run.context or {},
                    "error": run.error,
                    "started_at": run.started_at.isoformat() if run.started_at else None,
                }
        except Exception as e:
            logger.error(f"Failed to fetch run {run_id}: {e}")
            return None

    def list_active(self) -> list[dict]:
        try:
            with get_session() as db:
                runs = (
                    db.query(HermesRun)
                    .filter(HermesRun.status.notin_(["completed", "failed", "cancelled"]))
                    .order_by(HermesRun.started_at.desc())
                    .limit(100)
                    .all()
                )
                return [
                    {
                        "run_id": str(r.id),
                        "status": r.status,
                        "instruction": r.instruction[:80],
                    }
                    for r in runs
                ]
        except Exception as e:
            logger.error(f"Failed to list active runs: {e}")
            return []
