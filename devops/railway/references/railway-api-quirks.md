# Railway API Quirks and Session Notes

## Next.js `output` mode pitfalls

### `output: "export"` builds produce `out/`, NOT `.next/standalone/`

If your Dockerfile runs `COPY --from=builder /app/.next/standalone /app/staging` but `next.config` has `output: "export"`, the build will fail with:

```
[runner 3/6] COPY --from=builder /app/.next/standalone /app/staging
Build Failed: failed to compute cache key: failed to calculate checksum: "/app/.next/standalone": not found
```

The `export` mode produces a static `out/` directory, not the standalone Node server. For Railway deployments with a Dockerfile, always use `output: "standalone"`. For GitHub Pages static hosting, use `output: "export"` on a separate branch.

### Force-dynamic vs generateStaticParams for standalone mode

When `output: "standalone"` is set, pages with dynamic routes (like `/collection/[id]`) need either:
- `export const dynamic = 'force-dynamic'` — renders on every request (safe for Railway with CDN)
- `export async function generateStaticParams()` — pre-renders all known paths at build time

Using `generateStaticParams` is preferred for performance but requires all data to be available at build time. Using `force-dynamic` is simpler and prevents stale 404 caching on Railway's CDN.

---

## CLI v4 Auth Changes (as of v4.44.0)

- `railway login --token <TOKEN>` is **removed** — no `--token` flag exists
- `railway login --browserless` requires terminal interaction (displays pairing code)
- Only reliable headless auth method: `RAILWAY_TOKEN` environment variable
- Token format: UUID-style (e.g., `706a4dd7-529c-4548-a8e1-268f3934ae77`)

## GraphQL Endpoint

- URL: `https://backboard.railway.app/graphql/v2`
- Auth header: `Authorization: Bearer <token>`
- root query for user info is `me`, NOT `viewer`
- Example: `{ me { id name email } }`
- Example: `{ projects { edges { node { id name } } } }`

## Token Types

| Type | Scope | `whoami` works? | Created at |
|------|-------|-----------------|------------|
| Account-level API token | Full account access | Yes | railway.app/account/tokens |
| Team/project token | Scoped to specific project(s) | No (returns Unauthorized) | railway.app/team/settings/tokens or project settings |

**Always prefer account-level tokens** for agent/CLI usage. Team/project tokens will fail `whoami` AND most CLI commands (`link`, `up`, `variable`), but they CAN successfully call the GraphQL API for read operations (listing projects, querying services, reading deployments). If `whoami` fails but API project queries work, you have a team/project token — either get an account-level token from railway.app/account/tokens, or fall back to deploying from the Railway dashboard UI with GitHub auto-deploy.

## GraphQL API Patterns (Verified)

The `me` query returns `Not Authorized` with team/project tokens. But project-level queries DO work:

```bash
# List all projects (works with team/project tokens)
curl -s -H "Authorization: Bearer $RAILWAY_TOKEN" \
  https://backboard.railway.app/graphql/v2 \
  -H "Content-Type: application/json" \
  -d '{"query":"{ projects { edges { node { id name } } } }"}'

# Get project services (works with team/project tokens)
curl -s -H "Authorization: Bearer $RAILWAY_TOKEN" \
  https://backboard.railway.app/graphql/v2 \
  -H "Content-Type: application/json" \
  -d '{"query":"{ project(id: \"PROJECT_ID\") { name services { edges { node { id name } } } } }"}'
```

## GraphQL API Verified Queries (2025-05)

### List Projects
```bash
curl -s -H "Authorization: Bearer $RAILWAY_TOKEN" \
  https://backboard.railway.app/graphql/v2 \
  -H "Content-Type: application/json" \
  -d '{"query":"{ projects { edges { node { id name } } } }"}'
```

### Get Project Services + Environments
```bash
curl -s -H "Authorization: Bearer $RAILWAY_TOKEN" \
  https://backboard.railway.app/graphql/v2 \
  -H "Content-Type: application/json" \
  -d '{"query":"{ project(id: \"PROJECT_ID\") { name services { edges { node { id name } } } environments { edges { node { id name } } } } }"}'
```

