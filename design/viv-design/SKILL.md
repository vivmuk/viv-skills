---
name: viv-design
description: 'Use when designing, building, scaffolding, reviewing, auditing, critiquing, polishing, or shipping any frontend surface - website, landing page, web app, dashboard, admin panel, settings, onboarding, empty state, portfolio, brand site, marketing page, blog, editorial, or design system. Also use when the user asks for a redesign, asks to make something "more premium" / "more Linear-style" / "more Awwwards," or asks to fix the animations, typography, colors, layout hierarchy, motion, or remove AI-tells from an LLM-generated UI. Invoke explicitly as `viv-design <sub-command> [target]` where sub-command is one of craft / shape / audit / polish / critique / animate / typeset / layout / colorize / clarify / bolder / quieter / distill / harden / onboard / adapt / optimize / extract / document / init. Not for backend-only work, non-UI tasks, or copy-only edits with no visual surface.'
version: 1.0.0
author: Viv (Hermes Agent, packaged for Vivek M)
license: MIT
metadata:
  hermes:
    tags: [design, frontend, ui, ux, animation, motion, typography, color, anti-slop, brand, product, accessibility, redesign, oklch]
    related_skills: [claude-design, popular-web-designs, sketch, brandkit]
    category: creative
---

# Viv Design — Frontend Craft Doctrine

## Overview

`viv-design` is the unified frontend craft skill for Hermes. It packages three high-craft upstream sources into one coherent doctrine and is loaded automatically whenever the deliverable is a visible UI surface.

**Sources (resyncable from upstream):**
- `github.com/emilkowalski/skills` — animations.dev philosophy, animation decision framework, motion vocabulary, brutal animation review standards
- `github.com/pbakaus/impeccable` v3.9 — register-aware frontend craft (brand vs product), anti-AI-slop bans, codex-defects, commands (craft/shape/audit/polish/...), scene-sentence register pick
- `github.com/Leonxlnx/taste-skill` (`design-taste-frontend`) — brief inference, three dials (VARIANCE / MOTION / DENSITY), brief-to-design-system map, AI-tells production-tested tells

The skill distills these into a single front door (brief inference → dials → register), a color-typography-layout-motion core, a register-aware anti-slop playbook, and a verifiable preflight checklist. Detailed citable values live in `references/` so SKILL.md stays skim-able.

## When to Use

**Load automatically:**
- Building, scaffolding, or shipping any frontend surface (website, landing, app, dashboard, component, form, onboarding, empty state, marketing page, blog, portfolio).
- User asks for a redesign or visual refresh, with or without naming a system ("more Linear-style", "more premium", "more Awwwards").
- User asks to fix or improve typography, color, layout hierarchy, spacing, motion, micro-interactions.
- User pastes LLM-generated UI that "looks like AI made it" and wants the tells removed.
- Critiquing, polishing, auditing, or reviewing someone else's frontend work.
- Pairing real working code with committed design choices on production-grade surfaces.

**Don't load — use `viv-app-build` instead for:**
- **New application builds** (full-stack apps, mobile apps, dashboards, SaaS, internal tools, MVPs, prototypes). `viv-app-build` runs `grilling` interview first, then chains into this skill for the UI portion.
- Any "build me an app," "develop X," "ship X," "scaffold X," "create an app for Y" request.

**Don't load at all:**
- Backend-only, CLI, infra, or no-visible-UI work.
- Pure copywriting with no visual surface.
- Bug fixes that don't change the design.
- "Make a button look better" without a surrounding surface and audience.

**When in doubt:**
- App / project / scaffold / ship language → `viv-app-build` first.
- Surface / design / audit / polish / fix language → `viv-design` directly.

It is cheaper to skim a doctrine than to ship a generic frontend.

## App-Build Workflow (when triggered from `viv-app-build`)

If this skill loaded because `viv-app-build` routed an app-build request here, the workflow has already been:

1. **Grilling interview** — user-confirmed shared understanding (per `grilling`).
2. **Grilling recap** — 3-5 bullet brief in the conversation.

Continue from there:

3. Apply the three-step front door below.
4. Apply the doctrine (color → typography → layout → motion).
5. Run the preflight checklist.
6. Output reviews with the before/after table format.

**If grilling has NOT yet happened (this skill loaded without `viv-app-build`),** note this and either invoke grilling first or ask the user to confirm before coding. Application-build requests without grilling drift into "build what the agent assumes," which is the failure mode this workflow exists to prevent.

## The Three-Step Front Door

Before any code or styling, run these three steps in order. They are the highest-leverage moves and are easy to skip under time pressure. Don't skip them.

### 1. Brief inference — write the "design read" in one line

Read the brief. Output a single line before generating anything:

```
Reading this as: <page kind|genre> for <audience>, with <vibe words> language,
   leaning toward <design-system or aesthetic family>.
```

Examples:
- `Reading this as: B2B SaaS landing for technical buyers, minimalist-Restrained register, leaning toward Tailwind v4 utilities + Geist + restrained motion.`
- `Reading this as: solo designer portfolio for hiring managers, editorial-typographic language, leaning toward native CSS + scroll-driven animation + custom typographic details.`
- `Reading this as: redesign of a public-sector service site, trust-first register, leaning toward GOV.UK Frontend or USWDS.`

If the brief is genuinely ambiguous on a load-bearing aesthetic choice, ask **one** clarifying question. Otherwise declare the read and proceed.

### 2. Three Dials — set global variables

After the design read, pick dial values from the inference table. These are global variables every later decision (layout, motion, density) is gated by.

| Dial | What it controls | Range |
|---|---|---|
| `DESIGN_VARIANCE` | How off-axis / art-directed the layout is | 1=Perfect Symmetry ... 10=Artsy Chaos |
| `MOTION_INTENSITY` | How much / how orchestrated the motion is | 1=Static ... 10=Cinematic / Physics |
| `VISUAL_DENSITY` | How packed / how much data per viewport | 1=Art Gallery / Airy ... 10=Cockpit / Packed |

