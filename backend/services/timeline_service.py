from backend.repositories.timeline_repository import (
    TimelineRepository
)

from backend.repositories.event_repository import (
    EventRepository
)

from backend.events.timeline_events import (
    TIMELINE_GENERATED,
    CONTACT_TIMELINE_GENERATED,
    APPROVAL_TIMELINE_GENERATED
)


class TimelineService:

    def __init__(self):

        self.repository = TimelineRepository()

        self.event_repository = EventRepository()

    # -----------------------------------------
    # APPROVAL TIMELINE
    # -----------------------------------------

    def generate_approval_timeline(
        self,
        approval_id
    ):

        events = (
            self.repository.get_business_events_for_aggregate(
                approval_id
            )
        )

        self.event_repository.save(
            aggregate_type="approval_request",
            aggregate_id=approval_id,
            event_type=APPROVAL_TIMELINE_GENERATED,
            payload={
                "approval_id":
                    approval_id
            }
        )

        print(
            f"EVENT -> "
            f"{APPROVAL_TIMELINE_GENERATED}"
        )

        return events

    # -----------------------------------------
    # CONTACT TIMELINE
    # -----------------------------------------

    def generate_contact_timeline(
        self,
        contact_id
    ):

        events = (
            self.repository
            .get_recent_events(
                100
            )
        )

        self.event_repository.save(
            aggregate_type="contact",
            aggregate_id=contact_id,
            event_type=CONTACT_TIMELINE_GENERATED,
            payload={
                "contact_id":
                    contact_id
            }
        )

        print(
            f"EVENT -> "
            f"{CONTACT_TIMELINE_GENERATED}"
        )

        return events

    # -----------------------------------------
    # SYSTEM TIMELINE
    # -----------------------------------------

    def generate_system_timeline(
        self,
        limit=50
    ):

        events = (
            self.repository
            .get_recent_events(
                limit
            )
        )

        self.event_repository.save(
            aggregate_type="system",
            aggregate_id=None,
            event_type=TIMELINE_GENERATED,
            payload={
                "limit":
                    limit
            }
        )

        print(
            f"EVENT -> "
            f"{TIMELINE_GENERATED}"
        )

        return events
