from pydantic import BaseModel


class CaptureMemoryCommand(BaseModel):
    memory_type: str
    title: str
    content: str
    importance: str = "medium"
    confidence: float = 1.0
    source_type: str | None = None
