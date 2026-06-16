# Havilah OS — Frontend Dashboard (Vercel) Deployment Guide

This guide deploys the **Next.js frontend dashboard** to Vercel. The frontend talks to the Havilah backend deployed on Railway (see `havilah-workspace/docs/RAILWAY_DEPLOY.md`).

## Architecture

```
┌─────────────────────────┐         HTTPS         ┌─────────────────────────┐
│  Vercel (Next.js)       │  ───────────────────>  │  Railway (FastAPI)      │
│  havilah-dashboard      │   /api/hermes/*        │  havilah-backend        │
│  • Dashboard UI         │   /api/approvals/*     │  • Hermes Engine        │
│  • React Query          │   /api/memory/*        │  • PostgreSQL           │
│  • Mock data fallback   │                        │  • 10 AI Agents         │
└─────────────────────────┘                        └─────────────────────────┘
```

## Prerequisites

1. Backend deployed on Railway — get its URL (e.g. `https://havilah-backend.up.railway.app`)
2. A GitHub account with push access to `Ogienomo/havilah`
3. A Vercel account (free at [vercel.com](https://vercel.com))

## Step 1 — Push the Frontend to GitHub

The frontend lives in the **root of the `havilah` repo**, sibling to the `havilah-workspace/` backend folder. It's already pushed if you've been committing — verify:

```bash
git clone https://github.com/Ogienomo/havilah
cd havilah
ls src/app/page.tsx   # should exist
```

If not, commit and push the new `vercel.json`, `src/lib/havilah-api.ts`, and `src/lib/havilah-hooks.ts` files.

## Step 2 — Import to Vercel

1. Go to [vercel.com/new](https://vercel.com/new)
2. **Import Git Repository** → select `Ogienomo/havilah`
3. **Root Directory**: leave as `/` (the repo root contains the Next.js app)
4. **Framework Preset**: Vercel auto-detects **Next.js**
5. **Build Command**: `next build` (auto-filled)
6. **Install Command**: `bun install` (auto-filled from `vercel.json`)
7. Click **Deploy**

First deploy takes ~2 minutes. Vercel will give you a URL like:
`https://havilah.vercel.app`

## Step 3 — Configure Environment Variables

In Vercel → Project → **Settings** → **Environment Variables**, add:

| Name | Value | Environments |
|------|-------|--------------|
| `NEXT_PUBLIC_HAVILAH_API_URL` | `https://havilah-backend.up.railway.app` | Production, Preview, Development |
| `NEXT_PUBLIC_HAVILAH_API_TOKEN` | (leave empty for now) | Production |

**Redeploy** after adding env vars (Vercel → Deployments → ⋮ → Redeploy).

## Step 4 — Enable CORS on the Backend

The backend's `/api/hermes/*` endpoints need to accept requests from the Vercel domain. On Railway, set:

```
HAVILAH_CORS_ORIGINS=https://havilah.vercel.app,https://havilah-*.vercel.app
```

If using a custom domain:
```
HAVILAH_CORS_ORIGINS=https://dashboard.havilah.os
```

## Step 5 — Verify

1. Visit your Vercel URL
2. Open browser DevTools → Network tab
3. The dashboard should show **real backend data** (10 agents, pending approvals, recent memory)
4. Try the **Hermes Command Center**: type an instruction like `"Draft a welcome email for new client Acme Corp"`
5. Watch the orchestration pipeline animate as Hermes plans → dispatches → requests approval
6. The **Approval Queue** should show the new pending step

If the API isn't configured, the dashboard falls back to mock data automatically — so the UI always renders, even before the backend is up.

## Local Development

```bash
cd /home/z/my-project
cp .env.example .env.local
# Edit .env.local: set NEXT_PUBLIC_HAVILAH_API_URL=http://localhost:8000
bun install
bun dev
```

The dashboard runs on `http://localhost:3000` and proxies API calls to the local backend on `:8000`.

## Preview Deploys

Every PR automatically gets a preview URL like:
`https://havilah-git-feature-branch.vercel.app`

These are great for QA — share the preview URL with stakeholders before merging.

## Custom Domain (Optional)

In Vercel → Project → **Settings** → **Domains**:
1. Add `dashboard.havilah.os` (or your domain)
2. Add the DNS records Vercel shows you
3. Update `HAVILAH_CORS_ORIGINS` on Railway to include the new domain

## Cost

- **Hobby plan**: Free for personal projects
- **Pro plan**: $20/month/team (for commercial use, team collaboration)
- Most small deployments stay on the free tier indefinitely

## Troubleshooting

**Dashboard shows mock data instead of real data:**
- Check `NEXT_PUBLIC_HAVILAH_API_URL` is set in Vercel env vars
- Make sure you redeployed after adding the env var
- Open DevTools → Console for the error message

**API calls fail with CORS error:**
- Update `HAVILAH_CORS_ORIGINS` on Railway to include your Vercel URL
- Redeploy the backend (Railway auto-deploys on push, but env var changes need a manual redeploy)

**Build fails on Vercel:**
- Check the build log — most common cause is a TypeScript error
- Run `bun run lint` locally to catch issues before pushing

**`fetch failed` errors:**
- Backend may be sleeping on Railway's free tier — first request takes ~5s to wake
- Set `HAVILAH_RAILWAY_DONT_SLEEP=true` or upgrade to Hobby plan
