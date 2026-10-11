---
name: openclaw-model-management
description: "Register a brand-new Venice-hosted model in OpenClaw, set it as primary, configure reasoning effort at the highest available level (with proper levelMap translation), and survive OpenClaw update wipes. Distinct from the broader `openclaw` skill (configuration + plugins) by being narrowly focused on the model-registry + reasoning path code that the openclaw LLM dispatcher reads."
version: 1.0.0
triggers:
  - register new openclaw model
  - change primary model openclaw
  - openclaw reasoning effort
  - venice new model registration
  - xiaomi mimo register
  - openclaw plugin manifest patch
  - openclaw update wipes manifest
platforms: [macos, linux]
metadata:
  hermes:
    tags: [openclaw, model, venice, reasoning, plugin, registration, catalog]
---

# OpenClaw Model Management

This skill covers the niche the broader `openclaw` skill covers lightly:
**registering a model that is not in the OpenClaw bundled plugin
catalog, and configuring its reasoning effort** so an agent's turn
actually gets the behavior the user asked for.

The bundled `openclaw` skill lists "Adding a new Venice model
persistently" as 6 steps. This skill is the practical follow-through:
the bundled catalog is never the source of truth for newly released
models, the JSON schema on `models.<id>` config items is narrow, and
`reasoning_effort` plumbing happens through the PLUGIN MANIFEST's
`compat.thinkingLevelMap`, not through `openclaw.json`.

## When to use

- User says "change Paridhi/the agent to model X" where X is **not in
  `openclaw models list | grep venice`**.
- User wants reasoning effort explicitly at high/xhigh/max.
- `openclaw update` ran and a model you registered is gone — you need
  to re-patch the manifest.
- You're about to set a model as primary and want to confirm reasoning
  fires correctly end-to-end.

## When NOT to use

- **The model is in the plugin manifest AND already in your config
  pool** (`/openclaw models set venice/<model-id>` shows it). Just
  `openclaw models set venice/<model-id>` — it auto-adds to
  `agents.defaults.models.<id>` (verified) and the gateway hot-reload
  picks up the new primary. NO manifest edit, NO cache clear,
  NO gateway restart. Full procedure below is not needed.
- **The model is in the Venice API but NOT yet flagged as
  "configured"/"default" in `openclaw models list`.
  Same as above** — `openclaw models set venice/<model-id>` is
  enough; the validator only checks the plugin manifest, not the
  user config. Confirmed working 2026-07-09 with
  `openai-gpt-56-terra-pro` (1M ctx, $3.125/M in / $18.75/M out,
  reasoning=pro) — pinned primary without touching the manifest.
- You're adding a non-Venice local provider (Ollama, LM Studio) —
  those auto-discover.
- You're changing routing/bindings, not the primary. Use the broader
  `openclaw` skill.

## Procedure

### Step 1 — Verify against the LIVE Venice API

OpenClaw's bundled plugin catalog ships with a snapshot from the OpenClaw
release. New models appear in Venice long before the plugin catches up.
**Always verify the model is live in Venice itself** before assuming it
"doesn't exist":

```python
import json, urllib.request
req = urllib.request.Request(
    "https://api.venice.ai/api/v1/models",
)
# Inject your VENICE_API_KEY via Authorization header
```

Look for these fields:

- `model_spec.availableContextTokens` — context window
- `model_spec.capabilities.maxCompletionTokens` — output cap
- `model_spec.capabilities.supportsFunctionCalling` — tool use
- `model_spec.capabilities.supportsReasoning` and
  `model_spec.capabilities.defaultReasoningEffort` — reasoning support
- `model_spec.capabilities.reasoningEffortOptions` — valid effort levels

### Step 2 — Edit the plugin manifest, NOT catalog.json

OpenClaw rebuilds `models.json` and `catalog.json` from the plugin
manifest on every agent invocation. Editing those files directly is
lost. The persistent source is:

```
~/.hermes/node/lib/node_modules/openclaw/dist/extensions/venice/openclaw.plugin.json
```

Edit it with Python (NOT sed — JSON-with-arrays formatting can break
under sed):

```python
import json
p = "/Users/vivgatesai/.hermes/node/lib/node_modules/openclaw/dist/extensions/venice/openclaw.plugin.json"
with open(p) as f: d = json.load(f)
models = d["modelCatalog"]["providers"]["venice"]["models"]
# Insert (or in-place replace) the new entry
```

The shape OpenClaw expects (verified from existing entries):

