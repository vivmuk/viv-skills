#!/bin/bash
# railway-bootstrap.sh — first-time Railway project init + deploy
#
# Run from the deploy workdir (the directory containing
# Dockerfile, entrypoint.sh, railway.json, .env, hermes/).
#
# Idempotent: safe to re-run after a cold start, token rotation,
# or partial failure. Each step that has already succeeded will
# no-op or update-in-place.
#
# Required state on the host:
#   - ~/.config/railway/<service>-secrets.env  (chmod 600)
#   - or env vars VENICE_API_KEY / TELEGRAM_BOT_TOKEN /
#     TELEGRAM_ALLOWED_USERS / TELEGRAM_HOME_CHANNEL present
#   - hermes/ directory populated per templates/railway/

set -euo pipefail

# Hard-unset any pre-existing Railway env vars to prevent the CLI
# from short-circuiting on a stale token (skill pitfall #10).
unset RAILWAY_TOKEN RAILWAY_API_TOKEN

# Auth — interactive if not already authenticated
if ! railway whoami --json >/dev/null 2>&1; then
    echo "→ Not authenticated. Running railway login --browserless..."
    echo "  Open the printed URL on your phone to complete sign-in."
    railway login --browserless
fi

# Validate the local secrets are reachable
: "${VENICE_API_KEY:?VENICE_API_KEY must be set locally before running this script}"
: "${TELEGRAM_BOT_TOKEN:?TELEGRAM_BOT_TOKEN must be set locally before running this script}"
: "${TELEGRAM_ALLOWED_USERS:?TELEGRAM_ALLOWED_USERS must be set locally before running this script}"
: "${TELEGRAM_HOME_CHANNEL:?TELEGRAM_HOME_CHANNEL must be set locally before running this script}"

# Idempotent project init (re-associates if already linked)
echo "→ Initializing Railway project..."
railway init --skip-deployment || true

# Persistent volume (skill pitfall #12 — full /root/.hermes mount)
echo "→ Attaching /root/.hermes volume..."
railway volume add --mount-path /root/.hermes 2>/dev/null || \
    echo "  (volume already attached; skipping)"

# Push secrets (use --skip-deploys so we set all vars before the
# first build, avoiding partial redeploys)
echo "→ Pushing env vars to Railway..."
railway variables set \
    VENICE_API_KEY="$VENICE_API_KEY" \
    TELEGRAM_BOT_TOKEN="$TELEGRAM_BOT_TOKEN" \
    TELEGRAM_ALLOWED_USERS="$TELEGRAM_ALLOWED_USERS" \
    TELEGRAM_HOME_CHANNEL="$TELEGRAM_HOME_CHANNEL" \
    ${TELEGRAM_HOME_CHANNEL_NAME:+TELEGRAM_HOME_CHANNEL_NAME="$TELEGRAM_HOME_CHANNEL_NAME"} \
    HERMES_HUMAN_DELAY_MODE="${HERMES_HUMAN_DELAY_MODE:-natural}" \
    HERMES_ACCEPT_HOOKS="${HERMES_ACCEPT_HOOKS:-1}"

# Initial deploy (background build)
echo "→ Deploying (railway up --detach)..."
railway up --detach

echo ""
echo "→ Waiting 90s for cold build + first boot..."
sleep 90

# Verify
SVC=$(railway status --json | jq -r '.services[0].domains[0].domain')
echo "→ Smoke probe https://${SVC}/health"
curl -fsS "https://${SVC}/health" && echo " ✓ gateway is up" || \
    echo " ✗ healthcheck failed; check 'railway logs --tail 200'"

echo ""
echo "→ Boot log tail:"
railway logs --tail 30

echo ""
echo "→ Next: send /start from Telegram to your bot."
