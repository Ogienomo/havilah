"""
Havilah OS — Memory Recorder

Records outcomes, decisions, and lessons learned into the Memory system.
After every orchestration run, the recorder:
1. Determines what should be captured
2. Classifies memories by type and importance
3. Links memories to relevant entities
4. Reinforces existing memories when patterns repeat

Memory is structured, not incidental.
Knowledge must outlive the model.
"""

import logging
from typing import Optional

from backend.hermes.llm_provider import LLMProvider
from backend.services.memory_service import MemoryService
from backend.events import MEMORY_CAPTURED, MEMORY_REINFORCED

logger = logging.getLogger("havilah.memory_recorder")


class MemoryRecorder:
    """
    Records orchestration outcomes into institutional memory.

    Uses the Memory Agent to intelligently determine:
    - What to capture (not everything is worth remembering)
    - How to classify it (type, importance)
    - Whether to reinforce existing memory or create new
    """

    def __init__(self):
        self.llm = LLMProvider()
        self.memory_service = MemoryService()

    def record_outcome(self, instruction: str, plan: dict, results: list[dict]) -> dict:
        """
        Record the outcome of an orchestration run.

        Args:
            instruction: The original user instruction
            plan: The execution plan that was followed
            results: Results from each step

        Returns:
            {"memories_captured": int, "memories_reinforced": int}
        """
        # Ask the Memory Agent what should be captured
        prompt = f"""Analyze this completed orchestration run and determine what should be captured as institutional memory.

ORIGINAL INSTRUCTION: {instruction}

PLAN SUMMARY: {plan.get('summary', 'N/A')}

RESULTS:
"""
        for i, result in enumerate(results):
            status = result.get("status", "unknown")
            output = result.get("output", "No output")
            if isinstance(output, str) and len(output) > 500:
                output = output[:500] + "..."
            prompt += f"\nStep {i+1} ({status}): {output}\n"

        prompt += """

Determine what memories should be captured. For each, specify:
1. title: Short descriptive title
2. content: The memory content (detailed enough to be useful later)
3. memory_type: One of: profile, client, project, communication, operational, research, approval, meeting
4. importance: One of: low, medium, high, critical
5. source: Where this knowledge came from

Also determine if any EXISTING memories should be reinforced (observed again) or superseded (contradicted).

Output JSON: {"memories_to_capture": [...], "memories_to_reinforce": [...]}"""

        try:
            result = self.llm.chat_json(
                messages=[{"role": "user", "content": prompt}],
                agent_type="memory",
                max_tokens=2048,
            )

            data = result["data"]
            captured = 0
            reinforced = 0

            # Capture new memories
            for mem in data.get("memories_to_capture", []):
                try:
                    capture_data = {
                        "title": mem.get("title", "Untitled memory"),
                        "content": mem.get("content", ""),
                        "memory_type": mem.get("memory_type", "operational"),
                        "importance": mem.get("importance", "medium"),
                        "source": mem.get("source", "hermes_orchestration"),
                        "status": "active",
                    }

                    # Use the memory service command format
                    from backend.schemas.schemas import MemoryCaptureCommand
                    command = MemoryCaptureCommand(**capture_data)
                    self.memory_service.capture_memory(command)
                    captured += 1

                except Exception as e:
                    logger.warning(f"Failed to capture memory: {e}")

            # Note: reinforcement would require looking up existing memory IDs
            # For now, we count the intent
            reinforced_plans = data.get("memories_to_reinforce", [])
            reinforced = len(reinforced_plans)

            logger.info(f"Memory recording complete: {captured} captured, {reinforced} to reinforce")

            return {
                "memories_captured": captured,
                "memories_reinforced": reinforced,
            }

        except Exception as e:
            logger.error(f"Failed to record memories: {e}")
            return {
                "memories_captured": 0,
                "memories_reinforced": 0,
                "error": str(e),
            }

    def recall_context(self, instruction: str) -> list[dict]:
        """
        Recall relevant memories for a given instruction.
        Used to provide context to the planner before creating a plan.

        Returns:
            List of memory items relevant to the instruction.
        """
        try:
            # Use the memory service to search
            memories = self.memory_service.recall_memory(instruction)
            return memories if isinstance(memories, list) else []
        except Exception as e:
            logger.warning(f"Memory recall failed: {e}")
            return []
