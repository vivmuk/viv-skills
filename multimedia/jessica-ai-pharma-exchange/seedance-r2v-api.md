# Seedance R2V API Reference

Validated against Venice.ai on 2026-06-28.

## Endpoints

### Queue a video
```http
POST https://api.venice.ai/api/v1/video/queue
Authorization: Bearer <api_key>
Content-Type: application/json
```

### Retrieve a video
```http
POST https://api.venice.ai/api/v1/video/retrieve
Authorization: Bearer <api_key>
Content-Type: application/json

{"model": "seedance-2-0-enhanced-reference-to-video", "queue_id": "..."}
```

Response is `video/mp4` when ready. Otherwise JSON with `status`: `PROCESSING`, `COMPLETED`, `FAILED`, `CANCELLED`.

## Request body schema

| Field | Required | Allowed values / notes |
|-------|----------|------------------------|
| `model` | yes | `seedance-2-0-enhanced-reference-to-video` |
| `prompt` | yes | Visual/motion description. |
| `negative_prompt` | no | Strongly recommended for face quality. |
| `duration` | yes | `4s`, `5s`, `6s`, `7s`, `8s`, `9s`, `10s`, `11s`, `12s`, `13s`, `14s`, `15s` |
| `aspect_ratio` | yes | `21:9`, `16:9`, `4:3`, `1:1`, `3:4`, `9:16` |
| `resolution` | no | `720p` accepted. Omit if unsure. |
| `reference_image_urls` | no | Array of base64 `data:image/jpeg;base64,...` URLs. Required for consistent identity. |
| `reference_audio_urls` | no | Array of base64 `data:audio/mpeg;base64,...` URLs. Required for lip-sync. |
| `consents.seedance` | yes | `{confirmed_terms_and_privacy: true, confirmed_legal_right: true, confirmed_screening_acknowledged: true}` |

## Rejected fields

These produce HTTP 400 `unrecognized_keys`:
- `guidance_scale`
- `steps`

## Output characteristics

- Frame rate: 24 fps
- No embedded audio track
- Average generation time: ~5–6 minutes for 15s clips
- Output dimensions depend on aspect ratio (e.g., `3:4` yields ~834×1112)

## Error codes

| Status | Meaning | Action |
|--------|---------|--------|
| 400 | Invalid payload | Check schema, remove rejected keys, verify duration/aspect_ratio strings. |
| 401 | Unauthorized | Key invalid or missing prefix. Venice keys include the `VENICE_*_KEY_` prefix. |
| 402 | Insufficient balance | Venice credits depleted. Reuse existing host clips or add credits. |

## Audio/clip duration strategy

For best lip-sync, request the full 15s clip even when narration is shorter. Prepare audio as:

1. Generate natural-speed Jessica TTS.
2. If < 14.5s: slow to 0.95×, then pad silence to exactly 15.0s.
3. If 14.5–15.0s: pad silence to exactly 15.0s.
4. If > 15.0s: speed up to max 1.12×, or rewrite script.

Never pad to >15s and then truncate — it clips the final word and breaks sync.
