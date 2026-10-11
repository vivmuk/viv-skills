# Railway — PaaS recipe for personal AI agents

Proven deploy shape for running Hermes-style agents on
[railway.com](https://railway.com). The platform gives you
public HTTPS ingress, a managed container runtime, and a
persistent volume for `~/.hermes/` — no SSH, no docker compose,
no Cloudflare tunnel. The reward: an agent reachable from your
phone in <10 minutes once auth is solved.

This recipe is distilled from Tessa Kriesel's
"How I Deployed Hermes Agent on Railway with Telegram" (May 2026)
plus the specific auth quirks that bite headless / agent-run
deploys (`write_file` redaction of UUID-shaped values; Railway
CLI's `RAILWAY_TOKEN` env-var leak across tool calls).

## When this recipe fits

- Personal AI agent reachable 24/7 from Telegram or Discord
- One service, no multi-host orchestration
- $5–10/mo for the platform convenience is acceptable
- You do *not* need GPU / vLLM / local inference (use
  `serving-llms-vllm` instead for those workloads)

## When it doesn't fit

- Cost floor is $0 and you have access to free-tier cloud VMs
  (use the VM + Cloudflare Tunnel shape — see
  `references/oracle-always-free.md`)
- Multi-host fleet / kanban dispatch / shared state across
  regions (Railway's per-region volume model won't carry cross-region
  state — use Maritime.sh + `cloud-agent-provisioning`)

## Auth flow — the part that bites headless deploys

The Railway CLI's `login` has three modes, in order of preference:

1. **`railway login` (browser OAuth)** — opens your local
   browser, completes sign-in. Works ONLY when a human is at
   the machine, which is exactly when an AI agent is operating
   headless.

2. **`railway login --browserless` (device-code flow)** — prints
   a URL and an 8-char code; you open it on your phone, sign
   in, the CLI receives auth. **This is the canonical headless
   path.** Code validity is ~10 minutes; treat each invocation
   as fresh.

3. **Personal access tokens via `RAILWAY_TOKEN` /
   `RAILWAY_API_TOKEN`** — environment-variable support exists
   but has two caveats:
   * Persisted `RAILWAY_TOKEN` in any tool-call session leaks
     into subsequent shells. The CLI short-circuits with
     "Invalid RAILWAY_TOKEN. Please check that it is valid…"
     when both the env var is set AND the value triest to be
     used. Hard-`unset` before any auth operation:
     ```bash
     unset RAILWAY_TOKEN RAILWAY_API_TOKEN
     railway login --browserless
     ```
   * The Hermes tool layer's `write_file` redaction filter
     truncates UUID-shaped values paired with names like
     `RAILWAY_TOKEN` (first 5 chars + literal `...`, then `\n`).
     Tokens live in `~/.railway/sessions/<id>.session` after a
     successful `railway login`, NOT in a writable dotfile —
     device-code flow is the cleanest because there's nothing
     to write that would survive the redaction.

When you run a session through Hermes (this CLI), prefer option
2 every time. Bypass options 1 (you might not be at the machine)
and 3 (rediscover why the redaction + leak story above).

## Workdir structure

```
deploy-workdir/
├── Dockerfile              # tini as PID 1, python:3.13-slim
├── entrypoint.sh           # writes ~/.hermes/.env, copies config to BOTH names, exec gateway
├── railway.json            # builder=DOCKERFILE, no startCommand, restart=ON_FAILURE
├── .env.example            # placeholder keys + comments
└── hermes/
    ├── cli-config.yaml     # source-of-truth config (gateway and CLI both consume)
    └── SOUL.md             # agent identity
```

`Dockerfile`, `entrypoint.sh`, `railway.json`, `cli-config.yaml.example`,
`.env.example` — copy verbatim from `templates/railway/`. SOUL.md
is yours to author.

## Deploy sequence (verifiable)

### 1. Login (once per machine)

```bash
unset RAILWAY_TOKEN RAILWAY_API_TOKEN
railway login --browserless
# Output: https://railway.com/activate?user_code=ABC-12345
# Open on phone, sign in, code is consumed, CLI auth is established
```

Persistence: after success, `~/.railway/sessions/<id>.session`
holds the auth. No follow-up `RAILWAY_TOKEN` env work needed.

### 2. Project init

```bash
cd deploy-workdir
railway init           # creates project, prompts for workspace + name
railway service       # link to "main" service (or whatever you chose)
```

`railway init` is interactive on first run (workspace + name
pick). Subsequent invocations on an existing workdir are quick
re-associations.

### 3. Persistent volume (BEFORE first real deploy — gotcha #2)

```bash
railway volume add --mount-path /root/.hermes
```

**Critical**: the mount path is the *entire Hermes home*. Mounting
narrower paths like `/root/.hermes/memories` wipes everything
outside that path on every redeploy. Symptom of getting it wrong:
your bot comes back up and asks you to set the home channel,
because gateway state lives at the top level.

### 4. Environment variables

```bash
source ~/.config/railway/secrets.env   # your local secrets file (chmod 600)

railway variables set \
    VENICE_API_KEY="${VENICE_API_KEY}" \
    TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN}" \
    TELEGRAM_ALLOWED_USERS="6808691714" \
    TELEGRAM_HOME_CHANNEL="6808691714" \
    TELEGRAM_HOME_CHANNEL_NAME="Vivek M" \
    HERMES_HUMAN_DELAY_MODE="natural" \
    HERMES_ACCEPT_HOOKS="1"
```

`railway variables set` is idempotent — re-running updates the
value. For non-secret strings, it does NOT mark them secret; for
API keys / tokens, it does. To force non-secret marking on
strings (so they appear unmasked in `railway variables list`):
`railway variables set --no-secret KEY=VALUE`.

### 5. Initial deploy

```bash
railway up --detach
```

The `--detach` flag matters — without it, the CLI blocks on the
build log stream until the deploy finishes. With it, the CLI
returns once the build is queued and the deploy is rolling.

Cold build: 3–5 minutes (uv wheels cache miss). Warm rebuilds:
~45–90 seconds.

### 6. Smoke probe

```bash
sleep 90
railway logs --tail 100                # look for "Hermes Gateway Starting…"
SVC_URL=$(railway status --json | jq -r '.services[0].domains[0].domain')
curl -fsS "https://${SVC_URL}/health"  # 200 OK if gateway is up
```

Then send `/start` from Telegram to the bot. It should respond
within ~3 seconds. If it doesn't, check the logs for
`TELEGRAM_HOME_CHANNEL is not set` — the silent-bot gotcha.

## The 8 Tessa gotchas (condensed)

1. **`hermes gateway run`, not `start`.** Use `start` on a host
   service; in Docker, only `run` works (gotcha #11 in
   SKILL.md pitfalls).

2. **Volume at `/root/.hermes`, full home**, not a subdir.

3. **`mcp_servers:` not `mcp.servers:`.** Hermes silently drops
   the wrong key — you'll never see a tool-list error.

4. **Copy `cli-config.yaml` to BOTH `config.yaml` AND
   `cli-config.yaml`.** Different loaders, same content.

5. **`~/.hermes/.env`, not system env.** Rail-side `railway
   variables set` does not propagate into Hermes at runtime.
   The entrypoint shell-substitutes Railway env vars into
   `~/.hermes/.env` with `${VAR:-}` defaults.

6. **`TELEGRAM_HOME_CHANNEL` must be set.** Without it, the bot
   silently waits for setup. Set to your @userinfobot numeric
   user_id; same value as `TELEGRAM_ALLOWED_USERS` for personal
   DM.

7. **`tini` as PID 1.** Reaps zombie subprocesses (your MCP
   stdio servers will accumulate without it). Install in
   Dockerfile; `ENTRYPOINT ["/usr/bin/tini", "-g", "--",
   "/entrypoint.sh"]`. The `-g` flag forwards signals.

8. **Pre-install stdio MCP packages in Dockerfile.** `npx` cold-
   starts the download and can hang silently in Railway. Bake
   `RUN npm install -g @notionhq/notion-mcp-server` at build
   time; npx finds it locally.

## Provider override (Venice instead of default OpenAI)

Hermes config is OpenAI-compatible-endpoint agnostic. For
non-Anthropic providers, override the model block:

```yaml
# hermes/cli-config.yaml
model:
  default: minimax-m3                  # Venice's cheap 500k ctx model
  provider: custom
  base_url: https://api.venice.ai/api/v1
  api_key: ${OPENAI_API_KEY}            # injected from Railway env at entrypoint
  context_length: 500000
  max_output_tokens: 120000
```

Set `OPENAI_API_KEY` on Railway to your Venice key (which begins
with `VENICE_INFERENCE_KEY_…` — NOT a UUID, so `write_file`
redaction does not trigger). The entrypoint shells this into
`~/.hermes/.env`:

```bash
cat > "$HERMES_HOME/.env" << EOF
OPENAI_API_KEY=${OPENAI_API_KEY:-}
TAVILY_API_KEY=${TAVILY_API_KEY:-}
...
EOF
```

## Re-deploy runbook

```bash
cd deploy-workdir
git pull                      # if you wired auto-deploy via post-push hook
railway variables list        # verify env is unchanged
railway up --detach           # rebuild
sleep 90
railway logs --tail 100       # check for "Hermes Gateway Starting…"
curl -fsS https://<svc>.up.railway.app/health
```

Auto-redeploy on git push (Tessa's `post-push` hook trick):

```bash
cat > .git/hooks/post-push <<'EOF'
#!/bin/bash
echo "Deploying to Railway..."
cd "$(git rev-parse --show-toplevel)"
unset RAILWAY_TOKEN RAILWAY_API_TOKEN
railway up --detach
EOF
chmod +x .git/hooks/post-push
```

## Token rotation

When ANY secret leaks (chat history, public log, screenshot,
git push of `.env`, etc.), rotate immediately. Railway:

```bash
unset RAILWAY_TOKEN RAILWAY_API_TOKEN
railway login --browserless                       # fresh auth if your old token wasn't a personal access token
# if using a personal access token:
#   visit https://railway.com/account/tokens
#   + New Token → name it "deploy-<service>" → copy the new UUID
#   update your local ~/.config/railway/secrets.env (chmod 600)
#   railway variables set VENICE_API_KEY="<NEW>" --reload
```

For Telegram bot tokens leaked in chat: revoke via `@BotFather →
/revoke — and pick a new bot name. The deployed agent reads the
token at next `gateway` reload, no redeploy needed unless you
restart.

## When `railway up --detach` fails

The CLI returns non-zero with a JSON error. Common causes:

| Error | Fix |
|---|---|
| `Unauthorized` | Re-run `railway login --browserless` (env vars leaked — unset them first) |
| `Volume does not exist` | `railway volume add --mount-path /root/.hermes` |
| `Build failed: … tini not found` | Check Dockerfile has `apt-get install -y tini` |
| `startCommand override` | Remove `startCommand` from `railway.json` (gotcha #17) |
| `Exec format error` | `entrypoint.sh` lacks `#!/bin/bash` shebang OR missing `chmod +x` |

If the build itself fails, the deploy step never runs. Use
`railway logs --build` to see the Dockerfile output.

## Cost floor on Railway (2026 pricing snapshot)

| Plan | Monthly | Notes |
|---|---|---|
| Trial | $5 credit (one-time) | Enough for ~3 months of a personal Hermes at low traffic |
| Hobby | $5/mo + usage | $0.000463/GB-hour RAM + $0.20/GB egress |
| Pro | $20/mo + usage | For ≥2 services or consistent traffic |

Personal Hermes at idle (no chat traffic): ~$0.50/mo on
Hobby. With Telegram polling at 2-second cadence: ~$2–5/mo.
Egress is the variable cost — bots receive ZERO bytes from
Telegram until a user messages them.

## See also

- `templates/railway/` — scaffold files referenced above
- `scripts/railway-bootstrap.sh` — first-time project init +
  variable batch + deploy, idempotent
- Tessa Kriesel — "How I Deployed Hermes Agent on Railway with
  Telegram" — the canonical walkthrough this recipe is
  distilled from. Read it for the long-form prose; read this
  recipe for the operator-runnable steps.
