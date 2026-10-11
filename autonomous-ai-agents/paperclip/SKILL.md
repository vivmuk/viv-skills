---
name: paperclip
version: 0.2.0
description: Paperclip — self-hosted multi-agent orchestration platform. Configure companies, agents, tasks, adapters, secrets, and provider integrations.
tags: [paperclip, agents, orchestration, multi-agent, tasks, venice]
---

# Paperclip

Self-hosted multi-agent orchestration platform. Running locally (default port 3100). Paperclip manages companies, AI agents, tasks, projects, and the adapters/secrets that connect agents to LLM providers.

## Access

- App: `http://127.0.0.1:3100`
- Onboarding: `http://127.0.0.1:3100/onboarding`
- Settings: `http://127.0.0.1:3100/settings`
- Agent page: `http://127.0.0.1:3100/agents/<agent-slug>`

## App Structure

### Sidebar Navigation
- **Dashboard** — Agent count, tasks, spend, recent activity
- **Inbox** — Incoming items needing attention
- **Work** — Tasks, Routines, Goals, Artifacts
- **Projects** — Grouped task boards (e.g. "Newsletter Growth", "LinkedIn Growth")
- **Agents** — All configured agents (e.g. CEO, BrandGuardian, ContentDirector)
- **Company** — Org, Skills, Costs, Activity, Settings

### Settings (two sections)

**Company Settings:**
- General — Company name, mission
- Environments — Execution targets (must be enabled in experimental settings first)
- Members — Team members
- Invites — Pending invitations
- Secrets — Managed secrets + Provider vaults

**Instance Settings:**
- Profile — User profile
- General — Deployment, auth, keyboard shortcuts, backup retention
- Access — Access control
- Heartbeats — Agent heartbeat configuration
- Experimental — Feature flags (Environments must be enabled here)
- Plugins — Installed plugins
- Adapters — Built-in and external adapters

## Onboarding Flow (4 steps)

1. **Company** — Name + mission/goal
2. **Agent** — Name, adapter type (Claude Code, Codex, etc.), model selection, environment test
3. **Task** — Title + description for first task
4. **Launch** — Review summary → "Create & Open Task"

## Built-in Adapters

| Adapter | Models | Notes |
|---------|--------|-------|
| acpx_local | 19 | |
| claude_local | 9 | Claude Code CLI |
| codex_local | 10 | OpenAI Codex CLI |
| cursor | 39 | Cursor IDE |
| cursor_cloud | 0 | |
| gemini_local | 6 | Gemini CLI |
| grok_local | 1 | |
| hermes_local | 0 | |
| http | — | Generic HTTP/OpenAI-compatible endpoint |

External adapters can be installed via "Install Adapter" dropdown (alpha feature).

**`process` adapter (the one most agent setup uses):** spawns a subprocess. You wire it to a Python script at `~/.paperclip/adapters/<your-adapter>.py`. Two patterns exist: **LLM-driven** (venice-adapter calls Venice chat and returns model output) and **tool-driven** (tool-runner executes a named script). See "Two adapter types pattern" below.

## Agent Configuration

Each agent has tabs: Dashboard, Instructions, Skills, Configuration, Runs, Budget.

**Configuration sections:**
- **Identity** — Name, Title, Reports to (manager), Capabilities (markdown)
- **Adapter** — Adapter type (e.g. Process), with Test button
- **Run Policy** — Heartbeat toggle, interval (default 300 sec), advanced policy
- **Trust** — Preset (Standard / Low-trust review)
- **Permissions** — Can create new agents, Can assign tasks, etc.

## Task Assignment

Two ways to assign tasks:

1. **"New Task" button** (sidebar top) — Opens task creation form, pick any agent
2. **"Assign Task" button** (on agent page) — Pre-selects that agent for the task

Agents can also create sub-tasks and delegate if they have "Can assign tasks" permission enabled.

## Secrets & Provider Vaults

**Secrets tab** — Create managed secrets (e.g. API keys). Bind to agent environment variables or project env.

**Provider Vaults tab:**
- Local encrypted (default) — No vaults by default
- AWS Secrets Manager — Available
- GCP Secret Manager — Coming soon
- HashiCorp Vault — Coming soon

