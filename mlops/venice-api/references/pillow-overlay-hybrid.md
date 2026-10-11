# Pillow Overlay Hybrid — Text-Reliable Infographics

Every Venice image model mangles body text in dense compositions. Verified across
`flux-2-max`, `gpt-image-2`, and `grok-imagine-image-quality`: even a 4-card
infographic with one body sentence per card comes back with garbled words
("poverthart", "ecurscore", "beacewan a ber tro nsemer a punitica"), and at
least one card dropped entirely.

`gpt-image-2` is the best of the three for text (and is the only one that
sometimes renders short titles correctly), but for anything with > 1 line of
body copy per card it's still unreliable. Pills, disclaimers, citations, and
multi-paragraph captions are all in the danger zone.

The workaround: use the image model ONLY for the visual layer (background,
color, watercolor wash, texture, decorative shapes), and composite all text
with PIL. This gives:

- 100% text reliability — every word is exactly what you wrote
- Brand fidelity — exact fonts, exact sizes, exact colors (no model deciding
  to render "5%" as "50%" or "0" as "O")
- The visual richness of a real image — soft watercolor washes, painterly
  textures, photographic backgrounds
- Deterministic output — same code = same image every time

## Pattern

1. **Generate the background** with the preferred SOTA image model
   (`grok-imagine-image-quality` per user preference). Prompt is a
   painterly, abstract, brand-aligned background with NO text. Aspect ratio
   matches the deliverable.
2. **Composite the text layer** with PIL/Pillow. Use system serif + sans
   fonts (NewYork + Helvetica on macOS) as stand-ins for Fraunces + Inter.
   Draw title, subtitle, cards (rounded rectangles with teal borders), and
   a small brand mark.
3. **Save** as PNG.

## Working template

See `scripts/pillow_infographic.py` in this skill — generates a 4:5
(1080x1350) infographic with a grok-generated background and Pillow-rendered
title, numbered cards, body copy, and brand mark. Reusable as the base for
carousel slides, hero images, and LinkedIn/blog graphics.

## When NOT to use this pattern

- Hero/photographic images where the IMAGE is the point (no text or just
  one short title)
- Avatars, illustrations, abstract art
- Anything where a single short text overlay is fine — gpt-image-2 handles
  that case adequately

## Fallback when image models are blocked

**Do NOT silently fall back to a fully Pillow-rendered version.** The user
prefers the painterly watercolor look from the image model even at the
cost of waiting. A flat Pillow mock with crisp cards and a procedural wash
is not an acceptable substitute — the user has explicitly rejected it
("I don't like this version") because it loses the painterly character
that defines the brand.

Correct procedure when all image models return 402 (DIEM spend limit) or
429 (rate limit):

1. **Read the failing key value from `~/.paperclip/instances/default/.env`**
   or `~/.config/himalaya/config.toml` (whatever the script was using).
2. **Report the full key** to the user so they can fix the spend limit at
   venice.ai → API Keys. Without the key value, the user has to dig it up
   themselves.
3. **Tell the user explicitly** that the deliverable is delayed until
   they top up DIEM. Do not produce a Pillow-only version on their behalf.
4. **Only if the user explicitly says "just give me something"** may you
   fall back to the Pillow-only path. Note this is a one-off concession
   and not the default.

The procedural Pillow wash (`ImageDraw.ellipse` + `ImageFilter.GaussianBlur`)
is still useful as a test fixture or in dev/sandbox runs where DIEM is
intentionally off, but it should never be the production path for a
content deliverable.
