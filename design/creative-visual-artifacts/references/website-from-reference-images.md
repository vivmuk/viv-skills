# Website from Reference Images

Use this workflow when the user provides one or more reference images of a website (or a detailed vision description) and asks to recreate it as a local HTML/CSS/JS front-end, optionally generating matching imagery via Venice API.

## When to use

- "Build this website" accompanied by screenshot(s) or image descriptions.
- "Replicate this landing page" with reference images.
- Any request that involves visual reference → code translation, especially with custom illustrations or hybrid art styles.

## Pre-flight checklist

1. **Capture reference details** immediately via vision or manual description. Record: layout structure (grid/flex, split layout, hero section), color palette (hex values or close approximations), typography (serif vs sans, approximate sizes, weights), component inventory (nav, cards, CTAs, quotes, illustrations), and any specific visual effects (glassmorphism, gradients, backdrop-filter, parallax).
2. **Lock style brief** if imagery needs generation. Research the exact aesthetic requested (e.g., "classical oil painting + digital risograph/shader hybrid"). Note keywords: Renaissance, oil-on-canvas, impasto, chiaroscuro, halftone dots, chromatic aberration, CRT scanlines, chromatic glow, etc. Save this as a reusable prompt template.
3. **Budget check** before any API calls. Set a hard ceiling (e.g., $5) and track every generation. Never spend beyond the limit.
4. **Decide image scope** — full hero illustration, background texture, individual icons, or all of the above? One high-quality hero image is usually better than many mediocre ones when budget is tight.

## Prompt template for hybrid classical + digital art style

### MASTER PROMPT: Classical-Digital Hybrid Aesthetic

Always begin with this structure, then fill bracketed sections:

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

### Specific Subject Prompts

**For Botanical/Human Hybrid Portraits:**
```
Classical oil painting portrait of a [SUBJECT] in profile, merged with botanical and hydroponic elements. [SKIN TONE] rendered with visible brush texture and impasto technique. [HAIR DESCRIPTION] filled with swirling organic curves resembling root systems. A vibrant [PLANT COLOR] plant with bright healthy leaves sprouts from [LOCATION]. 

Background: Faint technical grid lines, constellation-like dot-to-dot patterns, geometric schematics. [CELESTIAL ELEMENT] hovers behind the head. [ADDITIONAL ELEMENTS: hydroponic vessels, water channels, root systems visible].

Style fusion: Classical Renaissance oil painting technique + modern digital risograph texture + subtle chromatic aberration shader effects + halftone dot patterns in shadows + visible paper grain + distressed edges.
```

**For Surrealist Landscape/Sanctuary:**
```
Surrealist [WATERCOLOR / ENGRAVING] illustration of a [SETTING]. [ARCHITECTURAL ELEMENT] frames a distant vista of [LANDSCAPE ELEMENTS]. [CENTRAL CREATURE] rendered in intricate [BLUE-WHITE CROSSHATCHING / ENGRAVING-STYLE LINEWORK] stands among [VEGETATION]. 

Behind looms an enormous [TEXTURED CELESTIAL BODY] partially obscured by [CLOUDS]. Tiered [STONE/WOOD] structures and curving [WATER CHANNELS] wind through the scene. [PLANT DESCRIPTION] fills the foreground. 

Visible paper grain, fine line details, subtle overlay of [GRID LINES / CONSTELLATION SYMBOLS]. Classical [WATERCOLOR / ENGRAVING] techniques fused with modern digital [RISOGRAPH TEXTURE / CHROMATIC ABERRATION] + subtle holographic glow effects on water. [PALETTE DESCRIPTION].
```

**For Scientific/Botanical Studies:**
```
Classical scientific [19th-century botanical illustration / anatomical engraving] of [SUBJECT], [CROSS-SECTION / FULL VIEW] with [VISIBLE SYSTEM: root system, vascular network, nutrient transport]. Hand-drawn in the style of [Aristotle / Leonardo / naturalist journal] with fine [CROSSHATCHING / STIPPLING] technique on [CREAM AGED PAPER / PARCHMENT].

[TECHNICAL ELEMENTS: measurement annotations, leader lines, taxonomic labels, scale bars].

Subtle digital [CHROMATIC ABERRATION / SCAN LINES / DATA-MOSHING] artifacts along edges. Overlaid with faint [TECHNICAL GRID / HEXADECIMAL CODES / COORDINATE MARKERS]. Classical [ENGRAVING / WATERCOLOR] technique fused with modern digital [GLITCH DISTORTION / SHADER EFFECTS]. [COLOR PALETTE: navy, cream, lime, coral].
```

