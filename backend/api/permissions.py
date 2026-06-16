"""
Havilah OS — RBAC Permission Definitions

Resource:action permission matrix for the 14 bounded contexts.
Core principle: AI agents can NEVER approve external execution — ever.

Role hierarchy:
  - admin:   Full system access, can approve critical actions
  - operator: Day-to-day operations, can approve medium-risk actions
  - viewer:  Read-only access across all resources
  - agent:   AI agent — can only read and draft, NEVER approve/execute
"""

from dataclasses import dataclass
from enum import Enum


class RoleName(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"
    AGENT = "agent"


@dataclass(frozen=True)
class Permission:
    resource: str
    action: str

    @property
    def name(self) -> str:
        return f"{self.resource}:{self.action}"


# ── All permissions in the system ─────────────────────────────────
# Format: resource:action

PERMISSIONS = {
    # Approval (most guarded — agents can NEVER approve/execute)
    Permission("approval", "create"),
    Permission("approval", "read"),
    Permission("approval", "approve"),     # HUMANS ONLY
    Permission("approval", "reject"),      # HUMANS ONLY
    Permission("approval", "escalate"),    # HUMANS ONLY
    Permission("approval", "execute"),     # HUMANS ONLY
    Permission("approval", "assess_risk"),

    # Task
    Permission("task", "create"),
    Permission("task", "read"),
    Permission("task", "update"),
    Permission("task", "update_status"),
    Permission("task", "delete"),

    # Project
    Permission("project", "create"),
    Permission("project", "read"),
    Permission("project", "update"),
    Permission("project", "update_status"),
    Permission("project", "recalculate_health"),

    # Contact / CRM
    Permission("contact", "create"),
    Permission("contact", "read"),
    Permission("contact", "update"),
    Permission("contact", "add_interaction"),

    # Memory
    Permission("memory", "capture"),
    Permission("memory", "read"),
    Permission("memory", "link"),
    Permission("memory", "reinforce"),
    Permission("memory", "search"),

    # Workflow
    Permission("workflow", "create"),
    Permission("workflow", "read"),
    Permission("workflow", "start"),
    Permission("workflow", "advance_step"),
    Permission("workflow", "add_step"),
    Permission("workflow", "add_transition"),

    # Agent
    Permission("agent", "register"),
    Permission("agent", "read"),
    Permission("agent", "run"),
    Permission("agent", "complete_run"),
    Permission("agent", "fail_run"),

    # Meeting
    Permission("meeting", "create"),
    Permission("meeting", "read"),
    Permission("meeting", "complete"),
    Permission("meeting", "add_agenda"),
    Permission("meeting", "add_decision"),
    Permission("meeting", "add_action_item"),

    # Knowledge
    Permission("knowledge", "create"),
    Permission("knowledge", "read"),
    Permission("knowledge", "add_version"),
    Permission("knowledge", "approve_version"),  # HUMANS ONLY
    Permission("knowledge", "publish"),           # HUMANS ONLY
    Permission("knowledge", "deprecate"),

    # Research
    Permission("research", "create"),
    Permission("research", "read"),
    Permission("research", "update_status"),
    Permission("research", "add_source"),
    Permission("research", "add_note"),
    Permission("research", "add_output"),

    # Content
    Permission("content", "create"),
    Permission("content", "read"),
    Permission("content", "add_version"),
    Permission("content", "add_comment"),
    Permission("content", "update_status"),

    # Notification
    Permission("notification", "create"),
    Permission("notification", "read"),
    Permission("notification", "mark_read"),
    Permission("notification", "deliver"),

    # Analytics
    Permission("analytics", "read"),
    Permission("analytics", "dashboard"),

    # Organization
    Permission("organization", "create"),
    Permission("organization", "read"),
    Permission("organization", "add_department"),
    Permission("organization", "add_stakeholder"),

    # Event / Audit
    Permission("event", "read"),
    Permission("audit", "read"),

    # Risk
    Permission("risk", "calculate"),
    Permission("risk", "read"),

    # Briefing
    Permission("briefing", "read"),

    # Search
    Permission("search", "read"),

    # Identity
    Permission("user", "create"),
    Permission("user", "read"),
    Permission("user", "update"),
    Permission("user", "manage_roles"),
}


# ── Role → Permission Mapping ────────────────────────────────────

ROLE_PERMISSIONS: dict[RoleName, set[str]] = {
    RoleName.ADMIN: {
        # Admin gets EVERYTHING
        p.name for p in PERMISSIONS
    },
    RoleName.OPERATOR: {
        # Operator: day-to-day operations, can approve medium-risk
        "approval:create", "approval:read", "approval:approve", "approval:reject",
        "approval:escalate", "approval:execute", "approval:assess_risk",
        "task:create", "task:read", "task:update", "task:update_status", "task:delete",
        "project:create", "project:read", "project:update", "project:update_status",
        "project:recalculate_health",
        "contact:create", "contact:read", "contact:update", "contact:add_interaction",
        "memory:capture", "memory:read", "memory:link", "memory:reinforce", "memory:search",
        "workflow:create", "workflow:read", "workflow:start", "workflow:advance_step",
        "workflow:add_step", "workflow:add_transition",
        "agent:read", "agent:run",
        "meeting:create", "meeting:read", "meeting:complete",
        "meeting:add_agenda", "meeting:add_decision", "meeting:add_action_item",
        "knowledge:create", "knowledge:read", "knowledge:add_version",
        "knowledge:approve_version", "knowledge:publish", "knowledge:deprecate",
        "research:create", "research:read", "research:update_status",
        "research:add_source", "research:add_note", "research:add_output",
        "content:create", "content:read", "content:add_version",
        "content:add_comment", "content:update_status",
        "notification:read", "notification:mark_read", "notification:deliver",
        "analytics:read", "analytics:dashboard",
        "organization:read",
        "event:read", "audit:read",
        "risk:calculate", "risk:read",
        "briefing:read",
        "search:read",
    },
    RoleName.VIEWER: {
        # Viewer: read-only across all resources
        "approval:read",
        "task:read",
        "project:read",
        "contact:read",
        "memory:read", "memory:search",
        "workflow:read",
        "agent:read",
        "meeting:read",
        "knowledge:read",
        "research:read",
        "content:read",
        "notification:read",
        "analytics:read", "analytics:dashboard",
        "organization:read",
        "event:read", "audit:read",
        "risk:read",
        "briefing:read",
        "search:read",
    },
    RoleName.AGENT: {
        # Agent: can read and draft, NEVER approve/execute
        "approval:create", "approval:read", "approval:assess_risk",
        "task:create", "task:read", "task:update",
        "project:read",
        "contact:read",
        "memory:capture", "memory:read", "memory:link", "memory:reinforce", "memory:search",
        "workflow:read",
        "agent:read", "agent:run", "agent:complete_run", "agent:fail_run",
        "meeting:read",
        "knowledge:create", "knowledge:read", "knowledge:add_version",
        "research:create", "research:read", "research:update_status",
        "research:add_source", "research:add_note", "research:add_output",
        "content:create", "content:read", "content:add_version", "content:add_comment",
        "notification:read",
        "analytics:read",
        "organization:read",
        "event:read",
        "risk:calculate", "risk:read",
        "briefing:read",
        "search:read",
    },
}

# ── Human-only permissions (agents can NEVER have these) ──────────
HUMAN_ONLY_PERMISSIONS = {
    "approval:approve",
    "approval:reject",
    "approval:escalate",
    "approval:execute",
    "knowledge:approve_version",
    "knowledge:publish",
    "user:manage_roles",
}
