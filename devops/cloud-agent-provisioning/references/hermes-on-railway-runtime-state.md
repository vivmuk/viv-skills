# Hermes-on-Railway runtime state anatomy

What lives where in a Nous `hermes-agent` container deployed on Railway.sh. Companion to `cloud-agent-provisioning`.

Read this when:
- "Reset Jiva's personality to default Hermes" (or any deployed agent)
- "Where does the persona live?" — `~/.hermes/profiles/<name>/` is the **common wrong guess** for a deployed Hermes; the actual locations are below.
- "Wipe and recreate, but keep skills."
- "The bot's voice changed after restart — what happened?"

## Mental model first: deployed = single-profile, NOT profile-aware

The `hermes profile create|list|delete|rename` CLI machinery in `autonomous-aiagents/hermes-agent` creates profiles under `~/.hermes/profiles/<name>/` — that's the **local CLI** multi-profile pattern. A **deployed** Hermes instance (Railway container, maritime.sh VM, Render service, any Docker) uses a single profile rooted at `$HERMES_HOME` and expresses identity through `SOUL.md`, NOT a separate profiles subtree.

Concretely: searching `~/.hermes/profiles/jiva/` on a Railway-deployed Hermes returns nothing useful. Search `~/.hermes/SOUL.md` and `~/.hermes/memories/{MEMORY,USER}.md` instead.

## Top-level filesystem layout

| Path | Lives on | Purpose | Reset? |
|---|---|---|---|
| `/app/hermes/` | Image layer | Build-time snapshot of persona + runtime config (single source of truth in `$HERMES_HOME` convention) | Reset here to survive next image build |
| `/app/hermes-src/` | Image layer | Untouched upstream clone of `NousResearch/hermes-agent` (reference; not used at runtime by the deployed instance) | Don't touch |
| `/entrypoint.sh` | Image layer | Boot script: mkdirs, copies SOUL.md + cli-config.yaml, writes `.env` from system env, `exec hermes gateway run`. Re-runs on every container start | Don't modify casually — it copies /app/ → /root/ on every start |
| `/root/.hermes/` | Persistent Railway volume | Runtime state: skills, sessions, memories, config, .env | Survives redeploy IF the volume stays attached |
| `/root/.hermes/SOUL.md` | Volume | Persona / identity file loaded into the system prompt at session start; independent of project-context files (`AGENTS.md`, `CLAUDE.md`, `.hermes.md`) | **Reset** for personality wipe |
| `/root/.hermes/cli-config.yaml` + `config.yaml` | Volume | Hermes runtime config (model, toolsets, memory chars, agent.max_turns); entrypoint copies `/app/hermes/cli-config.yaml` into both names per a single-source-of-truth gotcha | Keep — and remember the gateway reads `config.yaml`, NOT `~/.hermes/.env`; Railway env vars don't override the gateway. To hot-swap a model, MCP server, or toolset, edit the image-baked source `hermes/cli-config.yaml` and `railway up` — see `references/hermes-mcp-on-railway.md` for the worked MCP-from-source recipe |
| `/root/.hermes/.env` | Volume | Runtime secrets (e.g., Venice key, base URL, default model, Telegram / Discord tokens); written by entrypoint heredoc from system env at every boot. CLI loader reads this; the gateway does NOT | Keep — but don't expect changes here to affect the live gateway |
| `/root/.hermes/skills/` | Volume | Installed skills (autonomous-ai-agents, creative, mlops, software-development, etc., typically 18–20 directories) | **Keep** — that's the saved-list |
| `/root/.hermes/memories/` | Volume | `MEMORY.md` (agent notes / locked conventions) + `USER.md` (user profile); accumulated across sessions. Personality-shaped entries accumulate here over time | **Reset** if you want a clean slate, or surgically remove only the persona-flavored entries |
| `/root/.hermes/sessions/` + `state.db` + `state.db-{shm,wal}` | Volume | Active conversation history (SQLite + FTS5); FTS5-backed session log | Keep |
| `/root/.hermes/cron/`, `kanban/`, `kanban.db` | Volume | Operational schedule / work queue | Keep |
| `/root/.hermes/logs/` | Volume | Gateway + error logs | Keep |
| `/root/.hermes/gateway.lock`, `gateway.pid`, `gateway_state.json`, `channel_directory.json` | Volume | Gateway runtime state (PID, lock, paired channels) | Keep — wiping breaks Telegram / Discord pairing |
| `/root/.hermes/audio_cache/`, `image_cache/`, `cache/` | Volume | Generated media, model caches (can grow large) | Keep |
| `/root/.hermes/secrets/` | Volume | Cached secret files (chmod 600) | Keep |
| `/root/.hermes/auth.lock`, `auth.json` | Volume | OAuth state (cached credentials) | Keep |

