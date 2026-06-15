from backend.repositories.contact_repository import ContactRepository


class ContactService:

    def __init__(self):

        self.repository = ContactRepository()

    def create_contact(
        self,
        first_name,
        last_name,
        relationship_type,
        notes=None
    ):

        return self.repository.save(
            {
                "first_name": first_name,
                "last_name": last_name,
                "relationship_type": relationship_type,
                "notes": notes
            }
        )
