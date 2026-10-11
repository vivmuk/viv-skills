---
name: branded-infographic
version: 0.1.0
description: How to generate branded infographics for AIPharmaXchange (org maps, cost breakdowns, agent inventories, model comparisons). Covers when to use the image model vs Pillow, the brand palette, aspect ratios, text-overlay policy, and the data-fidelity pitfall.
tags: [infographic, brand, image-gen, pillow, aipharma, paperclip, watercolor, branding]
triggers:
  - infographic
  - org chart
  - model map
  - cost breakdown
  - agent inventory
  - architecture diagram
  - brand illustration
  - 3:4 portrait
  - watercolor
  - teal mint navy cream
---

# Branded infographic workflow (AIPharmaXchange)

## When to use this skill

You need a visual artifact that combines the AIPharmaXchange brand
identity (watercolor, teal/mint/navy/cream palette, Avenir Next
Condensed typeface) with structured data (an org tree, a model
comparison, a cost table, an activity breakdown, a system inventory).
The artifact will be sent to a human reviewer (typically as a Telegram
photo and/or an attachment in an `Agni Agent Report` email).

## The single most important rule

**For data-heavy infographics, use Pillow. The image model is the
wrong tool.**

I have empirically verified this three times in June 2026 with
different model pairings:

| Approach | What it did well | What it failed at |
|---|---|---|
| `grok-imagine-image-quality` (single mega-prompt, 2:3 portrait) | Visual hierarchy of the org tree | Dropped 60% of data — 4/6 cost rows + entire monthly section + footer; text rendering garbled for unfamiliar model names |
| `gpt-image-2` (single mega-prompt, 2:3 portrait) | Cleaner visual style, all 7 script-agent names correct | **Fabricated** the model cost table — substituted its own knowledge (GPT-4o, Claude 3.5 Sonnet, Llama 3.1 405B) for the actual 6 models; dropped the monthly section entirely |
| **Pillow composite** (bg image as faint wash, data tables rendered as text) | Pixel-perfect data: all 6 cost rows, all 7 monthly rows, all 10 agent names, accurate callout and footer | The visual structure is less polished than gpt-image-2's output |

The pattern is clear: **image models substitute their training-data
priors for the specific numbers you give them in the prompt**. This
is unacceptable for any artifact where the data is the point — cost
reports, model inventories, agent maps, evaluation summaries, audit
findings. The Pillow version is canonical for those. Use the image
model for hero images and decorative illustrations where the data
isn't load-bearing.

## Workflow

### Step 1 — decide which renderer

| Infographic type | Renderer |
|---|---|
| Hero / cover image, decorative | Image model (`grok-imagine-image-quality`) |
| Title slide for a deck | Image model |
| Org tree visual only (no tables) | Image model — can do this with empty-box placeholders + clean tree |
| **Org tree + data tables (model costs, monthly costs, etc.)** | **Pillow** — the only reliable option |
| Quantitative report (numbers, ranks, percentages) | **Pillow** |
| Multi-panel comparison (before/after, A vs B) | Pillow (image model mangles labels) |

### Step 2 — Pillow infographic recipe

Use the proven template at
`/Users/vivgatesai/.paperclip/workspaces/aipharmaxchange/generate_infographic_full.py`
(370 KB, 864×1296, 2:3 portrait). Structure:

```python
W, H = 864, 1296
img = Image.new("RGB", (W, H), CREAM)

# 1. Soft watercolor wash (gradient between teal corners)
# 2. Subtle paper grain via PIL noise + Gaussian blur
# 3. Header (large title + subtitle + tagline + thin teal divider)
# 4. Org tree (3 tiers) with rounded boxes, badges, bus lines
# 5. Data tables (alternating cream/mint rows, teal section headers)
# 6. Total/callout row in solid teal
# 7. Footer in dedicated cream band at the bottom (not overlapping data)
```

Key Pillow settings:

- **Fonts**: Avenir Next Condensed is the brand font on macOS —
  `/System/Library/Fonts/Avenir Next Condensed.ttc` (note: actual
  path on current macOS is `/System/Library/Fonts/Avenir Next Condensed.ttc`,
  NOT `/System/Library/Fonts/Supplemental/` as older docs claim —
  the Supplemental path does not exist on current macOS).
  Fall back to Helvetica if not present. Always pass explicit
  `size=`, never rely on default.
- **Box rendering**: `draw.rounded_rectangle(xy, radius, fill, outline, width)`
  for boxes. `rounded_rectangle` is available in Pillow 8.2+.
- **Text positioning**: use `draw.textbbox((0,0), text, font=...)` to
  measure text width, then `(W - tw) // 2` for center alignment.
  `textlength` is also available.
- **Badges**: small rounded rect with text inside. Position top-LEFT
  of the box (top-right collides with the name in narrow boxes).