### Get Recent Deployments (with commit info)
```bash
curl -s -H "Authorization: Bearer $RAILWAY_TOKEN" \
  https://backboard.railway.app/graphql/v2 \
  -H "Content-Type: application/json" \
  -d '{"query":"{ deployments(input: { projectId: \"PROJECT_ID\", environmentId: \"ENV_ID\", serviceId: \"SERVICE_ID\" }) { edges { node { id status meta } } } }"}'
```

**Important:** The `deployments` query requires an `input` object with `projectId`, `environmentId`, and `serviceId` — NOT `first` or `serviceId` as top-level args.

### Set Environment Variables (mutation)

The `variableUpsert` mutation works with project-scoped tokens. The schema is specific:

```bash
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $RAILWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"mutation { variableUpsert(input: { name: \"MY_VAR\", value: \"my_value\", projectId: \"PROJECT_ID\", environmentId: \"ENV_ID\", serviceId: \"SERVICE_ID\" }) }"}'
```

**Key points:**
- Use `name` (NOT `key`) — `key` is not a valid field and will error
- All three IDs are required: `projectId`, `environmentId`, `serviceId`
- Return type is `Boolean!` — do NOT add subfields like `{ id }`; just `variableUpsert(input: {...})` with no selection set
- Project-scoped tokens CAN use this mutation (contrary to the note below about dashboard-only)

### Restart a Deployment (mutation)

```bash
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $RAILWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"mutation { deploymentRestart(id: \"DEPLOY_ID\") }"}'
```

### Available Deployment Mutations

There is **NO** `deploymentCreate` mutation. Available mutations:
- `deploymentRestart` — re-deploy a specific deployment (pass the deployment ID)
- `deploymentCancel` — cancel a running deployment
- `deploymentApprove` — approve a pending deployment
- `deploymentStop` — stop a deployment
- `serviceInstanceRedeploy` — re-deploy the latest commit on a service (pass `serviceId` only, top-level arg NOT input object). Returns `Boolean!` — no subfields. This is the easiest way to trigger a deployment when you've pushed code to GitHub and need Railway to pick it up immediately.

**`serviceInstanceRedeploy` mutation:**
```bash
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $RAILWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"mutation { serviceInstanceRedeploy(serviceId: \"SERVICE_ID\") }"}'
```

Key difference from `serviceInstanceDeploy`:
- `serviceInstanceRedeploy` only needs `serviceId` (no `environmentId`) — it redeploys the latest commit
- `serviceInstanceDeploy` needs both `serviceId` AND `environmentId` AND triggers a fresh build
- `serviceInstanceRedeploy` works with project-scoped UUID tokens
- Returns `Boolean!` — do NOT add `{ id status }` subfields

To trigger a new deploy: push to the connected GitHub branch, then call `serviceInstanceRedeploy` to pick it up immediately. Alternatively, `deploymentRestart` can restart a specific past deployment.

### Debugging 502 "Application Failed to Respond"

When Railway shows SUCCESS for deployment but returns 502 on the public URL:

1. **Wrong port binding**: Railway sets `PORT` env var dynamically (usually NOT 5000). Your app MUST read `PORT` from the environment and bind to `0.0.0.0:$PORT`. Hardcoding `EXPOSE 5000` in Dockerfile or defaulting to 5000 will cause 502.
2. **Missing start command**: Ensure `Procfile` with `web: python main.py` or `railway.toml` with `startCommand = "python main.py"`. Nixpacks auto-detects Python but may not find the entrypoint.
3. **Crash at import time**: If a dependency fails to import (e.g., wrong twilio import path), the container starts then immediately crashes. You CANNOT see this without `railway logs` — which requires an account-level token.
4. **Nixpacks vs Dockerfile**: If both `Dockerfile` and Nixpacks config exist, Railway may pick Dockerfile (check deployment metadata `builder` field). If your Dockerfile has issues, delete it and use `nixpacks.toml` + `Procfile` instead.
5. **Check deployment metadata**: Query `fileServiceManifest` in deployments — look for `builder: "NIXPACKS"` vs `builder: "DOCKERFILE"` to confirm which builder Railway used.
6. **Impossible to get runtime logs via project-scoped token**: You MUST have an account-level token to use `railway logs`. Without it, you're flying blind on 502 errors. Always ask the user for an account-level token if debugging is needed.

