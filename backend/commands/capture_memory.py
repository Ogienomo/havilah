from backend.schemas.memory import CaptureMemoryCommand
from backend.services.memory_service import MemoryService


command = CaptureMemoryCommand(
    memory_type="client",
    title="Communication Preference",
    content="Jeffery prefers strategic discussions",
    importance="high",
    confidence=1.0,
    source_type="meeting"
)

service = MemoryService()

result = service.capture_memory(command)

print(result)
