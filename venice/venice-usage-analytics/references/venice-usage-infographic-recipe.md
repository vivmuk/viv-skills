# Venice Usage Infographic Prompt Recipe

A known-good pattern for generating a dense, data-rich infographic from Venice usage data using `gpt-image-2`.

## Endpoint

```python
POST https://api.venice.ai/api/v1/images/generations
Authorization: Bearer VENICE_INFERENCE_KEY_...
Content-Type: application/json

{
  "model": "gpt-image-2",
  "prompt": "<compressed prompt under 1500 chars>",
  "response_format": "b64_json"
}
```

## Hard constraints

- **Prompt length:** maximum 1500 characters. Failure is immediate `400` with `"String must contain at most 1500 character(s)"`.
- **Wrong endpoint:** `POST /image/generate` returns `400 Unrecognized key(s) in object: 'size'`. Use `/images/generations`.
- **Response path:** `result["data"][0]["b64_json"]`, not `result["images"]`.

## Prompt structure that works

Keep it dense and comma-separated. Avoid long prose. Group related numbers together.

Template:

```text
Swiss International Style infographic, landscape 16:9. Title "DIEM USAGE INTELLIGENCE 2025-2026". White background, gray grid, red/black/blue accents. Helvetica headlines, Inter body.
Data: TOTAL {total_diem} DIEM, {records} records, {requests} requests, {days} days.
2026: {diem_2026} DIEM, {requests_2026} requests, {input_tokens} input, {output_tokens} output, {ratio}:1 ratio.
2025: {diem_2025} DIEM, 2026 is {mult}x larger.
DAILY: avg {avg_daily}, peak {peak_daily} on {peak_date}, {cost_per_1k} per 1K tokens, +{trend} trend.
MONTHLY 2026 BARS: Jan {jan}, Feb {feb}, ...
CATEGORY PIE: LLM {llm}%, Image {image}%, Video {video}%, ...
LLM TOKEN SPLIT: Input {input}%, Cache Read {cache_read}%, Output {output}%, Cache Write {cache_write}%.
TOP 10 MODELS DIEM: {model1} {amt1}, {model2} {amt2}, ...
TEMPORAL: peak hour {hour} {hour_amt}, peak day {day} {day_amt}, peak week {week} {week_amt}.
REQUEST ECONOMICS: mean {mean}, median {median}, P99 {p99}, avg latency {latency}s.
Footer: "Generated {date} · Venice Usage Archive". Ultra-detailed consulting report, mathematical precision, asymmetric grid.
```

## Verification steps

1. Compute prompt length with `len(prompt)` before sending.
2. If over 1500, collapse categories, remove adjectives, or merge low-percentage categories into "Other".
3. Send via `/images/generations` with `response_format: "b64_json"`.
4. Decode `data[0].b64_json` and save as PNG.
5. Email the PNG via `~/vega_mail.py` or send via Telegram.

## Example values (mid-2026 snapshot)

- Total DIEM: 3,674.89
- Records: 344,472
- Requests: 139,028
- Days: 267
- 2026 DIEM: 3,388.05
- 2026 requests: 129,871
- 2026 input tokens: 4.45B
- 2026 output tokens: 60.43M
- Input/output ratio: 73.6:1
- 2025 DIEM: 286.84
- 2026 vs 2025: 11.8x
- Avg daily: 13.76
- Peak daily: 67.42 on 2026-06-27
- Cost per 1K tokens: 0.00080
- 30-day trend: +1.01/day
- Monthly 2026: Jan 182.97, Feb 517.89, Mar 504.52, Apr 652.23, May 784.91, Jun 745.53
- Categories: LLM 66.5%, Image 22.3%, Video 7.2%, Tool 2.8%, Other 1.0%, TTS 0.1%, STT 0.0%
- LLM token split: Input 55.1%, Cache Read 27.6%, Output 11.5%, Cache Write 5.8%
- Top models: zai-org-glm-5-1 492.36, nano-banana-pro 237.59, claude-opus-4-6 224.88, zai-org-glm-5-2 161.90, openai-gpt-54 142.96, gemini-3-1-pro-preview 134.01, openai-gpt-52-codex 122.31, claude-sonnet-4-6 117.50, kimi-k2-5 113.10, grok-41-fast 67.17
- Peak hour: 01:00 UTC 399.31
- Peak day: Saturday 812.73
- Peak week: 2026-W19 260.33
- Request economics: mean 0.0264, median 0.0074, P99 0.280, avg latency 12.2s
