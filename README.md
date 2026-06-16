# Havilah OS

**AI Executive Operating System** — AI thinks, drafts, recommends, and prepares; humans decide and approve.

## Repository Layout

```
havilah/
├── backend/              # FastAPI + PostgreSQL + Hermes orchestration engine
│   ├── api/              # 155+ REST endpoints across 21 routers
│   ├── hermes/           # 10 specialized AI agents + central orchestrator
│   ├── models/           # 55 SQLAlchemy models (14 bounded contexts)
│   ├── services/         # 18 service-layer modules
│   └── core/             # Security, logging, monitoring
├── frontend/             # Next.js dashboard (Vercel-ready)
│   ├── src/app/          # App Router pages
│   ├── src/components/   # 8 Havilah dashboard sections + shadcn/ui
│   └── src/lib/          # API client + React Query hooks
├── alembic/              # Database migrations
├── docs/                 # Architecture + deployment guides
├── tests/                # Pytest suite
├── Dockerfile            # Backend container image
├── docker-compose.yml    # Local dev stack (FastAPI + PostgreSQL 16)
├── railway.json          # Railway deployment config (backend)
└── requirements.txt      # Python dependencies
```

## Deployment

| Layer      | Platform | Guide                          |
|------------|----------|--------------------------------|
| Backend    | Railway  | [docs/RAILWAY_DEPLOY.md](docs/RAILWAY_DEPLOY.md) |
| Frontend   | Vercel   | [docs/VERCEL_DEPLOY.md](docs/VERCEL_DEPLOY.md)   |
| WhatsApp   | Meta     | [docs/WHATSAPP_SETUP.md](docs/WHATSAPP_SETUP.md) |

The frontend talks to the backend over HTTPS via `/api/hermes/*` and related routes. CORS is configurable via the `HAVILAH_CORS_ORIGINS` env var.

## Core Principles

- **Human authority remains final** — every external action passes through the Approval Ledger
- **Memory is structured, not incidental** — knowledge outlives the model
- **Work is represented as explicit objects** — projects, tasks, contacts, memory items
- **Important changes are event-driven** — full audit trail via event sourcing
- **AI never approves** — agents can think, draft, recommend, prepare, but only humans execute externally

## Quick Start (Local Dev)

```bash
# 1. Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r ../requirements.txt
export HAVILAH_DB_HOST=localhost HAVILAH_OPENAI_API_KEY=sk-...
uvicorn backend.main:app --reload --port 8000

# 2. Frontend (in another terminal)
cd frontend
bun install
cp .env.example .env.local  # set NEXT_PUBLIC_HAVILAH_API_URL=http://localhost:8000
bun dev
```

Open `http://localhost:3000` for the dashboard, `http://localhost:8000/docs` for the API.

## What's Inside

- **10 Specialized AI Agents**: planner, executive, research, writing, meeting, reviewer, critic, memory, learning, approval
- **Hermes Orchestration Engine**: instruction → plan → dispatch → approve → execute → remember
- **7+2 Approval State Machine**: AI never approves; humans are the only gate
- **55 Database Tables** across 14 bounded contexts
- **155+ REST API Endpoints** with JWT auth + RBAC
- **WhatsApp Business API**: chat-based control of Hermes
- **Event Sourcing**: full audit trail of every state change
- **Institutional Memory**: structured knowledge graph that survives model changes
