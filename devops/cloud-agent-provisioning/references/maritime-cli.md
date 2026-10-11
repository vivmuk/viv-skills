---
# maritime-cli cheat sheet

This is a **session-derived** reference. It mirrors the commands and shapes we
have actually used on maritime.sh, with the gotchas we hit. For the
authoritative commands run the CLI's `--help` and consult
https://maritime.sh/docs/cli and https://maritime.sh/docs/frameworks/zeroclaw (or
relevant framework).

## Install

```
npm install -g maritime-cli     # lands in ~/.hermes/node/bin/maritime on Hermes
maritime --version              # 1.5.1 as of 2026-07-08
```

## Login — *use the env-var route, not `login --token`*

| Path | Works? | Notes |
|---|---|---|
| `maritime login` (interactive browser) | OK in TTY | Opens browser to maritime.sh/cli/auth |
| `maritime login -e user -p pass` | OK | For non-SSO accounts |
| `maritime login --token mk_…` | ❌ CLIENT VALIDATOR TOO STRICT | Honest mk_... keys from `maritime keys create` get rejected with *"that does not look like a valid token"* even when the server accepts them |
| `MARITIME_TOKEN=mk_… maritime list --json` | ✅ WORKS | Bypass `maritime login` entirely on headless servers / SSH / CI |

**Canonical pattern:** put the token in `~/.config/maritime/maritime-env.sh`
(mode 0600) and source it before running maritime commands. Server-side
validation is the source of truth; the CLI's local validator can be wrong
without the server being wrong.

```bash
cat > ~/.config/maritime/maritime-env.sh <<'EOF'
export MARITIME_TOKEN=$(< "$HOME/.config/maritime/token")
EOF
chmod 600 ~/.config/maritime/maritime-env.sh ~/.config/maritime/token
source ~/.config/maritime/maritime-env.sh
# Verify
maritime list --json
```

## Tier + framework matrix

| Tier | Price | Use |
|---|---|---|
| `smart` | $1 / mo | Default, serverless Firecracker VM, auto-sleep on idle |
| `extended` | $5 / mo | More memory / awake window |
| `always_on` | $10 / mo | Never auto-sleep |

| Framework | Profile | Env vars it reads (in addition to `ZEROCLAW_GATEWAY_PASSWORD` if ZeroClaw) |
|---|---|---|
| `openclaw` | Default OpenClaw template | openclaw internals + `OPENAI_API_KEY` / `OPENAI_BASE_URL` |
| `hermes` | `nousresearch/hermes-agent` plugin image | `HERMES_INFERENCE_PROVIDER`, `HERMES_INFERENCE_MODEL`, `OPENAI_API_KEY` (falls back to OpenRouter) |
| `zeroclaw` | Single Rust binary, <5 MB RAM, OpenAI-compatible gateway | `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` (OpenAI-compatible provider) |

If you don't supply `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` for ZeroClaw, Maritime
injects a per-agent proxy token pointed at `https://api.maritime.sh/api/llm/v1`.
To bypass the proxy and talk to Venice directly:
`maritime env set <agent> OPENAI_BASE_URL=https://api.venice.ai/api/v1 --no-secret --reload`
and mirror your Venice key into `OPENAI_API_KEY`.

## Create

```
maritime create -n my-agent -t zeroclaw --tier smart --json
# { ok: true, framework: "zeroclaw", tier: "smart", status: "deploying", ... }
```

If the user says "Hermes agent," use `--template hermes`. Don't auto-substitute
OpenClaw for ZeroClaw or back without telling the user — framework choice
cascades into which env vars the container reads at boot.

## Deploy (after create)

For the bare frameworks: `maritime deploy my-agent --wait`. For image or repo
sources:

```
maritime deploy my-agent --source github --repo https://github.com/user/repo
maritime deploy my-agent --source docker --image myimage:latest
```

If `status` flips between `deploying → active` repeatedly with no progress, the
control plane has an upstream issue. Bound retries to 3–5 then defer to user.

## Env injection (the right way)

```
# One secret, secret+encrypted by default
maritime env set my-agent OPENAI_API_KEY=*** --json
# → { uploaded: ["OPENAI_API_KEY"], failed: [], reloaded: false }

# Multiple secrets at once
maritime env set my-agent OPENAI_API_KEY=*** VENICE_INFERENCE_KEY=*** --json

# Bulk import from a .env file
maritime env import my-agent ./prod.env --reload --json

# Non-secret (visible in `env list` unmasked)
maritime env set my-agent OPENAI_BASE_URL=https://api.venice.ai/api/v1 \
  --no-secret --reload --json

# Hot-apply to a running agent without restart
maritime env reload my-agent --json
```

