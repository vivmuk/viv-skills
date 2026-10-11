# Venice chat-completions quirks — verified July 2026

Knowledge bank for the failure modes and tuning notes that don't fit cleanly into
the headline `venice-api/SKILL.md`. Pulled from a 5-model BenchmarkViv brick-game
benchmark run that touched every category below.

## Credential resolution chain (chat-completions specific)

When `/v1/chat/completions` returns `401 Authentication failed`, `/v1/models`
often returns 200 on the same key. The catalog endpoint is lenient (accepts
workhorse keys under a public/docs scope); chat-completions is strict
(enforces the per-account key registry).

Verified on macOS with Hermes Agent `0.x` and a fresh, unmodified
`~/.paperclip/instances/default/.env`:

| Credential | `/v1/models` | `/v1/chat/completions` | notes |
|---|---|---|---|
| Paperclip env `VENICE_API_KEY` | ✅ 200 | ❌ 401 | workhorse key for paperclip image/augment workloads |
| Paperclip env `VENICE_INFERENCE_KEY` | ✅ 200 | ❌ 401 | same scope as VENICE_API_KEY; both 401 |
| Hermes config `:model:` block `api_key` | ✅ 200 | ✅ 200 | Hermes-agent's own key |
| Hermes config second `api_key:` entry (custom_providers) | ✅ 200 | ✅ 200 | separate DIEM pool, also works |

Fallback order for chat-completions scripts:

1. `os.environ["VENICE_INFERENCE_KEY"]` (explicit override)
2. `os.environ["VENICE_API_KEY"]` (explicit override)
3. Parse `~/.hermes/config.yaml` for `:model:` block's `api_key:` line
4. Look for any other `api_key:` entry in the same file (custom_providers usually have one)
5. Look in `~/.hermes/hermes-agent/.envrc` if present
6. Fail loudly — don't silently fall through to paperclip keys

