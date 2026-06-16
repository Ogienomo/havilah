"""
Havilah OS — Contact Repository

Full CRM with Contact Intelligence.
"""

from sqlalchemy import text
from backend.models.contact import Contact, ContactPreference, Interaction, RelationshipScore
from backend.repositories.base import get_session


class ContactRepository:

    def save(self, data: dict) -> dict:
        """Alias for create() — used by ContactService."""
        return self.create(data)

    def create(self, data: dict) -> dict:
        with get_session() as db:
            contact = Contact(
                full_name=data.get("full_name", f"{data.get('first_name', '')} {data.get('last_name', '')}".strip()),
                first_name=data.get("first_name"),
                last_name=data.get("last_name"),
                email=data.get("email"),
                phone=data.get("phone"),
                whatsapp_id=data.get("whatsapp_id"),
                linkedin_url=data.get("linkedin_url"),
                organization_id=data.get("organization_id"),
                relationship_status=data.get("relationship_status", "active"),
                priority_level=data.get("priority_level", "medium"),
                timezone=data.get("timezone"),
            )
            db.add(contact)
            db.flush()
            return {"id": str(contact.id), "full_name": contact.full_name, "status": contact.relationship_status}

    def get_by_id(self, contact_id):
        with get_session() as db:
            contact = db.query(Contact).filter(Contact.id == contact_id).first()
            if contact is None:
                return None
            return {
                "id": str(contact.id),
                "full_name": contact.full_name,
                "email": contact.email,
                "phone": contact.phone,
                "relationship_status": contact.relationship_status,
                "priority_level": contact.priority_level,
            }

    def get_all(self):
        with get_session() as db:
            contacts = db.query(Contact).order_by(Contact.priority_level.desc()).all()
            return [
                {"id": str(c.id), "full_name": c.full_name, "email": c.email, "priority": c.priority_level}
                for c in contacts
            ]

    def add_preference(self, contact_id, category, key, value, source="explicit"):
        with get_session() as db:
            pref = ContactPreference(
                contact_id=contact_id,
                preference_category=category,
                preference_key=key,
                preference_value=value,
                source=source,
            )
            db.add(pref)
            db.flush()
            return {"id": str(pref.id)}

    def record_interaction(self, contact_id, channel, interaction_type, summary, **kwargs):
        with get_session() as db:
            interaction = Interaction(
                contact_id=contact_id,
                channel=channel,
                interaction_type=interaction_type,
                summary=summary,
                outcome=kwargs.get("outcome"),
                project_id=kwargs.get("project_id"),
                created_by=kwargs.get("created_by"),
            )
            db.add(interaction)
            db.flush()
            return {"id": str(interaction.id)}

    def update_relationship_score(self, contact_id, score, score_type="overall", trend="stable", notes=None):
        with get_session() as db:
            rs = RelationshipScore(
                contact_id=contact_id,
                score=score,
                score_type=score_type,
                trend=trend,
                notes=notes,
            )
            db.add(rs)
            db.flush()
            return {"id": str(rs.id), "score": float(rs.score), "trend": rs.trend}