### Railway Domain URL Pattern

Once deployed, services are typically available at:
- `https://<service-name>.up.railway.app`
- `https://<service-name>-production.up.railway.app`

Check health: `curl https://<service-name>.up.railway.app/api/health`

**Cannot query service public URL via GraphQL API.** The `Service` type does not expose `hostname`, `domain`, or any URL field. The `deployment` query returns `url: null` for successful deployments. Attempted fields that DO NOT EXIST on `Service`: `hostname`, `domain { domain }`, `fqdn`, `redirectHost`. The only ways to discover a service's public URL are:
1. `railway domain` CLI command (requires account-level auth)
2. Railway dashboard UI → service → Settings → Domains
3. Guess the pattern `https://<service-name>.up.railway.app` and verify with `curl`

### 404 "Application not found" vs Real 404

Railway returns `{"status":"error","code":404,"message":"Application not found","request_id":"..."}` (JSON body) when a service domain is wrong OR when a hobby-plan service has gone to sleep. This is distinct from your app returning a normal HTTP 404. If you see this specific JSON response:
1. **Wrong URL pattern** — try `https://<service-name>.up.railway.app` or `https://<service-name>-production.up.railway.app`
2. **Hobby-plan service sleeping** — wake it by hitting the URL (first request may take 30s+)
3. **Domain not generated yet** — run `railway domain` or check the dashboard
4. **No public domain configured** — on hobby plan, Railway may not auto-assign a `.up.railway.app` domain. You need to either run `railway domain` or add a custom domain via the API (see Custom Domain Setup below)

### Custom Domain Setup via GraphQL API

When `railway domain` CLI doesn't work (auth issues), you can create and manage custom domains entirely through the GraphQL API.

#### Create a Custom Domain

```bash
curl -s -H "Authorization: Bearer $RAILWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST https://backboard.railway.app/graphql/v2 \
  -d '{"query":"mutation { customDomainCreate(input: { environmentId: \"ENV_ID\", projectId: \"PROJECT_ID\", serviceId: \"SERVICE_ID\", domain: \"voice.example.com\" }) { ... on CustomDomain { id domain } } }"}'
```

Key fields required: `environmentId`, `projectId`, `serviceId`, `domain`.

#### Query DNS Records for a Custom Domain

After creating the domain, query it to get the required DNS records:

```bash
curl -s -H "Authorization: Bearer $RAILWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST https://backboard.railway.app/graphql/v2 \
  -d '{"query":"{ customDomain(id: \"DOMAIN_ID\", projectId: \"PROJECT_ID\") { id domain status { verified dnsRecords { fqdn hostlabel purpose recordType requiredValue currentValue status zone } verificationDnsHost verificationToken certificateStatus } } }"}'
```

The response includes:
- **dnsRecords**: Each record has `fqdn`, `hostlabel`, `recordType` (CNAME, TXT), `requiredValue` (the target to point to), `purpose`, and `status`
- **verificationDnsHost** / **verificationToken**: For the TXT record proving domain ownership
- **certificateStatus**: `CERTIFICATE_STATUS_TYPE_VALIDATING_OWNERSHIP` means waiting for DNS propagation

#### Typical Cloudflare DNS Setup

For a domain like `voice.example.com` pointing to a Railway service:

1. **CNAME record**: `voice` → `<railway-hash>.up.railway.app` (the `requiredValue` from dnsRecords with purpose `DNS_RECORD_PURPOSE_TRAFFIC_ROUTE`)
2. **TXT record**: `_railway-verify.voice` → `railway-verify=<token>` (from verificationToken field)
3. Wait for DNS propagation (usually 1-5 min with Cloudflare)
4. Re-query the domain status — `verified: true` and `certificateStatus` should advance
5. Only then set the app's `BASE_URL` env var to `https://voice.example.com`

#### GraphQL Schema Introspection Tips

The Railway GraphQL schema is undocumented and evolves. When a query fails with field/type errors, use introspection:

```bash
# Introspect a type
curl -s -H "Authorization: Bearer $RAILWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST https://backboard.railway.app/graphql/v2 \
  -d '{"query":"{ __type(name: \"CustomDomainStatus\") { fields { name type { name kind ofType { name } } } } }"}'
```

