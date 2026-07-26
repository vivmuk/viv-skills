# Session reference: Netrak non-human profile image fallback

## Context

User asked for a profile picture around the Sanskrit-inspired word `Netrak`, explicitly `Non human`, on Telegram.

## What happened

- `image_generate` was attempted first with a square prompt for a cosmic eye / Sanskrit sigil avatar.
- The tool failed because the provider was not configured: `FAL_KEY environment variable not set`.
- Local environment lacked common renderers/libraries:
  - `PIL` / Pillow: missing
  - ImageMagick / `magick` / `convert`: missing
  - `cairosvg`, `svgwrite`, `matplotlib`, `cv2`: missing
  - `numpy`: available
- Installing Pillow with `python3 -m pip install pillow` failed because the venv had no `pip` module.

## Useful workaround

Use `numpy` arrays plus Python standard-library PNG writing (`zlib`, `struct`) to create a deterministic 512×512 PNG. The successful design included:

- dark cosmic background + deterministic starfield
- concentric gold/blue mandala rings
- abstract eye-shaped ellipse with iris and pupil
- Devanagari-inspired central geometric strokes
- block-font `NETRAK` text
- vignette for circular profile cropping
- final verification with `file /tmp/netrak_profile.png` and `du -h`

## Notes for future use

- If exact Devanagari text is required, first find/install a Devanagari-capable font. `fc-match 'Noto Sans Devanagari'` may fall back to DejaVu Sans, which is not sufficient proof that the target font exists.
- When exact script rendering is not possible, say the glyphs are “script-inspired” rather than claiming exact Sanskrit/Devanagari text.
- Telegram delivery should use `MEDIA:/absolute/path/to.png`.
