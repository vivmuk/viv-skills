# Configuration Reference

## Models

| Parameter | Default | Description |
|-----------|---------|-------------|
| `CHAT_MODEL` | `zai-org-glm-5-2` | Chat completions model for scene planning |
| `IMAGE_MODEL` | `grok-imagine-image-quality` | Image model for first/last frames |
| `VIDEO_MODEL` | `seedance-2-0-image-to-video` | Video model for frame interpolation |
| `VIDEO_FALLBACK` | `kling-o3-pro-image-to-video` | Fallback if Seedance fails |
| `TTS_MODEL` | `tts-elevenlabs-turbo-v2-5` | TTS model for narration |
| `TTS_VOICE` | `Charlotte` | Voice for narration |

## Video Settings

| Parameter | Default | Options |
|-----------|---------|---------|
| `CLIP_DURATION` | `6s` | `3s`, `4s`, `5s`, `6s`, `8s`, `10s` |
| `IMAGE_RESOLUTION` | `2K` | `1K`, `2K`, `4K` |
| `ASPECT_RATIO` | `16:9` | `16:9`, `9:16`, `1:1` |
| `NUM_SCENES` | `6` | 3-10 recommended |
| `MUSIC_VOLUME_DB` | `-20` | -15 to -30 recommended |
| `FPS` | `24` | Output framerate |

## Art Styles

### professional_watercolor (default)
Medical scientific aesthetic, AIPharmaXChange palette, navy line art, controlled watercolor washes.

### watercolor_whimsical
Storyboard art style, soft flowing watercolor, Studio Ghibli meets Beatrix Potter.

### chalkboard
White/colored chalk on dark slate, dusty chalk texture, hand-drawn chalk handwriting.

### whiteboard_marker
Bold black marker outlines on white whiteboard, watercolor fills inside marker outlines.

## Custom Brand Palette

Replace the palette string with your brand colors:

```python
PALETTE = (
    "Use ONLY this color palette: "
    "#YOUR_BASE hex (dominant base), "
    "#ACCENT hex (accent, sparingly), "
    "#LINE_ART hex (all line art, icons, text), "
    "#BODY_TEXT hex (body text)"
)
```

## AIPharmaXChange Palette

```
#F0E6D2 — cream beige (dominant base, warm parchment)
#E6E6D2 — soft sand
#E6DCC8 — tan
#E6DCD2 — warm beige
#BED2C8 — sage teal (accent, sparingly)
#F0E6DC — pale warm cream
#1B2A4A — navy blue (line art, icons, arrows, text)
#2C4A3E — dark teal (body text)
#B2541A — burnt orange (one accent element)
```
