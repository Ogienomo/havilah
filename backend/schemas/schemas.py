"""
Havilah OS — Pydantic Schemas for API Request/Response Validation

Every endpoint validates input and serializes output through these schemas.
No raw dicts escape the API boundary.
"""

from datetime import datetime, date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ════════════════════════════════════════════════════════════════
#  ORGANIZATION
# ════════════════════════════════════════════════════════════════

class OrganizationCreate(BaseModel):
    name: str
    organization_type: Optional[str] = None
    description: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None

class OrganizationResponse(BaseModel):
    id: UUID
    name: str
    organization_type: Optional[str] = None
    status: str = "active"
    description: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    created_at: Optional[datetime] = None

class DepartmentCreate(BaseModel):
    name: str
    department_type: Optional[str] = None
    head_id: Optional[UUID] = None

class DepartmentResponse(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    department_type: Optional[str] = None
    status: str = "active"
    head_id: Optional[UUID] = None


# ════════════════════════════════════════════════════════════════
#  CONTACT
# ════════════════════════════════════════════════════════════════

class ContactCreate(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=300)
    email: Optional[str] = Field(None, max_length=320)
    phone: Optional[str] = Field(None, max_length=50)
    organization_id: Optional[UUID] = None
    role: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = Field(None, max_length=10000)

class ContactResponse(BaseModel):
    id: UUID
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    organization_id: Optional[UUID] = None
    role: Optional[str] = None
    status: str = "active"
    notes: Optional[str] = None
    created_at: Optional[datetime] = None


# ════════════════════════════════════════════════════════════════
#  PROJECT
# ════════════════════════════════════════════════════════════════

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=300)
    description: Optional[str] = None
    project_type: Optional[str] = None
    priority: Optional[str] = "medium"
    status: Optional[str] = "active"
    client_contact_id: Optional[UUID] = None
    organization_id: Optional[UUID] = None

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None

class ProjectResponse(BaseModel):
    id: UUID
    title: str
    objective: Optional[str] = None
    status: str = "active"
    priority: str = "medium"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ════════════════════════════════════════════════════════════════
#  TASK
# ════════════════════════════════════════════════════════════════

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    project_id: Optional[UUID] = None
    parent_task_id: Optional[UUID] = None
    workflow_step_id: Optional[UUID] = None
    priority: Optional[str] = "medium"
    due_date: Optional[date] = None

class TaskStatusUpdate(BaseModel):
    status: str

class TaskResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    status: str
    priority: str = "medium"
    project_id: Optional[UUID] = None
    due_date: Optional[date] = None
    created_at: Optional[datetime] = None


# ════════════════════════════════════════════════════════════════
#  APPROVAL
# ════════════════════════════════════════════════════════════════

class ApprovalRequestCreate(BaseModel):
    action_type: str = Field(..., min_length=1, max_length=200)
    summary: str = Field(..., min_length=1, max_length=10000)
    channel: Optional[str] = Field("internal", max_length=50)
    risk_level: Optional[str] = Field("medium", pattern="^(low|medium|high|critical)$")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    draft_payload: Optional[dict] = None
    project_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None
    task_id: Optional[UUID] = None
    organization_id: Optional[UUID] = None
    created_by: Optional[UUID] = None

class ApprovalDecisionInput(BaseModel):
    reason: Optional[str] = None
    approver_id: Optional[UUID] = None

class ApprovalEscalateInput(BaseModel):
    escalated_to: UUID
    reason: Optional[str] = None
    decided_by: Optional[UUID] = None

class ApprovalExecutionInput(BaseModel):
    result: Optional[dict] = None

class ApprovalResponse(BaseModel):
    id: UUID
    current_state: str
    status: str
    action_type: str
    summary: Optional[str] = None
    risk_level: Optional[str] = None
    confidence: Optional[float] = None


# ════════════════════════════════════════════════════════════════
#  MEMORY
# ════════════════════════════════════════════════════════════════