**Baseline:** `8 / 6 / 4`. Use unless the design read overrides.

| Brief reads as… | VARIANCE | MOTION | DENSITY |
|---|---|---|---|
| minimalist / clean / calm / editorial / Linear-style | 5–6 | 3–4 | 2–3 |
| premium consumer / Apple-y / luxury | 7–8 | 5–7 | 3–4 |
| playful / wild / Dribbble / Awwwards / experimental | 9–10 | 8–10 | 3–4 |
| landing page / portfolio / marketing site (default) | 7–9 | 6–8 | 3–5 |
| trust-first / public-sector / accessibility-critical | 3–4 | 2–3 | 4–5 |
| redesign — preserve | match existing | +1 | match existing |
| redesign — overhaul | +2 | +2 | match existing |

Do not ask the user to edit these. Override conversationally.

### 3. Pick the register (brand vs product)

This is the single most important call. The two registers have different default aesthetics, different motion rules, and different anti-pattern checks.

| Signal | Pick |
|---|---|
| Brand site, landing page, marketing, campaign, portfolio, long-form, about page, event | **BRAND** (design IS the product) |
| App UI, dashboard, admin, settings, data table, tool, authenticated surface | **PRODUCT** (design SERVES the product) |
| Ambiguous: ask once OR pick by what the surface in focus is | — |

Then load the register reference:
- BRAND → `references/brand-register.md`
- PRODUCT → `references/product-register.md`

Each register has its own typography rules, color strategy permission, motion budget, layout defaults, ban list, and slop test.

## Color

### Use OKLCH throughout

Tint uniformly toward the brand's own hue. Don't default-tint toward warm or cool "because the brand feels that way" — that is the cross-project monoculture move.

### Pick a color strategy before picking colors

| Strategy | Where it fits | Mechanics |
|---|---|---|
| **Restrained** | Tinted neutrals + one accent ≤10%. Product default; restraint brands. | Use liberally. |
| **Committed** | One saturated color carries 30–60% of the surface. Default for identity-driven brands. | Commit, don't hedge with neutrals at the edges. |
| **Full palette** | 3–4 named roles, each used deliberately. Brand campaigns, data viz. | Name every role. |
| **Drenched** | The surface IS the color. Brand heroes, campaign pages. | Pick the drenched color deliberately. |

### Anti-cream monoculture guard (mandatory)

The cream/sand/beige body bg is the saturated AI default of 2026. The whole warm-neutral band (OKLCH L 0.84–0.97, C < 0.06, hue 40–100) reads as cream/sand/paper/parchment regardless of token name. `paper`, `cream`, `sand`, `bone`, `flour`, `linen`, `parchment`, `wheat`, `biscuit`, `ivory` are tells in themselves.

