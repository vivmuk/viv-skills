#!/usr/bin/env bash
# ZeroClaw → Venice deployment chain, observed 2026-07-08.
#
# What this does, top to bottom:
#   1. Source an env-loader that exposes $MARITIME_TOKEN, $VENICE_INFERENCE_KEY.
#      NEVER types the keys; refs come from chmod-600 files.
#   2. Sanity-check: $MARITIME_TOKEN and $VENICE_INFERENCE_KEY are non-empty.
#   3. maritime list to confirm auth and that we want to create <name>.
#   4. maritime create -n <name> -t zeroclaw --tier <tier>. Tier default: smart.
#   5. Wire Venice's openai-compatible endpoint + key onto the agent:
#        - OPENAI_BASE_URL=https://api.venice.ai/api/v1   (plain)
#        - OPENAI_API_KEY = $VENICE_INFERENCE_KEY           (secret)
#        - VENICE_INFERENCE_KEY = $VENICE_INFERENCE_KEY     (secret, for
#          application code that reads the literal env name)
#      All using --reload so the running container picks up without restart.
#   6. maritime info + env list to verify the wiring post-reload.
#
# Defaults:
#   name = my-agent        AGENT_NAME env var
#   tier = smart           AGENT_TIER env var
#
# Pre-flight (require once before this script will run):
#   - ~/.config/maritime/token              (chmod 600 — the maritime mk_… key)
#   - ~/.config/maritime/venice-key         (chmod 600 — the Venice inference key)
#   - ~/.config/maritime/maritime-env.sh     (the env-loader, mode 0600)
#
# Steps 1-2 are echoed; every secret-bearing line references a variable, never
# the literal. argv is clean of keys — every secret stays in $VAR.

set -euo pipefail

NAME="${AGENT_NAME:-my-agent}"
TIER="${AGENT_TIER:-smart}"
MARITIME_TOKEN_FILE="${MARITIME_TOKEN_FILE:-$HOME/.config/maritime/token}"
VENICE_KEY_FILE="${VENICE_KEY_FILE:-$HOME/.config/maritime/venice-key}"
ENV_LOADER="${ENV_LOADER:-$HOME/.config/maritime/maritime-env.sh}"

[ -r "$ENV_LOADER" ]    || { echo "missing env loader: $ENV_LOADER" >&2; exit 2; }
[ -s "$MARITIME_TOKEN_FILE" ] || { echo "empty or missing: $MARITIME_TOKEN_FILE" >&2; exit 2; }
[ -s "$VENICE_KEY_FILE" ]     || { echo "empty or missing: $VENICE_KEY_FILE"   >&2; exit 2; }

# shellcheck disable=SC1090
. "$ENV_LOADER"

: "${MARITIME_TOKEN:?MARITIME_TOKEN was not exported by $ENV_LOADER}"
VENICE_INFERENCE_KEY="$(< "$VENICE_KEY_FILE")"
export VENICE_INFERENCE_KEY

printf 'MARITIME_TOKEN=%d chars  VENICE_INFERENCE_KEY=%d chars\n' \
  "${#MARITIME_TOKEN}" "${#VENICE_INFERENCE_KEY}"

echo
echo "=== 1. confirm auth ==="
maritime list --json | jq '[.[] | {name, framework, tier, status}]'

# Idempotent: if the agent already exists with the right config, skip create.
if maritime info "$NAME" --json 2>/dev/null | jq -e \
  ".framework == \"zeroclaw\" and .tier == \"$TIER\"" >/dev/null; then
  echo
  echo "=== 2. agent $NAME already exists with framework=zeroclaw tier=$TIER; skipping create ==="
else
  echo
  echo "=== 2. create $NAME  framework=zeroclaw  tier=$TIER ==="
  maritime create -n "$NAME" -t zeroclaw --tier "$TIER" --json | jq '{name,id,framework,tier,status}'
fi

echo
echo "=== 3. wire Venice (OPENAI_BASE_URL + OPENAI_API_KEY + VENICE_INFERENCE_KEY, all --reload) ==="
# OPENAI_BASE_URL is plain text (visible in env list), --no-secret is required
# so it doesn't get masked.
maritime env set "$NAME" \
  OPENAI_BASE_URL=https://api.venice.ai/api/v1 \
  --no-secret --reload --json | jq '.uploaded,.reloaded'

# OPENAI_API_KEY and VENICE_INFERENCE_KEY are secrets; default behavior
# (secret+encrypted) is what we want, no --no-secret.
maritime env set "$NAME" \
  OPENAI_API_KEY="$VENICE_INFERENCE_KEY" \
  VENICE_INFERENCE_KEY="$VENICE_INFERENCE_KEY" \
  --reload --json | jq '.uploaded,.reloaded'

echo
echo "=== 4. verify ==="
maritime env list "$NAME" --json | jq '[.[] | {key, isSecret}]'
echo
maritime info "$NAME" --json | jq '{name, framework, tier, status, lastActiveAt}'

echo
echo "Done. Next: maritime chat $NAME 'Hi'  --json    (smoke test)"
echo "      or: maritime open $NAME                   (ZeroClaw native dashboard)"
