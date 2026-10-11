# Adding an MCP server to a Hermes-on-Railway deployment

Worked recipe for installing a stdio MCP server (GitHub, Linear, Notion, filesystem, etc.) onto a Hermes agent deployed on Railway.sh. Companion to the umbrella `cloud-agent-provisioning` skill.

Why this file exists: the native-mcp skill (`mcp/native-mcp/SKILL.md`) covers the **local** install path — drop `mcp_servers.X` into `~/.hermes/config.yaml` and restart. On a **deployed** Railway instance, two extra things break that recipe, and both have burned me on real deploys:

1. The gateway's runtime config doesn't read `~/.hermes/.env`; it reads `~/.hermes/config.yaml`, which is **re-baked from `/app/hermes/cli-config.yaml` on every container start**. So adding an MCP server in the volume doesn't survive the next `railway up` — you have to bake it into the source.
2. `hermes-agent` wheel does NOT include the `mcp` Python SDK. Discovery succeeds over `npx`, but every tool call fails with `Connection failed: MCP server 'X' requires the 'mcp' Python SDK`. The Dockerfile must install `hermes-agent[mcp]`, not `hermes-agent` alone.

## The full recipe (worked example: GitHub MCP on Jiva + Rati, 2026-07-17)

### Step 1 — Token via Railway env var, never in source

Read the token from your local keyring (suggested: macOS keychain or `gh auth token`), pipe to Railway stdin to keep it out of shell history:

```bash
gh auth token | railway variable set GITHUB_PERSONAL_ACCESS_TOKEN \
  --project <proj> --environment production --service <svc> --stdin
```

Verify (value gets redacted in CLI output):

```bash
railway variables --service <svc> --json | jq '.<name> | length'  # length, not the value
```

Other token env-var conventions MCP servers expect: `GITHUB_PERSONAL_ACCESS_TOKEN` (GitHub), `LINEAR_API_KEY`, `NOTION_TOKEN`, etc. Keep them in Railway env, never inline in source code or image.

### Step 2 — Dockerfile: install `hermes-agent[mcp]`

Edit the project source's `Dockerfile`:

```dockerfile
ARG HERMES_VERSION=
RUN if [ -n "${HERMES_VERSION}" ]; then \
        pip install --no-cache-dir "hermes-agent[mcp]==${HERMES_VERSION}"; \
    else \
        pip install --no-cache-dir "hermes-agent[mcp]"; \
    fi
```

The `[mcp]` extra pulls the `mcp` Python SDK alongside the hermes-agent wheel. **Without the extra, hermes-agent alone will satisfy discovery but break every tool invocation.** Don't try to compensate with a separate `pip install mcp` line — it gets blown away on the next hermes-agent wheel upgrade, so you're back to discover-but-don't-invoke.

Also confirm Node.js is in the image (most stdio MCP servers are npm packages launched via `npx`). The default `python:3.13-slim` doesn't include it. Add:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl bash git nodejs npm build-essential tini ca-certificates \
    && rm -rf /var/lib/apt/lists/*
```

### Step 3 — `entrypoint.sh`: write token to .env AND export it

Two places for the subprocess to pick up the token:

```bash
# Inside the heredoc building ~/.hermes/.env
cat > "$HERMES_HOME/.env" << EOF
VENICE_API_KEY=${VENICE_API_KEY:-}
OPENAI_API_KEY=${OPENAI_API_KEY:-}
GITHUB_PERSONAL_ACCESS_TOKEN=${GITHUB_PERSONAL_ACCESS_TOKEN:-}
# ... other secrets
EOF
chmod 600 "$HERMES_HOME/.env"

# Also export into the gateway subprocess env so MCP stdio inherits.
# Don't pass --env KEY=VAL inside the MCP command line args —
# that locks the literal token into the saved cli-config.yaml
# and a later `git log` view will leak it.
export GITHUB_PERSONAL_ACCESS_TOKEN

exec hermes gateway run
```

The MCP subprocess automatically inherits any `export`ed env vars on launch — no literal `--env KEY=VAL` needed. This keeps the source tree free of secrets.

### Step 4 — `hermes/cli-config.yaml`: bake the MCP server + toolset

The entrypoint copies this file to `/root/.hermes/config.yaml` on every start. Anything image-baked here is durable across restarts.

```yaml
mcp_servers:
  github:
    command: npx
    args:
      - -y
      - '@modelcontextprotocol/server-github'
    enabled: true

