# Railway deploy — daily-driver runbook

For the full rationale (each gotcha, the redaction / leak story,
the auth flow), read `references/railway.md`. This file is the
operator's tabs-kept-open reference.

## First-time setup

```bash
# 0. Install Railway CLI globally
npm install -g @railway/cli

# 1. Copy this workdir to a real project
cp -R templates/railway/* ./my-agent/
cd ./my-agent
cp .env.example .env && chmod 600 .env
$EDITOR .env                       # paste Venice key + Telegram token

# 2. Auth (HEADLESS — works when you're not at the machine)
unset RAILWAY_TOKEN RAILWAY_API_TOKEN
railway login --browserless
# Open https://railway.com/activate?user_code=ABC-12345 on phone.
# Code is valid for ~10 min; if you miss it, rotate.

# 3. Decide your agent's name (used as Telegram @handle later)
AGENT=myagent
HERMES_HOME=/root/.hermes

# 4. Initialize Railway project
railway init
# Pick workspace + project name = "$AGENT"

# 5. Attach persistent volume (BEFORE first real deploy)
railway volume add --mount-path $HERMES_HOME

# 6. Push env vars from local .env
. ./.env
railway variables set \
    VENICE_API_KEY="$VENICE_API_KEY" \
    TELEGRAM_BOT_TOKEN="$TELEGRAM_BOT_TOKEN" \
    TELEGRAM_ALLOWED_USERS="$TELEGRAM_ALLOWED_USERS" \
    TELEGRAM_HOME_CHANNEL="$TELEGRAM_HOME_CHANNEL" \
    TELEGRAM_HOME_CHANNEL_NAME="$TELEGRAM_HOME_CHANNEL_NAME" \
    HERMES_HUMAN_DELAY_MODE="$HERMES_HUMAN_DELAY_MODE" \
    HERMES_ACCEPT_HOOKS="$HERMES_ACCEPT_HOOKS"

# 7. Initial deploy (background build)
railway up --detach
sleep 90

# 8. Verify
railway logs --tail 200
SVC=$(railway status --json | jq -r '.services[0].domains[0].domain')
curl -fsS "https://${SVC}/health"
# 200 OK expected

# 9. Telegram smoke
# In Telegram: send /start to @<AGENT>Aibot (or whatever you named it)
# It should respond within ~3 seconds
```

## Re-deploy

```bash
cd ./my-agent
unset RAILWAY_TOKEN RAILWAY_API_TOKEN
railway variables list            # confirm env unchanged
railway up --detach
sleep 90
railway logs --tail 100 | grep -E "Gateway Starting|error|ERROR"
curl -fsS "https://$(railway status --json | jq -r '.services[0].domains[0].domain')/health"
```

When your repo is on GitHub, wire `railway up --detach` to a
git post-push hook (no dashboard click required):

```bash
cat > .git/hooks/post-push <<'EOF'
#!/bin/bash
unset RAILWAY_TOKEN RAILWAY_API_TOKEN
cd "$(git rev-parse --show-toplevel)"
railway up --detach
EOF
chmod +x .git/hooks/post-push
```

## Rotate a leaked token

If a token ends up in chat / unredacted screenshot / pushed
`.env`:

```bash
# Telegram bot:
# 1. @BotFather → /revoke → pick old bot
# 2. /newbot → new bot → paste new token to .env
# 3. railway variables set TELEGRAM_BOT_TOKEN="${NEW_TOKEN}"
# No redeploy needed — Hermes hot-reloads env per session.

# Venice/OpenAI key:
# 1. Mint new key in your provider's dashboard
# 2. rail via .env → railway variables set
# 3. Optional: rotate the OLD key to invalidate it

# Railway token (if you used one):
# 1. Mint fresh at https://railway.com/account/tokens
# 2. Re-do `railway login --browserless` flow
# 3. Revoke the leaked token in the same dashboard
```

## Common failure modes (cross-reference: SKILL.md pitfalls #9–19)

| Symptom | Pitfall | Fix |
|---|---|---|
| `write_file` produces a 30-byte truncated token file | #9 | Use `railway login --browserless` (no file write) or non-redacted env-name placeholder |
| `railway login --browserless` exits with "Invalid RAILWAY_TOKEN" | #10 | Hard-`unset RAILWAY_TOKEN RAILWAY_API_TOKEN` before invoking |
| `Build failed: tini not found` | #16 | Ensure `RUN apt-get install -y tini` in Dockerfile |
| Bot is reachable but `/start` returns nothing | #6 | Set `TELEGRAM_HOME_CHANNEL` to your `@userinfobot` numeric user_id |
| Bot resets on every redeploy (asks to set home channel) | #12 | `railway volume add --mount-path /root/.hermes` (full path, not subdir) |
| `startCommand override` build error | #17 | Remove `startCommand` from `railway.json` |
| Gateway logs missing | — | `railway logs --tail 200` (or `--build` for build phase) |
| MCP servers silently unloaded | — | Check `mcp_servers:` not `mcp.servers:` (gotcha #3) AND secrets in `~/.hermes/.env` |

## Cost awareness

| Plan | Floor | Hard cap |
|---|---|---|
| Trial ($5 credit, one-time) | — | $5 |
| Hobby ($5/mo + usage) | ~$0.50/mo at idle | unbilled, soft-stop at $0 |
| Pro ($20/mo + usage) | ~$5/mo at light use | unbilled |

Egress is the dominant variable cost. Telegram bots receive zero
bytes from Telegram when idle. Heavy image-attachment workflows
or workflows that fetch external URLs on every message are
where egress grows.

## Safe-rotation checklist (when something went into chat)

If a token leaked in this chat, treat it as one of:

1. **Token already revoked** (you confirmed `railway whoami` failed
   before re-paste) — still complete the rotation pass below.
2. **Active token** (revocation still pending) — rotate within
   the next few minutes; the gap is exposure time.

Pass:
- [ ] Mint fresh token (Railway: account/tokens; Telegram:
      @BotFather → /newbot; Venice: provider dashboard)
- [ ] Push new value into Railway env via `railway variables set`
- [ ] Hot-reload: gateway uses new value on next session start
- [ ] Revoke the OLD token in the same dashboard
- [ ] Confirm `railway whoami` still works with the new value
- [ ] Save the new token to your local secrets file (chmod 600)
- [ ] Update the hand-off runbook with the rotation date
