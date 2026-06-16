"""
Havilah OS — Memory Repository (FIXED)

Fixes from original:
  1. Uses context manager instead of manual try/finally
  2. Model now has reinforcement_count and last_reinforced_at columns
  3. Proper session handling
"""

from sqlalchemy import text, or_
from backend.models.memory import MemoryItem, MemoryLink
from backend.repositories.base import get_session


class MemoryRepository:

    def save(self, memory_data: dict) -> MemoryItem:
        with get_session() as db:
            clean_data = {k: v for k, v in memory_data.items() if v is not None}
            memory = MemoryItem(**clean_data)
            db.add(memory)
            db.flush()
            return memory

    def get_by_id(self, memory_id):
        with get_session() as db:
            return db.query(MemoryItem).filter(MemoryItem.id == memory_id).first()

    def reinforce_memory(self, memory_id):
        with get_session() as db:
            db.execute(
                text("""
                    UPDATE memory_items
                    SET reinforcement_count = reinforcement_count + 1,
                        last_reinforced_at = NOW(),
                        confidence = LEAST(confidence + 0.05, 1.0),
                        updated_at = NOW()
                    WHERE id = CAST(:memory_id AS UUID)
                """),
                {"memory_id": str(memory_id)},
            )

    def find_by_text(self, search_text: str):
        with get_session() as db:
            memories = (
                db.query(MemoryItem)
                .filter(
                    or_(
                        MemoryItem.title.ilike(f"%{search_text}%"),
                        MemoryItem.content.ilike(f"%{search_text}%"),
                    )
                )
                .filter(MemoryItem.status == "active")
                .order_by(MemoryItem.importance.desc(), MemoryItem.created_at.desc())
                .limit(50)
                .all()
            )
            return memories

    def find_by_type(self, memory_type: str):
        with get_session() as db:
            return (
                db.query(MemoryItem)
                .filter(MemoryItem.memory_type == memory_type, MemoryItem.status == "active")
                .order_by(MemoryItem.importance.desc())
                .all()
            )

    def find_by_entity(self, entity_type: str, entity_id: str):
        with get_session() as db:
            result = db.execute(
                text("""
                    SELECT m.* FROM memory_items m
                    INNER JOIN memory_links ml ON ml.memory_id = m.id
                    WHERE ml.linked_entity_type = :entity_type
                      AND ml.linked_entity_id = CAST(:entity_id AS UUID)
                      AND m.status = 'active'
                    ORDER BY m.importance DESC, m.created_at DESC
                """),
                {"entity_type": entity_type, "entity_id": str(entity_id)},
            )
            return [dict(row._mapping) for row in result.fetchall()]

    def link_memory(self, memory_id, entity_type, entity_id, relationship_type="related"):
        with get_session() as db:
            db.execute(
                text("""
                    INSERT INTO memory_links (memory_id, linked_entity_type, linked_entity_id, relationship_type)
                    VALUES (CAST(:memory_id AS UUID), :entity_type, CAST(:entity_id AS UUID), :relationship_type)
                    ON CONFLICT DO NOTHING
                """),
                {
                    "memory_id": str(memory_id),
                    "entity_type": entity_type,
                    "entity_id": str(entity_id),
                    "relationship_type": relationship_type,
                },
            )

    def archive_memory(self, memory_id):
        with get_session() as db:
            db.execute(
                text("""
                    UPDATE memory_items SET status = 'archived', updated_at = NOW()
                    WHERE id = CAST(:memory_id AS UUID)
                """),
                {"memory_id": str(memory_id)},
            )

    def supersede_memory(self, old_id, new_id):
        with get_session() as db:
            db.execute(
                text("""
                    UPDATE memory_items SET status = 'superseded', superseded_by = CAST(:new_id AS UUID), updated_at = NOW()
                    WHERE id = CAST(:old_id AS UUID)
                """),
                {"old_id": str(old_id), "new_id": str(new_id)},
            )
