# Venice Video & Audio API Recipe

Copy-paste snippets and real response shapes from production use.

## HappyHorse 1.1 reference-to-video

```json
POST /api/v1/video/queue
{
  "model": "happyhorse-1-1-reference-to-video",
  "prompt": "TikTok viral dance video, the person in the reference dancing energetically...",
  "reference_image_urls": ["data:image/jpeg;base64,..."],
  "duration": "10s",
  "aspect_ratio": "16:9"
}
```

Response:
```json
{"model": "happyhorse-1-1-reference-to-video", "queue_id": "019f..."}
```

⚠️ **Field gotchas:**
- Use `reference_image_urls` (flat array of data URLs). `image_url` returns `400` with `"reference_image_urls required"`.
- `duration` must be a **string** such as `"5s"`, `"10s"`, `"15s"` — a number returns `400`.
- The queue response has `queue_id`, not `id`.
- Do not include `audio` boolean.
- Output includes ambient audio; strip it with `ffmpeg -an` before merging custom music or TTS.

## Poll / retrieve video

```python
import requests, time

headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
body = {"model": model, "queue_id": queue_id}

while True:
    r = requests.post("https://api.venice.ai/api/v1/video/retrieve",
                      headers=headers, json=body, timeout=120)
    if r.headers.get("Content-Type", "").startswith("video/"):
        open("output.mp4", "wb").write(r.content)
        break
    status = r.json()
    print(status)
    if status.get("status") in ("COMPLETED", "FAILED", "CANCELLED"):
        break
    time.sleep(10)
```

## Music generation via `/audio/queue`

```json
POST /api/v1/audio/queue
{
  "model": "elevenlabs-music",
  "prompt": "Upbeat emotional late-90s boy band pop ballad instrumental, bright and catchy, no vocals"
}
```

Response:
```json
{"model": "elevenlabs-music", "queue_id": "019f...", "status": "QUEUED"}
```

⚠️ **Do not** pass `duration`/`duration_seconds`/`duration` — `elevenlabs-music` rejects it with `Unrecognized key(s) in object: 'duration'`. Trim the downloaded MP3 afterward if needed.

## Poll / retrieve music

```python
import requests

body = {"model": "elevenlabs-music", "queue_id": queue_id}
r = requests.post("https://api.venice.ai/api/v1/audio/retrieve",
                  headers=headers, json=body, timeout=120)
# While processing this returns JSON; when ready it returns raw audio bytes.
if r.headers.get("Content-Type", "").startswith("audio/"):
    open("music.mp3", "wb").write(r.content)
else:
    print(r.json())
```

⚠️ `/audio/retrieve` **requires** `model` in the body and uses `queue_id`, not `id`. Omitting `model` returns `404 {"error":"Model is required"}`; using `id` returns `400 {"queue_id":"Required"}`.

## Common failures

| Error | Cause | Fix |
|---|---|---|
| `400` `"reference_image_urls required"` | Used `image_url` on HappyHorse R2V | Switch to `reference_image_urls[]` |
| `400` `"Expected '3s' \| '4s' \| ... received number"` | `duration` is an integer | Make it a string like `"10s"` |
| `404` `"Model is required"` on `/audio/retrieve` | Forgot `model` field | Add `"model": "elevenlabs-music"` |
| `400` `"Unrecognized key(s) in object: 'id'"` on `/audio/retrieve` | Used `id` instead of `queue_id` | Use `queue_id` |
| `400` `"Unrecognized key(s) in object: 'duration'"` on `/audio/queue` | Passed `duration` to `elevenlabs-music` | Omit `duration`; trim after download |
| `422` content policy on music | Prompt referenced a specific song | Describe style/mood generically |

## Concatenate clips and add music

```bash
printf "file 'clip1_norm.mp4'\nfile 'clip2_norm.mp4'\n" > clips.txt
ffmpeg -y -f concat -safe 0 -i clips.txt -c copy combined.mp4

ffmpeg -y -i combined.mp4 -i music.mp3 -shortest \
  -c:v copy -c:a aac -b:a 192k final.mp4
```

To force an exact duration when the music is longer than the video:
```bash
ffmpeg -y -i combined.mp4 -i music.mp3 -t 20 \
  -c:v copy -c:a aac -b:a 192k final.mp4
```
