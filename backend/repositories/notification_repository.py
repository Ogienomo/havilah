"""
Havilah OS — Notification Repository
"""

from sqlalchemy import text
from backend.models.notification import Notification, NotificationDelivery
from backend.repositories.base import get_session


class NotificationRepository:

    def create(self, notification_type, title, message, **kwargs) -> dict:
        with get_session() as db:
            notification = Notification(
                notification_type=notification_type,
                title=title,
                message=message,
                priority=kwargs.get("priority", "medium"),
                category=kwargs.get("category", "operational"),
                recipient_id=kwargs.get("recipient_id"),
                related_entity_type=kwargs.get("related_entity_type"),
                related_entity_id=kwargs.get("related_entity_id"),
                action_required=kwargs.get("action_required", False),
                action_url=kwargs.get("action_url"),
            )
            db.add(notification)
            db.flush()
            return {"id": str(notification.id), "type": notification.notification_type}

    def mark_delivered(self, notification_id, channel, external_id=None):
        with get_session() as db:
            delivery = NotificationDelivery(
                notification_id=notification_id,
                channel=channel,
                status="delivered",
                external_id=external_id,
            )
            db.add(delivery)
            db.execute(
                text("UPDATE notifications SET status = 'delivered' WHERE id = CAST(:nid AS UUID)"),
                {"nid": str(notification_id)},
            )
            db.flush()

    def mark_read(self, notification_id):
        with get_session() as db:
            db.execute(
                text("UPDATE notifications SET status = 'read', read_at = NOW() WHERE id = CAST(:nid AS UUID)"),
                {"nid": str(notification_id)},
            )

    def get_unread(self, recipient_id, limit=50):
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT id, notification_type, title, message, priority, action_required, created_at
                    FROM notifications
                    WHERE recipient_id = CAST(:rid AS UUID) AND status IN ('pending', 'sent', 'delivered')
                    ORDER BY priority DESC, created_at DESC
                    LIMIT :limit
                """),
                {"rid": str(recipient_id), "limit": limit},
            )
            return [dict(row._mapping) for row in result]
