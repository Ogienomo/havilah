from backend.services.memory_service import MemoryService


service = MemoryService()

results = service.recall_memory("Jeffery")

print("\nMEMORIES FOUND\n")

for memory in results:

    print(f"Title: {memory.title}")

    print(f"Content: {memory.content}")

    print(f"Importance: {memory.importance}")

    print("-" * 40)
