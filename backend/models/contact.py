"""
Havilah OS — Contact / CRM Domain Model

Entities: Contact, ContactPreference, Interaction, CommunicationHistory, RelationshipScore
Part of the CRM bounded context with Contact Intelligence.
"""

from sqlalchemy import Column, Text, ForeignKey, Numeric, Integer, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.database import Base
from backend.models.mixins import UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin


class Contact(UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin, Base):
    __tablename__ = "contacts"

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    full_name = Column(Text, nullable=False)
    first_name = Column(Text)
    last_name = Column(Text)
    role_title = Column(Text)
    email = Column(Text)  # TODO: migrate to CITEXT with Alembic
    phone = Column(Text)
    whatsapp_id = Column(Text)
    linkedin_url = Column(Text)
    relationship_status = Column(Text, nullable=False, default="active")
    priority_level = Column(Text, nullable=False, default="medium")  # low, medium, high, critical
    timezone = Column(Text)
    notes = Column(Text)

    # ── Relationships ─────────────────────────────────────────
    organization = relationship("Organization", back_populates="contacts")
    preferences = relationship("ContactPreference", back_populates="contact", lazy="selectin")
    interactions = relationship("Interaction", back_populates="contact", lazy="selectin")
    communication_history = relationship("CommunicationHistory", back_populates="contact", lazy="selectin")
    relationship_scores = relationship("RelationshipScore", back_populates="contact", lazy="selectin")
    stakeholder_records = relationship("Stakeholder", back_populates="contact")


class ContactPreference(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "contact_preferences"

    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=False)
    preference_category = Column(Text, nullable=False)  # communication, content, scheduling
    preference_key = Column(Text, nullable=False)
    preference_value = Column(Text, nullable=False)
    confidence = Column(Numeric(3, 2), nullable=False, default=1.0)
    source = Column(Text, nullable=False)  # explicit, inferred, system
    last_verified_at = Column(DateTime(timezone=True), nullable=True)

    # ── Relationships ─────────────────────────────────────────
    contact = relationship("Contact", back_populates="preferences")


class Interaction(UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin, Base):
    __tablename__ = "interactions"

    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    channel = Column(Text, nullable=False)  # email, whatsapp, linkedin, phone, meeting
    interaction_type = Column(Text, nullable=False)  # inbound, outbound, meeting, note
    summary = Column(Text, nullable=False)
    outcome = Column(Text)
    occurred_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # ── Relationships ─────────────────────────────────────────
    contact = relationship("Contact", back_populates="interactions")
    project = relationship("Project", back_populates="interactions")


class CommunicationHistory(UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin, Base):
    __tablename__ = "communication_history"

    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=False)
    direction = Column(Text, nullable=False)  # inbound, outbound
    channel = Column(Text, nullable=False)  # email, whatsapp, linkedin
    subject = Column(Text)
    body = Column(Text)
    status = Column(Text, nullable=False, default="sent")  # draft, sent, delivered, read, failed
    approval_id = Column(UUID(as_uuid=True), ForeignKey("approval_requests.id"), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)

    # ── Relationships ─────────────────────────────────────────
    contact = relationship("Contact", back_populates="communication_history")
    approval = relationship("ApprovalRequest", back_populates="communications")


class RelationshipScore(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "relationship_scores"

    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=False)
    score = Column(Numeric(5, 2), nullable=False, default=50.0)  # 0-100
    score_type = Column(Text, nullable=False, default="overall")  # overall, responsiveness, engagement, trust
    trend = Column(Text, nullable=False, default="stable")  # improving, stable, declining
    calculated_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text)

    # ── Relationships ─────────────────────────────────────────
    contact = relationship("Contact", back_populates="relationship_scores")
