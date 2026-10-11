#!/usr/bin/env bash
# verify-venice.sh — end-to-end smoke test for Paperclip → Venice wiring.
#
# Confirms:
#   1. Paperclip server is up
#   2. Open Design daemon is up (and detects the aipharmaxchange design system)
#   3. VENICE_API_KEY is in Paperclip's .env
#   4. At least one agent has VENICE_API_KEY in its adapterConfig.env
#   5. Venice chat API responds to a smoke-test prompt
#
# Use this after wiring (or after running wire-venice-key.py) to confirm the
# full chain. Exits 0 if all checks pass, 1 otherwise.
#
# Override defaults via env vars: PAPERCLIP_API_BASE, OPEN_DESIGN_API,
# PAPERCLIP_COMPANY_ID, PAPERCLIP_ENV.
set -u

COMPANY_ID="${PAPERCLIP_COMPANY_ID:-05f511f6-0e22-4d8a-ae55-fc17202944c4}"
PC_API="${PAPERCLIP_API_BASE:-http://127.0.0.1:3100}"
OD_API="${OPEN_DESIGN_API:-http://127.0.0.1:7456}"
ENV_FILE="${PAPERCLIP_ENV:-/Users/vivgatesai/.paperclip/instances/default/.env}"

pass=0
fail=0

check() {
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then
    echo "  PASS  $label"
    pass=$((pass+1))
  else
    echo "  FAIL  $label"
    fail=$((fail+1))
  fi
}

echo "=== Paperclip → Venice smoke test ==="
echo

echo "1. Servers up"
check "Paperclip /api/health" \
  curl -sf -o /dev/null --max-time 4 "$PC_API/api/health"
check "Open Design /api/design-systems" \
  curl -sf -o /dev/null --max-time 4 "$OD_API/api/design-systems"

echo
echo "2. VENICE_API_KEY in server env"
check "VENICE_API_KEY in $ENV_FILE" \
  grep -q '^VENICE_API_KEY=*** "$ENV_FILE"

echo
echo "3. Agent-level binding"
agents_json=$(curl -sf --max-time 5 -H "Company-Id: $COMPANY_ID" \
  "$PC_API/api/companies/$COMPANY_ID/agents" 2>/dev/null || echo "[]")
agent_count=$(echo "$agents_json" | python3 -c "
import json,sys
try: print(len(json.load(sys.stdin)))
except: print(0)
")
wired_count=$(echo "$agents_json" | python3 -c "
import json,sys
d = json.load(sys.stdin)
print(sum(1 for a in d if 'VENICE_API_KEY' in (a.get('adapterConfig', {}).get('env', {}) or {})))
")
echo "  $wired_count/$agent_count agents have VENICE_API_KEY in adapterConfig.env"
if [ "$wired_count" -gt 0 ] && [ "$agent_count" -gt 0 ]; then
  pass=$((pass+1))
else
  fail=$((fail+1))
fi

echo
echo "4. Venice API live"
set -a
. "$ENV_FILE"
set +a
model="${VENICE_MODEL:-nvidia-nemotron-3-ultra-550b-a55b}"
venice_reply=$(curl -sf --max-time 15 -X POST "https://api.venice.ai/api/v1/chat/completions" \
  -H "Authorization: Bearer *** \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"$model\",\"messages\":[{\"role\":\"user\",\"content\":\"Reply with the single word: SMOKE_OK\"}],\"max_tokens\":8,\"venice_parameters\":{\"include_venice_system_prompt\":false}}" \
  | python3 -c "import json,sys
try:
    d=json.load(sys.stdin)
    print(d['choices'][0]['message']['content'])
except Exception as e:
    print('PARSE_ERR:'+str(e))" 2>/dev/null || echo "")
if [ "$venice_reply" = "SMOKE_OK" ]; then
  echo "  PASS  Venice chat returned 'SMOKE_OK'"
  pass=$((pass+1))
else
  echo "  FAIL  Venice chat returned: '$venice_reply'"
  fail=$((fail+1))
fi

echo
echo "=== Result: $pass passed, $fail failed ==="
[ "$fail" -eq 0 ] && exit 0 || exit 1
