---
name: managed-agent-deployment
description: Provisioning + operating AI agents on managed, serverless agent platforms (Maritime CLI and similar). Covers the agent lifecycle, custom LLM provider routing via env-var binding, MD-file taxonomy for agent schemas, the deploy-source modes, and known fc-manager lifecycle errors.
version: 0.1.0
triggers:
  - maritime
  - maritime cli
  - managed agent
  - zeroclaw
  - zero claw
  - serverless agent
  - fc-manager
  - agent fleet deploy
  - openclaw agent platform
---

# Managed Agent Deployment

When to use this skill:
- User asks to **create / configure / operate** an agent on a managed, serverless agent platform (Maritime CLI, similar).
- User wants to **override a platform-managed agent's default model** to a different LLM provider (Venice, OpenAI, Anthropic, Groq, etc.).
- User wants to **ship custom persona / CLAUDE.md / AGENTS.md / etc.** to a platform agent.
- User uses `maritime` (Maritime), `agent-platform` style CLIs, or references things like "zero claw", "openclaw", "fc-manager".

Related skills to load in tandem when relevant:
- `venice-api` for verifying that a model id is live in the registry, and for understanding Venice's default-model fallback.

## Core concept

**Managed agent platforms** run containers on the user's behalf (serverless Firecracker microVMs and similar). Three durable interfaces connect the user to a running agent:

1. **The platform CLI** (`maritime`, etc.) — drives lifecycle: create / init / link / deploy / chat / logs / env / status.
2. **Env vars on the agent** — runtime configuration (provider key, base URL, default model, framework-specific knobs).
3. **Framework MD + TOML files** (in a workdir linked to the agent) — persona, system-prompt template, operator notes, framework runtime config.

The platform **does not act as the LLM provider by default**. It fronts the agent's OpenAI-compatible chat with its own proxy token. To route chat to a custom LLM provider, override `OPENAI_BASE_URL` + `OPENAI_API_KEY` (and mirror the provider key into the framework-specific env var).

## Workflow

### Step 1 — Install the platform CLI

```bash
npm install -g maritime-cli                # or platform-specific
which maritime
maritime --version
```

### Step 2 — Authenticate (env-var route is canonical for headless/AI-agent flows)

```bash
# store the mk_… key chmod 600 (NEVER inline in shell history)
cat > ~/.maritime-token.env <<'EOF'
export MARITIME_TOKEN=<mk-key>
EOF
chmod 600 ~/.maritime-token.env

# verify: empty list means auth works; not 401
source ~/.maritime-token.env
maritime list --json
```

Why env-var and not `maritime login --token`? See **Pitfall P1**. The CLI's `--token` flag has stricter client-side validation than the server. Use the env var path even when the cli --token "looks" fine.

### Step 3 — Create the agent

```bash
maritime create -n my-agent -t zeroclaw --tier smart --json
# Frameworks (Maritime): zeroclaw (Rust, OpenAI-compatible on 42617), openclaw
# Tiers: smart ($1/mo, idle-sleep) · extended (warm) · always_on (continuous)
```

`smart` is the right default unless the user specified otherwise. Idle-sleep → ~1-3s first-wake latency, fine for batch agents.

### Step 4 — Wire env vars (THIS IS THE MOST DENSE STEP)

Env-var keys are framework-specific + client-specific. Tooling workflow:

