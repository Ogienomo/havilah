"""
Havilah OS — API Dependency Injection

FastAPI Depends() factories for DB sessions and service instances.
"""

from backend.database import SessionLocal, get_db


# ── Service Factories ────────────────────────────────────────
# Each route module can use these to get a fresh service instance.
# Services internally manage their own sessions via get_session().

from backend.services.approval_service import ApprovalService
from backend.services.task_service import TaskService
from backend.services.project_service import ProjectService
from backend.services.project_health_service import ProjectHealthService
from backend.services.memory_service import MemoryService
from backend.services.contact_service import ContactService
from backend.services.workflow_service import WorkflowService
from backend.services.agent_service import AgentService
from backend.services.risk_service import RiskService
from backend.services.notification_service import NotificationService
from backend.services.analytics_service import AnalyticsService
from backend.services.organization_service import OrganizationService
from backend.services.audit_service import AuditService
from backend.services.briefing_service import BriefingService
from backend.services.meeting_service import MeetingService
from backend.services.knowledge_service import KnowledgeService
from backend.services.research_service import ResearchService
from backend.services.content_service import ContentService


def get_approval_service() -> ApprovalService:
    return ApprovalService()

def get_task_service() -> TaskService:
    return TaskService()

def get_project_service() -> ProjectService:
    return ProjectService()

def get_project_health_service() -> ProjectHealthService:
    return ProjectHealthService()

def get_memory_service() -> MemoryService:
    return MemoryService()

def get_contact_service() -> ContactService:
    return ContactService()

def get_workflow_service() -> WorkflowService:
    return WorkflowService()

def get_agent_service() -> AgentService:
    return AgentService()

def get_risk_service() -> RiskService:
    return RiskService()

def get_notification_service() -> NotificationService:
    return NotificationService()

def get_analytics_service() -> AnalyticsService:
    return AnalyticsService()

def get_organization_service() -> OrganizationService:
    return OrganizationService()

def get_audit_service() -> AuditService:
    return AuditService()

def get_briefing_service() -> BriefingService:
    return BriefingService()

def get_meeting_service() -> MeetingService:
    return MeetingService()

def get_knowledge_service() -> KnowledgeService:
    return KnowledgeService()

def get_research_service() -> ResearchService:
    return ResearchService()

def get_content_service() -> ContentService:
    return ContentService()
