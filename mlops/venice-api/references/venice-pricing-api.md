# Venice API — Model Pricing Extraction

Verified 2026-06-14 against `https://api.venice.ai/api/v1`. Use this whenever
a pipeline needs real per-call cost (Paperclip finance events, budget tracking,
cost-aware routing, ROI dashboards). Don't hardcode prices — the catalog
moves.

## Two endpoints, one shape

```
GET /api/v1/models?type=text       → ~94 models (list)
GET /api/v1/models?type=image      → ~30 models
GET /api/v1/models?type=video      → models
GET /api/v1/models?type=audio      → models
GET /api/v1/models?type=music      → models
```

Auth: same `Authorization: Bearer <VENICE_API_KEY>` as the chat endpoint.
The endpoint is **not in the MCP tool list** — call it directly with
urllib/curl/httpx.

## Response shape

Each entry has:
```json
{
  "id": "model-id",
  "type": "text" | "image" | "video" | "audio" | "music",
  "context_length": <int>,
  "created": <unix>,
  "model_spec": {
    "pricing": { ... },          // varies by type, see below
    "constraints": { ... },      // model-specific limits (e.g. steps, divisor)
    "name": "Display Name",
    "modelSource": "https://...", // upstream HuggingFace / vendor page
    "offline": false,
    "privacy": "private"
  }
}
```

## Pricing shapes by type

**Text models — per 1M tokens, input + output:**
```json
"pricing": {
  "input":        { "usd": 0.625,  "diem": 0.625  },
  "output":       { "usd": 3.125,  "diem": 3.125  },
  "cache_input":  { "usd": 0.1875, "diem": 0.1875 },  // optional
  "cache_write":  { "usd": 3.35,   "diem": 3.35   },  // optional
  "extended":     { "usd": null,   "diem": null   }   // null for "not priced"
}
```

**Image models — per image at default resolution:**
```json
"pricing": {
  "generation":  { "usd": 0.09, "diem": 0.09 },
  "upscale":     { "2x": { "usd": 0.02 }, "4x": { "usd": 0.08 } }  // optional, structured
}
// OR resolution-tiered:
"pricing": {
  "resolutions": { ... },  // 1024x1024, 2048x2048, etc., each with usd
  "quality":     { ... },  // standard, hd, etc.
  "upscale":     { ... }
}
```

**Video / music — per second of generated media.** Use the `venice_video_quote`
and `venice_audio_quote` MCP tools for live quotes rather than scraping the
catalog; video and music prices change with model + duration.

**Web augment — flat per call (NOT in /v1/models response; hardcode from observed billing):**
- `POST /v1/augment/search` — $0.01/call
- `POST /v1/augment/scrape` — $0.02/call
- `POST /v1/augment/text-parser` — similar ballpark

If you need audited prices, log the response `timing` and cross-reference
the user-visible DIEM deduction from the web console. Augment calls are
frequent, so a $0.01–$0.02 misestimate adds up over a daily pipeline.

## Worked extraction (Python, stdlib only)

```python
import json, urllib.request, os
VENICE = "https://api.venice.ai/api/v1"
KEY = os.environ["VENICE_API_KEY"]

def fetch_models(kind: str) -> list[dict]:
    req = urllib.request.Request(
        f"{VENICE}/models?type={kind}",
        headers={"Authorization": f"Bearer {KEY}"},
    )
    return json.loads(urllib.request.urlopen(req, timeout=15).read())

def text_price_per_million(model_entry: dict) -> tuple[float, float] | None:
    """Return (input_per_million, output_per_million) in USD. None if unpriced."""
    p = (model_entry.get("model_spec") or {}).get("pricing") or {}
    if not isinstance(p, dict):
        return None
    inp = p.get("input", {}).get("usd") if isinstance(p.get("input"), dict) else None
    out = p.get("output", {}).get("usd") if isinstance(p.get("output"), dict) else None
    if inp is None or out is None:
        return None
    return float(inp), float(out)

def image_price_per_image(model_entry: dict) -> float | None:
    """Return USD per single image at default resolution. None if unpriced."""
    p = (model_entry.get("model_spec") or {}).get("pricing") or {}
    if not isinstance(p, dict):
        return None
    g = p.get("generation")
    if isinstance(g, dict) and g.get("usd") is not None:
        return float(g["usd"])
    # Resolution-tiered: take the lowest resolution as the default
    r = p.get("resolutions")
    if isinstance(r, dict) and r:
        first = next(iter(r.values()))
        if isinstance(first, dict) and first.get("usd") is not None:
            return float(first["usd"])
    return None
```