For warm briefs, DO NOT default-tint the body bg. Pick one of:
- (a) a saturated brand color as the body (terracotta, oxblood, deep ochre, near-black)
- (b) a true off-white at chroma 0 (or chroma toward the brand's own hue)
- (c) a darker mid-tone tinted neutral that's clearly the brand's own

"Warmth" in the brand is carried by accent + typography + imagery, not by body bg.

### Premium-consumer palette rotation

Premium-consumer briefs (cookware, wellness, artisan, luxury, DTC home) have a banned default: warm-beige + brass + oxblood + espresso. Banned hex families as backgrounds: `#f5f1ea`, `#f7f5f1`, `#fbf8f1`, `#efeae0`, `#ece6db`, `#faf7f1`, `#e8dfcb`. Default alternatives (rotate between projects):
- Cold luxury: silver-grey + chrome + smoke
- Forest: deep green + bone + amber
- Black + tan: true off-black + warm tan, sharp contrast, no beige
- Cobalt + cream: saturated blue against single neutral
- Terracotta + slate: warm rust against cool grey
- Olive + brick + paper
- Pure monochrome + single saturated pop

If your last premium-consumer project used beige + brass, this one MUST use a different family.

### Lila rule

"AI purple / blue glow" is discouraged as a default. No automatic purple button glows, no random neon gradients. Use neutral bases (Zinc / Slate / Stone) with high-contrast singular accents (Emerald, Electric Blue, Deep Rose, Burnt Orange, etc.). Override only when the brief explicitly names purple/violet/lila.

### Contrast (mandatory)

- Body text ≥ 4.5:1 against background. Large text (≥18px or bold ≥14px) ≥ 3:1. **Placeholder text needs the same 4.5:1**, not muted-gray default.
- Gray text on colored backgrounds looks washed out. Use a darker shade of the background's own hue, or a transparency of the text color.
- Audit every CTA: button text WCAG AA min against button background. White button + white text, `bg-white` CTA + `text-white`, ghost button over photo with no backdrop → all banned.

## Typography

### Brand registers: distinctive

See `references/brand-register.md` for the full font-selection procedure. Headline:

1. Write three concrete brand-voice words. Not "modern" or "elegant" — "warm and mechanical and opinionated," "calm and clinical and careful."
2. List the reflex fonts you'd reach for. If any appear in the reject list, dismiss them.
3. Browse a real catalog with the three words in mind. Find the font for the brand as a physical object.
4. Cross-check. "Elegant" is not necessarily serif. "Technical" is not necessarily sans. "Warm" is not Fraunces.

**Reflex-reject fonts (training-data defaults, ban list for new design choices):**
- Fraunces · Newsreader · Lora · Crimson · Playfair Display · Cormorant / Cormorant Garamond · Syne · IBM Plex Mono / Sans / Serif · Space Mono / Grotesk · Inter · DM Sans / DM Serif Display / DM Serif Text · Outfit · Plus Jakarta Sans · Instrument Sans / Instrument Serif

The reflex-reject list applies to **new design choices**. Identity preservation wins for variants on an existing surface — don't second-guess what's already shipping.

### Product registers: familiar but tuned

See `references/product-register.md`. Headline:

- One family often right. A well-tuned sans carries headings, buttons, labels, body, data.
- Fixed rem scale (not fluid `clamp()`). Users view at consistent DPI; a fluid h1 that shrinks in a sidebar looks worse.
- Tighter ratio: 1.125–1.2 between steps. More type elements here; exaggerated contrast creates noise.
- Line length still applies (65–75ch prose). Data tables can run denser.

### Hard typographic ceilings (apply both registers)

- **Display letter-spacing floor: ≥ -0.04em.** Anything tighter (especially in the default -0.05 to -0.085em range) makes letters touch; reads as cramped. -0.02 to -0.03em is plenty for tight grotesque display; -0.04em is the floor.
- **Hero / display heading ceiling: `clamp()` max ≤ 6rem (~96px).** Above that the page is shouting, not designing.
- **Cap body line length:** 65–75ch.
- Use `text-wrap: balance` on h1–h3 for even line lengths; `text-wrap: pretty` on long prose to reduce orphans.
- Display `leading-[1]` or `leading-none` will clip italic descenders on `y g j p q`. Use `leading-[1.1]` minimum + `pb-1` or `mb-1` reserve on the wrapping element.

## Layout

### Spacing rhythm

- Vary spacing deliberately. Generous separations, tight groupings.
- Cards are the lazy answer. Use them only when they're truly the best affordance. **Nested cards are always wrong.**
- Flexbox for 1D, Grid for 2D. Don't default to Grid when `flex-wrap` would be simpler.
- For responsive grids without breakpoints: `repeat(auto-fit, minmax(280px, 1fr))`.

### Z-index

Build a semantic scale: `dropdown → sticky → modal-backdrop → modal → toast → tooltip`. Never arbitrary values like 999 or 9999.

### Hero discipline (mandatory)

A broken hero is the #1 reason LLM landing pages fail preflight. All of these are mandatory:

- **Hero fits the initial viewport.** Headline ≤ 2 lines at desktop. Subtext ≤ 20 words AND ≤ 4 lines. CTAs visible without scroll.
- **Hero top padding ≤ `pt-24` (≈6rem) at desktop.** More than that and the hero floats halfway down the viewport = layout bug. Increase font scale or asset size instead.
- **Hero text stack max 4 elements:** eyebrow OR brand strip (pick zero or one) → headline → subtext → CTAs (1 primary + max 1 secondary).
- **Banned in the hero:** tiny taglines below CTAs ("Works with GitHub, GitLab…"), trust micro-strips, pricing teasers, feature bullets, social-proof avatar rows. All of those move to dedicated sections below the hero.
- **Hero font-scale discipline.** Plan font size and image size together. If the asset is large and the headline is more than 6 words, do NOT start at `text-7xl/text-8xl`. Default hero scale: `text-4xl md:text-5xl lg:text-6xl`. `text-6xl md:text-7xl` only when the headline is 3–5 words.
- **"Used by" / logo wall lives UNDER the hero, never inside it.**

### Section discipline

- **Eyebrow cap: max 1 eyebrow per 3 sections** (hero counts as 1). A page with 9 sections may use at most 3 eyebrows total. An eyebrow on every section is AI scaffolding.
- **Section-Layout-Repetition** ban. Once you use a layout family (3-column-image-cards, full-width-quote, split-text-image), that family can appear at most ONCE on the page. 8 sections → at least 4 different layout families.
- **Zigzag alternation cap.** Max 2 consecutive image+text-split sections. The 3rd consecutive = preflight fail.
- **Bento background diversity.** At least 2–3 cells in any multi-cell grid need real visual variation (real image, brand-appropriate gradient, tinted bg). A cream-on-cream bento with only typography inside reads as boring AI default.
- **Bento cell count rule.** N items → N cells, no empty cells in the middle or end. Re-shape the grid; do not paste a blank tile.

### Popovers, modals, tooltips

- Popovers/dropdowns/tooltips MUST scale from their trigger (`transform-origin`), not center. Use `var(--radix-popover-content-transform-origin)` or equivalent.
- Dropdowns rendered with `position: absolute` inside an `overflow: hidden / auto` container will be clipped. Use native `<dialog>` / popover API, `position: fixed`, or a portal.
- Modals are exempt from origin-aware scaling — they stay centered.

## Motion Doctrine (Emil Kowalski + review-animations)

This is the highest-leverage section. A single bad animation ships broken UI. The full citable values (curves, durations, springs, gestures) live in `references/animation-rules.md`. The vocabulary ("what's it called when…") lives in `references/animation-vocabulary.md`. Load them whenever a finding needs a precise value.

### The animation decision framework — answer in this order, every time

**1. Should this animate at all?**

| Frequency | Decision |
|---|---|
| 100+ times/day (keyboard shortcuts, command palette toggle) | No animation. Ever. |
| Tens of times/day (hover effects, list navigation) | Remove or drastically reduce |
| Occasional (modals, drawers, toasts) | Standard animation |
| Rare / first-time (onboarding, feedback, celebrations) | Can add delight |

**Never animate keyboard-initiated actions.** They repeat hundreds of times daily; animation makes them feel slow, delayed, and disconnected. Raycast has no open/close animation. That is optimal for something used hundreds of times a day.

**2. What is the purpose?**

Valid: spatial consistency, state indication, explanation, feedback, preventing a jarring change. Invalid: "it looks cool" on a frequently-seen element.

**3. Easing — pick a curve**

Decision order:
- Entering / exiting → `ease-out` (starts fast, feels responsive)
- Moving / morphing on screen → `ease-in-out` (natural acceleration/deceleration)
- Hover / color change → `ease`
- Constant motion (marquee, progress) → `linear`
- Default → `ease-out`

**Never `ease-in` on UI.** It starts slow, delaying the exact moment the user is watching. `ease-out` at 200ms *feels* faster than `ease-in` at 200ms.

**Critical: use custom curves.** Built-in CSS easings are too weak.

```css
--ease-out:    cubic-bezier(0.23, 1, 0.32, 1);   /* strong ease-out for UI */
--ease-in-out: cubic-bezier(0.77, 0, 0.175, 1);   /* strong ease-in-out for on-screen movement */
--ease-drawer: cubic-bezier(0.32, 0.72, 0, 1);    /* iOS-like drawer (Ionic) */
```

Find more at easing.dev or easings.co — don't hand-roll from scratch.

**4. Duration**

| Element | Duration |
|---|---|
| Button press feedback | 100–160ms |
| Tooltips, small popovers | 125–200ms |
| Dropdowns, selects | 150–250ms |
| Modals, drawers | 200–500ms |
| Marketing / explanatory | can be longer |

**Rule: UI animations stay under 300ms.** A 180ms dropdown feels more responsive than a 400ms one. Faster spinners make load feel faster (same actual time).

### The ten non-negotiable animation standards

Every animation in the diff is measured against these. Violation = finding.

1. **Justified motion** — every animation must answer "why does this animate?" with one of: spatial consistency / state indication / feedback / explanation / preventing a jarring change.
2. **Frequency-appropriate** — match motion to how often it's seen. Keyboard and 100+/day actions get no animation.
3. **Responsive easing** — entering/exiting → `ease-out` or a strong custom curve. `ease-in` on UI = block. Built-in easings too weak.
4. **Sub-300ms UI** — UI animations stay under 300ms; anything slower needs justification.
5. **Origin & physical correctness** — popovers scale from their trigger (`transform-origin`), not center. Never `scale(0)` — start `scale(0.9–0.97)` + opacity. Modals exempt.
6. **Interruptibility** — rapidly-triggered or gesture-driven motion must be interruptible. CSS transitions / springs retarget from current state. Keyframes restart from zero.
7. **GPU-only properties** — animate `transform` and `opacity` only. Animating `width` / `height` / `margin` / `padding` / `top` / `left` is a performance finding.
8. **Accessibility** — `prefers-reduced-motion` honored (gentler, not zero — keep opacity/color, drop movement). Hover motion gated behind `@media (hover: hover) and (pointer: fine)`.
9. **Asymmetric enter/exit** — deliberate actions (press, hold, destructive confirm) animate slower; system responses snap. Symmetric timing on press-and-release or hold = finding.
10. **Cohesion** — motion matches the component's personality and the rest of the product. Mismatched personality or jarring crossfade where subtle blur would bridge = finding. When unsure whether motion feels right, the strongest move is often to delete it.

### Reduced motion (mandatory, never optional)

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
    /* keep opacity / color transitions, drop movement */
  }
}
```

A serious motion surface keeps opacity/color changes under reduced-motion; it does not silently remove all transitions.

## Anti-Slop Playbook (the most-failed section)

If you ship code that matches any of these, the user (or a reviewer) will see it as default LLM output and the page fails the slop test before it loads. Match-and-refuse: rewrite with different structure.

### Shared absolute bans (both registers)

- **Side-stripe borders.** `border-left` / `border-right` > 1px as colored accent on cards, list items, callouts, alerts. Never intentional. Rewrite with full borders, background tints, leading numbers/icons, or nothing.
- **Gradient text.** `background-clip: text` + gradient bg. Decorative, never meaningful. Use a single solid color. Emphasis via weight or size.
- **Glassmorphism as default.** Blurs + glass cards decoratively. Rare and purposeful, or nothing.
- **The hero-metric template.** Big number + small label + supporting stats + gradient accent. SaaS cliché.
- **Identical card grids.** Same-sized cards with icon + heading + text, repeated endlessly.
- **Tiny uppercase tracked eyebrow above every section.** The 2023 kicker is the saturated AI scaffold. One named kicker as deliberate brand system = voice; eyebrow on every section = AI grammar.
- **Numbered section markers as default scaffolding (01 / 02 / 03).** `01 · About / 02 · Process / 03 · Pricing` above every section is the eyebrow trope one tier deeper. Numbers earn their place when the section IS a sequence.
- **Text that overflows its container.** Long heading + large clamp + narrow grid = overflow. Test every breakpoint. Reduce clamp or rewrite copy.
- **Em-dash (`—`) as a stylistic crutch.** **Banned outright.** No exceptions in headlines, eyebrows, pills, body copy, quotes, attribution, captions, button text, alt text. Em-dash is the #1 visual Tell in production tests. Use periods, commas, line breaks, hyphens. The only permitted dash characters: regular hyphen (`-`) and minus in math.
- **No `window.addEventListener('scroll')`** — use Motion `useScroll()` / ScrollTrigger / IntersectionObserver / CSS scroll-driven animations only.

### Codex-specific defects (refuse-and-rewrite)

- **`border: 1px solid` + `box-shadow: 0 Npx Mpx` with M ≥ 16px** on the same element. The "ghost-card" pattern. Pick one: solid border at brand color, OR defined shadow ≤ 8px blur, never both as decoration.
- **`border-radius: 32px+`** on cards / sections / inputs. Cards top out at 12–16px; full-pill for tags/buttons. Picking 24/28/32/40px on a card = codex tell.
- **Hand-drawn / sketchy SVG illustrations.** `loose-sketch`, `*-sketch`, `doodle`, `wavy`; `feTurbulence` / `feDisplacementMap` filters; 5-to-30 path crude scenes (otter, table-and-fork, album cover). Amateurish. If you can't render with real assets, ship no illustration.
- **`repeating-linear-gradient(...)` stripe backgrounds.** Diagonal stripes in `body:before` / section backgrounds. Pure codex decoration.
- **Decorative grid backgrounds.** Two-axis CSS grid overlays from `linear-gradient(... 1px, transparent 1px)`. Codex tell unless the surface is an actual canvas/map/blueprint.

### Production-test LLM tells (banned outright)

**Hero & top-of-page**
- No `v0.6 / BETA / INVITE-ONLY / EARLY ACCESS / ALPHA` version labels in hero unless brief is explicitly a launch.
- No `Brand · No. 01`-style micro-meta sub-eyebrows.

**Section labels & micro-meta**
- No `00 / INDEX / 001 · Capabilities / 06 · how it works` section-number eyebrows. Eyebrows name the topic in plain language.
- No `01 / 4`-style pagination on images or bento tiles.
- No `Scroll · 001 Capabilities`-style scroll cues.
- No `Index of Work, 2018 - 2026`-style range labels as eyebrows.

**Separators & dots**
- The middle-dot (`·`) rationed to max 1 per line in metadata strips. Don't use as default separator for everything.
- No decorative colored status dots on every list / nav / badge / before every row.
- No repeated section-numbering or section-lettering as AI scaffolding.

**Em-dash & typography flourishes**
- Em-dash (`—`) and en-dash-as-separator (`–`) banned everywhere. Use periods, commas, hyphens. (See absolute bans above.)

**Marketing-copy Tells**
- No generic names. No "John Doe", "Sarah Chan" — use creative, realistic, locale-appropriate names.
- No fake-perfect numbers (`99.99%`, `50%`, `1234567`). Use organic, messy data (`47.2%`, `+1 (312) 847‑1928`).
- No startup-slop brand names (`Acme`, `Nexus`, `SmartFlow`, `Cloudly`).
- No filler verbs: `elevate`, `seamless`, `unleash`, `next-gen`, `revolutionize`.
- No "Quietly in use at" / "Quietly trusted by" social-proof headers.
- No "From the field" / "Field notes" / "Currently on the bench" poetic labels.
- No micro-meta-sentences under eyebrows ("Each of these is a feature we ship today…").

**Pills & overlays**
- No pills/labels/tags overlaid on images. (`Brand · 02`, `PLATE · BRAND`.)
- No photo-credit captions as decoration.
- No version footers on marketing pages (`v1.4.2`, `Build 0048`).
- No faked stock-count counters (`Reservation 412 of 800`) without real data.

**Decoration text strips**
- No decoration text strip at hero bottom (`BRAND. MOTION. SPATIAL.`, `TYPE / FORM / MOTION`, `ESTD. 2018 · LISBON · BRAND. MOTION. SPATIAL.`). Only acceptable when the strip carries real navigable links or real status info.

**Lists, dividers, scoring**
- No `border-t` + `border-b` on every row of a long list / spec table. Pick one, sparsely.
- No scoring/progress bars with filled background tracks on landing pages.

**Locale / time / scroll cues**
- No locale strips (`Lisbon, working with founders`, `LIS 14:23 · 18°C`) unless the brief is genuinely a place-focused or globally-distributed studio.
- No scroll cues (the user knows what scroll is).

### Aesthetic-lane check (mandatory second-order reflex)

Before committing, name the aesthetic family explicitly. If the brief lands in a currently-saturated lane (editorial-typographic display serif + small mono labels + ruled separators; or brutalist-utility; or acid-maximalism; etc.) without a register reason that requires it, that's a tell one tier deeper than picking Fraunces reflexively.

In one sentence, describe what you're about to build the way a competitor would describe theirs. If that sentence fits the modal landing page in the category, restart.

### Brand and product slop tests

**Brand slop test:** If someone could look at this interface and say "AI made that" without hesitation, it's failed. The bar is distinctiveness.

**Product slop test:** Would a user fluent in the category's best tools (Linear / Figma / Notion / Raycast / Stripe) sit down and trust this interface, or pause at every subtly-off component? The product failure mode is strangeness without purpose, not flatness.

## Sub-commands (Sub-Routing)

When the user invokes `viv-design <command> [target]`, treat the command as the focus lens and apply the full doctrine below through that lens. Each command is conceptually a slice of the same doctrine; the table below says what that slice emphasizes.

### Routing rules

- **No per-command file refs.** The 22 commands resolve through SKILL.md doctrine plus the matching register reference (`references/brand-register.md` or `references/product-register.md`) and the topical references (`references/animation-rules.md`, `references/anti-slop-checks.md`). Future iterations may add per-command refs in `references/commands/<cmd>.md`; today, the route is doctrinal.
- **First word matches a command** → load that command's slice. Everything after the command name is the target.
- **First word is intent-mappable** ("fix the spacing" → `layout`, "rewrite this error message" → `clarify`, "the colors feel flat" → `colorize`, "the motion is off" → `animate` or `polish`): load the matching slice. If two commands could fit, ask once which.
- **No clear intent** → run the front door (design read → dials → register) and propose a 2-3 command menu, then await confirmation.

### Build commands (apply front door → build)

| Command | Lens |
|---|---|
| `craft [feature]` | Apply the full front door, then build the feature end-to-end against the doctrine. Default to a working, production-grade result. |
| `shape [feature]` | Stop at the plan. State the design read, the dials, the register, the surface structure, and the layout-family choices. No code. |
| `init` | Set up project context: prompt the user for PRODUCT.md (audience / goals / register) and DESIGN.md (brand tokens / type stack / motion budget). |
| `document` | Reverse-engineer an existing project into a DESIGN.md (tokens, type stack, motion rules, register inference) from CSS / theme / sample files. |
| `extract [target]` | Pull reusable tokens and components out of an implementation into a documented design system. |

### Evaluate commands (judge existing work)

| Command | Lens |
|---|---|
| `critique [target]` | UX design review with heuristic scoring. Surface-level: tells, hierarchy, motion, slop test. Output: brand-or-product slop test verdict + ranked findings. |
| `audit [target]` | Technical quality (a11y, perf, responsive, contrast, GPU-only motion, `prefers-reduced-motion`). Output: mechanical pass/fail checklist with fix recipes. |

### Refine commands (iterate existing work)

| Command | Lens |
|---|---|
| `polish [target]` | Final quality pass before shipping. Run the preflight checklist from SKILL.md; fix any failed box; produce a before/after diff. The "ship-it" command. |
| `bolder [target]` | Amplify safe or bland designs. Push color strategy up the axis (Restrained → Committed → Drenched). Pick a louder aesthetic family if currently in a reflex-reject saturated lane. |
| `quieter [target]` | Tone down aggressive or overstimulating designs. Step down color strategy, hero motion, micro-interactions, hover complexity. |
| `distill [target]` | Strip to essence. Remove decorative motion, decorative gradients, decorative strips, decorative status dots. Keep only what earns its place. |
| `harden [target]` | Production-ready: empty / loading / error states on every interactive; i18n; edge cases; analytics-safe event names; pre-commit checks. |
| `onboard [target]` | Design first-run flows, empty states, activation moments. Teach the interface to a new user in under 60 seconds. |

### Enhance commands (lift existing work in one dimension)

| Command | Lens |
|---|---|
| `animate [target]` | Add purposeful animations and motion. Always run the decision framework first (should animate? purpose? easing? duration?). Cross-ref `references/animation-rules.md`. |
| `colorize [target]` | Add strategic color to monochromatic UIs. Pick a color strategy, compose a palette around the brand seed, lock color-consistency. Replace the warm-neutral monoculture with deliberate chroma. |
| `typeset [target]` | Improve typography hierarchy and fonts. Cross-ref the reflex-reject list in `references/brand-register.md`. Constrain display letter-spacing ≥ -0.04em; clamp max ≤ 6rem. |
| `layout [target]` | Fix spacing, rhythm, visual hierarchy. Cross-ref the hero discipline and section-discipline rules in SKILL.md. |
| `delight [target]` | Add personality and memorable touches. One cohesive first-load moment, not scattered micro-interactions. |
| `overdrive [target]` | Push past conventional limits. Raise dials (VARIANCE / MOTION / DENSITY +1 to +3). Be prepared to walk back if it overshoots. |

### Fix commands (correct specific defects)

| Command | Lens |
|---|---|
| `clarify [target]` | Improve UX copy, labels, error messages. Plain language. No em-dash. No filler verbs. Locally-appropriate names where invented. |
| `adapt [target]` | Adapt for different devices and screen sizes. Mobile collapse per section is explicit; desktop / tablet / mobile read like separate surfaces that share a register. |
| `optimize [target]` | Diagnose and fix UI performance. CLS candidate hunt, LCP element audit, INP culprit scan, animation GPU-only enforcement, hover-gating. |

### Workaround: when a per-command file would help

The current `viv-design` does **not** ship `references/commands/<cmd>.md` files. Slices route through SKILL.md doctrine + the matching register reference. If a deeper file is wanted for one command (e.g. a full `critique` scoring rubric), write it under `references/commands/` and patch the SKILL.md section above to point to it. Don't promise refs in the table that don't exist.

## Output format for review work (mandatory)

When reviewing, designing, or critiquing code that has a before/after, **always use a markdown table**, never a "Before: … / After: …" list.

### Required: Before / After / Why table

| Before | After | Why |
| --- | --- | --- |
| `transition: all 300ms` | `transition: transform 200ms ease-out` | Specify exact properties; avoid `all` (`all` animates off-GPU) |
| `transform: scale(0)` | `transform: scale(0.95); opacity: 0` | Nothing in the real world appears from nothing |
| `ease-in` on dropdown | `ease-out` + custom curve | `ease-in` delays the moment the user watches most |
| `transform-origin: center` on popover | `var(--radix-popover-content-transform-origin)` | Popovers scale from trigger, not center (modals exempt) |
| No `:active` state | `transform: scale(0.97)` on `:active` | Buttons must feel responsive to press |
| `border-radius: 32px` on card | `border-radius: 12px` on card, pill on tag/button | Cards top out at 12–16px; full-pill is for tags/buttons |
| `border + box-shadow ≥16px blur` on same card | Pick one (single solid border OR shadow ≤ 8px) | "Ghost-card" pattern reads as LLM decoration |
| `p-6 mt-24` centered hero | `pt-24 max-w-5xl` with headline ≤ 2 lines | Hero top-padding cap is `pt-24` |

Wrong format (never do):

```
Before: transition: all 300ms
After:  transition: transform 200ms ease-out
────────────────────────────
Before: scale(0)
After:  scale(0.95)
```

Correct: a single markdown table with | Before | After | Why | columns, one row per issue.

### Required: tiered verdict + decision

After the table, group remaining commentary by impact tier, highest first:

1. Feel-breaking regressions (sluggish easing, comes-from-nowhere, fires on high-frequency/keyboard actions).
2. Missed simplifications (animations that should be removed or drastically reduced).
3. Performance (non-GPU properties, dropped-frame risks, recalc storms).
4. Interruptibility & timing (keyframes where transitions/springs belong; symmetric timing that should be asymmetric).
5. Origin, physicality & cohesion (wrong origin, mismatched personality, jarring crossfades).
6. Accessibility (reduced-motion and pointer/hover gating).

End with an explicit Decision: **Block**, **Approve-with-changes**, or **Approve**. Cite `file:line`. For precise values, pull from `references/animation-rules.md` rather than approximating.

## Common Pitfalls

Numbered list of mistakes agents (including this one) make repeatedly under time pressure.

1. **Skipping the front door.** Jumping to code without the design read + dials + register pick. The output reads as generic.
2. **Defaulting to Inter on sans + Fraunces on serif + cream body bg + AI-purple accent.** The four-way reflex collapse that the production tests catch instantly.
3. **Eyebrow on every section.** The most-violated rule in production tests. Cap is 1 per 3 sections.
4. **Centered hero with big pt-32+ padding.** Hero top-padding cap is `pt-24`. Beyond that = bug, not air.
5. **Animating `width` / `height` / `margin` / `padding` / `top` / `left`.** GPU-only is transform/opacity. The other props trigger layout + paint + composite.
6. **`ease-in` on any UI interaction.** It delays the moment the user is watching. Block.
7. **`scale(0)` entrances.** Nothing appears from nothing. Start `scale(0.9–0.97)` + opacity.
8. **Animation on a keyboard shortcut, command palette toggle, or other 100+/day action.** Skip it. Like Raycast.
9. **`transform: scale(0.97)` with the active state on touch / mobile.** Gate hover motion behind `@media (hover: hover) and (pointer: fine)`. Touch devices shouldn't see them.
10. **Missing reduced-motion fallback.** `@media (prefers-reduced-motion: reduce)` is non-optional.
11. **`position: absolute` tooltip inside `overflow: hidden` container.** Clipped dropdowns. Use `<dialog>`, popover API, fixed positioning, or portal.
12. **White-on-white button / CTA.** Always audit button contrast against the section background. WCAG AA min.
13. **Em-dash anywhere on the page.** Banned outright. Use periods, commas, hyphens. The `—` is the #1 visual Tell.
14. **Three-equal feature cards with icon + heading + text.** The most-generic AI layout. Vary cell sizes, use 2-column zig-zag, asymmetric grid, scroll-pinned, or horizontal-scroll.
15. **Logo wall with plain-text wordmarks.** Use real Simple-Icons (`https://cdn.simpleicons.org/{slug}/ffffff`), devicon, or generated SVG monograms.
16. **No CTA visible above the fold.** Hero overflow that forces scroll-to-find-CTA = broken layout.
17. **Two CTAs with the same intent on one page.** `Get in touch` + `Contact us` + `Let's talk` = all "contact" intent → pick ONE.
18. **Buttons that wrap to 2+ lines at desktop.** Audit every CTA label (3 words max for primary CTAs, ideally 1-2). If label is too long, shorten.
19. **Creating new font pairings without checking the reject list.** The reflex-reject list is not optional for new design choices.
20. **Treating `MOTION_INTENSITY: 8` as "add motion everywhere."** Motion should be motivated; orchestrated at the page level (a reveal) is more coherent than micro-interactions scattered across every component.

