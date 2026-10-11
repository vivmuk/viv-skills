# Venice augment/search 401 — diagnostic recipe

Symptom: `daily_post_generator.py` aborts at step 2/7 with
`PIPELINE FAILED: news_harvester returned no items`, and the stderr
shows `[news_harvester] search HTTP 401 for '<query>': {"error":"Authentication failed"}`
on every one of the 3 default topics. The pipeline burns ~$0.03 of
`sources_cost` (3 search calls × $0.01) before the abort and never
progresses to content generation.

Before declaring the key "dead" and rotating it, distinguish the
THREE failure shapes — only one of them requires a key rotation.

## Step 1 — Persistent vs transient (the cheap test)

Every harvest attempt writes `/tmp/daily_news_<YYYY-MM-DD>.json` with
the full result, including a 0-item payload. An empty `items=[...]`
file at ~65 bytes is the "no items harvested" fingerprint:

```bash
for f in $(ls -t /tmp/daily_news_*.json | head -10); do
  date=$(basename "$f" .json | sed 's/daily_news_//')
  size=$(wc -c < "$f")
  items=$(python3 -c "import json; d=json.load(open('$f')); print(len(d.get('items', [])))")
  echo "$date: $size bytes, $items items"
done
```

Reading:
- **3+ consecutive days with `0 items`** → persistent outage,
  do NOT retry the pipeline today.
- **Today is `0 items`, yesterday had N≥1** → likely transient;
  one retry after a few minutes is reasonable.
- **Most days have items, today is empty** → transient or rate-limit.

## Step 2 — Direct probe (confirm it's auth, not network)

Reproduce the failing call with the same key, outside the pipeline:

```bash
set -a; . /Users/vivgatesai/.paperclip/instances/default/.env; set +a
python3 -c "
import os, json, urllib.request, urllib.error
key = os.environ['VENICE_API_KEY']
req = urllib.request.Request(
    'https://api.venice.ai/api/v1/augment/search',
    data=json.dumps({'query': 'probe check', 'limit': 1}).encode(),
    headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
)
try:
    with urllib.request.urlopen(req, timeout=20) as r:
        print('OK', r.read()[:200])
except urllib.error.HTTPError as e:
    print('HTTP', e.code, '-', e.read().decode('utf-8', 'ignore')[:200])
"
```

