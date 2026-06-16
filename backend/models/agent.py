"""
Havilah OS — Agent Runtime Domain Model

Entities: Agent, AgentRun, AgentResult

Agent = a specialized AI worker with bounded responsibility.
AgentRun = a single execution of an agent.
AgentResult = the output of an agent run.

No agent can approve external execution — ever.

Events: AgentAssigned, AgentStarted, AgentCompleted, AgentFailed
"""

from sqlalchemy import Column, Text, ForeignKey, Numeric, Integer, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from backend.database import Base
from backend.models.mixins import UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin


class Agent(UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin, Base):
    __tablename__ = "agents"

    name = Column(Text, nullable=False, unique=True)  # planner, executive, research, writing, meeting, reviewer, critic, memory, learning, approval
    display_name = Column(Text, nullable=False)
    agent_type = Column(Text, nullable=False)  # planner, executor, researcher, writer, reviewer, critic, coordinator
    description = Column(Text)
    status = Column(Text, nullable=False, default="active")  # active, disabled, maintenance
    capabilities = Column(JSONB, nullable=False, default=list)  # ["research", "summarize", "draft"]
    model_config = Column(JSONB, default=dict)  # {"model": "gpt-4", "temperature": 0.7, "max_tokens": 4096}
    tool_access = Column(JSONB, nullable=False, default=list)  # ["web_search", "memory_read", "file_read"]
    approval_scope = Column(Text, nullable=False, default="none")  # none, low_risk_only, read_only
    max_concurrent_runs = Column(Integer, nullable=False, default=1)
    is_system = Column(Boolean, nullable=False, default=False)  # system agents cannot be disabled

    # ── Relationships ─────────────────────────────────────────
    runs = relationship("AgentRun", back_populates="agent", lazy="selectin")


class AgentRun(UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin, Base):
    __tablename__ = "agent_runs"

    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=True)
    approval_id = Column(UUID(as_uuid=True), ForeignKey("approval_requests.id"), nullable=True)
    workflow_step_id = Column(UUID(as_uuid=True), ForeignKey("workflow_steps.id"), nullable=True)
    status = Column(Text, nullable=False, default="assigned")  # assigned, running, completed, failed, cancelled
    input_context = Column(JSONB, nullable=False, default=dict)  # prompt, memory, project context
    configuration = Column(JSONB, default=dict)  # runtime overrides
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_ms = Column(Integer)
    token_usage = Column(JSONB, default=dict)  # {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    error_message = Column(Text)

    # ── Relationships ─────────────────────────────────────────
    agent = relationship("Agent", back_populates="runs")
    results = relationship("AgentResult", back_populates="agent_run", lazy="selectin")


class AgentResult(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "agent_results"

    agent_run_id = Column(UUID(as_uuid=True), ForeignKey("agent_runs.id"), nullable=False)
    result_type = Column(Text, nullable=False)  # draft, analysis, summary, recommendation, research, review
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    confidence = Column(Numeric(3, 2))
    quality_score = Column(Numeric(3, 2))  # self-assessed or reviewer-assessed
    is_actionable = Column(Boolean, nullable=False, default=False)
    requires_approval = Column(Boolean, nullable=False, default=False)
    metadata_ = Column("metadata", JSONB, default=dict)

    # ── Relationships ─────────────────────────────────────────
    agent_run = relationship("AgentRun", back_populates="results")
