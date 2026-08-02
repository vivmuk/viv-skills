---
name: railway
description: "Deploy apps and manage services on Railway via CLI and API."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Railway, deployment, hosting, PaaS, CLI]
    related_skills: [github-repo-management, github-pr-workflow]
---

# Railway Deployment

Deploy applications, manage services, and interact with Railway via the CLI and GraphQL API.

## Prerequisites

- Node.js / npm for CLI installation
- A Railway account with an API token

## Installation

```bash
npm install -g @railway/cli
```

**Important:** When installed via npm in the Hermes environment, the binary lands at `~/.hermes/node/bin/railway` — it may not be in `$PATH`. Use the full path or add it:

```bash
# Option 1: Use full path
~/.hermes/node/bin/railway --version

# Option 2: Add to PATH in current session
export PATH="$HOME/.hermes/node/bin:$PATH"
railway --version
```

## Authentication

### Getting an API Token

1. Go to **https://railway.app/account/tokens** (while logged in)
2. Click **"Create New Token"**
3. Name it (e.g., `hermes-agent`)
4. **Important:** Create an **account-level** token, NOT a team/project-scoped one. Team tokens have limited permissions and won't work for `railway whoami` or project listing.
5. Copy the token — it won't be shown again.

### Authenticating the CLI

Railway CLI v4+ does **not** support `--token` on the `login` command. Two approaches:

#### Approach A: Environment Variable (Headless / Agent)

```bash
export RAILWAY_TOKEN="<your-account-api-token>"
railway whoami  # Should show your account info
```

Store the token for persistence:

```bash
# Add to ~/.hermes/.env
echo "RAILWAY_TOKEN=<your-account-api-token>" >> ~/.hermes/.env

# Source in future sessions
source ~/.hermes/.env
```

#### Approach B: Interactive Browser Login (Desktop)

```bash
railway login
# Opens browser for OAuth
```

#### Approach C: Browserless Login (Requires Terminal Interaction)

```bash
railway login --browserless
# Displays a pairing code to enter in your browser
# DOES NOT work in fully non-interactive/agent contexts
```

### OAuth Client Credentials ≠ API Tokens

Users sometimes provide **OAuth client credentials** (format: `rlwy_oaci_...` for client ID, `rlwy_oacs_...` for client secret). These are **NOT** team API tokens and **CANNOT** be used as `RAILWAY_TOKEN` environment variables.

**What OAuth credentials are:** They're for the Railway OAuth2 authorization flow (used by custom integrations). They require a full authorization code exchange or device code flow with redirect URIs.

**Why they won't work for CLI/API access:**
- Setting `RAILWAY_TOKEN=rlwy_oacs_...` → "Unauthorized"
- Using `Authorization: Bearer rlwy_oacs_...` with the GraphQL API → "Not Authorized" on most queries
- The OAuth flow requires redirect URIs configured on the app, a browser-based authorization step, and token exchange

**OAuth discovery endpoint:** `https://api.railway.app/.well-known/oauth-authorization-server` returns the full OAuth2 server metadata:
```json
{
  "issuer": "https://backboard.railway.com",
  "authorization_endpoint": "https://backboard.railway.com/oauth/auth?resource=https%3A%2F%2Fapi.railway.app",
  "token_endpoint": "https://backboard.railway.com/oauth/token",
  "registration_endpoint": "https://backboard.railway.com/oauth/register",
  "grant_types_supported": ["authorization_code", "refresh_token", "urn:ietf:params:oauth:grant-type:device_code"],
  "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post", "none", "private_key_jwt"]
}
```

**Dynamic client registration:** You can register new OAuth clients via `POST https://backboard.railway.com/oauth/register` with redirect URIs and grant types. The response includes a new `client_id`, `client_secret`, and `registration_access_token`. However, the device code grant doesn't work even when registered — Railway requires browser-based authorization.

