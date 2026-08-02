#!/bin/bash
# verify-kriya-auth.sh — smoke test that OpenClaw/Kriya can authenticate to Venice
# and get a real model response. Run after re-registering the API key or after
# any OpenClaw upgrade.
#
# Usage: bash verify-kriya-auth.sh
# Exit codes:
#   0 — auth profile registered AND model returned a response
#   1 — no auth profile registered
#   2 — auth profile registered but model call failed

set -uo pipefail

OC=~/.hermes/node/bin/openclaw
GATEWAY_URL="${OPENCLAW_GATEWAY_URL:-http://127.0.0.1:18789}"

echo "1. Gateway health:"
curl -fsS "${GATEWAY_URL}/health" || { echo "❌ gateway not reachable"; exit 2; }
echo

echo "2. Registered auth profiles:"
PROFILES="$($OC models auth list 2>&1 | grep -E '^- ' || true)"
if [ -z "$PROFILES" ]; then
  echo "❌ no auth profiles registered"
  echo "   Fix: echo \"<VENICE_INFERENCE_KEY_...>\" | $OC models auth paste-api-key --provider venice"
  exit 1
fi
echo "$PROFILES"
echo

echo "3. Sending smoke-test prompt to main agent..."
RESPONSE="$($OC agent --message "Reply with exactly one word: pong" --agent main 2>&1)"
echo "$RESPONSE" | tail -3
echo

echo "4. Checking gateway logs for 'pong' response..."
sleep 2
if $OC logs 2>&1 | tail -200 | grep -q "pong"; then
  echo "✅ pong response found in logs — Kriya is healthy"
  exit 0
else
  echo "❌ no 'pong' in recent logs — model call likely failed"
  echo "   Recent error lines:"
  $OC logs 2>&1 | tail -200 | grep -iE "(failovererror|missing-provider-auth|no api key)" | head -3
  exit 2
fi