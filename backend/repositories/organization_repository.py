"""
Havilah OS — Organization Repository
"""

from sqlalchemy import text
from backend.models.organization import Organization, Department, Stakeholder
from backend.repositories.base import get_session


class OrganizationRepository:

    def create(self, data: dict) -> dict:
        with get_session() as db:
            org = Organization(
                name=data["name"],
                organization_type=data.get("organization_type"),
                description=data.get("description"),
                industry=data.get("industry"),
                website=data.get("website"),
            )
            db.add(org)
            db.flush()
            return {"id": str(org.id), "name": org.name, "status": org.status}

    def get_by_id(self, org_id):
        with get_session() as db:
            org = db.query(Organization).filter(Organization.id == org_id).first()
            if not org:
                return None
            return {"id": str(org.id), "name": org.name, "status": org.status}

    def add_department(self, organization_id, name, **kwargs) -> dict:
        with get_session() as db:
            dept = Department(
                organization_id=organization_id,
                name=name,
                department_type=kwargs.get("department_type"),
                head_id=kwargs.get("head_id"),
            )
            db.add(dept)
            db.flush()
            return {"id": str(dept.id), "name": dept.name}

    def add_stakeholder(self, organization_id, stakeholder_type, **kwargs) -> dict:
        with get_session() as db:
            sh = Stakeholder(
                organization_id=organization_id,
                contact_id=kwargs.get("contact_id"),
                stakeholder_type=stakeholder_type,
                influence_level=kwargs.get("influence_level", "medium"),
                interest_level=kwargs.get("interest_level", "medium"),
            )
            db.add(sh)
            db.flush()
            return {"id": str(sh.id), "type": sh.stakeholder_type}