## Verification Checklist (preflight)

Run this matrix before outputting code. If a single box cannot be honestly ticked, fix it before delivering.

### Front door
- [ ] Design read declared (single "Reading this as: …" line)?
- [ ] Dials explicit and reasoned from the brief (not silently using baseline)?
- [ ] Register picked (brand vs product) and the matching register reference loaded?
- [ ] If redesign: existing brand tokens extracted before applying color rules?

### Color
- [ ] OKLCH throughout (no hex-as-primary tokens)?
- [ ] Color strategy picked (Restrained / Committed / Full / Drenched) before colors?
- [ ] Cream/sand/warm-paper body bg only with deliberate warm-brief override?
- [ ] If premium-consumer: palette is NOT the beige+brass+oxblood+espresso default family?
- [ ] One accent color used identically across all sections (color consistency lock)?
- [ ] Body text ≥ 4.5:1 against bg; large text ≥ 3:1; placeholders 4.5:1?
- [ ] Every CTA passes WCAG AA contrast against its background?

### Typography
- [ ] No reflex-reject font used as default for a new design choice?
- [ ] Display letter-spacing ≥ -0.04em (not in the cramped -0.05 to -0.085em band)?
- [ ] Hero / display `clamp()` max ≤ 6rem (~96px)?
- [ ] Body line length 65–75ch on prose?
- [ ] `text-wrap: balance` on h1-h3, `text-wrap: pretty` on long prose?
- [ ] Italic words with `y g j p q` descenders have `leading-[1.1]` minimum + pb reserve?
- [ ] Brand brief uses two families only when voice requires it; product brief uses one family where one is right?

