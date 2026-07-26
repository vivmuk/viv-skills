---
title: Classical-Digital Hybrid Web Design
name: classical-digital-hybrid-web-design
description: Generate and build websites combining classical fine art aesthetics (oil painting, watercolor, engraving) with modern digital effects (glitch, chromatic aberration, shaders, risograph) using Venice AI image generation. Under $5 budget per project.
tags: [web-design, image-generation, venice-ai, classical-art, digital-shaders, creative, front-end]
author: Autonomous Loop Agent
date: 2026-07-14
---

# Classical-Digital Hybrid Web Design

## Overview

This skill enables the creation of sophisticated, art-forward websites that blend classical fine art techniques (Renaissance oil painting, 19th-century botanical engravings, watercolor atmospherics) with modern digital effects (chromatic aberration, scan lines, risograph texture, holographic glow, data-moshing). All imagery is generated via Venice AI's `flux-2-pro` model, staying under a strict $5 budget per project.

**Proven track record:** Successfully built a 4-section, fully responsive landing page for "Artisan Hydroponics" with 4 Venice-generated images (total spend: ~$0.32 of $5.00).

---

## When to Use This Skill

- User provides reference images of an art-heavy, editorial, or luxury website
- The aesthetic combines hand-drawn/painted textures with digital UI elements
- User wants to generate custom illustrations rather than use stock photos
- Budget constraint is explicit ($3-$5 for all imagery)
- The target style is: scientific romanticism, vintage naturalist journals, surrealist botanical art, or classical-digital collage

---

## Phase 1: Analyze Reference Images

**Goal:** Extract every visual element from the provided reference images.

**Checklist:**

| Element | What to Extract |
|---------|----------------|
| Layout | Split ratios, grid systems, section flow |
| Colors | Exact hex codes (eyedrop if possible), palette mood |
| Typography | Serif/sans pairing, sizes, weights, tracking, italic emphasis |
| Components | Cards, buttons, nav, footers, glassmorphism overlays, metrics |
| Illustrations | Subject matter, style fusion, texture details, color palette |
| Animations | Scroll effects, parallax, reveals, counters, hover states |
| Spacing | Padding, margins, section heights, border radii |

**Output:** A structured markdown document mapping every reference element to an implementation plan.

---

## Phase 2: Lock the Style Brief

**The Master Prompt Template (copy-paste, replace bracketed sections):**

```
A [COMPOSITION DESCRIPTION] rendered in a deliberate hybrid of classical fine art techniques and modern digital artifact effects.

**Classical Layer (60%):**
- Primary medium: [Oil painting / Watercolor / Tempera / Fresco / Fine-line engraving]
- Brushwork: Visible impasto strokes, cross-hatching, stippling, or fluid watercolor washes
- Lighting: Renaissance chiaroscuro with dramatic light/dark contrast, or soft atmospheric diffusion
- Texture: Visible paper grain, canvas weave, or aged parchment surface
- Color application: Layered glazes, opaque highlights, transparent shadows
- Linework: Fine contour lines, hatching for shading, anatomical precision

**Digital Layer (40%):**
- Raster effects: Halftone dot patterns, screen-print moiré, risograph grain
- Signal decay: Chromatic aberration (red/cyan channel shift), scan lines, CRT phosphor glow
- Data artifacts: Pixel sorting, data moshing, block compression artifacts, hex code overlays
- Technical overlays: Faint engineering grid lines, coordinate markers, measurement annotations
- Holographic effects: Iridescent sheen on water/moisture, prismatic light refraction
- Modern interference: VHS tracking errors, subtle glitch distortions, corrupted text strings

**Surface Quality:**
- Mixed media collage aesthetic: torn paper edges, tape residue, registration marks
- Visible process layers: underdrawings showing through, pentimenti, painter's tape borders
- Tactile depth: Real paint thickness, paper embossing, screen-print ink texture

**Color Palette (Strict):**
- Deep navy blue (#1a2332)
- Warm cream/off-white (#f5f1e8)
- Bright lime green (#a8d65a)
- Coral/terracotta (#d4736a, #c45c3e)
- Burnt orange accents
- Rich emerald greens
- Prussian blue depths
- Ochre/sienna warm neutrals

**Mood & Atmosphere:**
- Scientific romanticism: 19th-century naturalist journal meets contemporary digital art
- Sacred geometry: Hidden mathematical patterns, golden ratio spirals, Fibonacci sequences
- Temporal layering: Ancient symbols + futuristic data streams coexisting
- Contemplative stillness: Measured, precise, yet organically alive
```

