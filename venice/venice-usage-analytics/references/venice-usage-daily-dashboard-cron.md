# Venice Daily Dashboard Cron — Fix & Verification Recipe

**Job name:** `venice-usage-daily-dashboard`
**Job ID:** `4a378a1b2ef4`
**Schedule:** `15 20 * * *` (8:15 PM ET)
**Current working model/provider:** `grok-4-20` / `venice` (user forbids all Claude models for cron jobs)

## What the job does

1. Runs `/home/vivgates/venice_usage_dashboard.py`
2. Emails the generated CSV + HTML report to `vivek@live.de`
3. Computes the 24h DIEM window: **8:00 PM ET yesterday → 8:00 PM ET today**
4. Generates a watercolor infographic via Venice `gpt-image-2`
5. Sends the infographic to the Telegram home channel

## Failure signature: `HTTP 404: model: claude-sonnet-4`

When Venice retires a model ID, the cron job fails with:

```
RuntimeError: HTTP 404: model: claude-sonnet-4
```

The request goes to the provider configured on the job. In this case the job had been using provider `anthropic` with model `claude-sonnet-4`, but there was no Anthropic API key in Hermes, so it authed with `Authorization: Bearer None` and hit `api.anthropic.com`.

## Fix

Edit `~/.hermes/cron/jobs.json` directly. Find the job row and set:

```json
{
  "id": "4a378a1b2ef4",
  "model": "grok-4-20",
  "provider": "venice"
}
```

**Do NOT use Claude models** (`claude-sonnet-4`, `claude-sonnet-4-6`, etc.) — the user forbids them for cron jobs and tasks. If `grok-4-20` is retired, pick another current non-Claude Venice model from `/models` (e.g. `kimi-k2-5`, `qwen3-235b-a22b-instruct-2507`).

Also clear stale error state if needed:

```json
  "last_status": "scheduled",
  "last_error": null
```

The scheduler auto-reloads `jobs.json` changes. A `cronjob` tool update may appear to succeed but not persist the change; editing the JSON directly is reliable.

## Verification

Trigger and poll:

```bash
hermes cron run 4a378a1b2ef4
```

Poll until `last_status` is `ok`:

```python
import json, time
path = "/home/vivgates/.hermes/cron/jobs.json"
for _ in range(30):
    with open(path) as f:
        jobs = json.load(f)["jobs"]
    job = next(j for j in jobs if j["id"] == "4a378a1b2ef4")
    print(job["last_run_at"], job["last_status"], job.get("last_error"))
    if job["last_status"] == "ok":
        break
    time.sleep(10)
```

Confirm outputs:

```bash
ls -lt ~/.hermes/cron/output/4a378a1b2ef4/ | head -5
ls -lt ~/.venice_usage_reports/ | head -10
```

Look for:
- New `.md` file in the cron output dir
- Fresh `venice_usage_YYYYMMDD_HHMMSS.csv`
- Fresh `venice_dashboard_YYYYMMDD_HHMMSS.html`
- New `daily_diem_infographic_YYYYMMDD.png`

## Historical note

The model ID evolved from `claude-sonnet-4` (retired) to `claude-sonnet-4-6`, and then was switched to `grok-4-20` after the user forbade all Claude models for cron jobs. When Venice changes model IDs again, the same failure pattern will appear. The fix is always: pick a current **non-Claude** Venice model ID from `/models` (e.g. `grok-4-20`, `kimi-k2-5`, `qwen3-235b-a22b-instruct-2507`) and update the cron job JSON. Never pin this job to a Claude model.

## Automated repair

Use `../scripts/fix_venice_dashboard_cron_model.py` to verify and repair the model/provider in one command.
