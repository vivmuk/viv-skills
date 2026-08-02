# Generating a Daily Usage Infographic from the Dashboard CSV

This recipe is for the common follow-up after running the daily Venice usage dashboard: turning the prior-day numbers into a shareable watercolor infographic via Venice `gpt-image-2`.

## Inputs

- The daily CSV produced by `venice_usage_dashboard.py`, e.g. `~/.venice_usage_reports/venice_usage_YYYYMMDD_HHMMSS.csv`.
- The rows cover a 24h window (the dashboard script labels the report for the prior day).

## Aggregate the CSV

```python
import csv
from collections import defaultdict

rows = list(csv.DictReader(open('venice_usage_20260712_002345.csv')))
by_cat = defaultdict(lambda: {'diem': 0.0, 'requests': 0})
by_model = defaultdict(lambda: {'diem': 0.0, 'requests': 0})
total_diem = 0.0
for r in rows:
    amt = abs(float(r['amount'])) if r['currency'] == 'DIEM' else 0.0
    total_diem += amt
    by_cat[r['category']]['diem'] += amt
    by_cat[r['category']]['requests'] += 1
    by_model[r['sku']]['diem'] += amt
    by_model[r['sku']]['requests'] += 1

print(f'Total DIEM: {total_diem:.2f}')
print('By category:')
for cat, v in sorted(by_cat.items(), key=lambda x: x[1]["diem"], reverse=True):
    print(f'  {cat}: {v["diem"]:.2f} DIEM, {v["requests"]} requests')
print('Top models:')
for sku, v in sorted(by_model.items(), key=lambda x: x[1]["diem"], reverse=True)[:5]:
    print(f'  {sku}: {v["diem"]:.2f} DIEM, {v["requests"]} requests')
```

## Generate the infographic

Call `gpt-image-2` through `POST /api/v1/image/generate`.

Request:
```json
POST /api/v1/image/generate
{
  "model": "gpt-image-2",
  "prompt": "Whimsical watercolor-style infographic dashboard titled 'Venice Usage — July 11, 2026'. ... (keep under 1500 chars)",
  "aspect_ratio": "16:9",
  "resolution": "2K",
  "hide_watermark": true
}
```

Key parameters:
- `resolution` must be `"1K"`, `"2K"`, or `"4K"`. Pixel strings like `"1440x2560"` return `400`.
- `prompt` must be under ~1500 characters. Keep the data dense: comma-separated numbers and labels.
- Response field: `data["images"][0]` is a **base64 string**, not an object with `url` or `image`.

Decode and save:
```python
import base64, requests, yaml
from pathlib import Path

with open(Path.home() / '.hermes/config.yaml') as f:
    key = yaml.safe_load(f)['model']['api_key']

payload = {
    'model': 'gpt-image-2',
    'prompt': '...',  # under 1500 chars
    'aspect_ratio': '16:9',
    'resolution': '2K',
    'hide_watermark': True,
}

r = requests.post(
    'https://api.venice.ai/api/v1/image/generate',
    headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
    json=payload,
    timeout=300,
)
r.raise_for_status()
data = r.json()
img_bytes = base64.b64decode(data['images'][0])
out = Path.home() / '.venice_usage_reports/daily_diem_infographic_20260711.png'
out.write_bytes(img_bytes)
print(f'Saved {out} ({len(img_bytes)} bytes)')
```

## Delivery

Send the PNG in chat with:
```
MEDIA:/home/vivgates/.venice_usage_reports/daily_diem_infographic_20260711.png
```

## Known error: `Resolution '...' is not supported`

If you see:
```json
{"error":"Resolution '1440x2560' is not supported by model 'gpt-image-2'. Supported options: 1K, 2K, 4K"}
```
replace the pixel resolution with `"2K"` (or `"1K"`/`"4K"`).

## Known error: `string indices must be integers`

If you try `data['images'][0]['url']`, you will hit this. Use `data['images'][0]` as the base64 string and decode it.

## Template prompt

```text
Whimsical watercolor infographic titled "Venice Usage — {date}". Top cards: Total DIEM {diem}, Total USD {usd}, {requests} requests, Top model {top_model}. Pie chart: {cat_pct}. Bottom bar chart of top 5 models: {model_list}. Soft brushstrokes, hand-painted chart elements, pastel palette, white textured paper.
```

Substitute the placeholders with the aggregated CSV values before sending.