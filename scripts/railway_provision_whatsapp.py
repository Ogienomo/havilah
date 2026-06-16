#!/usr/bin/env python3
"""
Havilah OS — WhatsApp Business API Provisioning Script
====================================================================

Sets the WhatsApp-related environment variables on the Railway backend
service, then triggers a redeploy so the WhatsApp bridge becomes active.

After running this, you must still:
  1. Subscribe your webhook in the Meta App dashboard
     (URL: https://havilah-production.up.railway.app/api/whatsapp/webhook)
  2. Run scripts/whatsapp_webhook_test.py to simulate an inbound message
     and verify the Hermes bridge receives + processes it.

Usage:
    RAILWAY_TOKEN=... \
    HAVILAH_WHATSAPP_ACCESS_TOKEN=EAAxxxx... \
    HAVILAH_WHATSAPP_PHONE_NUMBER_ID=1234567890 \
    HAVILAH_WHATSAPP_BUSINESS_ACCOUNT_ID=1234567890 \
    HAVILAH_WHATSAPP_VERIFY_TOKEN=havilah_verify_2026 \
    python3 scripts/railway_provision_whatsapp.py

    # Or set values interactively:
    RAILWAY_TOKEN=... python3 scripts/railway_provision_whatsapp.py --interactive

    # Dry run (show what would be set, don't actually write):
    RAILWAY_TOKEN=... python3 scripts/railway_provision_whatsapp.py --dry-run
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

# ─── Configuration ────────────────────────────────────────────────────────

RAILWAY_TOKEN = os.environ.get("RAILWAY_TOKEN") or ""
PROJECT_ID = "a8545ef4-4d74-483b-b069-7e34d96bb990"
ENVIRONMENT_ID = "f696a67c-db24-4086-b5ce-3484ce0a354d"
BACKEND_SERVICE_ID = "7db751d0-b3a4-47f9-99c1-7541cb857fa3"
BACKEND_URL = "https://havilah-production.up.railway.app"
WEBHOOK_URL = f"{BACKEND_URL}/api/whatsapp/webhook"

RAILWAY_API = "https://backboard.railway.app/graphql/v2"

# What we need to collect from Meta:
REQUIRED_VARS = [
    ("HAVILAH_WHATSAPP_ACCESS_TOKEN",        "Permanent (System User) access token from Meta App",      "EAAxxxxxxxxxxxxxx"),
    ("HAVILAH_WHATSAPP_PHONE_NUMBER_ID",     "Phone Number ID from WhatsApp → API Setup",              "1234567890"),
    ("HAVILAH_WHATSAPP_BUSINESS_ACCOUNT_ID", "WhatsApp Business Account ID from API Setup",            "1234567890"),
    ("HAVILAH_WHATSAPP_VERIFY_TOKEN",        "Any string you choose — must match Meta webhook config", "havilah_verify_2026"),
]

OPTIONAL_VARS = [
    ("HAVILAH_WHATSAPP_API_VERSION", "Meta Graph API version", "v21.0"),
]


# ─── GraphQL helper ───────────────────────────────────────────────────────

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


def set_var(name: str, value: str, dry_run: bool = False) -> None:
    if dry_run:
        masked = value if len(value) < 12 else value[:6] + "..." + value[-4:]
        print(f"   [DRY-RUN] Would set {name}={masked}")
        return
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
    masked = value if len(value) < 12 else value[:6] + "..." + value[-4:]
    print(f"   ✓ Set {name}={masked}")


def trigger_redeploy() -> str:
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


# ─── Input collection ─────────────────────────────────────────────────────

def collect_vars(interactive: bool) -> dict[str, str]:
    """Read WhatsApp env vars from environment, prompting interactively if needed."""
    out: dict[str, str] = {}
    print("\n  Collecting WhatsApp credentials from Meta App Dashboard:")
    print("  (Get these from https://developers.facebook.com → your app → WhatsApp → API Setup)\n")

    for name, description, example in REQUIRED_VARS:
        value = os.environ.get(name, "").strip()
        if not value and interactive:
            print(f"  {description}")
            print(f"  Example: {example}")
            value = input(f"  {name} > ").strip()
        if not value:
            print(f"  ✗ {name} is required.")
            if not interactive:
                print(f"    Set it as an env var OR re-run with --interactive.")
            sys.exit(1)
        out[name] = value

    for name, description, default in OPTIONAL_VARS:
        value = os.environ.get(name, default)
        out[name] = value
        print(f"   {name} = {value}  ({description})")

    # Always enable WhatsApp after provisioning
    out["HAVILAH_WHATSAPP_ENABLED"] = "true"
    out["HAVILAH_WHATSAPP_WEBHOOK_URL"] = "/api/whatsapp/webhook"
    return out


# ─── Verify webhook reachable ─────────────────────────────────────────────

def verify_webhook_endpoint(verify_token: str) -> None:
    print("\n═══════════════════════════════════════════════════════════════")
    print("  Verifying webhook GET endpoint is reachable (before Meta setup)")
    print("═══════════════════════════════════════════════════════════════")
    url = f"{WEBHOOK_URL}?hub.mode=subscribe&hub.verify_token={verify_token}&hub.challenge=12345"
    print(f"  GET {url}")
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode()
            print(f"  ✓ HTTP {resp.status} — response: {body[:200]}")
            if body.strip() == "12345":
                print("  ✓ Webhook verification challenge PASSED.")
                print("    Meta will accept this URL when you subscribe.")
            else:
                print(f"  ⚠ Expected '12345' challenge response, got: {body}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"  ✗ HTTP {e.code}: {body[:200]}")
        if e.code == 403:
            print("  → Backend returned 403. This means the verify token hasn't")
            print("    propagated yet — wait for the redeploy to finish (1-2 min).")
    except urllib.error.URLError as e:
        print(f"  ✗ Network error: {e}")


# ─── Wait for redeploy ────────────────────────────────────────────────────

def wait_for_deploy(timeout_sec: int = 300) -> bool:
    print(f"\n  Waiting up to {timeout_sec}s for backend redeploy to finish...")
    start = time.time()
    last_status = None
    while time.time() - start < timeout_sec:
        try:
            data = gql("""
                query($envId: String!, $serviceId: String!) {
                    environment(id: $envId) {
                        latestDeployment {
                            id
                            status
                            createdAt
                        }
                    }
                }
            """, {"envId": ENVIRONMENT_ID, "serviceId": BACKEND_SERVICE_ID})
            status = data["environment"]["latestDeployment"]["status"]
            if status != last_status:
                print(f"   deploy status: {status}")
                last_status = status
            if status == "SUCCESS":
                print("  ✓ Deploy succeeded.")
                return True
            if status in ("FAILED", "CRASHED"):
                print(f"  ✗ Deploy {status}. Check Railway logs.")
                return False
        except Exception as e:
            print(f"   (status query failed: {e})")
        time.sleep(5)
    print(f"  ⚠ Timed out after {timeout_sec}s — check Railway dashboard.")
    return False


# ─── Main ─────────────────────────────────────────────────────────────────

def main():
    dry_run = "--dry-run" in sys.argv
    interactive = "--interactive" in sys.argv

    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║   Havilah OS — WhatsApp Business API Provisioning            ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print(f"  Backend  : {BACKEND_URL}")
    print(f"  Webhook  : {WEBHOOK_URL}")
    print(f"  Token    : {'set' if RAILWAY_TOKEN else 'NOT SET'}")
    print(f"  Mode     : {'DRY RUN' if dry_run else 'INTERACTIVE' if interactive else 'AUTO (env vars)'}")

    if not RAILWAY_TOKEN and not dry_run:
        sys.exit("RAILWAY_TOKEN env var required (or use --dry-run)")

    vars_to_set = collect_vars(interactive=interactive)

    print("\n═══════════════════════════════════════════════════════════════")
    print("  Setting WhatsApp env vars on Railway backend service")
    print("═══════════════════════════════════════════════════════════════")
    for name, value in vars_to_set.items():
        set_var(name, value, dry_run=dry_run)

    if dry_run:
        print("\n  [DRY-RUN] No changes written. Re-run without --dry-run to apply.")
        return

    print("\n═══════════════════════════════════════════════════════════════")
    print("  Triggering backend redeploy so WhatsApp bridge becomes active")
    print("═══════════════════════════════════════════════════════════════")
    try:
        trigger_redeploy()
    except RuntimeError as e:
        print(f"  ⚠ Redeploy trigger failed (env vars are still set): {e}")
        print("  Manually redeploy from Railway UI.")

    wait_for_deploy(timeout_sec=300)
    verify_webhook_endpoint(verify_token=vars_to_set["HAVILAH_WHATSAPP_VERIFY_TOKEN"])

    print("\n═══════════════════════════════════════════════════════════════")
    print("  Next Steps — Subscribe webhook in Meta App Dashboard")
    print("═══════════════════════════════════════════════════════════════")
    print(f"""
  1. Open  https://developers.facebook.com  →  your app  →  WhatsApp  →  Configuration
  2. Click  "Edit"  next to Webhook
  3. Callback URL  : {WEBHOOK_URL}
     Verify Token  : {vars_to_set["HAVILAH_WHATSAPP_VERIFY_TOKEN"]}
  4. Click  "Verify and Save"  (Meta will GET your webhook to verify)
  5. Subscribe to these fields:
       ☑ messages
       ☑ message_deliveries
       ☑ message_reads
       ☑ message_template_status_updates
  6. Add a test recipient phone number (WhatsApp → API Setup → To field)
  7. Send a WhatsApp message to your business number:
       "Hello"
  8. Run the webhook test script to simulate an inbound message:
       RAILWAY_TOKEN=... python3 scripts/whatsapp_webhook_test.py
  9. Check Railway backend logs — you should see:
       "WhatsApp webhook received: ..."
       "Routing WhatsApp message to Hermes: 'Hello'"
""")

    print("\n✓ WhatsApp provisioning complete.")
    print("  Hermes is now reachable via WhatsApp messages to your business number.")


if __name__ == "__main__":
    main()
