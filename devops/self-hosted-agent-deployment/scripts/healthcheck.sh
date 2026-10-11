#!/usr/bin/env bash
#
# End-to-end agent health probe.
#
# Verifies (in order):
#   1. Compose stack status.
#   2. In-container /health on the agent's HTTP port.
#   3. Public probe via the Cloudflare tunnel.
#   4. Recent agent + tunnel container logs.
#
# Usage:    bash scripts/healthcheck.sh
#
# Override defaults with env:
#   AGENT_PORT=8642   HEALTHCHECK_PATH=/health  ./scripts/healthcheck.sh

set -euo pipefail

AGENT_NAME="${AGENT_NAME:-agent}"
SERVICE="${SERVICE:-$AGENT_NAME}"
HEALTHCHECK_PORT="${HEALTHCHECK_PORT:-8642}"
HEALTHCHECK_PATH="${HEALTHCHECK_PATH:-/health}"
HOSTNAME="${TUNNEL_HOSTNAME:-${CLOUDFLARE_TUNNEL_HOSTNAME:-}}"

CYAN=$'\033[36m'; GREEN=$'\033[32m'; RED=$'\033[31m'; NC=$'\033[0m'
log_ok()   { printf '%s✓%s %s\n' "${GREEN}" "${NC}" "$1"; }
log_fail() { printf '%s✗%s %s\n' "${RED}"   "${NC}" "$1"; exit 1; }
log()      { printf '%s>%s %s\n' "${CYAN}"  "${NC}" "$1"; }

# 1. Compose stack status
log "Compose stack status"
docker compose ps

# 2. In-container local probe
log "In-container /health (port ${HEALTHCHECK_PORT})"
if docker compose exec -T "${SERVICE}" \
     curl -fsS "http://127.0.0.1:${HEALTHCHECK_PORT}${HEALTHCHECK_PATH}" >/dev/null
then
  log_ok "local /health 200"
else
  log_fail "local /health did NOT 200 (check ${SERVICE} container logs)"
fi

# 3. Public probe via tunnel (only if hostname set)
if [ -n "${HOSTNAME}" ]; then
  log "Public probe via Cloudflare Tunnel: https://${HOSTNAME}${HEALTHCHECK_PATH}"
  if curl -fsS --max-time 10 "https://${HOSTNAME}${HEALTHCHECK_PATH}" >/dev/null
  then
    log_ok "https://${HOSTNAME}${HEALTHCHECK_PATH} 200"
  else
    log_fail "https://${HOSTNAME}${HEALTHCHECK_PATH} failed (check tunnel container logs)"
  fi
else
  log "Skipping public probe (TUNNEL_HOSTNAME not set)"
fi

# 4. Recent container logs
log "Recent ${SERVICE} container log lines (last 40)"
docker compose logs --tail=40 "${SERVICE}" | sed 's/^/  /'

if docker compose ps --services | grep -q "^tunnel$"; then
  log "Recent tunnel container log lines (last 20)"
  docker compose logs --tail=20 tunnel | sed 's/^/  /'
fi

log_ok "healthcheck complete"
