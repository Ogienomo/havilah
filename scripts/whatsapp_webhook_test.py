#!/usr/bin/env python3
"""
Havilah OS — WhatsApp Webhook Test Script
====================================================================

Sends a SIMULATED WhatsApp webhook payload to the Havilah backend,
mimicking what Meta's servers would send when a user texts your
business number. This lets you verify the Hermes bridge end-to-end
WITHOUT needing a verified Meta Business account or production
WhatsApp number.

The script:
  1. Sends the Meta webhook verification GET (verify_token challenge)
  2. Sends a simulated inbound "help" text message
  3. Sends a simulated inbound "approve" text message
  4. Sends a simulated inbound "Draft an email to John" instruction
  5. Reads back /api/hermes/runs to confirm Hermes received + planned

Usage:
    python3 scripts/whatsapp_webhook_test.py
    # Or with a custom verify token:
    HAVILAH_WHATSAPP_VERIFY_TOKEN=havilah_verify_2026 \\
    python3 scripts/whatsapp_webhook_test.py

Prerequisites:
    - Backend deployed on Railway
    - WhatsApp env vars set (run scripts/railway_provision_whatsapp.py first)
    - Backend redeployed after env vars set
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

BACKEND_URL = os.environ.get("BACKEND_URL", "https://havilah-production.up.railway.app")
WEBHOOK_URL = f"{BACKEND_URL}/api/whatsapp/webhook"
VERIFY_TOKEN = os.environ.get("HAVILAH_WHATSAPP_VERIFY_TOKEN", "havilah_verify_2026")

# Use a fake phone number — Meta's test number is +1 555 555 1234
TEST_PHONE = "15555551234"
BOT_PHONE_ID = "1234567890"  # Whatever was set as HAVILAH_WHATSAPP_PHONE_NUMBER_ID


# ─── Helpers ──────────────────────────────────────────────────────────────

def http_get(url: str, timeout: int = 15) -> tuple[int, str, dict]:
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode(), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(), dict(e.headers)
    except urllib.error.URLError as e:
        return 0, str(e), {}


def http_post_json(url: str, payload: dict, timeout: int = 30) -> tuple[int, str]:
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except urllib.error.URLError as e:
        return 0, str(e)


def make_webhook_payload(message_text: str, msg_id: str = "wamid.test123") -> dict:
    """Construct a Meta-format webhook payload simulating an inbound text message."""
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "test_entry_id",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "+1 555 555 0000",
                                "phone_number_id": BOT_PHONE_ID,
                            },
                            "contacts": [
                                {
                                    "profile": {"name": "Test User"},
                                    "wa_id": TEST_PHONE,
                                }
                            ],
                            "messages": [
                                {
                                    "from": TEST_PHONE,
                                    "id": msg_id,
                                    "timestamp": str(int(time.time())),
                                    "text": {"body": message_text},
                                    "type": "text",
                                }
                            ],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
    }


# ─── Tests ────────────────────────────────────────────────────────────────

def test_verify_challenge() -> None:
    print("\n═══════════════════════════════════════════════════════════════")
    print("  Test 1 — Webhook verification (GET hub.challenge)")
    print("═══════════════════════════════════════════════════════════════")
    url = (
        f"{WEBHOOK_URL}"
        f"?hub.mode=subscribe"
        f"&hub.verify_token={VERIFY_TOKEN}"
        f"&hub.challenge=987654"
    )
    print(f"  GET {url}")
    code, body, _ = http_get(url)
    print(f"  HTTP {code} — response: {body[:200]}")
    if code == 200 and body.strip() == "987654":
        print("  ✓ Verification challenge PASSED. Meta can subscribe this webhook.")
    elif code == 403:
        print("  ✗ 403 Forbidden — verify token mismatch.")
        print(f"    Sent: {VERIFY_TOKEN}")
        print(f"    Check HAVILAH_WHATSAPP_VERIFY_TOKEN on Railway backend.")
    else:
        print(f"  ⚠ Unexpected response.")


def test_inbound_message(text: str, label: str, expect_hermes: bool = True) -> None:
    print(f"\n═══════════════════════════════════════════════════════════════")
    print(f"  Test — {label}")
    print(f"═══════════════════════════════════════════════════════════════")
    print(f"  Inbound WhatsApp text: \"{text}\"")

    payload = make_webhook_payload(text, msg_id=f"wamid.test.{int(time.time()*1000)}")
    print(f"  POST {WEBHOOK_URL}")
    print(f"  Body: {json.dumps(payload)[:300]}...")

    code, body = http_post_json(WEBHOOK_URL, payload, timeout=60)
    print(f"  HTTP {code} — response: {body[:500]}")
    if code == 200:
        print(f"  ✓ Webhook accepted by backend.")
    else:
        print(f"  ✗ Webhook POST failed.")


def check_hermes_runs() -> None:
    print("\n═══════════════════════════════════════════════════════════════")
    print("  Check — Latest Hermes runs (should show webhook-routed runs)")
    print("═══════════════════════════════════════════════════════════════")
    code, body, _ = http_get(f"{BACKEND_URL}/api/hermes/runs?limit=5", timeout=20)
    if code != 200:
        print(f"  ✗ /api/hermes/runs failed: HTTP {code} — {body[:200]}")
        return
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        print(f"  ⚠ Could not parse response: {body[:200]}")
        return

    runs = data.get("runs") or data.get("data") or data
    if not isinstance(runs, list):
        print(f"  ⚠ Unexpected response shape: {data}")
        return

    print(f"  Found {len(runs)} recent Hermes run(s):")
    for r in runs[:5]:
        status = r.get("status", "?")
        instruction = (r.get("instruction") or r.get("user_instruction") or "")[:80]
        run_id = r.get("id", "?")
        print(f"    • [{status:20}] {instruction}")
        print(f"      run_id={run_id}")


def check_whatsapp_status() -> None:
    print("\n═══════════════════════════════════════════════════════════════")
    print("  Check — WhatsApp integration status on backend")
    print("═══════════════════════════════════════════════════════════════")
    code, body, _ = http_get(f"{BACKEND_URL}/api/whatsapp/status", timeout=10)
    print(f"  HTTP {code} — response: {body[:400]}")
    if code == 200:
        try:
            data = json.loads(body)
            if data.get("enabled"):
                print("  ✓ WhatsApp integration is ENABLED.")
            else:
                print("  ⚠ WhatsApp integration is DISABLED (HAVILAH_WHATSAPP_ENABLED != true).")
            if not data.get("access_token_configured"):
                print("  ⚠ HAVILAH_WHATSAPP_ACCESS_TOKEN not set — replies won't work.")
            if not data.get("phone_number_id_configured"):
                print("  ⚠ HAVILAH_WHATSAPP_PHONE_NUMBER_ID not set — replies won't work.")
        except json.JSONDecodeError:
            pass
    elif code == 401 or code == 403:
        print("  (Status endpoint requires auth — skipping detailed check.)")


# ─── Main ─────────────────────────────────────────────────────────────────

def main():
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║   Havilah OS — WhatsApp Webhook Simulation Test              ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print(f"  Backend  : {BACKEND_URL}")
    print(f"  Webhook  : {WEBHOOK_URL}")
    print(f"  Token    : {VERIFY_TOKEN}")
    print(f"  Test phone (sender): {TEST_PHONE}")

    # 1. Backend health
    code, body, _ = http_get(f"{BACKEND_URL}/health", timeout=10)
    if code != 200:
        sys.exit(f"Backend not healthy: HTTP {code} — {body}")
    print(f"  ✓ Backend healthy: {body}")

    # 2. WhatsApp status
    check_whatsapp_status()

    # 3. Webhook verification challenge
    test_verify_challenge()

    # 4. Simulated inbound messages
    test_inbound_message("help", "Help command")
    time.sleep(2)

    test_inbound_message("What's pending?", "Status query")
    time.sleep(2)

    test_inbound_message(
        "Draft a welcome email for new client Acme Corp. Make it warm but professional.",
        "Real Hermes instruction via WhatsApp",
    )
    time.sleep(5)

    # 5. Verify Hermes processed them
    check_hermes_runs()

    print("\n═══════════════════════════════════════════════════════════════")
    print("  What to check in Railway backend logs:")
    print("═══════════════════════════════════════════════════════════════")
    print("""  You should see log lines like:
    INFO: WhatsApp webhook received: {...}
    INFO: Routing WhatsApp message to Hermes: 'help'
    INFO: Routing WhatsApp message to Hermes: 'What's pending?'
    INFO: Routing WhatsApp message to Hermes: 'Draft a welcome email...'

  View logs:
    Railway Dashboard → Backend service → Deployments → latest → Logs
  Or via GraphQL (requires Railway token):
    python3 scripts/railway_logs.py
""")

    print("\n✓ Webhook test complete.")
    print("  If Hermes planned the email instruction, the WhatsApp → Hermes bridge works.")


if __name__ == "__main__":
    main()