### Layout
- [ ] Hero fits in initial viewport: headline ≤ 2 lines, subtext ≤ 20 words ≤ 4 lines, CTAs visible without scroll?
- [ ] Hero top padding ≤ `pt-24` at desktop?
- [ ] Hero text stack ≤ 4 elements (eyebrow OR brand strip → headline → subtext → CTAs)?
- [ ] Logo wall lives under the hero (not inside it)?
- [ ] Eyebrow count across sections ≤ ceil(sectionCount / 3)? (Hero counts as 1.)
- [ ] Navigation on one line at lg+ breakpoint, ≤ 80px tall?
- [ ] Section-Layout-Repetition: no two sections share the same layout family (≥4 families across 8 sections)?
- [ ] Zigzag alternation cap: no 3+ consecutive image+text-split sections?
- [ ] No duplicate CTA intent (`Get in touch` + `Let's talk` both on page = fail)?
- [ ] Bento has rhythm AND exact cell count (N items → N cells, no empty cells)?
- [ ] No `border-t` + `border-b` on every row of long lists / spec tables?
- [ ] Z-index uses a semantic scale; no 999 / 9999?

### Motion
- [ ] Every animation can answer "why does this animate?" in one sentence?
- [ ] No animation on keyboard-initiated actions or 100+/day actions?
- [ ] `ease-out` on enters/exits; `ease-in` banned?
- [ ] Custom easing curves (no built-in `ease` / `linear` for deliberate UI motion)?
- [ ] UI animations ≤ 300ms with the per-element table respected?
- [ ] Popovers/dropdowns/tooltips have correct `transform-origin` (trigger-anchored)?
- [ ] Rapidly-triggered motion (toasts, toggles, drags) is interruptible (transitions or springs, not keyframes)?
- [ ] GPU-only properties (`transform`, `opacity`)? No `width` / `height` / `margin` / `padding` / `top` / `left` animation?
- [ ] `@media (prefers-reduced-motion: reduce)` handled (gentler, not zero)?
- [ ] Hover motion gated behind `@media (hover: hover) and (pointer: fine)`?
- [ ] Asymmetric timing on deliberate actions (press-and-release, hold)?
- [ ] No `window.addEventListener('scroll')` — use Motion / ScrollTrigger / IntersectionObserver?

