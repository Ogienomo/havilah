"""
Havilah OS — WhatsApp Repository

Data access layer for WhatsApp sessions, messages, templates, and approval votes.
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import desc, or_

from backend.repositories.base import get_session
from backend.models.whatsapp import (
    WhatsAppSession,
    WhatsAppMessage,
    WhatsAppTemplate,
    WhatsAppApprovalVote,
)


class WhatsAppRepository:

    # ── Session Operations ────────────────────────────────────────

    def get_or_create_session(self, phone_number: str, **kwargs) -> dict:
        """Get existing session or create a new one for a phone number."""
        with get_session() as db:
            session = db.query(WhatsAppSession).filter(
                WhatsAppSession.phone_number == phone_number
            ).first()
            if session:
                return self._session_to_dict(session)
            session = WhatsAppSession(phone_number=phone_number, **kwargs)
            db.add(session)
            db.flush()
            return self._session_to_dict(session)

    def get_session_by_phone(self, phone_number: str) -> dict | None:
        with get_session() as db:
            session = db.query(WhatsAppSession).filter(
                WhatsAppSession.phone_number == phone_number
            ).first()
            return self._session_to_dict(session) if session else None

    def get_session_by_id(self, session_id: str) -> dict | None:
        with get_session() as db:
            session = db.query(WhatsAppSession).filter(
                WhatsAppSession.id == session_id
            ).first()
            return self._session_to_dict(session) if session else None

    def update_session(self, session_id: str, **kwargs) -> dict | None:
        with get_session() as db:
            session = db.query(WhatsAppSession).filter(
                WhatsAppSession.id == session_id
            ).first()
            if not session:
                return None
            for key, value in kwargs.items():
                setattr(session, key, value)
            db.flush()
            return self._session_to_dict(session)

    def list_sessions(self, status: str | None = None, limit: int = 50, offset: int = 0) -> list[dict]:
        with get_session() as db:
            query = db.query(WhatsAppSession)
            if status:
                query = query.filter(WhatsAppSession.status == status)
            query = query.order_by(desc(WhatsAppSession.last_message_at))
            sessions = query.offset(offset).limit(limit).all()
            return [self._session_to_dict(s) for s in sessions]

    def opt_in_session(self, session_id: str) -> dict | None:
        now = datetime.now(timezone.utc)
        return self.update_session(
            session_id,
            opted_in=True,
            opted_in_at=now,
            opted_out_at=None,
            status="active",
        )

    def opt_out_session(self, session_id: str) -> dict | None:
        now = datetime.now(timezone.utc)
        return self.update_session(
            session_id,
            opted_in=False,
            opted_out_at=now,
            status="paused",
        )

    # ── Message Operations ────────────────────────────────────────

    def create_message(self, session_id: str, direction: str, message_type: str,
                       content_body: str = None, **kwargs) -> dict:
        with get_session() as db:
            msg = WhatsAppMessage(
                session_id=session_id,
                direction=direction,
                message_type=message_type,
                content_body=content_body,
                **kwargs,
            )
            db.add(msg)
            # Update session stats
            session = db.query(WhatsAppSession).filter(
                WhatsAppSession.id == session_id
            ).first()
            if session:
                session.message_count = (session.message_count or 0) + 1
                session.last_message_at = datetime.now(timezone.utc)
                if direction == "inbound":
                    session.last_inbound_at = datetime.now(timezone.utc)
                else:
                    session.last_outbound_at = datetime.now(timezone.utc)
            db.flush()
            return self._message_to_dict(msg)

    def get_message(self, message_id: str) -> dict | None:
        with get_session() as db:
            msg = db.query(WhatsAppMessage).filter(
                WhatsAppMessage.id == message_id
            ).first()
            return self._message_to_dict(msg) if msg else None

    def get_message_by_whatsapp_id(self, whatsapp_message_id: str) -> dict | None:
        with get_session() as db:
            msg = db.query(WhatsAppMessage).filter(
                WhatsAppMessage.whatsapp_message_id == whatsapp_message_id
            ).first()
            return self._message_to_dict(msg) if msg else None

    def update_message_status(self, message_id: str, status: str, **kwargs) -> dict | None:
        with get_session() as db:
            msg = db.query(WhatsAppMessage).filter(
                WhatsAppMessage.id == message_id
            ).first()
            if not msg:
                return None
            msg.status = status
            for key, value in kwargs.items():
                setattr(msg, key, value)
            db.flush()
            return self._message_to_dict(msg)

    def get_session_messages(self, session_id: str, limit: int = 50, offset: int = 0) -> list[dict]:
        with get_session() as db:
            messages = db.query(WhatsAppMessage).filter(
                WhatsAppMessage.session_id == session_id
            ).order_by(desc(WhatsAppMessage.created_at)).offset(offset).limit(limit).all()
            return [self._message_to_dict(m) for m in messages]

    def get_pending_approval_messages(self, approval_id: str) -> list[dict]:
        with get_session() as db:
            messages = db.query(WhatsAppMessage).filter(
                WhatsAppMessage.approval_id == approval_id,
                WhatsAppMessage.direction == "outbound",
                WhatsAppMessage.related_entity_type == "approval",
            ).order_by(desc(WhatsAppMessage.created_at)).all()
            return [self._message_to_dict(m) for m in messages]

    # ── Template Operations ────────────────────────────────────────

    def create_template(self, name: str, category: str, language: str,
                        body_text: str, **kwargs) -> dict:
        with get_session() as db:
            tmpl = WhatsAppTemplate(
                name=name,
                category=category,
                language=language,
                body_text=body_text,
                **kwargs,
            )
            db.add(tmpl)
            db.flush()
            return self._template_to_dict(tmpl)

    def get_template(self, name: str, language: str = "en") -> dict | None:
        with get_session() as db:
            tmpl = db.query(WhatsAppTemplate).filter(
                WhatsAppTemplate.name == name,
                WhatsAppTemplate.language == language,
                WhatsAppTemplate.status == "approved",
            ).first()
            return self._template_to_dict(tmpl) if tmpl else None

    def list_templates(self, status: str | None = None, limit: int = 50) -> list[dict]:
        with get_session() as db:
            query = db.query(WhatsAppTemplate)
            if status:
                query = query.filter(WhatsAppTemplate.status == status)
            templates = query.order_by(desc(WhatsAppTemplate.created_at)).limit(limit).all()
            return [self._template_to_dict(t) for t in templates]

    def update_template(self, template_id: str, **kwargs) -> dict | None:
        with get_session() as db:
            tmpl = db.query(WhatsAppTemplate).filter(
                WhatsAppTemplate.id == template_id
            ).first()
            if not tmpl:
                return None
            for key, value in kwargs.items():
                setattr(tmpl, key, value)
            db.flush()
            return self._template_to_dict(tmpl)

    def increment_template_use(self, template_id: str) -> None:
        with get_session() as db:
            tmpl = db.query(WhatsAppTemplate).filter(
                WhatsAppTemplate.id == template_id
            ).first()
            if tmpl:
                tmpl.use_count = (tmpl.use_count or 0) + 1

    # ── Approval Vote Operations ──────────────────────────────────

    def create_approval_vote(self, session_id: str, approval_id: str,
                             vote: str, **kwargs) -> dict:
        with get_session() as db:
            v = WhatsAppApprovalVote(
                session_id=session_id,
                approval_id=approval_id,
                vote=vote,
                **kwargs,
            )
            db.add(v)
            db.flush()
            return self._vote_to_dict(v)

    def get_approval_votes(self, approval_id: str) -> list[dict]:
        with get_session() as db:
            votes = db.query(WhatsAppApprovalVote).filter(
                WhatsAppApprovalVote.approval_id == approval_id
            ).order_by(desc(WhatsAppApprovalVote.created_at)).all()
            return [self._vote_to_dict(v) for v in votes]

    def mark_vote_processed(self, vote_id: str, error_message: str = None) -> dict | None:
        with get_session() as db:
            v = db.query(WhatsAppApprovalVote).filter(
                WhatsAppApprovalVote.id == vote_id
            ).first()
            if not v:
                return None
            v.processed = True
            v.processed_at = datetime.now(timezone.utc)
            if error_message:
                v.error_message = error_message
            db.flush()
            return self._vote_to_dict(v)

    def get_unprocessed_votes(self, limit: int = 100) -> list[dict]:
        with get_session() as db:
            votes = db.query(WhatsAppApprovalVote).filter(
                WhatsAppApprovalVote.processed == False
            ).order_by(WhatsAppApprovalVote.created_at).limit(limit).all()
            return [self._vote_to_dict(v) for v in votes]

    # ── Serialization Helpers ──────────────────────────────────────

    @staticmethod
    def _session_to_dict(session: WhatsAppSession) -> dict:
        return {
            "id": str(session.id),
            "phone_number": session.phone_number,
            "whatsapp_id": session.whatsapp_id,
            "user_id": str(session.user_id) if session.user_id else None,
            "contact_id": str(session.contact_id) if session.contact_id else None,
            "status": session.status,
            "session_context": session.session_context or {},
            "language": session.language,
            "last_message_at": session.last_message_at.isoformat() if session.last_message_at else None,
            "last_inbound_at": session.last_inbound_at.isoformat() if session.last_inbound_at else None,
            "last_outbound_at": session.last_outbound_at.isoformat() if session.last_outbound_at else None,
            "message_count": session.message_count or 0,
            "opted_in": session.opted_in,
            "opted_in_at": session.opted_in_at.isoformat() if session.opted_in_at else None,
            "opted_out_at": session.opted_out_at.isoformat() if session.opted_out_at else None,
            "created_at": session.created_at.isoformat() if session.created_at else None,
        }

    @staticmethod
    def _message_to_dict(msg: WhatsAppMessage) -> dict:
        return {
            "id": str(msg.id),
            "session_id": str(msg.session_id),
            "direction": msg.direction,
            "message_type": msg.message_type,
            "status": msg.status,
            "content_body": msg.content_body,
            "media_url": msg.media_url,
            "media_type": msg.media_type,
            "interactive_type": msg.interactive_type,
            "interactive_payload": msg.interactive_payload,
            "template_name": msg.template_name,
            "template_parameters": msg.template_parameters,
            "whatsapp_message_id": msg.whatsapp_message_id,
            "sender_phone": msg.sender_phone,
            "recipient_phone": msg.recipient_phone,
            "related_entity_type": msg.related_entity_type,
            "related_entity_id": str(msg.related_entity_id) if msg.related_entity_id else None,
            "approval_id": str(msg.approval_id) if msg.approval_id else None,
            "error_code": msg.error_code,
            "error_message": msg.error_message,
            "delivered_at": msg.delivered_at.isoformat() if msg.delivered_at else None,
            "read_at": msg.read_at.isoformat() if msg.read_at else None,
            "created_at": msg.created_at.isoformat() if msg.created_at else None,
        }

    @staticmethod
    def _template_to_dict(tmpl: WhatsAppTemplate) -> dict:
        return {
            "id": str(tmpl.id),
            "name": tmpl.name,
            "category": tmpl.category,
            "language": tmpl.language,
            "body_text": tmpl.body_text,
            "header_type": tmpl.header_type,
            "header_text": tmpl.header_text,
            "footer_text": tmpl.footer_text,
            "button_type": tmpl.button_type,
            "button_payload": tmpl.button_payload,
            "status": tmpl.status,
            "external_template_id": tmpl.external_template_id,
            "quality_score": tmpl.quality_score,
            "use_count": tmpl.use_count or 0,
            "created_at": tmpl.created_at.isoformat() if tmpl.created_at else None,
        }

    @staticmethod
    def _vote_to_dict(v: WhatsAppApprovalVote) -> dict:
        return {
            "id": str(v.id),
            "session_id": str(v.session_id),
            "approval_id": str(v.approval_id),
            "message_id": str(v.message_id) if v.message_id else None,
            "vote": v.vote,
            "vote_source": v.vote_source,
            "confidence": float(v.confidence) if v.confidence else None,
            "reason": v.reason,
            "processed": v.processed,
            "processed_at": v.processed_at.isoformat() if v.processed_at else None,
            "error_message": v.error_message,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        }