# Add `github` to the platform_toolsets block so the bot can actually invoke
# the discovered tools — discovery alone doesn't enable invocation.
platform_toolsets:
  cli: [hermes-cli]
  telegram: [hermes-telegram, session_search, github]
```

Edit these in the source tree (`/Users/<you>/tmp/<agent>-deploy/hermes/cli-config.yaml` — find yours via `cat ~/.railway/config.json | jq -r '.projects.<workdir>.project'`).

### Step 5 — Build + deploy

From the source tree:

```bash
cd /Users/<you>/tmp/<agent>-deploy
railway up -y -d
```

`railway up` uploads the directory and triggers a Docker build + redeploy. The MCP server is now in the image.

### Step 6 — Verify

Two-step verification: connection discovery AND runtime invocation.

```bash
# Get the project UUID (NOT the name — ssh requires the UUID; see railway-cli-notes.md)
uuid=$(cat ~/.railway/config.json | jq -r ".projects[\"/Users/<you>/tmp/<agent>-deploy\"].project")

# 1. List MCP servers + tools discovered
railway ssh -p $uuid -s <svc> -e production 'hermes mcp list'

# Expect:  Name: github   Transport: npx -y ...   ✓ enabled

# 2. Test full invocation (this MUST succeed — discovery without
#    hermes-agent[mcp] lets step 1 pass while step 2 fails)
railway ssh -p $uuid -s <svc> -e production 'hermes mcp test github'

# Expect:  ✓ Connected (~1s)  ✓ Tools discovered: 26
# If you see ✗ Connection failed (...): MCP server 'github' requires the
# 'mcp' Python SDK → go back to Step 2 and confirm [mcp] extra in Dockerfile.
```

### Step 7 — Smoke from the chat surface

Once MCP test passes, hit the bot on Telegram (or whichever platform the agent uses) and request a tool call: `search for repositories named hermes-agent on github`. The bot should call `mcp_github_search_repositories` and return results.

## Pitfalls

- **Locking the token into cli-config.yaml** — passing `--env KEY=VAL` as MCP-server CLI args puts the literal value into the saved yaml, and Git history leaks it forever. Always prefer `export KEY="$KEY"` in entrypoint.sh so the MCP subprocess inherits at launch time.
- **Discover-but-don't-invoke** — `hermes mcp list` showing ✓ enabled and 26 tools is necessary but not sufficient. `hermes mcp test` is the actual integration test. Always run both.
- **Tool chain = `--command npx --args -y <pkg>`** — the `-y` flag is what auto-installs the npm package on first launch; missing it stalls MCP startup on an interactive y/N npm prompt that the subprocess can't answer.
- **Don't forget Node.js** — `python:3.13-slim` image strips Node. Either base on `node:22-bookworm-slim` (heavier) or `apt-get install -y nodejs npm` in Dockerfile.
- **`platform_toolsets` ≠ auto-loaded** — discovered MCP tools are NOT auto-injected into all toolsets by name based on server name. Add the server name explicitly to the relevant `platform_toolsets.<platform>` list (e.g., `github` under `telegram:`) to expose them to that channel.
- **Any 502 on `/` after rebuild is normal** — Railway's Telegram DoH bootstrap can take 30-90s; the HTTP server might not bind until the platform adapter connects. The bot is healthy as long as Telegram messages flow. Don't conflate 502 on the public URL with model/MCP being broken.

## Recovery

If MCP test fails after a rebuild, the most likely culprits in order:

1. Dockerfile didn't include `[mcp]` extra, or hermes-agent wheel upgraded and blew away a separate `pip install mcp` line. Fix: re-push Dockerfile with `[mcp]`, `railway up`.
2. Token wasn't refreshed in Railway env after rotation. Fix: `railway variable set ... --stdin` again, restart.
3. Token not exported in entrypoint.sh, only written to .env. Fix: add `export VAR_NAME` after the .env heredoc.
4. `hermes mcp list` is empty — entrypoint overwrote ~/.hermes/config.yaml with the new image bake, but maybe `mcp_servers:` block was deleted in source. Diff and re-add.

## Reference docs and templates

- `cloud-agent-provisioning/references/hermes-on-railway-runtime-state.md` — full filesystem-anatomy and entrypoint-copy semantics
- `cloud-agent-provisioning/references/railway-cli-notes.md` — Railway CLI gotchas (link flag shape, ssh UUID requirement, restart 124 behavior)
- `mcp/native-mcp/SKILL.md` — umbrella for all MCP-related work; the **standard st** handbook for the [mcp] Python SDK requirement
