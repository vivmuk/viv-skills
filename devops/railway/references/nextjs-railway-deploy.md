# Next.js on Railway — Deployment Guide & Pitfalls

## Builder Selection: Dockerfile vs NIXPACKS

Railway auto-detects the build system. **If a `Dockerfile` exists in the repo root, Railway always uses it** — even if `railway.json` specifies `"builder": "NIXPACKS"`. The deployment metadata will show `builder: "DOCKERFILE"`.

To force NIXPACKS: delete the Dockerfile and set `"builder": "NIXPACKS"` in `railway.json`.

## Dockerfile for Next.js Standalone Mode

When using `output: "standalone"` in `next.config.ts`:

```dockerfile
FROM node:20-alpine AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npx prisma generate
RUN npm run build

# Production image
FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/prisma ./prisma
COPY --from=builder /app/node_modules/.prisma ./node_modules/.prisma
COPY --from=builder /app/node_modules/@prisma ./node_modules/@prisma

USER nextjs

EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
```

**Critical copies for Prisma**: You MUST copy both `node_modules/.prisma` and `node_modules/@prisma` into the runner stage. Without these, Prisma Client will not be found at runtime.

**`.dockerignore`** — Always include one:
```
node_modules
.next
.git
.env
.env.local
*.md
```

## `railway.json` startCommand Overrides Dockerfile CMD

If `railway.json` has a `startCommand`, it **overrides** the Dockerfile `CMD`. This is useful for running Prisma migrations before starting the app:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "deploy": {
    "startCommand": "npx prisma db push --skip-generate && node server.js",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

`npx prisma db push --skip-generate` creates/migrates the SQLite DB file on container start. The `--skip-generate` flag avoids re-running `prisma generate` (already done in build stage).

## SQLite on Railway — Ephemeral Warning

Using `file:./dev.db` as `DATABASE_URL`:
- **Works** for testing/demos, but the database is **ephemeral** — lost on every redeploy
- Path is relative to container CWD (usually `/app`)
- For production, use Railway's built-in PostgreSQL plugin instead

## NextAuth (Auth.js v5) on Railway

Key env vars:
- `NEXTAUTH_SECRET` — Generate with `openssl rand -hex 32` or `node -e "console.log(require('crypto').randomBytes(32).toString('base64'))`
- `NEXTAUTH_URL` — Must match the actual public URL (e.g., `https://your-app.up.railway.app` or custom domain)
- If using credentials provider only (no Google/GitHub OAuth), you don't need `GOOGLE_CLIENT_ID` etc.

## Credentials-Only Auth (No Google OAuth)

For MVP/quick deploy, use NextAuth v5 credentials provider instead of OAuth:

```typescript
// src/lib/auth.ts
import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";
import bcrypt from "bcryptjs";
import { prisma } from "@/lib/prisma";

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [
    Credentials({
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      authorize: async (credentials) => {
        const user = await prisma.user.findUnique({
          where: { email: credentials.email as string },
        });
        if (!user || !user.image) return null; // image field stores bcrypt hash
        const valid = await bcrypt.compare(credentials.password as string, user.image);
        if (!valid) return null;
        return { id: user.id, email: user.email, name: user.name };
      },
    }),
  ],
  session: { strategy: "jwt" },
});
```

Signup route (`/api/auth/signup/route.ts`):

```typescript
import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import bcrypt from "bcryptjs";

export async function POST(req: NextRequest) {
  const { email, password, name } = await req.json();
  if (!email || !password) {
    return NextResponse.json({ error: "Email and password required" }, { status: 400 });
  }
  const existing = await prisma.user.findUnique({ where: { email } });
  if (existing) {
    return NextResponse.json({ error: "User already exists" }, { status: 409 });
  }
  const hash = await bcrypt.hash(password, 12);
  const user = await prisma.user.create({
    data: { email, name: name || email.split("@")[0], image: hash },
  });
  return NextResponse.json({ id: user.id, email: user.email });
}
```

## Debugging CRASHED Deployments Without CLI Access

When `railway logs` is unavailable (team/project token auth failure):

1. **Check deployment events**: `deploymentEvents(id)` → shows build step progress
2. **Check deployment metadata**: `deployment(id) { meta }` → reveals builder, startCommand, Dockerfile path
3. **Common crash causes**:
   - Missing env vars (NEXTAUTH_URL, NEXTAUTH_SECRET, DATABASE_URL)
   - Prisma Client not generated (missing `npx prisma generate` in build)
   - SQLite path issues (`file:./dev.db` in standalone mode)
   - Port not reading `PORT` env var (Railway assigns dynamic port)
   - `bcryptjs` vs `bcrypt` — use `bcryptjs` for pure JS, avoid native `bcrypt` module
4. **NIXPACKS build failure**: May fail for Next.js with native deps — use Dockerfile instead
5. **If all else fails**: Get an account-level API token from railway.app/account/tokens, then `railway logs` works

## Programmatic Deployment via GraphQL API

See `references/railway-api-quirks.md` → "Deployment Strategy When CLI Auth Fails" for the complete flow: `projectCreate` → `serviceCreate` → `variableUpsert` → `serviceConnect` → `serviceInstanceDeploy`.