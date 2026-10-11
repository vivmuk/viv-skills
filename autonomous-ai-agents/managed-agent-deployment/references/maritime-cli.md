# maritime CLI quick reference + quirk catalog

Companion to `managed-agent-deployment/SKILL.md`. This file is platform-specific: it captures maritime CLI behavior, error strings, scope metadata, and per-framework env-var conventions. For the agent-platform general pattern (any serverless agent CLI), use the skill's workflow + pitfall table.

## Top-level commands

```bash
maritime --help                                   # show all subcommands
maritime guide                                     # machine-readable usage manifest
maritime guide --json                               # same, JSON form (best for AI agents)
maritime whoami                                    # token source + scope + expiry

maritime login                                     # interactive (browser flow)
maritime login --token <mk_…>                      # headless via flag (often client-rejects — see P1)
maritime logout

maritime keys create                               # mint a new mk_… key
maritime keys list

maritime create -n <name> -t <fw> --tier <tier>    # create an agent
maritime init [name] [--framework <fw>] [--tier <tier>] [--no-create]
maritime link [<agent>]                            # attach current dir to an agent
maritime deploy [<agent>] [--source <mode>] [--wait]
maritime unlink                                    # detach current dir

maritime list
maritime status [<agent>]
maritime delete [<agent>] --yes                    # requires manage scope (P6)
maritime open [<agent>]                            # web dashboard

maritime env list [<agent>]
maritime env set [<agent>] KEY=VAL [--no-secret] [--reload]
maritime env import [<agent>] <file> [--reload]     # bulk-load from a .env file
maritime env pull [<agent>] <file>                 # reverse: write agent env to local file (secrets masked)
maritime env remove [<agent>] KEY
maritime env reload [<agent>]                      # hot-reload env into running container

maritime chat <agent> "<message>"                  # note: NO --model flag (P4)
maritime chat -a <agent> "<message>"               # override linked-dir default
maritime chat --json                               # print raw response

maritime logs <agent> [-n 50] [--json]
```

## Token scopes

`mk_…` API keys carry scopes:

| Scope | Operations |
|---|---|
| `cli` (default) | create, list, init, link, deploy, env, chat, logs, status |
| `manage` | add: delete, lifecycle, recover-broken-VM operations |

To check what scope a key has: `maritime whoami` → look for `scopes`.

**Shell token env-var**: `MARITIME_TOKEN=<key>`.

The CLI's `login --token` flag has stricter client-side validation than the server. The server accepts the same mk_… token. Always use the env-var route in headless/AI-agent flows.

## Tiers

| Tier | Cost (approx.) | Liveness |
|---|---|---|
| `smart` | $1/mo | idle-sleep; ~1-3s first-wake latency |
| `extended` | $10/mo | warm pool; sub-second |
| `always_on` | $30/mo | continuous; no idle |

Default to `smart` unless the user has a reason otherwise.

## Frameworks (Maritime)

| Framework | Image | Notes |
|---|---|---|
| `zeroclaw` | `ghcr.io/zeroclaw-labs/zeroclaw:debian` | Lightweight Rust binary; OpenAI-compatible gateway on port 42617; `ZEROCLAW_GATEWAY_PASSWORD` auto-injected. |
| `openclaw` | per platform | More features; has Identity / Browser subvariants. |
| (others) | per platform | Per platform docs. |

## Auto-injected env on agent (ZeroClaw)

| Key | Source | Type |
|---|---|---|
| `ZEROCLAW_GATEWAY_PASSWORD` | maritime auto-generated | secret |
| `ZEROCLAW_HEADLESS=true` | maritime wrapper | plain |
| `ZEROCLAW_ALLOW_PUBLIC_BIND=true` | maritime wrapper | plain |
| `ZEROCLAW_GATEWAY_PORT=42617` | maritime wrapper | plain |
| `ZEROCLAW_WORKSPACE=/zeroclaw-data/workspace` | maritime wrapper | plain |
| `OPENAI_BASE_URL=https://api.maritime.sh/api/llm/v1` | DEFAULT maritime proxy (overwrite to point at custom provider) | plain |

To route through a custom provider (e.g. Venice):
1. Override `OPENAI_BASE_URL=https://api.venice.ai/api/v1` (plain)
2. Mirror provider key into `OPENAI_API_KEY` (secret)
3. Bind default-model env vars defensively (P2)

## Default model env-var candidates (ZeroClaw)

