#!/usr/bin/env python3
"""
Generate the initial Alembic migration file by introspecting SQLAlchemy models.
Mocks the database connection so we can import models without a running PostgreSQL.
"""

import sys
import os
import types

# ── Mock the database module BEFORE any model imports ──────────
sys.modules.pop("backend.database", None)
sys.modules.pop("backend.config", None)
sys.modules.pop("backend.config.settings", None)

mock_settings = types.ModuleType("backend.config.settings")
mock_settings_obj = type("Settings", (), {
    "DATABASE_URL": "postgresql+psycopg2://mock:mock@localhost/mock",
    "DB_ECHO": False,
})()
mock_settings.get_settings = lambda: mock_settings_obj
sys.modules["backend.config.settings"] = mock_settings
sys.modules["backend.config"] = types.ModuleType("backend.config")
sys.modules["backend.config"].settings = mock_settings

from sqlalchemy.orm import DeclarativeBase

class MockBase(DeclarativeBase):
    pass

mock_db = types.ModuleType("backend.database")
mock_db.Base = MockBase
mock_db.engine = None
mock_db.SessionLocal = None
mock_db.get_db = lambda: None
sys.modules["backend.database"] = mock_db

# ── Import all models ──────────────────────────────────────────
from backend.models.mixins import UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin
from backend.models.user import User, Role, Permission, UserRole, RolePermission
from backend.models.organization import Organization, Department, Stakeholder
from backend.models.contact import Contact, ContactPreference, Interaction, CommunicationHistory, RelationshipScore
from backend.models.project import Project, Milestone, Deliverable, ProjectLink
from backend.models.task import Task, TaskDependency
from backend.models.approval import ApprovalRequest, ApprovalDecision, ApprovalEvent, ExecutionRecord, ApprovalPolicy
from backend.models.risk import RiskAssessment
from backend.models.memory import MemoryItem, MemorySource, MemoryEvent, MemoryLink
from backend.models.knowledge import KnowledgeArtifact, KnowledgeVersion
from backend.models.research import ResearchJob, ResearchSource, ResearchNote, ResearchOutput
from backend.models.content import ContentDraft, ContentVersion, ContentComment
from backend.models.meeting import Meeting, AgendaItem, MeetingDecision, MeetingActionItem
from backend.models.workflow import Workflow, WorkflowStep, WorkflowTransition
from backend.models.agent import Agent, AgentRun, AgentResult
from backend.models.notification import Notification, NotificationDelivery
from backend.models.event import DomainEvent

metadata = MockBase.metadata

# ── Circular FK config ─────────────────────────────────────────
CIRCULAR_SOURCE = "approval_requests"
CIRCULAR_TARGET = "risk_assessments"
CIRCULAR_FK_COL = "risk_assessment_id"

# ── Dependency resolution ──────────────────────────────────────
def get_fk_deps(table):
    """Get table names referenced by FKs (excluding self-referential)."""
    deps = set()
    for fk in table.foreign_keys:
        ref = fk.column.table.name
        if ref != table.name:
            deps.add(ref)
    return deps

dep_graph = {}
for name, table in metadata.tables.items():
    deps = get_fk_deps(table)
    dep_graph[name] = deps

# Temporarily break the circular dependency for topological sort
if CIRCULAR_TARGET in dep_graph.get(CIRCULAR_SOURCE, set()):
    dep_graph[CIRCULAR_SOURCE].discard(CIRCULAR_TARGET)

# Topological sort
sorted_tables = []
visited = set()
temp_visited = set()

def visit(name):
    if name in visited:
        return
    if name in temp_visited:
        raise ValueError(f"Circular dependency at {name}")
    temp_visited.add(name)
    for dep in dep_graph.get(name, set()):
        visit(dep)
    temp_visited.discard(name)
    visited.add(name)
    sorted_tables.append(name)

for name in sorted(metadata.tables.keys()):
    visit(name)

# ── Column type / default helpers ──────────────────────────────
from sqlalchemy import types as sa_types
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB

def type_str(col_type):
    """Generate Alembic-compatible type string."""
    if isinstance(col_type, PG_UUID):
        return "sa.UUID(as_uuid=True)"
    if isinstance(col_type, JSONB):
        return "postgresql.JSONB()"
    if isinstance(col_type, sa_types.Text):
        return "sa.Text()"
    if isinstance(col_type, sa_types.DateTime):
        return "sa.DateTime(timezone=True)" if col_type.timezone else "sa.DateTime()"
    if isinstance(col_type, sa_types.Boolean):
        return "sa.Boolean()"
    if isinstance(col_type, sa_types.Integer):
        return "sa.Integer()"
    if isinstance(col_type, sa_types.Numeric):
        p, s = col_type.precision, col_type.scale
        if p is not None and s is not None:
            return f"sa.Numeric({p}, {s})"
        return "sa.Numeric()"
    if isinstance(col_type, sa_types.Date):
        return "sa.Date()"
    return f"sa.{type(col_type).__name__}()"


def is_text_type(col_type):
    return isinstance(col_type, sa_types.Text)