## Entrypoint copy semantics (the daemon behind the reset problem)

The Tessa Kriesel pattern (default hermes-on-Railway entrypoint, recognizable by these lines) re-copies on every container start:

```bash
cp /app/hermes/SOUL.md        "$HERMES_HOME/SOUL.md"
cp /app/hermes/cli-config.yaml "$HERMES_HOME/cli-config.yaml"
cp /app/hermes/cli-config.yaml "$HERMES_HOME/config.yaml"
```

These run from `entrypoint.sh` on every container start — restart, redeploy, even a `railway restart --yes`. Implications for persona reset:

- Wiping `/root/.hermes/SOUL.md` alone is correct but **not enough** — every restart re-copies `/app/ → /root/`, restoring whatever is in the image.
- To make a personality wipe durable across restart: also empty (truncate) `/app/hermes/SOUL.md` inside the running container. The image-baked file's writable overlay is then empty; entrypoint will `cp` an empty file into the volume.
- To make it durable across `railway up` rebuilds: also edit the source-tree `hermes/SOUL.md` (e.g., `~/tmp/jiva-deploy/hermes/SOUL.md`) before `railway up`.

## Surgical-wipe procedure (worked example, 2026-07-16, Jiva micro-railway-instance)

Goal: reset personality to default Hermes; preserve skills, sessions, model config, .env, gateway state.

```bash
# Phase 1 — Snapshot the entire state to /tmp inside the container.
# Restorable via `tar xzf` if any step below needs to be undone.
railway ssh --service <svc> 'tar czf /tmp/jiva-snapshot-$(date +%F).tar.gz -C /root .hermes && ls -lh /tmp/jiva-snapshot-*.tar.gz'

# Phase 2 — Wipe persona at runtime (in container)
railway ssh --service <svc> '
  rm -fv /root/.hermes/SOUL.md \
         /root/.hermes/memories/MEMORY.md \
         /root/.hermes/memories/USER.md
'

# Phase 3 — Truncate the image-baked SOUL.md (in container)
# Subsequent entrypoint runs will cp an empty file over /root/.hermes/SOUL.md again.
railway ssh --service <svc> ': > /app/hermes/SOUL.md && wc -c /app/hermes/SOUL.md'

# Phase 4 — Edit the source tree (durable across `railway up`)
cat > /Users/.../tmp/jiva-deploy/hermes/SOUL.md <<'EOF'
# Default Hermes — no persona override.
# SOUL.md is intentionally blank. Personality is reset to base Hermes.
EOF

# Phase 5 — Restart so the gateway reloads under default Hermes
railway restart --service <svc> --yes
# May exit 124 on success; verify:
sleep 30 && railway status   # expect: status ● Online, fresh deployment ID

# Phase 6 — Verify
# Confirm /root/.hermes/SOUL.md is empty post-restart:
railway ssh --service <svc> 'wc -c /root/.hermes/SOUL.md'
# Expect: 0 or 1 (just newline)
# Confirm skills still present:
railway ssh --service <svc> 'ls /root/.hermes/skills/ | wc -l'
# Expect: same count as before the wipe (typically 18–20)
```

