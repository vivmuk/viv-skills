# Venice API Integration with Paperclip

## Current Status (as of 2026-06-14)

Venice API is **fully wired** in the AIPharmaXchange Paperclip instance.

- ✅ All 10 agents have `VENICE_API_KEY`, `VENICE_MODEL`, `VENICE_API_BASE`, `PAPERCLIP_API_URL`, `PAPERCLIP_COMPANY_ID`, `PAPERCLIP_AGENT_ID` in `adapterConfig.env`
- ✅ LLM-driven agents (CEO, CTO, MarketingDirector) use `nvidia-nemotron-3-ultra-550b-a55b`
- ✅ Tool-driven leaf agents use `tool-runner-adapter.py` (no LLM, just exec)
- ✅ Function-calling tools enabled in venice-adapter.py v2 — LLM can call Paperclip API directly
- ✅ Scheduled heartbeats via external launchd daemon (not Paperclip's in-server scheduler)

## Setup Steps (for a new instance)

### Step 1: Enable Environments (if not already done)

Settings > Instance Settings > Experimental > Enable Environments

### Step 2: Store the Venice API Key

The key is already at `~/.paperclip/instances/default/.env` (under `VENICE_API_KEY=*** or `VENICE_INFERENCE_KEY=`). Verify with:

```bash
grep -E "^(VENICE_API_KEY|VENICE_INFERENCE_KEY)=" /Users/vivgatesai/.paperclip/instances/default/.env
```

To store via UI: Settings > Secrets > New secret. Name `VENICE_API_KEY`, paste the value. Bind to agent env in step 4.

### Step 3: Choose an Adapter

The shipped `process` adapter at `~/.paperclip/adapters/venice-adapter.py` works out of the box. It calls Venice chat completions. Two modes:
- **LLM-driven mode** — for CEO/CTO/CMO. Env: `VENICE_API_KEY`, `VENICE_MODEL`, `VENICE_API_BASE`, plus `PAPERCLIP_*` for tool calling.
- **Tool-runner mode** — for leaf agents. Adapter at `~/.paperclip/adapters/tool-runner-adapter.py` (custom). Env: `TOOL_SCRIPTS_DIR`, `TOOL_DEFAULT_SCRIPT`, `TOOL_TIMEOUT`.

For non-process integrations, the `http` built-in adapter is OpenAI-compatible and can be pointed at `https://api.venice.ai/api/v1` with a Bearer token.

### Step 4: Bind Env to Agent

Per-agent via API:
```bash
PATCH /api/agents/{id} body {"adapterConfig": {"env": {"VENICE_API_KEY": {"type":"plain","value":"..."}}}}
```

Bulk wire: `python3 ~/.hermes/skills/autonomous-ai-agents/paperclip/scripts/wire-venice-key.py`

### Step 5: Select Model

LLM agents use `nvidia-nemotron-3-ultra-550b-a55b` by default. Cheaper alternatives for tools that don't need top quality: `gemma-4-uncensored`, `deepseek-v4-flash`.

**Do NOT use `openai-gpt-55-pro`** — user explicitly excluded it (too expensive). Use `grok-4-20` for premium authoring, `gemma-4-uncensored` for A/B judging.

## Critical Integration Details

### PAPERCLIP_* env vars (required for tool-calling LLM agents)

For an LLM agent to call Paperclip API via the venice-adapter, all three must be in `adapterConfig.env`:

| Var | What it does |
|---|---|
| `PAPERCLIP_API_URL` | Base URL, e.g. `http://127.0.0.1:3100` |
| `PAPERCLIP_COMPANY_ID` | The company UUID — used to list agents, find delegation targets |
| `PAPERCLIP_AGENT_ID` | The agent's own UUID — used to fetch its assigned issues |

Without these, the LLM gets the system prompt but no way to interact with Paperclip — it produces only text.

### venice-adapter.py v2 — function-calling

The current adapter exposes these tools to the LLM (OpenAI-compatible tool format):

- `add_comment(issueId, body)` — POST `/api/issues/{id}/comments`
- `create_child_issue(parentId, title, description, assigneeAgentId, priority, status)` — POST `/api/issues/{id}/children`
- `update_issue_status(issueId, status)` — PATCH `/api/issues/{id}`
- `get_issue(issueId)` — GET `/api/issues/{id}`
- `list_my_issues(statuses)` — GET `/api/companies/{id}/issues?status=...`, filtered to current agent
- `checkout_issue(issueId)` — POST `/api/issues/{id}/checkout`
- `request_confirmation(issueId, message)` — POST `/api/companies/{id}/approvals`
- `get_agents_overview()` — GET `/api/companies/{id}/agents` (slim)

The adapter runs a tool-calling loop: model calls tool → adapter executes Paperclip API call → result returned to model → model produces final text. Set `PAPERCLIP_DISABLE_TOOLS=1` to disable and use the old text-only mode.

### Auto-fetch fallback for empty PAPERCLIP_TASK

Paperclip does NOT pass the assigned issue as `PAPERCLIP_TASK` on heartbeat invocation. The adapter has two fallbacks:

1. If `PAPERCLIP_TASK_ID` is set (some Paperclip versions) → fetch the issue and use as task
2. If only `PAPERCLIP_AGENT_ID` is set → call `list_my_issues(todo,in_progress,in_review,blocked)`, filter to this agent, build a "Triage your assigned issues" prompt

Both fallbacks are in `~/.paperclip/adapters/venice-adapter.py` lines ~50-90. Without them, the agent produces only a "READY" probe and never does work.

### Scheduled heartbeats — external daemon

Paperclip's in-server scheduler shows `intervalSec: 0, schedulerActive: False` even when `runtimeConfig.heartbeat.enabled: true` and `intervalMs` are set. This is a verified bug as of Paperclip 2026.609.0.

**Workaround:** external launchd daemon at `~/.paperclip/scheduler-daemon.py`, loaded via `~/Library/LaunchAgents/com.aipharmaxchange.paperclip-scheduler.plist`. It reads `~/.paperclip/scheduler-config.json` and calls `POST /api/agents/{id}/heartbeat/invoke` for each agent on a per-agent interval (CEO/CTO/CMO every 6h, daily leaf agents every 24h, weekly rare leaves every 7d). Skips an agent if it's already running a heartbeat (via `GET /api/agents/{id}/runtime-state`).

## Venice API Base URL

```
https://api.venice.ai/api/v1
```

This is the OpenAI-compatible endpoint. All models listed via `GET /v1/models` are available.

## Key Venice Models for Paperclip Agents

| Model | Context | Best For | Cost |
|-------|---------|----------|------|
| `nvidia-nemotron-3-ultra-550b-a55b` | 256K | Default LLM agent work | Cheap |
| `gemma-4-uncensored` | 256K | Raw text, no filter | Very cheap |
| `deepseek-v4-flash` | 1M | Fast/cheap extraction | Very cheap |
| `grok-4-20` | 2M | Premium authoring (NOT gpt-55-pro) | Moderate |
| ~~`openai-gpt-55-pro`~~ | 1M | ~~Top reasoning~~ | **EXCLUDED — too expensive** |
| `claude-opus-4-8` | 1M | Long-context analysis | Expensive |
| `grok-imagine-image-quality` | — | Image gen (SOTA, user preference) | Moderate |

## Content Filter Caveat

Models like `deepseek-v4-pro` have an input-side content filter that can block scraped web text with HTTP 400. Use `gemma-4-uncensored` for agents that process raw web content, or pass `venice_parameters: {include_venice_system_prompt: false}` via extra_body to attempt bypass.

## See also

- `references/agent-instructions-and-adapters.md` — full adapter + instructions wiring recipe
- `references/task-lifecycle.md` — the 5-layer task lifecycle and "Process exited with code 1" debugging
- `references/finance-events.md` — posting `inference_charge` events to track model spend
- The `venice-api` skill for full model catalog and SDK compatibility notes
- The `paperclip-delivery-daemon` skill for the auto-email-on-done pipeline
