# Kids' Educational Narrative Movie Workflow

A complete production recipe for turning a child in a source photo into the hero
of a 1–3 minute educational adventure movie using Venice AI image/video,
ElevenLabs TTS via Venice, and FFmpeg assembly.

## Project layout

```
ridhaan-dino-movie/
├── CLAUDE.md                  # Production rules for this specific project
├── project_state/
│   └── series.json            # Scene list, durations, summaries
├── scripts/
│   ├── script.md              # Full narration script
│   ├── storyboard_prompts.md  # gpt-image-2 prompts per scene
│   ├── popup_text.md          # Educational pop-up copy
│   └── model_selection.md     # Venice model picks + budget
├── assets/
│   ├── references/            # Character portrait, adventure pose, cutout
│   ├── storyboards/           # 16:9 PNG frames from gpt-image-2
│   └── compressed/            # JPEGs ≤150KB for video API
├── clips/                     # Wan I2V outputs
├── normalized/                # TTS narration segments
├── educational_cards/         # Pop-up PNGs
├── title_cards/               # Title + credits PNGs
├── final/                     # Assembled segments + final MP4
└── music/                     # Placeholder for future score
```

## Phase 1: Character extraction & reference images

1. Run vision analysis on the source photo to capture exact appearance.
2. Generate with `gpt-image-2`:
   - `ridhaan_portrait_cartoon_real.png` — painterly portrait, recognizable face
   - `ridhaan_adventure_pose.png` — full body in target world
   - `ridhaan_cutout.png` — transparent cutout (optional, for compositing)
   - `ridhaan_studio_portrait.png` — clean neutral backdrop
3. Compress all references to ≤150KB JPEG for API payloads.

## Phase 2: Storyboards & cards

Generate 16:9 storyboards with `gpt-image-2`:

```json
{
  "model": "gpt-image-2",
  "prompt": "Cinematic 16:9 storyboard frame. [scene description]. Style: photorealistic + soft cartoon hybrid, warm golden light, inspirational, child-friendly, high production value.",
  "aspect_ratio": "16:9",
  "resolution": "2K",
  "quality": "high"
}
```

Generate matching title / pop-up / credits cards at the same aspect ratio.

## Phase 3: Narration

Use `tts-elevenlabs-turbo-v2-5` with a warm voice (`Jessica` / `Matilda`):

```python
requests.post("https://api.venice.ai/api/v1/audio/speech", json={
    "model": "tts-elevenlabs-turbo-v2-5",
    "voice": "Jessica",
    "input": text,
    "response_format": "mp3",
    "speed": 1.0
})
```

Target ~25–30 words per 15 seconds for calm educational pacing.

## Phase 4: Video clips

Compress storyboards to 1920×1080 JPEG ≤150KB, then queue Wan I2V:

```python
payload = {
    "model": "wan-2.7-image-to-video",
    "prompt": "[motion description]. Slow cinematic motion, gentle, inspirational.",
    "duration": "10s",   # or 15s
    "resolution": "720p",
    "image_url": data_url(compressed_jpg)
}

r = requests.post("https://api.venice.ai/api/v1/video/queue", json=payload)
queue_id = r.json()["queue_id"]
```

Poll with `POST /video/retrieve` until `Content-Type == video/mp4`.

## Phase 5: FFmpeg assembly

### Per-scene base segment (loop clip + pad narration)

```bash
ffmpeg -y -stream_loop -1 -i clip.mp4 -i narr.mp3 \
  -filter_complex "[0:v]trim=0:TARGET,setpts=PTS-STARTPTS[v];[1:a]apad=pad_dur=TARGET[a]" \
  -map "[v]" -map "[a]" -t TARGET \
  -c:v libx264 -crf 23 -preset fast -c:a aac -b:a 192k -ar 48000 \
  seg_base.mp4
```

### Add overlays

```bash
ffmpeg -y -i seg_base.mp4 -loop 1 -i popup.png \
  -filter_complex "[1:v]scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p[over];[0:v][over]overlay=0:0:enable='between(t,START,END)'[v];[v]format=yuv420p[final]" \
  -map "[final]" -map 0:a -t TARGET \
  -c:v libx264 -crf 23 -preset fast -c:a copy \
  seg_final.mp4
```

### Concatenate

```bash
printf "file 'seg_s01_final.mp4'\nduration 12.0\nfile 'seg_s02_final.mp4'\nduration 18.0\n..." > concat.txt
ffmpeg -y -f concat -safe 0 -i concat.txt \
  -c:v libx264 -crf 23 -preset medium -c:a aac -b:a 192k -ar 48000 \
  final.mp4
```

## Phase 6: Deliverables

- Full-size MP4 (1280×720, ~40–45 MB)
- Telegram version: `ffmpeg -i final.mp4 -vf scale=960:-2 -crf 28 -c:a aac -b:a 128k`

## Pitfalls

- Don't request one long video clip; Wan I2V is limited per clip. Build the
  runtime by concatenating 10–15s clips.
- Pad narration with `apad=pad_dur=<target>` and enforce duration with `-t`.
- Do not escape commas in `between(t,0,4)` when passing args as a Python list.
- Scale overlay images to the output resolution and convert to yuv420p before
  overlaying.
- Venice `/audio/music` returned `404` in this session; generate music outside
  Venice or deliver narration-only.

## Cost estimate (2-minute movie)

| Item | Cost |
|---|---|
| 7 storyboard frames (gpt-image-2) | ~$0.50–$0.80 |
| 7 video clips (wan-2.7-i2v 10–15s) | ~$7–$9 |
| 7 narration segments (ElevenLabs) | ~$0.10 |
| Title / pop-up / credits cards | ~$0.30 |
| **Total** | **~$8–$10** |
