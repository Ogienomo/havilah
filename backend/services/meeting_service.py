"""
Havilah OS — Meeting Service

Meetings are structured workflows, not casual chats.
Every meeting produces decisions and action items.
"""

from backend.repositories.base import get_session
from backend.repositories.event_repository import EventRepository
from backend.models.meeting import Meeting, AgendaItem, MeetingDecision, MeetingActionItem

from sqlalchemy import text


class MeetingService:

    def __init__(self):
        self.event_repository = EventRepository()

    def create_meeting(self, data: dict) -> dict:
        with get_session() as db:
            meeting = Meeting(
                title=data["title"],
                meeting_type=data.get("meeting_type", "internal"),
                project_id=data.get("project_id"),
                scheduled_at=data.get("scheduled_at"),
                duration_minutes=data.get("duration_minutes"),
                organizer_id=data.get("organizer_id"),
                participants=data.get("participants", []),
            )
            db.add(meeting)
            db.flush()

            self.event_repository.save(
                aggregate_type="meeting",
                aggregate_id=str(meeting.id),
                event_type="MeetingCreated",
                payload={"title": meeting.title, "meeting_type": meeting.meeting_type},
            )

            return {
                "id": str(meeting.id),
                "title": meeting.title,
                "status": meeting.status,
                "scheduled_at": meeting.scheduled_at.isoformat() if meeting.scheduled_at else None,
            }

    def get_meeting(self, meeting_id) -> dict | None:
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT id, title, meeting_type, status, project_id, scheduled_at,
                           completed_at, duration_minutes, summary, organizer_id, participants
                    FROM meetings
                    WHERE id = CAST(:mid AS UUID)
                """),
                {"mid": str(meeting_id)},
            )
            row = result.mappings().first()
            if not row:
                return None
            return dict(row)

    def list_meetings(self, project_id=None, status=None, limit=50):
        with get_session() as db:
            conditions = []
            params = {"limit": limit}
            if project_id:
                conditions.append("project_id = CAST(:pid AS UUID)")
                params["pid"] = str(project_id)
            if status:
                conditions.append("status = :status")
                params["status"] = status

            where = "WHERE " + " AND ".join(conditions) if conditions else ""
            result = db.execute(
                text(f"""
                    SELECT id, title, meeting_type, status, scheduled_at, organizer_id
                    FROM meetings {where}
                    ORDER BY scheduled_at DESC NULLS LAST
                    LIMIT :limit
                """),
                params,
            )
            return [dict(row) for row in result.mappings().all()]

    def add_agenda_item(self, meeting_id, data: dict) -> dict:
        with get_session() as db:
            item = AgendaItem(
                meeting_id=meeting_id,
                title=data["title"],
                description=data.get("description"),
                order_index=data.get("order_index", 0),
                duration_minutes=data.get("duration_minutes"),
                owner_id=data.get("owner_id"),
            )
            db.add(item)
            db.flush()
            return {"id": str(item.id), "title": item.title, "order_index": item.order_index}

    def add_decision(self, meeting_id, data: dict) -> dict:
        with get_session() as db:
            decision = MeetingDecision(
                meeting_id=meeting_id,
                decision_text=data["decision_text"],
                decided_by=data.get("decided_by"),
                rationale=data.get("rationale"),
            )
            db.add(decision)
            db.flush()

            self.event_repository.save(
                aggregate_type="meeting",
                aggregate_id=str(meeting_id),
                event_type="MeetingDecisionMade",
                payload={"decision_id": str(decision.id), "decision_text": decision.decision_text},
            )

            return {"id": str(decision.id), "decision_text": decision.decision_text}

    def add_action_item(self, meeting_id, data: dict) -> dict:
        with get_session() as db:
            action = MeetingActionItem(
                meeting_id=meeting_id,
                task_id=data.get("task_id"),
                description=data["description"],
                assigned_to=data.get("assigned_to"),
                due_date=data.get("due_date"),
                status=data.get("status", "pending"),
            )
            db.add(action)
            db.flush()
            return {"id": str(action.id), "description": action.description, "status": action.status}

    def complete_meeting(self, meeting_id, summary: str = None):
        with get_session() as db:
            db.execute(
                text("""
                    UPDATE meetings
                    SET status = 'completed', summary = :summary, completed_at = NOW(), updated_at = NOW()
                    WHERE id = CAST(:mid AS UUID)
                """),
                {"mid": str(meeting_id), "summary": summary},
            )

        self.event_repository.save(
            aggregate_type="meeting",
            aggregate_id=str(meeting_id),
            event_type="MeetingCompleted",
            payload={"meeting_id": str(meeting_id)},
        )

        return {"id": str(meeting_id), "status": "completed"}

    def get_agenda(self, meeting_id):
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT id, title, description, order_index, duration_minutes, status
                    FROM agenda_items
                    WHERE meeting_id = CAST(:mid AS UUID)
                    ORDER BY order_index
                """),
                {"mid": str(meeting_id)},
            )
            return [dict(row) for row in result.mappings().all()]

    def get_decisions(self, meeting_id):
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT id, decision_text, decided_by, rationale
                    FROM meeting_decisions
                    WHERE meeting_id = CAST(:mid AS UUID)
                    ORDER BY created_at
                """),
                {"mid": str(meeting_id)},
            )
            return [dict(row) for row in result.mappings().all()]

    def get_action_items(self, meeting_id):
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT id, description, assigned_to, due_date, status
                    FROM meeting_action_items
                    WHERE meeting_id = CAST(:mid AS UUID)
                    ORDER BY created_at
                """),
                {"mid": str(meeting_id)},
            )
            return [dict(row) for row in result.mappings().all()]
