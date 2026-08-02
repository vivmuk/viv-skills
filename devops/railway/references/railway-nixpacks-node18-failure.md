# Railway Nixpacks Node Version Build Failure

**Context:** Next.js 16 + Tailwind CSS 4 project deployed on Railway using Nixpacks.

**Symptoms (build log):**
```
[stage-0  8/10] RUN --mount=type=cache,id=...-next/cache,target=/app/.next/cache \
                --mount=type=cache,id=...-node_modules/cache,target=/app/node_modules/.cache \
                npm ci && npm run build
npm warn EBADENGINE Unsupported engine {
  package: 'next@16.2.10',
  required: { node: '>=20.9.0' },
  current: { node: 'v18.20.5', npm: '10.8.2' }
}
npm error code EBUSY
npm error syscall rmdir
npm error path /app/node_modules/.cache
```

**Root cause:** Nixpacks defaulted to Node 18, but the project requires Node ≥ 20.9.0. The `EBUSY` on the cache mount is a secondary failure caused by the engine-mismatch path.

**Fix:**
1. Add `engines.node` to `package.json`:
   ```json
   "engines": { "node": ">=20.9.0" }
   ```
2. Pin Nixpacks to Node 20 with `nixpacks.toml`:
   ```toml
   [variables]
   NIXPACKS_NODE_VERSION = "20"
   ```
3. Add `.nvmrc` for local consistency:
   ```
   20
   ```

**Verification:** Re-run `npm run build` or trigger Railway redeploy. Engine warnings disappear and build succeeds.

**See also:** `railway` skill → "Railway Builders" and "Next.js startCommand must match output mode" sections.