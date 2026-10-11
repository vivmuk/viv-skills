---
name: venice-api
version: 0.6.0
description: Venice AI API via MCP Server — 31 tools for chat, image, video, audio, music, web search, crypto. Uncensored, private AI.
tags: [venice, api, mcp, llm, image-gen, video-gen, tts, music]
---

# Venice AI API via MCP Server

Use the Venice MCP Server (`@veniceai/mcp-server`) to access Venice's uncensored AI API. 31 tools across all modalities.

## Setup

Requires `VENICE_API_KEY` (get from venice.ai). Configure as MCP server or run directly:
```
npx -y @veniceai/mcp-server@0.2.0
```

## Tools Reference (31 total)

### Chat & Embeddings (x402 + API key)
- `venice_chat` — Chat completion. messages[] + model (default: `venice-uncensored`). Supports Claude, GPT-5, Llama, DeepSeek, Qwen, GLM, Kimi, etc.
- `venice_responses` — Responses API. Input as string or messages array.
- `venice_embeddings` — Text embeddings. OpenAI-compatible.
- `venice_chat_with_character` — Chat with a Venice character by slug. (API key only for character lookup)

### Image (x402 + API key)
- `venice_image_generate` — Generate image. prompt + model (default: `flux-2-pro`). Supports width/height/steps/style_preset/seed/negative_prompt. Models: Flux 2 Pro/Max, Lustify SDXL, Anime (WAI), Qwen Image, GPT Image, Nano Banana Pro.
- `venice_image_edit` — Edit image with prompt. image_url + prompt. Default model: `firered-image-edit`.
- `venice_image_multi_edit` — Multi-image composition. image_urls[] + prompt.
- `venice_image_upscale` — Upscale 1-4x. image_url + scale.
- `venice_image_remove_bg` — Remove background. image_url.
- `venice_image_styles` — List style presets (auth-free).

### Video — async queue pattern (x402 + API key)
- `venice_video_generate` — Queue video gen. Returns `{model, queue_id}` (no download_url). Models: Sora 2, Veo 3.1, Kling, Wan, LTX 2, Seedance, Runway Gen-4. Supports image_url, video_url, audio_url, reference images. Duration as string like "4s"/"6s"/"8s".
- `venice_video_status` — Poll queued video. `{queue_id, model}`. Returns `PROCESSING` (JSON) or `COMPLETED` — on completion the binary mp4 is returned inline, NOT a `download_url`. **Clients that expect a URL will fail.** See "Direct REST — Video & Music" below.
- `venice_video_complete` — Mark done + cleanup. `{queue_id, model}`.
- `venice_video_transcriptions` — Transcribe YouTube URL.
- `venice_video_quote` — Price quote (auth-free).

### Audio TTS/ASR (x402 + API key)
- `venice_tts` — Text to speech. input + voice + model (default: `tts-kokoro`). Emotion tags: [whispers], [sarcastically]. Formats: mp3/wav/opus/aac/flac/pcm.
- `venice_asr` — Speech to text. audio_url. Default: `openai/whisper-large-v3`.
- `venice_voice_clone` — action="list" shows built-in voices; action="create" clones from sample_url. Cloning models: `tts-chatterbox-hd`, `tts-minimax-speech-02-hd`.

### Music — async queue pattern (x402 + API key)
- `venice_music_generate` — Queue music gen. prompt + model. Models: ace-step-15, elevenlabs-music, minimax-music-v2/v25/v26, stable-audio-25, mmaudio-v2, elevenlabs-sound-effects-v2.
- `venice_music_status` — Poll queued music. {queue_id, model}.
- `venice_music_complete` — Mark done + cleanup. {queue_id, model}.
- `venice_audio_quote` — Music cost quote (auth-free).

### Web Augment (x402 + API key)
- `venice_web_search` — Web search (Firecrawl). query + limit.
- `venice_web_scrape` — Scrape URL to markdown. url + format.
- `venice_text_parser` — Extract text from PDF/DOCX/EPUB/PPTX/XLSX URL.

### Catalog (auth-free)
- `venice_list_models` — List models. Filter: text/image/video/audio/music/embedding/all.
- `venice_image_styles` — List image style presets.

### Characters (API key only)
- `venice_list_characters` — search/tag/limit/offset.
- `venice_chat_with_character` — Chat by character_slug.

### Crypto (x402 + API key)
- `venice_crypto_rpc` — JSON-RPC to blockchain. network (e.g. "base-mainnet") + rpc_method + rpc_params.

### x402 Wallet (SIWX only)
- `venice_x402_balance` — Check wallet balance. wallet_address.
- `venice_x402_top_up_info` — Top-up requirements. wallet_address + amount_usd.
- `venice_x402_transactions` — Transaction history. wallet_address + limit.

## Key Parameter Details

### venice_chat
- messages: [{role: "system"|"user"|"assistant", content: "..."}]
- model: string (default: venice-uncensored)
- temperature: 0-2, max_tokens: int (max 32000), top_p: 0-1
- stop: string[] (max 8)

### venice_image_generate
- prompt: 1-4000 chars (⚠️ gpt-image-2 max 1500), model: default flux-2-pro
- width/height: 256-2048 (⚠️ NOT supported by gpt-image-2)
- steps: 1-50 (⚠️ NOT supported by gpt-image-2)
- style_preset: see venice_image_styles (⚠️ NOT supported by gpt-image-2)
- seed: int (⚠️ NOT supported by gpt-image-2), safe_mode: bool, negative_prompt: string

### venice_video_generate
- prompt: 1-4096, model: REQUIRED (e.g. "veo3.1-fast-text-to-video")
- duration: string enum ("4s","6s","8s")
- aspect_ratio: "16:9"|"9:16"|"1:1"|"2:3"|"3:2"|"3:4"|"4:3"|"21:9"
- Optional: image_url, video_url, audio_url, end_image_url
- reference_image_urls: up to 9, reference_video_urls: up to 3, reference_audio_urls: up to 3

### venice_tts
- input: 1-4096 chars, voice: string (e.g. "af_heart", "leah")
- model: default tts-kokoro, speed: 0.25-4
- response_format: mp3|wav|opus|aac|flac|pcm

## Async Pattern (Video & Music)

High-level summary — empirically verified July 2026 against live `api.venice.ai/api/v1`. **The earlier "download_url available" claim was wrong for the REST endpoint**; see the "Direct REST — Video & Music" section below for full shapes.

1. **Generate** → `POST /video/queue` returns `{model, queue_id}` (NOT `download_url`).
2. **Poll** → `POST /video/retrieve {model, queue_id}` → during processing returns 200 + `application/json` + `{"status":"PROCESSING", …}`; on completion returns 200 + `Content-Type: video/mp4` + raw binary mp4 body (2–12 MB). **The mp4 is returned inline — there is no `download_url` field to follow.**
3. **Cleanup** → `POST /video/complete {model, queue_id}` is best-effort and currently a no-op for most models.
4. Music (`/music/queue`, `/music/status`, `/music/complete`) and async audio (`/audio/queue`, `/audio/retrieve`, `/audio/complete`) follow the same contract.

## Direct REST — Video & Music (without MCP)

When integrating video / music into Python/Node codebases (httpx, fetch, requests) without going through the MCP server, these are the verified REST endpoints. **All video / music / async-audio endpoints require `Authorization: Bearer …` and 200 responses come back EITHER as `application/json` OR as raw binary `video/mp4` / `audio/mpeg` — branch on `Content-Type`, not on response status alone.**

### `POST /video/quote` — Price quote (auth-free)

```bash
curl -s https://api.venice.ai/api/v1/video/quote \
  -H "Content-Type: application/json" \
  -d '{"model":"wan-2.6-text-to-video","duration":"5s","aspect_ratio":"16:9"}'
```

Response: `{"quote": 0.83}` (USD). Quotes are auth-free — useful for showing a price preview before the user supplies a key. The same shape works for `/audio/quote`.

### `POST /video/queue` — Queue a generation job

