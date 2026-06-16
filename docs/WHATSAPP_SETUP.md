# Havilah OS — WhatsApp Business API Setup Guide

This guide walks you through connecting WhatsApp Business API to Havilah OS so you can control Hermes via WhatsApp.

## Architecture

```
You text WhatsApp
       ↓
Meta Cloud API
       ↓
POST https://havilah-production.up.railway.app/api/whatsapp/webhook
       ↓
WhatsAppService.process_webhook()
   ├── Persist message to whatsapp_messages table
   ├── Lookup/create session in whatsapp_sessions table
   └── _route_to_hermes(payload)
              ↓
       WhatsAppBridge.process_incoming_message()
              ↓
       HermesOrchestrator.instruct()
              ↓
       Plan → Dispatch agents → Approval gate
              ↓
       (Optional) Reply via WhatsApp API
```

## Prerequisites

1. Backend deployed on Railway — `https://havilah-production.up.railway.app`
2. A **Meta Business Account** (free): [business.facebook.com](https://business.facebook.com)
3. A **WhatsApp Business Platform** app
4. A phone number NOT already registered with WhatsApp
5. Railway token: `976a6c97-33cb-418c-9f76-ac124b33f6b4`

The 4 WhatsApp tables (`whatsapp_sessions`, `whatsapp_messages`, `whatsapp_templates`, `whatsapp_approval_votes`) were added in migration `002_whatsapp_tables.py` and are already deployed.

---

## Step-by-Step Setup

### 1. Create Meta App

1. Go to [developers.facebook.com](https://developers.facebook.com)
2. Click **My Apps** → **Create App**
3. Select **Business** as the type
4. Name it "Havilah OS"
5. Add the **WhatsApp** product

### 2. Get Your Credentials

From the Meta App Dashboard → WhatsApp → API Setup, collect these four values:

| Setting | Where to find it | Env var |
|---------|------------------|---------|
| **Phone Number ID** | API Setup → "Phone Number ID" (top right) | `HAVILAH_WHATSAPP_PHONE_NUMBER_ID` |
| **Access Token** | API Setup → "Temporary Access Token" → Configure → System User → Generate token | `HAVILAH_WHATSAPP_ACCESS_TOKEN` |
| **Verify Token** | You create this (any string, e.g. `havilah_verify_2026`) | `HAVILAH_WHATSAPP_VERIFY_TOKEN` |
| **Business Account ID** | API Setup → "WhatsApp Business Account ID" | `HAVILAH_WHATSAPP_BUSINESS_ACCOUNT_ID` |

### 3. Provision WhatsApp on Railway (One Command)

Run the provisioning script — it sets all 5 env vars on the backend, triggers a redeploy, and verifies the webhook endpoint is reachable:

```bash
RAILWAY_TOKEN=976a6c97-33cb-418c-9f76-ac124b33f6b4 \
HAVILAH_WHATSAPP_ACCESS_TOKEN=EAAxxxxxxxxxxxxxx \
HAVILAH_WHATSAPP_PHONE_NUMBER_ID=1234567890 \
HAVILAH_WHATSAPP_BUSINESS_ACCOUNT_ID=1234567890 \
HAVILAH_WHATSAPP_VERIFY_TOKEN=havilah_verify_2026 \
  python3 scripts/railway_provision_whatsapp.py
```

Or interactively (it will prompt you for each value):

```bash
RAILWAY_TOKEN=976a6c97-33cb-418c-9f76-ac124b33f6b4 \
  python3 scripts/railway_provision_whatsapp.py --interactive
```

Dry-run mode (shows what would be set without writing):

```bash
RAILWAY_TOKEN=... python3 scripts/railway_provision_whatsapp.py --dry-run
```

After the script completes:
- ✅ `HAVILAH_WHATSAPP_ENABLED=true`
- ✅ `HAVILAH_WHATSAPP_VERIFY_TOKEN`, `ACCESS_TOKEN`, `PHONE_NUMBER_ID`, `BUSINESS_ACCOUNT_ID` all set
- ✅ Backend redeployed and webhook GET verification passes

### 4. Subscribe Webhook in Meta Dashboard

In Meta App → WhatsApp → Configuration → Webhook:

1. Click **Edit**
2. **Callback URL**: `https://havilah-production.up.railway.app/api/whatsapp/webhook`
3. **Verify Token**: `havilah_verify_2026` (must match what you set in Step 3)
4. Click **Verify and Save** — Meta will GET your webhook with `hub.mode=subscribe` and expect the challenge echoed back. The provisioning script already verified this works.
5. Subscribe to these fields (tick the checkboxes):
   - ☑ `messages`
   - ☑ `message_deliveries`
   - ☑ `message_reads`
   - ☑ `message_template_status_updates`

### 5. Add a Test Phone Number

1. In Meta App → WhatsApp → API Setup → "To" field
2. Add your personal phone number (the one you'll text FROM)
3. Verify with the SMS code Meta sends
4. (Optional) Send a test template message from the dashboard to confirm outbound works

### 6. Test End-to-End (Without Meta)

Run the simulated webhook test script — it sends a fake Meta-format payload to your backend, mimicking real inbound messages:

```bash
python3 scripts/whatsapp_webhook_test.py
```

The script will:
1. Test GET webhook verification challenge
2. Send a simulated "help" text message
3. Send a simulated "What's pending?" status query
4. Send a simulated real Hermes instruction: `"Draft a welcome email for new client Acme Corp"`
5. Verify the backend persisted messages and routed to Hermes

You should see HTTP 200 with `status: processed` for each message. Check Railway backend logs for:
```
INFO: WhatsApp webhook received: {...}
INFO: Routing WhatsApp message to Hermes: 'help'
INFO: Routing WhatsApp message to Hermes: 'Draft a welcome email...'
```

### 7. Test End-to-End (With Real WhatsApp)

Send a WhatsApp message to your business number:
- Text: `"Hello"` → Hermes should reply with a welcome + help text
- Text: `"Draft an email to John about Q2 goals"` → Hermes plans, asks for approval
- Text: `"approve"` → Hermes continues execution

### 8. Production Setup (Optional)

To send messages to ANY phone number (not just test numbers):

1. **Add a phone number** to your WhatsApp Business Account (WhatsApp → Phone Numbers → Add)
2. **Verify your business** (Meta → Business Settings → Business Verification)
3. **Create message templates** (WhatsApp → Message Templates — required for initiating conversations)
4. Wait for template approval (24-48 hours)
5. Run `python3 scripts/railway_register_test.py` to seed default templates (calls `/api/whatsapp/seed-templates`)

---

## WhatsApp Commands for Hermes

Once configured, you can text these to your business number:

| Message | What Hermes does |
|---------|------------------|
| `Create a project for Client X` | Plans and creates a project |
| `Draft an email to John about Q2 goals` | Drafts the email (requires approval before sending) |
| `What's pending?` | Shows approval queue |
| `approve` | Approves the pending step |
| `reject` | Rejects the pending step |
| `help` | Shows available commands |

---

## How It Works

```
You text WhatsApp
       ↓
Meta Webhook → POST /api/whatsapp/webhook
       ↓
WhatsAppService.process_webhook()
   ├── Save to whatsapp_messages table
   ├── Update whatsapp_sessions row
   └── _route_to_hermes() if HERMES_ENABLED and OPENAI_API_KEY set
              ↓
       WhatsAppBridge.process_incoming_message()
              ↓
       HermesOrchestrator.instruct(text)
              ↓
       GPT-4o plans steps → dispatches agents
              ↓
       If approval needed → creates approval_request
              ↓
       You reply "approve" or "reject"
              ↓
       Hermes continues or cancels
              ↓
       Result sent back via WhatsApp API
```

---

## Troubleshooting

**Webhook verification fails (Meta dashboard shows red X):**
- Ensure `HAVILAH_WHATSAPP_VERIFY_TOKEN` on Railway matches what you typed in Meta exactly
- Verify the callback URL is `https://havilah-production.up.railway.app/api/whatsapp/webhook` (note `https://`)
- Run `python3 scripts/railway_provision_whatsapp.py` again with `--interactive` to re-set the token
- Check Railway backend logs for the verification GET request

**Messages don't arrive at the backend:**
- Verify webhook subscription includes `messages` (Step 4.5)
- Make sure your phone number is added as a test recipient (Step 5)
- Check Railway → Backend Service → Deployments → Latest → Logs

**Webhook returns 200 but Hermes doesn't process:**
- Confirm `HAVILAH_HERMES_ENABLED=true` on Railway
- Confirm `HAVILAH_OPENAI_API_KEY` is set
- The bridge silently skips routing if either is missing
- Run `python3 scripts/whatsapp_webhook_test.py` to see exact backend response

**`relation "whatsapp_sessions" does not exist`:**
- Migration `002_whatsapp_tables.py` should have created the tables
- Verify it ran: check Railway deploy logs for "Running upgrade 001 -> 002"
- Force re-run: `RAILWAY_TOKEN=... python3 scripts/railway_run_migrations.py`
- Or trigger a fresh redeploy: Railway → Deployments → ⋮ → Redeploy

**Cannot send to non-test numbers:**
- Business verification required for production
- Use message templates for outbound messaging
- Run `python3 scripts/railway_register_test.py` to seed default templates

**Rate limits:**
- 80 messages per second (default)
- 1000 business-initiated conversations per 24h (free tier)

---

## Cost

- **First 1000 conversations/month**: FREE
- **Business-initiated**: $0.025/conversation
- **User-initiated**: $0.0088/conversation
- Most small businesses pay under $5/month

---

## Reference — Environment Variables

All WhatsApp env vars live on the Railway backend service. Set them via the provisioning script or Railway UI:

| Variable | Purpose | Example |
|----------|---------|---------|
| `HAVILAH_WHATSAPP_ENABLED` | Master on/off switch | `true` |
| `HAVILAH_WHATSAPP_VERIFY_TOKEN` | Webhook verification (any string) | `havilah_verify_2026` |
| `HAVILAH_WHATSAPP_ACCESS_TOKEN` | Meta System User token | `EAAxxxxxxxxx...` |
| `HAVILAH_WHATSAPP_PHONE_NUMBER_ID` | Sender phone number ID | `1234567890` |
| `HAVILAH_WHATSAPP_BUSINESS_ACCOUNT_ID` | WABA ID | `1234567890` |
| `HAVILAH_WHATSAPP_API_VERSION` | Meta Graph API version | `v21.0` |
| `HAVILAH_WHATSAPP_WEBHOOK_URL` | Webhook path on backend | `/api/whatsapp/webhook` |

## Reference — API Endpoints

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/api/whatsapp/webhook` | GET | none | Meta webhook verification |
| `/api/whatsapp/webhook` | POST | none | Meta inbound message delivery |
| `/api/whatsapp/status` | GET | JWT | Integration status check |
| `/api/whatsapp/send/text` | POST | JWT + `whatsapp:send_message` | Send a text message |
| `/api/whatsapp/send/template` | POST | JWT + `whatsapp:send_message` | Send a template message |
| `/api/whatsapp/send/interactive` | POST | JWT + `whatsapp:send_message` | Send buttons/list |
| `/api/whatsapp/send/approval` | POST | JWT + `whatsapp:send_approval` | Send approval with buttons |
| `/api/whatsapp/sessions` | GET | JWT + `whatsapp:manage_sessions` | List sessions |
| `/api/whatsapp/templates` | GET/POST | JWT + `whatsapp:manage_templates` | List/create templates |
| `/api/whatsapp/seed-templates` | POST | JWT (admin) | Seed default templates |
