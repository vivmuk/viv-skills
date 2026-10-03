---
name: frontend-design-taste
description: "Use when building, redesigning, auditing, or shipping any front-end UI. A five-source design doctrine: taste, guidelines audit, real design-system tokens, image-first references, and browser QA."
version: 2.0.0
author: Vega (Hermes Agent, packaged for Vivek M)
license: MIT
date: 2026-10-03
tags: [design, frontend, ui, ux, mobile-first, anti-slop, accessibility, design-systems, browser-qa]
---

# Frontend Design Taste

The complete front-end design doctrine, distilled from five source skills into one package. Simple surface, powerful underneath. The goal is always the same: interfaces that look intentionally designed, not generated.

```
THE PIPELINE: read the brief → set the dials → pick the foundation →
build with the rules → audit the code → verify in a browser → ship
```

## The five modules

| # | Module | What it does | Full reference |
|---|--------|--------------|----------------|
| 1 | Design taste | Brief inference, dials, anti-slop discipline, pre-flight check | `references/taste-skill.md` |
| 2 | Guidelines audit | Line-by-line UI code review rules (a11y, focus, forms, perf) | `references/vercel-web-interface-guidelines.md` |
| 3 | Design-system tokens | 74 real-world DESIGN.md files to build from instead of inventing | `references/design-md-index.md` + `references/design-md-exemplars/` |
| 4 | Image-first design | Generate reference images first, then implement to match | `references/image-to-code.md` |
| 5 | Browser QA | Automated open → screenshot → console-check before shipping | `references/playwright-cli.md` |

Plus nine auxiliary taste-skill styles, vendored in `references/`: redesign, brandkit, gpt-taste (GSAP motion), imagegen-frontend-web, imagegen-frontend-mobile, soft-skill, minimalist-skill, brutalist-skill, stitch-skill.

Load the main SKILL.md for the doctrine. Open a reference when a task needs that module's full depth.

---

## Module 1. Design taste (read the room before anything)

Before touching code, declare a one-line design read:

> "Reading this as: `<page kind>` for `<audience>`, with a `<vibe>` language, leaning toward `<system or aesthetic>`."

Signals to read: page kind, vibe words the user used, reference URLs/screenshots, audience, existing brand assets, quiet constraints (accessibility, trust, regulated).

Rules:
- If the brief is ambiguous, ask exactly ONE question. If inferable, declare the read and proceed.
- Never jump to a default aesthetic. The audience picks the aesthetic, not your taste.

### The three dials

Every layout, motion, and density decision is gated by three dials, set after the read:

| Dial | 1 | 10 | Pro tool | Landing | Trust-first |
|------|---|----|----------|---------|-------------|
| DESIGN_VARIANCE | perfect symmetry | artsy chaos | 6 | 8 | 3 |
| MOTION_INTENSITY | static | cinematic physics | 3 | 6 | 2 |
| VISUAL_DENSITY | art gallery | packed cockpit | 3 | 4 | 5 |

Dial map (from taste-skill): "minimalist / calm / Linear-style" → 5-6 / 3-4 / 2-3. "premium consumer / Apple-y / luxury" → 7-8 / 5-7 / 3-4. "Awwwards / agency" → 9-10 / 8-10 / 3-4. Redesign-preserve → match existing. Redesign-overhaul → +2.

Motion is motivated or it is cut. Every animation must answer "what does this communicate?" (hierarchy, storytelling, feedback, state transition) in one sentence or it gets deleted.

### The AI tells (hard bans)

These are the statistical defaults of generated UI. All are banned unless the brief explicitly calls for one:

- AI-purple gradients, centered hero over dark mesh, generic glassmorphism on everything
- Three equal feature cards in a row
- Inter as the default font; #000000 pure black; neon outer glows; oversaturated accents
- Fake product UIs built from styled divs; decorative status dots; section-number eyebrows ("01 / Capabilities")
- Version labels in heroes, scroll cues ("Scroll to explore"), locale/weather strips, "Quietly trusted by"
- Generic names ("Jane Doe"), startup-slop brands ("Acme", "Nexus", "SmartFlow"), filler verbs ("Elevate", "Unleash", "Seamless")
- Em-dash (—) anywhere visible. Zero. Use a period, comma, or hyphen. This is the single most-violated tell.
- Hand-rolled SVG icons. Use an icon library (Phosphor, Tabler, HugeIcons, Radix), one family per project.

The full tells list with production-test examples: `references/taste-skill.md` Section 9.

### Architecture defaults (when no design system is picked)

Tailwind v4, Motion (from `motion/react`, not `framer-motion`), `next/font` or self-hosted fonts with `font-display: swap`, never Google Fonts `<link>`. `min-h-[100dvh]`, never `h-screen`. CSS Grid over flex-math. Verify every 3rd-party import exists in `package.json` before importing it.

### The pre-flight check

Before outputting code, run the full matrix in `references/taste-skill.md` Section 14: hero fits the viewport, one accent color across all sections, one corner-radius system, WCAG AA contrast on every CTA and form, eyebrow count under ceil(sections/3), no two sections sharing a layout family, empty/loading/error states present, Core Web Vitals plausible. If a single box fails, the output is not done.

---

## Module 2. Guidelines audit (before shipping)

