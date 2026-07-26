---
name: avatar-logo-design
description: "Design and deliver profile pictures, avatars, logos, and symbolic non-human icons for messaging/social platforms."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [avatar, profile-picture, logo, icon, image-generation, social-media, telegram]
---

# Avatar & Logo Design

Use this skill when the user asks for a profile picture, avatar, app icon, social-media logo, symbolic mark, mascot-free/non-human identity image, or word-centered visual identity.

## Goals

- Produce an image file the user can use immediately, not just a prompt.
- Respect platform constraints: square composition, strong silhouette, legible at small sizes, minimal clutter.
- Honor identity constraints exactly: if the user says **non-human**, avoid human faces, bodies, portraits, hands, or anthropomorphic figures.
- For word/name-based avatars, make the text secondary unless legibility is explicitly required; profile pictures often crop small, so the symbol should carry the identity.

## Workflow

1. **Extract constraints**
   - Name/word to include.
   - Script/language requirements (e.g. Latin + Devanagari).
   - Human/non-human/animal restrictions.
   - Platform target (Telegram/Discord/GitHub/etc.) and size if specified.
   - Style cues: mystical, minimal, corporate, cyberpunk, sacred geometry, etc.

2. **Generate with the best available image tool**
   - Prefer `image_generate` for polished raster artwork when configured.
   - Use a square aspect ratio unless the user requests otherwise.
   - Prompt for: centered composition, high contrast, uncluttered background, circular-safe crop, no tiny details near edges.

3. **If AI image generation is unavailable, produce a deterministic fallback**
   - Do not stop at “image generation is not configured” if local drawing tools can create a usable icon.
   - Check for local capabilities (`Pillow`, `cairosvg`, `rsvg-convert`, `magick`, `matplotlib`, or raw PNG generation with `numpy` + `zlib`).
   - Create a clean vector-like/raster icon programmatically and deliver it as a PNG.
   - See `references/netrak-sigil-fallback.md` for a worked example using only `numpy` and Python’s standard library PNG writing.

4. **Deliver as media**
   - On Telegram, include `MEDIA:/absolute/path/to/file` so the image is sent natively.
   - Keep the final message concise: mention the concept and attach the file.

## Prompt Pattern

```text
Create a square profile picture/avatar centered around “[WORD]”.
Concept: [non-human symbolic object/sigil/emblem].
Style: [specific aesthetic], modern icon/logo quality, high contrast, crisp details, circular-safe composition.
Include “[WORD]” [tastefully/subtly/clearly] and optionally “[SCRIPT FORM]”.
Avoid: human face, human body, animal, photorealistic portrait, clutter, tiny unreadable text.
```

## Programmatic Fallback Design Tips

- Start with a dark or flat background and a strong central shape.
- Use radial symmetry, rings, glows, and simple geometric strokes for premium icon feel.
- Use deterministic random seeds for starfields/noise so outputs are reproducible.
- If font support for non-Latin scripts is missing, either:
  - use script-inspired geometric strokes, clearly labeling them as inspired rather than exact text, or
  - locate/install an appropriate font before rendering exact script.
- Export at 512×512 or 1024×1024 PNG.

## Verification

- Confirm the file exists and is a valid image (`file /path/to.png`).
- Confirm dimensions are square and profile-picture appropriate.
- Check that disallowed subjects (human/animal/etc.) were not introduced.
- If text/script is required, verify it is present or explicitly explain if the fallback uses inspired glyphs rather than exact font-rendered text.

## Pitfalls

- **Missing image provider key:** `image_generate` may fail with provider env errors such as `FAL_KEY environment variable not set`. Fall back to local rendering instead of ending the task.
- **Tiny text:** profile pictures crop and shrink; symbols survive better than detailed typography.
- **Non-human requests:** abstract eyes, mandalas, sigils, crystals, machines, planets, and emblems are safe; avoid humanoid robots unless the user allows human-like figures.
- **Telegram tables:** do not present design options in markdown tables on Telegram; use bullets.
