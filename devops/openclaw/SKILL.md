---
name: openclaw
version: 5
description: "Manage AI agent platforms — OpenClaw (agent gateway, Telegram, cron) and Paperclip (agent company control plane). Install, configure, migrate (Windows↔WSL), gateway lifecycle, plugins, cron jobs, and status."
triggers:
  - openclaw
  - migrating openclaw
  - openclaw gateway
  - openclaw cron
  - openclaw plugins
  - paperclip
  - paperclip gateway
  - paperclip dev server
  - agent control plane
  - agent platforms
---

# OpenClaw Management

OpenClaw is an AI agent platform that runs as a local gateway and connects to channels (Telegram, etc.) via plugins.

## Quick Reference

| Command | Purpose |
|---------|---------|
| `openclaw gateway --port 18789` | Start the gateway (default port 18789) |
| `openclaw status` | Full system overview (plugins, channels, agents, cron) |
| `openclaw status --deep` | Deep probe including connectivity checks |
| `openclaw plugins list` | List all discovered plugins (stock + global) |
| `openclaw plugins install <spec>` | Install a plugin |
| `openclaw plugins doctor` | Check plugin load issues |
| `openclaw doctor --fix` | Auto-repair config issues |
| `openclaw logs` | View recent gateway logs (no `--lines` flag — pipe to `tail`) |
| `openclaw logs --follow` | Live (streaming) gateway logs |
| `openclaw --version` | Installed OpenClaw version (compare to `npm view openclaw version`) |

## Installation (WSL)

```bash
npm install -g openclaw
# Binary lands at ~/.hermes/node/bin/openclaw (if installed via hermes node)
# Or global npm bin
```

Config directory: `~/.openclaw/`

Key files and directories:
```
~/.openclaw/
├── openclaw.json          # Main config (model, plugins, workspace path)
├── auth-profiles.json     # Auth credentials per provider
├── exec-approvals.json    # Tool approval state + socket path
├── credentials/           # Stored credentials
├── identity/              # Device auth (device.json, device-auth.json)
├── agents/                # Agent configs and session data
├── memory/                # Persistent memory files
├── cron/
│   ├── jobs.json          # Cron job definitions (schedule, payload, delivery)
│   └── jobs-state.json    # Run state (last run, errors, next run)
├── extensions/            # Global plugins (with node_modules)
├── workspace/             # Working directory (git repo, package.json)
├── plugins/               # Plugin registry (installs.json)
├── telegram/              # Telegram session data
├── browser/               # Chromium profile data
├── flows/                  # TaskFlow definitions
├── tasks/                  # Task definitions
├── media/                  # Generated media files
└── logs/                   # Gateway and stability logs
```

## Migrating Windows → WSL

**⚠️ Do NOT bulk-copy the entire `.openclaw` directory** — Windows `node_modules` are x86/PE binaries and the copy is very slow due to `node_modules` in `extensions/` and `workspace/`. Use selective copy instead.

### Step-by-step migration

1. **Copy config and data files** (fast, small):
   ```bash
   mkdir -p ~/.openclaw
   for f in openclaw.json auth-profiles.json exec-approvals.json update-check.json; do
     cp /mnt/c/Users/<winuser>/.openclaw/$f ~/.openclaw/
   done
   ```

2. **Copy subdirectories** (skip `node_modules`):
   ```bash
   for dir in agents credentials identity memory flows tasks cron telegram canvas completions media delivery-queue; do
     cp -r /mnt/c/Users/<winuser>/.openclaw/$dir ~/.openclaw/$dir
   done
   ```

3. **Copy extensions** selectively — each extension needs its source but NOT its `node_modules`:
   ```bash
   mkdir -p ~/.openclaw/extensions/email
   for f in openclaw.plugin.json package.json package-lock.json README.md; do
     cp /mnt/c/Users/<winuser>/.openclaw/extensions/email/$f ~/.openclaw/extensions/email/
   done
   cp -r /mnt/c/Users/<winuser>/.openclaw/extensions/email/src ~/.openclaw/extensions/email/
   cp -r /mnt/c/Users/<winuser>/.openclaw/extensions/email/skills ~/.openclaw/extensions/email/skills
   cp -r /mnt/c/Users/<winuser>/.openclaw/extensions/email/dist ~/.openclaw/extensions/email/dist
   cd ~/.openclaw/extensions/email && npm install
   ```

