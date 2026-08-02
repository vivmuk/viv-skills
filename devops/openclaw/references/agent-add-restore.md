# Restoring an OpenClaw Named Agent (Session Reference)

Real transcript from restoring the `kriya` agent on OpenClaw v2026.6.11 in WSL.

## What triggered this

`openclaw agents list` showed only `main`. The gateway was healthy, but Kriya was gone — likely lost during a v2026.6.x migration. No routing bindings existed.

## Commands that worked

```bash
# 1. Create the isolated agent
openclaw agents add kriya \
  --non-interactive \
  --workspace /home/vivgates/.openclaw/workspace-kriya \
  --agent-dir /home/vivgates/.openclaw/agents/kriya/agent \
  --model venice/zai-org-glm-5-2

# 2. Set display identity
openclaw agents set-identity --agent kriya --name "Kriya" --emoji "🪷"

# 3. Write workspace IDENTITY.md
cat > /home/vivgates/.openclaw/workspace-kriya/IDENTITY.md <<'EOF'
- **Name:** Kriya
- **Creature:** AI assistant
- **Vibe:** calm, capable, direct
- **Emoji:** 🪷
EOF

# 4. Bind to Telegram
openclaw agents bind --agent kriya --bind telegram

# 5. Restart gateway (required for agent/bindings to load)
systemctl --user restart openclaw-gateway.service

# 6. Verify
openclaw agents list --json
openclaw agents bindings --json
curl -s http://localhost:18789/health
```

## Non-interactive TUI test

When testing a message through the gateway, use the token from `openclaw.json`:

```bash
TOKEN=$(grep -oP '"token":\s*"\K[^"]+' ~/.openclaw/openclaw.json)
timeout 30 openclaw tui \
  --url ws://localhost:18789 \
  --session kriya-test \
  --message "ping" \
  --deliver \
  --token "$TOKEN"
```

Note: the TUI connected to `agent main` in this test because the `--agent` flag is not supported on `openclaw tui`; routing to `kriya` is determined by channel bindings at the gateway layer.

## What did NOT work

- `openclaw config set plugins.X.enabled true --agent kriya` — `--agent` is not a valid flag for `openclaw config set`. Plugin enablement is global in `openclaw.json` or handled per-extension.
- Guessing the gateway token — it lives in `~/.openclaw/openclaw.json` under `gateway.auth.token`.
- Hot-reloading agent additions — a full gateway restart was required.

## Verification checklist

| Check | Command | Expected |
|-------|---------|----------|
| Gateway running | `curl -s http://localhost:18789/health` | `{"ok":true,"status":"live"}` |
| Agent exists | `openclaw agents list --json` | `id: "kriya"` |
| Binding present | `openclaw agents bindings --json` | `agentId: "kriya", match.channel: "telegram"` |
| Identity set | `cat ~/.openclaw/workspace-kriya/IDENTITY.md` | Name / emoji defined |

## Follow-up work if Kriya will make model calls

Auth is per-agent in v2026.6.x+. After creating a new agent, re-register the provider key:

```bash
openclaw models auth paste-api-key --provider venice
# paste the key when prompted
```

Run the skill's `scripts/verify-kriya-auth.sh` (or equivalent) to confirm model calls succeed before relying on the agent in production.

## Side notes

- Doctor warnings about `discord` plugin metadata conflict are harmless leftovers from a state migration; they did not block Telegram routing.
- The empty `~/.openclaw/agents/kriya/agent/` directory after creation is normal until the agent handles its first session.