**Workflow:** Create secret → Open agent's Environment variables or project's Env field → Add env key (e.g. `VENICE_API_KEY`) → Choose Secret → Select the stored version.

## Venice API Integration

The shipped `process` adapter at `~/.paperclip/adapters/venice-adapter.py` is a 60-line Python script that calls Venice's chat completions endpoint. It reads `VENICE_API_KEY`, `VENICE_MODEL` (default `nvidia-nemotron-3-ultra-550b-a55b`), `VENICE_API_BASE` (default `https://api.venice.ai/api/v1`), and `PAPERCLIP_TASK` from env. No external deps.

### Setup (3 places to touch)

1. **Server-level env** — append to `~/.paperclip/instances/default/.env`:
   ```
   VENICE_API_KEY=VENICE_INFERENCE_KEY_xxx
   VENICE_API_BASE=https://api.venice.ai/api/v1
   VENICE_MODEL=nvidia-nemotron-3-ultra-550b-a55b
   ```
   Loaded by dotenv on server start. `dotenv@^17.0.1` is a dep.

2. **Per-agent adapter env** — each agent's `adapterConfig.env` is a dict of `{"KEY": {"type":"plain","value":"..."}}` (or `{"type":"secret","secretId":"..."}` for managed secrets). The Python adapter reads from `os.environ`, so the typed env must include the key. Quick way to wire all agents at once: PATCH `/api/agents/{id}` with body `{"adapterConfig":{...}}`. List endpoint is `GET /api/companies/{id}/agents` (NOT `/api/agents?companyId=...` which 404s). Board-token auth via `Authorization: Bearer <token>` + `Company-Id: <id>` headers.

3. **Open Design** — separate daemon, see `creative/open-design` skill. Update `~/.open-design/config.json` (`providers.openai.apiKey` is the key Venice uses — Open Design treats Venice as OpenAI-compatible).

### Endpoints (board-token auth)

| Action | Endpoint |
|--------|----------|
| List agents | `GET /api/companies/{companyId}/agents` |
| Get one | `GET /api/agents/{agentId}?companyId={companyId}` |
| Patch | `PATCH /api/agents/{agentId}` body `{"adapterConfig":{...}}` |
| Create board token | `paperclipai token board create --name X --json` |
| Create agent key | `paperclipai token agent create --agent <id> --name X --json` |
| Invoke heartbeat | `POST /api/agents/{agentId}/heartbeat/invoke` body `{}` |
| List runs | `GET /api/companies/{companyId}/heartbeat-runs` |

### Common gotchas

- **No board token = no writes.** The default `~/.paperclip/context.json` profile is `persona: board` but has no token. Use `paperclipai token board create` to mint one.
- **Empty PAPERCLIP_TASK = adapter exits with code 1.** The adapter has no fallback work; the heartbeat must be issue-driven (an open issue assigned to the agent), or use `paperclipai agent-prompt` to push a task directly to the agent (requires an agent profile context, not board).
- **Run logs:** `~/.paperclip/instances/default/data/run-logs/{companyId}/{agentId}/{runId}.ndjson` — one JSON line per stream chunk, has `ts`/`stream`/`chunk` fields. Read with `cat` + parse.
- **Venice image model restriction:** all Venice image models hard-cap `prompt` at 1500 chars at the gateway, regardless of model spec. Distill prompts to: titles → data points → layout → colors.
- **Venice `grok-imagine-image-quality`** returns `{"images": ["base64..."]}` (not `{"data": [{"b64_json": "..."}]}` like OpenAI). Use `flux-2-max` for native base64 output that works with the OpenAI shape.

For Venice model catalog and endpoints, see the `venice-api` skill.

For the 5-layer task lifecycle (project → project_workspace → issue → execution_workspace → run) and how the empty-PAPERCLIP_TASK symptom propagates, see `references/task-lifecycle.md`. Read it before debugging "Process exited with code 1" runs.

### Cost tracking — finance events (model → Paperclip)

The `paperclipai finance event:create` command is the bridge from any model call to Paperclip's cost/budget UI. Every dashboard surface (Costs, by-agent, by-agent-model, Finance Summary) reads from this stream. Without events, the cost UI stays empty even though Paperclip is running.

