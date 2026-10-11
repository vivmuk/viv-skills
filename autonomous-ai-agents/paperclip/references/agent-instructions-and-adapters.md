# Agent Instructions & Adapters — Field Notes

Deep detail on the agent-setup workflow in Paperclip. Companion to SKILL.md's "Two adapter types pattern" and "Agent setup" sections. Captures the exact API shapes, file contents, and gotchas hit while wiring 10 agents for AIPharmaXchange on 2026-06-14.

## The four instruction files (per agent)

Paperclip reads these as a single "bundle" at agent runtime. The UI's "Instructions" tab shows them. They are NOT a per-agent monorepo — they are the **agent's behavior contract**.

| File | Purpose | Length heuristic |
|---|---|---|
| `SOUL.md` | Persona, posture, voice, what kind of entity this agent is | 200-1500 chars |
| `AGENTS.md` | Who reports to this agent, delegation rules, what NOT to do | 300-2000 chars |
| `HEARTBEAT.md` | The step-by-step checklist the agent runs on every wake | 300-2000 chars |
| `TOOLS.md` | What scripts, APIs, or other agents this agent can use | 200-800 chars |

**Don't put data or runtime state here.** These are read on every heartbeat. Heavy files = slow heartbeats. Keep them under 2KB each.

## Upload API (verified working)

```bash
# Body shape is {path, content} — NOT a raw PUT body
PUT /api/agents/{agentId}/instructions-bundle/file
Content-Type: application/json

{
  "path": "SOUL.md",
  "content": "# SOUL.md -- Role Name\n\nMarkdown text..."
}
```

Returns: `{"path":"SOUL.md","size":1559,"language":"markdown","markdown":true,"isEntryFile":true,"editable":true,"deprecated":false,"virtual":false,"content":"..."}`

Loop over the 4 files for each agent. 40 PUTs for a 10-agent company finishes in ~10 seconds.

The "isEntryFile" flag is set on `SOUL.md` — that's the file the LLM reads first. The other 3 are supplemental.

## End-to-end bulk setup script shape

```python
import json, urllib.request

BASE = "http://127.0.0.1:3100"
COMPANY = "05f511f6-..."  # the real AIPharmaXchange id

def call(method, path, body=None):
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(f"{BASE}{path}", data=data, method=method)
    if body: req.add_header("Content-Type", "application/json")
    return json.loads(urllib.request.urlopen(req, timeout=30).read())

def read_venice_key():
    with open(f"/Users/vivgatesai/.paperclip/instances/default/.env") as f:
        for line in f:
            if line.startswith("VENICE_API_KEY=*** and "REDACTED" not in line:
                return line.split("=", 1)[1].strip().strip('"')
    return None

VENICE_KEY = read_venice_key()

# For each agent: configure adapter, configure heartbeat, upload 4 files
for agent in AGENTS:
    aid = agent["id"]
    if agent["llm"]:
        cfg = {
            "adapterConfig": {
                "cwd": "/Users/vivgatesai/.paperclip/workspaces/aipharmaxchange",
                "command": "python3",
                "args": ["/Users/vivgatesai/.paperclip/adapters/venice-adapter.py"],
                "env": {
                    "VENICE_MODEL": {"type":"plain","value":"nvidia-nemotron-3-ultra-550b-a55b"},
                    "VENICE_API_KEY": {"type":"plain","value": VENICE_KEY},
                    "VENICE_API_BASE": {"type":"plain","value":"https://api.venice.ai/api/v1"},
                }
            },
            "runtimeConfig": {"heartbeat": {"enabled": True, "intervalMs": 3600000, "maxConcurrentRuns": 5}},
        }
    else:
        cfg = {
            "adapterConfig": {
                "cwd": "/Users/vivgatesai/.paperclip/workspaces/aipharmaxchange",
                "command": "python3",
                "args": ["/Users/vivgatesai/.paperclip/adapters/tool-runner-adapter.py"],
                "env": {
                    "TOOL_SCRIPTS_DIR": {"type":"plain","value":"/Users/vivgatesai/.paperclip/workspaces/aipharmaxchange"},
                    "TOOL_DEFAULT_SCRIPT": {"type":"plain","value": agent["default_tool"]},
                    "TOOL_DEFAULT_PARAMS": {"type":"plain","value":"{}"},
                    "TOOL_TIMEOUT": {"type":"plain","value":"300"},
                }
            },
            "runtimeConfig": {"heartbeat": {"enabled": True, "intervalMs": 86400000, "maxConcurrentRuns": 1}},
        }
    call("PATCH", f"/api/agents/{aid}", cfg)
    for path, content in agent["files"].items():
        call("PUT", f"/api/agents/{aid}/instructions-bundle/file",
             body={"path": path, "content": content})
```

## The dummy "Paperclip Inc" gotcha

**Symptom:** you read what looks like a perfect SOUL.md/AGENTS.md/HEARTBEAT.md/TOOLS.md from disk, but those files have nothing to do with your company.

**Cause:** Paperclip CLI's `paperclip start` ships a starter company. The starter's agent files are at:

```
~/.paperclip/instances/default/companies/c9240459-d91e-415d-8f91-94510e827915/agents/<starter-ceo-id>/instructions/
```

This is **not** your company. Your company's agents (if you made them via the API) have empty `instructionsBundle.files` until you PUT them.