```json
{
  "id": "<model-id>",
  "name": "Display Name",
  "reasoning": true,
  "input": ["text", "image"],
  "contextWindow": 1000000,
  "maxTokens": 65536,
  "compat": {
    "supportsUsageInStreaming": false,
    "supportsReasoningEffort": true,
    "thinkingLevelMap": {
      "off":     "none",
      "minimal": "low",
      "low":     "low",
      "medium":  "medium",
      "high":    "high",     // Venice's MAX valid value
      "xhigh":   "high",     // collapse — Venice doesn't accept xhigh
      "max":     "high"      // collapse — Venice doesn't accept max
    }
  }
}
```

MUST include `supportsReasoningEffort: true` AND a complete
`thinkingLevelMap` — without these, OpenClaw silently drops your
effort level and you get the model's default (often OK, but if the
user asked specifically for "max", that gets lost).

### Step 3 — Register in `~/.openclaw/openclaw.json`

```bash
# Register in agents.defaults.models
openclaw config set agents.defaults.models.venice/<model-id> '{}'
# Set as primary
openclaw models set venice/<model-id>
```

NOTE: per-model config in `openclaw.json` accepts ONLY `alias`,
`params`, `agentRuntime`, `streaming`. **It does NOT accept
`reasoningEffort` directly** — that's misleading. The reasoning-effort
config lives on the plugin manifest entry's `compat.thinkingLevelMap`.
Trying to set `models.venice/<id>.reasoningEffort = "max"` will fail
`openclaw config validate` and `openclaw doctor --fix` will restore
from backup (potentially clobbering other edits you made in the same
session).

### Step 4 — Clear Node.js compile cache

After editing the plugin manifest, OpenClaw's compiled bytecode still
points at the old catalog. Clear it:

```bash
rm -rf /var/folders/*/T/node-compile-cache/openclaw /private/tmp/openclaw
```

Without this, the gateway may serve the old model list despite your
edits, and `openclaw models list` won't show the new entry until the
next gateway restart rebuilds bytecode.

### Step 5 — Full gateway restart (NOT just `gateway restart`)

```bash
pkill -f openclaw; sleep 2
openclaw gateway install --force
sleep 2
openclaw gateway start
sleep 4
openclaw models list | grep <model-id>
```

`openclaw gateway restart` is NOT enough for manifest changes. The
LaunchAgent reload process doesn't reload plugin bytecode. You must
kill the gateway process, reinstall the gateway LaunchAgent (forces
re-cache), then start.

### Step 6 — Smoke test under `--local`

```bash
openclaw agent --local \
  --agent main \
  --model venice/<model-id> \
  --message "Reply with OK exactly. No other text." \
  --json
```

Inspect the JSON:

- `winnerProvider == "venice"`
- `winnerModel == "<model-id>"`
- `stopReason == "stop"` (NOT `"length"` — length means the model
  ran out of tokens mid-reasoning)
- `finalAssistantVisibleText` is the model's actual response

If `stopReason == "length"`, raise `maxTokens` to 32K+ or disable
thinking.

### Step 7 — Verify reasoning is actually firing

Reasoning heavy models can be deceptive — they emit `content` without
ever calling the API param. Verify raw API usage:

```python
import json, urllib.request
req = urllib.request.Request(
    "https://api.venice.ai/api/v1/chat/completions",
    data=json.dumps({
      "model": "<model-id>",
      "messages": [{"role":"user","content":"What is 2+3? Answer with just the number."}],
      "max_tokens": 60000,
      "stream": False,
    }).encode(),
    headers={"Authorization": "Bearer *** "Content-Type": "application/json"},
)
with urllib.request.urlopen(req, timeout=120) as r:
    resp = json.loads(r.read())
len(resp["choices"][0]["message"].get("reasoning_content", "") or "")
```

Non-zero `reasoning_content` length means reasoning actually fired.
If zero, your `reasoning: true` flag in the manifest isn't being
picked up — go back to step 2.

## Pitfalls

- **Bundled plugin catalog is stale.** Newly released models show up
  in Venice's API days or weeks before OpenClaw's plugin catches up.
  NEVER trust `openclaw models list` as the source of truth — verify
  against `https://api.venice.ai/api/v1/models`.
- **`catalog.json` and `models.json` are ephemeral.** OpenClaw
  rebuilds both from the plugin manifest on every agent invocation.
  All edits to those files are lost. Edit the manifest.
- **Sed/edit the manifest by hand.** JSON-with-arrays layout can
  break under naïve sed transforms. Use Python's `json.load` /
  `json.dump` with `indent=2` to preserve format.