Audit the code line-by-line against the Web Interface Guidelines. Full rules: `references/vercel-web-interface-guidelines.md`. The highest-frequency failures:

- Icon-only buttons need `aria-label`. Every input needs a `<label>` or `aria-label`, correct `type` and `inputmode`.
- `<button>` for actions, `<a>` for navigation. Never `<div onClick>`.
- Visible `:focus-visible` rings on every interactive element. Never `outline: none` without a replacement.
- Async status updates need `aria-live="polite"`. Images need `alt` (empty if decorative).
- Semantic HTML before ARIA. `prefers-reduced-motion` respected. Hit areas ≥ 44px on touch.
- Audit output format: terse `file:line` findings, highest signal-to-noise, grouped by severity.

---

## Module 3. Design-system tokens (build from reality)

Never invent a design system when a real one exists. 74 real-world DESIGN.md files are indexed in `references/design-md-index.md`; eight curated exemplars are vendored in `references/design-md-exemplars/` (linear.app, apple, vercel, figma, stripe, notion, spotify, airbnb).

How to use them:

1. Match the brief to a reference system (a Linear-style dev tool → read `linear.app.md`; a premium consumer app → `apple.md`; a developer product → `vercel.md`).
2. Extract the token layer: canvas, surfaces 1-4, hairlines, ink levels, ONE accent, semantic colors, type scale (family, size, weight, line-height, tracking per role), spacing scale, radii.
3. Rebuild those tokens as CSS custom properties. Use the accent ONLY for CTAs, focus rings, and active states. Never decoratively.
4. One system per project. Do not mix.

Canonical token pattern (Linear, the most-imitated reference): near-black canvas `#010102`, charcoal surfaces `#0f1011`-`#191a1b`, hairline borders `#23252a`, ink `#f7f8f8` with three muted steps, single lavender accent `#5e6ad2`, display type at 500-700 weight with negative tracking, quietly luxurious.

---

## Module 4. Image-first design (references before code)

For visually-important work, do not design blind. Full doctrine: `references/image-to-code.md`. The rules that matter:

- Generate or collect design reference images FIRST, deeply analyze them, then implement to match as closely as possible.
- One section = one reference image. Never one compressed board of everything.
- Hero stays clean, spacious, readable, visible on a small laptop.
- No cards-inside-cards-inside-cards. No lazy under-generation.
- For mobile app UI, follow `references/imagegen-frontend-mobile.md`: app-native screens, safe-area aware, readable at a glance, one consistent palette, no purposeless glass.

---

## Module 5. Browser QA (never ship unseen)

Every deliverable gets opened, exercised, and screenshotted before it is called done. Full command reference: `references/playwright-cli.md` (plus 10 deep references in `references/playwright-cli-references/`).

```
playwright-cli open http://localhost:3000
playwright-cli snapshot            # accessibility tree, not pixels
playwright-cli find "Sign in"      # locate elements by text
playwright-cli click e15           # interact using snapshot refs
playwright-cli resize 390 844      # test mobile widths
playwright-cli screenshot          # visual evidence
playwright-cli eval "document.title"
playwright-cli close
```

The QA loop: open → exercise every state (empty, loaded, error, every tab/route) → screenshot each at 360px, 390px, 768px, 1280px → read the console for errors → fix → re-verify. A build that has not been seen in a browser is not done.

For test generation, request mocking, tracing, and video recording, see the playwright-cli references directory.

---

## The combined workflow (all five in sequence)

1. **Read** (Module 1): declare the design read, set the three dials.
2. **Ground** (Modules 3+4): pick the token system from the DESIGN.md collection, or generate reference images first for bespoke visuals.
3. **Build** (Module 1 rules): token-driven CSS, one accent, motivated motion, no tells.
4. **Audit** (Module 2): run the guidelines checklist over the code, fix every `file:line` finding.
5. **Verify** (Module 5): browser QA loop, all states, all widths, console clean.
6. **Ship**: pre-flight check from Module 1 Section 14, every box honestly ticked.

---

## Mobile-first doctrine (applies to every module)

This is a mobile-first doctrine by default. Test at 360-390px first, then widen:

- Bottom tab bar / primary actions in the thumb zone; `env(safe-area-inset-bottom)` padding.
- `100dvh` not `100vh`; sticky headers must not cover focused elements.
- Touch targets ≥ 44px. Body text ≥ 13px. No hover-dependent interactions.
- Sheets, not center-modals, on mobile. One primary action per screen.
- `prefers-reduced-motion` and `prefers-reduced-transparency` respected with real fallbacks.

## Provenance

| Source | Upstream | License |
|--------|----------|---------|
| taste-skill (+ 13 sub-skills) | github.com/Leonxlnx/taste-skill | MIT |
| Web Interface Guidelines | github.com/vercel-labs/web-interface-guidelines | MIT |
| awesome-design-md (74 systems) | github.com/VoltAgent/awesome-design-md | MIT |
| playwright-cli (+ 10 references) | github.com/microsoft/playwright-cli | Apache-2.0 |
| image-to-code | vendored from taste-skill | MIT |

Assembled 2026-10-03 from the "5 Claude Code front-end design plugins" skill set. All credit to the original authors; this package redistributes their material under the same licenses.