### Anti-slop
- [ ] ZERO em-dashes (`—` or `–`) anywhere on the page?
- [ ] No gradient text (`background-clip: text` + gradient)?
- [ ] No glassmorphism as default (only rare, purposeful use)?
- [ ] No side-stripe `border-left` / `border-right` > 1px as colored accent?
- [ ] No tiny uppercase tracked eyebrow above every section?
- [ ] No `01 / 02 / 03` numbered section markers as default scaffolding?
- [ ] No fake div-based product preview in the hero (real screenshot or generated image or none)?
- [ ] No scoped `border: 1px solid` + soft wide drop shadow on same element (ghost-card)?
- [ ] No `border-radius: 32px+` on cards (≤ 16px on cards, pill on tags/buttons)?
- [ ] No hand-drawn / sketchy SVG illustrations (`feTurbulence` / crude path scenes)?
- [ ] No `repeating-linear-gradient` stripe backgrounds?
- [ ] No decoration text strip at hero bottom (`BRAND. MOTION. SPATIAL.`)?
- [ ] No locale/time/weather strips (`LIS 14:23 · 18°C`) unless the brief is genuinely place-focused?
- [ ] No scroll cues (`Scroll`, `↓ scroll`, `Scroll to explore`)?
- [ ] No section-number eyebrows (`00 / INDEX`, `06 · how it works`)?
- [ ] No filled-track scoring bars as comparison visuals on landing pages?
- [ ] No decorative status dots before every nav / list row / badge?
- [ ] Aesthetic family named explicitly; not a reflex-reject saturated lane without reason?
- [ ] Impeccable-style category-reflex check (first-order + second-order) passed?

