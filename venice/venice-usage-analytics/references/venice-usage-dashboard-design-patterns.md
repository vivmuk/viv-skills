# Venice Usage Dashboard Design Patterns

Session-specific recipe: turning the raw `usage_archive.jsonl` into a polished, interactive, executive-grade HTML dashboard and delivering it by email.

## When to use this pattern

- User asks for a "comprehensive" or "executive" usage analysis.
- User explicitly asks for a styled webpage, dashboard, or report.
- The output is too large or too visual for Telegram; email delivery is preferred.
- The user wants a particular design language applied (Swiss typography, grid, colors, fonts).

## Design recipe used in this session

**Style:** Swiss Typography Revival
- Light background (`#F0F0F0`, `#FFFFFF`) with bold accent blocks.
- Colors: `#FF0000`, `#000000`, `#FFFFFF`, `#F0F0F0`, `#0066CC`.
- Typography: Inter/Helvetica Neue for both headlines and body.
- Layout: strict 12-column CSS Grid, 2px grid gutters, asymmetric highlight panels.
- Feel: precise, mathematical, clear.

**Data flow:**
1. Load `~/.venice_usage_reports/usage_archive.jsonl`.
2. Parse timestamps, filter to DIEM rows.
3. Compute summary KPIs, daily series with 7-day moving average, hourly/weekday stacked bars, category splits, LLM token-type split, model efficiency bubbles, cost/latency histograms, monthly progression, and per-request percentile tables.
4. Export all computed data to a single JSON object embedded in the HTML.
5. Render with Chart.js (bar, line, doughnut, bubble, stacked bar, dual-axis combo).
6. Add executive insight cards, model ledger tables, and board-level recommendations.
7. Save HTML locally and email it with `vega_mail.py`.

## Key metrics to surface

- Total DIEM, records, unique requests, days covered.
- 30-day spend vs prior 30 days.
- Average daily burn, peak single day, coefficient of variation.
- Category split: LLM, Image, Video, Tool, Audio, Other.
- LLM token-type split: Input, Cache Read, Output, Cache Write.
- Top models by DIEM, requests, tokens, and DIEM per 1M tokens.
- Hourly and weekly heat/stack patterns (UTC).
- Per-request cost percentiles and latency distribution.
- Monthly progression and trend slope.
- Cost per 1K tokens (blended efficiency metric).

## Model/SKU parsing helpers

```python
def extract_model(sku: str) -> str:
    parts = sku.split("-")
    suffix_markers = ["llm", "input", "output", "cache", "mtoken",
                      "image", "video", "tts", "stt", "embedding", "scribe", "unit"]
    model_parts = []
    for p in parts:
        if p in suffix_markers:
            break
        model_parts.append(p)
    return "-".join(model_parts) if model_parts else sku

def get_category(sku: str) -> str:
    if "image" in sku:
        return "Image"
    elif "video" in sku or "r2v" in sku:
        return "Video"
    elif "tts" in sku or "speech" in sku:
        return "TTS"
    elif "stt" in sku or "scribe" in sku:
        return "STT"
    elif "llm" in sku:
        return "LLM"
    elif "embedding" in sku:
        return "Embedding"
    elif "scrape" in sku or "search" in sku or "augmentation" in sku:
        return "Tool"
    else:
        return "Other"
```

## Deduplication key

Archive rows are appended with `(timestamp, sku, requestId)`. Use the same key when rebuilding from historical data.

## Email delivery

Use the configured helper:

```bash
python3 /home/vivgates/vega_mail.py "Subject" "Body text" /path/to/file.html
```

This is the reliable way to deliver large HTML dashboards.

## Pitfalls

- Do not try to paste large HTML into Telegram; attach via email instead.
- `inferenceDetails` may be `None`; always use `.get("inferenceDetails") or {}`.
- When computing token totals per request, aggregate across all rows sharing the same `requestId` and take `max(promptTokens)` / `max(completionTokens)` because the same request may produce multiple SKU rows.
- For latency, take `max(inferenceExecutionTime)` across rows for the same request.
- Bubble charts with wide efficiency ranges should use a logarithmic x-axis to prevent clustering.
- Keep the JSON data embedded in the HTML; do not rely on a separate `.json` file when emailing.

## Reference output from this session

- File: `/home/vivgates/venice_diem_dashboard_swiss.html`
- Key findings:
  - 3,674.89 DIEM over 267 days.
  - 139,028 unique requests.
  - 65.1% LLM, 24.1% Image, 6.9% Video.
  - Peak day: 67.42 DIEM on 2026-06-27.
  - 30-day trend rising at +1.01 DIEM/day.
  - Top model: zai-org-glm-5-1 (492.33 DIEM).
  - Saturday is the highest-consumption day (812.73 DIEM).
