# Cron Model Audit — 2026-07-20

## Context

User asked: "Don't use any Claude models. Did you use any today?" — then asked to audit all cron jobs for Claude model usage. Then asked to fix a failed job. Then asked to change Kriya (OpenClaw agent) model.

## Cron Job Findings

3 active cron jobs:

| Job ID | Name | Model Before | Model After |
|--------|------|-------------|-------------|
| `ace58b1260ce` | Weekly Activity Infographic | `null` (default) | `grok-4-20` (venice) |
| `04942dfe6ec2` | Vega shared brain backup (3am) | `null` (default) | `grok-4-20` (venice) |
| `4a378a1b2ef4` | venice-usage-daily-dashboard | `claude-sonnet-4-6` (venice) | `grok-4-20` (venice) |

## Issues Found

### 1. Venice usage dashboard was using Claude Sonnet 4-6
- User explicitly does not want Claude models
- Switched to `grok-4-20` via `cronjob action=update`

### 2. Shared brain backup cron was silently broken
- `last_status: "error"` on 2026-07-19 03:05 AM ET
- Root cause: job had `model: null`, inherited default session model `openai-gpt-56-luna-pro`
- Venice had deprecated that model → HTTP 404 at startup
- The actual backup system was healthy (log showed `exit=0, errors=0`)
- Only the verification cron was broken — never reported because it crashed before it could send an alert
- Fix: pinned to `grok-4-20` (venice)

### 3. Two jobs had no model pin at all
- Both inherited the default session model at runtime
- This is fragile: if the default changes or is deprecated, the job breaks silently
- Fix: pinned both to `grok-4-20` (venice)

## OpenClaw Agent Model Change

User asked to change Kriya from `venice/zai-org-glm-5-2` to `venice/minimax-m3-preview`.

- Local `catalog.json` at `~/.openclaw/agents/kriya/agent/plugins/venice/catalog.json` did NOT list `minimax-m3-preview`
- User insisted it was available — queried Venice API directly: `curl -s https://api.venice.ai/api/v1/models -H "Authorization: Bearer <key>"` confirmed `minimax-m3-preview` exists
- Updated two places in `~/.openclaw/openclaw.json`:
  1. `agents.list[].model` → `venice/minimax-m3-preview` (for the kriya agent)
  2. `agents.defaults.models` → added `"venice/minimax-m3-preview": {}`
- Gateway hot-reloads config — no restart needed

## Resolution

All 3 Hermes cron jobs pinned to `grok-4-20` on Venice. Kriya (OpenClaw) set to `venice/minimax-m3-preview`. No Claude models anywhere. No jobs depending on the default session model.

## Key Lessons

1. **Always pin cron job models** — unpinned jobs inherit the default, which can change or be deprecated
2. **Don't trust local model catalogs** — query the Venice API directly to verify model availability. The OpenClaw `catalog.json` is generated once and can be stale.
3. **No Claude models** — user preference enforced across all cron jobs and OpenClaw agents
4. **Named agent model changes need 2 updates** in `openclaw.json`: `agents.list[].model` and `agents.defaults.models`
