from sqlalchemy import text

from backend.database import SessionLocal
from backend.models.memory import MemoryItem


class MemoryRepository:

    def save(self, memory_data):

        db = SessionLocal()

        try:

            clean_data = {
                k: v
                for k, v in memory_data.items()
                if v is not None
            }

            memory = MemoryItem(**clean_data)

            db.add(memory)

            db.commit()

            db.refresh(memory)

            return memory

        finally:
            db.close()

    def reinforce_memory(self, memory_id):

        db = SessionLocal()

        try:

            db.execute(
                text("""
                    UPDATE memory_items
                    SET
                        reinforcement_count =
                            reinforcement_count + 1,
                        last_reinforced_at = NOW(),
                        confidence =
                            LEAST(confidence + 0.05, 1.0)
                    WHERE id = :memory_id
                """),
                {
                    "memory_id": str(memory_id)
                }
            )

            db.commit()

        finally:
            db.close()

    def find_by_text(self, search_text):

        db = SessionLocal()

        try:

            memories = (
                db.query(MemoryItem)
                .filter(
                    (MemoryItem.title.ilike(f"%{search_text}%")) |
                    (MemoryItem.content.ilike(f"%{search_text}%"))
                )
                .order_by(
                    MemoryItem.created_at.desc()
                )
                .all()
            )

            return memories

        finally:
            db.close()

    def link_memory(
        self,
        memory_id,
        entity_type,
        entity_id,
        relationship_type
    ):

        db = SessionLocal()

        try:

            db.execute(
                text("""
                    INSERT INTO memory_links (
                        memory_id,
                        linked_entity_type,
                        linked_entity_id,
                        relationship_type
                    )
                    VALUES (
                        :memory_id,
                        :entity_type,
                        :entity_id,
                        :relationship_type
                    )
                """),
                {
                    "memory_id": str(memory_id),
                    "entity_type": entity_type,
                    "entity_id": str(entity_id),
                    "relationship_type": relationship_type
                }
            )

            db.commit()

        finally:
            db.close()

