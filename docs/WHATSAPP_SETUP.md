# Havilah OS — WhatsApp Business API Setup Guide

This guide walks you through connecting WhatsApp Business API to Havilah OS so you can control Hermes via WhatsApp.

## Prerequisites

1. A **Meta Business Account** (free): [business.facebook.com](https://business.facebook.com)
2. A **WhatsApp Business Platform** app
3. A phone number NOT already registered with WhatsApp

## Step-by-Step Setup

### 1. Create Meta App

1. Go to [developers.facebook.com](https://developers.facebook.com)
2. Click **My Apps** → **Create App**
3. Select **Business** as the type
4. Name it "Havilah OS"
5. Add the **WhatsApp** product

### 2. Get Your Credentials

From the Meta App Dashboard, collect these values:

| Setting | Where to find it | Env var |
|---------|------------------|---------|
| **Phone Number ID** | WhatsApp → API Setup → Phone Number ID | `HAVILAH_WHATSAPP_PHONE_NUMBER_ID` |
| **Access Token** | WhatsApp → API Setup → Temporary Access Token (or System User token) | `HAVILAH_WHATSAPP_ACCESS_TOKEN` |
| **Verify Token** | You create this (any string) | `HAVILAH_WHATSAPP_VERIFY_TOKEN` |
| **Business Account ID** | WhatsApp → API Setup → WhatsApp Business Account ID | `HAVILAH_WHATSAPP_BUSINESS_ACCOUNT_ID` |

### 3. Configure Environment Variables

In your Railway project (or `.env` locally):

```bash
HAVILAH_WHATSAPP_ENABLED=true
HAVILAH_WHATSAPP_VERIFY_TOKEN=havilah_verify_2026
HAVILAH_WHATSAPP_ACCESS_TOKEN=EAAxxxxxxxxxxxxxx
HAVILAH_WHATSAPP_PHONE_NUMBER_ID=1234567890
HAVILAH_WHATSAPP_BUSINESS_ACCOUNT_ID=1234567890
```

### 4. Set Up Webhook

1. In Meta App → WhatsApp → Configuration → Webhook
2. Click **Edit**
3. **Callback URL**: `https://<your-railway-app>.up.railway.app/api/whatsapp/webhook`
4. **Verify Token**: `havilah_verify_2026` (must match your env var)
5. Click **Verify and Save**
6. Subscribe to these fields:
   - `messages`
   - `message_deliveries`
   - `message_reads`
   - `message_template_status_updates`

### 5. Add a Test Phone Number

1. In Meta App → WhatsApp → API Setup → To field
2. Add your phone number (the one you'll text FROM)
3. Verify with the SMS code

### 6. Test the Integration

Send a WhatsApp message to your business number:
- Text: `"Hello"`
- Expected response: Hermes processes it and replies

### 7. Production Setup

To send messages to ANY phone number (not just test numbers):

1. **Add a phone number** to your WhatsApp Business Account
2. **Verify your business** (Meta requires business verification)
3. **Create message templates** (required for initiating conversations)
4. Wait for approval (24-48 hours)

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

## How It Works

```
You text WhatsApp
       ↓
Meta Webhook → /api/whatsapp/webhook
       ↓
WhatsAppBridge detects intent
       ↓
HermesOrchestrator processes instruction
       ↓
If approval needed → creates approval request
       ↓
You reply "approve" or "reject"
       ↓
Hermes continues or cancels
       ↓
Result sent back via WhatsApp
```

## Troubleshooting

**Webhook verification fails:**
- Ensure `HAVILAH_WHATSAPP_VERIFY_TOKEN` matches exactly
- Check the webhook URL is publicly accessible (Railway provides this)

**Messages don't arrive:**
- Verify webhook subscription includes `messages`
- Check Railway logs for incoming requests

**Cannot send to non-test numbers:**
- Business verification required for production
- Use message templates for outbound messaging

**Rate limits:**
- 80 messages per second (default)
- 1000 business-initiated conversations per 24h (free tier)

## Cost

- **First 1000 conversations/month**: FREE
- **Business-initiated**: $0.025/conversation
- **User-initiated**: $0.0088/conversation
- Most small businesses pay under $5/month