**CLI shape (board-persona only — mint a board token with `paperclipai token board create`):**
```bash
paperclipai finance event:create \
  -C <companyId> \
  --api-base http://127.0.0.1:3100 \
  --payload-json '{
    "eventKind": "inference_charge",
    "occurredAt": "2026-06-14T01:30:00Z",
    "amountCents": 42,
    "model": "nvidia-nemotron-3-ultra-550b-a55b",
    "biller": "venice",
    "agentId": "b6c97c25-...",
    "heartbeatRunId": "f529771e-...",
    "metadata": {"promptTokens": 1500, "completionTokens": 800, "agentName": "ResearchSynthesizer"}
  }'
```

**Required fields** (zod-validated, 400 on missing/wrong type):
- `eventKind` — enum, one of: `inference_charge | platform_fee | credit_purchase | credit_refund | credit_expiry | byok_fee | gateway_overhead | log_storage_charge | logpush_charge | provisioned_capacity_charge | training_charge | custom_model_import_charge | custom_model_storage_charge | manual_adjustment`. For BYOK Venice calls use `inference_charge`.
- `occurredAt` — ISO 8601 string, REQUIRED.
- `amountCents` — **integer**, NOT float. Sending `0.4` → 400 "Expected integer, received float". Use `int(round(usd * 100))`, or `max(1, int(round(usd * 100)))` for sub-cent.

**Useful optional fields:** `model`, `biller`, `agentId` (top-level — NOT in metadata), `heartbeatRunId` (must be a real existing run UUID or 404 "Heartbeat run not found"), `issueId`, `projectId`, `goalId`, `description`, `metadata`.

**Verifying it landed:**
```bash
paperclipai finance summary -C <companyId>   # → eventCount, debitCents, netCents
paperclipai cost summary -C <companyId>     # → spendCents, budgetCents, utilizationPercent
```

**Pitfall:** `cost by-agent` / `by-agent-model` may show empty right after posting — rollups run on a schedule. Don't treat empty rollups as "events didn't post"; check `finance summary` first.

**Process-adapter env vars** (available to `venice-adapter.py` and any other spawned script — use them to attribute work to the right agent and post costs):
- `PAPERCLIP_AGENT_ID` — the agent's UUID
- `PAPERCLIP_COMPANY_ID` — the company's UUID
- `PAPERCLIP_API_URL` — server base URL (e.g. `http://127.0.0.1:3100`)
- `PAPERCLIP_RUN_ID` — current run UUID (set by some adapters, not all paths)
- `PAPERCLIP_ISSUE_WORK_MODE` — `standard` | `review` etc.

The shipped `venice-adapter.py` reads these and calls `model_pricing.record_finance_event()` on every successful chat call, which posts a `inference_charge` event to Paperclip. See `references/finance-events.md` for the full schema, all gotchas, and a Python example.

### Cost control — daily budget cap pattern

Recording costs is necessary but not sufficient. A pipeline that can spend $50 in one run still burns money. The right shape is a **hard daily cap** enforced pre-flight at pipeline start, with a local ledger that mirrors (or supplements) Paperclip's finance events.

The pattern in `model_pricing.py` (workspace):
- `DAILY_BUDGET_USD` — env-overridable constant (default 10.0; user set 10 Diems/day on 2026-06-16 after seeing one pipeline dry run burn $2.38 for webscraping 8 topics).
- `record_spend(amount, kind, model)` — appends to `/tmp/aipharmaxchange_spend/spend_{YYYY-MM-DD}.json`. Atomic via `os.replace(tmp, path)`. Side-effect: every successful Venice call should call this.
- `check_budget(estimated_cost)` — returns `{allowed, cap_usd, spent_usd, remaining_usd, would_exceed_by_usd}`. Pipeline calls this at startup; aborts if `not allowed`.
- `get_today_spend()` — for reporting at end of run.

The pre-flight check is critical. Without it, the pipeline happily runs through $20 of API calls before the ledger ever gets consulted. The flow should be:

```python
state = check_budget(estimated_full_run_cost)
if not state["allowed"]:
    raise RuntimeError(f"Daily budget exhausted: spent ${state['spent_usd']:.2f} / ${state['cap_usd']:.2f}")
# ... run pipeline, calling record_spend() after each stage ...
```

`AIPHARMAXCHANGE_DAILY_BUDGET_USD` env var overrides the cap (useful for ad-hoc testing without touching code).

