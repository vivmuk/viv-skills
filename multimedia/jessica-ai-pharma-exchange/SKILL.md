---
name: jessica-ai-pharma-exchange
title: Jessica AI Pharma Exchange Video Pipeline
version: 1.0
description: Reusable workflow for producing AI Pharma Exchange short podcast videos with Jessica voice, Seedance R2V hostess, watercolor slides, and proper lip-sync.
category: creative
tags:
  - video
  - seedance
  - r2v
  - podcast
  - jessica
  - aipharmaxchange
  - lipsync
  - elevenlabs
  - venice
---

# Jessica AI Pharma Exchange Video Pipeline

Reusable workflow for producing short-form AI Pharma Exchange podcast videos narrated by the ElevenLabs "Jessica" voice, with a hostess on the left and a watercolor infographic slide on the right, then assembled into a 1920×1080 landscape final.

## Goal

Turn a paper or topic summary into a polished ~30s split-screen video:
- Female AI Pharma Exchange hostess on the **left**
- Watercolor professional infographic slide on the **right**
- Narrated by **Jessica** via Venice `tts-elevenlabs-turbo-v2-5`
- Clean lip-sync via Seedance R2V reference-to-video
- Final total length ~30s, driven by two 15s Seedance clips

## Trigger

Use this skill whenever the user asks to produce an AI Pharma Exchange video, a Jessica-voice paper-summary video, or any short R2V hostess-led explainer with slides.

## API Schema (Venice.ai Seedance R2V)

### Queue video
```http
POST https://api.venice.ai/api/v1/video/queue
Authorization: Bearer <api_key>
Content-Type: application/json
```

**Request body fields:**
| Field | Required | Allowed values / notes |
|-------|----------|------------------------|
| `model` | yes | `seedance-2-0-enhanced-reference-to-video` |
| `prompt` | yes | Visual/motion description. See prompt template below. |
| `duration` | yes | `4s`–`15s` inclusive, as string (`"15s"`) |
| `aspect_ratio` | yes | `21:9`, `16:9`, `4:3`, `1:1`, `3:4`, `9:16` |
| `resolution` | no | `720p` works; omit if unsure |
| `negative_prompt` | no | Strongly recommended for face quality |
| `reference_image_urls` | no | Array of base64 data URLs. Required for consistent hostess identity. |
| `reference_audio_urls` | no | Array of base64 data URLs. Required for lip-sync. |
| `consents.seedance` | yes | Object with three boolean confirmations (see script). |

**Rejected fields** (will 400): `guidance_scale`, `steps`.

### Retrieve video
```http
POST https://api.venice.ai/api/v1/video/retrieve
Authorization: Bearer <api_key>
Content-Type: application/json

{"model": "seedance-2-0-enhanced-reference-to-video", "queue_id": "..."}
```

Response is `video/mp4` when ready; otherwise JSON with `status`:
`PROCESSING`, `COMPLETED`, `FAILED`, `CANCELLED`.

Average execution time observed: ~5–6 minutes for 5s–15s clips.

### Text-to-speech (Jessica)
```http
POST https://api.venice.ai/api/v1/audio/speech
Authorization: Bearer <api_key>
Content-Type: application/json

{"model": "tts-elevenlabs-turbo-v2-5", "voice": "Jessica", "input": "..."}
```

## Assets

| Asset | Default path |
|-------|--------------|
| Hostess reference portrait | `~/.hermes/image_cache/aipharmaxchange_hostess_gpt_final.jpg` — canonical user-provided hostess headshot (use this exact file for consistent identity across all future videos) |
| Project root | `~/faces/aipharmaxchange_openevidence_30s/` |
| Slides | `slides/slide1_*.jpg`, `slides/slide2_*.jpg` |
| Host clips | `host_video/seg1.mp4`, `host_video/seg2.mp4` |
| Audio | `audio/seg1_jessica_*.mp3`, `audio/seg2_jessica_*.mp3` |
| Final video | `final/openevidence_jessica_natural_final.mp4` |

## Pipeline Steps

