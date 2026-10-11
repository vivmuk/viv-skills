# Venice API rate limits — live snapshot

**Endpoint:** `GET https://api.venice.ai/api/v1/api_keys/rate_limits`
**Auth:** `Authorization: Bearer $VENICE_API_KEY`

## Current snapshot

| Field | Value | Last fetched |
|---|---|---|
| `requestsPerMinute` (RPM) | TBD | pending user paste (2026-06-28) |
| `tokensPerMinute` (TPM) | TBD | pending user paste |
| `requestsPerDay` (RPD) | TBD | pending user paste |
| `tokensPerDay` (TPD) | TBD | pending user paste |
| `imageGenerationsPerDay` | TBD | pending user paste |
| `audioGenerationsPerDay` | TBD | pending user paste |
| `dailySpend` cap (USD) | `$10.00` (AIPharmaXchange ledger, pre-existing) | 2026-06-19 |

> Snapshot is intentionally empty until the user pastes a fresh `/rate_limits`
> response. Update the table above the moment values land.

## How to refetch

```bash
# Preferred: env var is set
curl -s https://api.venice.ai/api/v1/api_keys/rate_limits \
  -H "Authorization: Bearer $VENICE_API_KEY" | python3 -m json.tool

# Fallback: read from Hermes config
KEY="$(awk '/^- name: venice/{f=1} f && /api_key:/{print $2; exit}' ~/.hermes/config.yaml)"
curl -s https://api.venice.ai/api/v1/api_keys/rate_limits \
  -H "Authorization: Bearer *** | python3 -m json.tool
```

If `awk` returns empty, the key in config is blank — check
`~/.hermes/config.yaml` line ~637 for `custom_providers` block.

## Throttle policy (default, used when snapshot is fresh)

- **Chat (interactive):** no guard. Single calls under RPM.
- **Batch text (e.g. carousel trio-review × 7 = 21 calls):** pace ≤80% of
  measured RPM; cap by `min(remaining_RPM, batch_size)`; on HTTP 429,
  backoff with `Retry-After`.
- **Image burst (carousel 7 slides):** sequential, 1s jitter; abort at ≤5%
  of `imageGenerationsPerDay`.
- **Long agent loops:** re-poll every 5 min, log delta. If any pool drops
  below 10% remaining, downgrade tier (e.g. swap `grok-4-3` → `deepseek-v4-flash`)
  or pause and wait for the next reset window.

## Cross-references

- Tier table (speed/price) — see `model-routing/SKILL.md` top of file.
- Carousel-specific model choices — same file, "Carousel pipeline" section.
- Daily $ ledger path — `/tmp/aipharmaxchange_spend/spend_{date}.json`.
- This snapshot is **not** cached across sessions; always refetch on job
  start. The `/rate_limits` endpoint is cheap (single GET, returns <2KB).