**Default "thrifty" pipeline shape** for a 10-Diem day (use these as the cost baseline):
- 3 search topics, 1 scrape per topic (was 8 topics × 2-3 scrapes — every additional scrape costs $0.02 + extraction tokens)
- 2 content variants, not 3 (drop the lowest-engagement channel — usually Twitter thread — re-enable with `AIPHARMAXCHANGE_N_VARIANTS=3`)
- Premium model (`openai-gpt-55-pro` or `grok-4-20`) ONLY for the A/B judge; everything else uses `deepseek-v4-flash` ($0.17/$0.35) or `gemma-4-uncensored` ($0.16/$0.5)
- `flux-2-pro` ($0.04/img) by default; `flux-2-max` ($0.09) is the "hero campaign" override (`AIPHARMAXCHANGE_IMAGE_MODEL`)
- Per-agent `VENICE_MODEL` set to `gemma-4-uncensored` for ALL agents (heartbeats included) — heartbeats are the silent cost leak when agents sit on `minimax-m3` or `nvidia-nemotron-3-ultra-550b-a55b`. The right per-agent env value shape is `{"type":"plain","value":"gemma-4-uncensored"}` (Paperclip's typed-env format), NOT just a string.

Expected daily pipeline cost at the thrifty defaults: $0.25–$0.50. Expected daily run with cron-fired heartbeats across 10 agents: add another $0.10–$0.30. Comfortably under a 10 Diem cap with headroom for the EOD report.

**"What does it have to show for it"** — the user's standing review criterion for any LLM-driven pipeline. Before approving a cost, surface what the run produced (a hero image, a 600-word article, three scored variants) alongside the spend. A pipeline that spent $2.38 to emit one image of a 2023 PMC article is not acceptable even if it stayed under cap. The thrifty refactor (3 topics, 2 variants, cheap models) wasn't just to fit under cap — it was to make each Diem produce something readable.

**Per-key Venice DIEM limit** — the silent blocker. Venice enforces a per-API-key DIEM spend cap, separate from the account balance. When the key's limit is hit, every call returns HTTP 402 `"API key DIEM spend limit exceeded. Your account may still have DIEM balance, but this API key has reached its configured DIEM spending limit."` This is a Venice dashboard setting, not a Paperclip config. If the spend ledger says you have headroom but the API is still 402-ing, the per-key cap is the cause. There is no public endpoint to inspect the cap from the CLI — `GET /api/v1/{api_key,user,billing,balance,keys,wallet,rate_limits,usage}` all return 404. Resolution: raise the cap on the Venice dashboard for the existing key, or mint a new key with a higher cap.

### Quick wire + verify (scripts)

For an existing instance with agents but no Venice env, the full chain can be wired and verified in two commands using the bundled scripts:

```bash
python3 ~/.hermes/skills/autonomous-ai-agents/paperclip/scripts/wire-venice-key.py
bash   ~/.hermes/skills/autonomous-ai-agents/paperclip/scripts/verify-venice.sh
```

- `wire-venice-key.py` — PATCHes every agent's `adapterConfig.env` to add `VENICE_API_KEY`, `VENICE_MODEL`, `VENICE_API_BASE`. Idempotent. Reads the key from `~/.paperclip/instances/default/.env` by default, or accept `--key VENICE_xxx`. Use `--dry-run` first to see which agents need wiring.
- `verify-venice.sh` — runs 4 checks (Paperclip up, Open Design up, key in .env, at least one agent wired) plus a real Venice chat call expecting the string `SMOKE_OK`. Exits 0 only if all pass.

Both scripts are env-var-overridable (`PAPERCLIP_API_BASE`, `OPEN_DESIGN_API`, `PAPERCLIP_COMPANY_ID`, `PAPERCLIP_ENV`).

## Status Check (recurring)

When the user asks "is Paperclip up / what's it doing / how is it configured," run this 6-step probe in one batch and report:

1. **Server listening?** `lsof -nP -iTCP:3100 -sTCP:LISTEN` — empty result means the server is down.
2. **Last log lines:** `tail -30 ~/.paperclip/instances/default/logs/server.log`. The literal string `Stopping embedded PostgreSQL` means the server was stopped cleanly (SIGTERM). Look for `ERROR` lines after that timestamp — those are from the *current* run.
3. **Active company + persona:** `cat ~/.paperclip/context.json`. `currentProfile` + `profiles.<name>.persona` tells you which workspace and which role the user is in (e.g. `persona: "board"` = read-only board view).
4. **Instance config:** `cat ~/.paperclip/instances/default/config.json` — note `server.port`, `database.embeddedPostgresPort`, `database.embeddedPostgresDataDir` (live state is under that path).
5. **Workspaces:** `ls ~/.paperclip/workspaces/` — each subdir is a workspace (e.g. `aipharmaxchange`). Inside, look for `*_MODELS.md`, `content_calendar_*.json`, `daily_post_generator.py`, and `visuals/` to characterize what the company is producing.
6. **Disk + DB size:** `du -sh ~/.paperclip/instances/default/db/ ~/.paperclip/workspaces/` — quickly tells you if the embedded postgres is healthy and whether the workspace is producing artifacts.

**Status report template** — keep it to ~10 lines: server up/down + last activity timestamp, company + persona, # of agents referenced in the log (use `grep -oE "GET /agents/[a-z-]+" server.log | sort -u`), workspace name + artifact count, last 2-3 ERROR lines from the log, and any obvious config drift (e.g. port mismatch, missing adapter).

### Known log signatures

- `Stopping embedded PostgreSQL` — server is down (clean SIGTERM). This is the *last* line on a stop; if it appears, the server is NOT running.
- `Skills catalog manifest not found at .../skills-catalog/generated/catalog.json` — **500 on `/api/skills/catalog`** but non-fatal; the rest of the app works. Fix: `cd ~/.hermes/node/lib/node_modules/paperclipai && pnpm --filter @paperclipai/skills-catalog build:manifest`. Safe to defer if the user isn't browsing the public skills catalog.
- `Failed query: update "projects" set ...` (HTTP 500) — a PATCH to `/api/projects/<id>` hit a DB constraint. Usually a stale `goal_id` reference. Non-fatal; user can re-edit the project in the UI to clear it.

## Pitfalls

- **Environments page says "not enabled"** — Go to Settings > Instance Settings > Experimental and enable Environments feature flag first
- **No external adapters installed by default** — The "External Adapters" section starts empty. Use "Install Adapter" to add, or use the `http` built-in adapter for OpenAI-compatible providers
- **Adapter model dropdown may be empty** — Some adapters (hermes_local, cursor_cloud) show 0 models. This means they're installed but no models are registered yet
- **Secrets must be bound explicitly** — Just creating a secret doesn't make it available to agents. You must go to agent/project environment settings and bind the secret to an env var name
- **Onboarding can be re-run** — The onboarding modal appears on the root page. Click "Start Onboarding" to create another company
- **Workspace switcher** — Top-left button shows current company. Click to switch between companies
- **`Process exited with code 1` from a tool-runner agent** — usually means: (a) the script named in `TOOL_DEFAULT_SCRIPT` doesn't exist at `TOOL_SCRIPTS_DIR`, (b) `PAPERCLIP_TASK` arrived empty AND `TOOL_DEFAULT_SCRIPT` is unset, or (c) the script ran and exited non-zero. Check `stderrExcerpt` on the run for the actual message.
- **`Process exited with code 1` from a venice-adapter agent** — usually means: empty `PAPERCLIP_TASK` with no issue/work binding (the venice-adapter has a "heartbeat probe" fallback that sends READY, so this is rare), OR the env doesn't have `VENICE_API_KEY` set with a real value (a `"REDACTED"` placeholder is rejected with 400: "Refusing to persist redacted placeholder for key: VENICE_API_KEY" — read it from `~/.paperclip/instances/default/.env` and pass the real value).
- **`PATCH /api/agents/{id}` rejects a `permissions` field** with "Expected never, received object". Don't include `permissions` in the PATCH body — it's read-only via that endpoint. If you need to change permissions, do it via the UI or `paperclipai` CLI.
- **Issue `status` enum is narrower than it looks** — valid values are exactly `['backlog', 'todo', 'in_progress', 'in_review', 'done', 'blocked', 'cancelled']`. There is **no `closed`** (this is what the delivery daemon was originally written to look for). A `PATCH /api/issues/{id}` with `{"status": "closed"}` returns 400 with `code: "invalid_enum_value"` and `options: [..., 'cancelled']`. To "close" an issue, PATCH `status: "cancelled"` (or `done` if the work actually shipped). The delivery daemon's `deliverStatuses` config should be `["done", "cancelled"]`, not `["done", "closed"]`.
- **Bulk issue cleanup needs iteration** — `GET /api/companies/{id}/issues?status=blocked&limit=100` is paginated; the count under-reports total. To clear the system, loop PATCHing until `moved == 0` per round, or it leaves residue across multiple status buckets. Expect 2-4 rounds of 100+ cancellations to reach a clean state.
- **API key rotation has three layers — check all three when you swap a key** (verified 2026-06-19, AIPharmaXchange v2 rebuild). When the user rotates their Venice API key, the new key must land in ALL of: (1) `~/.paperclip/instances/default/.env` — server-level env loaded by dotenv on Paperclip startup; (2) every agent's `adapterConfig.env.VENICE_API_KEY` — Paperclip spawns agents with these typed-env values, NOT with the server-level .env values, so the agent runs with whatever is in adapterConfig; (3) **every wrapper script that sets `env["VENICE_API_KEY"] = "..."` before invoking the orchestration** — wrapper scripts commonly force a specific key for reproducibility, but this overrides the user-provided new key with the (now-stale, DIEM-capped) old one, and the orchestration then silently runs against a 402-capped key and produces empty responses. The wrapper was hard-coding the old `c5diyYrdrr...` key in `~/.hermes/scripts/paperclip_wrap_carousel.py` even after the user gave me a new `mlgJHlfrx...` key. Symptom: every LLM call returns `finish_reason: "length"` with empty `content` and the orchestration logs "OUTLINE PARSE FAIL". Fix: `grep -rn "VENICE_INFERENCE_KEY_\|VENICE_API_KEY=" ~/.hermes/scripts/ ~/.paperclip/workspaces/` and patch every hard-coded literal. Also unset the env var in the shell that runs the wrapper (`unset VENICE_INFERENCE_KEY`) so the orchestration's `os.environ.get(...)` fallback to its module default is the new key, not the shell's stale one.
- **Two companies on disk, easy to confuse** — Paperclip CLI installs a starter "Paperclip Inc" company (`c9240459-...`) alongside the real one you create. Its agents have files on disk in `~/.paperclip/instances/default/companies/c9240459-.../agents/.../instructions/`. **Those are NOT your real company's instructions.** Always check an agent's `companyId` field — if it starts with `c9240459`, you're looking at the dummy.
- **Scheduled heartbeats may not fire** — even when `runtimeConfig.heartbeat.enabled: true` and `intervalMs: 86400000` are set, the scheduler endpoint may show `intervalSec: 0, schedulerActive: False` for that agent. On-demand and issue-driven heartbeats work; **interval-scheduled heartbeats are unreliable in this Paperclip version** (verified 2026-06-14). **Workaround:** an external launchd daemon at `~/.paperclip/scheduler-daemon.py` reads `~/.paperclip/scheduler-config.json` and calls `POST /api/agents/{id}/heartbeat/invoke` per agent on its own cron (CEO/CTO/CMO every 6h, daily leaf agents every 24h, weekly rare leaves every 7d). Skips agents that are already running a heartbeat via `GET /api/agents/{id}/runtime-state`. Loaded via `~/Library/LaunchAgents/com.aipharmaxchange.paperclip-scheduler.plist`. See `references/llm-agent-auto-fetch-and-tools.md` for the full pattern.
- **Don't set the scheduler interval too tight on LLM agents** — 1h intervals on the CEO/CTO/CMO are too aggressive. Every wake the LLM sees its assigned issues and creates new child issues for work it has already delegated, producing 200+ duplicate issues in a single day. **Use 6h for LLM agents**, 24h for daily leaf scripts, 7d for rare leaves (e.g. weekly reports). When the interval is wrong, the system spirals before you can stop it: cancel queued runs in batches of 10, then close duplicate issues with `status: "cancelled"`, then restart with the corrected interval. Verify with `GET /api/companies/{id}/live-runs` returning 0 before resuming.
- **Default to focused orchestration, not the full 10-agent template** — The default org (CEO + CTO + CMO + 7 leaves) is a *template*, not a target. For a specific deliverable class (paper-to-carousel, daily post, weekly report), the right size is usually 4-5 agents in a focused unit. Disable the rest with `PATCH /api/agents/{id} {"status": "paused"}`. Research, social posting, and newsletter production are separate work streams handled in the Hermes environment, not delegated to Paperclip agents. A 10-agent org with idle CTO + CMO + ResearchAnalyst + NewsletterEditor + 3 others generates 200+ Paperclip issues per day and 0 shipped deliverables; a 4-agent reviewer-gated unit ships 1 deliverable per cycle. (User preference, 2026-06-17.)

- **No instruction files = silent failure** — Agents with empty `instructionsBundle.files` will exit 1 on heartbeat with "no PAPERCLIP_TASK" errors that look like env issues. Always upload all 4 files (SOUL/AGENTS/HEARTBEAT/TOOLS) before triggering a heartbeat on a new agent.
- **`agent-hires` returns a different shape than `agent create`** — use `POST /api/companies/{id}/agent-hires` with `{name, title, role, description}` to create new agents; it returns `{agent, approval}` and the new agent has the default Venice-process adapter pre-wired. POSTing directly to `/api/companies/{id}/agents` is more raw.

## Two adapter types pattern (LLM-driven vs tool-driven)

When wiring an agent to a process adapter, you choose one of two patterns based on what the agent actually does:

**LLM-driven (venice-adapter):** the agent makes a decision, calls a model, returns text. Use for: CEO/CTO/CMO judgment calls, content writing, anything where the LLM is the work. Wires `VENICE_API_KEY`, `VENICE_MODEL`, `VENICE_API_BASE` into `adapterConfig.env`. Adapter is at `~/.paperclip/adapters/venice-adapter.py` (shipped).

**Tool-driven (tool-runner):** the agent's "work" is running a known script with known params. No LLM, no judgment — just exec. Use for: scheduled data pipelines, deterministic content runs, model-pricing refreshes, anything where you already have a Python script. Wires `TOOL_DEFAULT_SCRIPT` (script name) + `TOOL_TIMEOUT` into `adapterConfig.env`. Adapter at `~/.paperclip/adapters/tool-runner-adapter.py` reads `PAPERCLIP_TASK` for the script name, falls back to `TOOL_DEFAULT_SCRIPT`. Known-good template: `templates/tool-runner-adapter.py` (this skill).

**Mixed orgs (the common case):** leaf agents get tool-runner + a default script. Their parent agents get venice-adapter and decide when to delegate. The LLM in the parent decides what script the leaf should run by setting `PAPERCLIP_TASK` on the child run.

**Triggers the leaf runs at:** three ways in order of reliability —
1. **Issue-driven** — create an issue assigned to the leaf agent; Paperclip auto-wakes the agent's heartbeat. Reliable.
2. **Manual invoke** — `POST /api/agents/{id}/heartbeat/invoke` body `{}`. Works on-demand.
3. **Scheduled heartbeat** — set `runtimeConfig.heartbeat.intervalMs`. ⚠️ See pitfall below — currently this is unreliable in this Paperclip version; the scheduler shows `intervalSec: 0, schedulerActive: False` for agents whose heartbeats are "enabled". Prefer the issue-driven or manual-invoke pattern until that's fixed.

## Agent setup: instructions bundle (SOUL / AGENTS / HEARTBEAT / TOOLS)

An agent's behavior is driven by the four instruction files in its "instructions bundle" — what the agent reads at runtime, surfaced in the Paperclip UI's "Instructions" tab. **Without these files, an agent has no behavior** and the process adapter exits 1 on every heartbeat (the "Process exited with code 1" symptom).

**The four files (in `instructions/` per agent):**
- `SOUL.md` — persona, posture, voice. The LLM reads this as its "character."
- `AGENTS.md` — who reports to this agent, routing rules for delegation.
- `HEARTBEAT.md` — step-by-step checklist the agent runs every wake. Where most of the "what do I do" lives.
- `TOOLS.md` — what tools/scripts/people this agent has access to.

**Upload via API** (body shape, not raw text):
```
PUT /api/agents/{id}/instructions-bundle/file
Body: {"path": "SOUL.md", "content": "# SOUL.md ..\n\nmarkdown text..."}
```
Repeat for each of the 4 files. Verified working as of 2026-06-14. The endpoint returns `{path, size, language, markdown, ...}` on success.

**Don't confuse the dummy company** with the real one. The Paperclip CLI auto-creates a starter company called "Paperclip Inc" with id starting `c9240459-...` whose agents have SOUL/AGENTS/HEARTBEAT/TOOLS files on disk at `~/.paperclip/instances/default/companies/c9240459-.../agents/.../instructions/`. **Those files belong to the dummy, not to your real company.** Verify which company an instruction file belongs to by checking the agent's `companyId` field against `GET /api/companies`. The dummy's CEO has id `da52dc2d-...`; your real CEO will have a different id (e.g. `c375b5fb-...`).

**Bulk wiring** — for a fresh company, do all four steps in one Python script:
1. PATCH each agent's `adapterConfig` (env + command + args) with the right adapter
2. PATCH each agent's `runtimeConfig.heartbeat` (enabled + intervalMs)
3. PUT each of the 4 instruction files per agent
4. Trigger one heartbeat per agent to verify

A working example script that wired 10 agents (CEO + 9 reports) end-to-end is in the session log of 2026-06-14 — see `references/agent-instructions-and-adapters.md` for the full recipe and the file shape used.

## Restructuring the org chart (reportsTo)

The org tree shown in the UI is derived from each agent's `reportsTo` field. To restructure:

```bash
# Reassign an agent under a new manager
curl -X PATCH http://127.0.0.1:3100/api/agents/<agentId> \
  -H "Content-Type: application/json" \
  -d '{"reportsTo":"<newManagerAgentId>"}'

# Delete an orphan
curl -X DELETE http://127.0.0.1:3100/api/agents/<orphanId>
```

The org tree in the UI updates within seconds. No server restart needed.

**Verified working** for: 7 reassignments + 1 deletion + 1 hire in one batch. Pattern:
1. `POST /api/companies/{id}/agent-hires` with `{name, title, role, description}` to hire a new agent.
2. PATCH each existing agent's `reportsTo` to its new parent.
3. DELETE any agents that should be removed.
4. Verify: `GET /api/companies/{id}/org` shows the new tree; `GET /api/agents/{id}/chainOfCommand` shows the new ancestor chain.

## AIPharmaXchange Workspace (current)

Active workspace with 10 agents and 3 projects. All 10 agents have full instructions (4 files each) as of 2026-06-14. Org: CEO → {CTO, CMO}. CTO has 3 reports; CMO has 4.

**Agents (current):**
- LLM-driven: CEO, CTO, MarketingDirector (CMO) — venice-adapter, decide and delegate
- Tool-driven: ResearchAnalyst, ResearchSynthesizer, GitHubOSSLead, ContentDirector, LinkedInStrategist, NewsletterEditor, BrandGuardian — tool-runner-adapter, each with a default script

**Projects:** LinkedIn Growth (Pillar 2), Newsletter Growth (Pillar 1), Advocacy & GitHub (Pillar 3)

**Companies** (there are two — easy to confuse):
- `05f511f6-0e22-4d8a-ae55-fc17202944c4` — **AIPharmaXchange** (the real one)
- `c9240459-d91e-415d-8f91-94510e827915` — **Paperclip Inc** (the dummy starter; ignore unless testing the dummy)

**Status:** All 10 agents have full instructions and adapters wired. Manual heartbeats succeed for LLM-driven and tool-driven agents. Scheduled heartbeats are unreliable (see pitfall below). Real work starts when the user creates an issue in AIPharmaXchange; the auto-scheduler assigns it to an agent and wakes their heartbeat.

For the agent instructions and adapter patterns in detail, see `references/agent-instructions-and-adapters.md`.
For the LLM-agent auto-fetch + function-calling tools pattern (what makes CEO→CMO→Leaf delegation actually work), see `references/llm-agent-auto-fetch-and-tools.md`.
For Venice-specific integration details, see `references/venice-integration.md`.
For the auto-email pipeline that fires when an issue transitions to `done`, see the `paperclip-delivery-daemon` skill.

**Templates:**
- `templates/tool-runner-adapter.py` — drop-in adapter script for non-LLM agents that should run a known Python script on heartbeat. Set `TOOL_DEFAULT_SCRIPT` in the agent's env to point at the script name.
