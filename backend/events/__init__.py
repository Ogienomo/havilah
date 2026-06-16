"""
Havilah OS — Domain Event Constants

Central registry of all event type strings used across the system.
Everything Is an Event — nothing polls; everything reacts.
"""

# ── Approval Events ──────────────────────────────────────────
APPROVAL_REQUESTED = "ApprovalRequested"
APPROVAL_APPROVED = "ApprovalApproved"
APPROVAL_REJECTED = "ApprovalRejected"
APPROVAL_EXPIRED = "ApprovalExpired"
EXECUTION_STARTED = "ExecutionStarted"
EXECUTION_COMPLETED = "ExecutionCompleted"
EXECUTION_FAILED = "ExecutionFailed"

# ── Project Events ───────────────────────────────────────────
PROJECT_CREATED = "ProjectCreated"
PROJECT_STATUS_CHANGED = "ProjectStatusChanged"
PROJECT_APPROVAL_LINKED = "ProjectApprovalLinked"
PROJECT_BRIEFING_GENERATED = "ProjectBriefingGenerated"
PROJECT_DASHBOARD_GENERATED = "ProjectDashboardGenerated"

# ── Task Events ──────────────────────────────────────────────
TASK_CREATED = "TaskCreated"
TASK_STATUS_CHANGED = "TaskStatusChanged"
TASK_APPROVAL_LINKED = "TaskApprovalLinked"
TASK_BRIEFING_GENERATED = "TaskBriefingGenerated"
TASK_TIMELINE_GENERATED = "TaskTimelineGenerated"

# ── Memory Events ────────────────────────────────────────────
MEMORY_CAPTURED = "MemoryCaptured"
MEMORY_RECALLED = "MemoryRecalled"
MEMORY_LINKED = "MemoryLinked"
MEMORY_ARCHIVED = "MemoryArchived"
MEMORY_SUPERSEDED = "MemorySuperseded"
MEMORY_INVALIDATED = "MemoryInvalidated"
MEMORY_REINFORCED = "MemoryReinforced"

# ── Workflow Events ──────────────────────────────────────────
WORKFLOW_CREATED = "WorkflowCreated"
WORKFLOW_STARTED = "WorkflowStarted"
WORKFLOW_STEP_STARTED = "WorkflowStepStarted"
WORKFLOW_STEP_COMPLETED = "WorkflowStepCompleted"
WORKFLOW_COMPLETED = "WorkflowCompleted"
WORKFLOW_PAUSED = "WorkflowPaused"
WORKFLOW_CANCELLED = "WorkflowCancelled"

# ── Agent Events ─────────────────────────────────────────────
AGENT_ASSIGNED = "AgentAssigned"
AGENT_STARTED = "AgentStarted"
AGENT_COMPLETED = "AgentCompleted"
AGENT_FAILED = "AgentFailed"

# ── Risk Events ──────────────────────────────────────────────
RISK_CALCULATED = "RiskCalculated"
RISK_ESCALATED = "RiskEscalated"

# ── Notification Events ──────────────────────────────────────
NOTIFICATION_CREATED = "NotificationCreated"
NOTIFICATION_DELIVERED = "NotificationDelivered"

# ── Briefing Events ──────────────────────────────────────────
BRIEFING_GENERATED = "BriefingGenerated"
CONTACT_BRIEFING_GENERATED = "ContactBriefingGenerated"
EXECUTIVE_BRIEFING_GENERATED = "ExecutiveBriefingGenerated"
APPROVAL_BRIEFING_GENERATED = "ApprovalBriefingGenerated"
PROJECT_TIMELINE_GENERATED = "ProjectTimelineGenerated"

# ── Timeline Events ──────────────────────────────────────────
TIMELINE_GENERATED = "TimelineGenerated"
CONTACT_TIMELINE_GENERATED = "ContactTimelineGenerated"
APPROVAL_TIMELINE_GENERATED = "ApprovalTimelineGenerated"

# ── WhatsApp Events ──────────────────────────────────────────
WHATSAPP_MESSAGE_RECEIVED = "WhatsAppMessageReceived"
WHATSAPP_MESSAGE_SENT = "WhatsAppMessageSent"
WHATSAPP_MESSAGE_DELIVERED = "WhatsAppMessageDelivered"
WHATSAPP_MESSAGE_READ = "WhatsAppMessageRead"
WHATSAPP_MESSAGE_FAILED = "WhatsAppMessageFailed"
WHATSAPP_SESSION_CREATED = "WhatsAppSessionCreated"
WHATSAPP_SESSION_OPTED_IN = "WhatsAppSessionOptedIn"
WHATSAPP_SESSION_OPTED_OUT = "WhatsAppSessionOptedOut"
WHATSAPP_APPROVAL_VOTE_RECEIVED = "WhatsAppApprovalVoteReceived"
WHATSAPP_APPROVAL_VOTE_PROCESSED = "WhatsAppApprovalVoteProcessed"
WHATSAPP_APPROVAL_SENT = "WhatsAppApprovalSent"

# ── Hermes Orchestration Events ───────────────────────────────
HERMES_RUN_STARTED = "HermesRunStarted"
HERMES_RUN_COMPLETED = "HermesRunCompleted"
HERMES_RUN_FAILED = "HermesRunFailed"
HERMES_RUN_AWAITING_APPROVAL = "HermesRunAwaitingApproval"
HERMES_STEP_DISPATCHED = "HermesStepDispatched"
HERMES_STEP_COMPLETED = "HermesStepCompleted"
HERMES_STEP_FAILED = "HermesStepFailed"
HERMES_APPROVAL_REQUESTED = "HermesApprovalRequested"
HERMES_APPROVAL_GRANTED = "HermesApprovalGranted"
HERMES_APPROVAL_REJECTED = "HermesApprovalRejected"
HERMES_MEMORY_CAPTURED = "HermesMemoryCaptured"
