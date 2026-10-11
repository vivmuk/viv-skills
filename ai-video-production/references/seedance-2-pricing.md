---
title: Seedance 2.0 + Grok Imagine Private Pricing (live 2026-07)
parent: ai-video-production
audience: agents quoting video generation costs
---

# Pricing matrix (snapshot 2026-07-02)

Live data from `POST https://api.venice.ai/api/v1/video/quote` with the AIPharmaXchange key. **Re-quote before every batch — never cache.**

## Seedance 2.0 — Text-to-video (T2V)

| Duration | 480p | 720p | 1080p |
|---|---|---|---|
| 5s  | $0.44 | $0.95 | $2.34 |
| 10s | $0.88 | $1.89 | $4.68 |
| 15s | $1.32 | $2.84 | $7.02 |

## Seedance 2.0 — Image-to-video (I2V)

Same as T2V. (I2V does not accept `aspect_ratio` — it derives from input image dimensions.)

## Seedance 2.0 — Reference-to-video (R2V, +22% over T2V)

| Duration | 480p | 720p | 1080p |
|---|---|---|---|
| 5s  | $0.54 | $1.16 | $2.86 |
| 10s | $0.97 | $2.09 | $5.14 |
| 15s | $1.46 | $3.13 | $7.71 |

R2V adds the cost of donor processing but unlocks the four workflows:

| Workflow | Canonical prompt | Inputs |
|---|---|---|
| Reference | `Refer to <Subject N> in <Image N> to generate …` | text + ≥1 image OR video (0–9 images, 0–3 videos), optionally up to 3 audio donors |
| Edit | `Strictly edit <Video 1>, changing its …` | 1 input video + text |
| Extend | `Extend <Video 1>, generate …` | 1 input video + text |
| Stitch | `<Video 1> + <transition> + followed by <Video 2> + …` | 2-3 input videos + text; total combined duration ≤ 15s |

## Grok Imagine Private

| Duration | USD |
|---|---|
| 5s  | $0.44 |
| 10s | $0.89 |
| 15s | $1.33 |

No resolution kwarg. All four variants (T2V / I2V / R2V / V2V) exist. Returns a `download_url` (24h expiry, single-purpose; persist at queue time, `GET` from one network, save locally, then `DELETE` if you want it invalidated).

## Topaz video upscale

Requires `video_url` in body, then re-quote. Common pattern: 2× upscale of a generated clip before delivery. Pricing is per-second-of-output-duration and varies by multiplier; always quote.

## Live quote procedure (Python)

```python
import json, urllib.request

KEY = open(os.path.expanduser("~/.hermes/config.yaml")).read()
import re
m = re.search(r"api_key:\s*(\S+)", KEY)
key = m.group(1)

hdr = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

def quote(payload):
    req = urllib.request.Request(
        "https://api.venice.ai/api/v1/video/quote",
        data=json.dumps(payload).encode(), headers=hdr, method="POST")
    return urllib.request.urlopen(req, timeout=30).read().decode()

# 5s T2V 720p 9:16 batch estimate
for n in range(9):
    print(n, quote({"model": "seedance-2-0-text-to-video",
                     "duration": "5s", "resolution": "720p",
                     "aspect_ratio": "9:16"}))
```

## Cost estimate per 90-second paper reel

| Component | Qty | Unit (720p) | Subtotal |
|---|---|---|---|
| Seedance R2V B-roll clips | 9 | $1.16 | $10.44 |
| Face anchor R2V (5–15s) | 1 | $1.16 | $1.16 |
| R2V Stitch transition (3s) | 1 | $0.95 | $0.95 |
| Voice clone TTS (~110s, tts-chatterbox-hd) | 1 reel | ~$0.30 | $0.30 |
| Music bed (minimax-music-v2, 90s) | 1 | ~$0.50 | $0.50 |
| SFX × 4 transitions (elevenlabs-sound-effects-v2) | 4 | ~$0.20 | $0.80 |
| Topaz 2× upscale (optional) | 1 | ~$0.40 | $0.40 |
| LLM calls (analyze + storyboard + EDL, deepseek-v4-pro) | 3 | ~$0.05 | $0.15 |
| **Path A (recorded VO), 720p total** | | | **~$13.00** |
| **Path B (cloned VO), 720p total** | | | **~$13.30** |

Plus `$0.01` per paper for the Venice `/augment/text-parser` ingestion pass.

Cost levers (priority order):
1. Drop clip count from 9 → 6 (~30% cheaper) before downgrading resolution.
2. Stay at 720p for IG-native sizes; 1080p only when platform demands.
3. Reuse one music bed across an entire series — first creation only.
4. Reuse one cloned-voice handle (free; expires after 7 days, re-upload).
5. Use `seedance-2-0-fast-*` for previews/drafts, full-quality for final render.

Combined, levers 1+3+4+5 drop a reel to **<$7** while keeping 720p quality.
