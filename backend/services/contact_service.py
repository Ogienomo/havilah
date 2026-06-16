"""
Havilah OS — Contact Service
"""

from backend.repositories.contact_repository import ContactRepository
from backend.repositories.event_repository import EventRepository
from backend.events import MEMORY_CAPTURED


class ContactService:

    def __init__(self):
        self.repository = ContactRepository()
        self.event_repository = EventRepository()

    def create_contact(self, data: dict):
        result = self.repository.create(data)

        self.event_repository.save(
            aggregate_type="contact",
            aggregate_id=result["id"],
            event_type="ContactCreated",
            payload={"full_name": data.get("full_name", "")},
        )

        return result
