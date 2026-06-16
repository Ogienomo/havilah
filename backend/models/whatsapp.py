"""
Havilah OS — WhatsApp Integration Domain Model

Entities: WhatsAppSession, WhatsAppMessage, WhatsAppTemplate, WhatsAppApprovalVote

The WhatsApp Interface is the primary channel for:
1. Receiving approval requests on-the-go
2. Responding with approve/reject/escalate
3. Getting executive briefings via WhatsApp
4. Two-way communication with contacts

Core principle: Every WhatsApp approval is logged in the Approval Ledger.
No action executes without passing through the 7+2 state machine.
"""

from sqlalchemy import Column, Text, ForeignKey, Integer, Boolean, DateTime, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from backend.database import Base
from backend.models.mixins import UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin


class WhatsAppSession(UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin, Base):
    """Represents an active WhatsApp conversation session with a user."""
    __tablename__ = "whatsapp_sessions"

    phone_number = Column(Text, nullable=False, unique=True, index=True)
    whatsapp_id = Column(Text, nullable=True, unique=True)  # WhatsApp Business API contact ID
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # Linked Havilah user
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=True)  # Linked CRM contact
    status = Column(Text, nullable=False, default="active")  # active, paused, expired, blocked
    session_context = Column(JSONB, default=dict)  # Current conversation context
    language = Column(Text, nullable=False, default="en")  # en, yo, ha, ig (Nigerian languages)
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    last_inbound_at = Column(DateTime(timezone=True), nullable=True)
    last_outbound_at = Column(DateTime(timezone=True), nullable=True)
    message_count = Column(Integer, nullable=False, default=0)
    opted_in = Column(Boolean, nullable=False, default=False)  # User has opted in to WhatsApp notifications
    opted_in_at = Column(DateTime(timezone=True), nullable=True)
    opted_out_at = Column(DateTime(timezone=True), nullable=True)

    # ── Relationships ─────────────────────────────────────────
    messages = relationship("WhatsAppMessage", back_populates="session", lazy="selectin",
                            order_by="WhatsAppMessage.created_at.desc()")
    approval_votes = relationship("WhatsAppApprovalVote", back_populates="session", lazy="selectin")


class WhatsAppMessage(UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin, Base):
    """Every WhatsApp message sent or received — full audit trail."""
    __tablename__ = "whatsapp_messages"

    session_id = Column(UUID(as_uuid=True), ForeignKey("whatsapp_sessions.id"), nullable=False, index=True)
    direction = Column(Text, nullable=False)  # inbound, outbound
    message_type = Column(Text, nullable=False, default="text")  # text, interactive, template, media, document
    status = Column(Text, nullable=False, default="pending")  # pending, sent, delivered, read, failed, undeliverable
    content_body = Column(Text)  # Text content of the message
    media_url = Column(Text)  # URL for media attachments
    media_type = Column(Text)  # image, video, audio, document, sticker
    interactive_type = Column(Text)  # button, list, product — for interactive messages
    interactive_payload = Column(JSONB)  # Button/list selection payload
    template_name = Column(Text)  # WhatsApp template name used
    template_parameters = Column(JSONB)  # Template parameter values
    whatsapp_message_id = Column(Text, unique=True)  # Message ID from WhatsApp API
    external_timestamp = Column(DateTime(timezone=True), nullable=True)  # Timestamp from WhatsApp
    sender_phone = Column(Text)  # For inbound: sender's phone number
    recipient_phone = Column(Text)  # For outbound: recipient's phone number
    related_entity_type = Column(Text)  # approval, briefing, task, notification
    related_entity_id = Column(UUID(as_uuid=True))  # ID of the related entity
    approval_id = Column(UUID(as_uuid=True), ForeignKey("approval_requests.id"), nullable=True)
    error_code = Column(Text)  # Error code if delivery failed
    error_message = Column(Text)  # Error description
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)

    # ── Relationships ─────────────────────────────────────────
    session = relationship("WhatsAppSession", back_populates="messages")
    approval = relationship("ApprovalRequest", back_populates="whatsapp_messages")


class WhatsAppTemplate(UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin, Base):
    """WhatsApp message templates — must be pre-approved by Meta."""
    __tablename__ = "whatsapp_templates"

    name = Column(Text, nullable=False, unique=True)  # Template name (used in API calls)
    category = Column(Text, nullable=False)  # AUTHENTICATION, MARKETING, UTILITY
    language = Column(Text, nullable=False, default="en")  # Template language code
    body_text = Column(Text, nullable=False)  # Template body with {{1}}, {{2}} placeholders
    header_type = Column(Text)  # text, image, video, document, none
    header_text = Column(Text)  # Header text (if header_type=text)
    footer_text = Column(Text)
    button_type = Column(Text)  # none, quick_reply, url, call
    button_payload = Column(JSONB)  # Button definitions
    status = Column(Text, nullable=False, default="draft")  # draft, pending_approval, approved, rejected, paused
    external_template_id = Column(Text)  # Template ID from WhatsApp API
    quality_score = Column(Text)  # GREEN, YELLOW, RED (WhatsApp quality rating)
    use_count = Column(Integer, nullable=False, default=0)

    # ── Template Types ────────────────────────────────────────
    # approval_request: "You have a new approval request: {{1}}. Risk: {{2}}"
    # approval_reminder: "Reminder: Approval pending for {{1}}"
    # briefing_summary: "Your morning briefing: {{1}}"
    # task_overdue: "Task '{{1}}' is overdue. Due: {{2}}"
    # execution_result: "Action '{{1}}' has been {{2}}"


class WhatsAppApprovalVote(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Tracks approval/rejection decisions made via WhatsApp."""
    __tablename__ = "whatsapp_approval_votes"

    session_id = Column(UUID(as_uuid=True), ForeignKey("whatsapp_sessions.id"), nullable=False, index=True)
    approval_id = Column(UUID(as_uuid=True), ForeignKey("approval_requests.id"), nullable=False, index=True)
    message_id = Column(UUID(as_uuid=True), ForeignKey("whatsapp_messages.id"), nullable=True)
    vote = Column(Text, nullable=False)  # approve, reject, escalate, defer
    vote_source = Column(Text, nullable=False, default="whatsapp_button")  # whatsapp_button, whatsapp_text, whatsapp_reply
    confidence = Column(Numeric(3, 2), nullable=True)  # Confidence score for NLP-parsed votes
    reason = Column(Text)  # Optional reason text
    processed = Column(Boolean, nullable=False, default=False)  # Whether the vote was applied to the approval
    processed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text)  # If processing failed

    # ── Relationships ─────────────────────────────────────────
    session = relationship("WhatsAppSession", back_populates="approval_votes")
    approval = relationship("ApprovalRequest", back_populates="whatsapp_votes")
