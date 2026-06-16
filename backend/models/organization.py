"""
Havilah OS — Organization Domain Model

Entities: Organization, Department, Stakeholder
Part of the Organization bounded context.
"""

from sqlalchemy import Column, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.database import Base
from backend.models.mixins import UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin


class Organization(UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin, Base):
    __tablename__ = "organizations"

    name = Column(Text, nullable=False)
    organization_type = Column(Text)  # client, partner, vendor, internal, subsidiary
    status = Column(Text, nullable=False, default="active")
    description = Column(Text)
    industry = Column(Text)
    website = Column(Text)

    # ── Relationships ─────────────────────────────────────────
    departments = relationship("Department", back_populates="organization", lazy="selectin")
    contacts = relationship("Contact", back_populates="organization", lazy="selectin")
    stakeholders = relationship("Stakeholder", back_populates="organization", lazy="selectin")
    approval_requests = relationship("ApprovalRequest", back_populates="organization")


class Department(UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin, Base):
    __tablename__ = "departments"

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name = Column(Text, nullable=False)
    department_type = Column(Text)  # operations, research, content, executive, consulting
    status = Column(Text, nullable=False, default="active")
    head_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # ── Relationships ─────────────────────────────────────────
    organization = relationship("Organization", back_populates="departments")


class Stakeholder(UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin, Base):
    __tablename__ = "stakeholders"

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=True)
    stakeholder_type = Column(Text, nullable=False)  # decision_maker, influencer, champion, sponsor
    influence_level = Column(Text, nullable=False, default="medium")  # low, medium, high
    interest_level = Column(Text, nullable=False, default="medium")  # low, medium, high
    engagement_status = Column(Text, nullable=False, default="active")  # active, dormant, disengaged
    notes = Column(Text)

    # ── Relationships ─────────────────────────────────────────
    organization = relationship("Organization", back_populates="stakeholders")
    contact = relationship("Contact", back_populates="stakeholder_records")