- **Bus lines**: vertical line outside the column of boxes (offset
  by ~30px), with horizontal connectors into each box. Drawing the
  bus through the boxes looks broken.
- **Footer band**: dedicated 60px cream rectangle at the bottom so
  the footer text doesn't overlap the data table's last row.

### Step 2b — Card grid recipe (3 columns × N rows)

For dense inventories (10–20 items: project lists, agent rosters,
feature inventories), the proven grid is **3 columns × 5 rows** at
848×1264 (2:3 portrait). Empirically validated June 2026 with a
15-project infographic (rated 9/10 by vision QA).

Dimensions and typography:

```
Canvas:      848 × 1264 (nano-banana-2 output is 848×1264 by default)
Header band: y=0..180  (navy bg, white title, teal subtitle, 4-stat row)
Footer band: y=H-70..H (navy bg, brand left, meta right)
Card grid:   pad=12, gap_x=8, gap_y=8 → card_w ≈ 268, card_h varies
Card layout: number badge top-left (ellipse, accent fill, white digit)
             name in 15pt bold navy at y+40
             2-line description in 12pt bold soft-navy, pinned to bottom
```

Text-fitting rule for ~268px-wide cards (10px padding each side →
~248px usable): at 12pt font, plan for **≤26 characters per line**.
Anything longer gets clipped or wraps awkwardly. Cut adjectives,
abbreviate aggressively (`end-to-end` → `to`, `configurations` →
`config`). Pin all description lines to the bottom of the card
(`desc_y_start = y + card_h - 40`) for visual consistency across
rows where some descriptions are 1 line and others are 2.

Card outline color: cycle through teal/mint/navy per card index
(`accent = [TEAL, MINT, NAVY][i % 3]`). Gives the grid rhythm without
needing semantic color coding.

### Step 2c — Pillow-overlay HYBRID (image model for visual frame + Pillow for text)

This is the **best of both worlds** and what to reach for when
(1) the data is too dense for pure image model, (2) you still want
a watercolor brand feel, and (3) you have DIEM budget for one
image-model call. Validated end-to-end June 2026:

```python
# 1. Call image model for the background — visual-only prompt, NO TEXT.
bg_prompt = (
    "Abstract watercolor poster background, 2:3 vertical portrait orientation. "
    "Soft painterly gradient: deep navy at top fading to teal and mint in the "
    "middle, then warm cream at the bottom. Subtle organic watercolor blooms in "
    "teal and mint scattered around the edges. Paper grain texture throughout. "
    "Faint hexagonal grid overlay. Several soft circular halos suggesting nodes. "
    "Generous open space in upper-center and middle-center for text overlay. "
    "Brand palette: teal #00D4AA, mint #8FD3B6, navy #1A1A2E, cream #FEFCF8. "
    "No text, no words, no letters, no logos, no watermarks."
)
# → POST /api/v1/image/generate  model=nano-banana-2  aspect_ratio="2:3"
# → ~14s, ~2.5MB PNG (848×1264), $0.10–0.19/image

# 2. Composite header/footer/content bands on the background.
#    Use semi-transparent overlay rectangles (alpha ≈235) so the bg
#    watercolor blooms still bleed through at the edges.
overlay = Image.new("RGBA", bg.size, (0,0,0,0))
od = ImageDraw.Draw(overlay)
od.rectangle([(0,0),(W,180)], fill=(26,26,46,235))           # header
od.rectangle([(0,H-70),(W,H)], fill=(26,26,46,235))          # footer
od.rectangle([(0,170),(W,H-60)], fill=(254,252,248,235))     # content safe-zone
bg = Image.alpha_composite(bg.convert("RGBA"), overlay).convert("RGB")

# 3. Render ALL text on top via Pillow (the data-heavy step).
#    Use the card-grid recipe from Step 2b.
draw = ImageDraw.Draw(bg)
# ... header text, card grid, footer text ...
bg.save("/tmp/infographic.png", "PNG", optimize=True)
```

**Why this works**:
- Image model handles the visual aesthetic (watercolor blooms,
  paper grain, hex grid, color palette) — its strength.
- Pillow handles 100% of the typography — its strength, and
  immune to the "fabrication" failure mode of pure image-model
  infographics.

**Which image model for the bg**: `nano-banana-2` is the sweet
spot. Fast (10–30s), cheap ($0.10–0.19), and despite the skill
catalog's "good for avatars/thumbnails" caveat, it produced a
fully usable 848×1264 background with hex grid, paper grain, and
cream center safe-zone for text. (Vision QA rated the bg 6.5/10
for suitability as an infographic background — cream center was
the load-bearing feature; the hex grid is subtle enough not to
compete with foreground content.) `flux-2-max` and
`grok-imagine-image-quality` also work but cost 2–3× more.