### 1. Write the narration script

- Two segments max (Seedance clip limit ~15s).
- Each segment ≤ ~15s of spoken audio.
- Segment 1: hook + topic/cases.
- Segment 2: findings/scores + conclusion + CTA.
- CTA default: *“For a deeper dive, check the link in the description.”*

### 2. Generate Jessica TTS audio

Use Venice `tts-elevenlabs-turbo-v2-5`, voice `Jessica`.

Target each segment's final audio to land between **14.5s and 15.0s** so it matches a full 15s Seedance clip. If natural TTS is shorter (e.g., 13.8s), slow it slightly (0.95×) and pad silence to 15.0s. If it is longer than 15s, speed it up only as much as necessary (max ~1.12×) or rewrite the script.

See `scripts/prepare_audio_segment.py` for the padding recipe.

### 3. Generate watercolor infographic slides

Use `gpt-image-2` via Venice with a prompt that requests:
- Watercolor professional infographic style
- Clean hierarchy, large readable text
- Soft medical/healthcare palette
- No photo-realistic faces

### 4. Generate hostess talking-head clips (Seedance R2V)

**Prompt template (pass to R2V):**

```text
Cinematic talking-head portrait of a poised, warm, professional woman hosting a healthcare podcast from a sleek modern broadcast desk. She looks directly at the viewer with a subtle, confident smile and speaks with slow, deliberate facial motion for clear lip-sync. Natural subtle head nods, gentle hand gestures, and expressive but controlled eyebrows. Soft studio lighting, shallow depth of field, high production value, photorealistic. Upper-body framing, steady locked-off camera, no text overlays, no logos, no extra people, no fast cuts. Calm, authoritative, approachable delivery. Premium podcast aesthetic.
```

**Negative prompt:**

```text
blurry face, distorted face, extra limbs, deformed hands, text, watermark, logo, harsh lighting, overexposed, underexposed, fast motion, shaky camera, multiple people, cartoon, anime, painting, oversaturated, hand over mouth, looking away from camera
```

**Directorial / viral tips baked into the prompt:**
- “Looks directly at the viewer” + “subtle, confident smile” → audience connection.
- “Slow, deliberate facial motion” → better lip-sync.
- “Subtle head nods, gentle hand gestures, expressive but controlled eyebrows” → natural, not robotic.
- “Soft studio lighting, shallow depth of field” → premium look.
- “Steady locked-off camera, no fast cuts” → stable, podcast-like framing.
- “Hand over mouth, looking away from camera” in negative prompt → keeps lips visible and on-camera.

### 5. Poll and download

Use `/api/v1/video/retrieve` in a loop every 30s until `video/mp4` is returned.

### 6. Assemble final split-screen video

Target: **1920×1080**, each panel **960×1080**.

```bash
ffmpeg -y -i host_video/seg1.mp4 -i slides/slide1.jpg -i audio/seg1.mp3 \
  -filter_complex "
    [0:v]tpad=stop_mode=clone:stop_duration=1,scale=960:1080:force_original_aspect_ratio=decrease,pad=960:1080:(ow-iw)/2:(oh-ih)/2,setsar=1[v0];
    [1:v]scale=960:1080:force_original_aspect_ratio=decrease,pad=960:1080:(ow-iw)/2:(oh-ih)/2,setsar=1[v1];
    [v0][v1]hstack=inputs=2[v]
  " -map "[v]" -map "2:a" -c:v libx264 -crf 23 -preset medium -c:a aac -b:a 192k -shortest -r 30 final/segment1.mp4
```

Repeat for segment 2, then concatenate with `concat` demuxer.

## Lip-Sync Best Practices

