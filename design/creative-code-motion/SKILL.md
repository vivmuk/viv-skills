---
name: creative-code-motion
description: "Umbrella for code-driven generative visuals, browser demos, ASCII/video pipelines, Manim explainers, and TouchDesigner real-time scenes."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [creative, generative-art, animation, video, p5js, manim, ascii, touchdesigner, browser-demos]
---

# Creative Code & Motion

Use this umbrella when the user wants a code-generated visual, animation, explainer video, interactive browser demo, kinetic typography, ASCII video, or real-time visual system.

## Triage: choose the production lane

1. **p5.js / browser generative art** — for interactive sketches, procedural visuals, shaders, WEBGL, exported frame sequences, and single-file viewer demos. Use `references/p5js/`.
2. **Pretext text-layout demos** — for DOM-free text layout, text-as-geometry, kinetic typography, and typographic flow around obstacles. Use `references/pretext/`.
3. **Manim explainer animation** — for math, algorithms, 3Blue1Brown-style educational sequences, graphs, equations, and camera choreography. Use `references/manim-video/`.
4. **ASCII stills and terminal art** — for pyfiglet/cowsay/boxes, image-to-ASCII stills, terminal banners, and chat-friendly monospace compositions. Use `references/ascii-art/`.
5. **ASCII video pipeline** — for converting imagery/video/audio to colored ASCII MP4/GIF or stylized terminal-video compositions. Use `references/ascii-video/`.
6. **TouchDesigner MCP** — for live real-time visuals where Hermes controls an existing TouchDesigner process through twozero MCP tools. Use `references/touchdesigner-mcp/`.

## Core workflow

1. **Decide the runtime.** Browser/HTML, Python/Manim, FFmpeg/ASCII, or TouchDesigner have very different verification paths.
2. **Create a real project directory.** Include source, rendered output or preview, and a short README when more than one file is produced.
3. **Use the preserved lane package.** Each absorbed skill remains under `references/<lane>/` with its original scripts/templates/references preserved; the former SKILL.md is `references/<lane>/legacy-skill.md`.
4. **Render or smoke-test.** Do not stop at source code. Run the browser render/export script, Manim render, FFmpeg probe, or TouchDesigner discovery/build check as applicable.
5. **Iterate on aesthetics.** Motion work should have timing, composition, palette, and legibility decisions — not just technically valid output.

## Verification checklist

- Source file exists and can be opened or run.
- At least one output/preview path is produced, or a tool/runtime blocker is reported honestly.
- Logs do not show missing runtime dependencies that could be fixed in-session.
- If exporting video/GIF, verify duration, dimensions, and file size.
- If interactive, include controls and a local preview command.

## Reference packages preserved

- `references/ascii-art/`
- `references/ascii-video/`
- `references/manim-video/`
- `references/p5js/`
- `references/pretext/`
- `references/touchdesigner-mcp/`
