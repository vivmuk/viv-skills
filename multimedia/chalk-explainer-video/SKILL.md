---
description: Generate narrated professional watercolor explainer videos with first-frame/last-frame video interpolation, TTS voiceover, and background music. Use when the user asks to create an explainer video, whiteboard animation, educational video, or wants to turn a topic into a narrated visual explainer.
---

# Chalk — Explainer Video Generator

Generate professional narrated explainer videos from any topic using the Venice API.

## When to use

- User asks for an explainer video on a topic
- User wants a whiteboard-style or watercolor animation
- User wants to turn a lesson, concept, or presentation into a narrated video
- User mentions "progressive drawing", "hand-drawn animation", or "first frame / last frame"

## Prerequisites

- Venice API key (env `VENICE_API_KEY` or hermes config)
- ffmpeg + ffprobe installed
- Python 3 with `requests`

## Pipeline

```
Topic → Scene Planner (Chat API) → N scenes + 1 summary
         ↓
    Background Music (Venice Music API)
         ↓
    Per scene (parallel):
      ├── First Frame: title-only image (Grok Imagine Pro)
      ├── Last Frame: fully illustrated image (Grok Imagine Pro)
      ├── TTS Voiceover: narration (ElevenLabs)
      └── Video: first→last frame interpolation (Seedance 2.0)
         ↓
    Combine video + TTS + music (ffmpeg)
         ↓
    Concatenate → Final MP4
```

## Quick start

```bash
python3 scripts/chalk_v5.py "AI in Pharma" --output ./output
```

## How it works

### 1. Scene Planning

The chat model breaks the topic into N content scenes + 1 summary scene. Each scene gets:
- `title` — short title
- `narration` — 25-50 words explaining the concept (hook → explain → transition)
- `image_prompt` — all visual elements for the fully illustrated frame
- `video_prompt` — drawing order for the interpolation

The summary scene recaps all key points with a closing thought.

### 2. Frame Generation (per scene, parallel)

**First frame**: Clean surface with only the title in brand text color. Everything else blank.
**Last frame**: Same surface fully illustrated with all panels, icons, diagrams, and labels.

Both frames use identical `STYLE` and `PALETTE` strings for visual consistency.

### 3. Video Interpolation

Feed both frames to Seedance 2.0 (`image_url` = first, `end_image_url` = last). Seedance interpolates a 6-second progressive drawing animation. Fallback: Kling O3 Pro with first frame only.

### 4. TTS Voiceover

ElevenLabs Turbo v2.5 generates expressive narration per scene. Default voice: Charlotte.

### 5. Background Music

Venice Music API generates a subtle ambient bed, mixed at -20dB beneath the voiceover. Loops if needed, fades out in the last 2 seconds.

### 6. Assembly (ffmpeg)

Each scene's video is extended to match audio length (freeze last frame if needed), combined with TTS, then all clips are concatenated. Background music is mixed across the entire video.

## Configuration

All defaults can be overridden. See `references/config.md` for full reference.

### Models

| Component | Default | Alternatives |
|-----------|---------|-------------|
| Chat | `zai-org-glm-5-2` | Any Venice chat model |
| Image | `grok-imagine-image-quality` | `nano-banana-2`, `flux-2-pro` |
| Video | `seedance-2-0-image-to-video` | `kling-o3-pro-image-to-video` (fallback) |
| TTS | `tts-elevenlabs-turbo-v2-5` | `tts-xai-v1`, `tts-minimax-speech-02-hd` |
| Voice | `Charlotte` | See `references/voices.md` |

### Art Styles

| Style | Description |
|-------|-------------|
| `professional_watercolor` | Medical scientific, AIPharmaXChange palette (default) |
| `watercolor_whimsical` | Storybook, Studio Ghibli aesthetic |
| `chalkboard` | Chalk on dark slate |
| `whiteboard_marker` | Marker outlines with watercolor fills |

### AIPharmaXChange Brand Palette (default)

```
#F0E6D2 — cream beige (dominant base)
#E6E6D2 — soft sand
#E6DCC8 — tan
#E6DCD2 — warm beige
#BED2C8 — sage teal (accent, sparingly)
#F0E6DC — pale warm cream
#1B2A4A — navy blue (line art, icons, text)
#2C4A3E — dark teal (body text)
#B2541A — burnt orange (one accent element)
```

## Usage examples

```bash
# Default (professional watercolor, AIPharmaXChange palette)
python3 scripts/chalk_v5.py "AI in Pharma"

# Custom topic and output
python3 scripts/chalk_v5.py "How LLMs Work" --output ./my-video

# Programmatic
```

```python
from scripts.chalk_v5 import run_pipeline
video = run_pipeline(
    topic="AI in Pharma",
    output_dir="./output",
    num_scenes=6,
    style="professional_watercolor",
    voice="Charlotte",
    music=True
)
```

## Cost

~$2.50-3.50 per 6-scene video (Grok Imagine Pro 2K + Seedance 2.0 + ElevenLabs).

## Lessons learned

- First-frame + last-frame interpolation produces the most natural progressive drawing effect
- Grok Imagine Pro gives the best frame-to-frame style consistency
- Seedance 2.0 supports `image_url` + `end_image_url` but does NOT accept `aspect_ratio`
- Both frame prompts must share identical STYLE and PALETTE strings
- Background music at -20dB stays subtle beneath voiceover
- Always implement fallback to Kling O3 Pro if Seedance fails
- Read API key from hermes config via subprocess to avoid encoding issues

## Files

- `scripts/chalk_v5.py` — Full pipeline script
- `references/config.md` — Complete configuration reference
- `references/voices.md` — All available TTS voices by model
- `references/api-endpoints.md` — Venice API endpoints used
- `examples/sample-scenes.json` — Example scene plan output