1. **Always request full 15s Seedance clips.** The model paces lip motion for the requested duration. Trimming a longer generated clip down causes subtle sync drift.
1. **Keep each Seedance clip ≤ 15s.** Longer clips require speeding audio, which degrades lip-sync.
2. **Prefer natural speech speed.** Do not force total duration to 30s; match video length to audio length.
3. **Request a Seedance duration that matches the audio length.** If the audio is ~13.8s, request a `14s` clip; if ~15.0s, request `15s`. Avoid asking for 15s and trimming later.
4. **If you must hit exactly 15s,** slow the TTS slightly (e.g., 0.95×) and pad with silence rather than trimming, then request the full `15s` from Seedance.
5. **Slower face motion = better sync.** Use directorial prompts like “slow, deliberate facial motion.”
6. **Use reference audio.** Seedance uses the provided audio for lip-sync; always include it.
7. **Use a clean reference image.** One high-quality portrait, front-facing or 3/4, neutral expression, good lighting.
8. **Avoid hand-over-mouth gestures and looking away from camera** in the prompt/negative prompt; they break lip visibility.
9. **If audio is slightly longer than the host clip,** extend the host clip with `tpad=stop_mode=clone` and trim with `-shortest` rather than looping the whole clip.

## Common Pitfalls

- **402 Payment Required** means Venice video credits are depleted. In that case, reuse existing host clips and re-mux with new audio; do not silently fail.
- **400 Unrecognized keys** → remove `guidance_scale`/`steps` from payload.
- **Audio drift** → always verify final video/audio stream durations with `ffprobe` and ensure they match within ~0.05s.
- **Slides unreadable** → generate slides at high resolution and scale down in FFmpeg; do not upscale low-res slides.

## Verification

After assembly, run:

```bash
ffprobe -v error -show_streams -of json final/openevidence_jessica_natural_final.mp4
```

Expected:
- Video stream: 1920×1080, ~30 fps.
- Audio stream: same duration as video (±0.05s).
- Total duration ~30s (two 15s segments).

## Example Queue Script Snippet

```python
import requests, yaml, base64
from pathlib import Path

with open(Path.home() / ".hermes/config.yaml") as f:
    cfg = yaml.safe_load(f)
api_key = cfg.get("api_key") or cfg.get("model", {}).get("api_key")
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

def data_url(path, mime):
    b64 = base64.b64encode(Path(path).read_bytes()).decode()
    return f"data:{mime};base64,{b64}"

payload = {
    "model": "seedance-2-0-enhanced-reference-to-video",
    "prompt": (
        "Cinematic talking-head portrait of a poised, warm, professional woman hosting a healthcare podcast..."
    ),
    "negative_prompt": (
        "blurry face, distorted face, extra limbs, deformed hands, text, watermark, logo, harsh lighting, ..."
    ),
    "duration": "15s",
    "resolution": "720p",
    "aspect_ratio": "3:4",
    "reference_image_urls": [data_url("~/.hermes/image_cache/aipharmaxchange_hostess_gpt_final.jpg", "image/jpeg")],
    "reference_audio_urls": [data_url("audio/seg1_jessica_speed1.12.mp3", "audio/mpeg")],
    "consents": {
        "seedance": {
            "confirmed_terms_and_privacy": True,
            "confirmed_legal_right": True,
            "confirmed_screening_acknowledged": True
        }
    }
}

r = requests.post("https://api.venice.ai/api/v1/video/queue", headers=headers, json=payload)
queue_id = r.json()["queue_id"]
```

## Variations

- **Different topic:** replace slide prompts and narration script; keep hostess/voice/layout.
- **Different voice:** generate voice samples first, let user pick, then update the `voice` parameter in TTS.
- **Different aspect ratio:** hostess panel can be `3:4` or `9:16`; final assembly still stacks side-by-side into 16:9.

## Reference Files

- `references/seedance-r2v-api.md` — validated Venice Seedance API schema, limits, error codes, and audio strategy.
- `scripts/prepare_audio_segment.py` — helper to slow/pad Jessica TTS audio so each clip is exactly 15s for Seedance.

## Changelog

- v1.0 — Initial skill based on OpenEvidence paper-summary run. Validated Seedance schema, duration/aspect-ratio limits, and lip-sync behavior.
- v1.1 — Refined lip-sync strategy: always request 15s Seedance clips, slow+pad short audio instead of trimming long clips, added canonical hostess image rule, added API reference and audio-prep script.
