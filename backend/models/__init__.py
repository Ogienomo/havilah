"""
Havilah OS — Domain Models Package

All models import Base from backend.database.
This __init__ re-exports every model so that
`from backend.models import X` works everywhere
and Alembic can discover all tables via Base.metadata.
"""

from backend.database import Base  # noqa: F401 — needed for Alembic auto-import

from backend.models.organization import Organization, Department, Stakeholder
from backend.models.contact import (
    Contact,
    ContactPreference,
    Interaction,
    CommunicationHistory,
    RelationshipScore,
)
from backend.models.project import Project, Milestone, Deliverable, ProjectLink
from backend.models.task import Task, TaskDependency
from backend.models.approval import (
    ApprovalRequest,
    ApprovalDecision,
    ApprovalEvent,
    ExecutionRecord,
    ApprovalPolicy,
)
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
from backend.models.user import User, Role, Permission, UserRole, RolePermission
from backend.models.whatsapp import (
    WhatsAppSession,
    WhatsAppMessage,
    WhatsAppTemplate,
    WhatsAppApprovalVote,
)

__all__ = [
    # Organization
    "Organization", "Department", "Stakeholder",
    # CRM
    "Contact", "ContactPreference", "Interaction", "CommunicationHistory", "RelationshipScore",
    # Delivery
    "Project", "Milestone", "Deliverable", "ProjectLink",
    "Task", "TaskDependency",
    # Governance
    "ApprovalRequest", "ApprovalDecision", "ApprovalEvent", "ExecutionRecord", "ApprovalPolicy",
    "RiskAssessment",
    # Memory
    "MemoryItem", "MemorySource", "MemoryEvent", "MemoryLink",
    # Knowledge
    "KnowledgeArtifact", "KnowledgeVersion",
    # Research
    "ResearchJob", "ResearchSource", "ResearchNote", "ResearchOutput",
    # Content
    "ContentDraft", "ContentVersion", "ContentComment",
    # Meeting
    "Meeting", "AgendaItem", "MeetingDecision", "MeetingActionItem",
    # Workflow
    "Workflow", "WorkflowStep", "WorkflowTransition",
    # Agent
    "Agent", "AgentRun", "AgentResult",
    # Notification
    "Notification", "NotificationDelivery",
    # Events
    "DomainEvent",
    # Identity
    "User", "Role", "Permission", "UserRole", "RolePermission",
    # WhatsApp
    "WhatsAppSession", "WhatsAppMessage", "WhatsAppTemplate", "WhatsAppApprovalVote",
]