Common pattern: union/interface types require `... on TypeName` inline fragments. The `customDomainCreate` mutation returns a union, so use `... on CustomDomain { id domain }`.

## Token Scope Nuances (UUID vs. Account-Level vs. Project-Scoped)

There are THREE types of tokens, each with different capabilities:

| Type | Scope | `whoami` works? | `railway up` works? | GraphQL API? | Created at |
|------|-------|-----------------|---------------------|--------------|------------|
| Account-level API token | Full account | Yes | Yes | Yes | railway.app/account/tokens |
| Project-scoped token | Specific project | No | **Yes** (with `--service/--project/--environment` flags) | Yes (mutations + reads) | GraphQL `projectTokenCreate` mutation |
| OAuth client credentials | OAuth2 flows only | No | No | No | railway.app OAuth app settings |

**Account-level tokens** give full access. **Project-scoped tokens** are created via the `projectTokenCreate` GraphQL mutation and work for both API mutations AND `railway up` CLI deployments (with explicit `--service/--project/--environment` flags).

**CRITICAL**: If you're using an account-level token and `railway up` returns "401 Unauthorized" on the upload phase, create a project-scoped token via `projectTokenCreate` and use THAT for `railway up`. Account-level tokens sometimes get rejected by the upload endpoint.

**Key discovery**: Environment IDs are project-scoped. When creating a new project, query its environments first (`{ project(id) { environments { edges { node { id name } } } } }`) — do NOT reuse environment IDs from other projects.

**Deployment mutations** (discovered via introspection): `serviceInstanceDeploy`, `serviceInstanceDeployV2`, `githubRepoDeploy`, `serviceConnect`, `deploymentTriggerCreate`, `environmentTriggersDeploy`. These are for triggering deployments programmatically but may require higher-scope tokens.

## Introspecting Available Mutations

When you need to find available GraphQL operations:

```bash
curl -s -H "Authorization: Bearer $RAILWAY_TOKEN" \
  -H "Content-Type: application/json" \
  https://backboard.railway.app/graphql/v2 \
  -d '{"query":"{ __schema { mutationType { fields { name } } } }"}' | \
  python3 -c "import sys,json; [print(m['name']) for m in json.load(sys.stdin)['data']['__schema']['mutationType']['fields'] if 'deploy' in m['name'].lower() or 'service' in m['name'].lower()]"
```

## Deployment Strategy When CLI Auth Fails

When `railway whoami` returns Unauthorized (team/project/UUID token):

### Full Programmatic Deployment Flow (Verified 2026-05)

1. Push code to GitHub (`git push origin main`)
2. **Connect repo** using `serviceConnect` mutation:
   ```bash
   curl -s -X POST https://backboard.railway.app/graphql/v2 \
     -H "Authorization: Bearer $RAILWAY_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"query":"mutation { serviceConnect(id: \"SERVICE_ID\", input: { repo: \"owner/repo\", branch: \"main\" }) { id name } }"}'
   ```
   - `serviceConnect` takes `id` (service ID) as a SEPARATE arg, and `input: { branch, image, repo }` as the input object
   - Returns the service `{ id, name }` on success

3. **Trigger deployment** using `serviceInstanceDeploy`:
   ```bash
   curl -s -X POST https://backboard.railway.app/graphql/v2 \
     -H "Authorization: Bearer $RAILWAY_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"query":"mutation { serviceInstanceDeploy(serviceId: \"SERVICE_ID\", environmentId: \"ENV_ID\", latestCommit: true) }"}'
   ```
   - Returns `true` on success (boolean, not a selection set)
   - Works with UUID project-scoped tokens