**The correct fix:** Ask the user to create an **account-level Team API token** at https://railway.app/account/tokens (NOT OAuth credentials). This is the only reliable way to authenticate for CLI and API use.

### Pitfalls

| Problem | Solution |
|---------|----------|
| `Unauthorized` from `railway whoami` | Token is invalid, expired, or scoped to a team/project — recreate as account-level |
| `--token` flag not recognized | Railway v4 removed it — use `RAILWAY_TOKEN` env var instead |
| `Cannot login in non-interactive mode` | Using `--browserless` in a headless context — use `RAILWAY_TOKEN` env var |
| `railway: command not found` | Binary not in PATH — use full path `~/.hermes/node/bin/railway` |
| Both project-scoped AND account tokens return 403 | Tokens expire. Project-scoped tokens seem to stop working for both reads and mutations after some time. When both fail, you need to generate fresh tokens from the Railway dashboard. GitHub push auto-deploy should still work if the GitHub integration is connected, but it won't trigger if the integration is stale. As of 2026-05, both stored tokens (706a4dd7 and 39de4eec) are EXPIRED — user must create a fresh account-level token at railway.app/account/tokens. |
| User provides `rlwy_oaci_`/`rlwy_oacs_` credentials | These are OAuth client credentials, NOT API tokens. They cannot be used with `RAILWAY_TOKEN` or the CLI. Ask user to create an account-level token at railway.app/account/tokens instead. |
| OAuth device code flow returns `invalid_redirect_uri` | The OAuth app needs redirect URIs configured. Dynamic registration via `/oauth/register` can add them, but still requires browser-based auth code exchange. Not usable for headless CLI access. |
| `serviceConnect` returns "User does not have access to the repo" | Install the Railway GitHub App (slug: `railway-app`, ID: `73253`) on the repo at https://github.com/apps/railway-app. Without this, neither `serviceConnect` nor `githubRepoDeploy` can access the repo. |
| `railway up` returns "401 Unauthorized" on upload phase | Account-level API tokens (UUID format) get 401 on the upload endpoint. Create a project-scoped token via `projectTokenCreate` mutation and use that for `railway up` instead. |
| GraphQL `projectCreate` fails with "must specify workspaceId" | Include the user's workspace ID (from `me { workspaces { id name } }`) in the input. It's required. |
| `deploymentTriggerCreate` returns "no one in the project has access" | Same as `serviceConnect` — install the Railway GitHub App on the repo first. |

## Common Operations

### Verify Authentication

```bash
railway whoami
```

### Create a New Project

```bash
railway init
# Or with a name:
railway init --name my-project
```

### Link a Project to Current Directory

```bash
railway link
# Or specify project ID:
railway link <project-id>
```

### Deploy

```bash
# Deploy current directory
railway up

# Deploy with environment
railway up --environment production

# Deploy a specific service
railway up --service my-api
```

### View Logs

```bash
railway logs
railway logs --service my-api
railway logs --deployment <deployment-id>
```

### Environment Variables

```bash
# List variables
railway variable

# Set a variable
railway variable set KEY=value

# Set for a specific service
railway variable set KEY=value --service my-api
```

You can also set env vars via the GraphQL API using the `variableUpsert` mutation — see `references/railway-api-quirks.md` for the exact syntax, which requires `name` (not `key`), `projectId`, `environmentId`, and `serviceId`.

**Project-scoped tokens work for GraphQL mutations.** Although `railway whoami` and CLI commands fail with project-scoped tokens, the GraphQL API accepts them for `variableUpsert`. This is the recommended way to update env vars programmatically when you can't use the CLI:

```bash
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer <PROJECT_SCOPED_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"query":"mutation { variableUpsert(input: { projectId: \"<PID>\", environmentId: \"<EID>\", serviceId: \"<SID>\", name: \"KEY\", value: \"VALUE\" }) }"}'
```

