from backend.services.contact_service import ContactService


service = ContactService()

contact = service.create_contact(
    first_name="Jeffery",
    last_name="Agadumo",
    relationship_type="client",
    notes="LinkedIn branding client"
)

print(contact.id)

print(
    f"{contact.first_name} {contact.last_name}"
)
