# Anti-Slop Checks — The Production-Test Playbook

Consolidated from production-tested LLM landing-page tests. Treat each box as a mechanical check. Bins of tells — the more boxes you tick, the more the page reads as default LLM output.

## Layout tells

### Hero

- [ ] Version label in hero (`v0.6`, `BETA`, `INVITE-ONLY`, `EARLY ACCESS`, `ALPHA`) without brief naming it
- [ ] Sub-eyebrow micro-meta line (`Marrow · No. 01 · The 6-quart`)
- [ ] Centered hero that forces scroll-to-find-CTA
- [ ] Hero top padding > `pt-24`
- [ ] Hero has > 4 text elements (eyebrow + tagline + headline + sub-text + CTAs + trust strip)
- [ ] `text-7xl` / `text-8xl` headline with > 6 words
- [ ] "Used by" / "Trusted by" logo wall *inside* the hero
- [ ] Decoration text strip at hero bottom (`BRAND. MOTION. SPATIAL.`, `ESTD. 2018 · LISBON · BRAND. MOTION. SPATIAL.`)
- [ ] Logo wall using plain-text wordmarks (`<span>Acme Co</span>`)

### Sections

- [ ] Eyebrow above every section heading (count `uppercase tracking`). Threshold: ceil(sectionCount / 3).
- [ ] `00 / INDEX`, `001 · Capabilities`, `06 · how it works` numbered section markers as default scaffolding
- [ ] `01 / 4` pagination on images or bento tiles
- [ ] `Scroll · 001 Capabilities` scroll cue prefix
- [ ] `Index of Work, 2018 - 2026` range eyebrow
- [ ] Three consecutive image+text-split sections (zigzag reflex)
- [ ] Two sections with the same layout family back-to-back
- [ ] Local storage / weather strip (`Lisbon 14:23 · 18°C`) without travel/place brief
- [ ] `border-t` + `border-b` on every row of long lists / spec tables

### Bento & cards

- [ ] 6 white-on-white bento cells with text only (no visual variety)
- [ ] Empty cells in middle/end of bento grid
- [ ] Three-equal feature cards (icon + heading + text, endlessly repeated)
- [ ] Same-sized cards with icon + heading + text in a flat row

### CTAs & form

- [ ] Two CTAs with the same intent (`Get in touch` + `Contact us` + `Let's talk`)
- [ ] CTA button text wraps to 2+ lines at desktop
- [ ] White-on-white button / `bg-white` CTA + `text-white`
- [ ] Ghost button over photographic bg with no backdrop
- [ ] Long-form label like `VIEW SELECTED WORK` instead of 1-2 word CTA
- [ ] Form labels below inputs (or no labels)
- [ ] Placeholder text muted-gray on tinted near-white (passes no contrast)

## Visual / CSS tells

- [ ] Gradient text (`background-clip: text` + gradient bg) for emphasis
- [ ] Side-stripe `border-left 4px` as colored accent on cards/callouts/alerts
- [ ] Glassmorphism as default (decorative blurs everywhere)
- [ ] `border: 1px solid X` + soft wide drop shadow on the same element (ghost-card)
- [ ] `border-radius: 32px+` on cards
- [ ] `repeating-linear-gradient` diagonal stripe backgrounds
- [ ] Decorative grid background (`linear-gradient(... 1px, transparent 1px)` grid overlay) without data viz context
- [ ] Hand-drawn / sketchy SVG: `feTurbulence`, `feDisplacementMap`, crude 5-30 path scenes
- [ ] Hand-rolled decorative SVG (when icons from Phosphor/HugeIcons/Radix/Tabler exist)
- [ ] Scoped `border-radius` mix — round buttons on square layout, square cards on pill-button page
- [ ] Pure black `#000000` for ink (use off-black zinc-950 / charcoal instead)
- [ ] AI purple / blue glow gradient on default CTAs
- [ ] Pull-quote horizontal rule of `---` between every paragraph

## Typography tells

- [ ] Fraunces or Instrument Serif as default (forbidden)
- [ ] Inter as a default for a new brand choice (forbidden)
- [ ] DM Sans / Plus Jakarta Sans / Outfit / Space Grotesk / Syne as default (forbidden)
- [ ] IBM Plex Mono / Space Mono / Geist Mono as decorative shorthand for "developer" (without the brand being technical)
- [ ] Display letter-spacing in -0.05 to -0.085em band (cramped)
- [ ] Italic word with descender (`y g j p q`) in `leading-[1]` or `leading-none`
- [ ] Single-family fallback page (deliberate single family is fine; reflex single family is not)
- [ ] All-caps body copy (caps reserved for short labels)
- [ ] Locale prefix in display type without brief being a place

## Color tells