## Cost math (per call)

```python
def cost_text_call(model_entry, prompt_tokens, completion_tokens) -> float:
    p = text_price_per_million(model_entry)
    if p is None:
        return 0.0
    in_per_m, out_per_m = p
    return (prompt_tokens * in_per_m + completion_tokens * out_per_m) / 1_000_000

def cost_image_call(model_entry, n: int = 1) -> float:
    p = image_price_per_image(model_entry)
    if p is None:
        return 0.0
    return p * n
```

## Known model prices (snapshot 2026-06-14, USD)

Use as a fallback if `/v1/models` is unreachable. Refresh on the cron.

**Text (input / output per 1M tokens):**
| Model | in/out | Cache in |
|---|---|---|
| `nvidia-nemotron-3-ultra-550b-a55b` | 0.625 / 3.125 | 0.1875 |
| `openai-gpt-55-pro` | 37.5 / 225 | — |
| `deepseek-v4-pro` | 1.73 / 3.796 | 0.33 |
| `deepseek-v4-flash` | 0.17 / 0.35 | 0.028 |
| `qwen-3-7-max` | 2.7 / 8.05 | 0.27 |
| `google-gemma-4-31b-it` | 0.12 / 0.36 | 0.09 |
| `gemma-4-uncensored` | 0.1625 / 0.5 | — |
| `venice-uncensored-1-2` | 0.2 / 0.9 | — |
| `zai-org-glm-5-1` | 1.75 / 5.5 | 0.325 |
| `claude-opus-4-8` | 6.0 / 30.0 | 0.6 |
| `grok-4-20` | 1.42 / 2.83 | 0.23 |
| `kimi-k2-6` | 0.85 / 4.655 | 0.22 |

**Image (per image, default resolution):**
| Model | USD | Notes |
|---|---|---|
| `flux-2-max` | 0.09 | best overall, ~20–50s |
| `flux-2-pro` | 0.04 | MCP default, good balance |
| `grok-imagine-image-quality` | 0.05 | best text rendering for some prompts, unique `images[]` b64 response |
| `gpt-image-2` | 0.25 | best text rendering overall, ~150–300s, no width/height/steps |
| `nano-banana-2` | 0.01 | fast/cheap, avatars |
| `nano-banana-pro` | 0.04 | rejects b64_json |
| `recraft-v4-pro` | 0.29 | pro illustration |
| `qwen-image-2-pro` | 0.10 | good alternative |
| `venice-sd35` | 0.01 | baseline |

## Pitfalls

- **Field name varies**: `input`/`output` for text, `generation` for image,
  `resolutions` for some image models. Always defensive-check: `isinstance(value, dict)` and `value.get("usd") is not None` before doing math. Empty `{}` or `null` means "not priced for this tier" — treat as zero, not as an error.
- **`diem` is the on-platform currency; `usd` is the dollar equivalent.** In all observed entries they're 1:1, but verify before assuming. If `usd` is missing, fall back to `diem` (same number).
- **Cache pricing is per-million-cached, not a multiplier.** `cache_input` is a separate tier, not a discount on `input` — though in practice cache reads are cheaper than fresh reads.
- **The `/v1/models?type=text` endpoint returns 94 models including duplicates and aliases.** Filter by `context_length > 0` and dedupe by `id` if you cache the result.
- **Token counts come from `response.usage.{prompt,completion}_tokens` in the chat completion response.** These are reliable for Venice chat. For image generation, no token counts — cost is purely per-image.
- **Don't try to estimate video/music costs from `/v1/models`** — they vary by duration, resolution, and quality tier. Use the `venice_video_quote` and `venice_audio_quote` MCP tools (auth-free) for live quotes.
- **The Augment endpoints are NOT in `/v1/models`.** Prices above (search $0.01, scrape $0.02) are estimated from observed DIEM deductions; if precision matters, log the response `timing` and check the DIEM delta.

## Pattern: Paperclip finance events from per-call cost

For the AIPharmaXchange pipeline (or any agent that calls Venice and needs
Paperclip to track cost), see the `paperclip` skill's
`references/finance-events.md` + the wired `venice-adapter.py` for a
working example. The summary: `cost_usd = cost_text_call(entry, in, out)`,
then `record_finance_event(model, cost_usd, ...)`. Amount is in cents,
so `int(round(usd * 100))` — sub-cent rounds to 1.
