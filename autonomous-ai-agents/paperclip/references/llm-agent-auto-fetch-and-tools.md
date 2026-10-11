# LLM Agents Need Auto-Fetch + Function Calling

The shipped `venice-adapter.py` (60 lines, just calls Venice chat) is enough
to keep an LLM agent alive and producing text. But for the agent to actually
DO WORK in Paperclip — triage issues, delegate to reports, update statuses,
leave comments — it needs two extra capabilities. This file documents both
and the gaps that motivated them.

## Gap 1: Paperclip doesn't pass the issue context on heartbeat

When you `POST /api/agents/{id}/heartbeat/invoke`, Paperclip starts the
agent's process adapter with `PAPERCLIP_TASK` either empty or pointing to
a TASK file in the workspace. In the AIPharmaXchange production usage, the
env var is empty, the file is missing, and the agent has no idea what to
work on. The shipped adapter has a "heartbeat probe" fallback that asks
the LLM to say READY, but the LLM never sees the assigned issues.

**Fix — auto-fetch the agent's assigned issues inside the adapter:**

```python
if not TASK and PC_AGENT_ID and PC_COMPANY_ID:
    statuses = "todo,in_progress,in_review,blocked"
    issues = http_get(f"/api/companies/{PC_COMPANY_ID}/issues?status={statuses}")
    mine = [i for i in issues if i.get("assigneeAgentId") == PC_AGENT_ID]
    if mine:
        TASK = build_triage_prompt(mine)  # shows each issue's title/desc/id
```

The prompt structure that works: a list of `# Issue N: {title}` blocks with
status, priority, ID, and a short description, followed by a final
instruction: *"Triage each issue per your AGENTS.md / HEARTBEAT.md and take
action: delegate, comment, update status, or close."*

The CEO/CTO/CMO are the primary beneficiaries — without this, they only
ever produce READY probes. Leaf agents that have an issue auto-assigned to
them benefit similarly.

For agents that DO get a `PAPERCLIP_TASK_ID` from Paperclip (some agent
types or execution modes), the adapter should fetch the issue and use it
as the task — try this BEFORE the assigned-issues fallback.

## Gap 2: LLM has no way to call Paperclip API

Even with a good task, an LLM agent can only output text. It can't create
child issues, update statuses, add comments. Paperclip's process adapter
just runs the command, captures stdout, and stores the result. There's no
return path for side effects.

**Fix — function-calling tools in the venice-adapter:**

Define Paperclip API endpoints as OpenAI-compatible tool descriptions, send
them to Venice with `tool_choice: "auto"`, run a tool-call loop in the
adapter, and execute the corresponding Paperclip API call when the LLM
invokes a tool.

The eight tools that cover 95% of LLM agent work:

| Tool | Use case |
|---|---|
| `add_comment(issueId, body)` | Status updates, follow-ups, escalation notes |
| `create_child_issue(parentId, title, description, assigneeAgentId, priority, status)` | Delegation to direct reports |
| `update_issue_status(issueId, status)` | Progress tracking |
| `get_issue(issueId)` | Re-read context, check status of delegated work |
| `list_my_issues(statuses)` | Triage on heartbeat (covered above) |
| `checkout_issue(issueId)` | Claim an issue so the agent is its owner |
| `request_confirmation(issueId, message)` | Escalate to the board/owner for approval |
| `get_agents_overview()` | Find the right delegate (returns id+name+role+reportsTo) |

The tool-call loop in the adapter:

```python
for iteration in range(max_iterations):
    resp = call_venice(messages, tools=TOOLS)
    msg = resp["choices"][0]["message"]
    if not msg.get("tool_calls"):
        return msg["content"]  # done
    messages.append(msg)  # assistant's tool-call message
    for tc in msg["tool_calls"]:
        result = execute_tool(tc["function"]["name"], json.loads(tc["function"]["arguments"]))
        messages.append({
            "role": "tool",
            "tool_call_id": tc["id"],
            "content": json.dumps(result)[:4000],
        })
```

The system prompt needs an identity line so the LLM knows its own id and
company id (otherwise it can't pass `assigneeAgentId` correctly):

```
Identity: agentId={self_id}, companyId={self_company}, currentTaskId={self_task}.
When you need to act (comment, create child issue, change status, list
issues, request confirmation), call the appropriate tool. After all tool
calls are resolved, give a brief plain-text summary of what you did.
```

## End-to-end delegation chain

With both fixes, the CEO→CMO→Leaf delegation actually works:

1. User creates issue `AIP-1: "Build LinkedIn carousel on FDA guidance"`, assigned to CEO
2. CEO heartbeat runs. `list_my_issues` returns [AIP-1]. LLM sees it, calls `create_child_issue(parentId=AIP-1, title="...", assigneeAgentId=CMO_id)`. Returns 201 with new AIP-N.
3. CMO heartbeat runs. Sees AIP-N assigned to it. Calls `create_child_issue` again with `assigneeAgentId=LinkedInStrategist_id`.
4. LinkedInStrategist heartbeat runs. Sees its assigned issue. Tool-runner adapter runs `content_factory.py` to produce the carousel.

**Verified end-to-end 2026-06-14** — without the auto-fetch, step 1 still
fires but the LLM says "READY" and does nothing. Without function calling,
even if the LLM knows the task, it has no way to delegate.

## When to disable

If you want the LLM to only produce text (for content review, comment
drafting, advisory work), set `PAPERCLIP_DISABLE_TOOLS=1` in the agent's
env. The adapter falls back to a text-only mode. Useful for read-only
"reviewer" agents.

## References in the codebase

- The patched `venice-adapter.py` at `~/.paperclip/adapters/venice-adapter.py` is the working version
- The `~/.paperclip/workspaces/aipharmaxchange/` scripts directory has the leaf-agent scripts
- See `references/agent-instructions-and-adapters.md` for how to wire `PAPERCLIP_*` env vars into an agent's adapterConfig