4. **Copy workspace** (skip `node_modules`, they'll be rebuilt):
   ```bash
   rsync -a --exclude='node_modules' /mnt/c/Users/<winuser>/.openclaw/workspace/ ~/.openclaw/workspace/
   cd ~/.openclaw/workspace && npm install
   ```

5. **Fix Linux paths** in config files:
   - `openclaw.json`: Change `workspace` from `C:\Users\vivek\.openclaw\workspace` to `/home/<wsluser>/.openclaw/workspace`
   - `exec-approvals.json`: Change socket `path` from `C:\Users\...\.openclaw\exec-approvals.sock` to `/home/<wsluser>/.openclaw/exec-approvals.sock`

6. **Fix workspace `.secrets/`** — env files may have Windows paths; review and update.

7. **Start the gateway**:
   ```bash
   openclaw gateway --port 18789
   # Verify
   curl -s http://localhost:18789/health
   openclaw status
   ```

### Pitfalls

- **Missing `openclaw.plugin.json`**: Each extension directory must have this manifest file. If gateway fails with "plugin manifest not found", copy it from the Windows install.
- **Slow copy**: `rsync` over `/mnt/c/` with `node_modules` can take 10+ minutes. Always exclude `node_modules` and run `npm install` instead.
- **Path format**: Windows paths use backslashes and `C:\Users\...`; WSL uses `/home/<user>/...`. The gateway will crash on Windows paths in WSL config.
- **Binary node_modules**: Windows `.dll` and `.exe` in `node_modules` won't work on Linux. Always `npm install` fresh.

## Cron Jobs

OpenClaw has a built-in cron scheduler — **no system crontab needed**. Jobs are defined in `~/.openclaw/cron/jobs.json`.

```json
{
  "version": 1,
  "jobs": [
    {
      "id": "uuid",
      "agentId": "main",
      "name": "Job Name",
      "description": "What it does",
      "enabled": true,
      "schedule": { "kind": "cron", "expr": "0 18 * * *", "tz": "America/New_York" },
      "sessionTarget": "isolated",
      "wakeMode": "now",
      "payload": {
        "kind": "agentTurn",
        "message": "Your prompt here...",
        "model": "venice/kimi-k2-5",
        "thinking": "on",
        "timeoutSeconds": 600
      },
      "delivery": { "mode": "announce", "to": "<telegram-user-id>", "channel": "telegram" }
    }
  ]
}
```

Run state (last run time, errors, next run) is tracked in `jobs-state.json`. Migrating this file preserves job history.

### Cron Job Prompt Anti-Patterns

**⚠️ NEVER rely on Venice X Search alone for factual news.** X Search returns social media chatter which LLMs embellish into plausible-sounding but fabricated stories with fake URLs and timestamps. This produces "old news" or hallucinated news.

**Best practices for news/research cron prompts:**
1. **Require web_search + web_fetch verification** — every claimed story must be fetched and confirmed from the real source URL
2. **Add anti-hallucination rules** — "3 verified stories > 10 fabricated ones", "never fabricate URLs"
3. **Include today's date** in the prompt so the agent knows what "past 24 hours" means
4. **Use a reasoning model** — the user forbids Claude models on cron jobs and tasks; use `venice/grok-4-20` or `venice/kimi-k2-5` with `thinking: "on"` for factual prompts (the old recommendation of `claude-sonnet-4-6` is retired by user preference)
5. **Set generous timeouts** — 600s+ for research-heavy prompts that do multiple web fetches
6. **Quality > quantity** — explicitly tell the agent to report fewer stories rather than pad with unverified ones

See `references/cron-prompt-patterns.md` for a working news-research prompt template.

## Plugin Management

- **Stock plugins**: bundled with OpenClaw at `<npm-global>/lib/node_modules/openclaw/dist/extensions/`
- **Global (user) plugins**: at `~/.openclaw/extensions/<name>/`
- Enable: `openclaw plugins enable <id>`
- Disable: `openclaw plugins disable <id>`
- The `email` plugin requires SMTP config in `openclaw.json` under `plugins.entries.email.config`

## Gateway

- Default port: 18789 (localhost only)
- Health: `GET /health` → `{"ok":true,"status":"live"}`
- Dashboard: `http://127.0.0.1:18789/`
- Run in background: `openclaw gateway --port 18789 &` or via systemd

## Sending Tasks to the Agent

The `openclaw agent` command sends a single turn to the agent:

```bash
# Send a message to the main agent (returns the response)
openclaw agent --message "Your prompt here" --agent main

# Deliver the response to a channel (e.g., Telegram)
openclaw agent --message "Read /home/user/prd.md and build it" --agent main --deliver

# Specify model
openclaw agent --message "Quick summary" --agent main --model venice/llama-3.3-70b

# Send to a specific session
openclaw agent --message "Follow up" --agent main --session-id abc123
```

**Pitfalls:**
- **Scope approval error**: If agent requests more scopes than currently approved, you'll get `scope upgrade pending approval` and it falls back to embedded mode. Fix by running `openclaw configure` and approving the requested scopes.
- **Skills path**: The agent looks for skills in `~/.openclaw/workspace/skills/`, NOT `~/.hermes/skills/`. If skills are missing, check the path.
- **Timeout**: Agent turns can take 2-5+ minutes for complex tasks. Don't set short timeouts.

## Bulk-Copying Directories from Windows (WSL Performance)

Copying from `/mnt/c/` is VERY slow, especially directories with many small files or `node_modules`. Strategies:

1. **Selective copy** (fastest): Copy only config/data files, skip `node_modules`, then `npm install` fresh:
   ```bash
   rsync -a --exclude='node_modules' /mnt/c/Users/<user>/.openclaw/ ~/.openclaw/
   cd ~/.openclaw/extensions/email && npm install
   cd ~/.openclaw/workspace && npm install
   ```
   Even this can timeout on large repos. If rsync times out, copy file-by-file or directory-by-directory:
   ```bash
   cp /mnt/c/Users/<user>/.openclaw/openclaw.json ~/.openclaw/
   for dir in agents credentials identity memory; do
     cp -r "/mnt/c/Users/<user>/.openclaw/$dir" ~/.openclaw/
   done
   ```
2. **Install npm packages fresh** rather than copying `node_modules/` — Windows `.dll`/`.exe` binaries won't work on Linux anyway.

## WSL2 Memory & OOM

OpenClaw's Node.js gateway can consume ~2.5 GB of RAM. In WSL2 environments running multiple Node.js processes (Hermes, Paperclip, VoiceAI, etc.), the Linux OOM killer may terminate the gateway. Symptoms: gateway dies silently, `curl localhost:18789/health` returns connection refused, stability logs show `gateway.startup_failed`.

**Check if OOM-killed:**
```bash
dmesg | grep -i "oom\|killed process"
# Look for: "Out of memory: Killed process <pid> (node)"
```

**Mitigations:**
- Add a `.wslconfig` file on Windows (`%USERPROFILE%\.wslconfig`) to increase WSL2 memory:
  ```ini
  [wsl2]
  memory=8GB
  ```
- Set up a systemd service for auto-restart (see below).
- Monitor with `free -h` before launching additional Node.js processes.

## Systemd Auto-Restart (Optional)

To have the gateway auto-restart on crash or reboot:

```bash
cat > /etc/systemd/system/openclaw.service << 'EOF'
[Unit]
Description=OpenClaw Gateway
After=network.target

[Service]
Type=simple
User=vivgates
ExecStart=/home/vivgates/.nvm/versions/node/v24.15.0/bin/node /home/vivgates/.hermes/node/lib/node_modules/openclaw/dist/index.js gateway --port 18789
Restart=always
RestartSec=5
Environment=HOME=/home/vivgates

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now openclaw
```

**⚠️ Node runtime version matters.** OpenClaw v2026.6.11 requires Node ≥ v22.22.3 or v24.x. The bundled Hermes Node at `~/.hermes/node/bin/node` may be too old (e.g., v22.22.2). Point `ExecStart` to a Node v24 binary such as `~/.nvm/versions/node/v24.15.0/bin/node`. If the gateway exits immediately with an unsupported-runtime error, update the Node path in the service file, run `systemctl --user daemon-reload`, and restart.

**User-level service path:** On this machine the gateway is managed as a user service at `~/.config/systemd/user/openclaw-gateway.service`. Edit that file instead of `/etc/systemd/system/openclaw.service` when running as the user unit.

## Sharp Module Fix (Image Attachments)

The `media-understanding-core` stock extension uses `sharp` for image processing (resizing, optimizing attachments). On some installs, the dynamic `import("sharp")` fails with `Cannot find package 'sharp'`, breaking any action that attaches images — Telegram messages with images, email with inline images, etc.

**Symptom:** `Failed to optimize image: Optional dependency sharp is required for image attachment processing | Cannot find package 'sharp' imported from .../media-understanding-core/image-ops.js`

**Root cause:** The extension's `node_modules/` directory is misstructured — it contains sharp's own package files directly instead of a proper `node_modules/sharp/` resolution path.

**Fix:**

```bash
OPENCLAW_DIR=~/.hermes/node/lib/node_modules/openclaw
MEDIA_EXT=$OPENCLAW_DIR/dist/extensions/media-understanding-core

# Ensure sharp is installed in openclaw's dependencies
cd "$OPENCLAW_DIR" && npm install sharp@0.34.5

# Remove the broken node_modules directory (contains sharp's own files, not resolution)
rm -rf "$MEDIA_EXT/node_modules"

# Create proper resolution structure with symlinks
mkdir -p "$MEDIA_EXT/node_modules"
ln -s "$OPENCLAW_DIR/node_modules/sharp" "$MEDIA_EXT/node_modules/sharp"
ln -s "$OPENCLAW_DIR/node_modules/@img" "$MEDIA_EXT/node_modules/@img"

# Verify
cd "$MEDIA_EXT" && node --input-type=module -e "import('sharp').then(m => console.log('sharp OK')).catch(e => console.log('FAIL:', e.message))"
```

**⚠️ Must re-apply after every `npm install` or `openclaw update`** — npm wipes and recreates `node_modules`, destroying the symlinks. Add this as a post-update step.

### Auto-Update Breaking Dist Files

OpenClaw's gateway auto-updater sometimes applies an update that leaves missing `.js` dist files, causing `ERR_MODULE_NOT_FOUND` on startup:

```
Error [ERR_MODULE_NOT_FOUND]: Cannot find module '.../dist/server-chat-BGxc5alj.js'
```

**Fix:** Full reinstall + sharp re-apply:
```bash
~/.hermes/node/bin/npm install -g openclaw@latest
# Then re-apply the sharp module fix (see above)
```

The auto-update log line looks like: `[gateway] auto-update applied` — if you see this followed by a crash, assume dist files are broken.

### Post-Upgrade Auth Migration (v2026.6.x+)

Starting in OpenClaw v2026.6.x, auth storage moved from `~/.openclaw/auth-profiles.json` into a **per-agent SQLite database** at `~/.openclaw/agents/main/agent/openclaw-agent.sqlite`. The migration does NOT auto-import keys from `auth-profiles.json` — even if a valid key exists on disk, the agent may not have a key in its new store.

However, the gateway **still reads `~/.openclaw/auth-profiles.json`** as a fallback/shared auth source. In practice you may find:
- `openclaw models auth list` shows no profiles (per-agent store empty)
- But `~/.openclaw/auth-profiles.json` still contains the only valid key
- Updating `auth-profiles.json` and restarting the gateway fixes auth failures

This dual-storage state is common after upgrades/migrations. Treat `auth-profiles.json` as the source of truth until you confirm the per-agent store is populated and working.

**Symptom 1** (Kriya returns this when she tries to respond):

```
FailoverError: Couldn't sign in to venice. Your saved login looks expired
or no longer works. Run `openclaw models auth login --provider venice`
or `openclaw configure`.
(No API key found for provider "venice". Auth store:
~/.openclaw/agents/main/agent/openclaw-agent.sqlite ...)
```

**Symptom 2** (cron/heartbeat spam, every 30 minutes):

The bot sends repeated warnings like:

```
⚠️ Heartbeat check failed before it could produce an update. The main chat session remains available.
```

or cron failure alerts like:

```
⚠️ Cron job "..." failed: FallbackSummaryError: All models failed (4):
  venice/zai-org-glm-5-2: 401 "Authentication failed" (auth)
  venice/kimi-k2-5: 401 "Authentication failed" (auth)
  venice/qwen3-5-35b-a3b: 401 "Authentication failed" (auth)
  venice/minimax-m25: 401 "Authentication failed" (auth)
```

All four fallbacks failing with `401 Authentication failed` means the gateway has **no valid provider key at all**, not that one model is bad. Check `auth-profiles.json` first.

**Quick diagnosis:**

```bash
# 1. Check the legacy/shared auth store
cat ~/.openclaw/auth-profiles.json | python3 -m json.tool

# 2. Check the per-agent auth store
~/.hermes/node/bin/openclaw models auth list

# 3. Compare against the key in openclaw.json / Hermes config
grep -oP 'VENICE_INFERENCE_KEY_[A-Za-z0-9_-]+' ~/.openclaw/openclaw.json ~/.hermes/config.yaml ~/.openclaw/auth-profiles.json | sort -u
```

If the keys differ, `auth-profiles.json` is stale.

**Fix — update the legacy auth profile and restart:**

```bash
# Use the known-good key from openclaw.json or Hermes config
NEW_KEY=$(grep -oP 'VENICE_INFERENCE_KEY_[A-Za-z0-9_-]+' ~/.openclaw/openclaw.json | head -1)
python3 - <<'PY'
import json, os
p = os.path.expanduser('~/.openclaw/auth-profiles.json')
with open(p) as f: d = json.load(f)
d.setdefault('profiles',{})['venice:default'] = {
    'type': 'api_key', 'provider': 'venice', 'key': os.environ['NEW_KEY']
}
with open(p,'w') as f: json.dump(d, f, indent=2)
print('updated auth-profiles.json')
PY

# Restart the gateway so it loads the corrected profile
systemctl --user restart openclaw-gateway.service
sleep 5 && curl -s http://localhost:18789/health
```

**Alternative — re-register into the per-agent SQLite store (non-interactive):**

```bash
# Use the existing key from auth-profiles.json (or a fresh one)
KEY=$(grep -oP '"key":\s*"\K[^"]+' ~/.openclaw/auth-profiles.json)
echo "$KEY" | openclaw models auth paste-api-key --provider venice
```

Output confirms: `Auth profile: venice:manual (venice/api_key)`.

**Verify:**

```bash
openclaw models auth list
# Should show: venice:manual [venice/api_key]

# Smoke test (will print "scope upgrade pending approval" + use embedded fallback,
# but logs should show the model returning a response):
openclaw agent --message "Reply with exactly: pong" --agent main
~/.hermes/node/bin/openclaw logs 2>&1 | tail -50 | grep -i "pong\|auth profile\|agent model"
```

The gateway picks up the new profile on the next request — no restart needed (hot-reload works for `auth.profiles.*` changes). You may see `warn ... config change requires gateway restart (auth.profiles.venice:manual)` in logs, but in practice the next request uses the new profile successfully.

**Rule of thumb:** when you see all Venice models failing with `401 Authentication failed`, the problem is a stale or missing key — not model health. Update `auth-profiles.json` first, then re-register via `openclaw models auth paste-api-key` if needed, then restart the gateway.

**Add to every post-upgrade checklist** alongside the sharp symlink re-apply. Both break in the same `npm install` cycle and both are silent until the next model call.

**Automated verification** — a one-shot smoke test that checks the gateway, registered profiles, and round-trips a real model call is bundled at `scripts/verify-kriya-auth.sh`. Run it after any OpenClaw upgrade or auth re-registration to confirm Kriya is healthy before sending real traffic.

**Workaround for email attachments:** When the email plugin can't send images, use a Python SMTP helper directly:
```bash
python3 ~/workspace/kriya_email.py --to vivek@live.de --subject "Title" --html report.html --attach image.png
```
The script is also stored in the skill at `scripts/kriya_email.py` — copy it to `~/.openclaw/workspace/` to use it. It reads SMTP config from env vars (`OPENCLAW_SMTP_*`) or uses hardcoded Gmail defaults.
Text-only emails via the `email_send` tool work fine — only image attachments are affected.

## Post-Update State Migrations (Doctor Auto-Migrates on First Boot)

Starting around v2026.6.x, OpenClaw's `openclaw doctor` runs **automatic state migrations** on first boot after a major version bump. These are NORMAL and do not indicate a problem. The pattern is: legacy sidecar JSON / SQLite files → shared SQLite store, with the originals archived as `*.migrated` siblings.

**Expected migrations after a 2026.5.x → 2026.6.x upgrade:**
- `cron/jobs.json` cron store → SQLite (legacy run logs imported)
- `plugin-state/*.json` sidecars → shared `state.sqlite` (107+ entries typical)
- `tasks/runs.sqlite` task registry → shared SQLite
- `flows/registry.sqlite` task flows → shared SQLite
- Telegram update offset + sent-message cache + dispatch dedupe → plugin state
- `memory/.dreams/short-term-recall.json` → Memory Core SQLite (23 rows typical)

**How to recognize them:** Doctor output shows `◇ Doctor changes ─` followed by bullet points like:
```
- Cron store migrated to SQLite at ~/.openclaw/cron/jobs.json.
- Migrated 107 plugin-state sidecar entries → shared SQLite state
- Archived plugin-state sidecar legacy source → .../state.sqlite.migrated
```

**Cleanup after a successful update:**
```bash
# List archived legacy sources — safe to delete once you've verified nothing is broken
find ~/.openclaw -name "*.migrated" -mtime +7 -ls
```

**Known migration warning:** `Left plugin install index in place because shared SQLite state has conflicting plugin install metadata for: discord` — this is presented as a warning, but the gateway treats it as a **fatal startup error** and refuses to report ready. Do not ignore it.

**Fix via CLI (preferred):**
```bash
~/.hermes/node/bin/openclaw plugins disable discord
# Restart the gateway so the config change is validated
systemctl --user restart openclaw-gateway.service
```

**Fix via SQLite (when CLI/Doctor cannot finish the migration):**
If the gateway is stuck in a loop (migration lease still held, or Doctor itself fails because of the conflict), disable the plugin in `~/.openclaw/openclaw.json` first, then remove its metadata directly from the shared state database and clear the migration lock:

```bash
python3 - <<'PY'
import sqlite3, os, json
db = os.path.expanduser('~/.openclaw/state/openclaw.sqlite')
conn = sqlite3.connect(db)
cur = conn.cursor()
res = cur.execute("SELECT install_records_json, plugins_json FROM installed_plugin_index WHERE index_key='installed-plugin-index'")
row = res.fetchone()
install_records = json.loads(row[0])
plugins = json.loads(row[1])
install_records.pop('discord', None)
plugins = [p for p in plugins if p.get('pluginId') != 'discord']
cur.execute(
    "UPDATE installed_plugin_index SET install_records_json=?, plugins_json=? WHERE index_key='installed-plugin-index'",
    (json.dumps(install_records), json.dumps(plugins))
)
cur.execute("DELETE FROM state_leases WHERE scope='startup-migrations' AND lease_key='global'")
conn.commit()
print('discord metadata removed and migration lock cleared')
PY
systemctl --user restart openclaw-gateway.service
sleep 5 && curl -s http://localhost:18789/health
```

**Root cause:** The plugin install index (`installed_plugin_index` table) and the runtime config disagree about whether `discord` is installed/enabled. OpenClaw's startup migration refuses to proceed while that conflict exists. Re-installing Discord later is safe if needed; just make sure both the config and the SQLite index agree.

**Pitfall:** If you restore OpenClaw state from a backup taken BEFORE a major version bump, run `openclaw doctor` afterward to re-trigger migrations on the restored files. Don't run the new binary against unmigrated legacy files and assume everything is fine.

## Systemd Service Description Pitfall

The systemd user unit at `~/.config/systemd/user/openclaw-gateway.service` ships with a hardcoded version in `Description=OpenClaw Gateway (vYYYY.M.D)`. This goes stale immediately on the first update and makes `systemctl --user status` output misleading. **Don't hardcode the version** — just use `Description=OpenClaw Gateway` and check the actual version with `openclaw --version` when you need it. After editing, run `systemctl --user daemon-reload`.

## Security Permissions

`openclaw doctor --fix` or manual audit may flag these. Fix immediately:

```bash
chmod 600 ~/.openclaw/openclaw.json     # Config has API keys — must be owner-only
chmod 700 ~/.openclaw/credentials/       # Credential directory — must be owner-only
chmod 600 ~/.openclaw/credentials/*.json  # Individual credential files
```

## Web Fetch Limitations

Many popular sites block OpenClaw's `web_fetch` with 403 (Cloudflare/bot protection). Known blocked sites:
- **mckinsey.com** — 403
- **healthitanalytics.com** — 403
- **nejm.org** — 403
- **fda.gov** — 404 (moved URLs)

Sites that **do work** well with `web_fetch` for news research:
- **theverge.com** — works
- **techcrunch.com** — works
- **arstechnica.com** — works
- **wired.com** — works
- **the-decoder.com** — works
- **techstartups.com** — works
- **openai.com** (blog posts) — works
- **ibm.com** — works

**Workaround for blocked sites:** Use Venice X Search (via chat with `enable_x_search: true` in venice_parameters) or alternative sources for research from those domains. However, **never rely on X Search alone for factual claims** — always verify with web_fetch from a primary source.

## Current User Setup

- OpenClaw v2026.6.8 installed in WSL (via hermes node, updated 2026-06-19 from v2026.5.28)
- Auth migrated to per-agent SQLite: `~/.openclaw/agents/main/agent/openclaw-agent.sqlite` (re-register after upgrade via `openclaw models auth paste-api-key --provider venice`)
- Config at `~/.openclaw/` (migrated from Windows)
- Default model: `venice/zai-org-glm-5-2` (fallbacks: kimi-k2-5, qwen3-5-35b-a3b, minimax-m25)
- Enabled plugins: telegram, venice, email, memory-core (openrouter and other bundled providers are disabled — see "Removing a Provider Fallback" below)
- Agent identity: `agentId: "main"`, sender display name `"Kriya Viv's AI Bot"`. **User colloquially calls this agent "Drishti"** — do NOT confuse with the separate `vivgatesAI/Drishti` GitHub repo (a different web app deployed at drishti.up.railway.app). When the user says "drishti" in the OpenClaw context, they mean this agent, not that repo.
- Cron jobs: Daily AI News Summary (6PM EDT, model: grok-4-20, web_search+web_fetch verified — previously used claude-sonnet-4-6 but user forbids Claude models), MindShift Reminder (9PM EDT)
- Telegram connected (user ID 6808691714)
- Email: vivgatesai@gmail.com via Gmail SMTP (app password), default to vivek@live.de

## Model Configuration

The primary model and fallback chain are configured in `~/.openclaw/openclaw.json` under `agents.defaults.model`:

```json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "venice/zai-org-glm-5-2",
        "fallbacks": ["venice/kimi-k2-5", "venice/qwen3-5-35b-a3b", "venice/minimax-m25"]
      },
      "models": {
        "venice/kimi-k2-5": { "alias": "Kimi K2.5" },
        "venice/zai-org-glm-5-2": {},
        "venice/qwen3-5-35b-a3b": {},
        "venice/minimax-m3": {},
        "venice/minimax-m25": {},
        "venice/grok-4-20-beta": {}
      }
    }
  }
}
```

### Changing the Default Model — 3 Places to Update

When changing the primary model, you must update ALL THREE locations in `openclaw.json`:

1. **`agents.defaults.model.primary`** — The default model used for all agent turns
2. **`agents.defaults.models`** — Add an entry for the new model (even just `{}`) so it appears in the agent's available models
3. **`models.providers.venice.models[]`** — Add a full model definition with `id`, `name`, `api`, `reasoning`, `input`, `cost`, `contextWindow`, `maxTokens`, `compat`

Missing any of these causes inconsistent behavior (agent can't use the model, or model appears misconfigured).

### Removing a Provider Fallback (e.g. "drop openrouter")

A provider plugin can leave residue in **three** places — removing it cleanly means scrubbing all three and then restarting the gateway. The `openclaw plugins disable` CLI alone is NOT sufficient because it only updates the runtime registry; it does not strip auth credentials or the parallel `openclaw.json` entry.

**Three places a provider can be referenced:**

| Location | What to remove |
|---|---|
| `~/.openclaw/openclaw.json` | `plugins.entries.<provider>` block (e.g. `"openrouter": { "enabled": false }`) AND any `models.providers.<provider>` definition |
| `~/.openclaw/plugins/installs.json` | The plugin's `"enabled": false` field — set by `openclaw plugins disable` |
| `~/.openclaw/agents/main/agent/openclaw-agent.sqlite` | Any `auth_profile_store` row keyed to that provider (use `openclaw models auth list` to inspect; v2026.6.x+ auth lives here, not in `auth-profiles.json`) |

**Procedure:**

```bash
# 1. Inspect current state before changing anything
grep -ni "<provider>" ~/.openclaw/openclaw.json
~/.hermes/node/bin/openclaw plugins list | grep -i "<provider>"
~/.hermes/node/bin/openclaw models auth list | grep -i "<provider>"

# 2. Disable the plugin (updates installs.json runtime registry)
~/.hermes/node/bin/openclaw plugins disable <provider>

# 3. Verify openclaw.json has the parallel entry set to enabled:false
#    If plugins.entries.<provider> still says enabled:true, edit by hand.
grep -A2 "\"<provider>\"" ~/.openclaw/openclaw.json | grep enabled

# 4. Restart the gateway (plugin changes need full restart, NOT hot reload)
systemctl --user restart openclaw-gateway.service
sleep 5 && curl -s http://localhost:18789/health
# → {"ok":true,"status":"live"}

# 5. Verify the provider is no longer loaded
~/.hermes/node/bin/openclaw status
~/.hermes/node/bin/openclaw models auth list
# Should NOT list the disabled provider anywhere
```

**Pitfalls:**
- **Don't trust `openclaw.json` alone**: the file may show `plugins.entries.openrouter.enabled: false` while `installs.json` still has `"enabled": true`. Both must agree before the gateway actually drops the provider. Run the CLI to be safe.
- **Auth profiles persist after disable**: even with the plugin off, leftover API keys in the SQLite auth store may show in `openclaw models auth list`. This is harmless but messy — clear them if you want a clean slate.
- **Hot reload won't pick it up**: the `config hot reload applied (plugins.entries.<provider>)` log line confirms the config-level change but the gateway still needs a full restart to actually unload the provider module.

### Changing a Named Agent's Model

Each named agent (e.g., `kriya`) has its own `model` field in `openclaw.json` under `agents.list[]`. To change it:

```bash
python3 -c "
import json
with open('/home/vivgates/.openclaw/openclaw.json') as f:
    config = json.load(f)
for agent in config['agents']['list']:
    if agent.get('id') == 'kriya':
        agent['model'] = 'venice/minimax-m3-preview'
        break
# Also add to the models list so it appears as available
models_list = config['agents']['defaults'].get('models', {})
if 'venice/minimax-m3-preview' not in models_list:
    models_list['venice/minimax-m3-preview'] = {}
with open('/home/vivgates/.openclaw/openclaw.json', 'w') as f:
    json.dump(config, f, indent=2)
print('Done')
"
```

**Two places to update for a named agent:**
1. `agents.list[].model` — the agent's primary model
2. `agents.defaults.models` — add an entry (even just `{}`) so the model appears in the agent's available models list

Unlike the default model change (which requires 3 places), named agent model changes only need these 2 — the `models.providers.venice.models[]` catalog is for discovery, not per-agent assignment.

The gateway hot-reloads `openclaw.json` changes, so no restart is needed. The agent will use the new model on its next turn.

### Verifying Venice Model Availability (Don't Trust Local Catalog)

The OpenClaw model catalog at `~/.openclaw/agents/<name>/agent/plugins/venice/catalog.json` can be **stale** — it's generated once and doesn't auto-refresh. A model may exist on Venice but not appear in the local catalog.

**Always verify model availability by querying the Venice API directly:**

```bash
curl -s --max-time 15 "https://api.venice.ai/api/v1/models" \
  -H "Authorization: Bearer $(grep -oP 'VENICE_INFERENCE_KEY_[A-Za-z0-9_-]+' ~/.openclaw/openclaw.json | head -1)" | \
  python3 -c "import json,sys; d=json.load(sys.stdin); [print(m['id']) for m in d.get('data',[])]" | \
  grep <model-name>
```

If the model appears in the API response, it's available — even if the local `catalog.json` doesn't list it. The user may know about new models before the catalog is regenerated.

### Check OpenClaw Version vs Latest

Quick two-command check the user sometimes asks for ("is it up to date?"):

```bash
~/.hermes/node/bin/openclaw --version    # installed
~/.hermes/node/bin/npm view openclaw version  # latest stable on registry
# Ignore *-beta.* versions unless user asks for pre-release channel.
```

**Upgrading:**

1. If the installed version is already the latest stable, `npm install -g openclaw@latest` will still refresh dependencies but usually **does not** break the auth store or the sharp symlinks. You can skip the post-upgrade re-auth and sharp re-apply unless a symptom appears.
2. If the version actually changes (e.g., `2026.6.10` → `2026.6.11`), then run the full post-upgrade checklist:
   - `~/.hermes/node/bin/npm install -g openclaw@latest`
   - Re-apply the sharp module fix (image attachments may otherwise fail silently)
   - Re-register the Venice API key in the per-agent SQLite store (v2026.6.x+ auth migration does not auto-import old keys)

See "Post-Upgrade Auth Migration" and "Sharp Module Fix" sections below for the full procedures.

**Verification before doing extra work:** after `npm install`, compare `openclaw --version` output to `npm view openclaw version`. If they match, the only required step is usually `systemctl --user restart openclaw-gateway.service` and a health check.

**Additional post-startup checklist when the gateway fails to become live:**
1. `curl -s http://127.0.0.1:18789/health` — must return `{"ok":true,"status":"live"}`
2. Check the end of the gateway log: `~/.hermes/node/bin/openclaw logs 2>&1 | tail -30`
3. Look for two common startup killers:
   - `OpenClaw startup migrations did not complete cleanly` → run `openclaw doctor --fix`, or manually clear conflicting plugin metadata (see "Post-Update State Migrations" above)
   - `OpenClaw startup migrations are already running for this state directory` → another process holds the migration lease, or a previous crash left it stale. Wait for the lease timeout, or clear the `startup-migrations` row from `state_leases` in `~/.openclaw/state/openclaw.sqlite` (only when no gateway is running)
4. `openclaw status` should show the gateway state, loaded plugins, and configured agents

## Diagnosing Stalled Startup Migrations

OpenClaw **hot-reloads config changes** automatically — the gateway watches `openclaw.json` and applies changes without restart. Logs show:

```
[reload] config change detected; evaluating reload (agents.defaults.model.primary)
[reload] config hot reload applied (agents.defaults.model.primary)
```

A full restart (`systemctl --user restart openclaw-gateway.service`) is only needed for:
- Plugin changes (enable/disable/install)
- Major structural changes (auth profiles, workspace path)
- If hot-reload fails or behaves inconsistently

```bash
# Full restart via systemd
systemctl --user restart openclaw-gateway.service
# Verify (give it 5+ seconds — health check fails immediately after restart)
sleep 5 && curl -s http://localhost:18789/health
```

**⚠️ Don't manually start the gateway when systemd is managing it.** If you `kill` the process, systemd respawns it. If you try `openclaw gateway --port 18789` in the background, it will fail with "gateway already running; lock timeout" because the systemd-managed instance already holds the port. Always use `systemctl --user` commands instead.

### `jobs.json` Also Hot-Reloads

Editing `~/.openclaw/cron/jobs.json` (add/remove/change a job) does NOT require a gateway restart. The scheduler picks up changed schedules on the next tick. From the OpenClaw docs at `~/.hermes/node/lib/node_modules/openclaw/docs/automation/cron-jobs.md` line 121:

> If `jobs.json` is edited externally, the Gateway reloads changed schedules and clears stale pending slots; formatting-only rewrites do not clear the pending slot. Malformed job rows are removed from active `jobs.json` at load time after their raw contents are copied to `jobs-quarantine.json`.

**Always back up `jobs.json` before manual edits**: `cp jobs.json jobs.json.bak.<TS>`. If a row gets quarantined, the gateway writes the raw original to `jobs-quarantine.json` next to `jobs.json` — check there for repair.

### Backing Up OpenClaw Config (For Cross-Machine or Shared-Brain Handoff)

When handing off OpenClaw config to the shared AI Agents brain, only these are portable (the rest is live runtime and will corrupt if copied mid-write):

| Portable | Skip (live runtime) |
|---|---|
| `openclaw.json` — **must be redacted** (see below) | `logs/`, `tasks/`, `memory/main.sqlite*` |
| `plugins/installs.json` | `delivery-queue/`, `plugin-state/` |
| `cron/jobs.json` (no secrets, but review prompt text) | `telegram/`, `qqbot/`, `workspace/`, `browser/` |
| `extensions/*/skills/*/SKILL.md` | all `*.sqlite-tmp-*` / `*.sqlite-wal` / `*.sqlite-shm` |
| `~/.openclaw/auth-profiles.json` (SKIP — has secrets) | `~/.openclaw/credentials/` (SKIP) |

**Redaction patterns for `openclaw.json`** — a naive lowercase-only redaction misses:
- Uppercase env-var keys: `VENICE_API_KEY`, `OPENAI_API_KEY`, `TELEGRAM_BOT_TOKEN`
- All `env` dicts (every env-var-style field is sensitive by convention)
- Nested MCP server credentials: `mcp.servers.<name>.env.<KEY>`

Use suffix matching (`_KEY`, `_TOKEN`, `_SECRET`, `_PASSWORD`), whole-`env`-dict redaction, and a value-shape heuristic (32+ char base62, or `VENICE_INFERENCE_KEY_*` pattern). See `note-taking/ai-agents-handoff/references/first-time-full-backup.md` for the working redaction function and skip rules.

## Cron Job Model Selection

When creating cron prompts that require **factual accuracy** (news, research, data), model choice is critical. **The user forbids all Claude models (`claude-sonnet-4-6`, etc.) for cron jobs and tasks.** Use non-Claude alternatives only.

| Model | Hallucination Risk | Use For |
|-------|-------------------|---------|
| `venice/kimi-k2-5` | **Low** | Factual research, news, verified claims |
| `venice/grok-4-20` | **Low–Medium** | General tasks, cron jobs (user permits; previously `claude-sonnet-4-6` was listed here but user forbids Claude models) |
| `venice/grok-4-20-beta` | **High** | Creative tasks, brainstorming — NOT factual claims |
| `venice/qwen3-235b-a22b-instruct-2507` | Medium | General tasks, code analysis |

**Why grok-4-20-beta hallucinates news:** When given X Search data (social media trending topics), it fabricates plausible-sounding details: fake URLs, wrong dates, invented announcements. It treats trending hashtags as real news. Always pair with `web_search` + `web_fetch` verification if using grok for any factual task.

For the full anti-hallucination cron prompt pattern, see `references/cron-prompt-patterns.md`.

### `openclaw agent` Command — Scope Approval

The `openclaw agent` CLI command can fail with a "scope upgrade pending approval" error when the agent requests more tool scopes than currently approved. This often happens when using `--model` to specify a different model than the default, or when delivering to channels.

**Symptoms:**
```
gateway connect failed: GatewayClientRequestError: scope upgrade pending approval
EMBEDDED FALLBACK: Gateway agent failed; GatewayTransportError: gateway closed (1008): pairing required
```

**Fix:** Run `openclaw configure` and approve the requested scopes. Or run the agent without `--model`/`--deliver` flags (use the default model and manual delivery instead).

**Workaround:** Cron jobs with `delivery.mode: "announce"` don't hit this issue — they deliver through the gateway's own channel, not through agent-initiated sends.

## Adding or Restoring a Named Agent

A named agent (e.g., `kriya`) can disappear during OpenClaw upgrades or migrations. If `openclaw agents list` shows only `main`, the named agent is gone and must be recreated.

### Quick check

```bash
openclaw agents list
openclaw agents bindings
```

If the agent is missing or has no routing bindings, recreate it.

### Create the agent

```bash
openclaw agents add kriya \
  --non-interactive \
  --workspace /home/vivgates/.openclaw/workspace-kriya \
  --agent-dir /home/vivgates/.openclaw/agents/kriya/agent \
  --model venice/zai-org-glm-5-2
```

### Set identity

```bash
openclaw agents set-identity --agent kriya --name "Kriya" --emoji "🪷"
```

Write a minimal `IDENTITY.md` to the new workspace so the agent knows who it is:

```bash
cat > /home/vivgates/.openclaw/workspace-kriya/IDENTITY.md <<'EOF'
- **Name:** Kriya
- **Creature:** AI assistant
- **Vibe:** calm, capable, direct
- **Emoji:** 🪷
EOF
```

### Bind to channels

```bash
openclaw agents bind --agent kriya --bind telegram
openclaw agents bindings
```

### Restart the gateway

Plugin/agent changes require a full gateway restart; hot-reload is not enough:

```bash
systemctl --user restart openclaw-gateway.service
sleep 3
curl -s http://localhost:18789/health
```

### Verify

```bash
openclaw agents list --json
openclaw agents bindings --json
```

You should see `kriya` with the workspace, identity, and at least one binding.

### Pitfalls

- **`--agent-dir` may be created empty.** The CLI reports `agentDir` in the JSON output, but the directory may not be populated until the agent is first used. This is normal.
- **Identity changes need a restart.** `set-identity` updates the shared config, but the gateway loads identity at startup. Restart after setting identity.
- **Named agent not default?** `main` remains the default unless you rebind default routing or configure channel-specific routing. A Telegram binding tells the gateway to route Telegram messages to `kriya`.
- **Auth does not migrate to the new agent.** v2026.6.x+ stores auth per agent. After creating `kriya`, re-register provider keys with `openclaw models auth paste-api-key --provider venice` scoped to the new agent if it will make model calls directly. If it only needs the same keys as `main`, verify with a test message.

### Checking whether a named agent exists

`openclaw agents list` only shows configured agents. If a user asks whether a named agent (e.g., "Kriya") is present:

```bash
openclaw agents list
```

If the named agent is not in the list, **it is not currently configured**, even if the gateway is running and healthy. In this session, `openclaw agents list` showed only `main (default)` and no routing bindings; Kriya did not exist as a separate agent. Either re-add the agent with `openclaw agents add` (see "Adding or Restoring a Named Agent" above) or treat `main` as the active agent if the user previously used that nickname.

**Do not assume an agent exists just because the gateway is running.** Always verify with `openclaw agents list` and, if needed, `openclaw agents bindings`.

**Session reference:** `references/agent-add-restore.md` has the exact command transcript used to recreate `kriya`.

## Diagnosing Delivery & Cron Issues

When an agent says "trouble sending a report" or a cron job seems stuck:

1. **Check cron job state**: `cat ~/.openclaw/cron/jobs-state.json | python3 -m json.tool`
   - `lastRunStatus: "ok"` and `lastDeliveryStatus: "delivered"` → job ran fine
   - `consecutiveErrors > 0` → repeated failures, check `lastError`
2. **Check delivery queue failures**: `ls -la ~/.openclaw/delivery-queue/failed/`
   - Failed deliveries accumulate here with details
3. **Check gateway logs for model errors**:
   ```bash
   ~/.hermes/node/bin/openclaw logs 2>&1 | grep -i "error\|timeout\|fail\|429"
   ```
4. **Common failure patterns in logs**:
   - `FailoverError: LLM request timed out` → primary model overloaded, fell back to fallback
   - `reasoning-only assistant turn detected — retrying` → model returned only thinking, no visible output
   - `telegram sendChatAction failed: 429 Too Many Requests` → rate-limited by Telegram; wait and retry
   - `web_fetch failed (403)` → target site blocked the request (Cloudflare, etc.)
5. **Model fallback chain**: When the primary model times out, OpenClaw falls back through configured fallbacks. Check `agents/main/agent/auth-profiles.json` and `openclaw.json` for fallback configuration. The session view in `openclaw status` shows which model each session is actually using.
6. **Check `openclaw status --deep`** for security audit warnings and probe results.

### Cron job fails with HTTP 404: model: <name>

**Symptom**: Cron job fails with `RuntimeError: HTTP 404: model: claude-sonnet-4` (or similar provider/model error).

**Root cause**: The model ID stored in the cron job config is stale. Providers rename or retire model IDs over time. In this case the job was configured with `model: claude-sonnet-4` and `provider: anthropic`, but Venice now exposes `claude-sonnet-4-6` and `claude-sonnet-4-5`, and no Anthropic API key was configured in Hermes.

**Applies to**: Both Hermes cron jobs (`~/.hermes/cron/jobs.json`) and OpenClaw cron jobs (`~/.openclaw/cron/jobs.json`).

**Diagnosis**:
1. Read the failing job config and note the exact `model` and `provider` values.
2. Query the provider's model list for current IDs:
   ```bash
   # Venice example using key from ~/.hermes/config.yaml
   curl -s https://api.venice.ai/api/v1/models \
     -H "Authorization: Bearer $(grep -oP 'VENICE_API_KEY:\s*\K.*' ~/.hermes/config.yaml | head -1)" | \
     python3 -c "import json,sys; d=json.load(sys.stdin); [print(m['id']) for m in d.get('data',[])]"
   ```
3. Confirm the provider has a working API key in the relevant config/env.

**Fix**:
- Update the job's `model` field to the current provider-specific ID (e.g., `claude-sonnet-4-6`).
- Set `provider` to the provider that actually has auth configured (e.g., `venice`).
- For Hermes cron jobs, edit `~/.hermes/cron/jobs.json`; the scheduler hot-reloads changes.
- For OpenClaw cron jobs, edit `~/.openclaw/cron/jobs.json`.

**Verification**:
- Hermes: `hermes cron run <job_id>`
- OpenClaw: `openclaw cron run <job_id>` (or wait for the next scheduled tick)
- Confirm `last_status` changes from `error` to `ok` and that the request dump no longer hits a 404.

### Cron Job Hallucination (X Search Problem)

**Symptom**: Cron job delivers plausible-sounding but fabricated news stories with fake URLs, wrong timestamps, or hallucinated details.

**Root cause**: The default X Search capability (Venice `enable_x_search: true`) returns social media posts that sound authoritative but are not verified. Models like `grok-4-20-beta` will fabricate plausible stories by inferring from trends rather than fetching real sources. The model fills in gaps with invented headlines, fake URLs, and fabricated publication dates.

**Fix**: For any cron job that requires factual accuracy (news, research, summaries):
1. Switch the model to `venice/kimi-k2-5` (lowest hallucination risk) or `venice/grok-4-20` with `thinking: on` — **do NOT use Claude models** (`claude-sonnet-4-6` was previously recommended here but the user forbids Claude for cron jobs)
2. Rewrite the prompt to require `web_search` + `web_fetch` verification — every claim must be backed by a visited, confirmed URL
3. Add anti-hallucination rules: "3 verified stories > 10 fabricated ones", "NEVER fabricate URLs"
4. Include the current date in the prompt dynamically so the model knows what "past 24 hours" means
5. Increase `timeoutSeconds` to 600 (verification takes time)

**Example prompt pattern for factual research cron jobs**:
```
You are a news curator. ONLY include stories where you SUCCESSFULLY FETCHED AND READ the source URL.
NEVER fabricate URLs or timestamps.
If you find fewer stories than requested, that is FINE — report only what you verified.
Today's date is: [injected date]
Use web_search to find stories, then web_fetch to VERIFY each one.
```

## Paperclip — Removed

Paperclip (AI agent company control plane) was previously installed alongside OpenClaw but has been **removed from this machine** (deleted 2026-05-23). The `~/paperclip` directory and `~/.paperclip` data directory no longer exist. If Paperclip needs to be reinstalled, the fork was `HenkDz/paperclip` branch `feat/externalize-hermes-adapter`.

**Note:** The `references/fork-agents-md.md` file still exists in this skill's references directory for historical reference.

## Multi-Machine Networking

Connecting Hermes and OpenClaw agents across multiple home computers (e.g., 2 PCs + 1 Mac). See `references/multi-machine-networking.md` for the full setup guide covering:

- **Tailscale mesh VPN** — stable cross-machine networking with zero config
- **Hermes MCP server/client** — expose each Hermes instance's tools to other machines via `hermes mcp serve` + `hermes mcp add`
- **OpenClaw gateway as hub** — centralize one machine as the agent hub
- **Shared messaging channels** — simplest option: all agents in the same Telegram/Discord group

## Pitfalls

### Cron/Heartbeat Auth Failure Spam

If the bot starts sending repeated `⚠️ Heartbeat check failed before it could produce an update.` messages (often every 30 minutes) or cron failure alerts with `FallbackSummaryError: All models failed (4): ... 401 "Authentication failed"`, the gateway has lost its Venice API key.

**Likely causes:**
- `~/.openclaw/auth-profiles.json` still holds the old key after a rotation
- The per-agent SQLite auth store is empty after a v2026.6.x+ upgrade

**Fix:** See the "Post-Upgrade Auth Migration (v2026.6.x+)" section for the diagnostic and fix. Session reference: `references/auth-401-heartbeat-spam-fix-2026-07-19.md`.

### Multi-Agent Auth Sync (v2026.7.x+)

After a key rotation or migration, each agent may end up with a different auth state:

| Store | Scope | Typical state after rotation |
|-------|-------|------------------------------|
| `~/.openclaw/auth-profiles.json` | Legacy/shared fallback | Often stale — still holds the old key |
| `~/.openclaw/agents/main/agent/openclaw-agent.sqlite` | `main` agent | May be empty or hold old key |
| `~/.openclaw/agents/kriya/agent/openclaw-agent.sqlite` | Named `kriya` agent | May be empty even after `main` is fixed |

**Symptom:** After fixing `main`, the named agent (`kriya`) still fails with `401 Authentication failed (provider returned HTTP 401)` or `No API key found for provider "venice"`.

**Diagnose each agent's effective key:**

```bash
export NVM_DIR="$HOME/.nvm" && . "$NVM_DIR/nvm.sh" && nvm use 24
openclaw models status                        # main/default agent
openclaw models status --agent kriya          # named agent
```

Look for the `effective=` / `profiles=` lines. If `kriya` shows no profiles or an old key fingerprint, sync it.

**Sync script — update all OpenClaw Venice auth stores:**

```bash
export NVM_DIR="$HOME/.nvm" && . "$NVM_DIR/nvm.sh" && nvm use 24
NEW_KEY=$(grep -oP 'VENICE_INFERENCE_KEY_[A-Za-z0-9_-]+' ~/.openclaw/openclaw.json | head -1)

python3 - <<'PY'
import json, os, sqlite3, time
new_key = os.environ['NEW_KEY']
base = os.path.expanduser('~/.openclaw')

# 1. Legacy/shared auth-profiles.json
p = os.path.join(base, 'auth-profiles.json')
if os.path.exists(p):
    with open(p) as f: d = json.load(f)
    d.setdefault('profiles', {})
    for pid in ['venice:default', 'venice:manual']:
        d['profiles'][pid] = {'type': 'api_key', 'provider': 'venice', 'key': new_key}
    with open(p, 'w') as f: json.dump(d, f, indent=2)
    print('updated auth-profiles.json')

# 2. Per-agent SQLite stores
for agent_dir in ['agents/main/agent', 'agents/kriya/agent']:
    db = os.path.join(base, agent_dir, 'openclaw-agent.sqlite')
    if not os.path.exists(db):
        print(f'skipping {db} (not found)')
        continue
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS auth_profile_store (
        store_key TEXT PRIMARY KEY, store_json TEXT NOT NULL, updated_at INTEGER NOT NULL)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS auth_profile_state (
        state_key TEXT PRIMARY KEY, state_json TEXT NOT NULL, updated_at INTEGER NOT NULL)''')
    now = int(time.time() * 1000)
    store = {'version': 1, 'profiles': {
        'venice:default': {'type': 'api_key', 'provider': 'venice', 'key': new_key},
        'venice:manual':  {'type': 'api_key', 'provider': 'venice', 'key': new_key}
    }}
    cur.execute("INSERT OR REPLACE INTO auth_profile_store VALUES (?,?,?)",
                ('primary', json.dumps(store), now))
    state = {'version': 1, 'lastGood': {}, 'usageStats': {}}
    cur.execute("INSERT OR REPLACE INTO auth_profile_state VALUES (?,?,?)",
                ('primary', json.dumps(state), now))
    conn.commit()
    conn.close()
    print(f'updated {db}')
PY

# 3. Restart gateway
systemctl --user restart openclaw-gateway.service
sleep 5 && curl -s http://127.0.0.1:18789/health

# 4. Verify both agents
openclaw models status
openclaw models status --agent kriya

# 5. Smoke test Kriya
openclaw agent --agent kriya --local --message "pong"
# Should return a response with provider HTTP 200
```

**Key lesson:** Fixing auth for `main` does **not** automatically fix named agents. Each agent has its own SQLite auth store. Always verify with `openclaw models status --agent <name>` and a real agent turn before declaring auth fixed.

### Post-Upgrade Re-Auth Required (v2026.6.x+)

After `npm install -g openclaw@latest` to v2026.6.x or newer, the existing Venice API key in `~/.openclaw/auth-profiles.json` is no longer read. Auth moved to a per-agent SQLite store (`~/.openclaw/agents/main/agent/openclaw-agent.sqlite`) and migration does NOT auto-import. Kriya will fail with `No API key found for provider "venice"` and all four fallback models error with `(auth)`. Fix: re-register with `openclaw models auth paste-api-key --provider venice` (key on stdin). Full steps in the "Post-Upgrade Auth Migration (v2026.6.x+)" section below.

### WSL OOM Kill

OpenClaw's Node.js gateway can consume ~2.5 GB RAM. When WSL2 has limited memory (default ~3.9 GB dynamic), running OpenClaw alongside Paperclip, VoiceAI, or other Node services causes the Linux OOM killer to terminate the gateway process. Symptoms: gateway silently stops, no error in logs, `dmesg` shows `oom-kill` entry.

**Fix:** Increase WSL2 memory via `/mnt/c/Users/<username>/.wslconfig`:
```ini
[wsl2]
memory=5GB
swap=2GB
```
Then restart WSL: `wsl --shutdown` from PowerShell, then reopen terminal.

**Diagnostics:** Check `dmesg | grep oom` for OOM events. Check `free -h` for current memory. Check stability logs at `~/.openclaw/logs/stability/` for `gateway.startup_failed.json` entries.

**Prevention:** Don't run Paperclip + OpenClaw + VoiceAI simultaneously unless WSL2 has ≥5GB RAM. Kill unused Node services (`kill <pid>`) before starting the gateway.
- **Known issue:** Gateway can be OOM-killed in WSL2 when running alongside other Node.js processes — see stability logs at `~/.openclaw/logs/stability/`

### Scope Approval Error (`openclaw agent --deliver`)

When using `openclaw agent --message "..." --deliver`, the agent may request more tool scopes than currently approved in `exec-approvals.json`. This produces the error:

```
gateway connect failed: GatewayClientRequestError: scope upgrade pending approval (requestId: ...)
EMBEDDED FALLBACK: Gateway agent failed; running embedded agent: GatewayTransportError: gateway closed (1008): pairing required: device is asking for more scopes than currently approved
```

**Fix:** Run `openclaw configure` on the gateway host and approve the requested scopes. Alternatively, remove the `--deliver` flag and handle delivery explicitly through the cron `delivery` config or a separate mechanism. The cron jobs with `"delivery": { "mode": "announce" }` don't have this issue — they deliver through the gateway's built-in channel routing, not through scope-escalating agent commands.

### `openclaw logs` Has No `--lines` Flag

`openclaw logs` does NOT support `--lines N`. To get the last N lines, pipe to `tail`:
```bash
~/.hermes/node/bin/openclaw logs 2>&1 | tail -50
```
The `--follow` flag IS supported for live streaming.

### Model Timeouts & Fallbacks

When the configured model (e.g., `zai-org-glm-5-1`) times out, OpenClaw automatically falls back through the model fallback chain. In logs this appears as:
```
model_fallback_decision: candidate_failed → next fallback
```
Then eventually `candidate_succeeded` on a different model. This is normal but means:
- The agent's response may come from a different model than configured
- Timeout on reasoning models (GLM, Claude) is common for complex cron prompts — set `timeoutSeconds` generously (420+)
- Check `openclaw status` session rows to see which model a session is actually running

### Diagnosing Stalled Agent Projects

When the user says Kriya (or another OpenClaw agent) is "stalling" on a project, the issue is usually one of:

1. **Build errors blocking deployment** — Check the project's build command (`npm run build`, `tsc`, etc.) and run it. TypeScript errors in generated data files (truncated strings, missing apostrophes, syntax errors) are common when LLMs generate large data files. Fix the errors, commit, and push.

2. **Unpushed commits** — The agent may have written files but not committed/pushed. Check `git status` and `git log origin/<branch>..HEAD` in the project directory. If there are unpushed commits, push them. If the branch has no remote tracking (`git branch -vv` shows no `[origin/...]`), set it up with `git push -u origin <branch>`.

3. **No deployment config** — The project may build fine locally but lack Railway/Vercel/GitHub Pages deployment. Check for `railway.json`, `vercel.json`, or GitHub Pages setup. For static sites, `gh-pages` branch or `gh` CLI deployment is the quickest path.

4. **Agent lost context** — Check `~/.openclaw/workspace/memory/YYYY-MM-DD.md` for the agent's daily notes, which often contain the "next steps" the agent was working on. Also check `~/.openclaw/workspace/MEMORY.md` for long-term project state.

Quick diagnostic checklist:
```bash
# 1. Is the gateway running?
curl -s http://localhost:18789/health
# 2. Check project build
cd ~/.openclaw/workspace/<project> && npm run build 2>&1 | tail -20
# 3. Check git state
cd ~/.openclaw/workspace/<project> && git status && git log --oneline -5 && git branch -vv
# 4. Check agent's recent notes
cat ~/.openclaw/workspace/memory/$(date +%Y-%m-%d).md | tail -50
# 5. Check Open Design dev server logs (if running)
ls -lt ~/.openclaw/workspace/open-design/.tmp/tools-dev/default/logs/*/latest.log
```

### Telegram Rate Limiting (429)

Telegram returns `429 Too Many Requests` when the bot sends too many `sendChatAction` typing indicators in quick succession. This usually self-resolves in 5 seconds. If persistent, add delays between multi-message sends.

### "Drishti" Naming Collision

The user often refers to the OpenClaw agent (internally `agentId: "main"`, sender `"Kriya Viv's AI Bot"`) as **"Drishti"** in informal chat. This collides with two unrelated things:

- **`vivgatesAI/Drishti`** — a separate GitHub repo (Next.js + Railway web app deployed at `https://drishti.up.railway.app`, "visual intelligence hub" for AI insights/briefings).
- **`Drishti Backup/`** — a OneDrive directory on Windows (`/mnt/c/Users/vivek/OneDrive/Drishti Backup/`) that holds GAI Insights article output, infographics, and a `skills/` folder.

**When the user says "drishti" in an OpenClaw context, they mean the agent.** When they say "drishi repo" or "drishi app" or "drishi backup", they mean the GitHub project. Read the surrounding request to disambiguate — "remove the openrouter fallback on drishti" = OpenClaw config, not the repo.