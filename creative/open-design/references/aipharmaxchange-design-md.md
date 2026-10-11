# AIPharmaXchange DESIGN.md — Working Example

This is the actual DESIGN.md created for AIPharmaXchange, a healthcare AI community. It follows the 9-section canonical schema from the `design-md` skill and demonstrates a watercolor/wash aesthetic for a professional healthcare brand.

## Key Design Decisions

- **Primary: #00D4AA (teal)** — Conveys trust, innovation, and clinical credibility without the coldness of blue
- **Secondary: #FEFCF8 (warm cream)** — Softer than pure white, gives a "handcrafted" feel
- **Accent: #1A1A2E (deep indigo)** — For text and high-contrast elements
- **Fonts: Fraunces Variable (headlines) + Inter Variable (body)** — Fraunces adds character to headings, Inter ensures readability at small sizes
- **Watercolor wash effect** — Differentiates from typical tech/healthcare brands that use flat geometric styles

## Full DESIGN.md Content

```yaml
---
version: alpha
name: AIPharmaXchange
description: Where AI meets pharma — watercolor warmth meets clinical precision
colors:
  primary: "#00D4AA"
  secondary: "#FEFCF8"
  tertiary: "#1A1A2E"
  neutral: "#F0EDE8"
  accent: "#FFB347"
  danger: "#E74C3C"
  success: "#27AE60"
typography:
  h1:
    fontFamily: Fraunces Variable
    fontSize: 3rem
    fontWeight: 900
    lineHeight: 1.1
    letterSpacing: "-0.02em"
  h2:
    fontFamily: Fraunces Variable
    fontSize: 2rem
    fontWeight: 700
    lineHeight: 1.2
  body-md:
    fontFamily: Inter Variable
    fontSize: 1rem
    fontWeight: 400
    lineHeight: 1.6
  caption:
    fontFamily: Inter Variable
    fontSize: 0.75rem
    fontWeight: 500
    letterSpacing: "0.04em"
rounded:
  sm: 4px
  md: 12px
  lg: 20px
  xl: 32px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 48px
components:
  card-primary:
    backgroundColor: "{colors.secondary}"
    textColor: "{colors.tertiary}"
    rounded: "{rounded.lg}"
    padding: 24px
  card-accent:
    backgroundColor: "{colors.primary}"
    textColor: "#FFFFFF"
    rounded: "{rounded.lg}"
    padding: 24px
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "#FFFFFF"
    rounded: "{rounded.md}"
    padding: 12px
  button-primary-hover:
    backgroundColor: "#00B894"
---

## Overview

AIPharmaXchange bridges the gap between AI innovation and pharmaceutical practice. The visual identity combines watercolor warmth with clinical precision — evidence-first, never gimmicky.

## Colors

- **Primary (#00D4AA):** Teal — trust, innovation, clinical credibility. Used for CTAs, highlights, accent bars.
- **Secondary (#FEFCF8):** Warm cream — softer than white, gives handcrafted feel. Default background.
- **Tertiary (#1A1A2E):** Deep indigo — text, high-contrast elements. Never use pure black.
- **Accent (#FFB347):** Amber — data callouts, warning highlights. Use sparingly.
- **Neutral (#F0EDE8):** Washed stone — secondary backgrounds, cards, dividers.

## Typography

Fraunces Variable (display/headlines) — variable serif with personality. Use for h1–h3 only.
Inter Variable (body/UI) — clean sans-serif for everything else. All-caps for labels with 0.04em tracking.

## Layout

8px grid system. Max content width: 1200px. Carousel slides: 1080×1080px (LinkedIn native). Infographics: 1024×768px minimum.

## Elevation & Depth

Watercolor wash effect on card backgrounds. Subtle drop shadows (0 2px 8px rgba(0,0,0,0.08)). No harsh borders — use shadow and color differentiation instead.

## Shapes

Rounded corners on everything. Small: 4px (buttons), Medium: 12px (cards), Large: 20px (modals), XL: 32px (hero sections). No sharp corners.

## Components

Cards use cream background with teal accents. Primary buttons are teal with white text. Data visualizations use the teal-to-amber gradient palette.

## Do's and Don'ts

- ✅ Use teal for CTAs and key data highlights
- ✅ Use cream/warm white backgrounds, never pure white
- ✅ Watercolor wash on hero sections and card backgrounds
- ✅ Fraunces for headlines, Inter for body
- ❌ Never use pure black (#000) for text — use #1A1A2E
- ❌ Never use more than 3 colors in a single composition
- ❌ Never use geometric/flat design — this brand is organic and warm
- ❌ Never use comic sans, papyrus, or system default fonts
```

## Integration Pattern

When generating content with Open Design, reference this DESIGN.md by placing it at:
```
/tmp/open-design/design-systems/aipharmaxchange/DESIGN.md
```

The daemon auto-discovers it on startup. All skills that support design system selection will enforce these tokens automatically.