class MemoryCapture(BaseModel):
    memory_type: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=500)
    content: Optional[str] = Field(None, max_length=50000)
    source: Optional[str] = Field(None, max_length=200)
    importance: Optional[float] = Field(0.5, ge=0.0, le=1.0)
    confidence: Optional[float] = Field(0.5, ge=0.0, le=1.0)

class MemoryCaptureCommand(BaseModel):
    """Command model for Hermes memory recorder — matches MemoryCapture with string importance."""
    memory_type: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=500)
    content: Optional[str] = Field(None, max_length=50000)
    source: Optional[str] = Field(None, max_length=200)
    importance: Optional[str] = Field("medium", pattern="^(low|medium|high|critical)$")
    confidence: Optional[float] = Field(0.5, ge=0.0, le=1.0)
    status: Optional[str] = Field("active", max_length=50)

class MemoryLinkInput(BaseModel):
    entity_type: str
    entity_id: UUID
    relationship_type: Optional[str] = "related"

class MemoryReinforceInput(BaseModel):
    memory_id: UUID

class MemorySearchInput(BaseModel):
    search_text: str = Field(..., min_length=1)

class MemoryResponse(BaseModel):
    id: UUID
    memory_type: str
    title: str
    content: Optional[str] = None
    importance: Optional[float] = None
    confidence: Optional[float] = None
    status: str = "active"
    created_at: Optional[datetime] = None


# ════════════════════════════════════════════════════════════════
#  WORKFLOW
# ════════════════════════════════════════════════════════════════

class WorkflowCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    workflow_type: Optional[str] = "sequential"
    project_id: Optional[UUID] = None
    auto_advance: Optional[bool] = False

class WorkflowStepCreate(BaseModel):
    title: str
    step_order: int = 0
    step_type: Optional[str] = "task"
    requires_approval: Optional[bool] = False
    task_template: Optional[dict] = None
    approval_template: Optional[dict] = None

class WorkflowTransitionCreate(BaseModel):
    from_step_id: Optional[UUID] = None
    to_step_id: Optional[UUID] = None
    transition_type: Optional[str] = "on_complete"
    condition: Optional[dict] = None

class WorkflowResponse(BaseModel):
    id: UUID
    title: str
    status: str
    workflow_type: Optional[str] = None
    current_step_order: int = 0


# ════════════════════════════════════════════════════════════════
#  AGENT
# ════════════════════════════════════════════════════════════════

class AgentRegister(BaseModel):
    model_config = {"populate_by_name": True}
    name: str = Field(..., min_length=1)
    display_name: str
    agent_type: str
    description: Optional[str] = None
    capabilities: Optional[list] = []
    tool_access: Optional[list] = []
    approval_scope: Optional[str] = "none"
    agent_model_config: Optional[dict] = Field(None, alias="model_config")

class AgentRunCreate(BaseModel):
    agent_id: UUID
    input_context: dict
    task_id: Optional[UUID] = None
    approval_id: Optional[UUID] = None
    workflow_step_id: Optional[UUID] = None
    configuration: Optional[dict] = None

class AgentRunComplete(BaseModel):
    results: list
    duration_ms: Optional[int] = None
    token_usage: Optional[dict] = None

class AgentRunFail(BaseModel):
    error_message: str
    duration_ms: Optional[int] = None

class AgentResponse(BaseModel):
    id: UUID
    name: str
    display_name: str
    agent_type: str
    status: str
    approval_scope: str = "none"


# ════════════════════════════════════════════════════════════════
#  MEETING
# ════════════════════════════════════════════════════════════════

class MeetingCreate(BaseModel):
    title: str = Field(..., min_length=1)
    meeting_type: Optional[str] = "internal"
    project_id: Optional[UUID] = None
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    organizer_id: Optional[UUID] = None
    participants: Optional[list] = []

