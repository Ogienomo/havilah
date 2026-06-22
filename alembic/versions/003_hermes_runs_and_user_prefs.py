"""Havilah OS — Hermes Runs + User Preferences

Adds:
  - hermes_runs: persists orchestration run state across restarts
  - user_preferences: stores per-user settings (e.g. auto_approve)

Revision ID: 003
Revises: 002
Create Date: 2026-06-22
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "hermes_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("instruction", sa.Text(), nullable=False),
        sa.Column("source", sa.String(50), nullable=False, server_default="api"),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("plan", postgresql.JSONB(), nullable=True),
        sa.Column("results", postgresql.JSONB(), nullable=True, server_default="[]"),
        sa.Column("context", postgresql.JSONB(), nullable=True, server_default="{}"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_hermes_runs_status", "hermes_runs", ["status"])

    op.create_table(
        "user_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("auto_approve", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("preferences", postgresql.JSONB(), nullable=True, server_default="{}"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_user_preferences_user_id", "user_preferences", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_user_preferences_user_id", "user_preferences")
    op.drop_table("user_preferences")
    op.drop_index("ix_hermes_runs_status", "hermes_runs")
    op.drop_table("hermes_runs")