1. Provider secret + base URL (provider-side the OpenAI SDK will use).
2. Mirror the same key into `OPENAI_API_KEY` so the SDK's Bearer header is satisfied (Pitfall P5 — without this the platform injects its own proxy token and routes chat through the platform gateway).
3. Override the default model via multiple env-var names defensively (Pitfall P2 — the framework's exact naming is undocumented until exercised).

```bash
AGENT=my-agent

# 1. provider secret + base URL
maritime env set $AGENT VENICE_INFERENCE_KEY=<KEY>                  # marks secret
maritime env set $AGENT OPENAI_API_KEY=<KEY>                        # mirror so SDK Bearer works
maritime env set $AGENT OPENAI_BASE_URL=https://api.venice.ai/api/v1 --no-secret --reload

# 2. default-model override (3 candidates, one will hit the framework)
maritime env set $AGENT ZEROCLAW_DEFAULT_MODEL=zai-org-glm-5-2 --no-secret --reload
maritime env set $AGENT OPENAI_DEFAULT_MODEL=zai-org-glm-5-2 --no-secret --reload
maritime env set $AGENT MODEL=zai-org-glm-5-2                     --no-secret --reload
```

Some `env set` calls report `reloaded:false` when the agent is already mid-reload — that's fine, the next reload picks up the latest values.

### Step 5 — Init / link a local workspace

The platform's "directory-belongs-to-an-agent" model: a local folder keyed to the agent in `.maritime/project.json` (git-ignored). Edits to MDs/TOMLs in that folder propagate via `deploy`.

```bash
mkdir -p ~/tmp/<agent>-work && cd ~/tmp/<agent>-work
maritime init <agent-name> --framework <fw> --tier <tier> --no-create --json
#   scaffolds: <platform>.json + AGENTS.md
maritime link <agent-name> --json        # attaches current dir to the existing agent
```

### Step 6 — Author MD files with distinct roles

A list, not a suggestion. **Single role per file** — mixing personas with operator guides confuses the framework's loader.

| File | Role | Loaded by |
|---|---|---|
| `<platform>.json` (e.g. `maritime.json`) | Operator schema: name, framework, tier, defaultModel, provider block, env registration | `deploy` |
| `<framework>.toml` (e.g. `zeroclaw.toml`) | Framework runtime: `[provider]`, `[gateway]`, `[prompt]`, `[memory]`, `[playbook]`, `[runtime]` | framework at boot |
| `AGENTS.md` | Agent persona (the agent's voice at runtime) | framework at boot |
| `PROMPT.md` | Default system prompt template; YAML frontmatter declares `model`, `provider`, `baseUrl`, `apiKeyEnvVar`, `maxTokens`, `temperature` | framework at boot |
| `CLAUDE.md` | Human/operator context — guide for the editor, NOT loaded by the agent | human reader only |
| `STATE.md` | QHX self-improvement log; append-only per production delta | agent at boot + after each run |
| `.env.example` | env-var schema, no secrets | operator reference |
| `prompts/<task>.md` | Task-specific prompt variants. Each frontmatter-typed (`model`, `useWhen`, `tokens`) | framework at task invocations |

Editorial rules (apply to every commit-worthy change in the agent's repo):
- **Zero em-dashes (—).** Periods, commas, hyphens, or line breaks. The doctrine bans.
- **YAML frontmatter on PROMPT.md and prompts/*** ONLY**. Other MDs use plain prose.
- **The default model ID must agree across 5–7 places.** Frontmatter, TOML, maritime.json, README, CLAUDE.md, AGENTS.md, `.env.example`. A model swap is a *transaction* across the bundle, not a single string.

### Step 7 — Deploy (or work around if it breaks)

```bash
# pick the right --source mode for the workdir state
maritime deploy --source template --wait --json       # persona-only changes
maritime deploy --source github --repo <url>          # custom code in a public git repo
maritime deploy --source docker --image <image:tag>   # custom container image
```

Three source modes matter — pick deliberately:

| `--source` | When | Pitfall |
|---|---|---|
| `template` | Persona-only changes, no custom code | The platform may try to pull `maritime-agent-{name}` from a registry that doesn't have it. Pull fails → 500. **Don't retry blindly**; repeated retries thrash the VM lifecycle (P3). |
| `github` | Workdir has a public git repo | None severe — uses the repo to derive the agent image. |
| `docker` | Custom image published to a registry | You must host it on a registry the platform can read (`ghcr.io/<u>/<r>:tag` is the safe default). |

### Step 8 — Verify

```bash
# expect: status=active, framework + tier match
maritime status <agent> --json

# expect: every expected key present, secrets masked
maritime env list <agent> --json

# expect: real reply routed through the configured provider, in the configured model's register
maritime chat <agent> "Which model are you? State plainly in one line." --json

# expect: "Agent deployed and running" log line, no errors at last deploy
maritime logs <agent> -n 10 --json
```

If chat returns `VM not found` / `Circuit breaker open`, see Pitfall P3.

## Pitfalls (must-know, with the recovery recipe)

### P1. CLI `--token` flag client-rejects a server-accepted mk_… key

**Pattern**: `maritime login --token mk_…` → "that does not look like a valid token". But `MARITIME_TOKEN=mk_… maritime list --json` → `[]`, not 401.

**Why**: The CLI's local regex / length validation is stricter than the server's. The server accepts the same token as authoritative.

**Fix**: Use the env-var route (`MARITIME_TOKEN=<key>`). Skip `maritime login` entirely in headless/AI-agent flows.

### P2. Provider default = `llama-3.3-70b` when framework sends no `model` field

**Pattern**: Agent chat returns responses stylistically consistent with llama70b even though env vars name a different model. Including visible top-level `model: "llama-3.3-70b"` in Venice response payload.

**Why**: Venice's `/v1/chat/completions` family-picks `llama-3.3-70b` when no `model` is in the body. Some frameworks' OpenAI-compatible paths drop the field.

**Fix**: Defensively bind 2–3 default-model env-var names on the agent. After a successful chat smoke-test, prune to the one the framework actually honored.

```
ZEROCLAW_DEFAULT_MODEL=<id>     # framework-specific (ZeroClaw)
OPENAI_DEFAULT_MODEL=<id>       # OpenAI SDK convention
MODEL=<id>                      # generic
```

### P3. Failed deploys leave the VM unreachable; subsequent retries make it worse

**Pattern**: After a failed template-source deploy, `chat` returns `fc-manager 404 .../proxy {"detail":"VM not found"}` or `Circuit breaker open — container recently unreachable` — even after `env reload` says `reloaded:true`. Status API still says `active` because the registry entry exists.

**Why**: The platform's fc-manager (Firecracker controller) tracks VM lifecycle across deploy attempts. A failed docker pull leaves the VM entry orphaned; status still shows active; reload only restarts the framework *inside* the existing VM, which doesn't exist.

**Fix** (in preference order):
1. Wait ~5–10 minutes for the circuit breaker to reset, then retry chat.
2. `maritime delete --yes <agent>` — requires `manage` scope on the mk_ key. See P6.
3. Create a NEW agent with a different name; re-link the workdir; re-set every env var.

**Most important**: **don't retry the failing deploy blindly**. Each retry thrashes the VM lifecycle, which is what extends the recovery window from minutes to hours.

### P4. `maritime chat` has no `--model` flag — env-vars are the only override path

**Pattern**: The chat CLI accepts `agent` + `message`; no per-call model override knob.

**Fix**: Set the default model via env vars (P2). For per-model tests in CI, prefer direct `curl` to Venice over the maritime CLI chat.

### P5. Without `OPENAI_API_KEY`, the platform injects its own proxy token → all chat routed through platform gateway

**Pattern**: After setting `VENICE_INFERENCE_KEY`, chat still produces responses routed through the platform's LLM gateway (slow, with the platform's rate limits, unable to use provider-native features).

**Why**: The platform's wrapper injects a credentials block when no `OPENAI_API_KEY` is supplied.

**Fix**: Mirror the provider API key into `OPENAI_API_KEY`, and set `OPENAI_BASE_URL` to the provider's URL.

### P6. mk_ token `cli` scope cannot delete agents; recreate is the recovery path

**Pattern**: `maritime delete --yes my-agent` → "This API key lacks the 'manage' scope required for this action. status: 403".

**Why**: API key scopes are not auto-promoted. `cli` has `create / list / env / chat / logs`. `manage` adds delete and lifecycle operations.

**Fix**: Recreate with a new name and migrate. Or rotate to a `manage`-scoped mk_ key via `maritime keys create`.

### P7. `env reload` returns `reloaded:true` but chat still 404s — different problem

**Pattern**: After 3+ failed deploys, `maritime env reload` says `reloaded:true` but chat remains broken.

**Why**: Reload restarts the framework *inside* the existing VM. If the VM itself is gone, reload can't bring it back. Reload ≠ recreate.

**Fix**: Recreate (P3 #3) or wait for the circuit breaker (P3 #1).

### P8. Multi-role MD confuses framework loader

**Pattern**: A single `INSTRUCTIONS.md` mixes "you are an agent that…" with "for the operator, here's how to…" and the framework loader becomes ambiguous.

**Why**: Framework loaders (e.g. ZeroClaw) typically scan for a defined set of MDs (`AGENTS.md`, `PROMPT.md`). Operator-only files should be excluded from the load path explicitly.

**Fix**: Persona in `AGENTS.md` only. Operator notes in `CLAUDE.md` only. System template in `PROMPT.md` only. State in `STATE.md`. Aux prompts in `prompts/`.

### P9. Out-of-band operator hints are URL-form, not full commands

**Pattern**: User sends `https://api.venice.ai/api/v1` mid-turn as a hint about provider base URL, not as a request to call that URL.

**Fix**: Treat OOB URL hints as configuration instructions. Apply to the agent's `OPENAI_BASE_URL` and mirror the value across the workdir's `maritime.json` provider block, `zeroclaw.toml [provider].base_url`, and `PROMPT.md` frontmatter `baseUrl:`.

## Verification matrix

| Check | Expectation |
|---|---|
| `maritime status <agent>` | `active`; framework + tier match the user's spec |
| `maritime env list <agent>` | Every key in `.env.example` is present; secrets show `****<last4>`; values you care about (e.g. `OPENAI_BASE_URL`) plain |
| `maritime chat <agent> "which model are you?"` | Real reply; content styled by expected model register |
| `maritime logs <agent> -n 10` | One or more "Agent deployed and running" lines; no `error` markers at last deploy |

If any of the above fails, cross-reference the pitfall table before tweaking the env.

## See Also

- `references/maritime-cli.md` — full command reference, auth-quirk catalog (P1, P6), deploy-source modes, the Venice default-model caveat (P2), fc-manager error map (P3, P7), env reload vs recreate.
- `templates/maritime.json` — operator schema scaffold showing all binding slots (name, framework, tier, defaultModel, provider, env registration, autoPair).
- `templates/zeroclaw.toml` — ZeroClaw framework TOML scaffold (`[gateway]`, `[provider]`, `[provider.fallback]`, `[memory]`, `[playbook]`, `[runtime]`).
