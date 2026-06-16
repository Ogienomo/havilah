"""
Havilah OS — Hermes API

REST API endpoints for the Hermes orchestration engine.
These are the primary interface for interacting with Hermes.

Endpoints:
- POST /api/hermes/instruct — Give Hermes a natural language instruction
- POST /api/hermes/approve — Approve a pending step
- POST /api/hermes/reject — Reject a pending step
- GET  /api/hermes/runs — List active runs
- GET  /api/hermes/runs/{run_id} — Get run status
- GET  /api/hermes/agents — List available agents
- GET  /api/hermes/agents/{name} — Get agent details
- POST /api/hermes/chat — Direct chat with Hermes (no planning, just conversation)
- GET  /api/hermes/health — Check Hermes health
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.api.auth import require_auth, require_admin
from backend.hermes.orchestrator import HermesOrchestrator
from backend.hermes.agent_registry import AgentRegistry
from backend.hermes.llm_provider import LLMProvider
from backend.hermes.whatsapp_bridge import WhatsAppBridge
from backend.config.settings import get_settings

logger = logging.getLogger("havilah.hermes_api")
settings = get_settings()

router = APIRouter(prefix="/api/hermes", tags=["Hermes Orchestration"])

# ── Singleton instances ─────────────────────────────────────────
_hermes: Optional[HermesOrchestrator] = None
_registry: Optional[AgentRegistry] = None
_llm: Optional[LLMProvider] = None
_whatsapp_bridge: Optional[WhatsAppBridge] = None


def get_hermes() -> HermesOrchestrator:
    global _hermes
    if _hermes is None:
        _hermes = HermesOrchestrator()
    return _hermes


def get_registry() -> AgentRegistry:
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry


def get_llm() -> LLMProvider:
    global _llm
    if _llm is None:
        _llm = LLMProvider()
    return _llm


def get_whatsapp_bridge() -> WhatsAppBridge:
    global _whatsapp_bridge
    if _whatsapp_bridge is None:
        _whatsapp_bridge = WhatsAppBridge()
    return _whatsapp_bridge


# ── Pydantic Schemas ────────────────────────────────────────────

class HermesInstruction(BaseModel):
    """Natural language instruction for Hermes."""
    instruction: str = Field(..., min_length=1, max_length=10000, description="What you want Hermes to do")
    source: str = Field(default="api", description="Where this instruction came from: api, whatsapp, scheduled")
    context: Optional[dict] = Field(default=None, description="Additional context (user info, project info, etc.)")


class HermesApproval(BaseModel):
    """Approval decision for a pending Hermes run."""
    run_id: str = Field(..., min_length=1, description="The run ID to approve")
    reason: Optional[str] = Field(default=None, max_length=1000, description="Reason for the decision")


class HermesChat(BaseModel):
    """Direct chat message to Hermes (no planning pipeline)."""
    message: str = Field(..., min_length=1, max_length=10000, description="Chat message")
    agent_type: Optional[str] = Field(default=None, description="Optional: route to a specific agent type")
    conversation_history: Optional[list[dict]] = Field(default=None, description="Previous messages for context")


class HermesWhatsAppMessage(BaseModel):
    """Incoming WhatsApp message to route through Hermes."""
    phone_number: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1, max_length=4096)
    message_id: Optional[str] = None


# ── Endpoints ───────────────────────────────────────────────────

@router.post("/instruct", summary="Give Hermes an instruction")
async def instruct_hermes(
    request: HermesInstruction,
    user=Depends(require_auth),
):
    """
    Submit a natural language instruction to Hermes.

    Hermes will:
    1. Recall relevant memory context
    2. Plan the execution (decompose into steps)
    3. Execute each step via specialized agents
    4. If any step requires approval, pause and return with approval_id
    5. Record outcomes to memory

    If the response has status='awaiting_approval', call /approve or /reject
    with the run_id and approval_id.
    """
    if not settings.HERMES_ENABLED:
        raise HTTPException(status_code=503, detail="Hermes orchestration is disabled")

    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="OpenAI API key not configured")

    hermes = get_hermes()

    result = hermes.process_instruction(
        instruction=request.instruction,
        source=request.source,
        context=request.context,
    )

    return result


@router.post("/approve", summary="Approve a pending Hermes step")
async def approve_hermes_run(
    request: HermesApproval,
    user=Depends(require_auth),
):
    """
    Approve a pending step in a Hermes run.

    Only humans can approve — AI agents NEVER have approval authority.
    After approval, Hermes will continue executing remaining steps.
    """
    hermes = get_hermes()
    result = hermes.continue_run(
        run_id=request.run_id,
        approved=True,
        reason=request.reason,
    )
    return result


@router.post("/reject", summary="Reject a pending Hermes step")
async def reject_hermes_run(
    request: HermesApproval,
    user=Depends(require_auth),
):
    """
    Reject a pending step in a Hermes run.

    This cancels the run. No further steps will execute.
    """
    hermes = get_hermes()
    result = hermes.continue_run(
        run_id=request.run_id,
        approved=False,
        reason=request.reason,
    )
    return result


@router.get("/runs", summary="List active Hermes runs")
async def list_hermes_runs(
    user=Depends(require_auth),
):
    """List all currently active (non-completed) Hermes orchestration runs."""
    hermes = get_hermes()
    return {"active_runs": hermes.list_active_runs()}


@router.get("/runs/{run_id}", summary="Get Hermes run status")
async def get_hermes_run(
    run_id: str,
    user=Depends(require_auth),
):
    """Get the status and results of a specific Hermes run."""
    hermes = get_hermes()
    run = hermes.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return run


@router.get("/agents", summary="List available Hermes agents")
async def list_agents(
    user=Depends(require_auth),
):
    """List all 10 specialized agents in the Hermes system."""
    registry = get_registry()
    agents = []
    for agent in registry.list_all():
        agents.append({
            "name": agent.name,
            "display_name": agent.display_name,
            "agent_type": agent.agent_type,
            "description": agent.description,
            "capabilities": agent.capabilities,
            "approval_scope": agent.approval_scope,
        })
    return {"agents": agents, "total": len(agents)}


@router.get("/agents/{name}", summary="Get agent details")
async def get_agent(
    name: str,
    user=Depends(require_auth),
):
    """Get detailed information about a specific agent."""
    registry = get_registry()
    agent = registry.get(name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found")

    tools = registry.get_tools_for_agent(name)

    return {
        "name": agent.name,
        "display_name": agent.display_name,
        "agent_type": agent.agent_type,
        "description": agent.description,
        "capabilities": agent.capabilities,
        "tool_access": agent.tool_access,
        "approval_scope": agent.approval_scope,
        "model_overrides": agent.model_overrides,
        "tools": tools,
    }


@router.post("/chat", summary="Direct chat with Hermes")
async def chat_with_hermes(
    request: HermesChat,
    user=Depends(require_auth),
):
    """
    Have a direct conversation with Hermes.

    This bypasses the planning pipeline and goes straight to the LLM.
    Useful for quick questions, brainstorming, or exploration.

    For structured task execution, use /instruct instead.
    """
    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="OpenAI API key not configured")

    llm = get_llm()

    messages = request.conversation_history or []
    messages.append({"role": "user", "content": request.message})

    result = llm.chat(
        messages=messages,
        agent_type=request.agent_type,
    )

    return {
        "response": result["content"],
        "tokens": result["tokens"],
        "agent_type": request.agent_type or "general",
    }


@router.post("/whatsapp", summary="Process WhatsApp message through Hermes")
async def process_whatsapp_message(
    request: HermesWhatsAppMessage,
):
    """
    Process an incoming WhatsApp message through the Hermes bridge.

    This endpoint is called by the WhatsApp webhook when a message arrives.
    It detects intent (instruction, approval, rejection, status, help)
    and routes appropriately.

    No authentication required — the WhatsApp webhook verification handles security.
    """
    if not settings.HERMES_ENABLED:
        raise HTTPException(status_code=503, detail="Hermes is disabled")

    bridge = get_whatsapp_bridge()
    result = bridge.process_incoming_message(
        phone_number=request.phone_number,
        message_text=request.message,
        message_id=request.message_id,
    )
    return result


@router.get("/health", summary="Hermes health check")
async def hermes_health():
    """Check if Hermes is healthy and configured."""
    checks = {
        "hermes_enabled": settings.HERMES_ENABLED,
        "openai_configured": bool(settings.OPENAI_API_KEY),
        "model": settings.OPENAI_MODEL,
    }

    # Test LLM connection if configured
    if settings.OPENAI_API_KEY:
        try:
            llm = get_llm()
            result = llm.chat(
                messages=[{"role": "user", "content": "Say 'OK' and nothing else."}],
                max_tokens=10,
            )
            checks["llm_connected"] = True
            checks["llm_test_tokens"] = result["tokens"]["total"]
        except Exception as e:
            checks["llm_connected"] = False
            checks["llm_error"] = str(e)[:100]
    else:
        checks["llm_connected"] = False

    # Agent registry
    try:
        registry = get_registry()
        checks["agents_registered"] = len(registry.list_all())
    except Exception:
        checks["agents_registered"] = 0

    overall = "healthy" if checks.get("llm_connected") and checks.get("hermes_enabled") else "degraded"

    return {
        "status": overall,
        "checks": checks,
    }