A Telegram ping from the user's phone should now get a default-Hermes reply without persona-flavored framing. If the response still shows the previous persona, see the **Failure modes** section below.

## What NOT to wipe during a personality reset

| Path | Why keep |
|---|---|
| `/root/.hermes/skills/` | Per the user's "Just keep the skills" directive — they paid to compile these and the runtime `hermes skills list` should still show them |
| `/root/.hermes/{cli-config,config}.yaml` | Model setup (Venice key, toolsets, retries, agent.max_turns) — wipes invalidate boot |
| `/root/.hermes/.env` | Source of secrets rendered from `railway variables`; entrypoint rewrites this from system env on every start anyway |
| `/root/.hermes/sessions/`, `state.db` | Active conversation history; not persona |
| `/root/.hermes/cron/`, `kanban.db`, `kanban/` | Operational schedule / work queue |
| `/root/.hermes/logs/` | Health-density data for postmortems |
| `/root/.hermes/gateway.lock`, `gateway_state.json`, `channel_directory.json` | Telegram / Discord adapter pairing state — wiping breaks the bot |
| `/root/.hermes/auth.json`, `secrets/` | OAuth credentials and cached secrets |
| `/root/.hermes/audio_cache/`, `image_cache/`, `cache/` | Generated media + model caches (large; fine to keep) |

## Recovery after a wipe you regret

The phase-1 tarball contains the full state. To recover one file:

```bash
# Inside the container
mkdir -p /root/.hermes/memories
tar xzf /tmp/jiva-snapshot-2026-07-16.tar.gz -C /root .hermes/memories/MEMORY.md
```

For a full rollback:

```bash
# Inside the container — restore everything
rm -rf /root/.hermes
tar xzf /tmp/jiva-snapshot-2026-07-16.tar.gz -C /root
```

## Failure modes

| Symptom | Likely cause | Fix |
|---|---|---|
| Telegram still replies with old persona after restart | Entrypoint re-copied `/app/hermes/SOUL.md` (Phase 3 missed) — image-bake is non-empty | Re-run Phase 3: `: > /app/hermes/SOUL.md` then restart again |
| Skills `hermes skills list` is empty after wipe | Accidentally nicked `/root/.hermes/skills/` in Phase 2 (`rm -rf` instead of surgical `rm`) | Restore from Phase-1 snapshot: `tar xzf /tmp/...tar.gz -C /root .hermes/skills/` |
| `railway restart` returns exit 124 and the agent never comes back | CLI timed out before the new container started — actual restart may still be in flight | Wait + verify: `sleep 60 && railway status`; do NOT loop restart |
| Wiped `/root/.hermes/gateway_state.json` and Telegram pairing is broken | Over-eager Phase 2 | Re-pair Telegram: `hermes pairing approve` after a Telegram `/start`, or restore from Phase-1 snapshot |
| Personality persists AFTER `railway up` rebuild | Source-tree `hermes/SOUL.md` not updated before rebuild | Edit `~/tmp/jiva-deploy/hermes/SOUL.md` (or equivalent source path) before the next `railway up` |

## What's outside scope for this reference

- **Building the initial Hermes-on-Railway deploy** (entrypoint source, Dockerfile, env-var contract) — that lives in `references/hermes-venice-on-maritime.md` (the env-var contract generalizes to Railway; for the platform-specific deploy step, see `references/railway-cli-notes.md`).
- **Skill-related maintenance** (curator sweeps, hub installation, skill publishing) — `autonomous-aiagents/hermes-agent`.
- **Local-CLI multi-profile patterns** (`hermes profile create|rename|delete` against `~/.hermes/profiles/<name>/`) — `autonomous-aiagents/hermes-agent`. These do not apply to a deployed Railway Hermes.
