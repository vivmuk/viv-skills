---
title: Venice Video API Class-Level
name: venice-video-class
description: |
  Class-level umbrella for generating and assembling video through the
  Venice.ai API (text-to-video, image-to-video, reference-to-video, audio-driven
  workflows, avatar clips, FFmpeg post-production). This skill consolidates
  practical recipes from production sessions.
category: venice
tags:
  - venice
  - video
  - r2v
  - itv
  - ttv
  - kling
  - seedance
  - wan
  - ffmpeg
  - avatar
  - lip-sync
trigger: |
  Use whenever the task involves generating video through the Venice.ai API or
  assembling AI-generated clips with FFmpeg.
---

# Venice Video Production (Class-Level)

This umbrella skill covers practical Venice video workflows. For detailed
recipes from specific production sessions, see the `references/` files linked
below.

## Authentication

The Venice API key is in `~/.openclaw/auth-profiles.json` under `profiles["venice:default"].key`. It is **NOT** in `~/.hermes/config.yaml` — that file has no `api_key` field.

```bash
# Extract the key
VENICE_API_KEY=$(python3 -c "import json; print(json.load(open('$HOME/.openclaw/auth-profiles.json'))['profiles']['venice:default']['key'])")
curl -H "Authorization: Bearer $VENICE_API_KEY" https://api.venice.ai/api/v1/...
```

> **Pitfall:** Some cron job prompts contain a hardcoded Venice key (e.g., `VENICE_INFERENCE_KEY_LbAZyaw...`). That key may have limited scope and fail with `"Authentication failed"` on `/video/queue`. Always use the full key from `auth-profiles.json` for video generation. Verify the key works with `GET /models` before queuing expensive video jobs.

## Google Veo Models

Venice offers several Veo variants. List them with:
```bash
curl -s "https://api.venice.ai/api/v1/models?type=video" -H "Authorization: Bearer $VENICE_API_KEY" | python3 -c "import json,sys; [print(m['id']) for m in json.load(sys.stdin)['data'] if 'veo' in m['id']]"
```

| Model | Type | Durations | Aspect Ratios | Resolutions | Audio |
|---|---|---|---|---|---|
| `veo3-fast-text-to-video` | T2V | 4s, 6s, 8s | 16:9, 9:16 | 720p, 1080p | Yes (native) |
| `veo3-full-text-to-video` | T2V | 4s, 6s, 8s | 16:9, 9:16 | 720p, 1080p | Yes (native) |
| `veo3-fast-image-to-video` | I2V | 8s | 16:9 only | (derived) | Yes (native) |
| `veo3-full-image-to-video` | I2V | 8s | 16:9 only | (derived) | Yes (native) |
| `veo3.1-fast-text-to-video` | T2V | 4s, 6s, 8s | 16:9, 9:16 | 720p, 1080p, 4K | Yes (native) |
| `veo3.1-full-text-to-video` | T2V | 4s, 6s, 8s | 16:9, 9:16 | 720p, 1080p, 4K | Yes (native) |
| `veo3.1-fast-image-to-video` | I2V | 4s, 6s, 8s | (derived from image) | 720p, 1080p, 4K | Yes (native, configurable) |
| `veo3.1-full-image-to-video` | I2V | 4s, 6s, 8s | (derived from image) | 720p, 1080p, 4K | Yes (native, configurable) |

