"""
Havilah OS — Project Delivery Domain Model

Entities: Project, Milestone, Deliverable, ProjectLink
Part of the Project bounded context.
"""

from sqlalchemy import Column, Text, ForeignKey, Date, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.database import Base
from backend.models.mixins import UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin


class Project(UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin, Base):
    __tablename__ = "projects"

    client_contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    title = Column(Text, nullable=False)
    objective = Column(Text)
    project_type = Column(Text)  # consulting, research, writing, branding, multi-delivery
    status = Column(Text, nullable=False, default="active")  # active, at_risk, on_hold, completed, cancelled
    priority = Column(Text, nullable=False, default="medium")  # low, medium, high, critical
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    start_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # ── Relationships ─────────────────────────────────────────
    client_contact = relationship("Contact", foreign_keys=[client_contact_id])
    organization = relationship("Organization", foreign_keys=[organization_id])
    milestones = relationship("Milestone", back_populates="project", lazy="selectin")
    deliverables = relationship("Deliverable", back_populates="project", lazy="selectin")
    tasks = relationship("Task", back_populates="project", lazy="selectin")
    approvals = relationship("ApprovalRequest", back_populates="project", lazy="selectin")
    interactions = relationship("Interaction", back_populates="project")
    links = relationship("ProjectLink", back_populates="project", lazy="selectin")
    research_jobs = relationship("ResearchJob", back_populates="project")
    workflows = relationship("Workflow", back_populates="project", lazy="selectin")


class Milestone(UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin, Base):
    __tablename__ = "milestones"

    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text)
    due_date = Column(Date, nullable=True)
    status = Column(Text, nullable=False, default="pending")  # pending, in_progress, completed, overdue
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # ── Relationships ─────────────────────────────────────────
    project = relationship("Project", back_populates="milestones")
    deliverables = relationship("Deliverable", back_populates="milestone")


class Deliverable(UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin, Base):
    __tablename__ = "deliverables"

    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    milestone_id = Column(UUID(as_uuid=True), ForeignKey("milestones.id"), nullable=True)
    title = Column(Text, nullable=False)
    deliverable_type = Column(Text, nullable=False)  # document, research, strategy, content, report
    status = Column(Text, nullable=False, default="pending")  # pending, in_progress, under_review, approved, delivered
    version_label = Column(Text)
    file_id = Column(UUID(as_uuid=True))  # FK to file_objects (future)

    # ── Relationships ─────────────────────────────────────────
    project = relationship("Project", back_populates="deliverables")
    milestone = relationship("Milestone", back_populates="deliverables")


class ProjectLink(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "project_links"

    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    linked_entity_type = Column(Text, nullable=False)  # approval, task, memory, contact, research
    linked_entity_id = Column(UUID(as_uuid=True), nullable=False)
    link_role = Column(Text, nullable=False)  # primary, related, blocking

    # ── Relationships ─────────────────────────────────────────
    project = relationship("Project", back_populates="links")
