---
name: hermes-cron-ops
description: "Manage, audit, and troubleshoot Hermes cron jobs — model pinning, output logs, silent failure debugging, and model policy enforcement."
version: 1.0.0
author: Vega
metadata:
  hermes:
    tags: [hermes, cron, scheduling, operations, troubleshooting, model-management]
---

# Hermes Cron Job Operations

Manage, audit, and troubleshoot Hermes cron jobs. Covers model pinning, silent failure debugging, output log analysis, and model policy enforcement.

## When to Load

- User asks to audit, review, or check cron jobs
- A cron job fails (`last_status: error`) and needs debugging
- User wants to change or standardize models across cron jobs
- User wants to ensure specific models are/aren't being used
- Setting up a new cron job that needs a stable model pin

## Core Operations

### List All Jobs
```
cronjob action=list
```
Returns all jobs with: `job_id`, `name`, `model`, `provider`, `schedule`, `last_run_at`, `last_status`, `next_run_at`, `enabled`.

Key fields to audit:
- `model: null` → **DANGER** — job inherits default session model (see Pitfalls)
- `last_status: "error"` → needs investigation
- `enabled: false` → job is paused

### Update a Job's Model
```
cronjob action=update job_id=<id> model={"model": "grok-4-20", "provider": "venice"}
```
The `model` parameter takes an object with `model` and `provider` keys. Both must be set together.

### Read Output Logs
Cron run outputs are stored as markdown files at:
```
~/.hermes/cron/output/<job_id>/<YYYY-MM-DD_HH-MM-SS>.md
```
Each file contains: the prompt, any tool output, and an `## Error` section if the run failed. To debug a failed run, read the most recent file for that job ID.

### Trigger a Test Run
```
cronjob action=run job_id=<id>
```
Runs the job immediately instead of waiting for the next scheduled tick.

## Pitfalls

### CRITICAL: Always Pin Model+Provider on Every Cron Job

**Problem:** Cron jobs without an explicit model pin (`model: null`) inherit the **default session model** at runtime. If the default model changes (e.g., user switches models) or is **deprecated by the provider** (e.g., Venice removes a model from their catalog), the cron job will silently fail with an HTTP 404 error.

**Real example (2026-07-19):** The "Vega shared brain backup" cron job ran successfully for months with no model pin. On July 19, the default session model was `openai-gpt-56-luna-pro`, which Venice had deprecated. The job crashed at startup:
```
RuntimeError: HTTP 404: {"error":"Specified model not found: venice/openai-gpt-56-luna-pro. Did you mean: openai-gpt-56-luna-pro, e2ee-venice-uncensored-24b-p, openai-gpt-54-pro?"}
```
The actual backup it was monitoring was fine (`exit=0, errors=0`) — only the verification cron broke.

**Fix:** Pin every cron job to a specific model+provider:
```
cronjob action=update job_id=<id> model={"model": "grok-4-20", "provider": "venice"}
```

**Audit pattern:** When reviewing cron jobs, flag every job where `model` is `null`. These are time bombs — they work today but will break when the default model changes or is deprecated.

### Model Policy: No Claude Models for This User

This user does not want Claude models (`claude-sonnet-4`, `claude-sonnet-4-6`, etc.) used for any task or cron job. When auditing cron jobs:

1. Check `model` field for any `claude-*` variant
2. Replace with a non-Claude alternative
4. Preferred replacements on Venice: `grok-4-20`, `zai-org-glm-5-2`, `gemini-3-5-flash-lite` (for token-conscious jobs)
4. Verify the change took effect with a follow-up `cronjob action=list`

This preference is also in user memory, but the operational check belongs here.

### CRITICAL: Cron Jobs Going [SILENT] Instead of Executing

**Problem:** A cron job's `last_status` shows `"ok"` but the job didn't actually do anything — it returned `[SILENT]` instead of executing its pipeline. This is a **silent delivery failure**: no email sent, no infographic generated, no Telegram message posted. The cron system reports success because the model responded cleanly, but the model chose to suppress output rather than run the steps.

**Real example (2026-07-20 & 2026-07-21):** The Venice usage dashboard cron (`4a378a1b2ef4`) was switched from GLM 5.2 to `grok-4-20`. For two consecutive days, grok-4-20 returned `[SILENT]` without running the dashboard script, generating the infographic, emailing the report, or posting to Telegram. The user noticed when they didn't receive their daily dashboard.

**Detection:** When a cron job's output file is suspiciously small (under ~3KB for a multi-step pipeline) or contains only `[SILENT]` as the response, investigate:
```bash
# Check output file size — small files are suspicious
ls -la ~/.hermes/cron/output/<job_id>/ | tail -5
# Read the latest output — look for [SILENT] as the entire response
```

**Fix:** When a prompt has mandatory delivery steps (email, Telegram, image generation):
1. Add explicit instructions: `IMPORTANT: Never return [SILENT]. Always execute all steps and deliver the infographic.`
2. Make each step's output a required part of the final response
3. Consider whether the model is appropriate for multi-step tool-use tasks — some models are more prone to going silent than others

### Don't Assume the Underlying Task Failed

When a watchdog/verification cron fails, the system it monitors may still be healthy. Always check the actual logs of the monitored process, not just the cron output. Example: the backup verification cron failed (model 404), but the actual backup log showed `exit=0, errors=0` — the backup was fine, only the verifier was broken.

## Debugging Workflow

1. **List jobs** — `cronjob action=list` — identify any with `last_status: "error"`
2. **Find the job's output directory** — `~/.hermes/cron/output/<job_id>/`
3. **Read the latest output file** — look for `## Error` section at the bottom
4. **Identify root cause** — common causes:
   - Model 404 (deprecated model) → pin a current model
   - API key error → check `.env` or credential config
   - Timeout → simplify the job's prompt or reduce scope
   - Tool error → check if required toolsets are enabled for the job
5. **Fix and verify** — update the job, then trigger a test run with `cronjob action=run`

## Verification Checklist

After making changes to cron jobs:
- [ ] `cronjob action=list` confirms `model` field shows the new model (not `null`)
- [ ] `provider` field matches the expected provider
- [ ] No `claude-*` models appear anywhere in the job list
- [ ] `next_run_at` shows a valid upcoming time
- [ ] `enabled: true` for all jobs that should be active

## Verifying Model Availability on Venice

When a user requests a model that isn't in the local OpenClaw catalog or seems unfamiliar, **always verify against the Venice API directly** before telling the user it doesn't exist:

```bash
curl -s --max-time 15 "https://api.venice.ai/api/v1/models" \
  -H "Authorization: Bearer $(grep -oP 'VENICE_INFERENCE_KEY_[A-Za-z0-9_-]+' ~/.openclaw/openclaw.json | head -1)" | \
  python3 -c "import json,sys; d=json.load(sys.stdin); [print(m['id']) for m in d.get('data',[])]" | \
  grep <model-name>
```

The local catalog (`~/.openclaw/agents/<name>/agent/plugins/venice/catalog.json`) is generated once and can be stale. The API is the source of truth.

## References

- `references/model-audit-2026-07-20.md` — session-specific audit log from the July 2026 cron review (includes OpenClaw Kriya model change)
