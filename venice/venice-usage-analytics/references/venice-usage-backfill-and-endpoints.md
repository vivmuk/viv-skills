# Venice Usage Endpoints & Backfill Notes

Session-level reference for building Venice usage dashboards and archives.

## Endpoints that work (admin key, read-only)

- `GET /v1/billing/balance` — DIEM/USD balance, epoch info, `canConsume`.
- `GET /v1/billing/usage-analytics?lookback=N` — daily/model/key aggregations. Retention ~90 days. `lookback` accepts `1d`, `7d`, `30d`, `90d`.
- `GET /v1/billing/usage` — paginated line-item log. Timestamp, SKU, currency, amount, units, `requestId`, prompt/completion tokens, `inferenceExecutionTime`, API key id/description.
- `GET /v1/api_keys` — all keys with descriptions, limits, `lastUsedAt`, trailing/current DIEM usage.
- `GET /v1/api_keys/rate_limits` — model-level RPM/TPM limits.
- `GET /v1/api_keys/rate_limits/log` — last 50 rate-limit violations.
- `GET /v1/models` — model catalog for display-name enrichment.

## Endpoints that do NOT work

- `GET /v1/openapi.json` → 404.
- `GET /v1/api-keys` (hyphenated) → 404; use `/api_keys` (underscore).
- `GET /v1/usage` → 404; use `/billing/usage`.
- `/v1/admin/*` → 404. There is no separate admin path; admin scope is handled by key permissions on the standard endpoints above.

## Pagination

- `/billing/usage` supports `?limit=200` (maximum observed).
- One account snapshot: 355,934 rows / 1,781 pages at 200 rows/page.
- Oldest row observed: `2025-02-28T22:41:53.952Z`.
- Total count available in headers; compute pages before launching chunked backfills.

## Backfill strategy

1. Determine total pages from `/billing/usage` with `limit=200`.
2. Fetch in chunks (e.g. 500 pages each) via parallel background processes to finish in reasonable time.
3. Append to `~/.venice_usage_reports/usage_archive.jsonl`.
4. Dedupe by `(timestamp, sku, requestId)` so chunks can overlap/resume safely.
5. Keep a gzip copy: `usage_archive.jsonl.gz` (117 MB → ~8.6 MB).
6. Daily incremental runs only fetch the last 1-2 days and append them.

## Live implementation

`/home/vivgates/venice_usage_dashboard.py` fetches balance, analytics, usage log, keys, rate limits, and models; writes HTML + CSV; emails them; and supports `--backfill` / `--backfill-start-page` / `--backfill-max-pages`.

Daily cron job: `venice-usage-daily-dashboard` (ID `4a378a1b2ef4`) at 8:01 PM ET, emailed to `vivek@live.de`.