**Key Veo characteristics:**
- **`audio_input: false`** on all Veo models — they cannot accept a user-supplied voiceover for lip-sync. Veo generates its own native audio (dialogue, ambient sound, music) from the prompt.
- **9:16 vertical (Instagram reel format):** Use the T2V variants (`veo3-fast-text-to-video` or `veo3.1-fast-text-to-video`) with `aspect_ratio: "9:16"`. The I2V variants are locked to 16:9 (veo3) or derive from the input image (veo3.1).
- **Image-to-video with `veo3.1-fast-image-to-video` (face preservation):** Pass `image_url` (data URL or http URL) as the starting frame. The aspect ratio is **inherited from the input image** — a vertical 9:16 portrait input produces a 9:16 video. This is the best Venice-native approach for preserving a character's face from a reference photo, since text-to-video generates a new face each time and image models with `style_references` do NOT preserve identity (confirmed across krea-v2-large at 0.85 and luma-uni-1-max at 1.0 — user rejected both as "completely wrong face"). Audio is generated natively from the prompt. See `references/veo-image-to-video-recipe.md` for a worked example.
- **CRITICAL: `veo3.1-fast-image-to-video` does NOT accept `aspect_ratio`.** Passing it returns `400: {"details":{"aspect_ratio":{"_errors":["This model does not support aspect_ratio"]}}}`. The aspect ratio is always derived from the input image — omit the field entirely.
- **Poisoned queue → 500 on every retrieve.** If a queue submission accepts an unsupported parameter but still returns a `queue_id`, the job is poisoned: every `POST /video/retrieve` returns `500 {"error":"An unknown error occurred"}` indefinitely (not the normal `PROCESSING` JSON). Fix: remove the offending parameter and submit a fresh queue request — do not keep polling the poisoned queue.
- **Platform-wide image-input video retrieve outage (July 2026).** All image-input video models (image-to-video AND reference-to-video) returned `500 {"error":"An unknown error occurred"}` on every retrieve call across `veo3.1-fast-image-to-video`, `sora-2-image-to-video`, `kling-o3-pro-image-to-video`, `kling-o3-pro-reference-to-video`, and `happyhorse-1-1-image-to-video`. Queue submissions all succeeded (returned `queue_id`) but retrieve always 500'd. Meanwhile `veo3.1-fast-text-to-video` retrieve worked perfectly on the same key. **Diagnostic:** if image-to-video retrieve 500s on 2-3 polls, test text-to-video retrieve — if that works, the image-input retrieve path is down platform-wide. Fall back to T2V with detailed character description or wait.
- **Parameter mismatches across video model families.** Different families require different params for the same concept:
  - **Sora-2 does NOT accept `audio` parameter.** Both `sora-2-image-to-video` and `sora-2-text-to-video` return `400 {"details":{"audio":{"_errors":["This model does not support audio configuration"]}}}` if `audio` is passed. Audio is on by default — omit the field.
  - **Reference-to-video models need `image_url`, not `reference_image_urls`.** `kling-o3-pro-reference-to-video` returns `400 {"details":{"image_url":{"_errors":["At least one visual input is required: image_url, elements, or scene_image_urls"]}}}` if you pass `reference_image_urls`. Use `image_url` instead.
  - **Most image-to-video models reject `aspect_ratio`.** The ratio is derived from the input image. Only some reference-to-video models (Kling O3) accept it.
- **Video and image API spending limits are SEPARATE.** Image generation can exhaust its spending limit (HTTP 402) while video generation still works fine. Do not assume all Venice API calls are blocked when one category returns 402.
- **Cost-conscious:** Use `veo3-fast-*` at 720p for the cheapest runs. Use `veo3.1-full-*` at 4K for highest quality.
- **Forcing specific dialogue:** Since Veo can't accept audio input, put the dialogue/language instructions directly in the text prompt. Veo will generate native audio that attempts to match. Results are unpredictable — Veo may or may not speak the exact words/dialect requested. For precise lip-sync, use Wan I2V with `audio_url` instead.
- **Prompting for dialogue scenes:** Describe the speaker's appearance, setting, camera perspective, body language, and the content/tone of what they say. Veo handles the rest including generating matching audio.

**Veo T2V 9:16 example (cheapest, for experimentation):**
```python
payload = {
    "model": "veo3-fast-text-to-video",
    "prompt": "First-person camera walks through sun-drenched fields, tracking a young woman...",
    "duration": "8s",
    "aspect_ratio": "9:16",
    "resolution": "720p",
}
# Queue → poll /video/retrieve → save MP4
```

## Reusable recipes

- `references/v2v-cowboy-composite-session.md` — adding characters into an existing video with `grok-imagine-video-to-video-private` and `wan-2-7-video-to-video`; covers the `download_url` fallback, V2V spatial-control limits, planning/confirmation before queueing, character-count confirmation, stripping unwanted reference-image props/clothing, and why adding one element preserves the scene while adding multiple elements rewrites it.
- `references/single-photo-multi-person-action-recipe.md` — extract and animate
  several people from one photo doing a coordinated action (karate, dancing,
  sports, etc.) using Kling O3 Pro R2V.
- `references/multi-photo-couples-face-crop-r2v-recipe.md` — combine people
  from **separate photos** into one scene by extracting tight face crops and
  passing one `elements[].frontal_image_url` per face. Use this when face
  likeness is the top priority (anniversaries, reunions, celebrations).
- `references/avatar-model-constraints.md` — audio/lip-sync support matrix.
- `references/r2v-reference-preparation.md` — face-exact cutouts and Kling vs
  Grok field-name rules.