**Subject-Specific Prompt Branches:**

**For Botanical/Human Hybrid Portraits:**
```
Classical oil painting portrait of a [SUBJECT] in profile, merged with botanical and hydroponic elements.
[SKIN TONE] rendered with visible brush texture and impasto technique.
[HAIR DESCRIPTION] filled with swirling organic curves resembling root systems.
A vibrant [PLANT COLOR] plant with bright healthy leaves sprouts from [LOCATION].
Background: Faint technical grid lines, constellation-like dot-to-dot patterns, geometric schematics.
[CELESTIAL ELEMENT] hovers behind the head.
Style fusion: Classical Renaissance oil painting + modern digital risograph texture + subtle chromatic aberration + halftone dots + visible paper grain + distressed edges.
```

**For Surrealist Landscapes:**
```
Surrealist [WATERCOLOR / ENGRAVING] illustration of a [SETTING].
[ARCHITECTURAL ELEMENT] frames a distant vista of [LANDSCAPE ELEMENTS].
[CENTRAL CREATURE] rendered in intricate [BLUE-WHITE CROSSHATCHING / ENGRAVING-STYLE LINEWORK] among [VEGETATION].
Behind looms an enormous [TEXTURED CELESTIAL BODY] partially obscured by [CLOUDS].
Tiered [STONE/WOOD] structures and curving [WATER CHANNELS] wind through the scene.
Visible paper grain, fine line details, subtle overlay of [GRID LINES / CONSTELLATION SYMBOLS].
Classical [WATERCOLOR / ENGRAVING] + modern digital [RISOGRAPH / CHROMATIC ABERRATION] + holographic glow on water.
```

**For Scientific/Botanical Studies:**
```
Classical scientific [19th-century botanical illustration / anatomical engraving] of [SUBJECT],
[CROSS-SECTION / FULL VIEW] with [VISIBLE SYSTEM: root system, vascular network, nutrient transport].
Hand-drawn in the style of [Aristotle / Leonardo / naturalist journal] with fine [CROSSHATCHING / STIPPLING] on [CREAM AGED PAPER].
[TECHNICAL ELEMENTS: measurement annotations, leader lines, taxonomic labels, scale bars].
Subtle digital [CHROMATIC ABERRATION / SCAN LINES / DATA-MOSHING] artifacts along edges.
Overlaid with faint [TECHNICAL GRID / HEXADECIMAL CODES / COORDINATE MARKERS].
```

---

## Phase 3: Venice API Image Generation

**Tool:** `mcp_venice_venice_image_generate`
**Model:** `flux-2-pro` (proven reliable for this hybrid style)
**Dimensions:** 1024x1024 (default) or 1024x768 for wide compositions
**Steps:** 40 (higher quality, ~$0.08/image)
**Seed:** Always specify a seed for reproducibility in case of regeneration

**Budget Tracker:**

| Item | Estimated Cost | Running Total |
|------|---------------|---------------|
| 1024x1024, 40 steps, flux-2-pro | ~$0.08 | +$0.08 |
| 1024x768, 40 steps, flux-2-pro | ~$0.06 | +$0.06 |
| 1024x1024, 30 steps, flux-2-pro | ~$0.06 | +$0.06 |
| **Budget Ceiling** | **$5.00** | **Hard stop** |