The config-file parser should match the `:model:` block first (highest
specificity for the Hermes-agent's own Venice route), then fall back to any
`api_key:` line that looks like a Venice bearer token (alpha+digit+`_`+`-`,
length ≥ 30 to filter out unrelated config entries).

```python
import re, os
from pathlib import Path

def resolve_venice_key():
    env = os.environ.get("VENICE_INFERENCE_KEY") or os.environ.get("VENICE_API_KEY")
    if env: return env
    cfg = Path.home() / ".hermes" / "config.yaml"
    if not cfg.exists(): return None
    text = cfg.read_text(encoding="utf-8", errors="ignore")
    for pat in (
        r"^:model:\s*\n(?:\s+.+\n)*?\s+api_key:\s*['\"]?([A-Za-z0-9_\-]{30,})['\"]?",
        r"^api_key:\s*['\"]?([A-Za-z0-9_\-]{30,})['\"]?",
        r"^\s*api_key:\s*['\"]?([A-Za-z0-9_\-]{30,})['\"]?",
    ):
        m = re.search(pat, text, re.M)
        if m: return m.group(1)
    return None
```

The full resolver with logging + DIEM-balance check lives in
`scripts/resolve_venice_key.py`.

## `max_tokens=32000` stall pattern

The Venice docs (`venice_chat` schema) advertise `max_tokens: int (max 32000)`.
That ceiling exists but the streaming behavior degrades sharply near it for
certain models:

### Test conditions

Single prompt sent to `POST /v1/chat/completions` with `max_tokens=32000`,
`temperature=0.5`, no `stream`. Connection timeout = 600s. Same prompt across
all models.

### Observed latencies (no stream, single shot)

| Model | `max_tokens=16384` | `max_tokens=32000` | notes |
|---|---|---|---|
| `minimax-m3-preview` | ~45s | not tested | smallest model, fastest |
| `zai-org-glm-5-2` | 127.5s | not tested | |
| `claude-opus-4-8` | 165.9s | **stalled 4+ min** | returned HTTP 200 after kill, truncated |
| `deepseek-v4-pro` | 251.8s | not tested | |
| `openai-gpt-55` | 255.3s | **stalled 4+ min** | same pattern as Opus |
| `_STATUS_` for one call | | | see transcripts in curl probes (this file's appendix) |

**Conclusion:** for one-shot HTML/JSON generation where the model has headroom
but you want the call to finish in a tractable wall-clock window, set
`max_tokens=16384`. Models still produce their preferred length, latency stays
under 5 minutes per model, and the resulting output is still substantial
(6,000–10,000 lines of code per generation).

### When to push higher

Only if the model genuinely needs it (e.g. multi-file code refactor that has
to fit in one response). In that case:

- Run in background with `notify_on_complete=true` and budget ≥ 15 minutes
  per call
- Track the streaming throughput — if first byte takes >30s, kill early
- For preview/reasoning models, also pass `extra_body={"venice_parameters":
  {"disable_thinking": true}}` so they don't burn budget on chain-of-thought lines

### Streaming doesn't help with the stall

Setting `stream: true` does not change when the first chunk arrives. The model
takes the same time to begin producing output regardless of stream mode;
streaming only affects how often the server flushes chunks once production
begins. If your goal is to abort early when the model stalls, set both
`stream: true` AND a per-chunk timeout.

## HTTP 200 + Malformed response

Distinct from the "empty content / reasoning budget" failure mode in the main
SKILL.md. The header is HTTP 200 OK, but the body doesn't match the OpenAI
chat-completions schema:

- `body["choices"]` missing entirely
- `body["choices"]` is an empty array
- `body["choices"][0]` has no `"message"` key
- `body["choices"][0]["message"]` lacks `content` (and lacks
  `reasoning_content` too — not a reasoning-model case)

Empirically observed with `minimax-m3-preview` calling the simple "Reply
with pong" probe — same key, same endpoint, same payload shape that worked
for `nvidia-nemotron-3-ultra-550b-a55b`. Distinct model behavior, not a
credential issue.

### Defensive parser

```python
def safe_chat_content(body):
    """Return (content_text, was_malformed_flag).

    was_malformed=True means the body had HTTP 200 but no usable content;
    caller should log the raw body for manual inspection.
    """
    try:
        msg = body["choices"][0]["message"]
        content = msg.get("content") or msg.get("text") or ""
        return content, False
    except (KeyError, IndexError, TypeError, AttributeError):
        return "", True
```

### Pipeline pattern

```python
results = []
for model_id in MODELS:
    body = call_venice(api_key, model_id, prompt)
    if body.get("error"):
        results.append({"model": model_id, "status": "error", "error": body["error"]})
        continue
    content, malformed = safe_chat_content(body)
    if malformed:
        results.append({"model": model_id, "status": "error",
                        "error": f"Malformed response: {json.dumps(body)[:200]}"})
        continue
    results.append({"model": model_id, "status": "ok", "content": content})
```

Don't let a single malformed response crash a multi-model run. Surface it,
log it, continue.

## Appendix — diagnostic curl probes

Probes used to verify the auth/key column above (replace `$VENICE_*_KEY`
placeholders with the actual env vars; do not commit the keys):

```bash
# Probe 1: GET /v1/models with paperclip VENICE_API_KEY
K=…; KEY="$K"
curl -sS -m 15 -H "Authorization: Bearer $KEY" \
  https://api.venice.ai/api/v1/models | head -c 200; echo

# Probe 2: GET /v1/models with paperclip VENICE_INFERENCE_KEY (if different)
KI=…; KEY="$KI"
curl -sS -m 15 -H "Authorization: Bearer $KEY" \
  https://api.venice.ai/api/v1/models | head -c 200; echo

# Probe 3: GET /v1/models with hermes :model: api_key
KH=…; KEY="$KH"
curl -sS -m 15 -H "Authorization: Bearer $KEY" \
  https://api.venice.ai/api/v1/models | head -c 200; echo

# Probe 4: POST /v1/chat/completions with each key (max_tokens=16 to keep fast)
curl -sS -m 30 -X POST \
  -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"model":"minimax-m3-preview","messages":[{"role":"user",
  "content":"Reply with the single word: pong"}],"max_tokens":16,"temperature":0}' \
  https://api.venice.ai/api/v1/chat/completions | head -c 200; echo
```

If probes 1–2 return 200 but probe 4 with the same key returns 401, the key is
paperclip-scoped and you need the hermes-config key for chat.

## Models used in this benchmarking run

The verification calls above were made while benchmarking 5 chat models for
the BenchmarkViv Arcade lineup. Final verified latencies for the C-prompt
("Generate the most advanced single-file HTML Brick Breaker..."):

| Model id | Display | 16K tokens | 32K stall? | Score (heuristic) | Bytes |
|---|---|---|---|---|---|
| `openai-gpt-55` | GPT-5.5 | 255s | yes (4+ min) | 83 | 20,734 |
| `claude-opus-4-8` | Opus 4.8 | 166s | yes (4+ min) | 90 | 34,394 |
| `zai-org-glm-5-2` | GLM 5.2 | 127s | not tested | 90 | 53,259 |
| `deepseek-v4-pro` | DeepSeek V4 | 252s | not tested | 90 | 40,021 |
| `minimax-m3-preview` | MiniMax M3 | 81s (error) | malformed body | — | — |

Total cost for the 5-model run: **$1.87** at the prompt's level of complexity
(one-shot HTML generation, 1087 char prompt). The malformed MiniMax M3 response
is documented in "HTTP 200 + Malformed response" above.
