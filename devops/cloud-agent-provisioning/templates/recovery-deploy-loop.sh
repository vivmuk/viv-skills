#!/usr/bin/env bash
# recovery-deploy-loop.sh — idempotent bounded retry loop for cloud-agent deploys.
#
# Save path:    ~/.config/<platform>/recovery-deploy-loop.sh
# Re-applies:
#   - Auth probe via shell-source env loader (no token in argv)
#   - Create the agent if missing (idempotent)
#   - Re-write the .env file from loaded env vars (no secret in argv)
#   - Platform `env import <file>` (only file path on argv)
#   - Deploy with bounded N attempts (politeness toward upstream VM provisioner)
#   - Poll `status` until active / running / ready or budget exhausted
#
# Override via env:
#   AGENT_NAME=foo ./recovery-deploy-loop.sh
#   MAX_ATTEMPTS=8 ./recovery-deploy-loop.sh
#   POLL_INTERVAL=60 ./recovery-deploy-loop.sh

set -euo pipefail

PLATFORM=${PLATFORM:-maritime}
PLATFORM_ENV=${PLATFORM_ENV:-$HOME/.config/${PLATFORM}/maritime-env.sh}

# 1. Source env (find the env-loader script first, then source it)
[ -r "$PLATFORM_ENV" ] || { echo "ERROR: env loader missing: $PLATFORM_ENV" >&2; exit 2; }
# shellcheck disable=SC1090
source "$PLATFORM_ENV"

# 2. Tunables
AGENT_NAME=${AGENT_NAME:-nira}
TEMPLATE=${TEMPLATE:-hermes}
TIER=${TIER:-extended}
MODEL=${MODEL:-xiaomi-mimo-v2-5}
ENV_FILE=${ENV_FILE:-$HOME/.config/${PLATFORM}/${AGENT_NAME}.env}
MAX_ATTEMPTS=${MAX_ATTEMPTS:-5}
POLL_INTERVAL=${POLL_INTERVAL:-30}

# 3. Auth probe
if ! "$PLATFORM" whoami --json 2>/dev/null | grep -q '"authenticated": true'; then
  echo "ERROR: $PLATFORM auth failed; check $PLATFORM_ENV" >&2; exit 2
fi

# 4. Create-if-missing (clean idempotent gate)
existing=$("$PLATFORM" list --json 2>/dev/null | python3 -c "
import sys,json
try: print(any(a.get('name')=='$AGENT_NAME' for a in json.loads(sys.stdin.read())))
except: print('check_failed')
")
if [ "$existing" = "True" ]; then
  echo "[deploy-loop] agent '$AGENT_NAME' exists; reusing"
else
  echo "[deploy-loop] creating agent name=$AGENT_NAME  tier=$TIER  template=$TEMPLATE"
  "$PLATFORM" create "$AGENT_NAME" --template "$TEMPLATE" --tier "$TIER" --json \
    | python3 -c "
import sys,json
d=json.loads(sys.stdin.read())
for k in ('id','framework','tier','status'):
    print(f'  {k}: {d.get(k)}')
"
fi

# 5. Write the .env file from loaded env vars; never from argv
export NV_FILE="$ENV_FILE"
export NV_MODEL="$MODEL"
python3 -c "
import os
content = (
    'OPENAI_API_KEY=*** + os.environ.get('VENICE_API_KEY','') + '\n'
    'OPENROUTER_BASE_URL=https://api.maritime.sh/api/llm/v1\n'
    'HERMES_INFERENCE_MODEL=' + os.environ.get('NV_MODEL','xiaomi-mimo-v2-5') + '\n'
)
with open(os.environ['NV_FILE'], 'w') as f: f.write(content)
import os as _o; _o.chmod(_o.environ['NV_FILE'], 0o600)
"
"$PLATFORM" env import "$AGENT_NAME" "$ENV_FILE" --reload --json \
  | grep -E '"uploaded"|"failed"|"reloaded"' || true

# 6. Bounded deploy-with-backoff loop
attempt=0
while [ $attempt -lt "$MAX_ATTEMPTS" ]; do
  attempt=$((attempt+1))
  echo "[deploy-loop] deploy attempt $attempt/$MAX_ATTEMPTS"
  "$PLATFORM" deploy "$AGENT_NAME" --json 2>&1 \
    | grep -E '"status"|"id"' | head -2 || true
  sleep 10

  s=$("$PLATFORM" status "$AGENT_NAME" --json | python3 -c "
import sys,json
try:
    d=json.loads(sys.stdin.read())
    print(d.get('status','?') + (' lastErr=' + (d.get('lastError') or '')[:80] if d.get('lastError') else ''))
except: print('PARSE_ERR')
")
  echo "  status: $s"
  case "$s" in
    active*|running*|ready*)
      echo "[deploy-loop] READY \u2014 agent '$AGENT_NAME' is live"; break ;;
    error*|PARSE_ERR|"")
      echo "[deploy-loop] error; sleeping ${POLL_INTERVAL}s before retry"; sleep "$POLL_INTERVAL" ;;
    *)
      echo "[deploy-loop] indeterminate; waiting 15s for status to settle"; sleep 15 ;;
  esac
done

if [ $attempt -eq "$MAX_ATTEMPTS" ]; then
  echo "[deploy-loop] FAIL: $MAX_ATTEMPTS attempts exhausted"
  echo "[deploy-loop] latest error logs:"
  "$PLATFORM" logs "$AGENT_NAME" 2>&1 | tail -8 || true
  echo "[deploy-loop] if 500/409 repeats, the platform's VM provisioner is the bottleneck"
  echo "[deploy-loop] escalate to maintainer; do not loop further from this side"
  exit 1
fi

echo "[deploy-loop] done \u2014 agent '$AGENT_NAME' is live"
exit 0
