# Havilah OS — Frontend Dashboard (Vercel) Deployment Guide

This guide deploys the **Next.js frontend dashboard** to Vercel. The frontend talks to the Havilah backend deployed on Railway (see `havilah-workspace/docs/RAILWAY_DEPLOY.md`).

## Architecture

```
┌─────────────────────────┐         HTTPS         ┌─────────────────────────┐
│  Vercel (Next.js)       │  ───────────────────>  │  Railway (FastAPI)      │
│  havilah-dashboard      │   /api/hermes/*        │  havilah-backend        │
│  • Dashboard UI         │   /api/approvals/*     │  • Hermes Engine        │
│  • React Query          │   /api/memory/*        │  • PostgreSQL           │
│  • Mock data fallback   │   /api/whatsapp/*      │  • 10 AI Agents         │
└─────────────────────────┘                        └─────────────────────────┘
```

## Prerequisites

1. Backend deployed on Railway — `https://havilah-production.up.railway.app`
2. A GitHub account with push access to `Ogienomo/havilah`
3. A Vercel account (free at [vercel.com](https://vercel.com))
4. The `RAILWAY_TOKEN` env var (so the helper script can update CORS for you)

## One-Command Deploy (Recommended)

The helper script verifies the backend, prints step-by-step Vercel UI instructions, and after you paste your new Vercel URL it automatically sets `HAVILAH_CORS_ORIGINS` on the Railway backend and triggers a redeploy so the two can talk.

```bash
RAILWAY_TOKEN=976a6c97-33cb-418c-9f76-ac124b33f6b4 \
  python3 scripts/vercel_deploy.py
```

If you just want the printed instructions (no automation):

```bash
RAILWAY_TOKEN=... python3 scripts/vercel_deploy.py --instructions-only
```

---

## Manual Step-by-Step

### Step 1 — Verify the Frontend is in the Repo

The frontend lives in `frontend/` at the root of the `havilah` repo (sibling to `backend/`, `alembic/`, etc.):

```bash
git clone https://github.com/Ogienomo/havilah
cd havilah
ls frontend/src/app/page.tsx   # should exist
ls frontend/vercel.json         # should exist
```

### Step 2 — Import to Vercel

1. Go to [vercel.com/new](https://vercel.com/new)
2. Sign in with GitHub (the account that has access to `Ogienomo/havilah`)
3. Click **Import Git Repository** → select `Ogienomo/havilah`
4. **IMPORTANT — Root Directory**: expand "Root Directory" settings and set it to `frontend/`
   (If you leave it as `/`, Vercel will try to build the backend folder and fail)
5. Configure the project:
   - **Framework Preset**: Next.js (auto-detected)
   - **Build Command**: `next build` (auto-filled)
   - **Install Command**: `bun install` (auto-filled from `vercel.json`)
   - **Node.js Version**: 20.x (Vercel default)
6. Expand **Environment Variables** and add:

   | Name | Value | Environments |
   |------|-------|--------------|
   | `NEXT_PUBLIC_HAVILAH_API_URL` | `https://havilah-production.up.railway.app` | Production, Preview, Development |
   | `NEXT_PUBLIC_HAVILAH_API_TOKEN` | (leave empty) | Production |

7. Click **Deploy**

First deploy takes ~2-3 minutes. Vercel will give you a URL like:
- `https://havilah.vercel.app` (production), or
- `https://havilah-<hash>-Ogienomo.vercel.app` (auto-assigned)

### Step 3 — Add Your Vercel URL to Backend CORS

The backend rejects cross-origin requests unless the origin is in `HAVILAH_CORS_ORIGINS`. The helper script does this for you:

```bash
# After pasting your Vercel URL when prompted:
RAILWAY_TOKEN=... python3 scripts/vercel_deploy.py
# → Sets HAVILAH_CORS_ORIGINS=https://your-vercel-url.vercel.app,https://*.vercel.app,...
# → Triggers Railway redeploy so CORS takes effect
# → Verifies OPTIONS preflight succeeds
```

Or manually via Railway UI → Backend Service → Variables:

```
HAVILAH_CORS_ORIGINS=https://havilah.vercel.app,https://havilah-*.vercel.app,https://*.vercel.app,https://localhost:3000
```

After setting this, **manually redeploy** the backend (Railway → Deployments → ⋮ → Redeploy) for the change to take effect.

### Step 4 — Verify

1. Visit your Vercel URL
2. Open browser DevTools → Network tab
3. The dashboard should show **real backend data**:
   - Hero Stats shows 10 agents registered
   - Agent Grid shows all 10 agents as "Active"
   - Approval Queue shows pending approvals
   - Activity Timeline shows recent Hermes runs
   - Memory Explorer shows recent memory entries
4. Try the **Hermes Command Center**:
   - Type: `Draft a welcome email for new client Acme Corp`
   - Click **Execute**
   - Watch the pipeline animate: Plan → Dispatch → Approval gate
   - The **Approval Queue** should populate with a new pending step

If `NEXT_PUBLIC_HAVILAH_API_URL` is not set, the dashboard automatically falls back to mock data — so the UI always renders, even before the backend is up.

---

## Local Development

```bash
cd frontend
cp .env.example .env.local
# Edit .env.local: set NEXT_PUBLIC_HAVILAH_API_URL=http://localhost:8000
bun install
bun dev
```

The dashboard runs on `http://localhost:3000` and proxies API calls to the local backend on `:8000`.

---

## Preview Deploys

Every PR automatically gets a preview URL like:
`https://havilah-git-feature-branch.vercel.app`

These are great for QA — share the preview URL with stakeholders before merging. The wildcard `https://*.vercel.app` in `HAVILAH_CORS_ORIGINS` means preview deploys work without any extra config.

---

## Custom Domain (Optional)

In Vercel → Project → **Settings** → **Domains**:
1. Add `dashboard.havilah.os` (or your domain)
2. Add the DNS records Vercel shows you
3. Update `HAVILAH_CORS_ORIGINS` on Railway to include the new domain
4. Redeploy the backend

---

## Cost

- **Hobby plan**: Free for personal projects
- **Pro plan**: $20/month/team (for commercial use, team collaboration)
- Most small deployments stay on the free tier indefinitely

---

## Troubleshooting

**Dashboard shows mock data instead of real data:**
- Check `NEXT_PUBLIC_HAVILAH_API_URL` is set in Vercel env vars (with no trailing slash)
- Make sure you redeployed after adding the env var (Vercel → Deployments → ⋮ → Redeploy)
- Open DevTools → Console for the error message

**API calls fail with CORS error (browser console shows "blocked by CORS policy"):**
- Update `HAVILAH_CORS_ORIGINS` on Railway to include your Vercel URL
- Use the helper script: `RAILWAY_TOKEN=... python3 scripts/vercel_deploy.py`
- Or set it manually and redeploy the backend

**Build fails on Vercel ("Root Directory" error or "Cannot find module next"):**
- Make sure Root Directory is set to `frontend/`, not `/`
- The Next.js app lives in `frontend/`, the backend lives at the repo root

**`fetch failed` errors:**
- Backend may be sleeping on Railway's free tier — first request takes ~5s to wake
- Send a warmup request: `curl https://havilah-production.up.railway.app/health`

**401 Unauthorized on /api/hermes/runs:**
- That endpoint requires JWT auth (the dashboard's hooks use public endpoints by default)
- For now, dashboard reads work without auth; mutations (instruct, approve) may require login
- Coming soon: Vercel-side auth via NextAuth + Havilah JWT
