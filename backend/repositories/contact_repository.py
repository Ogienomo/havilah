from backend.database import SessionLocal

from backend.models.contact import Contact


class ContactRepository:

    def save(self, contact_data):

        db = SessionLocal()

        try:

            contact = Contact(**contact_data)

            db.add(contact)

            db.commit()

            db.refresh(contact)

            return contact

        finally:
            db.close()