To discover `environmentId`, query the project's environments (project-scoped tokens can read this too):
```bash
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"query":"{ project(id: \"<PID>\") { environments { edges { node { id name } } } } }"}'
```

**Batch updates must be rate-limited.** Add 1-second delays between consecutive `variableUpsert` mutations to avoid `"Service deployment rate limit exceeded"`. Each variable change triggers a redeploy — changing 3+ vars in rapid succession can hit this limit.

### Railway Builders (2026-05)

Railway supports three builders, selected in priority order:

1. **DOCKERFILE** — if `Dockerfile` exists in repo root, Railway ALWAYS uses it, even if `railway.toml` says NIXPACKS
2. **RAILPACK** — default if no Dockerfile exists. Auto-detects Node, Python, etc. Railway's current default builder.
3. **NIXPACKS** — only if `railway.toml` explicitly sets `builder = "NIXPACKS"` AND no Dockerfile exists

**Key insight**: If your build fails with DOCKERFILE or NIXPACKS, **delete the Dockerfile** and remove the explicit builder from `railway.toml** — let Railway auto-detect using RAILPACK. This fixed both CongressAI and StitchVid deployments that failed with DOCKERFILE but succeeded immediately with RAILPACK.

### Nixpacks + Node version mismatch

When using NIXPACKS, Railway may default to an old Node version (e.g. Node 18) even though `package.json` dependencies require Node ≥ 20. This produces `EBADENGINE Unsupported engine` errors and can cause `EBUSY` on `/app/node_modules/.cache`.

**Fix:**
- Add `engines.node` to `package.json` (e.g. `">=20.9.0"`)
- Add `nixpacks.toml` with `NIXPACKS_NODE_VERSION = "20"`
- Add `.nvmrc` with `20` for local consistency

See `references/railway-nixpacks-node18-failure.md` for a full transcript and reproduction.

**Security vulnerability blocking**: Railway (as of 2026-05) scans `package-lock.json` for known CVEs and **blocks deploys** if HIGH severity vulnerabilities are found. The error message appears in build logs like:
```
SECURITY VULNERABILITIES DETECTED
Found 1 vulnerable package(s):
  next@14.2.0
  Severity: HIGH
  Upgrade to 14.2.35: npm install next@^14.2.35
```
Fix: `npm install <package>@<minimum-version>`, commit the updated `package-lock.json`, and push. This takes precedence over any builder choice — even a valid Dockerfile build will fail if vulnerabilities are detected.

### Next.js startCommand must match output mode

| `next.config` output | `railway.toml` startCommand | Works? |
|---|---|---|
| `output: 'standalone'` | `node server.js` | ✅ |
| `output: 'standalone'` | `npx next start` | ❌ |
| No output / default | `npx next start` | ✅ |
| No output / default | `node server.js` | ❌ |

### Next.js output mode vs Dockerfile

The `output` field in `next.config.ts` controls what `next build` produces and **must match your Dockerfile's expectations**:

| `output` | Build artifact | Dockerfile must... |
|---|---|---|
| `"standalone"` | `.next/standalone/` directory | `COPY --from=builder /app/.next/standalone /app/staging` then reorganize |
| `"export"` | `out/` static directory | Serve with Nginx or a static host — **no Node server needed** |
| (default) | `.next/` server-ready directory | Use `npx next start` or a custom server |

**Critical pitfall**: If the Dockerfile expects `.next/standalone` (as the standard Next.js Docker template does) but `next.config` says `output: "export"`, the build fails with:

```
failed to compute cache key: "/app/.next/standalone": not found
```

`output: "export"` does NOT produce `.next/standalone/` — it produces `out/` with static HTML. If you're deploying to Railway with a Dockerfile, you **must use `output: "standalone"`**. Only use `output: "export"` for static hosting like GitHub Pages.

**Dual deployment pattern**: If you need both Railway (standalone) and GitHub Pages (static export), maintain two branches or two build configs. The `gh-pages` branch can have `output: "export"` in `next.config.ts` and use `next build && npx next export` (or the automated GitHub Actions workflow), while `main` keeps `output: "standalone"` for Railway.

### next.config.js vs next.config.mjs conflict

Never have both `next.config.js` and `next.config.mjs` — merge into one `next.config.mjs` and delete the other. When `package.json` has `"type": "module"`, use `.mjs`.

### variableUpsert rate limiting

Setting multiple env vars in rapid succession can trigger `"Service deployment rate limit exceeded"`. Add 1-second delays between consecutive `variableUpsert` mutations.

### Debugging 502 Errors

If your app deploys successfully (status = SUCCESS) but returns 502 "Application failed to respond":

1. **Most common cause**: App not reading `PORT` env var. Railway assigns a dynamic port — your app MUST bind to `0.0.0.0:$PORT`.
2. **Second most common**: Missing start command. Use a `Procfile` (`web: python main.py`) or `railway.toml` (`startCommand`).
3. **To see runtime logs**, you need an account-level Railway token. Project-scoped tokens cannot access `railway logs`.
4. See `references/railway-api-quirks.md` for full debugging checklist.

### Add a Database

```bash
# Add PostgreSQL
railway add --service postgres

