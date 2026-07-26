# Railway CLI token auth in non-interactive shells

Session date: 2026-05-09

## Observed environment

- Node and npm were available.
- Railway CLI was not installed initially.
- `npm install -g @railway/cli` installed Railway CLI `4.57.1` successfully.

## Key behavior

`railway login --browserless` failed in the Telegram/agent shell with:

```text
Browserless login requires an interactive terminal. For non-interactive environments, set RAILWAY_API_TOKEN or RAILWAY_TOKEN.
```

Installed CLI README confirmed:

- Project token: set `RAILWAY_TOKEN` for project-level actions.
- Account or workspace token: set `RAILWAY_API_TOKEN` for account/workspace actions.

## Verification pattern

Check an account/workspace token without project-token ambiguity:

```bash
env -u RAILWAY_TOKEN RAILWAY_API_TOKEN="$RAILWAY_API_TOKEN" railway whoami
env -u RAILWAY_TOKEN RAILWAY_API_TOKEN="$RAILWAY_API_TOKEN" railway list
```

Check a project token separately:

```bash
env -u RAILWAY_API_TOKEN RAILWAY_TOKEN="$RAILWAY_TOKEN" railway status
```

## Invalid token behavior

A UUID-shaped token was stored temporarily as both vars and Railway returned:

```text
Unauthorized. Please check that your RAILWAY_API_TOKEN is valid and has access to the resource you're trying to use.
Unauthorized. Please check that your RAILWAY_TOKEN is valid and has access to the resource you're trying to use.
```

Action taken: remove invalid `RAILWAY_API_TOKEN=` and `RAILWAY_TOKEN=` entries from `~/.hermes/.env` to avoid poisoning future Railway commands.

## Valid account token behavior and stale `RAILWAY_TOKEN` pitfall

A later UUID-shaped Railway token worked as an account/workspace API token when tested as `RAILWAY_API_TOKEN`:

```bash
env -u RAILWAY_TOKEN RAILWAY_API_TOKEN="$TOKEN" railway whoami
# Logged in as vivgates@hotmail.com 👋

env -u RAILWAY_TOKEN RAILWAY_API_TOKEN="$TOKEN" railway list
# listed projects
```

The same token failed as `RAILWAY_TOKEN`:

```text
Unauthorized. Please check that your RAILWAY_TOKEN is valid...
Invalid RAILWAY_TOKEN...
```

After persisting only `RAILWAY_API_TOKEN=...` to `~/.hermes/.env`, plain `railway whoami` still failed because the long-running agent process had already inherited a stale `RAILWAY_TOKEN`. Verification succeeded when explicitly unsetting it:

```bash
env -u RAILWAY_TOKEN RAILWAY_API_TOKEN="$RAILWAY_API_TOKEN" railway whoami
```

Practical fix for future sessions: source `~/.hermes/.env` and unset `RAILWAY_TOKEN` when `RAILWAY_API_TOKEN` is present, or install a local wrapper around the npm CLI:

```bash
#!/usr/bin/env bash
if [ -f "$HOME/.hermes/.env" ]; then
  set -a; . "$HOME/.hermes/.env"; set +a
fi
if [ -n "${RAILWAY_API_TOKEN:-}" ] && [ "${RAILWAY_USE_PROJECT_TOKEN:-}" != "1" ]; then
  unset RAILWAY_TOKEN
fi
exec node "$HOME/.local/lib/node_modules/@railway/cli/bin/railway.js" "$@"
```

Use `RAILWAY_USE_PROJECT_TOKEN=1 railway ...` only for intentionally project-token-scoped operations.

## Direct API check

Railway docs specify the public API endpoint:

```text
https://backboard.railway.com/graphql/v2
```

A valid account token returned `me { id name email }`; invalid tokens returned HTTP 200 with GraphQL `Not Authorized` errors. The older `.app` endpoint may respond similarly but the documented endpoint is `.com`.

## Practical user guidance

For broad deploy help, ask the user for an Account or Workspace API token from Railway account tokens. For one project, a Project token can be safer but may not support `whoami`/`list`.
