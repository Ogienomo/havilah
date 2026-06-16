"""
Havilah OS — Notifications API

Events generate notifications:
  - Approval Needed, Task Overdue, Project Completed, Agent Completed/Failed
All endpoints require authentication.
"""

from uuid import UUID

from fastapi import APIRouter, Depends

from backend.api.deps import get_notification_service
from backend.api.middleware import RequirePermission
from backend.schemas.schemas import (
    NotificationCreate,
    NotificationDeliveryInput,
    NotificationResponse,
)
from backend.services.notification_service import NotificationService

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.post("/", status_code=201)
def create_notification(
    payload: NotificationCreate,
    user: dict = Depends(RequirePermission("notification:create")),
    service: NotificationService = Depends(get_notification_service),
):
    """Create a new notification. Typically called by the event system."""
    return service.create_notification(
        notification_type=payload.notification_type,
        title=payload.title,
        message=payload.message,
        priority=payload.priority,
        category=payload.category,
        recipient_id=payload.recipient_id,
        related_entity_type=payload.related_entity_type,
        related_entity_id=payload.related_entity_id,
        action_required=payload.action_required,
        action_url=payload.action_url,
    )


@router.get("/unread/{recipient_id}")
def get_unread_notifications(
    recipient_id: UUID,
    limit: int = 50,
    user: dict = Depends(RequirePermission("notification:read")),
    service: NotificationService = Depends(get_notification_service),
):
    """Get unread notifications for a recipient."""
    return service.get_unread(recipient_id, limit)


@router.post("/{notification_id}/read")
def mark_notification_read(
    notification_id: UUID,
    user: dict = Depends(RequirePermission("notification:mark_read")),
    service: NotificationService = Depends(get_notification_service),
):
    """Mark a notification as read."""
    service.mark_read(notification_id)
    return {"id": str(notification_id), "status": "read"}


@router.post("/{notification_id}/deliver")
def mark_notification_delivered(
    notification_id: UUID,
    payload: NotificationDeliveryInput,
    user: dict = Depends(RequirePermission("notification:deliver")),
    service: NotificationService = Depends(get_notification_service),
):
    """Mark a notification as delivered via a specific channel."""
    service.mark_delivered(notification_id, payload.channel, payload.external_id)
    return {"id": str(notification_id), "channel": payload.channel, "status": "delivered"}