**How to tell them apart:**
- `GET /api/companies` → list with ids. Yours starts with the prefix from when you created it (e.g. `05f511f6-...`). Dummy starts with `c9240459-...`.
- The dummy's CEO agent id is `da52dc2d-...` (a UUID generated at install time). Yours will be different.

**Lesson:** when the user asks "what do the agents do?", always cross-check the agent's `companyId` field against the API. Don't read on-disk files for context.

## Hire an agent (one HTTP call)

```bash
POST /api/companies/{companyId}/agent-hires
{
  "name": "CTO",
  "title": "Chief Technology Officer",
  "role": "engineer",         # see enum in SKILL.md Pitfalls
  "description": "Leads engineering, research, and infrastructure for AIPharmaXchange."
}
```

Returns `{agent, approval}`. The new agent:
- Has `adapterType: "process"`, `adapterConfig: {}` (empty), `runtimeConfig.heartbeat.enabled: false`
- Has `reportsTo: null` (top-level — set it via PATCH)
- Has no instructions (empty bundle)

So hiring is step 1 of N. Then: PATCH `reportsTo`, PATCH `adapterConfig`, PATCH `runtimeConfig.heartbeat`, PUT 4 instruction files.

## Restructure the org

Single-PATCH reassignment works:
```bash
PATCH /api/agents/{id}
{"reportsTo": "<newManagerId>"}
```

`GET /api/companies/{id}/org` reflects changes within seconds. The org tree is computed from `reportsTo` on every read — no server restart.

**Orphan detection:** if an agent's `reportsTo` is `null` and they're not the CEO, they appear in the org tree as a top-level entry alongside the CEO. Fix by setting `reportsTo` to a real manager.

## Adapter runtime env vars (read by your Python adapter)

These are set by Paperclip and available to your subprocess:

| Var | Value |
|---|---|
| `PAPERCLIP_AGENT_ID` | UUID of the running agent |
| `PAPERCLIP_COMPANY_ID` | UUID of the company |
| `PAPERCLIP_API_URL` | Server base URL, e.g. `http://127.0.0.1:3100` |
| `PAPERCLIP_RUN_ID` | UUID of the current run (some adapters, not all paths) |
| `PAPERCLIP_ISSUE_WORK_MODE` | `standard` or `review` |
| `PAPERCLIP_TASK` | The task string (sometimes a file path, sometimes inline) |

Plus whatever you set in `adapterConfig.env`. The `venice-adapter.py` reads these to attribute cost events. The `tool-runner-adapter.py` uses `TOOL_DEFAULT_SCRIPT` and `TOOL_SCRIPTS_DIR`.

## When `Process exited with code 1` is the empty-task symptom

The venice-adapter has a defensive "heartbeat probe" fallback (see `references/task-lifecycle.md` in this skill) that sends a READY prompt when PAPERCLIP_TASK is empty. So a venice-agent with no issue binding will succeed at the probe. A tool-runner agent will NOT — its adapter exits 1 if PAPERCLIP_TASK is empty AND TOOL_DEFAULT_SCRIPT is unset. **Always set TOOL_DEFAULT_SCRIPT for tool-runner agents** or every heartbeat will fail.

## Heartbeat states (observed 2026-06-14)

- `idle` — ready, no current run
- `running` — has a live run
- `error` — last run failed

The "status" updates AFTER the run finishes. A queued run shows the previous status until the new one starts.

## Validating an end-to-end run (post-setup smoke test)

After wiring an agent:

1. `POST /api/agents/{id}/heartbeat/invoke` body `{}` — returns 202 with a `runId`
2. `GET /api/heartbeat-runs/{runId}` — poll every 5s
3. For venice: expect `status: "succeeded"`, `exitCode: 0`, `stdoutExcerpt` containing the CEO/agent's persona text
4. For tool-runner: expect `status: "succeeded"`, `exitCode: 0`, `stdoutExcerpt` containing the script's output

If the run stays in `queued` for >60s, the scheduler isn't picking it up — check the agent's heartbeat status via `GET /api/instance/scheduler-heartbeats` and the `schedulerActive` flag.

## Quick lookup: agent ids for AIPharmaXchange (snapshot 2026-06-14)

If the user asks you to operate on a specific agent, these ids are stable as of the snapshot:

| Name | id (first 8) | Role | Adapter |
|---|---|---|---|
| CEO | c375b5fb | ceo | venice |
| CTO | 639f20e9 | engineer | venice |
| MarketingDirector | d91a2779 | cmo | venice |
| ResearchAnalyst | 8e9c2e79 | researcher | tool-runner (news_harvester) |
| ResearchSynthesizer | b6c97c25 | researcher | tool-runner (ab_judge) |
| GitHubOSSLead | 0c71d6f2 | engineer | tool-runner (github_oss_lead) |
| ContentDirector | cb400a24 | pm | tool-runner (daily_post_generator) |
| LinkedInStrategist | 9b775997 | cmo | tool-runner (content_factory) |
| NewsletterEditor | 3ddb103d | designer | tool-runner (content_factory) |
| BrandGuardian | d490ea6f | designer | tool-runner (content_factory) |

Re-query with `GET /api/companies/05f511f6-0e22-4d8a-ae55-fc17202944c4/agents` to confirm; the prefix `05f511f6` is the AIPharmaXchange company id (the real one), and that's what the rest of the org is anchored to.
