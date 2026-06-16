from backend.repositories.memory_repository import MemoryRepository
from backend.repositories.event_repository import EventRepository

from backend.events import (
    MEMORY_CAPTURED,
    MEMORY_LINKED,
    MEMORY_REINFORCED,
)


class MemoryService:

    def __init__(self):

        self.memory_repository = MemoryRepository()

        self.event_repository = EventRepository()

    def capture_memory(self, command):

        memory = self.memory_repository.save(
            command.model_dump()
        )

        self.event_repository.save(
            aggregate_type="memory_item",
            aggregate_id=str(memory.id),
            event_type=MEMORY_CAPTURED,
            payload={
                "memory_type": memory.memory_type,
                "title": memory.title
            }
        )

        print(f"EVENT -> {MEMORY_CAPTURED}")

        return memory

    def recall_memory(self, search_text):

        return self.memory_repository.find_by_text(
            search_text
        )

    def link_memory(
        self,
        memory_id,
        entity_type,
        entity_id,
        relationship_type
    ):

        self.memory_repository.link_memory(
            memory_id,
            entity_type,
            entity_id,
            relationship_type
        )

        self.event_repository.save(
            aggregate_type="memory_item",
            aggregate_id=str(memory_id),
            event_type=MEMORY_LINKED,
            payload={
                "entity_type": entity_type,
                "entity_id": str(entity_id),
                "relationship_type": relationship_type
            }
        )

        print(f"EVENT -> {MEMORY_LINKED}")

        return {
            "status": "linked"
        }

    def reinforce_memory(self, memory_id):

        self.memory_repository.reinforce_memory(
            memory_id
        )

        self.event_repository.save(
            aggregate_type="memory_item",
            aggregate_id=str(memory_id),
            event_type=MEMORY_REINFORCED,
            payload={
                "memory_id": str(memory_id)
            }
        )

        print(f"EVENT -> {MEMORY_REINFORCED}")

        return {
            "status": "reinforced",
            "memory_id": str(memory_id)
        }
