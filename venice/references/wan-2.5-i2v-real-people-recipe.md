# Wan 2.5 Image-to-Video: Real-People Music-Video Clips

Use `wan-2.5-preview-image-to-video` when you want to animate a still photo of real people while preserving the original backdrop, clothing, and overall face structure. This is the right choice over HappyHorse/R2V when the user asks for **Wan 2.1/2.5 I2V explicitly**, or when the scene is a landscape/landmark-heavy photo where the background matters as much as the subjects.

## Queue payload

```json
POST /api/v1/video/queue
{
  "model": "wan-2.5-preview-image-to-video",
  "prompt": "The two men in the image are lip-syncing and performing Backstreet Boys' 'I Want It That Way' in a 90s pop music video. Man on the left in light-blue striped polo sings with hand on heart. Man on the right in white graphic t-shirt with camera around neck joins in on harmony. Both sway gently to the beat. Bright, even key light on faces, soft golden glow, cinematic shallow depth of field, 4K.",
  "duration": "10s",
  "resolution": "720p",
  "image_url": "data:image/jpeg;base64,..."
}
```

## Field rules for Wan I2V

| Field | Required? | Notes |
|---|---|---|
| `model` | yes | `wan-2.5-preview-image-to-video` |
| `prompt` | yes | Describe the motion/performance, not the image content. Be explicit with verbs ("sing", "sway", "point", "hand on heart", "imaginary microphone"). |
| `image_url` | yes | Single data URL or public URL. Use `image_url`, **not** `reference_image_urls`. |
| `duration` | yes | String: `"5s"` or `"10s"`. For 20-second final videos, render multiple 10s clips and concatenate. |
| `resolution` | optional | `"720p"` is a good default; `"480p"`/`"1080p"` available depending on model. |
| `aspect_ratio` | **omit** | This model does **not** accept `aspect_ratio`; including it returns `400 {"aspect_ratio":["This model does not support aspect_ratio"]}`.

## Retrieval

Same async loop as other Venice video models:

```python
import requests, time

headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
payload = {"model": model, "queue_id": queue_id}

while True:
    r = requests.post("https://api.venice.ai/api/v1/video/retrieve",
                      headers=headers, json=payload, timeout=120)
    ct = r.headers.get("Content-Type", "")
    if ct.startswith("video/") or not ct.startswith("application/json"):
        open("wan_clip.mp4", "wb").write(r.content)
        break
    status = r.json()
    print(status)
    if status.get("status") in ("COMPLETED", "FAILED", "CANCELLED"):
        break
    time.sleep(10)
```

## Prompting lessons for real-people photos

- **Reference clothing/camera explicitly** in the prompt ("light-blue striped polo", "white graphic t-shirt", "camera hanging from neck"). Wan tends to preserve these details well, but naming them reduces drift.
- **Ask for strong performance verbs** if you want singing/dancing energy. Motion is still relatively subtle compared to R2V models, so prompts like "sings passionately", "hand on heart", "drapes arm around shoulder", and "points at camera" help.
- **Faces stay backlit by the original scene** — you cannot add artificial key light that wasn't in the photo. If the original faces are in harsh midday sun, expect harsh shadows under sunglasses/chins.
- **Sunglasses hide eyes** in the final video just like the source photo; emotional performance reads through mouth/body language, not eye contact.
- **Prompt for the actual song when the user names one**, but describe the performance/mood rather than quoting copyrighted lyrics. For example: "lip-syncing and performing Backstreet Boys' 'I Want It That Way' in a 90s pop music video" works; verbatim lyrics in the music prompt can trigger content-policy rejections.

## Polling with long-running background tasks

Wan 2.5 I2V takes ~2–2.5 minutes for a 10-second 720p clip. In this environment `process(action='wait')` is clamped to 60s, so a background generator script will time out. Use one of these patterns:

1. **Run in a terminal background process** with `notify_on_complete=True`, then poll the process status:
   ```bash
   terminal(background=True, notify_on_complete=True)
   ```
2. **Or run in foreground with a long `timeout`** and accept the blocking wait:
   ```bash
   timeout=600 python3 gen_wan_clip.py
   ```
3. **Or poll incrementally** after the 60s clamp times out:
   ```python
   process(action='poll')
   process(action='wait', timeout=600)  # repeats until completion
   ```

The retrieve loop should sleep at least 10 seconds between polls to avoid rate limits and should handle both `video/mp4` (raw bytes) and `application/json` with `"status": "COMPLETED"` plus `download_url`.

## Post-production

Wan I2V output includes its own ambient audio. Strip it before adding custom music/TTS:

```bash
ffmpeg -y -i wan_clip.mp4 -an -c:v copy wan_clip_muted.mp4
```

Normalize to 720p/30fps for clean concatenation:

```bash
ffmpeg -y -i wan_clip.mp4 -vf "fps=30,scale=1280:720:flags=lanczos,format=yuv420p" \
  -c:v libx264 -preset fast -crf 23 -an wan_clip_norm.mp4
```

Then concatenate multiple clips and add music:

```bash
printf "file 'wan_clip1_norm.mp4'\nfile 'wan_clip2_norm.mp4'\n" > clips.txt
ffmpeg -y -f concat -safe 0 -i clips.txt -c copy combined.mp4

ffmpeg -y -i combined.mp4 -i music_20s.mp3 -shortest \
  -c:v copy -c:a aac -b:a 192k final.mp4
```

## When to prefer Wan I2V vs HappyHorse vs Kling R2V

| Goal | Best model |
|---|---|
| User explicitly asks for Wan 2.1/2.5 I2V | `wan-2.5-preview-image-to-video` |
| Background/landmark must stay intact | Wan I2V |
| Strong singing/dancing motion, mic-holding | Kling O3 Pro R2V or HappyHorse (set expectations — motion may still be gentle) |
| Multiple people from separate photos combined | Kling/Grok R2V with face-crop elements |
| True face-likeness preservation with subtle motion | HappyHorse R2V or Kling O3 Pro R2V |
