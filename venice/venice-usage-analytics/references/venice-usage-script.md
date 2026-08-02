# Venice Usage Dashboard — Script Pattern

## Overview
A self-contained Python script that:
1. Reads `VENICE_ADMIN_KEY` from the environment.
2. Fetches balance, analytics (1d/7d/30d/90d), keys, rate limits, rate-limit log, models, and recent usage log.
3. Appends new usage rows to a local JSONL archive.
4. Generates a dark-themed HTML dashboard.
5. Emails HTML + CSV via Gmail SMTP.
6. Supports chunked backfill of older usage log pages.

## Key design decisions

- **Long-term archive:** `~/.venice_usage_reports/usage_archive.jsonl` is the source of truth for data older than ~90 days.
- **Incremental updates:** Each run fetches only the last 1-2 days of `/billing/usage`, deduplicates against the archive, and appends.
- **Safe backfill:** `--backfill` is capped at 500 pages by default. Run repeatedly or raise the cap explicitly if you need more history.
- **Defensive access:** `item.get("inferenceDetails") or {}` everywhere.
- **Read-only:** The script only GETs billing/key/model endpoints.

## Usage examples

```bash
export VENICE_ADMIN_KEY="..."
python3 /home/vivgates/venice_usage_dashboard.py --lookback 2 --email vivek@live.de

# Generate locally without email
python3 /home/vivgates/venice_usage_dashboard.py --no-email --lookback 2

# Backfill older usage rows (limited)
python3 /home/vivgates/venice_usage_dashboard.py --backfill
```

## Cron job example

```bash
1 20 * * * /usr/bin/env bash -lc 'source ~/.venice_usage_reports/.env && python3 /home/vivgates/venice_usage_dashboard.py --lookback 2 --email vivek@live.de'
```

In Hermes, use the `cronjob` tool with enabled_toolsets `["terminal", "file"]` and set `profile` if needed. The cron definition should **not** embed the key directly; load it from the restricted `.env` file.

## Environment / credential setup

1. Create `~/.venice_usage_reports/.env` with permissions `600`:
   ```bash
   printf '%s' 'VENICE_ADMIN_KEY=VENICE_ADMIN_KEY_...' > ~/.venice_usage_reports/.env
   chmod 600 ~/.venice_usage_reports/.env
   ```
2. The dashboard script auto-loads this file at startup.
3. If running manually outside the script, source it first:
   ```bash
   source ~/.venice_usage_reports/.env && python3 /home/vivgates/venice_usage_dashboard.py
   ```

## Already-deployed instance

The user has a running daily cron job:
- **Job ID:** `4a378a1b2ef4`
- **Name:** `venice-usage-daily-dashboard`
- **Schedule:** `1 20 * * *` (8:01 PM ET)
- **Recipient:** `vivek@live.de`
- **Script:** `/home/vivgates/venice_usage_dashboard.py`
- **Reports saved to:** `~/.venice_usage_reports/`
- **Archive:** `~/.venice_usage_reports/usage_archive.jsonl`

## Extending the dashboard

Common additions:
- **Yearly/one-off deep dive from the archive:** Use `scripts/venice_usage_archive_dashboard.py` to generate an interactive Chart.js dashboard directly from `usage_archive.jsonl` without calling the API again. It produces `~/.venice_usage_reports/venice_usage_dashboard.html` with monthly breakdowns, 7-day rolling average, category donut chart, request volume, and top models by category.
- **Agent mapping:** If you maintain a mapping of key description → agent/project, merge it in before grouping.
- **Cost alerting:** Compare 24h spend to a threshold and include a warning banner in the HTML.
- **Per-request latency percentiles:** From `inferenceExecutionTime` in the usage log.

## Files produced

- `~/.venice_usage_reports/venice_dashboard_YYYYMMDD_HHMMSS.html`
- `~/.venice_usage_reports/venice_usage_YYYYMMDD_HHMMSS.csv`
- `~/.venice_usage_reports/usage_archive.jsonl`
- `~/.venice_usage_reports/venice_usage_database.xlsx` — master workbook with `Raw Usage`, `Daily Summary`, `SKU Summary`, and `Monthly Summary` sheets; rebuilt from the full archive after every update so missing days are backfilled.

## Excel database rebuild snippet

After appending new usage rows to the archive, rebuild the workbook:

```python
import json, pandas as pd
from pathlib import Path

archive = Path.home() / ".venice_usage_reports/usage_archive.jsonl"
out = Path.home() / ".venice_usage_reports/venice_usage_database.xlsx"

records = []
with open(archive) as f:
    for line in f:
        rec = json.loads(line)
        inf = rec.get("inferenceDetails") or {}
        records.append({
            "timestamp": rec.get("timestamp"),
            "date": rec.get("timestamp", "")[:10],
            "sku": rec.get("sku"),
            "pricePerUnitUsd": rec.get("pricePerUnitUsd"),
            "units": rec.get("units"),
            "amount": rec.get("amount"),
            "currency": rec.get("currency"),
            "notes": rec.get("notes"),
            "requestId": inf.get("requestId"),
            "inferenceExecutionTimeMs": inf.get("inferenceExecutionTime"),
            "promptTokens": inf.get("promptTokens"),
            "completionTokens": inf.get("completionTokens"),
        })

df = pd.DataFrame(records)
df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True).dt.tz_convert(None)
df["date"] = pd.to_datetime(df["timestamp"]).dt.date
df["month"] = df["timestamp"].dt.to_period("M").astype(str)

daily = df.groupby("date").agg(
    requests=("requestId", "nunique"),
    total_amount_usd=("amount", "sum"),
    total_units=("units", "sum"),
    prompt_tokens=("promptTokens", "sum"),
    completion_tokens=("completionTokens", "sum"),
).reset_index()
daily["total_tokens"] = daily["prompt_tokens"] + daily["completion_tokens"]

sku_summary = df.groupby("sku").agg(
    total_amount_usd=("amount", "sum"),
    total_units=("units", "sum"),
    requests=("requestId", "nunique"),
).reset_index().sort_values("total_amount_usd", ascending=False)

monthly = df.groupby("month").agg(
    requests=("requestId", "nunique"),
    total_amount_usd=("amount", "sum"),
    total_units=("units", "sum"),
).reset_index().sort_values("month")

with pd.ExcelWriter(out, engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name="Raw Usage", index=False)
    daily.to_excel(writer, sheet_name="Daily Summary", index=False)
    sku_summary.to_excel(writer, sheet_name="SKU Summary", index=False)
    monthly.to_excel(writer, sheet_name="Monthly Summary", index=False)
```