# Venice Usage Endpoints — Reference Notes

## Base URL
`https://api.venice.ai/api/v1`

## Authentication
`Authorization: Bearer <VENICE_ADMIN_KEY>`

## Read-only endpoints useful for usage dashboards

### `GET /billing/balance`
Returns:
- `canConsume`: bool
- `consumptionCurrency`: usually "DIEM"
- `balances.diem`, `balances.usd`
- `diemEpochAllocation`: total DIEM allocated this epoch

Derived metric: `(diemEpochAllocation - balances.diem) / diemEpochAllocation` = epoch usage %.

### `GET /billing/usage-analytics`
Query params:
- `lookback`: one of `1d`, `7d`, `30d`, `90d` (and possibly longer, but server retains ~90 days)

Response fields:
- `byDate`: list of `{date, USD, DIEM}`
- `byModel`: list of `{modelName, unitType, modelType, totalUsd, totalDiem, totalUnits, breakdown[]}`
  - `breakdown` items: `{type, usd, diem, units}` where type is Input/Output/Cache Read/Cache Write
- `byModelDaily`: per-day per-model DIEM map
- `byModelDailyUsd`: per-day per-model USD map
- `byKey`: list of `{apiKeyId, description, totalUsd, totalDiem, totalUnits}`
- `byKeyDailyDiem`: per-day per-key DIEM map
- `byKeyDailyUsd`: per-day per-key USD map
- `topModels`: ordered model display names
- `topKeyNames`: ordered key descriptions

### `GET /billing/usage`
Paginated line-item log.
Query params:
- `limit` (max seems to be 200)
- `page`

Response has `data[]` and `pagination.totalPages`.

Each item:
- `timestamp`: ISO UTC
- `sku`: pricing SKU string, e.g. `zai-org-glm-5-2-llm-input-mtoken`
- `pricePerUnitUsd`
- `units`
- `amount`: negative for consumption
- `currency`: "DIEM" or "USD"
- `notes`: e.g. "API Inference"
- `inferenceDetails`: may be `null`. When present:
  - `requestId`
  - `promptTokens`
  - `completionTokens`
  - `inferenceExecutionTime` (ms)

### `GET /api_keys`
Returns `data[]` of keys.
Key fields:
- `id`, `description`, `apiKeyType` (ADMIN/INFERENCE)
- `consumptionLimits`: `{diem, usd, vcu}`
- `limitPeriod`: "EPOCH" or "MONTH"
- `createdAt`, `expiresAt`, `lastUsedAt`
- `usage.trailingSevenDays`: `{diem, usd, vcu}`
- `usage.currentPeriodUsage`: `{diem, usd, vcu}`

### `GET /api_keys/rate_limits`
Returns per-model RPM/TPM limits visible to the authenticated key.

### `GET /api_keys/rate_limits/log`
Returns up to 50 recent rate-limit events:
- `apiKeyId`, `modelId`, `rateLimitTier`, `rateLimitType` (RPM/TPM), `timestamp`

### `GET /models`
Model catalog. Use `?type=tts|image|video|audio|embedding` for subsets.

## SKU parsing heuristics
SKUs generally follow the pattern `<model-id>-<service>-<variant>-mtoken`.

Service/category markers:
- `llm` → LLM
- `image` or `unit` → IMAGE
- `video` or `r2v` → VIDEO
- `tts` or `speech` → TTS
- `stt`, `scribe`, `whisper` → STT
- `embedding` → EMBEDDING
- `scrape`, `search` → TOOL

Token variant markers:
- `input` → Input
- `output` → Output
- `cache-input` → Cache Read
- `cache-write` → Cache Write