4. **Monitor deployment** via `project { deployments }`:
   ```bash
   curl -s -H "Authorization: Bearer $RAILWAY_TOKEN" \
     https://backboard.railway.app/graphql/v2 \
     -H "Content-Type: application/json" \
     -d '{"query":"{ project(id: \"PROJECT_ID\") { deployments { edges { node { id status createdAt } } } } }"}'
   ```
   - Status values: `BUILDING` → `DEPLOYING` → `SUCCESS` | `CRASHED` | `FAILED`
   - `CRASHED` = build succeeded, runtime failed (app exits on start)
   - `FAILED` = build step itself failed (Docker/Nixpacks couldn't compile)
   - `REMOVED` = old superseded deployment, not an error

5. **Get build/error info** via `deploymentEvents`:
   ```bash
   curl -s -H "Authorization: Bearer $RAILWAY_TOKEN" \
     https://backboard.railway.app/graphql/v2 \
     -H "Content-Type: application/json" \
     -d '{\"query\":\"{ deploymentEvents(id: \\\"DEPLOY_ID\\\") { edges { node { step createdAt completedAt payload { error } } } } }\"}''
   ```
   - Steps: `SNAPSHOT_CODE` → `BUILD_IMAGE` → `PUBLISH_IMAGE` → `CREATE_CONTAINER` → `CONFIGURE_NETWORK` → `HEALTHCHECK`
   - `BUILD_IMAGE` with `error: "Failed to build an image..."` means the builder (Nixpacks/Railpack/Dockerfile) couldn't compile the app
   - If all steps have `error: null` but status is CRASHED → runtime crash (need `railway logs`)
   - **Important**: The `payload` field is type `DeploymentEventPayload` and requires subfield selection like `{ error }`. Querying just `payload` without subfields causes a GraphQL validation error.

6. **Get deployment metadata** (builder type, startCommand, Dockerfile path):
   ```bash
   # meta is a scalar JSON string, not selectable
   curl -s -H "Authorization: Bearer $RAILWAY_TOKEN" \
     https://backboard.railway.app/graphql/v2 \
     -H "Content-Type: application/json" \
     -d '{"query":"{ deployment(id: \"DEPLOY_ID\") { id status meta } }"}'
   ```
   - `meta` contains: `builder` (DOCKERFILE/NIXPACKS), `startCommand`, `commitHash`, `imageDigest`, `fileServiceManifest`, etc.
   - **Critical**: If Dockerfile exists in repo, Railway uses DOCKERFILE builder even if `railway.json` says NIXPACKS. Delete Dockerfile to force NIXPACKS.

7. **Environment variables** via `variableUpsert` (works with UUID tokens):
   ```bash
   curl -s -X POST https://backboard.railway.app/graphql/v2 \
     -H "Authorization: Bearer $RAILWAY_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"query":"mutation { variableUpsert(input: { name: \"KEY\", value: \"value\", projectId: \"PROJECT_ID\", environmentId: \"ENV_ID\", serviceId: \"SERVICE_ID\" }) }"}'
   ```

8. **CRITICAL LIMITATION**: Runtime logs are NOT accessible via GraphQL API. The `deploymentEvents` only shows infrastructure steps (build, publish, configure). You MUST have an account-level token for `railway logs`, or check the Railway dashboard UI. Without runtime logs, debugging CRASHED deployments is guesswork — you can only see build errors, not application errors.

9. **Build logs for FAILED deploys**: Deployment build logs containing security vulnerability errors or build step failures are NOT accessible via the `deployment` or `deploymentLogs` queries. The `Deployment` type has no `logs` field, and `deploymentLogs(deploymentId)` is not a valid query. Only `deploymentEvents` (infrastructure steps) is available. To get actual build/output logs, you MUST either: (a) use `railway logs --deployment <ID>` with an account-level token, or (b) ask the user to check the Railway dashboard UI.

10. **Nuking a broken service**: When a service has many FAILED deploys and you want a clean slate, use `serviceDelete(id)` to remove it entirely, then `serviceCreate` + `serviceConnect` + `serviceDomainCreate` + `serviceInstanceDeploy` to recreate from scratch. This avoids stale builder caches and configuration drift. Remember to set env vars on the new service before deploying.

### Railway Security Vulnerability Blocking (2026-05)

Railway now scans `package-lock.json` (and likely other lockfiles) for known CVEs during the build phase. If vulnerabilities above a severity threshold are found, the entire deploy is **blocked** with an error like:

```
SECURITY VULNERABILITIES DETECTED
Found 1 vulnerable package(s):
  next@14.2.0
  Severity: HIGH
  Upgrade to 14.2.35: npm install next@^14.2.35
```

**This blocks ALL builders** — Dockerfile, NIXPACKS, and RAILPACK alike. No builder choice will work until the vulnerable dependency is upgraded.

**Fix**: Upgrade the flagged package to the minimum safe version, commit the updated `package-lock.json`, and push. Then redeploy.

**Troubleshooting flow for repeated FAILED deploys**:
1. If you can't get build logs via API, ask the user to check the Railway dashboard or share the build log output
2. The security scan runs before the actual build step, so it will fail before any `npm install` or `apt-get` runs
3. Known affected packages: `next@<14.2.35` (CVE-2025-55184, CVE-2025-67779)

### Next.js on Railway — Common Pitfalls (2026-05)

1. **Dockerfile vs RAILPACK vs NIXPACKS priority**: If a `Dockerfile` exists, Railway ALWAYS uses it regardless of `railway.toml` settings. If no Dockerfile and no explicit builder in `railway.toml`, Railway uses **RAILPACK** (new default builder). If `railway.toml` sets `builder = "NIXPACKS"`, NIXPACKS is used. **Order: DOCKERFILE > explicit builder setting > RAILPACK (auto-detect)**. The deployment meta `builder` field shows which one was used: `"DOCKERFILE"`, `"NIXPACKS"`, or `"RAILPACK"`.

2. **RAILPACK is the new default**: As of 2026-05, Railway uses RAILPACK as the default builder when no Dockerfile and no explicit builder config exists. RAILPACK often succeeds where NIXPACKS fails for Next.js projects. If your NIXPACKS build fails, remove the explicit `builder = "NIXPACKS"` from `railway.toml` and delete any Dockerfile — let RAILPACK auto-detect.

3. **Standalone mode + startCommand**: When using `output: "standalone"` in Next.js config, the `startCommand` must be `node server.js` (not `npx next start`). Without standalone, use `npx next start`. Mismatching these causes 502 errors.

4. **next.config conflicts**: Never have both `next.config.js` and `next.config.mjs`. Merge into one file. When `package.json` has `"type": "module"`, use `.mjs`.

5. **variableUpsert rate limiting**: Setting env vars too fast triggers `"Service deployment rate limit exceeded"`. Add 1-second delays between consecutive mutations.

6. **Standalone mode + Prisma**: When using `output: "standalone"` in Next.js config:
   - Build: `npx prisma generate` must run during the Docker build stage (before `npm run build`)
   - Runtime: `npx prisma db push --skip-generate` must run before `node server.js`
   - The standalone output is at `.next/standalone/` and includes `server.js`, `package.json`, and `node_modules/`
   - You MUST copy `node_modules/@prisma` and `node_modules/.prisma` into the runner stage
   - `railway.json` `startCommand` **overrides** the Dockerfile `CMD`

7. **SQLite on Railway**: Using `file:./dev.db` as `DATABASE_URL`:
   - Works but the DB is ephemeral (lost on redeploy) since Railway containers don't persist filesystem
   - For production, use Railway's built-in PostgreSQL plugin instead
   - Path is relative to container CWD (usually `/app`)

8. **NIXPACKS build failures**: NIXPACKS may fail for Next.js projects with native dependencies (like `bcryptjs` → `bcrypt`). Try RAILPACK by removing explicit builder config, or use Dockerfile for better control.

9. **NEXTAUTH_URL**: Must be set to the actual public URL where the app will be accessed. If not set, NextAuth will fail cookie/session handling. Set it to the Railway domain (`https://<service>.up.railway.app`) or your custom domain.

## GraphQL API Verified Mutations (2026-05)

### Create Project (requires workspaceId)

```bash
# Must include workspaceId — get it from: { me { workspaces { id name } } }
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $RAILWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"mutation { projectCreate(input: {name: \"My Project\", isPublic: true, workspaceId: \"WORKSPACE_ID\"}) { id name } }"}'
```

**Pitfall**: Omitting `workspaceId` causes: `"You must specify a workspaceId to create a project"`

### Create Service (with optional GitHub repo)

```bash
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $RAILWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"mutation { serviceCreate(input: {projectId: \"PROJECT_ID\", name: \"web\", source: {repo: \"owner/repo\"}, branch: \"main\", environmentId: \"ENV_ID\"}) { id name } }"}'
```

`source` and `branch` are optional — you can create a service first, then connect a repo via `serviceConnect`.

### Create Project Token (for `railway up`)

Account-level tokens get 401 on the upload endpoint. Create a project-scoped token for CLI deploys:

```bash
# Returns the token as a plain string
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $RAILWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"mutation { projectTokenCreate(input: {name: \"deploy-token\", projectId: \"PROJECT_ID\", environmentId: \"ENV_ID\"}) }"}'
```

**Critical**: `projectTokenCreate` takes `name` (required, String!), `projectId`, and `environmentId`. It returns a `String!` (the token), NOT an object — do NOT add `{ id token }` subfields.

### Connect GitHub Repo to Service
```bash
# serviceConnect takes id as a top-level arg and input object
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $RAILWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"mutation { serviceConnect(id: \"SERVICE_ID\", input: {repo: \"owner/repo\", branch: \"main\"}) { id name } }"}'
```

### Connect Docker Image to Service
```bash
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $RAILWAY_TOKEN" \
  -H "Content-Type: application/json" \
### Deploy Service
```bash
# V1 returns Boolean! (no subfields, no selection set)
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $RAILWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"mutation { serviceInstanceDeploy(serviceId: \"SERVICE_ID\", environmentId: \"ENV_ID\") }"}'