- [ ] Cream / sand / warm-paper body bg for a non-warm brand
- [ ] Beige + brass + oxblood + espresso palette for premium-consumer brief that didn't name it
- [ ] Different accent colors mid-page (warm grey → blue CTA in section 7)
- [ ] Tinted neutrals not tuned to brand hue (default warm tinting on a cold brand)
- [ ] No semantic state vocabulary (no defined error/warning/success/info colors)
- [ ] Different grey temperature mid-page (cool grey sidebar + warm grey content)
- [ ] AI-purple / blue-violet glow gradients on CTAs

## Content / copy tells

- [ ] Em-dash (`—`) anywhere on the page
- [ ] En-dash (`–`) as separator (date ranges, number ranges) — use hyphen
- [ ] Generic names (`John Doe`, `Sarah Chan`, `Jack Su`)
- [ ] Generic avatars (SVG egg, Lucide user icon)
- [ ] Fake-perfect numbers (`99.99%`, `50%`, `1234567`)
- [ ] Startup-slop brand names (`Acme`, `Nexus`, `SmartFlow`, `Cloudly`)
- [ ] Filler verbs (`elevate`, `seamless`, `unleash`, `next-gen`, `revolutionize`)
- [ ] "Quietly in use at" / "Quietly trusted by" social-proof header
- [ ] "From the field" / "Field notes" / "Currently on the bench" poetic section labels
- [ ] Mock-humble industry reference in body copy ("We respect the French ones…")
- [ ] Filler tagline below CTAs (`Works with GitHub, GitLab, and self-hosted Git`)
- [ ] Pills/labels/tags overlaid on images (`Brand · 02`)
- [ ] Photo-credit captions as decoration (`Field study no. 12 · Ines Caetano`)
- [ ] Version footers (`v1.4.2`, `Build 0048`) on marketing pages
- [ ] Micro-meta-sentence under eyebrow (`Each of these is a feature we ship today…`)
- [ ] Scoring/progress bar with filled bg track on landing page
- [ ] Generic step labels (`Stage 1 / Stage 2 / Stage 3`)
- [ ] Faked stock counters (`Reservation 412 of 800`) without real data
- [ ] Decorative status dots before every nav / list row / badge
- [ ] `field notes · journal` / `PLATE · BRAND` style labels overlaid on images

## Imagery tells

- [ ] Zero images on a brief that implies imagery (restaurant / hotel / food / travel / fashion / photography)
- [ ] Div-based fake screenshot in hero (built from styled divs that simulate a UI)
- [ ] Hand-rolled decorative SVG instead of real assets
- [ ] Pure-text minimalism (`no images`) on a brief with imagery
- [ ] Logo wall with plain-text wordmarks (no real Simple Icons / devicon / generated SVG marks)

## Motion tells

- [ ] Animation on keyboard shortcuts / command palette (100+/day actions)
- [ ] `transition: all 300ms` (animates unintended off-GPU properties)
- [ ] `scale(0)` entrance (nothing appears from nothing)
- [ ] `ease-in` on any UI interaction
- [ ] Built-in `ease` / `linear` for a deliberate UI animation (use custom curves)
- [ ] UI duration > 300ms without justification
- [ ] `transform-origin: center` on trigger-anchored popover / dropdown / tooltip
- [ ] Keyframes on toasts / toggles / rapidly-triggered motion (use transitions or springs)
- [ ] Animating layout properties (`width`/`height`/`margin`/`padding`/`top`/`left`)
- [ ] Framer Motion `x`/`y`/`scale` shorthand (no hardware acceleration)
- [ ] CSS variable on parent driving child transform (recalc storm)
- [ ] Missing `@media (prefers-reduced-motion: reduce)` handling
- [ ] Hover transition not gated behind `@media (hover: hover) and (pointer: fine)`
- [ ] Symmetric enter/exit timing on a press-and-release / hold interaction
- [ ] `window.addEventListener('scroll')` (use ScrollTrigger / Motion `useScroll` / IntersectionObserver)
- [ ] `useEffect` animation with no cleanup
- [ ] Symmetric stagger on every section (uniform reflex applied to everything)
- [ ] Reveal animation that gates visibility on a class-triggered transition (fails on hidden tabs)

## Aesthetic-lane tells (second-order reflex)

- [ ] Editorial-typographic lane on a brief that isn't editorial
- [ ] Brutalist cargo-cult on a brief that isn't industrial
- [ ] Acid-maximalism lane without brand permission
- [ ] Stripe-minimal line-spacing as reflex, not deliberate
- [ ] Apple-Liquid Glass approximation labeled as if it were the real platform API

## Two reflex checks (mandatory)

Before shipping, run these in order:

1. **First-order**: if someone could guess the theme + palette from the category alone, it's the first training-data reflex. Rework the scene sentence and color strategy until the answer isn't obvious from the domain.
2. **Second-order**: if someone could guess the aesthetic family from category-plus-anti-references (`AI workflow tool that's not SaaS-cream → editorial-typographic`, `fintech that's not navy-and-gold → terminal-native dark mode`), it's the trap one tier deeper.

If both answers are not obvious, you can ship. Otherwise, rework.
