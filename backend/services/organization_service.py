"""
Havilah OS — Organization Service

Manages organizations, departments, and stakeholders.
"""

from backend.repositories.organization_repository import OrganizationRepository
from backend.repositories.event_repository import EventRepository


class OrganizationService:

    def __init__(self):
        self.repository = OrganizationRepository()
        self.event_repository = EventRepository()

    def create_organization(self, data: dict):
        org = self.repository.create(data)

        self.event_repository.save(
            aggregate_type="organization",
            aggregate_id=org["id"],
            event_type="OrganizationCreated",
            payload={"name": org["name"]},
        )

        return org

    def get_organization(self, org_id):
        return self.repository.get_by_id(org_id)

    def add_department(self, organization_id, name, **kwargs):
        dept = self.repository.add_department(organization_id, name, **kwargs)

        self.event_repository.save(
            aggregate_type="organization",
            aggregate_id=str(organization_id),
            event_type="DepartmentAdded",
            payload={"department_id": dept["id"], "name": name},
        )

        return dept

    def add_stakeholder(self, organization_id, stakeholder_type, **kwargs):
        sh = self.repository.add_stakeholder(organization_id, stakeholder_type, **kwargs)

        self.event_repository.save(
            aggregate_type="organization",
            aggregate_id=str(organization_id),
            event_type="StakeholderAdded",
            payload={"stakeholder_id": sh["id"], "type": stakeholder_type},
        )

        return sh
