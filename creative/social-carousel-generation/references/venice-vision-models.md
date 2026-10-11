# Venice Vision Models — Slide QA Reference

(Updated 2026-06-24, confirmed on Doximity Ask carousel run.)

## TL;DR

The active chat model (`minimax-m3` / `google-gemma-4-31b-it` / `grok-4-3`)
**cannot see images**. `vision_analyze` returns HTTP 400 "Image content is not
supported by this model". For slide QA after image gen, call a vision-capable
Venice model directly via the chat completions API with the image passed as
base64.

**Working model (confirmed 2026-06-24):** `qwen3-vl-235b-a22b`

```python
import urllib.request, json, base64

def vision_qa(image_path: str, question: str, model: str = 'qwen3-vl-235b-a22b',
              key: str = '<VENICE_KEY>', max_tokens: int = 500) -> str:
    with open(image_path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode()
    body = {
        'model': model,
        'messages': [{
            'role': 'user',
            'content': [
                {'type': 'text', 'text': question},
                {'type': 'image_url',
                 'image_url': {'url': f'data:image/png;base64,{b64}'}}
            ]
        }],
        'max_tokens': max_tokens,
    }
    req = urllib.request.Request(
        'https://api.venice.ai/api/v1/chat/completions',
        data=json.dumps(body).encode(),
        headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())['choices'][0]['message']['content']
```

## Models probed on 2026-06-24

| Model | Status |
|---|---|
| `qwen3-vl-235b-a22b` | ✅ works — vision-capable, returns clean verdict |
| `e2ee-qwen3-vl-30b-a3b-p` | ⚠ listed but privacy-gated; same family |
| `qwen-2.5-vl-72b` | ❌ 404 not found |
| `qwen-2.5-vl-3b` | not probed |
| `minimax-m3` (chat) | ❌ 400 — no vision in chat path |

The model list endpoint `GET /api/v1/models` returns vision-capable IDs
filtered on `m.get('capabilities', {}).get('vision')` or substring match on
`'vl'` / `'vision'` in the ID.

## Recommended QA prompts per slide type

### Universal slide QA (~80 words, fast)

```
Slide QA. Answer in <120 words:
(1) Title legible & correct (no "1." prefix)?
(2) All bullets/diagram visible?
(3) Footer ONLY "AIPharmaXchange" (bottom-left) + "swipe ->" (bottom-right) — NO URL/DOI/extra text?
(4) Any hallucinated journal logos, DOIs, URLs, or gibberish text?
(5) Palette teal/navy/cream (no pink/red wash)?
(6) Publishable as LinkedIn slide? Score 1-10.
```

### Chart slide (slide 3)

```
Slide QA. Answer in <120 words:
(1) Title legible?
(2) Clear bar/line chart with these numbers visible as labels: <paste expected numbers>?
(3) Footer ONLY "AIPharmaXchange" + "swipe ->"?
(4) Any hallucinated numbers, logos, DOIs?
(5) Palette teal/navy/cream?
(6) Publishable? Score 1-10.
```

### URL-leak audit (slide 7 implications)

```
Look at the slide carefully. List every URL/website/DOI text you see verbatim.
Note position (top/middle/bottom, left/center/right).
State whether each is the real source URL or a hallucinated/fake one.
```

This one is critical for slide 7 because the model often adds the correct
URL in a body CTA box (desired) but can also add hallucinated ones in the
footer (Pitfall #18 violation). Position matters.

### Limitations 2×2 grid (slide 6)

```
Slide QA. Answer in <100 words:
(1) Is it a 2x2 grid of 4 cards (limitations)?
(2) All 4 cards visible with headers and body text?
(3) Footer ONLY "AIPharmaXchange" + "swipe ->"?
(4) Any hallucinated text inside cards?
(5) Palette teal/navy/cream?
(6) Publishable? Score 1-10.
```

## Cost & speed

- `qwen3-vl-235b-a22b`: ~3-7s per slide, ~$0.01-0.02 per call (estimate).
  For an 8-slide carousel, full QA round = ~40-60s, ~$0.10-0.15.
- Worth doing — caught the slide 1 gibberish ("umshkcipimt") and the
  slide 7 URL bleed in the Doximity Ask run. Both regenerated and
  re-shipped successfully.

## When NOT to use vision QA

- Pre-flight for trivial slides (slide 8 Follow CTA, slide 2 method if
  very simple)
- During fast iteration loops (test 1 image, QA 1 image — don't
  batch-QA 8 failed renders, fix the prompt first)

When to ALWAYS use vision QA:

- Before shipping a final carousel (one pass over all 8 slides)
- When the accuracy reviewer scores < 5/10 on any slide
- After any regen (verify the new render fixed the issue and didn't
  introduce a new one)

## What reviewers do that vision QA does not (and vice versa)

| Check | Text reviewer | Vision QA |
|---|---|---|
| "Is 150 the correct number for health systems?" | ✅ | ✅ (sees label) |
| "Are all 4 cards visible?" | ❌ can only check spec | ✅ |
| "Is the footer clean?" | ❌ can only check spec | ✅ |
| "Is the title spelled correctly?" | partial (only sees spec) | ✅ |
| "Did the model fabricate an extra number?" | ✅ (cross-ref paper) | partial (sees label, can't verify) |
| "Does the layout drift?" | ❌ | ✅ |

Run **both**. The reviewer catches fabricated claims; vision QA catches
layout drift and hallucinated footer text. Together they're the safety net
behind the single-model image gen.
