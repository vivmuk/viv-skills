---
name: venice-usage-analytics
title: Venice Usage Analytics & Dashboards
description: Build read-only usage dashboards, automated reports, and long-term cost archives from the Venice.ai billing and admin APIs.
trigger: |
  User asks for Venice.ai usage reports, billing dashboards, daily/weekly/monthly/yearly usage summaries,
  API key utilization, model spend analysis, cost tracking, or rate-limit incident review.
  Also applies when planning automated reports or digging into which keys/agents/models consume resources.
scope: |
  Read-only extraction of billing, usage, and key data from the Venice.ai admin/account API.
  Includes building HTML/CSV dashboards, emailing reports, and maintaining long-term archives.
safety: |
  The Venice admin key is strictly read-only for usage reporting.
  Allowed endpoints: /billing/*, /api_keys, /api_keys/rate_limits, /api_keys/rate_limits/log, /models.
  Never use the admin key for inference, voice cloning, key mutation, or any state-changing call.
  Any non-reporting use of the admin key requires explicit user approval per session.
---

# Venice Usage Analytics & Dashboards

## Goal
Produce detailed, automated, read-only usage dashboards for a Venice.ai account: balances, daily spend,
spend by model and API key, token breakdowns, rate-limit incidents, and long-term archives for yearly reporting.

## What data is available

| Endpoint | Purpose | Notes |
|---|---|---|
| `GET /billing/balance` | Current DIEM/USD balance, epoch allocation, canConsume | Lightweight; call first |
| `GET /billing/usage-analytics?lookback=N` | Aggregated daily/model/key spend | N supports `1d`, `7d`, `30d`, `90d`. Server-side retention is ~90 days; older data must come from a local archive |
| `GET /billing/usage` | Paginated line-item transaction log | Each row has timestamp, SKU, currency, amount, units, requestId, promptTokens, completionTokens, inferenceExecutionTime |
| `GET /api_keys` | All API keys with descriptions, limits, last used, trailing/current usage | Admin key returns all keys on the account |
| `GET /api_keys/rate_limits` | Account-wide RPM/TPM limits per model | Returns limits for the key used; admin key shows paid-tier limits |
| `GET /api_keys/rate_limits/log` | Last 50 rate-limit violations | key/model/type/timestamp |
| `GET /models` | Model catalog | Use to enrich SKU/model IDs with display names and capabilities |

## Excel database

Maintain a master Excel workbook alongside the JSONL archive:

- **Path:** `~/.venice_usage_reports/venice_usage_database.xlsx`
- **Sheets:**
  - `Raw Usage` — every archived row (timestamp, date, SKU, price, units, amount, currency, notes, requestId, execution time, prompt/completion tokens)
  - `Daily Summary` — requests, USD amount, units, tokens aggregated per day
  - `SKU Summary` — total USD, units, requests per SKU/model
  - `Monthly Summary` — requests, USD amount, units per month
- **Update rule:** After each daily dashboard run, rebuild the workbook from the full `usage_archive.jsonl`. This automatically backfills any missing days and keeps all summaries current.
- **Implementation:** Use `pandas` + `openpyxl`. Load the archive, flatten rows with safe handling for `None` inference details, write all four sheets in one `ExcelWriter` pass. Convert UTC timestamps to timezone-naive before writing.

## Important limitations

1. **Usage analytics retention is ~90 days.** The `lookback` parameter accepts `365d` but only returns available history. For yearly reports, maintain a local JSONL archive of `/billing/usage` rows.
2. **Detailed usage log is huge.** As of mid-2026 the account had ~356k rows across ~1,780 pages at 200 rows/page, covering 16 months (2025-02-28 through 2026-06-26). Do not attempt a full backfill in one run; chunk it by page ranges (e.g. 500 pages per background process) and resume safely because the archive deduplicates by `(timestamp, sku, requestId)`.
3. **Pagination defaults to a small page size.** Use `?limit=200` (the observed supported maximum) when calling `/billing/usage` to minimize API round trips. Inspect `x-total-count` or the response headers to compute total pages.
4. **`/billing/usage-analytics` only retains ~90 days.** Do not rely on it for yearly reports; build them from the local archive.
5. **`inferenceDetails` can be `None`.** Always access as `item.get("inferenceDetails") or {}`.
6. **Admin key has a 1 DIEM/epoch inference limit.** Do not use it for running models.
7. **Model names from usage log come from SKUs.** Parse SKUs (e.g. `kimi-k2-7-code-llm-cache-input-mtoken`) to derive category and token type; map to display names from `/models` or from the analytics endpoint.
8. **Archives compress well.** A 117 MB JSONL archive compressed to ~8.6 MB with gzip. Keep a `.gz` backup alongside the live archive.
9. **Image generation uses a different endpoint.** Use the OpenAI-compatible `POST /images/generations`, not `/image/generate`. The `gpt-image-2` model enforces a hard **1500-character prompt limit**; compress the prompt aggressively to fit all data. Response contains `data[0].b64_json`.

## Token-first metrics

Usage dashboards should lead with these metrics, computed from the archive:

| Metric | Formula | Notes |
|---|---|---|
| Total DIEM | `sum(abs(amount))` for DIEM rows | Primary headline |
| Total input tokens | `sum(promptTokens)` across deduplicated requests | Deduplicate by `requestId` to avoid double-counting rows per SKU |
| Total output tokens | `sum(completionTokens)` across deduplicated requests | Same deduplication |
| Input/output ratio | `input_tokens / output_tokens` | High ratios signal RAG/agentic/large-context workloads |
| Cost per 1K tokens | `total_diem / (total_tokens / 1000)` | Blended across modalities; lower for high-volume LLMs, higher for image/video |
| Cost per request | `total_diem / unique_requests` | Useful for budget alerts |

When asked "how much this year", filter the archive by `timestamp.year == 2026` and report total DIEM, request count, input/output tokens, top categories, and top models for that year.

## Admin key management

- Store the full admin key (including the `VENICE_ADMIN_KEY_` prefix) in a restricted `.env` file, not in the script or in shell history.
- **Path:** `~/.venice_usage_reports/.env` with permissions `600`.
- **Contents:** `VENICE_ADMIN_KEY=VENICE_ADMIN_KEY_...`
- Have the dashboard script auto-load this file at startup before reading `os.environ["VENICE_ADMIN_KEY"]`.
- This keeps the key out of git/cron logs and lets the daily cron job run without exporting secrets in the cron definition.

## Recommended workflow

1. **Confirm scope:** Is this a one-off report, a scheduled daily email, or a yearly deep dive?
2. **Authenticate with admin key** from environment variable `VENICE_ADMIN_KEY` (loaded from the restricted `.env` file).
3. **Fetch in this order:** balance → analytics (1d/7d/30d/90d) → keys → rate limits + log → usage log (last 1-2 days) → models.
4. **Archive:** Append every new usage-log row to `~/.venice_usage_reports/usage_archive.jsonl`, deduplicated by `(timestamp, sku, requestId)`.
5. **Excel database:** Rebuild `venice_usage_database.xlsx` from the full archive after every archive update so missing days are backfilled and summaries stay current.
6. **Analyze:** Group by model, key, SKU, category (LLM/IMAGE/VIDEO/TTS/STT/EMBEDDING/TOOL), and hour.
7. **Generate:** Produce an HTML dashboard with tables and bar charts, plus a CSV of raw line items.
8. **Deliver:** Email HTML + CSV via Gmail SMTP, or save locally for inspection. When the user prefers email or an HTML file is too large for Telegram, use the existing `vega_mail.py` helper at `~/vega_mail.py` (Gmail SMTP) and attach the `.html` file.
9. **Schedule:** Create a cron job if the user wants daily delivery.

## Safety checklist

- [ ] Admin key is only used for GET /billing/*, GET /api_keys*, GET /models
- [ ] No POST/DELETE/PATCH calls with the admin key
- [ ] No inference calls with the admin key
- [ ] If user asks for anything outside usage reporting, ask for explicit approval before using the admin key

## Pitfalls

- Assuming `inferenceDetails` is always present will crash the script.
- Trying to backfill all usage-log pages at once will time out and waste API quota.
- Using `item.get("inferenceDetails", {}).get(...)` still crashes when the value is explicitly `null`.
- Saving only the key suffix (after `VENICE_ADMIN_KEY_`) to `.env` causes a 401 Unauthorized. Save the full token including the prefix.
- Forgetting to rebuild the Excel database after adding new archive rows leaves the workbook stale with missing days.
- The analytics `byModel` field sometimes returns `modelType: null` for non-LLM services; fall back to SKU parsing.
- When generating an HTML dashboard from the local archive, the user may not see it in Telegram if the file is rendered as a generic attachment. Offer to email it via the configured `vega_mail.py` helper.
- When the user asks for yearly or "this year" usage, build the answer from the local archive (filtering rows by `timestamp` year) rather than the analytics endpoint, which lacks full-year retention.
- Always surface **input vs output token totals** as first-class metrics in usage dashboards; the user's follow-up question showed this is expected, not buried.
- The Venice `gpt-image-2` model is called through `POST /api/v1/image/generate` (not `/images/generations`). It returns `data["images"][0]` as a **base64 string**; decode with `base64.b64decode(...)` and save the bytes. It enforces a hard **1500-character prompt limit** and resolution values of `"1K"`/`"2K"`/`"4K"`; pixel dimensions like `"1440x2560"` return `400`. For data-dense infographics, write a dense comma-separated prompt rather than long prose.
- If you generate an infographic and the user previously asked for an HTML dashboard, proactively send both via email with clear subject lines.

## Daily dashboard cron job

The live daily dashboard is driven by a Hermes cron job (`venice-usage-daily-dashboard`, ID `4a378a1b2ef4`) that runs at `15 20 * * *` (8:15 PM ET). It runs `/home/vivgates/venice_usage_dashboard.py`, emails the report, computes the prior 24h DIEM window (8 PM ET → 8 PM ET), generates a watercolor infographic via Venice `gpt-image-2`, and sends the infographic to Telegram.

### Keeping the cron job healthy

1. **Model IDs retire.** The job historically used `claude-sonnet-4`, which Venice removed, then `claude-sonnet-4-6` — but the **user forbids all Claude models** for cron jobs and tasks. The current working model is `grok-4-20` via provider `venice`. Do NOT pin this job to any `claude-*` model.
2. **If the job fails with `HTTP 404: model: …`**, update the model in `~/.hermes/cron/jobs.json` directly, then reload:
   ```bash
   python3 ~/.hermes/skills/venice/venice-usage-analytics/scripts/fix_venice_dashboard_cron_model.py
   ```
   The script defaults to `grok-4-20`. If you change the default, keep it non-Claude.
3. **Verify after any change:** Run the job immediately and poll until `last_status` becomes `ok`:
   ```bash
   hermes cron run 4a378a1b2ef4
   # Then watch:
   python3 -c "import json,time; [print((d:=json.load(open('/home/vivgates/.hermes/cron/jobs.json')))['jobs'][2]['last_status']) or time.sleep(10) for _ in range(30)]"
   ```
4. **Confirm outputs:** Check `~/.hermes/cron/output/4a378a1b2ef4/` for the latest `.md`, and `~/.venice_usage_reports/` for fresh CSV/HTML/PNG files.

See `references/venice-usage-daily-dashboard-cron.md` for full fix/verification transcript and `scripts/fix_venice_dashboard_cron_model.py` for the automated repair script.

## Reusable assets

- `references/venice-usage-endpoints.md` — endpoint details and response field notes
- `references/venice-usage-backfill-and-endpoints.md` — pagination strategy, working/non-working endpoint inventory, archive tips
- `references/venice-usage-script.md` — known-good dashboard generator pattern and archive strategy
- `references/venice-usage-dashboard-design-patterns.md` — design recipes for high-impact executive dashboards from the archive: Swiss typography/grid style, data-to-JSON preprocessing, Chart.js interactive charts, and email delivery via `vega_mail.py`
- `references/venice-usage-infographic-recipe.md` — prompt recipe and exact parameters for generating dense data infographics with Venice `gpt-image-2`
- `references/daily-infographic-from-csv-recipe.md` — step-by-step recipe for aggregating the daily dashboard CSV and generating a shareable watercolor infographic
- `references/venice-usage-daily-dashboard-cron.md` — cron job fix/verification recipe when model IDs retire or the daily run fails
- `scripts/venice_usage_archive_dashboard.py` — offline HTML dashboard generator from the local JSONL archive (monthly breakdown, 7-day rolling average, top models by category)
- `scripts/analyze_venice_usage_archive.py` — quick offline analysis of `usage_archive.jsonl`: monthly totals, last-N-day category breakdown, top models, and hourly today view
- `scripts/venice_usage_dashboard.py` — starter report generator script (live instance at `/home/vivgates/venice_usage_dashboard.py`)
- `scripts/fix_venice_dashboard_cron_model.py` — verify/repair the daily dashboard cron job model/provider after a model retirement

## Archive schema

`~/.venice_usage_reports/usage_archive.jsonl` stores one raw `/billing/usage` row per line. The schema is not transformed:

```json
{
  "timestamp": "2026-06-26T11:11:34.193Z",
  "sku": "kimi-k2-7-code-llm-cache-input-mtoken",
  "pricePerUnitUsd": 0.2,
  "units": 0.084096,
  "amount": -0.0168192,
  "currency": "DIEM",
  "notes": "API Inference",
  "inferenceDetails": {
    "requestId": "chatcmpl-a5e9a13d2c335ddc",
    "inferenceExecutionTime": 4433,
    "promptTokens": 84306,
    "completionTokens": 214
  }
}
```

New rows are appended by `update_archive()` in the dashboard script and deduplicated by `(timestamp, sku, requestId)`. Existing rows are never mutated.

## When to escalate

- If voice cloning or model access errors appear, those are account/plan issues, not usage-reporting issues. Route to Venice support, do not try to bypass with the admin key.
- If the user asks to modify API keys, limits, or billing settings, stop and ask for explicit confirmation; these are outside this skill's scope.