**Rules:**
- Reject any generation that would push total over $5.00
- Save every generated image to project `images/` folder immediately
- Log Venice generation ID, prompt, and cost for every image
- If a generation fails, retry once with refined prompt; if still failing, stop and report
- Prefer 4-5 images max to stay well under budget (proven: 4 images = $0.32)

---

## Phase 4: Build the Front-End

**File Structure:**

```
project-name/
├── index.html
├── styles/
│   └── main.css
├── scripts/
│   └── main.js
└── images/
    ├── image-1.png
    ├── image-2.png
    └── ...
```

**CSS Architecture:**

```css
:root {
  --color-navy: #1a2332;
  --color-cream: #f5f1e8;
  --color-lime: #a8d65a;
  --color-coral: #d4736a;
  --font-serif: 'Playfair Display', Georgia, serif;
  --font-sans: 'Inter', -apple-system, sans-serif;
}
```

**Key CSS Techniques:**

| Effect | Implementation |
|--------|----------------|
| Frosted glass header | `backdrop-filter: blur(12px)` + semi-transparent bg |
| Glassmorphism cards | `backdrop-filter: blur(16px)` + white border + shadow |
| Split layout | `display: flex` with `flex: 1` children, `max-width: 50%` |
| Responsive stack | `flex-direction: column` at `max-width: 1024px` |
| Staggered card reveals | `IntersectionObserver` + CSS `transition-delay` per card index |
| Parallax | `scroll` event listener + `translateY` based on scroll progress |
| Animated counter | `setInterval` incrementing to target value over ~1s |
| Smooth scroll | `html { scroll-behavior: smooth; }` + JS `scrollIntoView` |
| Hover lifts | `transform: translateY(-3px)` + `box-shadow` transition |

**JavaScript Patterns:**

```js
// Intersection Observer for scroll reveals
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) entry.target.classList.add('active');
  });
}, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

// Parallax for background images
window.addEventListener('scroll', () => {
  const progress = (scrolled + viewportHeight - sectionTop) / (sectionHeight + viewportHeight);
  bgImage.style.transform = `translateY(${progress * 50 - 25}px) scale(1.1)`;
});

// Animated counter triggered by IntersectionObserver
const animateMetric = (element, target) => {
  let current = 0;
  const timer = setInterval(() => {
    current += target / 60;
    if (current >= target) { current = target; clearInterval(timer); }
    element.textContent = current.toFixed(1);
  }, 16);
};
```

**Google Fonts Pairing (proven):**
- `Playfair Display` (serif) for headlines and quotes
- `Inter` (sans-serif) for body, nav, buttons, labels

**Blending generated illustrations into page backgrounds:**

See `references/hero-image-blending.md` for the full three-layer technique (mask-image + mix-blend-mode + radial gradient overlay). This is the standard approach when AI-generated images have a solid background that doesn't match the page color exactly.

```css
.hero-bg-illustration {
    position: absolute;
    top: 0;
    right: -5%;
    width: 75%;
    height: 100%;
    z-index: 1;
    background-color: var(--page-cream); /* harmonize base */
}

.hero-bg-illustration img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    object-position: right 35%;
    /* Fade the image's own left edge so it dissolves into the page */
    -webkit-mask-image: linear-gradient(
        to right,
        transparent 0%,
        rgba(0,0,0,0.15) 25%,
        rgba(0,0,0,0.5) 40%,
        rgba(0,0,0,0.85) 52%,
        black 65%,
        black 100%
    );
    mask-image: linear-gradient(
        to right,
        transparent 0%,
        rgba(0,0,0,0.15) 25%,
        rgba(0,0,0,0.5) 40%,
        rgba(0,0,0,0.85) 52%,
        black 65%,
        black 100%
    );
}

/* Organic blend overlay on top for seamless integration */
.hero-blend-overlay {
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    z-index: 2;
    pointer-events: none;
    background: radial-gradient(
        ellipse 90% 110% at 45% 50%,
        var(--color-cream) 0%,
        var(--color-cream) 30%,
        rgba(245, 241, 232, 0.92) 40%,
        rgba(245, 241, 232, 0.6) 52%,
        rgba(245, 241, 232, 0.25) 62%,
        transparent 75%
    );
}
```

