---
name: cloud-agent-provisioning
description: Provision and operate an AI agent on a hosted agent SaaS (Railway.sh, maritime.sh, Render, Fly.io, Modal, Daytona, Replicate, etc.). Use when the user wants "host my agent", "deploy to Railway/maritime/Render", "managed agent", or a Hermes/OpenClaw-style agent reachable as a service without owning the underlying VM. NOT for self-hosted setups (use devops:self-hosted-agent-deployment) and NOT for local CLI-only agents (autonomous-ai-agents:openclaw or hermes-agent). For Railway-specific CLI recipes (link syntax, restart confirmation, ssh quirks), see references/railway-cli-notes.md. For Hermes-on-Railway runtime state anatomy (SOUL.md, memories/, entrypoint copy semantics), see references/hermes-on-railway-runtime-state.md.
---

# Cloud Agent Provisioning

Operate an AI agent living on a *third-party hosted agent platform* rather than on the user's own VM. The platform owns the VM, the gateway, the dashboard, the channel pairing, and the metering; you bring the persona config, secrets, and the upstream model provider.

## When to use

- User says *deploy my agent to maritime / hosted service / a SaaS platform*, *run this 24x7*, *spin up a fleet*, or *I need a second agent running on a different profile*.
- A class of work exists: install platform CLI > auth > create agent from a template > inject secrets securely > deploy > smoke test via platform's chat endpoint > monitor.
- **NOT** for: self-hosting on the user's own VM (`devops:self-hosted-agent-deployment`); backups (`devops:ai-agents-nightly-backup`); changing the **local** OpenClaw/Hermes install (`autonomous-ai-agents:openclaw` / `hermes-agent`).

## Anchoring scan — read these first

Confirm what agent runtime is involved BEFORE provisioning:

- **Local OpenClaw on the user's machine** (e.g. Paridhi): the user's existing `~/.openclaw/openclaw.json` is the source of truth. The cloud-side Hermes container does NOT affect the local OpenClaw.
- **Hermes (`nousresearch/hermes-agent`)**: cloud container reads `HERMES_INFERENCE_PROVIDER`, `HERMES_INFERENCE_MODEL`, and falls back via OpenRouter to `OPENAI_API_KEY`. Working setup details in `references/hermes-venice-on-maritime.md`.
- **ZeroClaw (Rust, <5MB)**: smaller memory footprint, useful fallback when the heavier template fails.

Template choice drives what env vars the container reads. Always cross-check with the platform's framework page before injecting vars.

## Workflow

1. **Store the platform token and any model-provider keys as chmod-600 files first.** Never let the key text appear on a command line. Locations: `~/.config/<platform>/<key_file>` (with `0600` dir mode) plus macOS keychain as backup via `security add-generic-password -a <slug> -s <service> -w "$(< /path/key)" -U`.
2. **Read the platform CLI's existing docs page** (`/docs/cli`, `/docs/frameworks/<template>`, `/docs/api/provisioning`) BEFORE installing. Confirm: install command, login command, template IDs, env-var shape, tier options, and the env-import path.
3. **Install the platform CLI.** Usually `npm i -g <pkg>`. On Hermes's bundled node/npm, install lands in `~/.hermes/node/bin/<cli>` with no sudo needed.
4. **Authenticate non-interactively.** Prefer a sourced env-loader script (`source ~/.config/<platform>/env.sh`) over `login --token <literal>` on argv.
5. **Pick the template that matches the user's explicit ask, not a vague fallback.** When user says "Hermes agent," use `--template hermes`; only fall back to a smaller template after the named one fails to provision repeatedly AND the user agrees.
6. **Inject secrets via the platform's file-import path** (`<cli> env import <file>`). Never pass `-e KEY=value` on argv with a literal secret.
7. **Deploy with bounded retries.** Hosted agent platforms frequently fail the first deploy with HTTP 500/409 from their VM provisioner — usually transient, recovers on 30–60s backoff. Bound to 3–5 attempts then defer to the user.
8. **Once `status` flips to `active` / `ready` / `running`, smoke-test via the platform's chat endpoint.** If the chat endpoint returns "Circuit breaker open" right after deploy, that's the platform's self-throttle — wait ~60s and retry once.
9. **Save an idempotent recovery script** so a failed deploy can be replayed late at night or after upstream recovery. Both the recovery script and the env-loader MUST use file-based env loading — never raw key on argv.

## Pitfalls

- **`export VAR=<placeholder> $(< /path)` is a bash trap.** Combining a placeholder literal with command substitution is two tokens, not one. Bash emits error messages that *will* contain whatever the substituted value was. **Use one of:**
  - `export VAR=$(< /path/file)`  — bash's single-token file slurp, no cat subprocess
  - `export VAR=$(cat /path/file)` — `cat` subprocess, OK as long as the FILE PATH is the only thing on argv
  - `source <env-loader.sh>` — load from an existing file that does the assignment internally

  See `references/secure-env-injection.md` for the full taxonomy.

