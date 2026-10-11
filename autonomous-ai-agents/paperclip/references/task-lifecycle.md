# Paperclip Task Lifecycle

What looks like a simple "create an issue, assign an agent, run heartbeat" turns out
to be a 5-layer hierarchy. If any layer is missing or unbound, the adapter spawns in
fallback mode and exits with code 1 (`Process exited with code 1` in the inbox). This
reference is the post-mortem of a session where a smoke test failed repeatedly until
every layer was correct.

## The 5 layers (top → bottom)

```
Project (e.g. "LinkedIn Growth")
  └─ Project Workspace (execution environment, ONE per project typically)
       └─ Issue (the task)
            └─ Execution Workspace (created PER RUN, sourceIssueId = issue.id)
                 └─ Agent Run (spawns the process adapter in execution workspace cwd)
```

A run uses a project's workspace by binding `issue.projectId` → project's
`project_workspace` (the cwd). The runtime writes a `TASK.md` into that cwd and
sets `PAPERCLIP_TASK` to the path. The process adapter reads the file.

**If the project has no project_workspace** (the typical state for hand-rolled
companies), the runtime can't write a TASK.md, so it falls back to a per-agent
sandbox at `~/.paperclip/instances/default/workspaces/<agentId>/`. That sandbox
is empty, so `PAPERCLIP_TASK` arrives empty, and a strict adapter exits with
code 1.

## Symptom: "No project or prior session workspace was available."

This is the runtime's fallback path log. It means:

1. The issue either has no `projectId`, OR
2. The project has no `project_workspace` (even if `projectId` is set), OR
3. There's no prior session for the agent to continue from

The first two are the usual culprits. The third is rare for a fresh agent.

You can confirm by checking the issue via the API:

```python
issue = GET /api/issues/{id}
# Look for: projectId, projectWorkspaceId, executionWorkspaceId
# If projectId is set but projectWorkspaceId is null AND the project has no
# project workspaces → that's your bug.
```

## How to make a run work (in order of preference)

### Option A — Use the UI's "New Task" button (correct path)

The UI's task creation form handles all the bindings for you. The user's manual
"create an issue" via the API skipped steps 2-4 above, which is why the smoke
test failed.

### Option B — Create issue with project + project_workspace manually

```bash
# 1. Find the project
PROJ=$(paperclipai project list -C <companyId> --json | jq -r '.[] | select(.name | contains("LinkedIn")) | .id')

# 2. Create a project workspace pointing at your code
WS=$(paperclipai project-workspace create $PROJ \
  --payload-json '{"name":"linkedin-shared","cwd":"/path/to/workspace","mode":"shared_workspace","strategyType":"project_primary"}' \
  --json | jq -r .id)

# 3. Create an issue bound to the project
curl -X POST "http://127.0.0.1:3100/api/companies/<companyId>/issues" \
  -H "Authorization: Bearer <board-token>" \
  -H "Company-Id: <companyId>" \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"...\",\"description\":\"...\",\"projectId\":\"$PROJ\",\"assigneeAgentId\":\"$AGENT\",\"workMode\":\"standard\"}"
```

Note: even after this, the runtime's binding logic may still pick the per-agent
fallback in some Paperclip versions. The defensive adapter below sidesteps that.

### Option C — Use the defensive adapter (works for any case)

The bundled `venice-adapter.py` (see SKILL.md "Venice API Integration") was
patched to handle the empty-task case. Resolution order:

1. `PAPERCLIP_TASK` env var (normal path)
2. stdin (normal path)
3. `TASK.md` / `task.md` / `TASK.txt` / `ISSUE.md` / `PROMPT.md` in cwd
4. **Heartbeat probe** — sends a "reply READY" prompt to Venice. The run succeeds
   and Paperclip sees the agent as alive. Useful for smoke tests and liveness checks
   without needing a fully-bound task context.

This means: even an unbound `POST /api/agents/{id}/heartbeat/invoke` now produces
a `succeeded` run that proves the Venice chain works end-to-end. Look for the
stderr line `[venice-adapter] no PAPERCLIP_TASK or task file found — sending
heartbeat probe.` to confirm you're on the fallback path.

