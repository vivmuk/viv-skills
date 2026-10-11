#!/usr/bin/env bash
#
# Read-only diagnostic for "my agent is down, what broke?".
#
# Walks through the obvious failure modes for a self-hosted agent
# deploy built from this skill's templates. Each step prints WHY
# it's checking and what the healthy answer looks like. Exits 0
# if all clear, non-zero on the first failure.
#
# Usage:    bash scripts/diagnose.sh

set -uo pipefail

CYAN=$'\033[36m'; GREEN=$'\033[32m'; RED=$'\033[31m'; NC=$'\033[0m'
ok()   { printf '%s✓%s  %s\n' "${GREEN}" "${NC}" "$1"; }
warn() { printf '%s!%s  %s\n' "${CYAN}"  "${NC}" "$1"; }
bad()  { printf '%s✗%s  %s\n' "${RED}"   "${NC}" "$1"; return 1; }

# --- Step 1: Docker is up ----------------------------------------------------
printf '\n== 1. Docker daemon ==\n'
if ! command -v docker >/dev/null 2>&1; then
  bad "docker not installed"; exit 1
fi
if docker info >/dev/null 2>&1; then
  ok "docker daemon responding"
else
  bad "docker daemon not responding"; exit 1
fi

# --- Step 2: Compose file exists --------------------------------------------
printf '\n== 2. compose file ==\n'
if [ ! -f docker-compose.yml ]; then
  bad "docker-compose.yml not in $(pwd)"; exit 1
fi
ok "compose file present"

docker compose config >/dev/null 2>&1 \
  && ok "compose file parses" \
  || { bad "compose file has syntax errors (run 'docker compose config')"; exit 1; }

# --- Step 3: Required env vars ----------------------------------------------
printf '\n== 3. .env surface ==\n'
[ -f .env ] || { bad ".env not in $(pwd)"; exit 1; }
ok ".env file present"

# Sanity-check file mode (warn, don't fail, if too open)
mode=$(stat -c %a .env 2>/dev/null || stat -f %Lp .env 2>/dev/null)
case "${mode}" in
  600|400) ok ".env perms ${mode} (correct)" ;;
  *)       warn ".env perms ${mode} (prefer 600: chmod 600 .env)" ;;
esac

# Check required keys present (and not placeholder)
required_keys=(LLM_API_KEY TELEG_CRED_FILE_PATH TELEGRAM_BOT_TOKEN TUNNEL_ID)
for key in "${required_keys[@]}"; do
  if grep -qE "^${key}=(YOUR_|REPLACE_|.*\.\.\.)" .env 2>/dev/null; then
    bad ".env contains placeholder for ${key}"
  elif ! grep -qE "^${key}=" .env 2>/dev/null; then
    bad ".env missing ${key}"
  else
    ok ".env has ${key}"
  fi
done

# --- Step 4: Agent container running and healthy -----------------------------
printf '\n== 4. agent container ==\n'
agent_state=$(docker compose ps --format json agent 2>/dev/null \
             | python3 -c "import json,sys;d=json.load(sys.stdin);print(d.get('Health',''))" 2>/dev/null || echo "")
case "${agent_state}" in
  healthy) ok "agent container healthy" ;;
  starting) warn "agent container starting (give it 90s)" ;;
  unhealthy) bad "agent container unhealthy — docker compose logs agent" ; exit 1 ;;
  "")       bad "agent container not running" ; exit 1 ;;
  *)        warn "agent container state: ${agent_state}" ;;
esac

# --- Step 5: Tunnel running and connected ------------------------------------
printf '\n== 5. tunnel container ==\n'
if ! docker compose ps --services 2>/dev/null | grep -q "^tunnel$"; then
  warn "no tunnel service in compose — skipping"
else
  tunnel_state=$(docker compose ps --format json tunnel 2>/dev/null \
                 | python3 -c "import json,sys;d=json.load(sys.stdin);print(d.get('State',''))" 2>/dev/null || echo "")
  case "${tunnel_state}" in
    running) ok "tunnel container running" ;;
    *)       bad "tunnel container state: ${tunnel_state}"; exit 1 ;;
  esac

  recent=$(docker compose logs --tail=100 tunnel 2>/dev/null | grep -ciE "registered tunnel conn" || true)
  if [ "${recent}" -gt 0 ]; then
    ok "tunnel registered HA connections (${recent} log lines)"
  else
    bad "no 'Registered tunnel connection' in last 100 tunnel log lines"
  fi
fi

# --- Step 6: public hostname resolves ----------------------------------------
printf '\n== 6. public hostname ==\n'
hostname="${TUNNEL_HOSTNAME:-${CLOUDFLARE_TUNNEL_HOSTNAME:-}}"
[ -n "${hostname}" ] || { warn "TUNNEL_HOSTNAME empty; skipping public probe"; hostname=""; }
if [ -n "${hostname}" ]; then
  cname=$(dig +short "${hostname}" 2>/dev/null | head -1)
  if echo "${cname}" | grep -qE "cfargotunnel\.com$"; then
    ok "${hostname} → ${cname}"
  else
    bad "${hostname} resolves to '${cname}', not a cfargotunnel.com CNAME"
    exit 1
  fi
  if curl -fsS --max-time 10 "https://${hostname}/health" >/dev/null 2>&1; then
    ok "https://${hostname}/health 200"
  else
    bad "https://${hostname}/health not 200"; exit 1
  fi
fi

printf '\n=== diagnose complete: agent stack looks healthy ===\n'
