# OpenClaw's reasoning-effort plumbing — verified code paths

This document traces exactly how OpenClaw decides what
`reasoning_effort` value to send to a provider when the user (or the
session level) sets a thinking level. Pulled from OpenClaw 2026.6.6,
verified with `grep` against the dist tree.

## The 7 thinking levels OpenClaw exposes

From `dist/source-info-CkJy0T_l.d.ts:175`:

```typeScript
type ThinkingLevel = "off" | "minimal" | "low" | "medium" | "high" | "xhigh" | "max";
```

The user's UI slider exposes all 7. Per-session override too.

## The two translator paths

### For providers with a `compat.thinkingFormat`

OpenClaw has special-case branches for vendors that use non-standard
param names (Z.AI, Qwen chat-template, DeepSeek, OpenRouter, Together):
the per-vendor branch sets the param the vendor expects, AND looks
up `model.thinkingLevelMap?.[options.reasoningEffort]` for translation.

For example Z.AI (`thinkingFormat === "zai"`):

```javascript
if (compat.thinkingFormat === "zai" && model.reasoning)
  params.enable_thinking = Boolean(options?.reasoningEffort);
```

For Venice, NO `compat.thinkingFormat` is set, so the FALL-THROUGH
branch applies:

### The Venice / OpenAI-compat fall-through

From `dist/openai-completions-DObeyZ3K.js`, the fall-through branch
(after all special-cases):

```javascript
else if (options?.reasoningEffort && model.reasoning && compat.supportsReasoningEffort)
  params.reasoning_effort = model.thinkingLevelMap?.[options.reasoningEffort]
                          ?? options.reasoningEffort;
else if (!options?.reasoningEffort && model.reasoning && compat.supportsReasoningEffort) {
  const offValue = model.thinkingLevelMap?.off;
  if (typeof offValue === "string")
    params.reasoning_effort = offValue;
}
```

Translation: when the user picks a level:

1. If `compat.supportsReasoningEffort === true` AND `model.reasoning`,
   look up `thinkingLevelMap[level]`. If found, use that. If not,
   pass `level` raw.
2. If user picked "off", set `reasoning_effort = thinkingLevelMap.off`
   (which you control).

### The pre-call clamp

Earlier in the file (line 648):

```javascript
const clampedReasoning = options?.reasoning
                       ? clampThinkingLevel(model, options.reasoning)
                       : void 0;
const reasoningEffort = clampedReasoning === "off"          ? void 0
                       : clampedReasoning === "max"         ? "xhigh"
                                                            : clampedReasoning;
```

This means at FIRST pass, OpenClaw maps `max → "xhigh"`, then passes
through `options.reasoningEffort` (which the LLM dispatcher code
above re-translates via `thinkingLevelMap`).

Net effect: a user clicking "max" in OpenClaw, with a properly
configured `thinkingLevelMap`, ends up sending whatever
`thinkingLevelMap.max` says. For Venice (no xhigh), set that to
`"high"` so Venice's max valid value lands.

## The "assert" reasoning-fires check (without OpenClaw)

```python
import json, urllib.request
req = urllib.request.Request(
    "https://api.venice.ai/api/v1/chat/completions",
    data=json.dumps({
      "model": "xiaomi-mimo-v2-5",  # or whatever you're testing
      "messages": [{"role":"user","content":"What is 2+3? Answer with just the number."}],
      "max_tokens": 60000,
      "stream": False,
    }).encode(),
    headers={"Authorization": "Bearer *** "Content-Type": "application/json"},
)
with urllib.request.urlopen(req, timeout=120) as r:
    resp = json.loads(r.read())
reasoning = resp["choices"][0]["message"].get("reasoning_content", "") or ""
print(f"reasoning_content length: {len(reasoning)}")
print(f"first 200 chars: {reasoning[:200]!r}")
print(f"finish_reason: {resp['choices'][0]['finish_reason']}")
```

If `reasoning_content` is empty AND the model itself supports
reasoning (check `defaultReasoningEffort` in catalog), then the model
defaulted to "off" somehow. Investigate.

## Per-model config in `openclaw.json` vs per-model config in plugin manifest

| Setting location | What OpenClaw reads it as |
|---|---|
| `openclaw.json::agents.defaults.models.venice/x.<config>` | Per-model `alias`, `params`, `agentRuntime`, `streaming` |
| `openclaw.json::agents.defaults.model.reasoningEffort` | INVALID — fails validate |
| `openclaw.plugin.json::modelCatalog.providers.venice.models[x].reasoning` | Boolean: does this model ever reason? |
| `…models[x].compat.supportsReasoningEffort` | Boolean: do we send the param? |
| `…models[x].compat.thinkingLevelMap` | Dict: OpenClaw's 7 levels → provider's API values |

The thinking_level plumbing lives at the manifest, NOT at
`openclaw.json::models.<id>`. If you're trying to set per-model
reasoning on a registered model and it doesn't take, you're setting
it in the wrong place.

## Xiaomi MiMo special case

OpenClaw ships a Xiaomi provider plugin (`dist/extensions/xiaomi/`)
with separate routing:

```javascript
const MIMO_REASONING_MODEL_IDS = new Set([
  "mimo-v2-pro", "mimo-v2-omni", "mimo-v2.5", "mimo-v2.5-pro", "mimo-v2.6-pro"
]);
const MIMO_THINKING_PROFILE = {
  levels: ["off","minimal","low","medium","high","xhigh","max"].map(id => ({id})),
  defaultLevel: "high"
};
```

Routing through Xiaomi provider directly:

- Model IDs are bare (`mimo-v2.5`, no `xiaomi-` prefix).
- Default reasoning level is "high".
- The plugin handles its own reasoning translation.

The README at `~/.hermes/skills/autonomous-ai-agents/openclaw/references/venice-skills-integration.md`
(loaded via the openclaw skill) doesn't mention this. Mention it the
next time you onboard a Xiaomi-direct use case.

## Edge case: a reasoning model falls back to "off" because no thinkingLevel was set

Looking at the `!options?.reasoningEffort && model.reasoning &&
compat.supportsReasoningEffort` branch:

```javascript
const offValue = model.thinkingLevelMap?.off;
if (typeof offValue === "string")
  params.reasoning_effort = offValue;
```

So if you have `compat.supportsReasoningEffort === true` but
`thinkingLevelMap.off` is undefined, AND the user didn't pick a
level, the dispatcher silently sets NO `reasoning_effort`. Provider
then applies its model default (`defaultReasoningEffort` from the
catalog).

If you want explicit "high" by default — and want to be sure no
session accidentally gets less — make sure `compat` has:

```json
{
  "supportsReasoningEffort": true,
  "thinkingLevelMap": {
    "off":     "none",
    ...
    "high":    "high",
    "xhigh":   "high",
    "max":     "high"
  }
}
```

And set the per-session thinking level through the OpenClaw UI (or via
the `cron`-job `thinking` field) to "max". That'll reliably land
"high" at Venice's API.

If you can't drive the session level, rely on Venice's own
`defaultReasoningEffort` field — for MiMo V2.5 that's already
"high", so even with no explicit slider choice, you get reasoning at
the maximum tier.