# V2 returns deployment ID string
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $RAILWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"mutation { serviceInstanceDeployV2(serviceId: \"SERVICE_ID\", environmentId: \"ENV_ID\") }"}'
```

**Key points**:
- V1 takes `serviceId` and `environmentId` as **top-level args** (NOT an `input:` wrapper object)
- V1 returns `Boolean!` — do NOT add `{ id status }` subfields
- V2 is preferred when you need the deployment ID back
- Both trigger a new deployment; pushing to the connected GitHub branch also auto-triggers one
- Each call creates a separate deployment — calling it twice rapidly creates two deploys
```bash
# Use ServiceDomainCreateInput (serviceId + environmentId required)
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $RAILWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"mutation { serviceDomainCreate(input: {serviceId: \"SERVICE_ID\", environmentId: \"ENV_ID\"}) { domain id } }"}'
```

### Delete Service
```bash
# Top-level id arg, NOT input object
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $RAILWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"mutation { serviceDelete(id: \"SERVICE_ID\") }"}'
```

### Get Project Environments
```bash
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $RAILWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"{ project(id: \"PROJECT_ID\") { environments { edges { node { id name } } } } }"}'
```

### GraphQL Schema Introspection Pattern

Many Railway GraphQL mutations differ from what you'd expect. When queries fail:
1. **Check arg structure**: Some use `input:` objects (e.g., `variableUpsert`, `serviceDomainCreate`), others use top-level args (e.g., `serviceDelete`, `serviceInstanceDeploy`)
2. **Check return type**: Some return `Boolean!` (no subfields), others return objects (need `{ id name }` selection)
3. **Introspect**: `{ __type(name: "MutationType") { fields { name args { name type { name } } } } }`
4. **ServiceConnectInput** fields are: `branch`, `image`, `repo` — connect a GitHub repo OR a Docker image

## VarupleUpsert Mutation

**Key field names** (not what you'd expect from REST conventions):
- `name` NOT `key` for variable names
- Returns `Boolean!` — no subfields, just `variableUpsert(input: {...})`
- Required fields: `projectId`, `environmentId`, `name`, `value`
- Optional: `serviceId`, `skipDeploys`

**Pitfall**: Setting `DATABASE_URL=${{POSTGRES.DATABASE_URL}}` only resolves for managed plugin services. For raw containers, set the connection string directly using Railway's internal DNS hostname (e.g., `postgresql://user:pass@postgres:5432/dbname`).

## Binary Location After npm Install

In the Hermes environment, npm global installs go to:
- Binary: `~/.hermes/node/bin/railway`
- Modules: `~/.hermes/node/lib/node_modules/@railway/cli/`

The binary is NOT automatically added to `$PATH`. Either use the full path or:
```bash
export PATH="$HOME/.hermes/node/bin:$PATH"
```