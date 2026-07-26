# Security Audit Prompts

Copy-paste these prompts into your AI coding tool (Claude Code, Cursor, Windsurf, or any agent with codebase access) before every launch. Run them in order.

## Prompt 1: Baseline Security Posture

```
Review my app as a security specialist and make sure I have
strong security headers and a solid baseline security posture.
```

What this catches: missing security headers (CSP, HSTS, X-Frame-Options), insecure cookie settings, missing HTTPS enforcement, and other baseline configuration issues.

## Prompt 2: OWASP Standards Check

```
Review my app against OWASP standards and highlight vulnerabilities.
```

What this catches: SQL injection, XSS, broken authentication, sensitive data exposure, XML external entities, broken access control, security misconfiguration, insecure deserialization, components with known vulnerabilities, and insufficient logging.

## Prompt 3: Data Leak Audit

```
Check my app for any credential or sensitive data leaks in
frontend or API routes.
```

What this catches: `.env` values bundled into frontend code, API responses returning too much data (over-fetching), secrets in log statements, sensitive data in error messages, and PII exposed in network responses.

## Prompt 4: API Key Exposure Check

```
Ensure no API keys are exposed in frontend code or network calls.
```

What this catches: secret keys in frontend bundles, API keys in network requests visible in DevTools, keys committed to version control, and keys in client-side configuration files.

## Prompt 5: Rate Limiting & Cost Protection

```
Review my API routes and serverless functions for rate limiting.
Identify any endpoint that calls a paid API (OpenAI, Anthropic,
Stripe, Resend, Twilio) and ensure it has rate limiting applied.
Flag any endpoint that could be abused to generate unbounded costs.
```

## Prompt 6: Auth Flow Audit

```
Review my authentication flows for security issues. Check for:
user enumeration in signup/login/reset flows, session fixation,
insecure token storage, missing email verification, and whether
error messages reveal whether an account exists.
```

## Claude Code Security Plugin (Paid Plans)

If using Claude Code v2.1.154 or newer with a paid plan:

```
/plugin install claude-security@claude-plugins-official
/reload-plugins
/claude-security
```

This runs a multi-agent vulnerability scanner that:
- Maps your architecture and builds a threat model
- Hunts across 4 categories: injection, auth/access, memory, crypto/secrets
- Uses a 3-agent adversarial panel to filter false positives
- Reports severity, CWE ID, exact file and line
- Can generate patch files for findings

Uses your plan's tokens. Run as the final gate before deploy.

## Post-Fix Verification

After fixing all findings, re-run prompts 1-4 to confirm no regressions. Security fixes can introduce new issues. Never deploy with outstanding warnings.
