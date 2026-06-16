"""
Havilah OS — Research Domain Model

Entities: ResearchJob, ResearchSource, ResearchNote, ResearchOutput
Part of the Research bounded context.

Research ≠ Knowledge Management — research is a work process.
"""

from sqlalchemy import Column, Text, ForeignKey, Numeric, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.database import Base
from backend.models.mixins import UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin


class ResearchJob(UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin, Base):
    __tablename__ = "research_jobs"

    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    title = Column(Text, nullable=False)
    research_question = Column(Text, nullable=False)
    status = Column(Text, nullable=False, default="pending")  # pending, in_progress, completed, failed
    priority = Column(Text, nullable=False, default="medium")  # low, medium, high, critical
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    assigned_agent_run_id = Column(UUID(as_uuid=True), ForeignKey("agent_runs.id"), nullable=True)
    summary = Column(Text)
    confidence = Column(Numeric(3, 2))

    # ── Relationships ─────────────────────────────────────────
    project = relationship("Project", back_populates="research_jobs")
    sources = relationship("ResearchSource", back_populates="research_job", lazy="selectin")
    notes = relationship("ResearchNote", back_populates="research_job", lazy="selectin")
    outputs = relationship("ResearchOutput", back_populates="research_job", lazy="selectin")


class ResearchSource(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "research_sources"

    research_job_id = Column(UUID(as_uuid=True), ForeignKey("research_jobs.id"), nullable=False)
    source_title = Column(Text, nullable=False)
    source_type = Column(Text, nullable=False)  # academic, news, report, interview, web, document
    source_reference = Column(Text)
    source_url = Column(Text)
    source_summary = Column(Text)
    reliability_score = Column(Numeric(3, 2))  # 0.0-1.0

    # ── Relationships ─────────────────────────────────────────
    research_job = relationship("ResearchJob", back_populates="sources")


class ResearchNote(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "research_notes"

    research_job_id = Column(UUID(as_uuid=True), ForeignKey("research_jobs.id"), nullable=False)
    source_id = Column(UUID(as_uuid=True), ForeignKey("research_sources.id"), nullable=True)
    note_text = Column(Text, nullable=False)
    note_type = Column(Text, nullable=False, default="observation")  # observation, insight, question, contradiction

    # ── Relationships ─────────────────────────────────────────
    research_job = relationship("ResearchJob", back_populates="notes")
    source = relationship("ResearchSource")


class ResearchOutput(UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin, Base):
    __tablename__ = "research_outputs"

    research_job_id = Column(UUID(as_uuid=True), ForeignKey("research_jobs.id"), nullable=False)
    output_type = Column(Text, nullable=False)  # brief, summary, analysis, comparison, citation_graph
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    confidence = Column(Numeric(3, 2))
    status = Column(Text, nullable=False, default="draft")  # draft, reviewed, approved

    # ── Relationships ─────────────────────────────────────────
    research_job = relationship("ResearchJob", back_populates="outputs")