```bash
curl -s -X POST https://api.venice.ai/api/v1/video/queue \
  -H "Authorization: Bearer $VENICE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"wan-2.6-text-to-video","prompt":"blue ocean waves","duration":"5s","aspect_ratio":"16:9"}'
```

Response: `{"model":"<id>","queue_id":"<uuid>"}` — typically 80–95 bytes. **Does NOT return a `download_url`** (the earlier "download_url available" MCP-tool hint was misleading — only the MCP tool's wrapper added such a field). Do not assume a URL is present; the next step is always a poll against `/video/retrieve`.

Per-model required params (gateway validates strictly):

| Param family | Required when | Notes |
|---|---|---|
| `prompt` | always | 1–4096 chars |
| `duration` | always | String enum, **per-model** — `["4s","6s","8s"]` for Veo 3.1, `["5s","10s","15s"]` for Wan 2.7, `["5s","8s"]` for Pixverse, `["4s","8s","12s"]` for Sora 2. Sending the wrong enum = 400. |
| `aspect_ratio` | text-to-video models | `"16:9"` or `"9:16"` for most. image-to-video / upscale models reject this field. |
| `resolution` | only models that advertise it | Veo 3.1 accepts `"720p"`, `"1080p"`, `"4k"`. |
| `image_url` | image-to-video ONLY | Some models also require `reference_image_urls[]` array instead. |
| `consents` | face-detected inputs on Seedance / runtime 409 | Pass-through attestation: re-POST the same body with `consents: {...}`. |

Always read `/v1/models?type=video` first to get the per-model `model_spec.constraints` block before constructing a request — the per-model enums drift with each release.

### `POST /video/retrieve` — Poll for completion (the tricky one)

```bash
curl -s -X POST https://api.venice.ai/api/v1/video/retrieve \
  -H "Authorization: Bearer $VENICE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"wan-2.6-text-to-video","queue_id":"019f4e85-…"}'
```

**This endpoint has two completely distinct response shapes based on status — your poller MUST branch on `Content-Type`:**

**During processing (~200 ms each call, body ~80 bytes):**
```http
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8

{"status":"PROCESSING","average_execution_time":125635,"execution_duration":21470}
```

**When complete (~125–200 ms for the binary stream itself, body 2–12 MB):**
```http
HTTP/1.1 200 OK
Content-Type: video/mp4
Content-Length: 12413738

<binary mp4 bytes>
```

There is **no JSON COMPLETED response with `video_url`** — the bytes ARE the deliverable. This is also **idempotent**: completed jobs return the same binary mp4 every time you poll, so a duplicate poll is harmless if your proxy caches by `queue_id`.

⚠️ **Transient 5xx during the poll cycle is normal — even on jobs that ultimately succeed.** Verified pattern observed in real Railway edge logs July 2026: 3× 200 PROCESSING → 7× 500 with identical JSON body (~91 bytes each, e.g. `{"error":"Upstream temporarily unavailable. Retry after a short delay.","code":"TEMP_DOWN"}`) → 1× 200 with binary. A polling loop with `MAX_SOFT_FAILS = 6` will surface this as a terminal failure; **`MAX_SOFT_FAILS` should be ≥ 10** for video. Reset the soft-fail count on any 200 success so a recovered cycle starts the budget fresh.

When this endpoint is fronted by an Express / FastAPI proxy, also implement:
- **Upstream fetch timeout** (~95 s default, 180 s for `/video/*`) so hung connections don't escape to Express's default 500.
- **Server-side log of the upstream body on every non-OK response** so future incidents leave a breadcrumb.
- **80 MB upstream-payload cap** before base64-encoding — runaway fetches otherwise OOM the proxy.

### `POST /video/complete` — Cleanup (best-effort)

```bash
curl -s -X POST https://api.venice.ai/api/v1/video/complete \
  -H "Authorization: Bearer $VENICE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"wan-2.6-text-to-video","queue_id":"019f4e85-…"}'
```

Returns 200 JSON with success/failure flag. Fire-and-forget after you have the binary. **Do NOT rely on this to mark the queue deleted** — Venice caches completed mp4s and re-serving them on subsequent polls is harmless, so polling again when in doubt is safer than calling `complete` and then hitting a 404.

### Music — same shape, different `/audio/queue` prefix

Music (`/music/queue`, `/music/status`, `/music/complete`) follows the same contract: JSON PROCESSING during render, binary `audio/mpeg` (mp3) returned inline when COMPLETED. For full REST recipes and per-model quirks (lyrics suffix handling, `force_instrumental`, `ace-step-15` 6-min limit, etc.), see `references/venice-video-rest-shape.md` — kept under that umbrella even though it covers async video + audio + music.

For the verified full transcripts (queue calls for 12 models, COMPLETED response behavior, per-model duration/aspect_ratio enums, 5xx cascade proof), see `references/venice-video-rest-shape.md`.

## Async progress math — `average_execution_time` vs `execution_duration`

For UI progress bars, `average_execution_time` is the projection and `execution_duration` is the elapsed time on the current poll. A reasonable progress fraction is:

```js
const progress = avg_execution_time
  ? Math.min(0.97, execution_duration / average_execution_time)
  : null;  // null = unknown, render indeterminate spinner
```

Clamp at 0.97 so the bar visibly lingers in the "finalizing" state — Venice doesn't push past PROCESSING for ~3 s while it stages the binary. Don't try to be clever about touching 1.0; users prefer a smooth step than a hard jump.


## Auth Modes
- API key (VENICE_API_KEY): works for all except x402 wallet helpers
- x402/SIWX (VENICE_SIWX_TOKEN): wallet-based, no account needed
- Auth-free: model listing, style presets, quotes
- Hybrid: set both → API key wins

### Chat-completions key resolution — paperclip keys 401 on `/v1/chat/completions`

When scripting chat-completions calls (not image endpoints, not `/v1/models`), the credential validation is stricter than for the catalog/augment endpoints. Empirically verified July 2026:

| Key | `/v1/models` | `/v1/chat/completions` |
|---|---|---|
| `~/.paperclip/instances/default/.env` → `VENICE_API_KEY` | ✅ 200 | ❌ **401 Authentication failed** |
| `~/.paperclip/instances/default/.env` → `VENICE_INFERENCE_KEY` | ✅ 200 | ❌ **401 Authentication failed** |
| `~/.hermes/config.yaml` → `:model:` → `api_key` | ✅ 200 | ✅ 200 |
| `~/.hermes/hermes-agent/.envrc` → `VENICE_*` | ✅ 200 | varies (check the file) |

`GET /v1/models` is lenient — it often returns a public model catalog even without auth, or accepts the paperclip key under a more permissive scope. `/v1/chat/completions` is strict — it enforces the per-account key registry, and the paperclip workhorse keys are scoped for paperclip's own image/augment workloads, not for arbitrary chat calls.

**Resolution order for chat-completions scripts** (in priority):
1. `os.environ['VENICE_INFERENCE_KEY']` if explicitly set
2. `os.environ['VENICE_API_KEY']` if explicitly set
3. **Parse `~/.hermes/config.yaml`** for the `:model:` block's `api_key:` line (regex: `^:model:\s*\n(?:\s+.+\n)*?\s+api_key:\s*['\"]?([A-Za-z0-9_\-]{30,})['\"]?`) — this is the Hermes-agent's own Venice key, separate DIEM pool, always works for chat
4. None → fail with a clear "set VENICE_INFERENCE_KEY or wire :model: api_key in ~/.hermes/config.yaml" message

Image scripts should still try paperclip first per the existing DIEM-fallback chain below; only chat scripts need the config-parsing fallback. See `references/venice-chat-completions-quirks.md` for the full transcript + `scripts/resolve_venice_key.py` for a reusable resolver.

## OpenAI SDK Integration (Python)

When using the `openai` Python SDK pointed at Venice (`base_url="https://api.venice.ai/api/v1"`), there are critical compatibility issues to handle:

### `extra_body` for Venice-specific parameters

The OpenAI SDK validates kwargs against the OpenAI API schema and rejects unknown parameters like `venice_parameters`. Use `extra_body=` to pass Venice-specific params:

```python
from openai import AsyncOpenAI

client = AsyncOpenAI(
    api_key=VENICE_API_KEY,
    base_url="https://api.venice.ai/api/v1",
)

# ✅ Correct — extra_body bypasses SDK validation
resp = await client.chat.completions.create(
    model="deepseek-v4-pro",
    messages=messages,
    temperature=0.3,
    extra_body={"venice_parameters": {"include_venice_system_prompt": False}},
)

# ❌ Wrong — SDK rejects unknown kwarg
resp = await client.chat.completions.create(
    model="deepseek-v4-pro",
    messages=messages,
    venice_parameters={"include_venice_system_prompt": False},  # TypeError!
)
```

### Content filtering bypass

Venice may reject scraped web content with `{"error": "Input text data may contain inappropriate content."}` (HTTP 400). This is an input-side safety filter on models like `deepseek-v4-pro`, not an output refusal.

**Fix:** Pass `venice_parameters: {include_venice_system_prompt: false}` via `extra_body`. This disables the Venice-injected system prompt that enables content filtering on the input.

This is essential for pipelines that feed raw scraped web text into the LLM (e.g., knowledge distillation, research summarization).

### `max_tokens=None` sends `null`, causes 400

Venice's API does not accept `null` for `max_tokens`. When using the OpenAI SDK, passing `max_tokens=None` serializes to `"max_tokens": null` in the JSON body, which Venice rejects with a 400 error.

**Fix:** Conditionally include `max_tokens` only when it has a value:

```python
kwargs = dict(model=model, messages=messages, temperature=temperature)
if max_tokens is not None:
    kwargs["max_tokens"] = max_tokens

resp = await client.chat.completions.create(**kwargs, extra_body=extra_body)
```

### Recommended models

Model catalog changes frequently. Query `venice_list_models` or `GET /v1/models?type=text` (or `?type=image`) for the current list. Below are the best-in-class picks as of May 2026.

> **Live API is the source of truth, not the local catalog.** Bundled MCP-server catalog snapshots, OpenClaw plugin manifests, and any local "model lists" go stale. When a user names a model, **first verify with `GET /api/v1/models`** (or `venice_list_models`) before assuming it doesn't exist. Case study (2026-06-14): user asked to set OpenClaw to `minimax-m3-preview`; the bundled OpenClaw plugin only listed `minimax-m21` and `minimax-m25`, but a live `GET /v1/models` returned the preview model as a real entry. Trust the API.

#### LLM / Chat models

| Model | Context | Notes |
|-------|---------|-------|
| `openai-gpt-55-pro` | 1M | Top-tier reasoning, no input content filter issues |
| `deepseek-v4-pro` | 1M | ⚠️ Input-side content filter blocks scraped web text (HTTP 400). Use `extra_body={"venice_parameters": {"include_venice_system_prompt": False}}` to attempt bypass, or use `gemma-4-uncensored` for raw pipeline stages |
| `deepseek-v4-flash` | 1M | Faster/cheaper DeepSeek. Same content filter caveat as `deepseek-v4-pro` |
| `claude-opus-4-8` | 1M | Excellent long-context reasoning |
| `grok-4-20` | 2M | Largest context window available. Newest Grok |
| `qwen-3-7-max` | 1M | Strong multilingual, 1M ctx |
| `google-gemma-4-31b-it` | 256K | Same family as `gemma-4-uncensored` but instruction-tuned (not uncensored) |
| `kimi-k2-6` | 256K | Strong general-purpose |
| `gemma-4-uncensored` | 256K | **Best for raw scraped web text** — no input-side content filter. Default for pipelines that feed scraped content into the LLM |
| `venice-uncensored-1-2` | 128K | Uncensored chat, smaller context |
| `zai-org-glm-5-1` | 200K | Good general-purpose, no known filter issues |

#### Smart model routing

When a pipeline has stages with different requirements, route to different models rather than using one model for everything:

- **Raw/scraped-text stages** (web scraping, distillation, research extraction) → `gemma-4-uncensored` (no content filter, 256K ctx)
- **Final authoring/critique stages** (synthesis, quality review, formatting) → `openai-gpt-55-pro` or `deepseek-v4-pro` (higher quality, 1M ctx, no scraped text in input)
- **Fast/cheap stages** (identity resolution, simple classification) → `deepseek-v4-flash` or `llama-3.3-70b`

This avoids content filter failures on raw stages while getting the best quality on final output.

#### Image generation models

**User preference: `grok-imagine-image-quality` is the SOTA image model for this account** (verified by direct user directive — "always use the grok sota model for image generation"). Use it first; fall back to `gpt-image-2` or `flux-2-max` only if it returns 402 / DIEM-spend errors or is unavailable for the requested parameters. If all image models return 402 due to DIEM spend limit, see the **Fallback when image models are blocked** section below — do NOT silently produce a Pillow-only mock.

**Avoid `openai-gpt-55-pro` for any agent or pipeline on this account** — the user has flagged it as "very expensive." It appears in the chat-model catalog but should not be selected for production agents, content pipelines, or research stages. For premium text reasoning, use `grok-4-20` (cheaper, 2M ctx). For uncensored scraped-text stages, use `gemma-4-uncensored`. The `gpt-55-pro` entry stays in the catalog table as a reference; do not actively route to it.

| Model | Notes |
|-------|-------|
| `grok-imagine-image-quality` | **Preferred SOTA.** ⚠️ **Unique response format**: returns `images` as array of plain base64 strings (NOT `data[].b64_json`). Rejects `resolution`, `cfg_scale`, `steps`, `style_preset`, `seed` — only `model`, `prompt`, `aspect_ratio`, `format`, `hide_watermark`, `safe_mode` accepted. Good for data-heavy infographic slides. See `references/image-response-format-compat.md` |
| `gpt-image-2` | Excellent prompt adherence, latest OpenAI. ⚠️ **Does NOT accept `width`/`height`/`steps`** — only `prompt`, `model`, `n`, `response_format`. Prompt max **1500 chars** (not 4000). See `references/gpt-image-2-constraints.md` |
| `flux-2-max` | Best Flux quality, detailed portraits |
| `flux-2-pro` | Strong quality, good balance of speed/quality. Default in MCP `venice_image_generate` |
| `nano-banana-pro` | Upgrade from nano-banana-2, same family, better quality. ⚠️ Does NOT support `response_format: "b64_json"` — returns 400. Omit `response_format` and use default (URL) format, or use `flux-2-max` instead |
| `recraft-v4-pro` | Professional illustration quality |
| `gpt-image-1-5` | Mid-range OpenAI image model |
| `seedream-v4` | Strong portrait generation |
| `qwen-image-2-pro` | Good quality alternative |
| `hunyuan-image-v3` | Tencent's model, solid quality |
| `nano-banana-2` | Fast/cheap, good for avatars and thumbnails. **Also the budget pick for infographic backgrounds** (~14s, $0.10–0.19, 848×1264 PNG). See "Background-quality confirmation" under Direct REST Image Generation. |

**Most image models mangle body text in dense compositions** — verified for `flux-2-max` and `gpt-image-2`: garbled words, dropped characters, text bleeding across cards. `gpt-image-2` is best-in-class for text but still imperfect for anything beyond a single-line title. **`grok-imagine-image-quality` is the exception** — with a very explicit prompt (exact text strings, font family by name, layout spelled out, brand mark explicitly forbidden from hex codes), it can render multi-card text layouts correctly. See `references/pillow-overlay-hybrid.md` for both the Pillow-overlay fallback AND the prompt-engineering pattern that lets `grok-imagine-image-quality` skip the overlay.

**Image models FABRICATE data they don't recognize** — empirically verified June 2026: when asked to render a model cost table with 6 custom-priced models (`Nemotron 3 Ultra 550B`, `minimax-m3`, `grok-4-20-multi-agent`, `deepseek-v4-pro`, `gemma-4-uncensored`, `deepseek-v4-flash`), `gpt-image-2` substituted `GPT-4o (2024-08-06)`, `Claude 3.5 Sonnet`, and `Llama 3.1 405B Instruct` with stale 2024 prices. `grok-imagine-image-quality` dropped 2/6 rows and the entire monthly section. The cardinal rule: **for any data-heavy artifact, use Pillow**. The image model is appropriate for hero images and decorative content; not for shipping artifacts that will be reviewed for data accuracy. See `branded-infographic` skill for the full workflow and case study.

## Direct REST Image Generation (without MCP)

There are **two distinct REST endpoints** for image generation, with different parameter schemas and response formats. Use the correct one for your integration:

### DIEM spend cap is per-API-key — fall back when one key is exhausted (June 2026)

When you get `HTTP 402 {"error":"API key DIEM spend limit exceeded..."}`
from one Venice key, **the limit is on that specific key, not your
account**. Try a different key before assuming the whole account
is blocked. Verified by direct test: 7 different image models
(`nano-banana-2`, `nano-banana-pro`, `flux-2-max`, `flux-2-pro`,
`grok-imagine-image-quality`, `gpt-image-2`, `venice-sd35`) all
returned the same 402 from the same exhausted key.

**Fallback keys on this system** (in load order):
1. `~/.paperclip/instances/default/.env` — `VENICE_API_KEY` /
   `VENICE_INFERENCE_KEY`. The Paperclip workhorse key. Often
   exhausted first because Paperclip agents run continuously.
2. `~/.hermes/config.yaml` → `model.api_key` — Hermes-agent's own
   Venice key. Separate DIEM pool. Use this when Paperclip's key
   hits its daily cap.
3. `~/.hermes/hermes-agent/.envrc` — another option, check for
   `VENICE_*` entries.

Both Paperclip and Hermes keys are `VENICE_INFERENCE_KEY_…`
format. The keys are NOT interchangeable in config (different DIEM
buckets), but they both authenticate against the same Venice API.

If both keys 402, the account-level DIEM is genuinely exhausted.
Daily reset at midnight UTC. Do NOT silently fall back to Pillow
for an image the user explicitly requested — surface the cap and
ask whether to wait, top up, or proceed text-only.

### Background-quality confirmation: `nano-banana-2` is the budget pick for infographic bgs

The skill catalog tags `nano-banana-2` as "fast/cheap, good for
avatars and thumbnails" — implying it's not for hero/decorative
work. **In practice, for infographic backgrounds, it is the sweet
spot.** Empirically validated June 2026 with a 2:3 portrait prompt
for a watercolor brand background:

- Generation time: ~14s (vs ~20–50s for flux-2-max, ~150–300s for gpt-image-2)
- Cost: $0.10–0.19/image (1K resolution; 1.5–2× for 2K, 2–4× for 4K)
- Output size at `aspect_ratio="2:3"`: **848×1264 PNG, ~2.5 MB**
- Visual quality: watercolor blooms, paper grain, hex grid overlay,
  cream center safe-zone — all present, fully usable as a Pillow
  overlay substrate (vision QA 6.5/10 for bg suitability; cream
  center is the load-bearing feature)
- Response format: Venice-native `images: ["<b64>", ...]` (NOT
  `data[].b64_json`)

If you need a "real" hero/decorative image with strong artistic
control, `flux-2-max` or `grok-imagine-image-quality` are still
the right picks. But for the Pillow-overlay hybrid (image model
for visual frame + Pillow for typography), nano-banana-2 is the
budget pick — and the savings let you run more iterations or
allocate budget to the final Pillow data composition.

See `branded-infographic` skill for the full hybrid pattern.

### Endpoint A: Venice-native — `POST /api/v1/image/generate`

### Endpoint A: Venice-native — `POST /api/v1/image/generate`

The primary endpoint used by the MCP server internally. Supports Venice-specific parameters like `aspect_ratio`, `format`, `hide_watermark`. **Use this endpoint for programmatic image generation from Python/scripts.**

```bash
curl -s https://api.venice.ai/api/v1/image/generate \
  -H "Authorization: Bearer $VENICE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"flux-2-max","prompt":"...","aspect_ratio":"16:9","format":"png","hide_watermark":true}'
```

**Parameters (Venice-native):**

| Parameter | Type | Notes |
|-----------|------|-------|
| `model` | string | Required |
| `prompt` | string | Max 1500 chars (gateway cap). Required |
| `aspect_ratio` | string | `"16:9"`, `"9:16"`, `"1:1"`, `"4:5"`, `"3:4"`, etc. |
| `format` | string | `"png"` or `"webp"` |
| `hide_watermark` | bool | Remove Venice watermark |
| `safe_mode` | bool | Enable content safety filter |
| `width` | int | Explicit pixel width (alternative to aspect_ratio) |
| `height` | int | Explicit pixel height (alternative to aspect_ratio) |
| `cfg_scale` | float | ⚠️ Rejected by `grok-imagine-image-quality` |
| `steps` | int | ⚠️ Rejected by `grok-imagine-image-quality` |
| `seed` | int | Reproducible generation |
| `style_preset` | string | ⚠️ Rejected by `grok-imagine-image-quality` |
| `negative_prompt` | string | Exclude concepts |
| `variants` | int | Number of images |
| `resolution` | string | ⚠️ Rejected by `grok-imagine-image-quality` |

**Response format (Venice-native):**

```json
{
  "id": "...",
  "images": ["<base64-encoded-string>", ...],
  "request": {...},
  "timing": {...}
}
```

⚠️ **`images` is an array of plain base64 strings** — NOT the OpenAI-style `data[].b64_json` wrapper. Some models (e.g., `grok-imagine-image-quality`) use this format. Others may return `data[].b64_json` or `data[].url`. Parse defensively:

```python
result = json.loads(resp.read())
# Try Venice-native format first
images = result.get("images", [])
if images and isinstance(images[0], str):
    img_bytes = base64.b64decode(images[0])
else:
    # Fall back to OpenAI-compatible format
    data = result.get("data", [])
    if data and "b64_json" in data[0]:
        img_bytes = base64.b64decode(data[0]["b64_json"])
    elif data and "url" in data[0]:
        # Download from URL
        ...
```

See `references/image-response-format-compat.md` for the full model-by-model breakdown.

### Endpoint B: OpenAI-compatible — `POST /api/v1/images/generations`

Compatible with the OpenAI SDK and curl patterns from OpenAI docs. Uses `size` instead of `width`/`height`/`aspect_ratio`.

```bash
curl -s https://api.venice.ai/api/v1/images/generations \
  -H "Authorization: Bearer $VENICE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"flux-2-max","prompt":"...","n":1,"size":"1024x1024"}'
```

**Parameters (OpenAI-compatible):**

| Parameter | Type | Notes |
|-----------|------|-------|
| `model` | string | Required |
| `prompt` | string | Max 1500 chars (gateway cap). Required |
| `n` | int | Number of images |
| `size` | string | `"1024x1024"`, `"512x768"`, etc. |
| `response_format` | string | `"b64_json"` or `"url"` |

**Response format (OpenAI-compatible):**

```json
{
  "data": [
    {"b64_json": "..."} // or {"url": "https://..."}
  ]
}
```

### Critical parameter differences between endpoints

| Parameter | Venice-native (`/image/generate`) | OpenAI-compatible (`/images/generations`) |
|-----------|-----------------------------------|------------------------------------------|
| Dimensions | `width` + `height` OR `aspect_ratio` | `size` only (e.g. `"1024x1024"`) |
| Style preset | `style_preset` | ❌ Not supported |
| Steps | `steps` | Supported for Flux models |
| Aspect ratio | `aspect_ratio` | ❌ Not supported (use `size`) |
| Format | `format` (`png`/`webp`) | ❌ Not supported (use `response_format`) |
| Watermark | `hide_watermark` | ❌ Not supported |

**⚠️ Passing `width`, `height`, or `style_preset` to the OpenAI-compatible endpoint returns:**
```json
{"details": {"_errors": ["Unrecognized key(s) in object: 'width', 'height', 'style_preset'"]}}
```

**⚠️ Passing `size` or `n` to the Venice-native endpoint may also fail.** Use the correct parameter schema for the endpoint you're calling.

**Recommendation:** Use the **Venice-native endpoint** (`/api/v1/image/generate`) for programmatic image generation — it supports `aspect_ratio`, `format`, and `hide_watermark` which are essential for batch carousel workflows. Use the OpenAI-compatible endpoint only when integrating with OpenAI SDK code.

### Image edit endpoint — `POST /api/v1/image/edit`

Sister endpoint to the generate endpoint. Accepts an input image + a prompt, returns a modified image. Useful for *some* local fixes (background swap, color grading) but **use with caution** for text/element corrections — the model is too aggressive and tends to wipe unrelated content (cards, headings, layout) along with the thing you're trying to fix. In most cases it's better to regenerate with a corrected prompt than to use this endpoint.

```bash
curl -s -X POST https://api.venice.ai/api/v1/image/edit \
  -H "Authorization: Bearer $VENICE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "flux-2-max-edit",
    "prompt": "describe the new image you want",
    "image": "data:image/png;base64,<b64>"
  }' --output out.png
```

Available edit models (verified June 2026): `flux-2-max-edit`, `qwen-image-edit`, `gpt-image-2-edit`, `nano-banana-pro-edit`, `flux-kontext-max`, `flux-kontext-pro`, `imagen-3`, `imagen-4`, `veo-3`, `kling-2`, `luma-photon`, `ideogram-2`, `recraft-v3`, `stability-sdxl`, `imagineart-1.5-pro`. **Prompt-content note:** some edit models (e.g., `nano-banana-pro-edit`) reject prompts mentioning text removal or content manipulation. Rephrase neutrally — describe the desired end state, not what to remove.

**Response format is dual**: some models return JSON `{"images": ["<b64>"]}` (parse the base64 string), others return raw PNG bytes with `Content-Type: image/png`. Handle both:

```python
ct = resp.headers.get("Content-Type", "")
body = resp.read()
if "image/png" in ct or body[:8].startswith(b"\x89PNG"):
    img_bytes = body  # raw PNG
else:
    data = json.loads(body)
    img_bytes = base64.b64decode(data["images"][0])
```

**Default model for the MCP `venice_image_edit` tool is `firered-image-edit`**, which is fine for background swaps but not for surgical text fixes.

For full OpenAI SDK compatibility pitfalls (`extra_body`, `max_tokens`,
content filtering bypass), see `references/openai-sdk-compat.md`.

For `gpt-image-2` specific constraints (no width/height, gateway prompt limits),
see `references/gpt-image-2-constraints.md`.

For bash heredoc / `write_file` literal mangling of `***REDACTED***` and how
to work around it (the `X` * 16 pattern, /tmp/load_venice_key.sh helper, or
just use environment variables), see `references/bash-literal-mangling.md`.

For the full image model catalog with pricing, resolution, and spec-vs-reality prompt limits,
see `references/venice-image-model-catalog.md`.

For image-response-format compatibility across image models (nano-banana-pro rejects `b64_json`, grok-imagine uses a different response schema entirely),
see `references/image-response-format-compat.md`.

### Pitfalls — Upload proxy to free file hosts (litterbox.catbox.moe URL canonicalization)

`litterbox.catbox.moe` is the canonical free upload host for Venice video pipelines (1 GB / 72-hour TTL). When proxying an upload from your backend, **hit the canonical API path directly** — don't rely on the `/resources` redirect:

```
POST https://litterbox.catbox.moe/resources/
        → 301 Moved Permanently → /resources/internals/api.php
POST https://litterbox.catbox.moe/resources/internals/api.php
   (multipart: reqtype=fileupload, time=72h, fileToUpload=@file)
        → 200 https://litter.catbox.moe/<id>.<ext>
```

**Why direct?** `POST /resources` returns 301, and Node's `fetch` (and most HTTP clients) follow it — but per HTTP spec the multipart FormData POST body is **dropped** during cross-host redirects. The upstream receives an empty request and answers **403 Forbidden**. The user-visible error appears as `Upload failed: litterbox 403: ×`.

The same redirect-body-drop pattern applies to any service that 301s the upload endpoint to a different internal handler. Direct probe + then adopt the canonical URL is faster than debugging 403s from indirect hits. See `references/free-file-host-proxy.md` for the full proxy pattern, multipart fields, and the `motherless` / `pixhost` alternatives.

### Pitfalls — Prompt-polishing calls for V2V edit models need a PRESERVATION voice

When calling Venice chat to polish or rewrite a user's prompt before sending it to `wan-2-7-video-to-video` / `grok-imagine-video-to-video-private` / `happyhorse-1-0-video-to-video`, a single "creative elaboration" system prompt breaks the result. Empirically derived from a Venice-Video user session (2026-07-12, Wan 2.7 V2V two-character test):

- **Simple prompts** that ask a V2V model to add one element stay inside the model's complexity envelope → the original video is preserved, the new element is layered in.
- **Complex prompts** that demand 2+ characters + props + spatial relations + ethnicities **force a full scene rewrite**. The original dancers / subjects are replaced. The model doesn't "paste" — it adds noise across the whole latent video and re-denoises.

**Fix:** branch the system prompt on the model id. For any `-video-to-video` or `-reference-to-video` model, use:

> "You are a video-direction consultant for an edit-style V2V model. The uploaded source video is sacred. Wan-2.7 / Grok / HappyHorse edit-models preserve the original ONLY if your rewritten prompt stays below a complexity threshold. Multi-add prompts (2+ characters, props, spatial relations, ethnicities) force a full scene rewrite. **Rule: PRESERVE-FIRST. Add nothing the user did not explicitly request. Prefer minimal phrasing.** Avoid cinematic elaboration that adds background detail."

For text-to-video / image-to-video polishing, keep the standard "creative elaboration" system prompt ("tight, evocative, concrete"). Detect the model class with:

```js
const isPreserveFirst = /-video-to-video|-reference-to-video/.test(modelId.toLowerCase());
```

Always pair preservation calls with `disable_thinking: true` + `max_tokens ≤ 800` so reasoning isn't blown on background scene elaboration.

For full recipes, the dual-voice `buildSystemPrompt(modelId)` helper, and per-model style hints (grok, kling, runway, veo, sora), see `references/prompt-polishing-dual-voice.md`.

For a reusable weekly infographic report script (reads CSV, generates image via
Venice, outputs MEDIA: path for Telegram delivery), see `scripts/weekly_report.py`.

For a text-reliable infographic pattern (image model for background + PIL for
text overlay — for the rare case where grok-imagine-image-quality's prompt
pattern doesn't fit, or when the prompt is over the 1500-char gateway cap),
see `references/pillow-overlay-hybrid.md` and `scripts/pillow_infographic.py`.

For the two Venice image REST endpoints (Venice-native `/api/v1/image/generate` vs
OpenAI-compatible `/api/v1/images/generations`), parameter differences, and
response format parsing, see the "Direct REST Image Generation" section above.

## Direct REST API (bypass MCP)

When integrating Venice into Python codebases (httpx, requests) without the
MCP server, call the Augment endpoints directly:

- **Search:** `POST /v1/augment/search` — `{query, limit}`
- **Scrape:** `POST /v1/augment/scrape` — `{url, format}`
- **Text parser:** `POST /v1/augment/text-parser` — multipart form

These endpoints are not in Venice's public docs. See
`references/augment-rest-api.md` for full request/response shapes, auth,
and the npm-pack technique for discovering future endpoints.

**Replacing other SDKs:** When migrating a project from another web-search
provider (Parallel, Firecrawl, Tavily) to Venice, rewrite the client class
to call `/augment/search` and `/augment/scrape` via httpx. Preserve the
original class name so the rest of the pipeline doesn't need changes.

For a worked example of migrating a full repo (OpenRouter → Venice, Parallel
SDK → Venice Augment, building a frontend), see
`references/mimeo-integration-pattern.md`.

## Vision / Image Understanding

Venice supports sending images to chat models for analysis, OCR, and description. Not all models support vision — check `supportsVision: true` in the model spec via `venice_list_models` or the `/v1/models` endpoint.

### Vision-capable models (as of mid-2026)

| Model | Context | Notes |
|-------|---------|-------|
| `nvidia-nemotron-3-ultra-550b-a55b` | 256K | Best quality for image analysis, reasoning + vision + tools |
| `qwen-3-7-plus` | 1M | Good vision + long context |
| `z-ai-glm-5v-turbo` | 200K | Fast vision model from GLM family |
| `venice-uncensored-1-2` | 128K | Uncensored with vision |

### Direct API call for vision

When the Hermes `vision_analyze` tool fails (e.g., the main model lacks vision support), call the Venice chat API directly with a base64-encoded image:

```python
import base64, json, urllib.request

with open("image.jpg", "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode()

payload = {
    "model": "nvidia-nemotron-3-ultra-550b-a55b",
    "messages": [{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
            {"type": "text", "text": "Describe this image in detail."}
        ]
    }],
    "max_tokens": 4096,
    "venice_parameters": {"include_venice_system_prompt": False}
}

req = urllib.request.Request(
    "https://api.venice.ai/api/v1/chat/completions",
    data=json.dumps(payload).encode(),
    headers={
        "Authorization": f"Bearer {VENICE_API_KEY}",
        "Content-Type": "application/json"
    }
)
resp = urllib.request.urlopen(req, timeout=120)
result = json.loads(resp.read())["choices"][0]["message"]["content"]
```

### Pitfalls — Vision

- **Telegram compresses images severely**: Photos sent via Telegram get downscaled to ~96px wide before reaching the Hermes image cache. At this resolution, no vision model can read text or identify details. If the user sent an image you can't read, ask them for: (1) the original URL, (2) a higher-resolution screenshot (PNG preferred), or (3) the text pasted directly.
- **Image URL format**: Use `data:image/jpeg;base64,{b64}` for local files, or `https://...` for publicly accessible URLs. Relative paths and `file://` URLs do not work.
### Pitfalls — Chat completions (verified July 2026)

**`max_tokens=32000` (Venice's documented ceiling) can stall 4+ minutes with zero bytes streamed on slow models.** Empirically verified with `openai-gpt-55` and `claude-opus-4-8`:

- `openai-gpt-55` at `max_tokens=32000`: hung ~4 min, then returned HTTP 200 with truncated `finish_reason: "length"`. Real latency-to-first-byte was 240s+ even though the model wasn't producing visible tokens.
- `claude-opus-4-8` at `max_tokens=32000`: same stall pattern, similar latency.

**Working ceiling for one-shot HTML/JSON generation is `max_tokens=16384`** — yields 6,000–10,000 lines of code per model, finishes in 1–4 minutes, all 5 models in the BenchmarkViv lineup returned successfully. Don't push higher unless you specifically need >10K lines and can wait 5–10 minutes per call.

The latency ceiling per call breaks down roughly as:

| Model | `max_tokens=16384` latency | `max_tokens=32000` latency |
|---|---|---|
| `minimax-m3-preview` | ~45s | not measured |
| `zai-org-glm-5-2` | ~127s | not measured |
| `claude-opus-4-8` | ~166s | stalled 4+ min |
| `deepseek-v4-pro` | ~252s | not measured |
| `openai-gpt-55` | ~255s | stalled 4+ min |
| `qwen-image-2` (image) | n/a | confirmed working up to 32K |

**HTTP 200 + Malformed response** — distinct from the "empty content" reasoning-model case below. Some valid chat-completions responses omit `choices` entirely or shape it differently from the OpenAI spec (e.g. `minimax-m3-preview` returned HTTP 200 with `body["choices"]` missing). `body["choices"][0]["message"]["content"]` then raises `KeyError`, producing the runtime error `"Malformed response"`.

Defensive parser:

```python
def safe_get_content(body):
    try:
        return body["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError):
        # Some adapters / preview models emit different shapes; fall back to raw
        return json.dumps(body)[:2000]   # log only, do not treat as content
```

For per-call robustness in scripts that loop over multiple models, wrap the body parse:

```python
def safe_text_only(body):
    try:
        msg = body["choices"][0]["message"]
        return msg.get("content") or msg.get("text") or ""
    except (KeyError, IndexError, TypeError, AttributeError):
        return ""
```

Treat the result as empty text and log the raw body for retry — do NOT crash the whole run over a single model returning an unexpected shape.

**`stream: true` doesn't help with the stall pattern.** The model still takes the same time to produce the first chunk; streaming only reduces perceived latency when tokens arrive in bursts.

See `references/venice-chat-completions-quirks.md` for the full transcripts (curl probes, latency timing, model-by-model behavior). The `scripts/resolve_venice_key.py` helper applies the credential-resolution chain from the "Chat-completions key resolution" section above.

### Pitfalls — Reasoning / Preview Models (Empty Content ≠ Failure)

Some Venice models (preview builds, reasoning models like `minimax-m3-preview`, `google-gemma-4-31b-it`, Nemotron 3 Ultra) spend the bulk of their output budget in `reasoning_content` before emitting any final text. With a small `max_tokens`, you can see:

```json
{
  "choices": [{
    "finish_reason": "length",
    "message": {
      "content": "",
      "reasoning_content": "The user is asking me to reply..."
    }
  }],
  "usage": {"prompt_tokens": 1804, "completion_tokens": 10}
}
```

This is **not** a failure — the call returned 200, the model is just still reasoning and ran out of token budget before producing the visible reply. Signals:
- `finish_reason: "length"` with empty `content` but non-empty `reasoning_content` → budget was too small, not a registration or quota issue
- `usage.completion_tokens` is non-zero → the model did respond, it just used those tokens for internal reasoning

**Workarounds**:
- Increase `max_tokens` to the model's `maxTokens` limit (32K is common) when smoke-testing reasoning/preview models
- **Use `extra_body={"venice_parameters": {"disable_thinking": true, "strip_thinking_response": true}}` to skip the reasoning pass entirely** — the model writes its final answer directly to `content` with no reasoning overhead. This is the canonical fix when the call site doesn't need chain-of-thought (spec generation, JSON extraction, review scoring).
- For agent calls that hang for 60+ seconds on a reasoning model, kill them and rerun with a direct curl — the model is reasoning, the wrapper is fine

**Verified case study (2026-06-19, AIPharmaXchange v2 rebuild):** `google-gemma-4-31b-it` returned empty `content` + ~150-char `reasoning_content` on every call when `disable_thinking` was NOT set, even with `max_tokens=600`. The wrapper's `safe_parse_json(content)` then failed silently, the orchestration logged "OUTLINE PARSE FAIL", and the carousel pipeline never produced slides. With `venice_parameters: {disable_thinking: true, strip_thinking_response: true}`, the same model returns the final JSON in `content` cleanly with `finish_reason: "stop"`. **For any model on the reasoning/preview list, default to `disable_thinking: true` unless you specifically want the reasoning trace.**

**Content-vs-reasoning_content fallback pattern** — when you can't guarantee `disable_thinking` is honored (some adapters strip it, some models ignore it), add a fallback in your wrapper that reads `reasoning_content` when `content` is empty:

```python
msg = body['choices'][0]['message']
content = msg.get('content') or ''
if (not content or len(content.strip()) < 10):
    rc = msg.get('reasoning_content') or ''
    if rc and len(rc.strip()) > 10:
        content = rc   # disable_thinking was ignored; reasoning is the answer
```

This makes the wrapper robust regardless of which model + which adapter stack you end up on. See `references/venice-chat-call-robustness.md` for a full worked example.

## Image Generation — Model Speed Benchmarks (June 2026)

Real generation times for a ~1500-char infographic prompt at 1024×1024 via REST API:

| Model | Time | Notes |
|-------|------|-------|
| `flux-2-max` | ~20-50s | Fast, good for iterations and drafts. Returns b64_json by default. Speed varies by prompt complexity and server load. |
| `gpt-image-2` | ~150-300s | Slow but best text rendering in images. Set timeout ≥300s. Only `size`, `prompt`, `n`, `response_format` accepted. Can take up to 5 min for complex scenes. |
| `nano-banana-2` | ~10-30s | Fast/cheap, good for avatars/thumbnails. |
| `grok-imagine-image-quality` | ~20-40s | Good for data-heavy infographics. ⚠️ Different response format — `images[]` of plain b64 strings. Rejects `resolution`/`cfg_scale`/`steps`/`style_preset`/`seed`. Only basic params work. |

**Batch carousel strategy**: Generate all slides with `flux-2-max` first (fast iteration cycle), then re-render only the hero/key slide with `gpt-image-2` (best quality). This avoids paying 3-5 min per slide for the full deck.

When generating infographics or text-heavy images, prefer `gpt-image-2` for final output and `flux-2-max` for quick drafts/comparisons.

## Video Generation — Model Speed Benchmarks (July 2026)

Real `average_execution_time` from live `/video/retrieve` polls:

| Model | Avg time | Notes |
|-------|----------|-------|
| `wan-2.6-text-to-video` | ~80 s | Cheap & reliable; default pick for tx2video in this account |
| `wan-2.6-flash-image-to-video` | ~16 s ("fast" tier) | Requires `image_url`; rejects `aspect_ratio` in the request body |
| `wan-2.7-text-to-video` | ~50–90 s | Newer Wan, similar envelope, sometimes more text-faithful |
| `veo3.1-fast-text-to-video` | ~125 s | Google Veo 3.1 fast tier. Largest end-to-end budget in the Sora/Veo tier. |
| `veo3.1-full-text-to-video` | longer | Higher quality; same REST shape as the "fast" tier |
| `kling-2.5-turbo-pro-text-to-video` | ~30–60 s | Reliable mid-tier. Easy consent/retry interaction. |
| `kling-v3-pro-text-to-video` | ~30–60 s | Same family |
| `sora-2-text-to-video` | need 4s/8s/12s duration, no 5s | OpenAI tier, separate "pro" variant |
| `pixverse-v5.6-text-to-video` | ~30 s | Mid-tier, supports `duration: ["5s","8s"]` |
| `longcat-distilled-text-to-video` | fast | Distilled tier, fastest in family |
| `veo-3.1-4k`, `sora-2-4k` | budget scale linearly with resolution | Set timeout ≥300 s |
| `topaz-video-upscale` | `"Auto"` duration | Pass an existing `video_url`; not a generative model |

**Poll-strategy implication**: with `average_execution_time` ≥125 s on Veo 3.1, a naive 3 s backoff multiplied by 8-minute MAX budget only fits ~50 polls — and Venice's transient 5xx noise burns 5–10 of them. Plan for **at most 30 useful polls per render** and use the `execution_duration / average_execution_time` ratio (capped at 0.97) for the progress bar so users see real movement rather than a flat indeterminate spinner.

**For a real-time preview UX**: a 16-second Wan 2.6 flash is the cheapest option that survives the transient-5xx pattern at ≥99% success in observed logs. Reserve Veo 3.1 for final renders where the extra time pays for itself.


### ⚠️ CRITICAL: API Gateway Prompt Limit (ALL Models)

The Venice API gateway hard-caps the `prompt` field at **1500 characters for ALL image models** — not just gpt-image-2. Model specs in the catalog advertise higher limits (gpt-image-2: 10K, nano-banana-2: 32K, flux-2-max: 3K), but the gateway validation rejects anything over 1500 with:

```json
{"details": {"prompt": {"_errors": ["String must contain at most 1500 character(s)"]}}}
```

This is a gateway-level constraint, not a model limitation. When Venice lifts this cap, the full model-spec limits will apply. Until then, craft all image prompts to fit within 1499 chars regardless of which model you use.

**Prompt packing strategy for 1500 chars**: Prioritize section titles > key data points > layout direction > color scheme. Use abbreviations. Drop verbose descriptions. Each char counts.

For the full image model catalog with spec limits, pricing, and supported features, see `references/venice-image-model-catalog.md`.

### Article-to-infographic workflow

When a user shares an article (URL or screenshot) and wants an infographic:

1. **Extract article content** — For X/Twitter links, use `browser_navigate` + `document.querySelector('article').innerText` via `browser_console` to get full text. For other URLs, try `web_scrape` or browser extraction.
2. **Summarize into key points** — Extract title, author, stats, core concepts, key data points, and actionable takeaways.
3. **Craft a ≤1500 char prompt** for `gpt-image-2` — prioritize section titles, data, layout direction, and color scheme. Omit verbose descriptions.
4. **Generate** — Use `flux-2-max` first for a quick draft (~49s), then `gpt-image-2` for the final version (~225s).
5. **Deliver** — Save to `/tmp/` and send via `MEDIA:/tmp/...png` in `send_message`.

**Pitfall**: If the user sends an article as a Telegram photo, the image gets compressed to ~96px wide — unreadable by any vision model. Always ask for the URL instead.

## Config Defaults
- VENICE_DEFAULT_CHAT_MODEL: venice-uncensored
- VENICE_DEFAULT_IMAGE_MODEL: flux-2-pro
- VENICE_DEFAULT_TTS_MODEL: tts-kokoro
- VENICE_DEFAULT_ASR_MODEL: openai/whisper-large-v3
- VENICE_HTTP_TIMEOUT_MS: 60000

### Pitfalls — `style` parameter is rejected on `/api/v1/image/generate`

The `"style": "editorial"` (or `"natural"`, `"vivid"`, etc.) key in the request body is **not supported** by the Venice-native image generation endpoint as of mid-2026. Sending it returns:

```json
HTTP 400
{"details":{"_errors":["Unrecognized key(s) in object: 'style'"]},"issues":[{"code":"unrecognized_keys","keys":["style"],"path":[],"message":"Unrecognized key(s) in object: 'style'"}]}
```

**Fix:** drop the `style` key. The visual style must come from the prompt itself (e.g., "editorial medical illustration aesthetic", "painterly watercolor"). The OpenAI-compatible `/api/v1/images/generations` endpoint also does not accept `style_preset`.

**`style_preset` and `steps` and `cfg_scale` and `seed` and `resolution` are similarly rejected by `grok-imagine-image-quality`** — see the model-specific parameter table above. Don't copy these fields over from other image models.

### Pitfalls — Image dimension caps (per model, not per endpoint)

The dimension cap is per-model, not per-endpoint. Empirically verified June 2026:

| Model | Max dimension (per axis) | Max area | Verified at |
|---|---|---|---|
| `grok-imagine-image-quality` | **1024** (NOT 1280 as the catalog implies) | 1024×1024 only | request `1024×1280` → got `1024×1024` square; request `1280×1280` → 400 |
| `gpt-image-2` | N/A — only `size: "1024x1024"`, `"1024x1792"`, `"1792x1024"` accepted | 1792×1024 max | `references/gpt-image-2-constraints.md` |
| `flux-2-max`, `flux-2-pro` | 2048 per axis | up to 2048×2048 | documented |
| `nano-banana-2` | ~1264 height (returns 848×1264 for `aspect_ratio: "2:3"`) | decent for bgs | verified June 2026 |

**For LinkedIn carousels with `grok-imagine-image-quality`:** use `width: 1024, height: 1024` (square). The image model will square-cap you even if you ask for 4:5 portrait.

**Empirical finding (2026-06-18):** the MIRA carousel asked for 1024×1280 (4:5 LinkedIn portrait) on `grok-imagine-image-quality`; all 7 PNGs came back as 1024×1024. Square is actually fine for LinkedIn (cleanest carousel format), but the prior guidance in this skill ("1024×1280 is the max 4:5 LinkedIn size") is wrong for `grok-imagine-image-quality`. It may apply to other models, but always verify the actual output dimensions after the first render — don't trust the request params.

### Pitfalls — Nemotron CoT-then-JSON pattern

`nvidia-nemotron-3-ultra-550b-a55b` (and similar reasoning-tuned models) often return content that begins with chain-of-thought text **before** the JSON block:

```
The user wants a 7-slide carousel spec for the MIRA paper. I should structure
each slide with title, body bullets, key claim, and visual hint. Let me think
about which metrics are most important...

{
  "slides": [
    {"slide_num": 1, "title": "...", ...}
  ]
}
```

Plain `json.loads(content)` will fail because the content has prose preamble.

**Fix:** regex-extract the JSON block before parsing:

```python
import re, json

def safe_parse_json(text):
    # Try direct first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Try extracting the largest {...} block
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    # Last resort: try markdown-fence extraction
    m = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    return None
```

This pattern handles Nemotron CoT, minimax-m3 (when it returns content with preamble), and markdown-fenced responses.

### Pitfalls — JSON output reliability

When calling Venice chat for structured output (reviewer scores, spec JSON, classifications), **`response_format: {"type": "json_object"}` is supported by some models and NOT others**. Empirical matrix (June 2026):

| Model | `response_format: json_object` support |
|---|---|
| `nvidia-nemotron-3-ultra-550b-a55b` | ✅ Works. Use as default. |
| `grok-4-20` | ✅ Works. |
| `gemma-4-uncensored` | ✅ Works. |
| `minimax-m3` | ❌ HTTP 400 — does NOT support this parameter. Use a different model or `safe_parse_json` fallback. |
| `deepseek-v4-pro`, `deepseek-v4-flash` | ❌ HTTP 400 on most prompts (separate content filter issue, see below) |

**Workaround for models that reject `response_format: json_object`:**
1. Switch to Nemotron for the spec/review calls (preferred)
2. Or use free-form text + `safe_parse_json` with regex extraction (handles markdown fences, brace extraction, quote repair)

```python
import urllib.request, json
req = urllib.request.Request(
    f"{VENICE_BASE}/chat/completions",
    data=json.dumps({
        "model": "nvidia-nemotron-3-ultra-550b-a55b",   # not minimax-m3
        "messages": [
            {"role": "system", "content": "You are an accuracy reviewer. Return JSON only."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 800,
        "response_format": {"type": "json_object"},   # safe with Nemotron
    }).encode(),
    headers={"Authorization": f"Bearer {VENICE_KEY}", "Content-Type": "application/json"},
    method="POST",
)
resp = urllib.request.urlopen(req, timeout=60)
body = json.loads(resp.read())
content = body["choices"][0]["message"]["content"]
data = json.loads(content)   # succeeds because response_format enforced JSON on Nemotron
```

The system prompt must also be explicit ("Output JSON only. No preamble, no markdown fences.") as a belt-and-suspenders measure. Strip-then-parse logic is no longer needed when `response_format` is set.

### Pitfalls — Video / async polling (verified July 2026 in production logs)

These four pitfalls surfaced in real Railway edge logs from a video polling loop on `wan-2.6-text-to-video`. Address all four in any new Venice video integration:

**1. `/video/retrieve` regularly returns 5xx mid-poll, even on successful jobs.** Observed pattern: 3× 200 PROCESSING → 7× 500 with identical body (~91 bytes e.g. `{"error":"Upstream temporarily unavailable…","code":"TEMP_DOWN"}`) → 1× 200 with binary. A polling loop with `MAX_SOFT_FAILS = 6` aborts 1 retry before the binary would arrive. **Set `MAX_SOFT_FAILS ≥ 10` for video** and reset the budget on any 200 success so a recovered cycle starts fresh. Treat 429 / 408 / 5xx uniformly as retryable; surface 4xx (`400/401/402/422`) immediately.

**2. `/video/retrieve` returns the binary mp4 inline on COMPLETED — never a JSON with a `download_url`.** Proxies that call `await r.json()` first and only fall back to `arrayBuffer()` will throw on the binary stream and surface a successful completion as a 500. Branch on `Content-Type` *before* reading the body:

```js
const ct = r.headers.get('content-type') || '';
const isJson = ct.includes('application/json');
const isBinaryVideo = ct.startsWith('video/');

if (isBinaryVideo && r.ok) {
  const buf = Buffer.from(await r.arrayBuffer());
  return res.json({ data: `data:${ct};base64,${buf.toString('base64')}`, contentType: ct, bytes: buf.length });
}
if (isJson) {
  const text = await r.text();
  return res.status(r.status).type('application/json').send(text);
}
if (!r.ok) {
  const text = await r.text();
  return res.status(r.status).json({ error: text });
}
```

**3. With no upstream timeout, a hung Venice fetch escapes to Express's default 500 handler.** Without intervention, Railway edge logs the failure as a 500 indistinguishable from a Venice 5xx. Wrap with `AbortController` and a route-aware cap — ~95 s for chat / image, **180 s for `/video/queue` and `/video/retrieve`** to cover Veo 3.1's `average_execution_time: 125635 ms`. On abort, return a clean 504 (`Venice upstream timed out`) so the client can distinguish upstream-slow from upstream-failed.

**4. The proxy must log the upstream body on every non-OK response**, otherwise future "unexplained 500" debugging is blind. One line of `console.warn` per upstream failure, with the first ~300 bytes of body:

```js
if (!r.ok) {
  const text = await r.text();
  console.warn(`[proxy ${endpoint}] upstream ${r.status} (${ct}, ${text.length}b): ${text.slice(0,300)}`);
}
```

Without this, when a user reports "render failed" weeks later, you can't tell whether it was Venice, the proxy, or the client.

**Bonus — caching completed retrieves**: since `/video/retrieve` is idempotent for COMPLETED jobs (same binary every time), a small in-memory cache keyed by `(model, queue_id)` for ~10 min would make redundant client retries free. Add it when you next touch the proxy; without it the per-retry base64 encode generates ~3.6 MB of garbage-collector churn per call on a 12 MB mp4.

### Pitfalls — Image models hallucinate text inside illustrations

**This guidance is OUTDATED and superseded by `social-carousel-generation` for carousel work.** The 2026-06-18 MIRA carousel measurement run produced hallucinated text inside limitations cards ("One mec coce card feels cocd opbasteri"), but that was on a V1 prompt with `{title}`/`{bullets}` placeholders left as literals. With V2 prompt fixes (inline real text strings, color names not hex codes, negative prompt for "gibberish letters, distorted glyphs", watercolor brand descriptor preserved), `grok-imagine-image-quality` reliably renders all 7 slide types of the MIRA carousel at publishable quality — chart labels, all 8 medical condition names, both 88.9% / 78.1% numbers, card titles, body bullets, brand mark.

**The decision rule:**
- **Carousel / multi-slide infographic (per `social-carousel-generation`):** image model renders text in the prompt. NO Pillow overlay. This is the canonical pattern and the user's hard preference.
- **One-off hero image, decorative background, non-text-bearing illustration:** image model is fine; Pillow overlay not relevant.
- **Data-heavy infographic with strict text accuracy requirements AND where you need fine typographic control:** Pillow overlay may still be the right call. See `branded-infographic` skill.

**Do not silently fall back to Pillow for carousel work** — the user has explicitly rejected it multiple times.

## Model Pricing

Per-call cost is critical for any pipeline that needs to report spend (Paperclip finance events, budget tracking, cost-aware routing). The pricing is **not in the MCP tool list** — query the live catalog with `GET /api/v1/models?type=text|image|video|audio|music` and read `model_spec.pricing`. Verified endpoint shape, extraction code, the per-million-tokens / per-image formulas, and a 2026-06-14 price snapshot are in `references/venice-pricing-api.md`. The Augment endpoints (search/scrape) are NOT in the catalog — they're flat per-call ($0.01 / $0.02).
