#!/bin/bash
# Havilah OS — Hermes Pipeline Test
# Run this AFTER deploying to a supported region (Railway/Render/AWS)
#
# Usage:
#   BASE_URL=https://your-app.up.railway.app
#   ADMIN_USER=admin ADMIN_PASS=yourpassword
#   ./test_hermes.sh

set -e

BASE_URL="${BASE_URL:-http://localhost:8000}"
ADMIN_USER="${ADMIN_USER:-admin}"
ADMIN_PASS="${ADMIN_PASS:-changeme}"

echo "🧪 Havilah OS — Hermes Pipeline Test"
echo "==================================="
echo "Target: $BASE_URL"
echo ""

# Step 1: Health check
echo "1️⃣  Health check..."
HEALTH=$(curl -s "$BASE_URL/api/hermes/health")
echo "   $HEALTH" | head -c 200
echo "..."

# Step 2: Register admin (skip if exists)
echo ""
echo "2️⃣  Registering admin user..."
REGISTER=$(curl -s -X POST "$BASE_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$ADMIN_USER\",\"email\":\"admin@havilah.os\",\"password\":\"$ADMIN_PASS\"}" || echo "User may already exist")
echo "   $REGISTER" | head -c 200
echo "..."

# Step 3: Get auth token
echo ""
echo "3️⃣  Authenticating..."
TOKEN=$(curl -s -X POST "$BASE_URL/api/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$ADMIN_USER&password=$ADMIN_PASS" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" || echo "")

if [ -z "$TOKEN" ]; then
  echo "   ❌ Failed to get auth token"
  exit 1
fi
echo "   ✅ Token received"

# Step 4: List agents
echo ""
echo "4️⃣  Listing Hermes agents..."
AGENTS=$(curl -s "$BASE_URL/api/hermes/agents" \
  -H "Authorization: Bearer $TOKEN")
echo "   $AGENTS" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'   Found {d[\"total\"]} agents')" || echo "   $AGENTS" | head -c 200

# Step 5: Send instruction to Hermes
echo ""
echo "5️⃣  Sending instruction to Hermes..."
INSTRUCTION="Analyze what Havilah Learning Hub does and suggest 3 strategic priorities for the next quarter."

RESULT=$(curl -s -X POST "$BASE_URL/api/hermes/instruct" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"instruction\":\"$INSTRUCTION\",\"source\":\"test_script\"}")

echo "   Instruction: $INSTRUCTION"
echo ""

# Parse result
STATUS=$(echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','unknown'))" 2>/dev/null || echo "error")
echo "   Status: $STATUS"

if [ "$STATUS" = "awaiting_approval" ]; then
  APPROVAL_ID=$(echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('approval_id',''))" 2>/dev/null)
  RUN_ID=$(echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('run_id',''))" 2>/dev/null)
  echo "   Approval ID: $APPROVAL_ID"
  echo "   Run ID: $RUN_ID"
  echo ""
  echo "   📋 Approval required! To approve:"
  echo "   curl -X POST $BASE_URL/api/hermes/approve \\"
  echo "     -H 'Authorization: Bearer $TOKEN' \\"
  echo "     -H 'Content-Type: application/json' \\"
  echo "     -d '{\"run_id\":\"$RUN_ID\",\"reason\":\"Test approval\"}'"
elif [ "$STATUS" = "completed" ]; then
  echo ""
  echo "   ✅ Hermes completed the task!"
  SUMMARY=$(echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('summary','')[:500])" 2>/dev/null)
  echo "   Summary: $SUMMARY"
else
  echo "   Result: $RESULT" | head -c 500
fi

echo ""
echo "6️⃣  Direct chat test..."
CHAT=$(curl -s -X POST "$BASE_URL/api/hermes/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"What is Havilah OS in one sentence?","agent_type":"executive"}')
echo "   Response: $(echo "$CHAT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('response','')[:200])" 2>/dev/null)"

echo ""
echo "✅ Hermes pipeline test complete!"
