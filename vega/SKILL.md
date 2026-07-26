---
name: vega-app-dev-qa
description: Comprehensive pre-build Q&A and post-build security checklist for AI-assisted app development. Use when building any app that collects user data, calls paid APIs, or ships publicly. Enforces a mandatory Q&A session before coding begins and a 30-minute security audit before launch. Incorporates legal, database, auth, API key, and infrastructure protections directly into the application.
version: 1.0.0
author: Vega
license: MIT
metadata:
  hermes:
    tags: [app-dev, security, qa, pre-launch, checklist, vibe-coding, owasp]
    related_skills: [requesting-code-review, plan, writing-plans]
---

# Vega App Dev Q&A and Security Protocol

Two non-negotiable gates around every app build:

1. **Pre-build Q&A** — a structured interview before writing a single line of code.
2. **Pre-launch security audit** — a 30-minute checklist run before every deploy.

Skipping either gate is shipping a liability.

## Phase 1: Pre-Build Q&A (Before Coding)

Before any code is written, the agent must conduct a Q&A session with the user. Do not skip questions. Do not assume answers. Ask each question, wait for the user's response, and record it in the project's design document.

### Mandatory Questions

**Data & Legal**
1. Will this app collect any user data? If yes, what specifically (email, name, phone, payment, health, location)?
2. Where will user data be stored (Supabase, Firebase, Postgres, other)? Which region?
3. Will you sell, share, or export user data to any third party?
4. Do you have a privacy policy? If not, generate one before launch (Termly, PrivacyPolicies.com).
5. Is any of the data regulated (HIPAA, GDPR, CCPA, financial)? If yes, this checklist is the floor — a real compliance audit is required on top.

**Authentication**
6. What auth provider will you use (Supabase Auth, Clerk, Auth0, custom)?
7. Will you support social login, email/password, or both?
8. Will you implement password reset flows? Email verification?

**Paid APIs & Costs**
9. Will the app call any paid APIs (OpenAI, Anthropic, Stripe, Resend, Twilio)?
10. What are the expected cost per request and daily volume?
11. Have you set hard daily spend caps in each provider's dashboard?

**Infrastructure**
12. Where will the app be deployed (Vercel, Railway, Render, self-hosted)?
13. Will you use Supabase, Firebase, or another backend with direct database access from the client?
14. Will there be public forms (contact, signup, waitlist) exposed to the internet?

**Scope & Timeline**
15. What is the MVP scope? List the must-have features only.
16. What is the launch timeline?
17. Who are the first users (internal team, beta group, public)?

### Post-Q&A: Generate a Design Document

After the Q&A, produce a design document that includes:

- App summary and MVP scope
- Data flow diagram (user → frontend → API → database → third-party services)
- Auth model
- API consumption and cost projections
- Security plan referencing each item in Phase 2 below
- Architecture decisions and trade-offs

Only after the user approves the design document, begin coding.

## Phase 2: Pre-Launch Security Audit (30 Minutes)

Run this checklist before every deploy. Not once at the start — before every launch.

### Step 1: Legal Protection (10 min)

- [ ] Privacy policy exists and is linked in the app (even if generated).
- [ ] You know exactly where user data lives ( Supabase region, Vercel region, any third-party ).
- [ ] No selling or exporting user data to personal accounts.
- [ ] No plaintext password storage anywhere.
- [ ] If AI-generated code: understand it may not be copyrightable in the US. Do not rely solely on AI-generated code for IP protection.
- [ ] Check for GPL contamination: if AI pulled in GPL-licensed code, the entire codebase may need to be open-sourced. Run a license scan.

### Step 2: Database Lockdown (5 min)

- [ ] **Row Level Security (RLS) enabled** on every Supabase table. Zero policies = naked database. Anyone can query it from DevTools.
- [ ] **Server-side validation on every form.** Zod on the client is UX, not security. Attackers can bypass JavaScript and send raw requests. Validate data types, length limits, and sanitize inputs on the server.
- [ ] **Error messages do not leak data.** Never expose table names, column names, SQL queries, or stack traces to the user. Log full errors server-side. Show generic messages ("User not found") to users.

### Step 3: Auth Failure Testing (10 min)

Test each of these manually before launch:

- [ ] Log in with wrong password 5 times in a row. Does the account lock? Does the error message confirm the email exists (it should not)?
- [ ] Reset password for a non-existent email. Does the response reveal whether the email is in the system?
- [ ] Click an email verification link twice. Does it break or handle gracefully?
- [ ] Sign up with an already-registered email. Does it leak that the user exists?
- [ ] Test session expiry and token refresh behavior.

### Step 4: API Key & Secrets Audit (3 min)

