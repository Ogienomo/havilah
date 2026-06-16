"""
Havilah OS — Knowledge Domain Model

Entities: KnowledgeArtifact, KnowledgeVersion
Part of the Knowledge bounded context.

Knowledge ≠ Memory:
  - Knowledge is approved canonical truth (policies, SOPs, templates)
  - Memory is contextual recall (preferences, observations, history)

Artifact Lifecycle: draft → review → approved → published → deprecated → archived
"""

from sqlalchemy import Column, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.database import Base
from backend.models.mixins import UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin


class KnowledgeArtifact(UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin, Base):
    __tablename__ = "knowledge_artifacts"

    title = Column(Text, nullable=False)
    knowledge_type = Column(Text, nullable=False)  # policy, sop, template, framework, playbook, reference
    category = Column(Text, nullable=False)  # operations, research, content, executive, compliance
    summary = Column(Text)
    status = Column(Text, nullable=False, default="draft")  # draft, review, approved, published, deprecated, archived
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    canonical_version_id = Column(UUID(as_uuid=True), nullable=True)  # FK to knowledge_versions.id

    # ── Relationships ─────────────────────────────────────────
    versions = relationship("KnowledgeVersion", back_populates="artifact", lazy="selectin")


class KnowledgeVersion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "knowledge_versions"

    knowledge_artifact_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_artifacts.id"), nullable=False)
    version_label = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    change_note = Column(Text)
    version_status = Column(Text, nullable=False, default="draft")  # draft, approved, published
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    # ── Relationships ─────────────────────────────────────────
    artifact = relationship("KnowledgeArtifact", back_populates="versions")
