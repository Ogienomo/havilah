"""
Havilah OS — Audit Engine v2 Service

Cross-domain audit: Who changed what? When? Why?
"""

from backend.repositories.audit_repository import AuditRepository


class AuditService:

    def __init__(self):
        self.repository = AuditRepository()

    def get_entity_audit_trail(self, entity_type: str, entity_id: str, limit=100):
        return self.repository.get_entity_audit_trail(entity_type, entity_id, limit)

    def get_actor_actions(self, actor_id: str, limit=100):
        return self.repository.get_actor_actions(actor_id, limit)

    def get_correlation_chain(self, correlation_id: str):
        return self.repository.get_correlation_chain(correlation_id)

    def get_approval_audit(self, approval_id: str):
        return self.repository.get_approval_audit(approval_id)

    def get_recent_changes(self, limit=50, aggregate_type=None):
        return self.repository.get_recent_changes(limit, aggregate_type)
