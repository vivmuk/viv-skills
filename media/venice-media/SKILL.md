---
name: venice-media
description: "Generate images, speech, and experimental video via the Venice.ai API. For music, defer to the heartmula skill (open-source Suno-alike). Reads VENICE_API_KEY from env; never embeds a literal key in this file."
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [media, venice, image-generation, video, tts, speech, ai-generation]
    related_skills: [heartmula, gifs, branded-infographic]
---

# Venice.ai — Multimodal Generation Skill

## When to use

Trigger when the user wants AI-generated media via their Venice.ai account and the request fits one of the listed endpoints:

| Need | Endpoint | Endpoint path |
|---|---|---|
| Image (txt2img, img2img, upscale, edit) | `/api/v1/image/generate` | first-party |
| Speech (TTS) | `/api/v1/audio/speech` | first-party, beta |
| Video | `/api/v1/video/generate` | experimental; check quota + model availability |
| Music | _not a first-party Venice feature_ | use the `heartmula` skill instead |
| Chat / embeddings | `/api/v1/chat/completions`, `/api/v1/embeddings` | first-party (covered by main model config) |

> **Canonical reference:** https://github.com/veniceai/api-docs — read on demand for parameters, model IDs, and rate-limit notes; do **not** pin a curl-fetch of it into every call. (Olympus rule: chat-leaked API keys must be rotated — this skill does not embed any key.)

## Preflight

```bash
# 1. Confirm the key is present
test -n "$VENICE_API_KEY" || test -n "$OPENAI_API_KEY" || {
  echo "missing VENICE_API_KEY / OPENAI_API_KEY in env" >&2
  exit 1
}

# 2. Pick whichever alias is set
KEY="${VENICE_API_KEY:-$OPENAI_API_KEY}"
BASE="https://api.venice.ai/api/v1"

# 3. Quick liveness check
curl -fsS -H "Authorization: Bearer $KEY" "$BASE/models" \
  | python3 -c "import json,sys; print(len(json.load(sys.stdin).get('data',[])), 'available models')"
```

If `models` returns a list, Venice is reachable. If it 401s, the key is invalid → stop and tell the user to rotate at dashboard.venice.ai → Keys.

## Image generation

```bash
KEY="${VENICE_API_KEY:-$OPENAI_API_KEY}"
BASE="https://api.venice.ai/api/v1"

curl -fsS -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"model":"venice-sd35","prompt":"<your prompt>","width":1024,"height":1024,"steps":30}' \
  "$BASE/image/generate" \
  | python3 -c "import json,sys,base64; d=json.load(sys.stdin); open('/tmp/out.png','wb').write(base64.b64decode(d['images'][0]))"
```

Image models to try (list explicitly via `$BASE/models` and grep `type=="image"` for the latest set): `venice-sd35`, `fluently-xl`, `ideogram-v2`, `dall-e-3`-equivalent alts. Always pick from the live model list, not a hardcoded catalog.

## Speech (TTS)

```bash
curl -fsS -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"model":"tts-kokoro","input":"Hello, world.","voice":"af_bell","format":"mp3"}' \
  "$BASE/audio/speech" \
  --output /tmp/out.mp3
```

## Video (experimental)

Before committing to a render, list available video models first — endpoint surface area changes frequently:

```bash
curl -fsS -H "Authorization: Bearer $KEY" "$BASE/models" \
  | python3 -c "import json,sys; [print(m['id']) for m in json.load(sys.stdin)['data'] if 'video' in m.get('type','')]"
```

Then submit a generation job, poll for status, and download the resulting URL — exact flow is in the live api-docs repo. If no video models show up on your tier, do **not** paper over with image sequences; tell the user video is unavailable on their plan.

## Music

Venice doesn't ship a music-gen endpoint. Hand off:

```bash
# Tell the user to use the heartmula skill, or your own songsee / Suno pipeline.
echo "[venice-media] Music gen is out of scope for Venice; routing to 'heartmula' skill."
```

Common false-positive triggers (skip):

- User asks to "make a song" → heartmula.
- User wants a logo / infographic → `branded-infographic`.
- User wants an animated GIF from existing footage → `gifs` skill.

## Cost / quota awareness

Venice bills per endpoint. The daily Venice spend ledger on this workstation is at `/tmp/aipharmaxchange_spend/spend_YYYY-MM-DD.json` (daily $10 cap per stored memory). Don't blindly burn budget on speculative renders — confirm the user wants the call before firing.

## Output handling

| Artifact | Default path | Convention |
|---|---|---|
| Image | `/tmp/out.png` or `MEDIA:/abs/path/to/img` if returning to chat | Telegram renders inline |
| Audio (TTS) | `/tmp/out.mp3` | Send via `MEDIA:` reference for native voice bubble |
| Video | `/tmp/out.mp4` | Same as image; obey platform size caps |

When replying to a user, prefer `MEDIA:/abs/path/to/file` over base64-in-message so Telegram / Discord render natively.

## Failure modes

| Symptom | Likely cause | Fix |
|---|---|---|
| 401 Unauthorized | Key missing/rotated | Re-export `VENICE_API_KEY`; if rotation needed, dashboard.venice.ai |
| 402 Payment required | Tier doesn't include endpoint | Tell user, switch to a cheaper/available endpoint |
| 429 Too Many Requests | Quota exceeded | Back off, retry with jitter, or switch endpoint |
| `models` empty | Wrong base URL or apex domain | Make sure `$BASE` = `https://api.venice.ai/api/v1`, not `venice.ai/api/v1` (no https) |
| TTS audio is silent/garbled | Wrong voice code | Run `$BASE/models` and grep `type=="audio"` |

## Pitfalls

- **Never** write the literal `VENICE_API_KEY=…` value into this file or any git-tracked path — the env alias is the contract.
- **Never** re-fetch api-docs on every call. Read it once per session when the endpoint surface seems to have shifted; cache the parts you need in the running conversation.
- If the user gives you a fresh Venice key in chat, treat it as Olympus-leaked: save it via the secure path (chmod-600 file + Railway env var), then advise rotation.
