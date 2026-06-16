"""
Havilah OS — Agent Registry

Registry of the 10 specialized agents in Havilah OS.
Each agent has a type, capabilities, tool access, and an approval scope.

Agent types: planner, executive, research, writing, meeting, reviewer,
             critic, memory, learning, approval

No agent can approve external execution — ever.
"""

import logging
from typing import Optional
from dataclasses import dataclass, field

logger = logging.getLogger("havilah.agents")


@dataclass
class AgentDefinition:
    """Static definition of a specialized agent."""
    name: str
    display_name: str
    agent_type: str
    description: str
    capabilities: list[str] = field(default_factory=list)
    tool_access: list[str] = field(default_factory=list)
    approval_scope: str = "none"  # none, low_risk_only, read_only
    model_overrides: dict = field(default_factory=dict)  # temperature, max_tokens, model


# ── The 10 Specialized Agents ───────────────────────────────────

AGENT_DEFINITIONS: dict[str, AgentDefinition] = {
    "planner": AgentDefinition(
        name="planner",
        display_name="Planner Agent",
        agent_type="planner",
        description="Decomposes high-level instructions into structured execution plans with approval checkpoints.",
        capabilities=["decompose_tasks", "sequence_steps", "identify_dependencies", "assess_approval_needs"],
        tool_access=["memory_read", "project_read", "task_read", "approval_read"],
        approval_scope="none",
        model_overrides={"temperature": 0.3},
    ),
    "executive": AgentDefinition(
        name="executive",
        display_name="Executive Agent",
        agent_type="executive",
        description="Provides strategic recommendations, executive briefings, and priority assessments.",
        capabilities=["strategic_analysis", "briefing_generation", "priority_assessment", "risk_flagging"],
        tool_access=["memory_read", "project_read", "task_read", "approval_read", "analytics_read", "contact_read"],
        approval_scope="none",
        model_overrides={"temperature": 0.5},
    ),
    "research": AgentDefinition(
        name="research",
        display_name="Research Agent",
        agent_type="research",
        description="Conducts research, synthesizes findings, and produces structured reports.",
        capabilities=["research", "summarize", "source_analysis", "trend_identification"],
        tool_access=["memory_read", "knowledge_read", "research_read", "web_search"],
        approval_scope="none",
        model_overrides={"temperature": 0.4},
    ),
    "writing": AgentDefinition(
        name="writing",
        display_name="Writing Agent",
        agent_type="writing",
        description="Drafts communications, documents, and content. Never sends externally without approval.",
        capabilities=["draft_emails", "draft_messages", "content_writing", "style_adaptation"],
        tool_access=["memory_read", "contact_read", "project_read", "content_read", "knowledge_read"],
        approval_scope="none",
        model_overrides={"temperature": 0.7},
    ),
    "meeting": AgentDefinition(
        name="meeting",
        display_name="Meeting Agent",
        agent_type="meeting",
        description="Prepares agendas, documents decisions, tracks action items, generates summaries.",
        capabilities=["agenda_preparation", "decision_documentation", "action_tracking", "summary_generation"],
        tool_access=["memory_read", "meeting_read", "project_read", "task_read", "contact_read"],
        approval_scope="none",
        model_overrides={"temperature": 0.4},
    ),
    "reviewer": AgentDefinition(
        name="reviewer",
        display_name="Reviewer Agent",
        agent_type="reviewer",
        description="Critically evaluates outputs from other agents. Quality gate before external delivery.",
        capabilities=["quality_review", "accuracy_check", "policy_compliance", "improvement_suggestions"],
        tool_access=["memory_read", "content_read", "approval_read", "project_read"],
        approval_scope="none",
        model_overrides={"temperature": 0.3},
    ),
    "critic": AgentDefinition(
        name="critic",
        display_name="Critic Agent",
        agent_type="critic",
        description="Plays devil's advocate on strategic decisions. Identifies failure modes and blind spots.",
        capabilities=["risk_identification", "assumption_challenging", "failure_mode_analysis", "stress_testing"],
        tool_access=["memory_read", "project_read", "approval_read", "risk_read", "analytics_read"],
        approval_scope="none",
        model_overrides={"temperature": 0.8},
    ),
    "memory": AgentDefinition(
        name="memory",
        display_name="Memory Agent",
        agent_type="memory",
        description="Determines what to capture as institutional memory. Classifies and links knowledge.",
        capabilities=["memory_capture", "memory_classification", "importance_assessment", "link_identification"],
        tool_access=["memory_read", "memory_write", "contact_read", "project_read", "approval_read"],
        approval_scope="low_risk_only",
        model_overrides={"temperature": 0.3},
    ),
    "learning": AgentDefinition(
        name="learning",
        display_name="Learning Agent",
        agent_type="learning",
        description="Analyzes patterns in decisions and outcomes to extract operational insights.",
        capabilities=["pattern_recognition", "workflow_analysis", "policy_improvement", "trend_analysis"],
        tool_access=["memory_read", "analytics_read", "approval_read", "event_read"],
        approval_scope="none",
        model_overrides={"temperature": 0.5},
    ),
    "approval": AgentDefinition(
        name="approval",
        display_name="Approval Agent",
        agent_type="approval",
        description="Prepares approval briefings and risk assessments. NEVER approves or rejects — only humans can.",
        capabilities=["briefing_preparation", "risk_assessment", "context_compilation", "escalation_recommendation"],
        tool_access=["memory_read", "approval_read", "risk_read", "project_read", "contact_read"],
        approval_scope="none",
        model_overrides={"temperature": 0.3},
    ),
}


