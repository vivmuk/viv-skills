# Secrets management — .env vs config.yaml, key rotation, failure modes

The discipline that keeps a personal-agent deploy from leaking keys
to a public repo.

## The split

| Surface | What lives there | Why |
|---|---|---|
| `config.yaml` | Behavioural settings: model defaults, fallback chain, telegram `allowed_chats` whitelist, logging level | Travels with the image — commit-safe |
| `.env` | Secrets: `LLM_API_KEY`, `TELEGRAM_BOT_TOKEN`, `DATABASE_URL`, `TUNNEL_CREDENTIALS_FILE` | `chmod 600`, never committed |

The runner idiom:

```yaml
# config.yaml
agent:
  bot_token: ${TELEGRAM_BOT_TOKEN}      # resolved from .env at start

# docker-compose.yml
services:
  agent:
    env_file: .env
```

Hermes Agent, Codex CLI, OpenClaw all read this split. Don't paste
secrets into YAML.

## .env template

```
# UID/GID for non-root remap inside the container.
AGENT_UID=1000
AGENT_GID=1000

# --- LLM provider (OpenAI-compatible) ---
LLM_BASE_URL=https://api.venice.ai...
LLM_API_KEY=***HERE
# Backup LLM
LLM_FALLBACK_BASE_URL=https://openrouter.ai...
LLM_FALLBACK_API_KEY=***HERE

# --- Telegram ---
TELEGRAM_BOT_TOKEN=***HERE
T...<chat_id_2>     # numeric IDs, comma-separated

# --- Managed Postgres (operational state) ---
DATABASE_URL=postgresql://...@...?...=require

# --- Cloudflare tunnel ---
TUNNEL_ID=...
T...>=
```

## Hard rules

- `chmod 600 .env` immediately after creating.
- Never paste `.env` into a chat message, screenshot, or commit.
- Never paste secrets into `config.yaml`.
- Use a **dedicated key per environment**. Running a local agent
  on key A and the cloud agent on the same key A means a
  runaway cloud session can lock you out locally.
- Use `:latest-free` model slugs only if you've tested the
  tool-use behaviour.

## Key rotation

1. Generate the new key in the provider's console.
2. SSH into the VM. Edit `.env` — substitute the new key for the
   old one. `chmod 600` (already set).
3. `docker compose restart agent` (no image rebuild needed).
4. Verify with `docker compose logs --tail=20 agent | grep -i auth`
   — should NOT show 401 anymore.

## Failure modes and what they look like in logs

| Symptom | Cause | Fix |
|---|---|---|
| `401 Unauthorized` from `agent_init` | Wrong LLM key | Rotate, restart |
| `tunnel ... connection refused :8642` | Agent not up yet / restart loop | `docker compose ps` to see health |
| `TELEGRAM_ALLOWED_CHATS ... not in list` | New chat ID, whitelist needs updating | Append to `TELEGRAM_ALLOWED_CHATS` in `.env` |
| `Error: P1001: Can't reach database server` | Postgres URL wrong or down | Verify `DATABASE_URL` ends with `?sslmode=require` |
| Agent keeps restarting every 30s | Healthcheck firing on a port not bound | Verify the agent's actual health port |

## Backup strategy

- `~/.hermes/<profile>/state.db` style memory files: include
  in a daily tar snapshot to a separate bucket.
- `cloudflared/credentials.json`: git-ignored, but back up.
  If you lose it, you must recreate the tunnel + DNS CNAME.
- `.env`: never back up to a public bucket. If you lose it,
  rotate each secret at the provider.