class MeetingComplete(BaseModel):
    summary: Optional[str] = None

class AgendaItemCreate(BaseModel):
    title: str
    description: Optional[str] = None
    order_index: Optional[int] = 0
    duration_minutes: Optional[int] = None
    owner_id: Optional[UUID] = None

class MeetingDecisionCreate(BaseModel):
    decision_text: str
    decided_by: Optional[UUID] = None
    rationale: Optional[str] = None

class MeetingActionItemCreate(BaseModel):
    description: str
    task_id: Optional[UUID] = None
    assigned_to: Optional[UUID] = None
    due_date: Optional[date] = None

class MeetingResponse(BaseModel):
    id: UUID
    title: str
    meeting_type: Optional[str] = None
    status: str
    scheduled_at: Optional[datetime] = None
    organizer_id: Optional[UUID] = None


# ════════════════════════════════════════════════════════════════
#  KNOWLEDGE
# ════════════════════════════════════════════════════════════════

class KnowledgeArtifactCreate(BaseModel):
    title: str = Field(..., min_length=1)
    knowledge_type: str
    category: Optional[str] = "operations"
    summary: Optional[str] = None
    owner_id: Optional[UUID] = None

class KnowledgeVersionCreate(BaseModel):
    version_label: str
    content: str
    change_note: Optional[str] = None
    created_by: Optional[UUID] = None

class KnowledgeVersionApprove(BaseModel):
    approved_by: UUID

class KnowledgeResponse(BaseModel):
    id: UUID
    title: str
    knowledge_type: str
    category: Optional[str] = None
    status: str


# ════════════════════════════════════════════════════════════════
#  RESEARCH
# ════════════════════════════════════════════════════════════════

class ResearchJobCreate(BaseModel):
    title: str = Field(..., min_length=1)
    research_question: str
    project_id: Optional[UUID] = None
    priority: Optional[str] = "medium"
    owner_id: Optional[UUID] = None

class ResearchSourceCreate(BaseModel):
    source_title: str
    source_type: str
    source_reference: Optional[str] = None
    source_url: Optional[str] = None
    source_summary: Optional[str] = None
    reliability_score: Optional[float] = None

class ResearchNoteCreate(BaseModel):
    note_text: str
    source_id: Optional[UUID] = None
    note_type: Optional[str] = "observation"

class ResearchOutputCreate(BaseModel):
    output_type: str
    title: str
    content: str
    confidence: Optional[float] = None
    status: Optional[str] = "draft"

class ResearchJobResponse(BaseModel):
    id: UUID
    title: str
    research_question: str
    status: str
    priority: str


# ════════════════════════════════════════════════════════════════
#  CONTENT
# ════════════════════════════════════════════════════════════════

class ContentDraftCreate(BaseModel):
    title: str = Field(..., min_length=1)
    content_type: Optional[str] = "article"
    content: Optional[str] = ""
    project_id: Optional[UUID] = None
    created_by: Optional[UUID] = None
    source_agent_run_id: Optional[UUID] = None

class ContentVersionCreate(BaseModel):
    content: str
    created_by: Optional[UUID] = None

class ContentCommentCreate(BaseModel):
    comment_text: str
    version_id: Optional[UUID] = None
    author_id: Optional[UUID] = None

class ContentStatusUpdate(BaseModel):
    status: str

class ContentDraftResponse(BaseModel):
    id: UUID
    title: str
    content_type: Optional[str] = None
    status: str
    project_id: Optional[UUID] = None


# ════════════════════════════════════════════════════════════════
#  NOTIFICATION
# ════════════════════════════════════════════════════════════════

class NotificationCreate(BaseModel):
    notification_type: str
    title: str
    message: str
    priority: Optional[str] = "medium"
    category: Optional[str] = "operational"
    recipient_id: Optional[UUID] = None
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[UUID] = None
    action_required: Optional[bool] = False
    action_url: Optional[str] = None