Key points:
- `mask-image` on the `img` itself (not a parent div) fades the actual pixel edge
- The container `background-color` matches the page so any transparent mask area shows page color, not checkerboard
- A radial gradient overlay on top provides a second, softer transition zone
- Combine both for a seamless organic blend rather than a straight vertical split

**Global hover shading effects:**

When the user asks for "hover effects that change shading across the site," apply a consistent set of micro-interactions:

| Element | Hover Effect | Implementation |
|---------|-------------|----------------|
| Hero section | Image brightens, grid texture intensifies | `.hero-section:hover img` + `.hero-section:hover .grid-overlay` |
| Service cards | Lift + glow + left accent border | `transform: translateY(-4px)`, `box-shadow: ...`, `::before` pseudo-element `scaleY` border |
| Section images | Darken overlay + image zoom | `::after` pseudo-element background transition + `transform: scale(1.04)` on image |
| Glass cards | Brighten + lift + border glow | `background`, `border-color`, `box-shadow` transitions |
| Header | Deepen background | `background: rgba(...)` transition on hover |
| Buttons | Shimmer sweep + color shift | `::before` with `linear-gradient` sweep, `left: -100%` → `left: 100%` |
| Text elements | Subtle color shift, text-shadow | `color` + `text-shadow` transitions |

Pattern: Apply the `transition` properties to the element, trigger the visual change on the parent/section hover. This creates a cohesive "shading shift" feeling when the user moves the cursor around the page rather than isolated per-element effects.

---

## Phase 5: Proof & Verification

**Required Checklist:**

- [ ] All images generated by Venice API, saved locally, properly embedded with `alt` text
- [ ] HTML validates as well-formed (no unclosed tags)
- [ ] CSS and JS have no syntax errors
- [ ] All file paths resolve correctly
- [ ] Responsive breakpoints tested at 1024px and 768px minimum
- [ ] Total spend logged and ≤ $5.00
- [ ] Side-by-side visual comparison against reference images (mental or screenshot)
- [ ] Style fidelity checklist: palette match, typography match, component match, layout match

**Output Artifacts:**
1. `index.html` — complete site
2. `styles/main.css` — all styles
3. `scripts/main.js` — interactions
4. `images/*.png` — generated assets
5. `PROOF.md` — cost ledger, fidelity checklist, reflection notes

---

## Phase 6: Reflection & Memory Update

**After every cycle, update:**

1. **Locked Style Brief** — if new prompt phrases worked better, add them
2. **Cost Ledger** — running total, per-image costs, remaining budget
3. **Generated Image Inventory** — filenames, Venice IDs, prompts used
4. **Source Tree** — current file list
5. **Reference Analysis Notes** — what was easy/hard to match
6. **Failure Log** — failed prompts, style mismatches, embedding issues, what to fix next

**Optimization Questions:**
- Which prompt phrases produced the best results? (Add to style brief)
- Which CSS techniques saved time vs. struggled? (Document)
- Any Venice API errors or cost surprises? (Log for next time)
- Did the layout match within tolerance? (If not, adjust grid/flex next cycle)

---

## Pitfalls & Troubleshooting

### Venice API generation gets interrupted

Occasionally the Venice API returns `Operation interrupted` during image generation. The fix is simply to retry the exact same call with the same prompt and seed. The generation usually succeeds on the second attempt. Budget impact: none — the interrupted call does not consume credits.

### Venice image cache location

Generated images are stored in the Hermes cache at `~/.hermes/cache/images/` with hashed filenames (e.g., `img_5df4257a440e.png`). They must be copied to the project's `images/` folder before they can be referenced by the HTML. Always verify the copy succeeded:

```bash
cp ~/.hermes/cache/images/img_*.png project/images/
ls -la project/images/
```

