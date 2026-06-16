"""
Havilah OS — Notification Service

Events generate notifications:
  - Approval Needed, Task Overdue, Project Completed, Agent Completed/Failed
"""

from backend.repositories.notification_repository import NotificationRepository
from backend.repositories.event_repository import EventRepository
from backend.events import NOTIFICATION_CREATED, NOTIFICATION_DELIVERED


class NotificationService:

    def __init__(self):
        self.repository = NotificationRepository()
        self.event_repository = EventRepository()

    def create_notification(self, notification_type, title, message, **kwargs):
        notification = self.repository.create(notification_type, title, message, **kwargs)

        self.event_repository.save(
            aggregate_type="notification",
            aggregate_id=notification["id"],
            event_type=NOTIFICATION_CREATED,
            payload={"type": notification_type, "title": title},
        )

        return notification

    def mark_delivered(self, notification_id, channel, external_id=None):
        self.repository.mark_delivered(notification_id, channel, external_id)

        self.event_repository.save(
            aggregate_type="notification",
            aggregate_id=str(notification_id),
            event_type=NOTIFICATION_DELIVERED,
            payload={"channel": channel},
        )

    def mark_read(self, notification_id):
        self.repository.mark_read(notification_id)

    def get_unread(self, recipient_id, limit=50):
        return self.repository.get_unread(recipient_id, limit)

    # ── Convenience Methods ───────────────────────────────────

    def notify_approval_needed(self, approval_id, summary, recipient_id):
        return self.create_notification(
            notification_type="approval_needed",
            title="Approval Needed",
            message=summary,
            priority="high",
            category="approval",
            recipient_id=recipient_id,
            related_entity_type="approval",
            related_entity_id=approval_id,
            action_required=True,
        )

    def notify_task_overdue(self, task_id, title, recipient_id):
        return self.create_notification(
            notification_type="task_overdue",
            title="Task Overdue",
            message=f"Task '{title}' is overdue",
            priority="high",
            category="operational",
            recipient_id=recipient_id,
            related_entity_type="task",
            related_entity_id=task_id,
        )

    def notify_project_completed(self, project_id, title, recipient_id):
        return self.create_notification(
            notification_type="project_completed",
            title="Project Completed",
            message=f"Project '{title}' has been completed",
            priority="medium",
            category="operational",
            recipient_id=recipient_id,
            related_entity_type="project",
            related_entity_id=project_id,
        )