- `references/venice-video-api-recipe.md` — copy-paste queue/retrieve shapes for HappyHorse R2V, Wan I2V, music generation, and common `400`/`404` failures.
- `references/wan-2.5-i2v-real-people-recipe.md` — prompting and field rules for turning a real-people still into a music-video-style clip with Wan 2.5 image-to-video while preserving face/clothing/backdrop.
- `references/kids-educational-movie-workflow.md` — turning a child from a photo into the hero of a 1–3 minute educational adventure movie with storyboards, pop-up facts, narration, and FFmpeg assembly.
- `references/veo-image-to-video-recipe.md` — using `veo3.1-fast-image-to-video` with `image_url` to preserve a character's face from a reference photo while generating dialogue video. Includes prompt structure for non-English (Kathiawadi Gujarati) double-meaning reels.

## Quick guardrails

- Always use `POST /api/v1/video/queue`, never `/video/generate`.
- **CRITICAL: `/video/retrieve` requires the `model` field.** Omitting it returns `404` with `{"error":"Model is required"}`. The `RetrieveVideoRequest` schema marks both `model` and `queue_id` as required. Always include both:
  ```python
  retrieve_payload = {
      "model": "veo3.1-fast-text-to-video",  # must match the queue request model
      "queue_id": queue_id
  }
  ```
  This is the #1 polling failure — a 60-poll loop will waste 10+ minutes returning 404s if `model` is missing.
- Poll with `POST /api/v1/video/retrieve`; `/video/complete` deletes media.
- `wan-2.7-image-to-video` durations above 10s commonly return `400`. Queue at `10s` or less; extend scenes by concatenating multiple clips in post rather than requesting very long single clips.
- Match reference fields to the model family:
  - Kling R2V → `elements[].frontal_image_url` + `elements[].reference_image_urls`
  - Kling reference-to-video → `image_url` (NOT `reference_image_urls` — returns 400)
  - Grok R2V → flat `reference_image_urls[]`
  - Wan I2V → `image_url` (single data URL)
  - **HappyHorse R2V → flat `reference_image_urls[]` (not `image_url`)**
- **Sora-2 audio param:** Do NOT pass `"audio": true` to Sora-2 models. They return 400. Audio is on by default.
- **Image-to-video `aspect_ratio`:** Most I2V models reject `aspect_ratio` (derived from input image). Only some reference-to-video models (Kling O3) accept it.
- **Video-to-video spatial control:** V2V models (`grok-imagine-video-to-video-private`, `wan-2-7-video-to-video`) interpret positioning prompts loosely. Phrases like "directly behind her" or "grinding" nudge composition but do not guarantee exact placement. **Composition threshold:** V2V preserves the original scene well when asked to add one simple element, but rewrites the whole scene when asked to recompose with multiple new characters + props + specific poses. For precise multi-element placement, composite a reference frame first and use I2V/R2V.
- **Thin/detailed V2V props:** V2V renders falling money, confetti, cards, etc. as flat, sticker-like objects with wrong lighting and no physics. Use real stock footage overlays in FFmpeg/MoviePy instead.
- **V2V download fallback:** Grok V2V queue responses include a `download_url`. If `/video/retrieve` returns `{"status":"COMPLETED"}` JSON without switching to `video/mp4`, download directly from `download_url`.
- Seedance R2V frequently `422`s on real-people photos; prefer Kling O3 Pro R2V
  or Wan I2V for those cases.
- **HappyHorse-specific gotchas:**
  - `duration` must be a **string** (`"5s"`, `"10s"`, `"15s"`) — a number returns `400`.
  - Queue response returns `queue_id` (not `id`).
  - Motion is usually gentle/ambient; for explicit singing, dancing, or mic-holding, push the prompt hard with verbs like "sings passionately into microphone," "performs like a music video star," "dramatic boy-band choreography." Even then, expect subtle movement rather than true lip-sync.
- **Venice music generation gotchas:**
  - Music models are queued via `POST /api/v1/audio/queue` with `"model": "elevenlabs-music"` (or `ace-step-15`, `minimax-music-v2`).
  - Poll with `POST /api/v1/audio/retrieve` **including the `model` field** and using `queue_id` (not `id`). Omitting `model` returns `404`; using `id` returns `400`.
  - `elevenlabs-music` does **not** accept a `duration`/`duration_seconds` field. If the track is too long, trim it with FFmpeg after download.
  - Prompts that reference specific copyrighted songs may be rejected with a content-policy violation; describe the style/mood generically instead.
- **Async task queue gotcha:** The poll timeout on `process(action='wait')` is clamped to 60s in this environment. Long-running video/audio generation tasks will time out before completion; check the process log with `process(action='poll')` or `process(action='log')` and wait again, or run the generator in a terminal with a long timeout instead of relying on background-process wait.
