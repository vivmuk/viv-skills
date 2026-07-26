---
name: creative-visual-artifacts
description: "Umbrella for visual design artifacts: HTML/SVG mockups, diagrams, avatars/logos, infographics, hand-drawn diagrams, design systems, and token specs."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [creative, design, html, svg, diagrams, infographics, logos, mockups, design-systems]
---

# Creative Visual Artifacts

Use this umbrella whenever the user asks for a visual artifact, design deliverable, static browser mockup, SVG/HTML diagram, infographic, avatar/logo, design token spec, or a design-system-inspired composition.

## Triage: choose the artifact lane

1. **One-off HTML artifact / landing / deck / prototype** — start from the user's context and produce a single self-contained HTML file. Use the `claude-design` reference package for HTML/CSS standards, WSL preview pitfalls, and deck rules.
2. **Fast comparison mockups** — create 2-3 variants, each with a stance, trade-offs, and real HTML. Use the `sketch` reference package for the variant README pattern.
3. **Architecture or systems diagrams** — render dark-themed SVG/HTML with semantic colors, clean layout, labeled edges, and previewable output. Use the `architecture-diagram` package for template structure and palette guidance.
4. **Hand-drawn diagrams** — use Excalidraw JSON for architecture, flow, and sequence diagrams where a sketch aesthetic is desired. Use the `excalidraw` package for element schemas and upload helper details.
5. **Infographics / knowledge visuals** — analyze the content, select a layout (roadmap, comparison, dashboard, funnel, iceberg, etc.) and a style palette, then generate structured content before rendering. Use the `baoyu-infographic` package for the layout/style catalog.
6. **Avatar/logo/sigil design** — produce prompt-first visual concepts, then verify platform fit; fall back to programmatic SVG/logo construction when image generation is unavailable. Use the `avatar-logo-design` package.
7. **Design systems / named brand styles** — borrow structure, spacing, typography, and color language from a known web design system without copying proprietary assets. Use the `popular-web-designs` package.
8. **DESIGN.md token specs** — author or validate a design token contract; maintain canonical section order, token references, and contrast checks. Use the `design-md` package.
9. **Local generative-media workflows / ComfyUI** — use `references/comfyui/legacy-skill.md` for ComfyUI installation, hardware checks, REST/WebSocket workflow execution, parameter injection, dependency checks, output downloads, and the preserved scripts/workflows package.

## Core workflow

1. **Clarify only if necessary.** If the requested artifact type is obvious, proceed. Ask only when output medium, dimensions, or audience materially changes the implementation.
2. **Pick a lane and name it in your own working notes.** A human maintainer should be able to see whether you are doing infographic, mockup, diagram, brand/avatar, or token-spec work.
3. **Create a real artifact, not a description.** Prefer a saved HTML/SVG/JSON/MD file with enough CSS/data included to preview or reuse.
4. **Use references as source packages.** Legacy narrow skills were preserved under `references/<old-skill-name>/`; read `references/<old-skill-name>/legacy-skill.md` and any nested files when a lane needs detailed syntax, templates, or pitfalls.
5. **Preview or validate.** For HTML/SVG, use browser/screenshot or static checks where available. For JSON diagrams, validate JSON. For token specs, run the validator/lint path from the reference. When WSL lacks local Chromium/Playwright, use the Windows Chrome/Edge headless screenshot path from `references/html-summary-atlas.md` rather than skipping visual verification.
6. **Report file paths and verification.** Include exactly what was created and how it was checked.

## Agent/session-history summary artifacts

When the user asks to combine agent work history, tasks, or themes into a beautiful summary HTML, follow `references/html-summary-atlas.md`: make an atlas-style self-contained HTML with hero, stats, agent cards, themes, timeline, ownership cleanup, and next steps; verify with HTML parsing plus a rendered screenshot; deliver both the `.html` and preview PNG when possible.

## Quality bar

- Make the artifact opinionated and usable, not a vague mood board.
- Encode layout, typography, spacing, and palette decisions explicitly.
- Prefer semantic structure and reusable components over one giant blob.
- Avoid placeholder-only outputs unless the user explicitly asked for a template.
- Keep generated images/designs platform-aware: avatar safe areas, slide aspect ratios, responsive HTML, and contrast.

## Reference packages preserved

The following previous narrow skills were absorbed into this umbrella and their complete packages were copied under `references/` before archiving the original skill roots:

- `references/architecture-diagram/`
- `references/avatar-logo-design/`
- `references/baoyu-infographic/`
- `references/claude-design/`
- `references/design-md/`
- `references/excalidraw/`
- `references/popular-web-designs/`
- `references/sketch/`
- `references/comfyui/`
- `references/website-from-reference-images.md` — reference-to-code workflow: translating visual references (images, screenshots, descriptions) into local HTML/CSS/JS builds, with Venice API image generation, budget tracking, and hybrid classical+digital art prompt templates.
