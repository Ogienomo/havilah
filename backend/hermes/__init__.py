"""
Havilah OS — Hermes Orchestration Engine

The AI brain of Havilah OS. Hermes receives instructions, plans work,
dispatches to specialized agents, routes through the Approval Ledger,
and records everything to Memory.

Core principle: AI thinks, drafts, recommends, and prepares — but NEVER
executes externally without human approval.

Architecture:
    HermesOrchestrator (central loop)
    ├── LLMProvider (OpenAI integration)
    ├── AgentRegistry (10 specialized agents)
    ├── TaskPlanner (decompose instructions into plans)
    ├── ApprovalGate (route through Approval Ledger)
    └── MemoryRecorder (capture outcomes to Memory)
"""

from backend.hermes.llm_provider import LLMProvider
from backend.hermes.agent_registry import AgentRegistry
from backend.hermes.task_planner import TaskPlanner
from backend.hermes.orchestrator import HermesOrchestrator
from backend.hermes.approval_gate import ApprovalGate
from backend.hermes.memory_recorder import MemoryRecorder

__all__ = [
    "LLMProvider",
    "AgentRegistry",
    "TaskPlanner",
    "HermesOrchestrator",
    "ApprovalGate",
    "MemoryRecorder",
]