### Validate JS before declaring success

When incrementally building JavaScript, it's easy to declare the same `const` variable twice in the same scope (e.g., `const glassCard = ...` in two different places). Always validate syntax before finishing:

```bash
node --check scripts/main.js
```

If Node.js reports `SyntaxError: Identifier 'X' has already been declared`, rename the duplicate variable or merge the two blocks.

### Validate HTML structure

Use a simple Python parser to verify no unclosed tags before finishing:

```python
from html.parser import HTMLParser
class Validator(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
    def handle_starttag(self, tag, attrs):
        if tag not in {'meta', 'link', 'img', 'br', 'hr', 'input', 'source', 'area', 'base', 'col', 'embed', 'param', 'track', 'wbr'}:
            self.stack.append(tag)
    def handle_endtag(self, tag):
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
v = Validator()
v.feed(open('index.html').read())
assert not v.stack, f"Unclosed tags: {v.stack}"
print("✅ HTML valid")
```

### GitHub repository target verification

Before pushing to any repository, confirm the user's target account name. Do not assume the active `gh` login is the correct one. If the user says "commit to vivmuk, not vivgatesAI", respect that explicitly. Common failure modes:

- The `GITHUB_TOKEN` environment variable can override `gh` CLI auth. To use `gh` CLI's stored credentials, run: `unset GITHUB_TOKEN && gh auth status`
- SSH keys may be tied to a different account. Generate a new key if needed: `ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_<account>` and add the public key to the target GitHub account's SSH settings.
- If `gh repo create` fails with "Name already exists", the repo may already exist under the wrong account. Check with `gh repo list`.

### Delivery methods

The user may want files delivered via multiple channels. Default to GitHub (persistent, versioned, accessible). Offer email as secondary if SMTP credentials are available. For Telegram, send files directly as attachments. Always confirm the user's preferred delivery target before acting.

1. **Explicit technique naming** — say "classical oil painting," not "artistic"
2. **Percentage-weighted fusion** — 60% classical, 40% digital in prompts
3. **Specific texture vocabulary** — impasto, crosshatching, halftone, chromatic aberration
4. **Surface quality details** — paper grain, torn edges, registration marks
5. **Color palette lock** — always specify exact hex codes for consistency
6. **Budget discipline** — ~$0.08/image, 4-5 images max, hard stop at $5.00
7. **Responsive first** — build for desktop, then collapse to mobile at 1024px and 768px
8. **Semantic HTML** — proper `<section>`, `<article>`, `<blockquote>`, `<nav>` tags

---

## Example Project: Artisan Hydroponics

**Reference:** Two images (Artisan Hydroponics landing page + AUREA LABS hybrid aesthetic)
**Generated Images:** 4
**Total Spend:** ~$0.32
**Budget Used:** 6.4%
**Result:** 4-section responsive landing page with glassmorphism, parallax, scroll animations, animated counter

**Venice Generation IDs:**
- `dvIj1mTxFPv2QMqYYkI2dQxprNliE0BI` — hero-illustration.png (classical oil + botanical)
- `PHfsfDtofJ1MvHRYqC1QeATXJ8D6Lew9` — surrealist-sanctuary.png (watercolor + elephant + archway)
- `lb2uQWyRhnSPt0kedr1ts1dr9WGNn7j7` — botanical-study.png (engraving + glitch)
- `Ttsu_EsAGqXzcwcuQV-4iCnwG3MWAwEX` — hydroponic-towers.png (oil + technical grid)

---

## Stop Conditions

- **Success:** Site matches references, all images embedded, spend ≤ $5, proof green
- **Budget exhausted:** <$0.08 remaining (can't generate another image)
- **Iteration cap:** 4 cycles or 90 minutes elapsed
- **Blocked:** No safe work remains — report honestly with current best artifacts

---

*Skill version: 1.0*
*Created: 2026-07-14*
*Tool chain: Venice AI (flux-2-pro), vanilla HTML/CSS/JS, Google Fonts*
