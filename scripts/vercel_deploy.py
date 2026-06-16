#!/usr/bin/env python3
"""
Havilah OS — Vercel Frontend Deployment Helper
====================================================================

This script guides you through deploying the Havilah OS Next.js dashboard
to Vercel, and wires up the backend CORS so the two can talk to each other.

What it does:
  1. Verifies the backend on Railway is reachable (/health).
  2. Prints step-by-step Vercel UI instructions (import repo, set Root
     Directory, set env vars, click Deploy).
  3. After you paste your new Vercel URL, sets HAVILAH_CORS_ORIGINS on
     the Railway backend to allow your Vercel domain (plus Vercel preview
     URLs). Triggers a redeploy so CORS takes effect.
  4. Tests the deployed frontend can fetch /api/hermes/health from the
     backend (basic CORS preflight check).

Usage:
    RAILWAY_TOKEN=... python3 scripts/vercel_deploy.py

    # Skip the interactive CORS step if you only want the instructions:
    RAILWAY_TOKEN=... python3 scripts/vercel_deploy.py --instructions-only

Prerequisites:
    - Backend deployed on Railway (https://havilah-production.up.railway.app)
    - Repo pushed to github.com/Ogienomo/havilah (frontend/ folder present)
    - A Vercel account (free at https://vercel.com)
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Optional

# ─── Configuration ────────────────────────────────────────────────────────

RAILWAY_TOKEN = os.environ.get("RAILWAY_TOKEN") or ""
PROJECT_ID = "a8545ef4-4d74-483b-b069-7e34d96bb990"
ENVIRONMENT_ID = "f696a67c-db24-4086-b5ce-3484ce0a354d"
BACKEND_SERVICE_ID = "7db751d0-b3a4-47f9-99c1-7541cb857fa3"
BACKEND_URL = "https://havilah-production.up.railway.app"
REPO_URL = "https://github.com/Ogienomo/havilah"

RAILWAY_API = "https://backboard.railway.app/graphql/v2"

# Vercel URLs we always want to allow through CORS:
DEFAULT_VERCEL_ORIGINS = [
    "https://havilah.vercel.app",          # main production URL
    "https://havilah-*.vercel.app",        # branch previews
    "https://havilah-git-*.vercel.app",    # git push previews
    "https://*.vercel.app",                # any Vercel preview (broad)
    "https://localhost:3000",              # local dev
]

# ─── Helpers ──────────────────────────────────────────────────────────────

def gql(query: str, variables: dict | None = None) -> dict:
    if not RAILWAY_TOKEN:
        sys.exit("RAILWAY_TOKEN env var required")
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(
        RAILWAY_API,
        data=body,
        headers={
            "Authorization": f"Bearer {RAILWAY_TOKEN}",
            "Content-Type": "application/json",
            # Cloudflare blocks the default Python urllib User-Agent (error 1010).
            "User-Agent": "curl/8.5.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            if data.get("errors"):
                raise RuntimeError(f"GraphQL errors: {json.dumps(data['errors'], indent=2)}")
            return data["data"]
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"HTTP {e.code}: {body}")


def http_get(url: str, headers: Optional[dict] = None, timeout: int = 15) -> tuple[int, str, dict]:
    req = urllib.request.Request(url, headers=headers or {}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode(), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(), dict(e.headers)
    except urllib.error.URLError as e:
        return 0, str(e), {}


def http_options(url: str, origin: str, timeout: int = 15) -> tuple[int, dict]:
    """CORS preflight check."""
    req = urllib.request.Request(
        url,
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "content-type",
        },
        method="OPTIONS",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers)
    except urllib.error.URLError as e:
        return 0, {"error": str(e)}


def set_var(name: str, value: str, skip_deploys: bool = True) -> None:
    """Upsert a Railway env var on the backend service."""
    gql("""
        mutation variableUpsert($input: VariableUpsertInput!) {
            variableUpsert(input: $input)
        }
    """, {
        "input": {
            "environmentId": ENVIRONMENT_ID,
            "serviceId": BACKEND_SERVICE_ID,
            "name": name,
            "value": value,
        },
    })
    print(f"   ✓ Set {name}={value[:60]}{'...' if len(value)>60 else ''}")
    if not skip_deploys:
        time.sleep(0.5)


def trigger_redeploy() -> str:
    """Redeploy the latest deployment. Returns deployment ID."""
    data = gql("""
        mutation redeploy($input: RedeployInput!) {
            redeploy(input: $input)
        }
    """, {
        "input": {
            "environmentId": ENVIRONMENT_ID,
            "serviceId": BACKEND_SERVICE_ID,
        },
    })
    deploy_id = data["redeploy"]
    print(f"   ✓ Triggered redeploy: {deploy_id}")
    return deploy_id


# ─── Step 1: Backend health check ─────────────────────────────────────────

def verify_backend() -> None:
    print("\n═══════════════════════════════════════════════════════════════")
    print("  Step 0 — Verify backend on Railway is healthy")
    print("═══════════════════════════════════════════════════════════════")
    print(f"  Backend URL: {BACKEND_URL}")

    code, body, _ = http_get(f"{BACKEND_URL}/health")
    if code == 200:
        print(f"  ✓ /health returned 200: {body[:200]}")
    else:
        print(f"  ✗ /health failed (HTTP {code}): {body[:200]}")
        sys.exit("Backend not healthy. Fix Railway deploy first.")

    code, body, _ = http_get(f"{BACKEND_URL}/api/hermes/health")
    if code == 200:
        print(f"  ✓ /api/hermes/health returned 200: {body[:200]}")
    else:
        print(f"  ⚠ /api/hermes/health failed (HTTP {code}) — Hermes may not be ready")


# ─── Step 2: Print Vercel UI instructions ─────────────────────────────────

def print_vercel_instructions() -> None:
    print("\n═══════════════════════════════════════════════════════════════")
    print("  Step 1 — Import the Havilah repo into Vercel")
    print("═══════════════════════════════════════════════════════════════")
    print(f"""
  1. Open  https://vercel.com/new
  2. Sign in with GitHub (the account that has access to {REPO_URL})
  3. Click  "Import Git Repository"  →  select  Ogienomo/havilah
  4. Configure the project:
       ┌──────────────────────────────────────────────────────────┐
       │ Framework Preset   : Next.js (auto-detected)            │
       │ Root Directory     : frontend/        ← IMPORTANT        │
       │ Build Command      : next build       (leave default)    │
       │ Install Command    : bun install      (from vercel.json) │
       │ Node.js Version    : 20.x            (Vercel default)    │
       └──────────────────────────────────────────────────────────┘
  5. Expand  "Environment Variables"  and add:

       NEXT_PUBLIC_HAVILAH_API_URL = {BACKEND_URL}
         → Environments: Production, Preview, Development

       NEXT_PUBLIC_HAVILAH_API_TOKEN =
         → Leave EMPTY for now (public Hermes endpoints don't need auth)

  6. Click  "Deploy"
  7. Wait ~2-3 minutes. Vercel will give you a URL like:
       https://havilah.vercel.app
       https://havilah-<hash>-Ogienomo.vercel.app   (auto-assigned)

  8. Copy your new Vercel URL — you'll paste it in Step 2 below.
""")


# ─── Step 3: Set CORS on backend ──────────────────────────────────────────

def configure_cors(vercel_url: str) -> None:
    print("\n═══════════════════════════════════════════════════════════════")
    print("  Step 2 — Add your Vercel URL to backend CORS allow-list")
    print("═══════════════════════════════════════════════════════════════")

    if not RAILWAY_TOKEN:
        print("  ⚠ RAILWAY_TOKEN not set — skipping automatic CORS update.")
        print(f"    Manually set this env var on Railway:")
        origins = ",".join([vercel_url] + DEFAULT_VERCEL_ORIGINS)
        print(f"    HAVILAH_CORS_ORIGINS = {origins}")
        return

    origins_list = [vercel_url] + [o for o in DEFAULT_VERCEL_ORIGINS if o != vercel_url]
    origins_value = ",".join(origins_list)
    print(f"  Setting HAVILAH_CORS_ORIGINS on Railway backend to:")
    for o in origins_list:
        print(f"    • {o}")
    set_var("HAVILAH_CORS_ORIGINS", origins_value)

    print("\n  Triggering redeploy so CORS change takes effect...")
    try:
        trigger_redeploy()
    except RuntimeError as e:
        print(f"  ⚠ Redeploy trigger failed (env var is still set): {e}")

    print("  → Backend will redeploy in ~30s. CORS is updated.")


# ─── Step 4: Verify CORS preflight ────────────────────────────────────────

def verify_cors(vercel_url: str) -> None:
    print("\n═══════════════════════════════════════════════════════════════")
    print("  Step 3 — Verify CORS preflight (Vercel → Backend)")
    print("═══════════════════════════════════════════════════════════════")
    print(f"  Simulating browser preflight from {vercel_url} ...")

    # Wait a moment for redeploy to settle
    print("  Waiting 30s for backend redeploy to complete...")
    time.sleep(30)

    code, headers = http_options(
        f"{BACKEND_URL}/api/hermes/health",
        origin=vercel_url,
    )

    if code == 200 or code == 204:
        allow_origin = headers.get("access-control-allow-origin", "(missing)")
        allow_methods = headers.get("access-control-allow-methods", "(missing)")
        print(f"  ✓ OPTIONS preflight succeeded (HTTP {code})")
        print(f"    access-control-allow-origin : {allow_origin}")
        print(f"    access-control-allow-methods: {allow_methods}")

        if allow_origin in ("*", vercel_url):
            print(f"  ✓ Your Vercel domain IS allowed by CORS.")
        else:
            print(f"  ⚠ Your Vercel domain may NOT be in the CORS allow-list.")
            print(f"    Expected: '{vercel_url}' or '*'")
            print(f"    Got:      '{allow_origin}'")
    else:
        print(f"  ⚠ OPTIONS preflight returned HTTP {code}")
        print(f"    This may indicate the redeploy hasn't finished yet.")
        print(f"    Wait 1-2 minutes and visit your Vercel URL in a browser.")
        print(f"    Open DevTools → Network tab → look for /api/hermes/health requests.")

    # Also verify a simple GET works
    print("\n  Verifying backend GET /api/hermes/health ...")
    code, body, _ = http_get(f"{BACKEND_URL}/api/hermes/health")
    if code == 200:
        print(f"  ✓ Backend is responding: {body[:200]}")
    else:
        print(f"  ✗ Backend GET failed: HTTP {code}")


# ─── Step 5: Final verification ───────────────────────────────────────────

def print_final_checklist(vercel_url: str) -> None:
    print("\n═══════════════════════════════════════════════════════════════")
    print("  Final Checklist — manually verify in your browser")
    print("═══════════════════════════════════════════════════════════════")
    print(f"""
  1. Open  {vercel_url}
  2. The dashboard should render with REAL data (not mock data):
       • Hero Stats shows 10 agents registered
       • Agent Grid shows all 10 agents as "Active"
       • Approval Queue shows any pending approvals
       • Activity Timeline shows recent Hermes runs
       • Memory Explorer shows recent memory entries

  3. Try the Hermes Command Center:
       • Type:  "Draft a welcome email for new client Acme Corp"
       • Click  "Execute"
       • Watch the pipeline animate: Plan → Dispatch → Approval gate
       • The Approval Queue should populate with a new pending step

  4. If the dashboard shows mock data instead of real data:
       • Check browser console for CORS errors
       • Verify NEXT_PUBLIC_HAVILAH_API_URL is set on Vercel
       • Verify HAVILAH_CORS_ORIGINS on Railway includes your Vercel URL
       • Redeploy on Vercel (Project → Deployments → ⋮ → Redeploy)

  5. Frontend ↔ Backend wiring is now complete:
       Vercel (frontend)  ──HTTPS──>  Railway (backend)  ──>  PostgreSQL
            ↓                              ↓
       Next.js + React Query        FastAPI + Hermes + 10 Agents
""")


# ─── Main ─────────────────────────────────────────────────────────────────

def main():
    instructions_only = "--instructions-only" in sys.argv

    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║   Havilah OS — Vercel Frontend Deployment Helper              ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print(f"  Backend : {BACKEND_URL}")
    print(f"  Repo    : {REPO_URL}")
    print(f"  Token   : {'set' if RAILWAY_TOKEN else 'NOT SET (CORS step will be skipped)'}")

    verify_backend()
    print_vercel_instructions()

    if instructions_only:
        print("\n  --instructions-only specified. Stopping here.")
        print("  Run again without the flag once you have your Vercel URL.")
        return

    print("\n  ───────────────────────────────────────────────────────────")
    print("  Once you have your Vercel URL, paste it below.")
    print("  (Include https://, e.g. https://havilah.vercel.app)")
    vercel_url = input("  Your Vercel URL > ").strip()

    if not vercel_url.startswith("https://"):
        sys.exit(f"URL must start with https:// — got: {vercel_url}")

    vercel_url = vercel_url.rstrip("/")
    configure_cors(vercel_url)
    verify_cors(vercel_url)
    print_final_checklist(vercel_url)
    print("\n✓ Vercel deployment helper complete.")


if __name__ == "__main__":
    main()