### Imagery
- [ ] When the brief implies imagery, real images shipped (gen-tool / picsum-seed / Unsplash / explicit placeholder slots)?
- [ ] Even minimalist sites have ≥2-3 real images (hero + supporting), not pure-text minimalism?
- [ ] No `div`-based fake screenshots in hero?
- [ ] Logo wall uses real SVG logos (Simple Icons / devicon / generated SVG marks)?

### Production
- [ ] Empty / loading / error states provided on every interactive component?
- [ ] All interactive components have default / hover / focus / active / disabled / loading / error?
- [ ] Forms: labels above inputs, placeholder text passes contrast, helper + error inline?
- [ ] Mobile collapse per section is explicit (`< 768px` fallback declared)? Not "Tailwind handles it"?
- [ ] `prefers-reduced-motion` respected as a real behavioral fork, not a one-line comment?
- [ ] Core Web Vitals plausibly hit (LCP < 2.5s, INP < 200ms, CLS < 0.1)?

## One-Shot Recipes

### Recipe: "Build me a landing page"

1. State the design read in one line.
2. Set dials from inference table; override conversationally if asked.
3. Pick register. For most "landing page" briefs → **brand**. Load `references/brand-register.md`.
4. Pick color strategy (Restrained / Committed / Full / Drenched).
5. Pick design system from `references/design-systems-map.md` OR label aesthetic honestly if no system.
6. Pick hero font from non-reflex-reject list.
7. Build hero per hero discipline (≤ 4 text elements, ≤ pt-24 top padding, ≤ 2-line headline, ≤ 20-word subtext).
8. For each section: pick a layout family from `references/layout-families.md`. No family repeats ≤ 2 sections.
9. Eyebrow cap = ceil(sectionCount / 3). Hero counts as 1.
10. Run preflight checklist. Fix anything that fails. Ship.