The framework reads ONE of these names for its default model. Pick defensively; prune later after smoke-test.

```
ZEROCLAW_DEFAULT_MODEL=<id>     # framework-specific (ZeroClaw)
OPENAI_DEFAULT_MODEL=<id>       # OpenAI SDK convention
MODEL=<id>                      # generic
```

## Common errors + recovery

### `Error: that does not look like a valid token. Copy a fresh one from https://maritime.sh/cli/auth`

Client-side `maritime login --token` validation rejects the key. Same token works through the env-var route. Switch to:

```bash
export MARITIME_TOKEN=<mk_…>
maritime list --json     # expect: [] or actual agent list, NOT 401
```

### `Deploy failed: fc-manager 500 … pull access denied for maritime-agent-{name}`

Template-source deploy tried to pull a registry image that doesn't exist. Recovery:
1. Push the workdir to a GitHub repo, then `maritime deploy --source github --repo https://github.com/<u>/<r>`.
2. Or rebuild the workdir with `--no-create` history (a brand-new init with the same content works).
3. Or recreate the agent with a different name.

**Repeated retries cause VM lifecycle thrash — do not just retry.** See P3 in the umbrella skill.

### `fc-manager 404 for /vms/<id>/proxy {"detail":"VM not found"}`

VM registry entry exists but the actual VM is gone. Status API still says `active` because the entry exists. Recovery in order of preference:
1. Wait 5–10 minutes for circuit breaker to clear.
2. `maritime delete --yes <agent>` (requires `manage` scope). See P6.
3. Create a new agent (different name), re-link, re-set env, re-deploy with `--source github`.

### `fc-manager 409 for /vms {"detail":"VM … already exists"}`

Concurrent deploy attempts collapsed onto a single VM slot. Same recovery as above.

### `Circuit breaker open — container recently unreachable`

Status API accepts requests but chat proxy blocks. Wait ~2 minutes and retry chat.

### `Unauthorized — This API key lacks the 'manage' scope required for this action. status: 403`

mk_ key has `cli` scope, not `manage`. Cannot delete or perform lifecycle operations on the agent. Recreate with a different name and migrate. Or rotate to a `manage`-scoped mk_ key via `maritime keys create`.

### `Agent is in error state. Please redeploy or check the agent logs.`

Status API reports `error`. Check `maritime logs <agent> -n 50`. Common cause: a previous failed deploy broke the VM state. Apply the P3 recovery recipe.

## Venice default-model caveat (P2)

Venice's `/v1/chat/completions` family-picks `llama-3.3-70b` when no `model` is in the body. To verify:

```bash
# list live models
curl -sS -H "Authorization: Bearer *** https://api.venice.ai/api/v1/models \
  | python3 -c "import json,sys; m=json.load(sys.stdin)['data']; print([x['id'] for x in m if 'glm' in x['id']][:10])"
```

Or with the env-var route:

```bash
source ~/.maritime-token.env
# (use the agent's VENICE_INFERENCE_KEY if you've stored it locally as ~/.venice-key.env)
```

If a framework's chat path drops the `model` parameter, the agent's reply will look like llama70b even if env vars name a different model. Defensively bind 2–3 default-model env-var names (see list above). After a successful chat smoke-test, prune to whichever var the framework actually honored.

## Workspace persistence

`.maritime/project.json` (git-ignored) inside the workdir maps the current directory to an agent. Re-running `maritime link <other-agent>` rebinds.

The persistent state of edited MDs / TOMLs lives **outside** agent containers (containers are ephemeral). If you care about long-term continuity, **commit and push the workdir to git** before any recover-via-recreate cycle.

## Channel integration

Agents with `hasWebUi: true` have a web dashboard accessible from the platform UI. `maritime chat` is the terminal-side smoke-test; the dashboard is for browser-based interaction incl. ZeroClaw's native web UI.

## mk_ key rotation

```bash
# create a new key (recommended to keep separate keys per environment)
maritime keys create --json
# typically returns: {"mk_…"} — copy to your secrets manager
```

Rotate out old CLI-scoped keys once you have a `manage` key in place, so the old key can't be replayed from history files.

## Free-tier / billing sanity

`maritime status <agent>` returns `usage` data:
- `totalComputeSeconds` — cumulative compute time
- `invocationCount` — chat invocations / chat triggers
- `lastStartedAt`, `lastActiveAt` — liveness logs

Use these to spot idle agents still accruing cost. Delete or stop agents that have been quiet > 30 days.
