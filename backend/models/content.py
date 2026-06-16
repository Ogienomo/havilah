"""
Havilah OS — Content Domain Model

Entities: ContentDraft, ContentVersion, ContentComment
Part of the Content bounded context.
"""

from sqlalchemy import Column, Text, ForeignKey, Numeric, Integer, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from backend.database import Base
from backend.models.mixins import UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin


class ContentDraft(UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin, Base):
    __tablename__ = "content_drafts"

    title = Column(Text, nullable=False)
    content_type = Column(Text, nullable=False)  # linkedin_post, article, proposal, report, email, marketing_asset
    status = Column(Text, nullable=False, default="draft")  # draft, in_review, approved, published, archived
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=True)
    approval_id = Column(UUID(as_uuid=True), ForeignKey("approval_requests.id"), nullable=True)
    target_channel = Column(Text)  # linkedin, email, whatsapp, blog
    tags = Column(JSONB, default=list)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # ── Relationships ─────────────────────────────────────────
    versions = relationship("ContentVersion", back_populates="draft", lazy="selectin")
    comments = relationship("ContentComment", back_populates="draft", lazy="selectin")


class ContentVersion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "content_versions"

    draft_id = Column(UUID(as_uuid=True), ForeignKey("content_drafts.id"), nullable=False)
    version_number = Column(Integer, nullable=False, default=1)
    content = Column(Text, nullable=False)
    change_summary = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    is_current = Column(Boolean, nullable=False, default=True)

    # ── Relationships ─────────────────────────────────────────
    draft = relationship("ContentDraft", back_populates="versions")


class ContentComment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "content_comments"

    draft_id = Column(UUID(as_uuid=True), ForeignKey("content_drafts.id"), nullable=False)
    comment_text = Column(Text, nullable=False)
    comment_type = Column(Text, nullable=False, default="feedback")  # feedback, approval, revision_request
    commented_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # ── Relationships ─────────────────────────────────────────
    draft = relationship("ContentDraft", back_populates="comments")