Shape decoder:
- `HTTP 401 - {"error":"Authentication failed"}` → auth/key problem.
  Before treating as a key rotation, also check whether `/v1/models`
  returns 200 with the same key — if it does, the key authenticates
  the admin surface but lacks inference scope. See Step 2.5 for the
  full discriminator. (Also: if the 401 was preceded by a malformed,
  placeholder, or identical-value key — see Pitfall #1 in SKILL.md.)
- `HTTP 429 - {"error":"Rate limit exceeded"}` → billing/rate-limit,
  distinct fix path (raise DIEM cap or wait).
- `HTTP 402 - {"error":"DIEM spend limit exceeded..."}` → per-key
  DIEM cap, fix path is operator action on the API key.
- `HTTP 402 - {"x402Version": 2, ...}` → Venice has moved this
  endpoint behind the **x402 paid-protocol** — a bearer key has no
  path to it regardless of how many times the operator rotates.
  See Step 2.5 — this is durable industry-level protocol knowledge,
  not a one-day API drift.
- `Connection refused` / `URLError` / timeout → upstream Venice
  unavailable, retry once after ~30s; not an auth issue.

## Step 2.5 — Discriminate "key is invalid" from "endpoint is x402-paid"

A bare `401` from Bearer auth collapses several underlying causes
into one signal and risks the wrong fix (key rotation that won't
help). Probe **three more endpoints before deciding the key is
dead**:

```bash
set -a; . /Users/vivgatesai/.paperclip/instances/default/.env; set +a
python3 -c "
import os, json, urllib.request, urllib.error
key = os.environ['VENICE_API_KEY']
base = 'https://api.venice.ai/api/v1'

def probe(label, url, headers, body=None):
    req = urllib.request.Request(url, method='POST' if body else 'GET',
        data=json.dumps(body).encode() if body else None, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            print(f'{label}: {r.status} OK')
    except urllib.error.HTTPError as e:
        b = e.read().decode('utf-8','ignore')[:160]
        print(f'{label}: {e.code} - {b}')

bearer = {'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}
xapikey = {'X-Api-Key': key, 'Content-Type': 'application/json'}

# 1. Should always work for any authenticated key (admin surface)
probe('GET /models (Bearer)', f'{base}/models', bearer)

# 2. The failing endpoint, with X-Api-Key to probe paid-protocol scope
probe('POST /augment/search (X-Api-Key)', f'{base}/augment/search',
      xapikey, {'query': 'probe', 'limit': 1})

# 3. Chat completions — confirms whether the alternate fallback
#    (enable_web_search='auto') is also dead
probe('POST /chat/completions (Bearer)', f'{base}/chat/completions',
      bearer, {'model': 'gemma-3-27b-it',
               'messages': [{'role':'user','content':'hi'}],
               'max_tokens': 5})
"
```

Discriminator matrix:

| `/models` | `/augment/search` Bearer | `/augment/search` X-Api-Key | `/chat/completions` Bearer | Verdict |
|---|---|---|---|---|
| 200 | 401 | **402 `x402Version:2`** | 401 | Endpoint is x402-paid. Bearer key is fine for admin; even a fully-rotated key won't reach `/augment/search` without paid-protocol settlement. **Don't just rotate — switch to a paid-protocol key OR change the source.** Note: `news_harvester`'s `enable_web_search="auto"` fallback is also unreachable since `/chat/completions` is also 401 with the bearer key. |
| 200 | 401 | 401 or 402 (no x402) | 401 | Key authenticates `/models` but lacks inference scope (per-key gating on Venice side). Key was likely downgraded or scoped; rotate and retry. |
| 200 | 401 | 200 (or other 2xx/4xx-not-401) | 200 | Transient — Bearer auth failed for THIS endpoint only. Just retry the pipeline; do NOT rotate the key. |
| 401 | 401 | 401 | 401 | Key is broadly broken across the surface. Almost certainly a malformed placeholder value or fully revoked. Apply Pitfall #1 (SKILL.md): check `len()`, prefix, and that `VENICE_API_KEY` ≠ `VENICE_INFERENCE_KEY`. Then rotate both. |

The x402 `{"x402Version": 2, "accepts": [...]}` response includes a
machine-readable settlement spec in `accepts[]`. x402 is an
industry-level payment protocol (Coinbase, Cloudflare, others),
presenting as `HTTP 402` with a structured `accepts` list. Venice
has begun migrating endpoints behind it. The migration is durable
knowledge for any Venice work — not a one-day API drift — so the
discriminator above should always be the second probe, not just
when the bearer probe looks "weird".

## Step 3 — Decision

| Diagnostic combination | Verdict | Action |
|---|---|---|
| 401 on probe + ≥3 days empty harvests | Persistent key failure | Regenerate `VENICE_API_KEY` at venice.ai → API settings. Rewrite BOTH `~/.hermes/config.yaml` AND `~/.paperclip/instances/default/.env` (the keys can drift). Do NOT retry the pipeline today. |
| 401 on probe + past days had items | Recent key rotation or token revocation | Treat as persistent for today — do NOT queue another cron run with the same key. Ask the user to confirm before regenerating. |
| Network/timeout (not 401) | Upstream Venice health | Retry once after ~30s; if still failing, escalate to user. |
| Probe returns 200 | Transient flake | Re-run the pipeline normally. |

## Reference transcript — 2026-07-03 (persistent, scope-limited)

The daily cron aborted cleanly with these signals:

```
[daily] 2026-07-03 — starting pipeline (generate_assets=True, n_variants=2)
[0/7] budget pre-flight
      spent=$0.0000 / cap=$10.00  (remaining $10.0000)
[1/7] refresh_pricing
      text=89, image=28
[2/7] news_harvester.harvest
[news_harvester] search HTTP 401 for 'AI pharma news today': {"error":"Authentication failed"}
[news_harvester] search HTTP 401 for 'AI FDA drug approval': {"error":"Authentication failed"}
[news_harvester] search HTTP 401 for 'AI clinical trial result': {"error":"Authentication failed"}
PIPELINE FAILED: news_harvester returned no items
```

Historical check:

```
2026-07-01: 65 bytes, 0 items
2026-07-02: 65 bytes, 0 items
2026-07-03: 65 bytes, 0 items
```

Direct probe: `HTTP 401 - {"error":"Authentication failed"}`.

Pre-flight had passed cleanly (`OK: $0.0000/$10.00`), so this is
NOT a budget problem and `spend >= cap` is NOT the cause. The
aborted pipeline consumed `sources_cost=$0.03` (3×$0.01 search
calls, no scrapes succeeded). Telegram 50/75/90% alerts did not
fire (well below threshold). The pre-flight ledger showing `$0.00` alongside the side-channel `sources_cost=$0.03` in `/tmp/daily_news_*.json` is NOT a contradiction — those are independent accounting paths, see Pitfall #19 in `SKILL.md`.

**Verdict:** Persistent auth failure (Step 2.5 discriminator row
`200 / 401 / 401 / 401` — key authenticates admin surface but
lacks augment/chat scope). Operator-side fix only: regenerate
`VENICE_API_KEY` with augment scope at venice.ai → API settings,
OR swap `news_harvester.search()` to a non-Venice backend (Tavily /
SerpAPI / Brave). No point retrying today — every call will 401
with the same key. If the user is unavailable until later, the
cron simply skips that day; the next morning's cron will succeed
if the key has been rotated by then.

## Reference transcript — 2026-07-15 (4-week recurring)

By mid-July, the same failure has been repeating every day for the
AIPharmaXchange cron since at least 2026-06-19 — a **~26-day
recurrence**. The shape is identical: `$0.0000/$10.00` pre-flight,
`text=N, image=M` refresh_pricing success (proves `/v1/models`
works), then 3× `HTTP 401` on augment/search, then hard abort.

```
2026-07-11: 65 bytes, 0 items
2026-07-12: 65 bytes, 0 items
2026-07-13: 65 bytes, 0 items
2026-07-14: 65 bytes, 0 items
2026-07-15: 65 bytes, 0 items   ← today
```

`session_search` confirms earlier failures: 2026-06-19, 2026-06-21,
2026-06-26, 2026-07-05, 2026-07-12 — same stderr fingerprint, all
reports the same root cause. **The daily cron has been producing
0 content for over three weeks.** `content_library.jsonl` last
successful run: **2026-06-14** (a *Nature Medicine* review of AI in
drug development).

Direct probe (Step 2.5) on 2026-07-15:

| Endpoint | Status | Notes |
|---|---|---|
| `GET /v1/models` (Bearer) | **200** | admin surface is fine — that is why step [1/7] `refresh_pricing()` succeeds |
| `POST /v1/augment/search` (Bearer) | **401** | news_harvester's 3 default topics |
| `POST /v1/chat/completions` (Bearer) | **401** | gemma-4-uncensored extraction call would also fail |
| `POST /v1/image/generate` | (untested; presumably 200 if scope is image-only) | flux-2-pro image path |

This matches the **scope-limited** failure mode — key authenticates
admin surface (`/v1/models` 200) but lacks augment and chat scope
(both 401). The key value itself is well-formed (63 chars, starts
with the legitimate `VENICE_INFERENCE_KEY__` prefix; NOT a
placeholder or truncated corruption — see Pitfall #1 in SKILL.md).

**Verdict:** Persistent scope-limited key failure lasting ≥26
days. The pre-flight's continued clean `$0.0000/$10.00` reading,
combined with the clean empty `/tmp/daily_news*.json` fingerprint
across that whole span, means the cron is failing *gracefully*:
zero Diem has been burned across the entire outage because the
401 fails before `record_spend()` is ever called. **That is the
correct behavior — don't audit the pre-flight thinking it's
broken just because the pipeline content is empty.**

**Recommendation to operator:** when a 401-augment fingerprint
persists for ≥3 consecutive days, stop recommending "wait and see"
or "monitor" — escalate with the cadence number ("12 days
running", "26 days running") and one of two concrete next steps:
(a) rotate the key with augment scope, or (b) swap the search
backend to a non-Venice provider. The cron will keep running
every day either way, but no content will be produced.