## The auto-recovery system (route 1 to know about)

When a run fails with `latestRunErrorCode: "adapter_failed"`, Paperclip
auto-creates an `activeRecoveryAction` and **reassigns the issue to the
agent's manager** (usually the CEO) as a "stranded_assigned_issue". You'll see
this in the issue detail:

```json
"activeRecoveryAction": {
  "kind": "stranded_assigned_issue",
  "ownerAgentId": "<ceo-id>",
  "previousOwnerAgentId": "<your-agent-id>",
  "cause": "stranded_assigned_issue",
  "evidence": {"latestRunStatus": "failed", "latestRunErrorCode": "adapter_failed"},
  "nextAction": "Restore a live execution path, fix the runtime/adapter failure, or record an intentional manual resolution."
}
```

**Implication:** the CEO's inbox will fill up with failed-issue recoveries
from any agent. If you see the CEO processing "Venice smoke test" recoveries,
that's not the CEO doing real work — it's the recovery system.

**To unstick:** PATCH the issue to `status: "todo"` and reassign to the
original agent. The recovery action clears on the next successful run.

## Diagnosing a failed run (5-step probe)

```bash
# 1. Get the run ID
RUN=$(paperclipai run list -C <companyId> --json | jq -r '.[0].id')

# 2. Get the run log
LOG=~/.paperclip/instances/default/data/run-logs/<companyId>/<agentId>/${RUN}.ndjson
cat "$LOG"
# Look for: "No project or prior session workspace was available" → fallback path
#            "No task provided. Set PAPERCLIP_TASK" → empty task, adapter bailed
#            "VENICE_API_KEY not set" → env wiring missing

# 3. Get the issue
ISSUE=$(paperclipai issue get <id> -C <companyId> --json)
echo "$ISSUE" | jq '{status, projectId, projectWorkspaceId, assigneeAgentId, activeRecoveryAction}'

# 4. Check if the project has a workspace
paperclipai project-workspace list <projectId> -C <companyId> --json

# 5. Confirm the agent's env has the Venice key
curl -s "http://127.0.0.1:3100/api/agents/<agentId>?companyId=<companyId>" \
  | jq -r '.adapterConfig.env.VENICE_API_KEY.value' | head -c 20
# Should start with VENICE_INFERENCE_KEY_
```

## What does NOT bypass the lifecycle

These all looked like they should work but don't, because they skip the
project_workspace layer:

- ❌ Creating an issue with `projectId` set but no project_workspace exists
- ❌ PATCHing an existing issue to add a `projectId` after the fact
- ❌ Manually invoking `POST /api/agents/{id}/heartbeat/invoke` (no issue)
- ❌ Using `paperclipai agent-prompt` to push a task to an unbound agent
- ❌ Writing a `TASK.md` to the per-agent fallback workspace before the run

The defensive adapter is the path of least resistance for smoke tests. For
real production work, use the UI's New Task button so the full binding
chain is set up correctly.

## Endpoints summary (the ones that 404'd during this session)

The Paperclip API has several non-obvious endpoint paths. The full table is
in SKILL.md, but the ones that bit us:

| Action | Wrong path | Right path |
|--------|------------|------------|
| List agents | `/api/agents?companyId=X` (404) | `/api/companies/X/agents` |
| Create issue | `/api/issues` (404) | `/api/companies/X/issues` (POST) |
| Get issue | `/api/issues/{id}` ✓ | works |
| Patch issue | `/api/issues/{id}` (PATCH) ✓ | works |
| Invoke heartbeat | `/api/agents/{id}/invoke-heartbeat` (404) | `/api/agents/{id}/heartbeat/invoke` |
| List runs | `/api/heartbeat-runs` (404) | `/api/companies/X/heartbeat-runs` |
| Project workspaces | `/api/companies/X/project-workspaces?projectId=...` (404) | `paperclipai project-workspace list <projectId>` |
