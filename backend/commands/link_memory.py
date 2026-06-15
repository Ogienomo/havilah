from backend.services.memory_service import MemoryService

service = MemoryService()

memory_id = "0f0d8af9-5004-4c38-afaf-e1af349e2068"

contact_id = "31a93590-cdf4-40a6-9aef-ce979e137f02"

result = service.link_memory(
    memory_id,
    "contact",
    contact_id,
    "communication_preference"
)

print(result)