- **Don't keep failed deploys cycling in the account.** When a deploy truly fails for upstream reasons and you've decided to defer to the user, leave the slot alone so the user can investigate, or `delete --yes` to clean up. Cycling through delete-recreate burns audit trail.

- **Security: the platform token is high-value.** If the platform supports `keys list`, `keys create`, `keys revoke`, rotate *immediately* on any exposure. Mirror the new token, then revoke the old **using the new token** (revoking with the leaked token silently fails).

- **Container-level warning logs are normal boot noise**, not failures. `EXT4 mounted`, `ChaCha RNG init done`, `auto-pair burst sweeper`, etc. all appear in the `<container>` block — that's the kernel/init phase. The `<system>` block is where deploy failures show up.

- **Don't echo secret strings as test fixtures.** `echo "KEY=${#VAR}"` is fine — length is not sensitive. `echo "KEY=$VAR"` is not.

- **The platform you used may have upstream outages** you'll only see in `logs <agent>`. When the same 500/409 repeats more than 3 times in 5 minutes from the same `X.Y.Z.W:N` endpoint, the platform has a known upstream dependency issue. Report to the user with the evidence — do not loop on retry.

- **OneDrive / iCloud mounted via FUSE filters** can hang sub-directory writes (`EDEADLK`) during your recovery attempts. Pre-create a local mirror directory and have the launcher auto-detect.

- **`maritime login --token` rejects valid mk_… keys client-side.** The CLI runs a local format check on the token before sending it to the server; tokens minted by `maritime keys create` (the documented headless path per the docs at `/docs/cli`) can return `Error: that does not look like a valid token` even though the same key string works fine as `MARITIME_TOKEN=… maritime list --json`. **Working pattern:** skip the `login` step and source the token via an env-loader script (`source ~/.config/maritime/maritime-env.sh`). The server accepts without complaining; the local CLI validator does not. Save time by going straight to the env-var route on headless/server/CI hosts.

- **Framework picker matters — `OpenClaw / Hermes / ZeroClaw` are separate templates with different env-var contracts.** Don't auto-fall-back from one to the next: each reads different env vars at boot, and ZeroClaw (single Rust binary, <5 MB) is the lighter option. Confirm with the user before substituting; template choice cascades into which `OPENAI_API_KEY / ANTHROPIC_API_KEY / HERMES_INFERENCE_*` vars the container reads at runtime.

- **`maritime env set` is secret+encrypted by default.** Strip `--no-secret` for any value that's truly a secret (API keys, tokens). Plain env vars should explicitly carry `--no-secret` so they don't get marked secret by accident and stay masked in `maritime env list`. The default-vs-flag inversion is the kind of foot-gun that masks endpoints you actually want to inspect.

- **`maritime env set … --reload` hot-applies env to running agents; without it, changes apply on the next container boot.** Useful for reaching a deployed agent that you don't want to redeploy just to swap an API key. Pair with `maritime status <agent>` to confirm the agent restarted cleanly post-reload (a string of consecutive "Agent restarted" log lines is the expected pattern — not an error).

- **Tier / pricing reminder when the threshold matters.** smart = $1 / mo, extended = $5 / mo, always_on = $10 / mo. If the user is provisioning a fleet, get the tier right before they sign in; there is no easy monthly rollback. Default for unknown is smart.

- **maritime.sh is the canonical example in this skill, but the Workflow section is platform-agnostic.** Any hosted-agent SaaS that owns the VM, gateway, dashboard, channel pairing, and metering (Railway.sh, Render, Fly.io, Modal, Daytona, Replicate) follows the same shape: install CLI > auth > create/import > env-inject > deploy > smoke-test via the platform's chat endpoint. When the user names one of these instead of maritime, this is still the right home. **Platform-specific CLI recipes live in references files, not the Workflow section** — Railway.sh requires `railway link --project <id>` (positional doesn't work), `railway restart --service X --yes` for non-interactive cycles, and tolerates the CLI timing out at 60 s on restart even after the container has cycled. See `references/railway-cli-notes.md`. For runtime-state anatomy on a deployed Hermes (where SOUL.md lives, what entrypoint re-copies on every start), see `references/hermes-on-railway-runtime-state.md`.

- **A deployed Hermes instance is single-profile, NOT profile-aware.** The `hermes profile create|rename|delete` CLI machinery in `autonomous-aiagents/hermes-agent` creates profiles under `~/.hermes/profiles/<name>/` — that's the *local CLI* multi-profile pattern. A **deployed** Hermes (Railway container, maritime VM, any Docker) uses a single profile rooted at `$HERMES_HOME` and expresses identity through `SOUL.md`, NOT a separate profiles subtree. Future agents looking to inspect or reset a deployed agent's personality should search for `SOUL.md` and `memories/MEMORY.md / USER.md` first; searching for `profiles/<name>/` returns nothing useful. Cross-reference: `references/hermes-on-railway-runtime-state.md`.