class AgentRegistry:
    """
    Registry for Hermes agents.

    Provides lookup, listing, and auto-registration of agents
    into the database on first startup.
    """

    def __init__(self):
        self._agents = dict(AGENT_DEFINITIONS)

    def get(self, name: str) -> Optional[AgentDefinition]:
        """Get an agent definition by name."""
        return self._agents.get(name)

    def get_by_type(self, agent_type: str) -> list[AgentDefinition]:
        """Get all agents of a given type."""
        return [a for a in self._agents.values() if a.agent_type == agent_type]

    def list_all(self) -> list[AgentDefinition]:
        """List all registered agent definitions."""
        return list(self._agents.values())

    def list_names(self) -> list[str]:
        """List all agent names."""
        return list(self._agents.keys())

    def seed_database(self):
        """
        Ensure all 10 agents exist in the database.
        Called during application startup.

        This registers agents into the 'agents' table if they don't already exist.
        Agents are system-level and cannot be disabled.
        """
        from backend.services.agent_service import AgentService

        agent_service = AgentService()

        for name, definition in self._agents.items():
            try:
                existing = agent_service.get_agent_by_name(name)
                if existing:
                    logger.debug(f"Agent '{name}' already registered")
                    continue

                agent_data = {
                    "name": definition.name,
                    "display_name": definition.display_name,
                    "agent_type": definition.agent_type,
                    "description": definition.description,
                    "capabilities": definition.capabilities,
                    "tool_access": definition.tool_access,
                    "approval_scope": definition.approval_scope,
                    "model_config": definition.model_overrides,
                    "max_concurrent_runs": 1,
                    "is_system": True,
                    "status": "active",
                }

                agent_service.register_agent(agent_data)
                logger.info(f"Registered agent: {name}")

            except Exception as e:
                logger.warning(f"Could not register agent '{name}': {e}")

        logger.info(f"Agent registry seeded: {len(self._agents)} agents")

    def get_tools_for_agent(self, name: str) -> list[dict]:
        """
        Get the tool definitions (OpenAI function calling format) for an agent.
        These tools define what actions the agent can request.
        """
        definition = self.get(name)
        if not definition:
            return []

        tools = []
        tool_access = definition.tool_access

        # Map tool access to OpenAI function definitions
        tool_map = {
            "memory_read": {
                "type": "function",
                "function": {
                    "name": "memory_recall",
                    "description": "Search institutional memory for relevant information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query for memory recall"},
                            "memory_type": {"type": "string", "description": "Optional filter: profile, client, project, communication, operational, research, approval, meeting"},
                            "importance": {"type": "string", "description": "Optional filter: low, medium, high, critical"},
                        },
                        "required": ["query"],
                    },
                },
            },
            "memory_write": {
                "type": "function",
                "function": {
                    "name": "memory_capture",
                    "description": "Capture new institutional memory",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Short title for the memory"},
                            "content": {"type": "string", "description": "The memory content"},
                            "memory_type": {"type": "string", "description": "Category: profile, client, project, communication, operational, research, approval, meeting"},
                            "importance": {"type": "string", "description": "Importance level: low, medium, high, critical"},
                            "source": {"type": "string", "description": "Where this memory came from"},
                        },
                        "required": ["title", "content", "memory_type", "importance"],
                    },
                },
            },
            "project_read": {
                "type": "function",
                "function": {
                    "name": "project_list",
                    "description": "List projects or get project details",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "project_id": {"type": "string", "description": "Optional: get specific project by ID"},
                            "status": {"type": "string", "description": "Optional: filter by status"},
                        },
                    },
                },
            },
            "task_read": {
                "type": "function",
                "function": {
                    "name": "task_list",
                    "description": "List tasks or get task details",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_id": {"type": "string", "description": "Optional: get specific task by ID"},
                            "project_id": {"type": "string", "description": "Optional: filter by project"},
                            "status": {"type": "string", "description": "Optional: filter by status"},
                        },
                    },
                },
            },
            "approval_read": {
                "type": "function",
                "function": {
                    "name": "approval_list",
                    "description": "List approval requests or get approval details",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "approval_id": {"type": "string", "description": "Optional: get specific approval by ID"},
                            "status": {"type": "string", "description": "Optional: filter by status"},
                        },
                    },
                },
            },
            "contact_read": {
                "type": "function",
                "function": {
                    "name": "contact_list",
                    "description": "List contacts or get contact details",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "contact_id": {"type": "string", "description": "Optional: get specific contact by ID"},
                            "search": {"type": "string", "description": "Optional: search contacts by name"},
                        },
                    },
                },
            },
            "analytics_read": {
                "type": "function",
                "function": {
                    "name": "analytics_dashboard",
                    "description": "Get analytics dashboard data",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "metric": {"type": "string", "description": "Optional: specific metric to retrieve"},
                        },
                    },
                },
            },
            "risk_read": {
                "type": "function",
                "function": {
                    "name": "risk_assessment",
                    "description": "Get risk assessment data",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "approval_id": {"type": "string", "description": "Approval ID to assess risk for"},
                        },
                    },
                },
            },
            "knowledge_read": {
                "type": "function",
                "function": {
                    "name": "knowledge_search",
                    "description": "Search knowledge base",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                        },
                        "required": ["query"],
                    },
                },
            },
            "research_read": {
                "type": "function",
                "function": {
                    "name": "research_jobs",
                    "description": "List research jobs or get research results",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "job_id": {"type": "string", "description": "Optional: get specific research job"},
                        },
                    },
                },
            },
            "meeting_read": {
                "type": "function",
                "function": {
                    "name": "meeting_list",
                    "description": "List meetings or get meeting details",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "meeting_id": {"type": "string", "description": "Optional: get specific meeting by ID"},
                        },
                    },
                },
            },
            "content_read": {
                "type": "function",
                "function": {
                    "name": "content_list",
                    "description": "List content drafts or get content details",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "content_id": {"type": "string", "description": "Optional: get specific content by ID"},
                        },
                    },
                },
            },
            "event_read": {
                "type": "function",
                "function": {
                    "name": "event_timeline",
                    "description": "Get domain event timeline",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "aggregate_type": {"type": "string", "description": "Optional: filter by aggregate type"},
                            "limit": {"type": "integer", "description": "Max events to return (default 20)"},
                        },
                    },
                },
            },
            "web_search": {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Search the web for information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                        },
                        "required": ["query"],
                    },
                },
            },
        }

        for access in tool_access:
            if access in tool_map:
                tools.append(tool_map[access])

        return tools
