# Paperclip Finance Events — Recording Model Costs

Paperclip's dashboard surfaces (Costs, by-agent, by-agent-model, Finance Summary)
are driven by **finance events** posted via `paperclipai finance event:create`.
Without events, the cost UI stays empty even though Paperclip itself is running.

## When to emit

For every model call (chat, image, embedding) you make on behalf of a
Paperclip agent, emit one event. Even sub-cent calls (round to 1¢ minimum).

## Payload schema (zod-validated)

```typescript
{
  eventKind: "inference_charge" | "platform_fee" | "credit_purchase" |
             "credit_refund" | "credit_expiry" | "byok_fee" | "gateway_overhead" |
             "log_storage_charge" | "logpush_charge" |
             "provisioned_capacity_charge" | "training_charge" |
             "custom_model_import_charge" | "custom_model_storage_charge" |
             "manual_adjustment",         // REQUIRED, enum

  occurredAt: string,                    // REQUIRED, ISO 8601
  amountCents: integer,                   // REQUIRED, integer (NOT float)

  // Optional but useful:
  model?: string,
  biller?: string,                       // e.g. "venice", "openai"
  agentId?: string,                      // top-level (NOT in metadata)
  heartbeatRunId?: string,               // must be a real existing run UUID
  issueId?: string,
  projectId?: string,
  goalId?: string,
  description?: string,
  metadata?: object                      // free-form, not extracted into rollups
}
```

## Common gotchas (learned the hard way)

1. **`amountCents` must be an integer.** Sending `0.4` returns
   `Expected integer, received float`. Always `int(round(usd * 100))` or
   `max(1, int(round(usd * 100)))` for sub-cent calls.

2. **`agentId` is top-level, not in metadata.** Putting it under `metadata`
   silently stores null on the event. Same for `heartbeatRunId`, `issueId`.

3. **`heartbeatRunId` must reference a real existing run.** If you pass a
   made-up UUID, Paperclip returns 404 "Heartbeat run not found". For
   pipeline scripts NOT spawned by Paperclip, omit this field entirely.

4. **Only the board persona can write.** `agent` persona cannot create
   finance events. The `~/.paperclip/context.json` default is `board` but
   has no token — mint one with `paperclipai token board create --name X`.

5. **Empty rollups ≠ events lost.** `cost by-agent` / `by-agent-model`
   may show empty right after posting — rollups run on a schedule. Check
   `finance summary` first to confirm events landed.

## Reference: full API surface

| Command | Purpose |
|---------|---------|
| `paperclipai finance event:create --payload-json '{...}'` | Record an event |
| `paperclipai finance events -C <id>` | List recent events |
| `paperclipai finance summary -C <id>` | Aggregated totals |
| `paperclipai finance by-biller -C <id>` | Group by biller (venice/openai) |
| `paperclipai cost summary -C <id>` | Spend vs budget |
| `paperclipai cost by-agent -C <id>` | Per-agent spend |
| `paperclipai cost by-agent-model -C <id>` | Per-agent-per-model spend |
| `paperclipai cost by-provider -C <id>` | Per-provider spend |

## Worked example (Python, in a script)

```python
import json, subprocess, datetime
from model_pricing import cost_text_call, record_finance_event

# After a successful Venice chat call:
usage = response["usage"]
cost_usd = cost_text_call(model, usage["prompt_tokens"], usage["completion_tokens"])

record_finance_event(
    model=model,
    cost_usd=cost_usd,
    description=f"venice chat: {usage['prompt_tokens']}+{usage['completion_tokens']} tok",
    agent_id=os.environ.get("PAPERCLIP_AGENT_ID"),
    run_id=os.environ.get("PAPERCLIP_RUN_ID"),
    api_base=os.environ.get("PAPERCLIP_API_URL"),
    company_id=os.environ.get("PAPERCLIP_COMPANY_ID"),
    metadata={
        "promptTokens": usage["prompt_tokens"],
        "completionTokens": usage["completion_tokens"],
        "agentName": agent_name,
    },
)
```

The `record_finance_event()` helper in `model_pricing.py` (in the AIPharmaXchange
workspace) does this and falls back to a no-op if the board token isn't in
context. Ship it everywhere that makes model calls.
