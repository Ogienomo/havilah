"""
Havilah OS — FastAPI Application

AI Executive Operating System for Havilah Learning Hub.

Principle: AI thinks, drafts, recommends, and prepares — but NEVER
executes externally without human approval.

Architecture:
  - 14 Bounded Contexts
  - 10 Specialized AI Agents
  - 7+2 Approval State Machine
  - Event Sourcing (Command → Event → State)
  - CQRS-lite (Commands, Events, Consumers)
  - RBAC (admin, operator, viewer, agent)
  - Human-only approval gates (agents NEVER approve/execute)
  - WhatsApp Business API integration
  - Rate limiting, security headers, structured logging
"""

import time
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config.settings import get_settings

settings = get_settings()

# ── Configure Structured Logging ────────────────────────────────
from backend.core.logging_config import configure_logging, get_logger
configure_logging(environment=settings.ENVIRONMENT, level="DEBUG" if settings.DEBUG else "INFO")
logger = get_logger("main")

# ── Application Lifespan ────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: seed RBAC, WhatsApp templates, configure logging. Shutdown: cleanup."""
    logger.info("Havilah OS starting up...")
    try:
        from backend.api.middleware import seed_roles_and_permissions
        seed_roles_and_permissions()
        logger.info("RBAC seeding complete")
    except Exception as e:
        logger.warning(f"RBAC seeding skipped (DB not available?): {e}")
    try:
        from backend.services.whatsapp_service import WhatsAppService
        WhatsAppService().seed_default_templates()
        logger.info("WhatsApp templates seeded")
    except Exception as e:
        logger.warning(f"WhatsApp template seeding skipped: {e}")
    yield
    logger.info("Havilah OS shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Havilah OS — AI Executive Operating System. "
        "AI thinks, drafts, recommends, and prepares — "
        "but NEVER executes externally without human approval."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Security Headers Middleware ──────────────────────────────────
from backend.core.security import SecurityHeadersMiddleware, RateLimitMiddleware, get_cors_origins
app.add_middleware(SecurityHeadersMiddleware)

# ── Rate Limiting Middleware ─────────────────────────────────────
app.add_middleware(RateLimitMiddleware)

# ── CORS ────────────────────────────────────────────────────────
cors_origins = get_cors_origins(settings.ENVIRONMENT) if not settings.DEBUG else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Audit Middleware ─────────────────────────────────────────────
from backend.api.middleware import AuditMiddleware
app.add_middleware(AuditMiddleware)


# ── Health Check ────────────────────────────────────────────────

@app.get("/", tags=["System"])
def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "environment": settings.ENVIRONMENT,
        "principle": "AI thinks, drafts, recommends, prepares — humans decide.",
        "auth": "JWT + RBAC enabled on all /api/* routes",
    }


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "healthy", "auth": "enabled"}


@app.get("/health/detailed", tags=["System"])
def detailed_health_check():
    """Detailed health check with system metrics and dependency status."""
    from backend.core.monitoring import HealthChecker
    checker = HealthChecker()
    return checker.full_health_check()


@app.get("/metrics", tags=["System"])
def get_metrics():
    """Application metrics for monitoring dashboards."""
    from backend.core.monitoring import get_metrics as get_metrics_collector
    return get_metrics_collector().get_metrics()


# ── Register API Routers ────────────────────────────────────────
from backend.api.projects import router as projects_router
from backend.api.tasks import router as tasks_router
from backend.api.approvals import router as approvals_router
from backend.api.contacts import router as contacts_router
from backend.api.memory import router as memory_router
from backend.api.workflows import router as workflows_router
from backend.api.agents import router as agents_router
from backend.api.meetings import router as meetings_router
from backend.api.knowledge import router as knowledge_router
from backend.api.research import router as research_router
from backend.api.content import router as content_router
from backend.api.notifications import router as notifications_router
from backend.api.analytics import router as analytics_router
from backend.api.organizations import router as organizations_router
from backend.api.events import router as events_router
from backend.api.risk import router as risk_router
from backend.api.briefings import router as briefings_router
from backend.api.search import router as search_router
from backend.api.auth_routes import router as auth_router
from backend.api.whatsapp import router as whatsapp_router

# Auth routes (no auth guard — these are the entry point)
app.include_router(auth_router)

# Business routes (all guarded by RequirePermission)
app.include_router(projects_router)
app.include_router(tasks_router)
app.include_router(approvals_router)
app.include_router(contacts_router)
app.include_router(memory_router)
app.include_router(workflows_router)
app.include_router(agents_router)
app.include_router(meetings_router)
app.include_router(knowledge_router)
app.include_router(research_router)
app.include_router(content_router)
app.include_router(notifications_router)
app.include_router(analytics_router)
app.include_router(organizations_router)
app.include_router(events_router)
app.include_router(risk_router)
app.include_router(briefings_router)
app.include_router(search_router)
app.include_router(whatsapp_router)