def sd_str(col):
    """Generate proper server_default string for a column."""
    sd = col.server_default
    if sd is not None:
        # Already has server_default from mixin (gen_random_uuid, NOW())
        txt = str(sd.arg)
        if hasattr(sd.arg, 'text'):
            txt = sd.arg.text
        return f"text('{txt}')"

    # Generate from Python default only if no server_default exists
    if col.default is None:
        return None

    default_val = col.default.arg
    if callable(default_val):
        return None  # ORM-side only

    if isinstance(col.type, sa_types.Boolean):
        return f"text('{str(default_val).lower()}')"
    if isinstance(col.type, (sa_types.Integer, sa_types.Numeric)):
        return f"text('{default_val}')"
    # Text columns — wrap in literal quotes
    if isinstance(col.type, sa_types.Text):
        return f"text('{default_val}')"
    return f"text('{default_val}')"


def col_def(col, skip_fk_to=None):
    """Build the sa.Column(...) argument string.
    
    sa.Column signature: Column(name, type_, *args, **kwargs)
    ForeignKey is a positional arg and must come BEFORE keyword args.
    """
    # Positional args after type: ForeignKeyConstraint
    positional = []
    # Keyword args
    keywords = []

    # Primary key
    if col.primary_key:
        keywords.append("primary_key=True")

    # Nullable
    if not col.nullable:
        keywords.append("nullable=False")
    else:
        keywords.append("nullable=True")

    # Server default
    sd = sd_str(col)
    if sd:
        keywords.append(f"server_default={sd}")

    # Foreign key — MUST be positional (before kwargs)
    fks = list(col.foreign_keys)
    if fks:
        fk = fks[0]
        ref_table = fk.column.table.name
        ref_col = fk.column.name
        if skip_fk_to and ref_table == skip_fk_to:
            pass  # will be added later
        else:
            positional.append(f"sa.ForeignKey('{ref_table}.{ref_col}')")

    # Unique
    if col.unique:
        keywords.append("unique=True")

    all_parts = [type_str(col.type)] + positional + keywords
    return ", ".join(all_parts)


# ── Column ordering: id → created_at → updated_at → metadata → domain cols ──
MIXIN_COLS = {"id", "created_at", "updated_at", "metadata"}

def ordered_columns(table):
    """Return columns in a natural order: mixin cols first, then domain cols."""
    mixin = []
    domain = []
    for col in table.columns:
        if col.name in MIXIN_COLS:
            mixin.append(col)
        else:
            domain.append(col)
    # Sort mixin cols in canonical order
    order = {"id": 0, "created_at": 1, "updated_at": 2, "metadata": 3}
    mixin.sort(key=lambda c: order.get(c.name, 99))
    return mixin + domain


# ── Build the migration file ───────────────────────────────────
L = []  # lines

L.append('"""Havilah OS — Initial Schema Migration')
L.append('')
L.append('Auto-generated from SQLAlchemy model introspection.')
L.append('Handles circular FK between approval_requests and risk_assessments.')
L.append('"""')
L.append('')
L.append('from alembic import op')
L.append('import sqlalchemy as sa')
L.append('from sqlalchemy.dialects import postgresql')
L.append('from sqlalchemy import text')
L.append('')
L.append('')
L.append("# revision identifiers, used by Alembic.")
L.append("revision = '001'")
L.append("down_revision = None")
L.append("branch_labels = None")
L.append("depends_on = None")
L.append('')
L.append('')
L.append('def upgrade() -> None:')

for tname in sorted_tables:
    skip_fk = CIRCULAR_TARGET if tname == CIRCULAR_SOURCE else None
    table = metadata.tables[tname]

    L.append(f"    op.create_table('{tname}',")
    for col in ordered_columns(table):
        # For the circular FK column: include the column but without FK
        if tname == CIRCULAR_SOURCE and col.name == CIRCULAR_FK_COL:
            L.append(f"        sa.Column('{col.name}', {type_str(col.type)}, nullable=True),")
        else:
            L.append(f"        sa.Column('{col.name}', {col_def(col, skip_fk_to=skip_fk)}),")
    L.append("    )")
    L.append("")

# Add the circular FK constraint after both tables exist
L.append("    # ── Add circular FK: approval_requests.risk_assessment_id → risk_assessments.id ──")
L.append("    op.create_foreign_key(")
L.append("        'fk_approval_requests_risk_assessment_id',")
L.append("        'approval_requests',")
L.append("        'risk_assessments',")
L.append("        ['risk_assessment_id'],")
L.append("        ['id'],")
L.append("    )")
L.append("")

# Downgrade
L.append("")
L.append("")
L.append("def downgrade() -> None:")
L.append("    # ── Remove circular FK first ──")
L.append("    op.drop_constraint('fk_approval_requests_risk_assessment_id', 'approval_requests', type_='foreignkey')")
L.append("")
L.append("    # ── Drop tables in reverse dependency order ──")
for tname in reversed(sorted_tables):
    L.append(f"    op.drop_table('{tname}')")
L.append("")

# ── Write ──────────────────────────────────────────────────────
out = "/home/z/my-project/havilah-workspace/alembic/versions/001_initial_schema.py"
with open(out, "w") as f:
    f.write("\n".join(L))

print(f"Wrote {len(L)} lines to {out}")
print(f"Tables: {len(sorted_tables)}")