### Recipe: "Review this animation code"

1. Read the diff. List every animated element.
2. For each, run the animation decision framework (should animate? purpose? easing? duration?).
3. For each finding, cite a precise value from `references/animation-rules.md`, not an approximation.
4. Output the Before/After/Why table.
5. Group remaining commentary by tier.
6. End with Block / Approve-with-changes / Approve.

### Recipe: "Make this look less like AI made it"

1. Run the brand slop test on the current state. What fails? List it.
2. Run the aesthetic-lane check on the current state.
3. Eyebrow audit: count `uppercase tracking` micro-labels. If ≥ ceil(sectionCount / 3), strip the excess.
4. Em-dash audit: grep the markup. Replace every `—` and `–` (when used as separator) with `.`, `,`, `-`, or line break.
5. Cream/BG audit: is the body bg in the warm-neutral monoculture band? Replace with deliberate choice.
6. Hero-metric / identical-card-grid audit: collapse or restructure.
7. Add the section that's missing: real imagery (not div rectangles), real CTA contrast, real component states.

### Recipe: "Fix the typography"

1. Pick register. Product → one well-tuned sans. Brand → distinctive selection per procedure.
2. Run the font reject list against the current font.
3. Pick a non-reject font. Browse a real catalog (Google Fonts, Pangram Pangram, Future Fonts, Adobe Fonts).
4. Single family or paired pair on a contrast axis (serif + sans, geometric + humanist).
5. Set modular scale ≥ 1.25 ratio (brand) or tighter 1.125–1.2 (product).
6. Display letter-spacing ≥ -0.04em; clamp max ≤ 6rem.
7. `text-wrap: balance` on headings; `text-wrap: pretty` on prose.
8. Run preflight typographic checks.

## How to Resync from Upstream

The three sources evolve. To re-sync:

```bash
mkdir -p ~/tmp/design-skills-research
cd ~/tmp/design-skills-research
git pull            # in each of: skills/  impeccable/  taste-skill/
# then re-extract the doctrine into viv-design/references/
```

When a v2 of any source ships, revisit:
- the font reflex-reject list
- the production-test LLM tells list
- the animation standards table
- the canonical sources list

The viv-design skill is the integration. The reference files are the citable values. The preflight checklist is the contract.