- [ ] **No secret keys in frontend code.** Search the frontend bundle for: `sk_`, `service_role`, `SECRET`, `PRIVATE_KEY`, API keys without `publishable` or `anon` prefix.
- [ ] Public keys (Supabase anon, Stripe publishable) are OK in frontend.
- [ ] Secret keys (Supabase service role, Stripe secret, OpenAI, Anthropic) must be server-side only — stored in environment variables or edge function secrets.
- [ ] No secrets in version control. Check `.gitignore` covers `.env`, `.env.local`, `.env.production`.
- [ ] If any key may have been exposed: regenerate it immediately. Do not wait. GitHub repos get scraped for keys within minutes.

### Step 5: Infrastructure Protection (2 min)

- [ ] **Rate limits** on every endpoint that hits a paid API. Baseline: 100 req/min per IP for public endpoints, 1,000 req/min for authenticated users. Use Upstash for Supabase Edge Functions.
- [ ] **Hard daily spend caps** set in OpenAI, Anthropic, and other paid API dashboards.
- [ ] **Alerts at 50% of daily cap** so you catch a spike before morning.
- [ ] **CAPTCHA on every public form.** Cloudflare Turnstile is free and privacy-focused. 10-minute integration.
- [ ] **CORS restrictions.** Specify allowed domains explicitly. Allow production domain + localhost for testing. Block everything else.

### Step 6: AI-Powered Security Scan (Final Gate)

Run these 4 prompts inside your AI coding tool (Claude Code, Cursor, etc.) before every launch:

**Prompt 1 — Baseline security posture:**
```
Review my app as a security specialist and make sure I have
strong security headers and a solid baseline security posture.
```

**Prompt 2 — OWASP standards check:**
```
Review my app against OWASP standards and highlight vulnerabilities.
```

**Prompt 3 — Data leak audit:**
```
Check my app for any credential or sensitive data leaks in
frontend or API routes.
```

**Prompt 4 — API key exposure check:**
```
Ensure no API keys are exposed in frontend code or network calls.
```

If using Claude Code with a paid plan (v2.1.154+), also run:
```
/plugin install claude-security@claude-plugins-official
/reload-plugins
/claude-security
```
This runs a multi-agent vulnerability scanner across injection, auth/access, memory, and crypto/secrets categories.

**Fix everything flagged. Do not ship with warnings. Security debt compounds faster than feature debt.**

## Phase 3: Bake Security Into the Application

These protections must be part of the application code itself, not just a one-time check:

### In the codebase
- Use environment variables for all secrets. Never hardcode keys.
- Implement server-side validation on every API route (Zod, Joi, or equivalent).
- Use parameterized queries only. No string-concatenated SQL.
- Set security headers via middleware or framework config (Helmet for Express, `next.config.js` headers for Next.js).
- Implement rate limiting middleware on all public endpoints.
- Use HTTP-only, secure, same-site cookies for auth tokens.
- Sanitize all user input before rendering (prevent XSS).
- Use `dangerouslySetInnerHTML` never, or only with sanitized content.

### In the database
- Enable RLS on every table from day one.
- Write policies that restrict CRUD operations to the authenticated user.
- Test policies by querying as a different user.
- Use database-level constraints (not null, unique, check) as a second layer.

### In the deployment
- Set CORS to allow only production domain + localhost.
- Enable Cloudflare Turnstile (or reCAPTCHA) on all public forms.
- Configure environment variables in the deployment platform (Vercel, Railway), not in the codebase.
- Set up uptime monitoring and error tracking (Sentry, LogRocket).
- Configure spend alerts on all paid API dashboards.

## When to Use This Checklist

**Always use when:**
- Shipping any app that collects user data, even just an email
- Running on Supabase, Firebase, or any backend with database access
- Calling paid APIs (OpenAI, Anthropic, Stripe) from the codebase
- About to share the app publicly for the first time

**Phase in slowly when:**
- Shipping internal tools used only by your own team behind auth
- Working with a security team that already runs a more comprehensive audit
- In pre-MVP exploration mode and not collecting any user data yet

## What This Checklist Is Not

This checklist gets you to a confident baseline, not enterprise-grade compliance. If you are storing health data, financial data, or anything regulated, you need a real security audit on top of this.

AI prompts and scanners catch surface-level issues. They do not catch business logic vulnerabilities, complex auth state bugs, or sophisticated injection attacks. Treat them as the floor, not the ceiling.

## References

- [references/security-prompts.md](references/security-prompts.md) — Copy-paste security audit prompts for Claude Code, Cursor, and other AI coding tools
- [references/rls-templates.md](references/rls-templates.md) — Supabase RLS policy templates for common table patterns
- [references/legal-checklist.md](references/legal-checklist.md) — Legal protection details including 2026 AI copyright rulings and GPL contamination risks
