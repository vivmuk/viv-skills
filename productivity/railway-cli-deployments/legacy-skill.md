> Re-homed package note: this former standalone skill now lives under `devops/agent-infrastructure-operations/references/railway-cli-deployments/`. Any legacy path such as `references/...`, `templates/...`, `scripts/...`, or `assets/...` should be resolved relative to this package directory, not the umbrella skill root.

---
name: railway-cli-deployments
description: "Railway CLI setup, token authentication, project linking, deployments, logs, and env vars from agent/non-interactive shells."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Railway, CLI, Deployments, Hosting, DevOps, Authentication]
    related_skills: []
---

# Railway CLI Deployments

Use this skill when the user asks to install/configure Railway CLI, authenticate Railway, link a Railway project, deploy a repo to Railway, inspect logs, set variables, or troubleshoot Railway deploy access.

## Quick detection

Run these checks first:

```bash
printf 'node: '; node --version 2>/dev/null || echo 'not installed'
printf 'npm: '; npm --version 2>/dev/null || echo 'not installed'
printf 'railway: '; railway --version 2>/dev/null || echo 'not installed'
printf 'railway auth status:\n'; railway whoami 2>&1 || true
```

## Install Railway CLI

If npm/node are available:

```bash
npm install -g @railway/cli
railway --version
```

Alternative installer from Railway docs:

```bash
bash <(curl -fsSL cli.new)
```

Railway CLI help may suggest `railway setup agent -y`; use it only when intentionally configuring editor/agent MCP integration, not as a prerequisite for normal CLI deploys.

## Authentication in non-interactive agent sessions

Interactive login is usually not available over Telegram/headless shells.

```bash
railway login --browserless
```

can fail with:

```text
Browserless login requires an interactive terminal. For non-interactive environments, set RAILWAY_API_TOKEN or RAILWAY_TOKEN.
```

Use tokens instead:

- `RAILWAY_API_TOKEN`: account/workspace token for account-level or workspace-level actions such as listing projects and broad management.
- `RAILWAY_TOKEN`: project token for project-level actions such as deploying a linked project.

Store tokens in the Hermes env file with restrictive permissions, without echoing the secret back to the user:

```bash
mkdir -p ~/.hermes
umask 077
# Replace placeholder via a secure input path/tool approval flow; do not print it.
printf 'RAILWAY_API_TOKEN=%q\n' "$RAILWAY_API_TOKEN" >> ~/.hermes/.env
chmod 600 ~/.hermes/.env
```

For project tokens, write `RAILWAY_TOKEN=...` instead. Some workflows benefit from setting both names only if the token type is known to work for both; otherwise prefer the correct variable for the token type.

Load for one command:

```bash
set -a
. ~/.hermes/.env
set +a
railway whoami
```

## Verify auth

For account/workspace tokens, explicitly unset any project token from the inherited agent environment. A stale `RAILWAY_TOKEN` can make plain `railway whoami` fail even when `RAILWAY_API_TOKEN` is valid:

```bash
env -u RAILWAY_TOKEN RAILWAY_API_TOKEN="$RAILWAY_API_TOKEN" railway whoami
env -u RAILWAY_TOKEN RAILWAY_API_TOKEN="$RAILWAY_API_TOKEN" railway list
```

For project tokens:

```bash
env -u RAILWAY_API_TOKEN RAILWAY_TOKEN="$RAILWAY_TOKEN" railway status
```

Optional direct API sanity check for an account/workspace token, using the documented `.com` endpoint:

```bash
python3 - <<'PY'
import json, os, urllib.request
body=json.dumps({'query':'query { me { id email name } }'}).encode()
req=urllib.request.Request('https://backboard.railway.com/graphql/v2', data=body, headers={
    'Authorization': f"Bearer {os.environ['RAILWAY_API_TOKEN']}",
    'Content-Type': 'application/json',
})
print(urllib.request.urlopen(req, timeout=20).read().decode()[:1000])
PY
```

If Railway returns Unauthorized, the token is invalid, expired, wrong type, or lacks access. Remove bad entries from `~/.hermes/.env` so future commands are not poisoned:

```bash
python3 - <<'PY'
from pathlib import Path
p=Path.home()/'.hermes/.env'
if p.exists():
    lines=p.read_text().splitlines()
    lines=[l for l in lines if not (l.startswith('RAILWAY_API_TOKEN=') or l.startswith('RAILWAY_TOKEN='))]
    p.write_text('\n'.join(lines).rstrip()+('\n' if lines else ''))
    p.chmod(0o600)
PY
```

## Common deployment flow

From the repo root, prefer a helper function or wrapper that sources `~/.hermes/.env` and unsets stale `RAILWAY_TOKEN` when using an account token:

```bash
set -a; [ -f ~/.hermes/.env ] && . ~/.hermes/.env; set +a
[ -n "${RAILWAY_API_TOKEN:-}" ] && unset RAILWAY_TOKEN
railway link             # choose existing project/environment, or pass project id if known
railway status
railway up               # upload and deploy current directory
railway logs             # inspect logs
```

If the long-running agent process already inherited a bad `RAILWAY_TOKEN`, consider installing a local wrapper at `~/.local/bin/railway` that sources `~/.hermes/.env` and unsets `RAILWAY_TOKEN` unless `RAILWAY_USE_PROJECT_TOKEN=1`. Keep the original CLI target as `node ~/.local/lib/node_modules/@railway/cli/bin/railway.js` when installed via npm.

Other useful commands:

```bash
railway variables        # list vars
railway variables set KEY=value
railway redeploy
railway restart
railway domain           # generate/add domains when requested
```

## Pitfalls

- Do not assume `railway login --browserless` works in non-interactive shells; token env vars are the reliable path.
- Account/workspace tokens use `RAILWAY_API_TOKEN`; project tokens use `RAILWAY_TOKEN`. Do not store an account token under `RAILWAY_TOKEN` just because it is UUID-shaped.
- `railway whoami` with a project token may still be unauthorized for account-level checks. Test account tokens with `railway list`; test project tokens with project-scoped commands after linking.
- If `RAILWAY_API_TOKEN` verifies with `env -u RAILWAY_TOKEN ...` but plain `railway whoami` fails, the process likely inherited a stale `RAILWAY_TOKEN`; unset it or use the wrapper pattern.
- If a user pastes a token and verification fails, remove it from persistent env files immediately.
- Avoid printing tokens in command output, logs, summaries, or final replies. When commands require secrets, rely on approved secure command execution and redact in explanations.
- Account/workspace tokens are best when the user wants the agent to link/manage/deploy across projects; project tokens are safer for one already-linked project.

## References

- `references/token-auth-noninteractive.md` — session-derived notes on Railway token variables and Unauthorized behavior in headless shells.