# Add Redis
railway add --service redis

# Add MySQL
railway add --service mysql

# Connect to database shell
railway connect postgres
```

### Custom Domains

```bash
# Generate a Railway-provided domain
railway domain

# Add custom domain
railway domain add myapp.example.com
```

#### Custom Domain via GraphQL API (when CLI auth fails)

When `railway domain` CLI doesn't work (e.g., project-scoped token), use the GraphQL API to create custom domains and retrieve DNS records. See `references/railway-api-quirks.md` → "Custom Domain Setup via GraphQL API" for the full walkthrough including Cloudflare DNS configuration and schema introspection tips.

### Manage Services

```bash
railway service list
railway service add my-api
railway status
```

### SSH Access

```bash
railway ssh --service my-api
```

## Using the GraphQL API Directly

The Railway API is GraphQL at `https://backboard.railway.app/graphql/v2`. See `references/railway-api-quirks.md` for the full set of verified queries, mutations, and gotchas including deployment management.

## GitHub Integration

Railway can auto-deploy from GitHub repos:

1. In the Railway dashboard, create a new project
2. Select "Deploy from GitHub repo"
3. Connect your GitHub account and choose the repo
4. Railway will auto-deploy on push to the default branch

This is often simpler than CLI deployment for ongoing projects. Use CLI for one-off deploys, quick iteration, or agent-driven workflows.

### Deploy from CLI with Explicit Flags

When GitHub auto-deploy triggers are broken, missing, or you want to deploy from local source without pushing first, use `railway up` with explicit flags:

```bash
RAILWAY_TOKEN="<token>" railway up --detach \
  --service "my-service" \
  --environment "production" \
  --project "<project-uuid>" \
  --message "deploy: description of changes"
```

**Flags explained:**
- `--detach` — Returns immediately after upload; build continues in the background
- `--service` — Service name (not UUID). Must match the service name in Railway dashboard
- `--environment` — Environment name (usually `production`)
- `--project` — Project UUID (find via `railway status` or GraphQL query)
- `--message` — Deploy description shown in Railway deploy history

**After deploying**, wait ~2.5 minutes for build + start, then check:
1. Deployment status via GraphQL `deployments` query
2. Runtime logs via `railway logs --service <name> --environment production`
3. Health endpoint: `curl -sI https://<app>.up.railway.app/api/health`

**Verifying deployment succeeded:**
```bash
# Check latest deployment status
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"{ deployments(input: {serviceId: \"<SID>\"}) { edges { node { id status createdAt } } } }"}'
```

**Pitfall**: If `railway up` without flags fails with "no service linked", you need the `--service`, `--environment`, and `--project` flags. Alternatively, run `railway link` interactively first.