**Caveat — hex grid bleeds through**: a subtle hexagonal overlay
in the bg may visually echo chart elements in the foreground.
If your cards have grid-like content, either (a) generate the
bg with a flat wash prompt (no hex grid), or (b) increase the
content overlay panel alpha from 235 to 250 to suppress the
underlying grid.

### Step 3 — Image model recipe (hero/decorative only)

When the data isn't load-bearing, the image model can do well. Use
the brand palette and explicit text strings:

```
Vertical poster, 2:3 portrait, painterly watercolor with paper
grain texture, brand palette: teal #00D4AA, mint #8FD3B6, navy
#1A1A2E, cream #FEFCF8.

[exact text strings quoted in the prompt]
[layout description]
[brand mark]
```

Prompt packing for the 1500-char gateway cap:
- Section titles: 100 chars each max
- Key data points: count them; lose the ones you can't fit
- Layout: "upper third / middle / lower third" zones
- Color scheme: palette names, not hex codes in the rendered output
  (the model interprets hex codes as text to draw)

### Step 4 — visual review loop

After generation, use `vision_analyze` to check:
1. All text labels present and not obscured
2. No fabricated data (this is the #1 image-model failure mode)
3. No clipping at edges
4. Watermark bleed-through (if you used a bg image as wash, its
   wordmark may render through the foreground — drop the bg image
   if so)
5. Footer placement (must not overlap data rows)

Iterate until clean. Pillow iterations are cheap (~1 sec each);
image-model iterations are expensive (~20-300 sec + $0.03-0.36).

**Pitfall — `vision_analyze` OCR is unreliable below ~14pt.**
Empirically observed June 2026 on a 15-card infographic with 12pt
descriptions: vision consistently misread small-font glyphs.
Examples from one run:
- `vivmuk` → "vivmek" (u→e confusion)
- `open-design` → "open-4esign" (d→4)
- `5s PATCH + GET` → "5x PATCH = GET" (s→x, +→=)
- `OpenClaw` → "OpenClaw" (this one was correct by luck)
- `vivgatesai@gmail.com` → "vlog4heal@gmail.com" (multiple confusions)

**Rule**: use `vision_analyze` only for **layout QA** — clipping,
overlap, alignment, visual hierarchy, watermark bleed. **Trust
your code-written text** for content/correctness. Re-rendering
based on vision's OCR misreads will introduce real bugs.

If you need a content QA pass, render the text via Pillow to a
plain white background (no bg image), then vision will OCR it
much more reliably. Or just `read_file` the .py source to confirm
the strings before shipping.

## Brand spec

| Token | Value | Use |
|---|---|---|
| Teal (primary) | `#00D4AA` | Headlines, dividers, badges, total-row highlight |
| Mint (secondary) | `#8FD3B6` | Outlines, alternating row tint, callout boxes |
| Navy (text) | `#1A1A2E` | Body text, LLM-box fill |
| Cream (background) | `#FEFCF8` | Canvas background |
| Dark teal | `#009C7E` | Subtitle, secondary text |
| Light mint (alt row) | `#DCF0E8` | Table row striping |
| Warm cream (alt row) | `#FAF6EC` | Table row striping |

| Token | Value | Use |
|---|---|---|
| Aspect ratio (default) | 2:3 portrait (864×1296) | Tall infographic stacks |
| Aspect ratio (LinkedIn) | 3:4 portrait (864×1152) | Square-ish carousel slide |
| Aspect ratio (story) | 9:16 | Vertical story format |
| Aspect ratio (header) | 4:5 portrait | Newsletter cover image |
| Brand mark | `● AIPharmaXchange` | Footer right corner, no hex codes in wordmark |

## Files implementing this

- `~/.paperclip/workspaces/aipharmaxchange/generate_infographic_full.py`
  — Pillow template (the canonical one for data-heavy)
- `~/.paperclip/workspaces/aipharmaxchange/generate_org_map.py`
  — single-image-model org chart (less data, decorative)
- `~/.paperclip/workspaces/aipharmaxchange/generate_org_visual.py`
  — empty-box image-model output used as bg wash (then dropped in v2
  because the wordmark bled through)
- `~/.paperclip/workspaces/aipharmaxchange/generate_infographic_gpt_image_2.py`
  — the gpt-image-2 attempt, kept for the design reference

## See also

- `editorial-rigor` — for the text content of any critique slide
  (use this skill for the visual; use editorial-rigor for the
  language of the cards)
- `model-routing` — for the data of any model-comparison infographic
  (the per-agent assignments, the tier table, the cost numbers)
- `venice-api` — for the image model parameter constraints
  (grok-imagine rejects `cfg_scale`/`steps`/`style_preset`; gpt-image-2
  rejects `width`/`height`; gateway caps prompts at 1500 chars; the
  `images` vs `data[].b64_json` response format difference)