### Critical Success Factors

1. **Explicit technique naming**: Always say "classical oil painting," "Renaissance chiaroscuro," "19th-century engraving" — never just "artistic" or "beautiful"
2. **Percentage-weighted fusion**: Emphasize classical as foundation (60%) with digital as overlay (40%)
3. **Specific texture vocabulary**: 
   - Classical: impasto, crosshatching, stippling, glazing, scumbling, sfumato
   - Digital: halftone, moiré, chromatic aberration, pixel sorting, data moshing, scan lines, CRT phosphor, holographic sheen
4. **Surface quality details**: Visible paper grain, canvas texture, torn edges, registration marks, tape residue
5. **Color palette lock**: Always specify exact hex codes or color names for consistency across generations
6. **Mood keywords**: Scientific romanticism, sacred geometry, temporal layering, contemplative stillness, organic precision

### Proven keywords from working sessions
- `impasto technique`, `visible brushstrokes`, `chiaroscuro lighting`
- `halftone dot pattern`, `screen-printed texture`, `risograph overlay`
- `chromatic aberration`, `subtle digital glow`, `CRT scanline artifact`
- `faint geometric grid lines`, `constellation dot-connect patterns`, `technical schematics`

## Build workflow

1. **Create project directory** with subfolders: `images/`, `styles/`, `scripts/`.
2. **Generate HTML first** as semantic structure before styling. Use the reference to map sections: header, hero split, cards, quote, footer/values.
3. **Use CSS custom properties** for the locked palette. This makes iteration easy and keeps the design consistent.
4. **Use Google Fonts** for typography matching (Playfair Display + Inter is a proven pairing for editorial/natural-science aesthetics).
5. **Implement layout in this order:**
   - Fixed header with `backdrop-filter: blur()` for glassmorphism
   - Split hero (`display: flex`, 50/50 or 60/40)
   - Service cards with flex/grid, hover transforms, staggered animation
   - Quote block with decorative oversized quotation marks
   - Values section with minimal iconography
6. **Add JS last** — IntersectionObserver for scroll reveals, smooth scroll, header shadow on scroll. Keep it minimal.
7. **Embed generated image** with proper `alt` text describing the art style for accessibility.

## Responsive breakpoints

| Breakpoint | Layout change |
|------------|---------------|
| `1024px` | Split → stack; illustration becomes 50vh |
| `768px` | Header wraps; nav goes full-width; cards full-width |
| `480px` | Headline scales to `2rem`; padding reduces to `1.5rem` |

## Cost tracking ledger (example)

| Call | Model | Resolution | Steps | Est. Cost | Notes |
|------|-------|------------|-------|-----------|-------|
| Hero illustration | `flux-2-pro` | 1024x1024 | 40 | ~$0.08 | Single image, high quality |

**Budget discipline:** After each generation, check remaining budget. If < $0.50 remaining, switch to CSS/SVG approximations for secondary visuals rather than generating more images.

## Verification checklist

- [ ] HTML parses without unclosed tags
- [ ] All referenced files exist (`styles/main.css`, `scripts/main.js`, `images/hero.png`)
- [ ] CSS custom properties match locked palette
- [ ] Image `alt` text describes the art style
- [ ] Responsive breakpoints tested at 1024px and 768px
- [ ] No external dependencies beyond Google Fonts CDN
- [ ] `PROOF.md` or inline summary documents cost and fidelity

## Common pitfalls

- **Image generation divergence:** Venice may produce multiple elements when one was requested (e.g., two hydroponic vessels instead of one). Prompt more explicitly: "a SINGLE hydroponic vessel..." or accept the artistic variation.
- **Provider config mismatch:** If Venice API requires `provider: custom:venice` in config but code uses `provider: custom`, the key may not resolve. Always verify the exact provider string.
- **Grid lines vs. constellation lines:** "Technical grid lines" often renders as constellation/diagrammatic dot-connect patterns rather than orthogonal grids. Be explicit: "faint Cartesian grid lines" or "architectural blueprint grid."
- **Color accuracy:** "Lime green" may render as emerald in some areas. Specify hex ranges if exact color matching is critical.
- **Risograph texture location:** The texture may apply to background only, not the full image. Prompt: "uniform risograph halftone texture across entire composition."

## Reference session

This workflow was validated in a session producing an "Artisan Hydroponics" landing page (July 2026). The reference was a split-layout editorial site with classical botanical illustration. One `flux-2-pro` 1024x1024 image was generated at ~$0.08, leaving $4.92 budget for additional assets. The resulting build was 468KB total, fully self-contained except for Google Fonts.