**Pitfall**: Project-scoped tokens may work for `railway up` with flags but fail for `railway logs`. Use an account-level token for full CLI access, or check logs via the GraphQL API instead.

## Database Connections on Railway

### Managed Plugin (recommended) vs Raw Container

When adding PostgreSQL to a Railway project, you have two options:

1. **Managed plugin** (preferred): Railway auto-generates `DATABASE_URL` and other connection vars. Reference them in other services as `${{POSTGRES.DATABASE_URL}}` — Railway resolves these at deploy time.
2. **Raw container** (e.g., `postgres:16-alpine` via `serviceConnect`): Railway does NOT auto-generate connection variables. You must:
   - Set `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` env vars on the postgres service
   - Set `DATABASE_URL` on the app service using Railway's internal DNS hostname

### Internal DNS Between Services

Services within the same Railway project communicate via **service name** as hostname. For a postgres service named "postgres":

```
DATABASE_URL=postgresql://user:password@postgres:5432/dbname
```

**Pitfall**: `${{POSTGRES.DATABASE_URL}}` reference syntax only works for managed plugins. For raw containers, use the service name as hostname directly. The reference `${{POSTGRES.RAILWAY_PRIVATE_DOMAIN}}` is NOT set for raw containers.

**Gotcha**: When you create a raw postgres container via `serviceConnect`, then later replace it with a managed plugin, you must also update the `DATABASE_URL` env var on the app service. The managed plugin uses `${{POSTGRES.DATABASE_URL}}` syntax but if you initially set a hardcoded connection string, that takes precedence. Delete the old hardcoded value and set it to `${{POSTGRES.DATABASE_URL}}` instead.

### Prisma Auto-Migration Pattern

On Railway, running `prisma migrate deploy` at build time requires a running database, creating a chicken-and-egg problem. Instead, auto-create tables at runtime:

```typescript
// src/app/api/vents/route.ts
async function ensureTable() {
  try {
    await prisma.$executeRawUnsafe(`
      CREATE TABLE IF NOT EXISTS "vents" (
        "id" TEXT NOT NULL PRIMARY KEY DEFAULT gen_random_uuid(),
        "text" TEXT NOT NULL,
        "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
      )
    `)
  } catch (e) {
    // Table already exists, ignore
  }
}
```

Call `ensureTable()` before `prisma.vent.findMany()` or `prisma.vent.create()`. This makes the app self-healing on fresh deployments.

**Pitfall**: Prisma v7 changed the config format to `prisma.config.ts` and requires `datasourceUrl` in the client constructor. For simplicity, pin to Prisma v6 or pass `datasourceUrl: process.env.DATABASE_URL` to `new PrismaClient()`.

**Pitfall**: When FK fields are optional (`String?`), the relation field must also be optional (`User?`). Writing `user User @relation(fields: [userId], references: [id])` when `userId String?` causes Prisma validation error: "The relation field uses scalar fields. At least one of those fields is optional." Fix: `user User? @relation(fields: [userId], references: [id])`.

## Deploying Raw Docker Images

To deploy a pre-built Docker image (like `postgres:16-alpine`) on Railway via the GraphQL API:

### Redeploy Latest Commit (Easiest)

If your service is already connected to a GitHub repo and you've pushed new code, call `serviceInstanceRedeploy` to trigger Railway to pick it up:

```bash
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $RAILWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"mutation { serviceInstanceRedeploy(serviceId: \"SERVICE_ID\") }"}'
```

- Only needs `serviceId` (no `environmentId` required)
- Returns `Boolean!` — do NOT add subfields like `{ id status }`
- Works with project-scoped UUID tokens

### Deploy Service
# V2 returns deployment ID string, V1 returns boolean
# Both work with UUID project-scoped tokens

# V1 (returns Boolean! — no subfields):
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $RAILWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"mutation { serviceInstanceDeploy(serviceId: \"SERVICE_ID\", environmentId: \"ENV_ID\") }"}'