class NotificationMarkRead(BaseModel):
    pass  # just needs the notification_id from path

class NotificationDeliveryInput(BaseModel):
    channel: str
    external_id: Optional[str] = None

class NotificationResponse(BaseModel):
    id: UUID
    notification_type: str
    title: str
    message: str
    priority: str
    status: str
    action_required: bool = False
    created_at: Optional[datetime] = None


# ════════════════════════════════════════════════════════════════
#  RISK
# ════════════════════════════════════════════════════════════════

class RiskCalculateInput(BaseModel):
    approval_id: UUID
    action_type: str
    channel: str
    external_audience: Optional[bool] = False
    irreversible: Optional[bool] = False

class RiskResponse(BaseModel):
    id: UUID
    risk_level: str
    risk_score: float
    approval_required: bool
    escalation_required: bool


# ════════════════════════════════════════════════════════════════
#  EVENT
# ════════════════════════════════════════════════════════════════

class EventResponse(BaseModel):
    id: UUID
    aggregate_type: Optional[str] = None
    aggregate_id: Optional[UUID] = None
    event_type: str
    event_category: Optional[str] = None
    actor_type: Optional[str] = None
    payload: Optional[dict] = None
    created_at: Optional[datetime] = None


# ════════════════════════════════════════════════════════════════
#  AUDIT
# ════════════════════════════════════════════════════════════════

class AuditTrailResponse(BaseModel):
    events: list[dict]


# ════════════════════════════════════════════════════════════════
#  ANALYTICS
# ════════════════════════════════════════════════════════════════

class ExecutiveDashboardResponse(BaseModel):
    executive_summary: Optional[dict] = None
    approval_counts: Optional[dict] = None
    project_completion_rate: Optional[dict] = None
    task_counts: Optional[dict] = None
    overdue_tasks: Optional[list] = None
    agent_success_rate: Optional[dict] = None
    memory_counts: Optional[dict] = None


# ════════════════════════════════════════════════════════════════
#  BRIEFING
# ════════════════════════════════════════════════════════════════

class ContactBriefingResponse(BaseModel):
    contact: Optional[dict] = None
    memories: Optional[list] = None

class ApprovalBriefingResponse(BaseModel):
    approval: Optional[dict] = None
    decisions: Optional[list] = None
    execution: Optional[dict] = None
    events: Optional[list] = None

class ExecutiveBriefingResponse(BaseModel):
    memory_count: Optional[int] = None
    project_count: Optional[int] = None
    task_count: Optional[int] = None
    approval_count: Optional[int] = None
    execution_count: Optional[int] = None
    project_status_breakdown: Optional[list] = None
    task_status_breakdown: Optional[list] = None
    recent_events: Optional[list] = None


# ════════════════════════════════════════════════════════════════
#  WHATSAPP
# ════════════════════════════════════════════════════════════════

class WhatsAppSessionResponse(BaseModel):
    id: UUID
    phone_number: str
    whatsapp_id: Optional[str] = None
    user_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None
    status: str = "active"
    language: str = "en"
    message_count: int = 0
    opted_in: bool = False
    created_at: Optional[datetime] = None

class WhatsAppMessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    direction: str
    message_type: str
    status: str
    content_body: Optional[str] = None
    template_name: Optional[str] = None
    whatsapp_message_id: Optional[str] = None
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[UUID] = None
    approval_id: Optional[UUID] = None
    created_at: Optional[datetime] = None

class WhatsAppTemplateResponse(BaseModel):
    id: UUID
    name: str
    category: str
    language: str
    body_text: str
    status: str = "draft"
    use_count: int = 0
    created_at: Optional[datetime] = None

class WhatsAppApprovalVoteResponse(BaseModel):
    id: UUID
    session_id: UUID
    approval_id: UUID
    vote: str
    vote_source: str
    confidence: Optional[float] = None
    processed: bool = False
    created_at: Optional[datetime] = None