- **Railway env vars do NOT override the gateway's runtime config.** On a Hermes-on-Railway deployment, `entrypoint.sh` re-copies `/app/hermes/cli-config.yaml` → `~/.hermes/config.yaml` on every boot. The **gateway process reads `~/.hermes/config.yaml`** (not `.env`), so the model/provider/mcp_servers/platform_toolsets blocks are image-baked. Railway env vars DO flow into `~/.hermes/.env` (CLI loader, hermes-cli and CronJob use), but they do NOT change the live gateway. `railway variable set OPENAI_DEFAULT_MODEL=X` will leave the running bot unchanged until the next `railway up` rebuilds with a new cli-config.yaml. To hot-swap a model, MCP server, or toolset, edit the source-tree `hermes/cli-config.yaml` and rebuild. See `references/hermes-on-railway-runtime-state.md` for the full config-triad map (config.yaml vs .env vs cli-config.yaml) and `references/hermes-mcp-on-railway.md` for the worked MCP-from-source recipe.

- **`hermes-agent[mcp]` is required for stdio MCP servers in Docker.** `pip install hermes-agent` alone gives the wheel but not the `mcp` Python SDK — `hermes mcp list` shows tools discovered, but every tool call fails with "MCP server X requires the 'mcp' Python SDK". Use `pip install 'hermes-agent[mcp]'` (or `[all]`) in the Dockerfile; see `references/hermes-mcp-on-railway.md`.

## Reference docs and templates

- `references/maritime-cli.md` — maritime.sh v1.4.0 CLI cheat sheet covering install, login, create, env-set/import/list, deploy, status, logs, chat, keys.
- `references/railway-cli-notes.md` — Railway.sh CLI gotchas for agents (not humans): `link` requires `--project` not positional; `status` is project-level post-link and ignores `--service`; `restart` needs `--yes` and may exit 124 even on success (verify via `sleep 30 && railway status`); ssh sessions lack `ps`/`lsof` so use `/proc/<pid>/{cmdline,comm}`; team/project disambiguation via `railway list --json`.
- `references/hermes-on-railway-runtime-state.md` — anatomy of a deployed Hermes-on-Railway instance: where identity (SOUL.md) lives vs skills (skills/), the entrypoint copy semantics that re-bake `/app/hermes/SOUL.md` → `/root/.hermes/SOUL.md` on every start, memories/ structure, the surgical-wipe procedure that resets personality to default Hermes while preserving skills/sessions/config/.env. Companion also exposes the **"deployed = single-profile, NOT profile-aware"** mental model that protects future agents from searching for `profiles/<name>/` that doesn't exist. Pairs with **references/hermes-mcp-on-railway.md** (the worked recipe for stdio MCP from source: token-via-env, Dockerfile `[mcp]` extra, entrypoint `export`, cli-config.yaml bake, `hermes mcp test` as the actual integration test).
- `references/secure-env-injection.md` — generic pattern for injecting secrets into CLI tools. Includes the bash-substitution trap taxonomy and four working patterns.
- `references/hermes-venice-on-maritime.md` — the specific working config for Hermes Agent on maritime.sh with Venice inference (`OPENAI_API_KEY`, `OPENROUTER_BASE_URL`, `HERMES_INFERENCE_MODEL`). For Railway, the same env-var contract works because the underlying cloud-harness build of hermes-agent reads `OPENAI_API_KEY`/`OPENAI_BASE_URL`/`OPENAI_DEFAULT_MODEL` at boot — see `references/railway-cli-notes.md` for the `railway variables` shape.
- `templates/maritime-env-loader.sh` — safe env-loading snippet. **TEMPLATE NOTE:** the `MARITIME_TOKEN=` and `VENICE_API_KEY=` assignment lines in this template currently carry a broken two-token concatenation pattern (`KEY=<literal> $(cat "$FILE")`) that LOOKS LIKE but is NOT bash's file slurp. Until patched, the canonical replacement is bash's single-token file slurp: `<literal> appended directly to a leading shell-only construct — see `references/secure-env-injection.md` Pattern A for the full taxonomy.
- `templates/recovery-deploy-loop.sh` — idempotent bounded retry + status-polling + smoke-test scaffold. (Same template-bug caveat applies to any `$(< "$FILE")` substitution on the env-loading lines.)
- `templates/zero-claw-venice-deploy.sh` — zero-claw variant deploy script (Venice inference, lighter footprint).
- `scripts/probe-cloud-backend-health.sh` — quick health probe for maritime.sh's control plane and VM provisioner. Clean and directly runnable.

## Daily-driver cheat-sheet

```
# Source the env loader (safe; never types keys)
source ~/.config/maritime/maritime-env.sh
printf "MARITIME_TOKEN=%d chars  VENICE_API_KEY=%d chars\n" \
  "${#MARITIME_TOKEN}" "${#VENICE_API_KEY}"

# Replay the recovery deploy
~/.config/maritime/<agent>-deploy.sh

# Manual loop
while true; do
  maritime deploy <agent> --json 2>&1 | grep '"status"'
  s=$(maritime status <agent> --json | python3 -c "import sys,json; print(json.loads(sys.stdin.read()).get('status','?'))" 2>/dev/null)
  [ "$s" = "active" ] && break
  sleep 60
done
maritime chat <agent> "Reply with exactly OK if you can hear me."
```