- **Per-model `openclaw.json` schema is restrictive.** Trying to set
  `models.<id>.reasoningEffort` fails validation. `openclaw doctor
  --fix` will then RESTORE the file from backup, dropping ANY OTHER
  CONFIG EDITS YOU MADE in the same session.
- **`agents.defaults.thinkingLevel` is NOT a valid schema field
  either.** A natural-looking mistake: "set the default thinking
  level for the whole agent to `high`." The schema doesn't accept
  it; `openclaw config validate` returns "agents.defaults: Invalid
  input" and you have to revert manually. Thinking level is
  session-level (per-turn) only — drive it through the plugin
  manifest's `compat.thinkingLevelMap` and the runtime UI/API
  sliders, NEVER through `openclaw.json`.
- **`models.<id>.params.reasoning_effort = "high"` does NOT override
  the session-level slider.** `params` is the OpenClaw generic
  passthrough bucket for unrecognized provider fields, but the LLM
  dispatcher reads `options.reasoningEffort` directly (built from
  session thinkingLevel + manifest `compat.thinkingLevelMap`) and
  writes the API param itself. If you've set per-model params and
  don't see them in the live request, that's why — set the level in
  the manifest and let the dispatcher do the rest.
- **`session_status` and other per-turn tools can't self-register
  a missing model.** If you ask the in-session tool to switch to a
  model not yet in the manifest, it errors with
  `"Model venice/<id> is not allowed"` — the whitelist check is the
  same code path that requires the manifest patch first. The
  CLI workflow (steps 2→5) is the only path.
- **Gateway restart alone is not enough for manifest changes.**
  `pkill -f openclaw && openclaw gateway install --force && sleep 4 &&
  openclaw gateway start`. The bytecode cache + LaunchAgent both need
  resetting.
- **`openclaw update` wipes your manifest patches.** Bundled plugin
  reinstalls over your edits. After every `openclaw update`, re-run
  step 4-5-6.
- **`openclaw models set venice/<id>` silently no-ops on the first
  run after a fresh boot.** State-migration warnings (legacy plugin
  index / 1 stale `config-health.json`) are emitted to stderr and
  consume the write output; the validator runs but the COMMIT LINE
  (`Updated config: ~/.openclaw/openclaw.json / Default model: …`)
  is hidden. Subsequent `openclaw models get` / `jq` will show the
  primary UNCHANGED. **Two cheap fixes:** (a) add
  `--log-level info` so the commit confirmation prints despite the
  warnings; or (b) just run it twice. Verified 2026-07-09 on
  OpenClaw 2026.6.11 (e085fa1). Symptom checklist:
  - `openclaw models set venice/<id>` returns exit 0 with no errors
  - But `jq -r '.agents.defaults.model.primary' ~/.openclaw/openclaw.json`
    still shows the OLD model
  - The most recent log line is a `state-migrations` warning, not the
    "Updated config" / "Default model" commit line
  Fix: re-run with `--log-level info`. Set this in any script that
  swaps primaries so you never get silent-failure false positives.
- **Reasoning models silently emit empty content if `max_tokens` is
  too small.** Reasoning tokens come out of the same budget as
  completion tokens. For reasoning-heavy models, set
  `max_tokens=32K` minimum or you'll get `finish_reason: "length"`
  with empty `content`.
- **Venice API rejects values not in `reasoningEffortOptions`.** For
  MiMo V2.5 that's `[none, low, medium, high]`. The "max" or "xhigh"
  values some other providers accept are INVALID here and will be
  rejected server-side. Translate them via `compat.thinkingLevelMap`
  to "high".
- **Direct reasoning API param is `reasoning_effort`, not
  `reasoningEffort`.** Bridge through OpenClaw's `params` JSON schema
  by using `compat.thinkingLevelMap` — that's the official path
  verified in the codebase.
- **The Xiaomi provider plugin already has MiMo defaults set to
  "high".** If you ever route through Xiaomi provider directly (not
  via Venice), the Xiaomi plugin's `MIMO_THINKING_PROFILE` already
  defaults `defaultLevel: "high"`. You only need the thinkingLevelMap
  for Venice routing.

## Per-session overrides — when `models set` "didn't take"

`openclaw models set` writes only the **config primary**
(`agents.defaults.model.primary`). It does **not** clear session-scoped
overrides. Sessions are tracked in
`~/.openclaw/agents/main/sessions/sessions.json` and each one can carry
`modelOverride` / `providerOverride` / `modelOverrideSource: "user"`.
When set, that session keeps using the OLD model even after a successful
config swap — and the override **survives hot-reload and gateway
restart**. Symptoms:

- `openclaw models status` shows `Default: venice/<new>` ✅
- `openclaw models list` tags the new one as `default,configured` ✅
- But the user reports the agent is "still running <old>" ❌

**Diagnose with `openclaw status` (NOT `models status`):**

```bash
openclaw status | sed -n '/Model selection/,$p'
```

If any session is pinned, you'll see a `Session X is pinned to Y … ·
Clear with: /model default · Reason: session override` block per
session.

**Clear from chat (preferred):** `/model default` in the active chat.

**Clear from the shell** (when you can't reach the chat session — e.g. it
was opened from CLI/telegram and is now stale):

```bash
cp ~/.openclaw/agents/main/sessions/sessions.json \
   ~/.openclaw/agents/main/sessions/sessions.json.before-clear-override.$(date +%Y%m%d-%H%M%S).bak
python3 - <<'PY'
import json, sys
p = '/Users/vivgatesai/.openclaw/agents/main/sessions/sessions.json'
s = json.load(open(p))
for k, m in s.items():
    if not isinstance(m, dict): continue
    for key in ['modelOverride', 'providerOverride', 'modelOverrideSource']:
        m.pop(key, None)
    if m.get('model') and 'claude-fable' in str(m['model']):  # tighten per case
        m.pop('model', None)
    if m.get('modelProvider') == 'venice' and 'modelOverride' not in m:
        m.pop('modelProvider', None)
with open(p, 'w') as f: json.dump(s, f, indent=2)
PY
openclaw status | grep -A 2 "pinned to" || echo "✓ no overrides remaining"
```

**Don't** touch subagent sessions (`agent:main:subagent:*`) that still
have `modelOverride` unless you own that delegation — those are
explicit per-task pins and clearing them silently reroutes work to the
default model.

Always re-run `openclaw status` (not just `models status`) at the end —
that's the only command that surfaces per-session overrides.

## Verification

After implementing, run this smoke check:

```bash
# 1. Model registered
openclaw models list | grep <model-id>     # expect: yes configured, default

# 2. OpenClaw routes correctly
openclaw agent --local --agent main --model venice/<model-id> \
  --message "Reply OK" --json | jq '.winnerProvider,.winnerModel,.stopReason'

# 3. Reasoning fires
python3 -c "
import json, urllib.request
req = urllib.request.Request('https://api.venice.ai/api/v1/chat/completions',
  data=json.dumps({'model':'<model-id>','messages':[{'role':'user','content':'2+3'}],
                   'max_tokens':60000}).encode(),
  headers={'Authorization':'Bearer *** 'Content-Type':'application/json'})
print(len(json.loads(urllib.request.urlopen(req,timeout=120).read())
       ['choices'][0]['message'].get('reasoning_content','')))
"  # expect: > 0
```

If any fails, walk back the steps. Most common regression: forgetting
`compat.supportsReasoningEffort: true` — reasoning fails to fire on
the per-turn level even though the model itself has reasoning.

### Fast field-name escape hatch

Whenever you don't know whether a config field exists or what its
exact shape is, run:

```bash
openclaw config schema | grep -B1 -A20 'agents\|models\|thinking'
```

The schema dump is huge but searchable. It's what the Editor uses to
decide if a `config set` call will validate — if you grep the schema
for a path you're about to write, you'll know in 5 seconds whether
the field exists or whether you'll resurrect a backup file because
of a validation failure. This is the single fastest way to avoid the
"3 wrong-field attempts → revert → try again" cycle.

## Support files

- `references/venice-model-discovery-and-thinkinglevelmap.md` —
  walkthrough of how OpenClaw's openai-completions.js dispatcher
  reads `compat.thinkingLevelMap` and translates OpenClaw's 7-level
  thinking slider into the provider's API param. Includes the exact
  fallback chain (`parameters.reasoning_effort = ...`) so you can
  verify reasoning plumbing without running live tests.
- `templates/patch-venice-plugin.py` — copy-and-edit script for
  inserting/updating a Venice model entry in the plugin manifest.
  Idempotent (re-runnable). Validates the entry shape before saving.
  Includes the canonical `thinkingLevelMap` for Venice (4-valid-value
  set: none|low|medium|high, with xhigh/max collapsed to high).
- `templates/smoke-test-reasoning-fires.py` — minimal Python that
  POSTs to Venice's chat completions endpoint with `max_tokens=32K`,
  asserts `reasoning_content` length > 0, and prints the first 200
  chars of reasoning. Use before/after editing the plugin manifest
  to confirm whether your change had the desired effect.