# V2 (returns deployment ID string):
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $RAILWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"mutation { serviceInstanceDeployV2(serviceId: \"SERVICE_ID\", environmentId: \"ENV_ID\") }"}'
```

**Pitfall**: The V1 `serviceInstanceDeploy` takes `serviceId` and `environmentId` as **top-level args** (NOT an input object). Do NOT wrap in `input: {...}`. It returns `Boolean!` — do NOT add subfields like `{ id status }`.

### Add Public Domain
```

## Full Programmatic Setup (Project → Service → Token → Deploy)

When starting from scratch (no existing project or service), use the GraphQL API to create everything:

### 1. Get Workspace ID

Projects must belong to a workspace. Query your workspaces:

```bash
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $RAILWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"{ me { id name username workspaces { id name projects { edges { node { id name } } } } } }"}'
```

### 2. Create Project (requires workspaceId)

```bash
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $RAILWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"mutation { projectCreate(input: { name: \"My Project\", isPublic: true, workspaceId: \"WORKSPACE_ID\" }) { id name } }"}'
```

**Pitfall**: `workspaceId` is REQUIRED. Without it, you get: `"You must specify a workspaceId to create a project"`

### 3. Create Service

```bash
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $RAILWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"mutation { serviceCreate(input: { projectId: \"PROJECT_ID\", name: \"web\", source: { repo: \"owner/repo\" }, branch: \"main\", environmentId: \"ENV_ID\" }) { id name } }"}'
```

The project's default environment ID is returned in step 2 — query `{ project(id) { environments { edges { node { id name } } } } }` to get it.

### 4. Create Project Token (for `railway up`)

Account-level API tokens get `401 Unauthorized` on the upload endpoint. You need a project-scoped token:

```bash
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $RAILWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"mutation { projectTokenCreate(input: { name: \"deploy-token\", projectId: \"PROJECT_ID\", environmentId: \"ENV_ID\" }) }"}'
```

Returns the token as a plain string (UUID format). Use this for `RAILWAY_TOKEN` with `railway up`.

**Pitfall**: The account-level token used for GraphQL API queries gets 401 on `railway up`'s upload phase. You MUST create a project token for CLI deployments.

### 5. Deploy via CLI

```bash
RAILWAY_TOKEN="<project-token-from-step-4>" railway up \
  --service "SERVICE_ID" \
  --project "PROJECT_ID" \
  --environment "ENV_ID"
```

### 6. Connect GitHub Repo (Optional — for Auto-Deploy)

```bash
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $RAILWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"mutation { serviceConnect(id: \"SERVICE_ID\", input: {repo: \"owner/repo\", branch: \"main\"}) { id name } }"}'
```

**Critical**: This will fail with `"User does not have access to the repo"` if the **Railway GitHub App** is not installed on the repository. The Railway GitHub App (slug: `railway-app`, ID: `73253`) must be installed via **https://github.com/apps/railway-app** — select the repo and authorize. Without this installation, `serviceConnect` and `githubRepoDeploy` both fail.

After connecting, pushes to the branch auto-trigger deployments.

### Alternative: Deploy via `railway up` Without GitHub Integration

If you can't or don't want to install the Railway GitHub App, use `railway up` with a project token. This uploads local source directly to Railway's builder. It bypasses the GitHub integration entirely. This is the recommended approach for:
- Private repos where you don't want to install the Railway app
- Quick deploys from local code
- Agent-driven deployments where you want full control

## Adding a Public Domain

```bash
# Via GraphQL (ServiceDomainCreateInput needs serviceId and environmentId)
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $RAILWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"mutation { serviceDomainCreate(input: {serviceId: \"SERVICE_ID\", environmentId: \"ENV_ID\"}) { domain id } }"}'
```

## References

- `references/railway-api-quirks.md` — CLI v4 auth changes, GraphQL endpoint details, token type gotchas, binary PATH issues