`maritime env list my-agent --json` shows masked values; secrets stay `****…`
although the secret prefix (last 4 chars) shows for some entries.

## Status / info / logs

```
maritime status my-agent            # active / deploying / sleeping / error
maritime info my-agent --json       # full record (env keys + framework + image)
maritime logs my-agent -n 100       # lifecycle + request logs
maritime logs my-agent --level error
maritime logs my-agent -f           # follow
```

Useful diagnostic shortcuts:

```
# Cheap health probe
maritime status my-agent --json | jq '.status,.tier,.framework'

# Was the agent alive in the last hour?
maritime status my-agent --json | jq -r '.lastActiveAt'

# Memory + compute usage
maritime info my-agent --json | jq '{mem:.memMb, vcpu:.vcpus, idleTTL:.idleTtlSeconds}'
```

## Chat smoke-test

```
maritime chat my-agent "Reply with exactly OK if you can hear me." --json
# → { ok: true, response: "OK" }

# Long prompts via stdin
cat prompt.txt | maritime chat my-agent --json

# Multi-turn
maritime chat my-agent "and the one before?" --conversation-id abc123 --json
```

**Empty-response shape (`ok: true, response: ''`)** is a known shape on freshly-
spawned ZeroClaw agents before any chat logic is configured. The framework is up
(status flips to `active`) but the chat path returns nothing until you wire a
provider. Don't treat empty as a wire-up bug — open the agent's dashboard
(`maritime open my-agent`) and chat there for the canonical path, or wire
`OPENAI_BASE_URL` + `OPENAI_API_KEY` to a working provider and retry.

## Exit codes

```
0  success
1  generic / network
2  auth (no token / expired / wrong)
3  not found (no such agent)
4  usage (invalid args)
```

Use these in CI / scripts. Prefer `maritime … --json` for stderr-clean error
parsing:

```
reply=$(maritime chat my-agent "status?" --json 2>/dev/null | jq -r .response) || {
  echo "maritime chat failed (exit $?)" >&2
  exit 1
}
```

## Cost-fleet creation

For a swarm-of-N:

```
maritime create swarm --template openclaw --count 5 --idle 3600 --json
# Names become swarm-1 … swarm-5; each bills $1/mo from your wallet;
# exit 0 = all created, 1 = partial or none.
```

Per-agent resource overrides (rare):

```
maritime create acme-bot --ram 2048 --cpu 1.5 --idle 600 --disk 20
maritime create always-up --always-on --max-compute 120
```

## Keys (rotate, revoke)

```
maritime keys list
maritime keys create                 # mint a new mk_… token
maritime keys revoke <id>            # revoke with the *new* token
```

If a token leaks, mint a fresh one *first*, then revoke the leaked one with the
fresh token. Revoking with the leaked token silently fails.

## Triggers

```
maritime triggers my-agent           # list cron/webhook/email/telegram/discord
```

## Common patterns in this repo

- *Hermes on maritime → Venice backend:* `references/hermes-venice-on-maritime.md`
- *ZeroClaw → Venice direct:* see the `templates/zero-claw-venice-deploy.sh` for
  the ready-to-sourced chain.
- *Recovery loop:* `templates/recovery-deploy-loop.sh`.
- *Self-hosted alternative:* `devops:self-hosted-agent-deployment`.

## Quirks worth remembering

| Quirk | Why it bites | Working pattern |
|---|---|---|
| `login --token <mk>` rejected | CLI client-side validator | Use `MARITIME_TOKEN` env var directly |
| Tier change is sticky | No easy monthly rollback | Confirm tier before sign-in |
| `maritime env list` masks secrets | Useful for audit, unhelpful for debugging chat-path issues | Use `maritime info` to *see* which key names exist |
| Auto-pair warnings during deploy are boot noise | `auto-pair burst sweeper` 500s in logs are normal | Don't loop; deploy is still successful if `status` flips to `active` |
| Empty chat reply on ZeroClaw | Fresh agent has no chat persona | Wire OPENAI_BASE_URL + OPENAI_API_KEY or use the dashboard |
| Server often HAMMERS the same 5xx across 30 s | Upstream dependency outage | Report to user with evidence, don't loop |

