---
title: Still-Photo Celebration Composite
name: still-photo-celebration-composite
description: Face-likeness-guaranteed celebration videos using original photos on a generated background, animated in FFmpeg. Use when R2V fails for multi-person dynamic scenes.
category: venice
tags: [venice, video, ffmpeg, composite, anniversary, patriotic, multi-person, face-likeness]
trigger: Use when the user wants a celebratory video featuring multiple real people and AI video models fail to preserve face likeness.
---

# Still-Photo Celebration Composite

Worked approach for face-likeness-guaranteed celebration videos when R2V fails.

## Core idea

Use the **original photos unchanged**, place them on a generated thematic
background, add subtle Ken Burns zoom/pan, animated text, and music. This avoids
face generation entirely.

## When to use

- 3+ people in dynamic/fast motion where face likeness is critical.
- R2V has already failed (invented people, wrong clothing, generic faces).
- User prefers guaranteed likeness over full AI motion.

## Workflow

1. Generate background with `gpt-image-2` (`aspect_ratio: 16:9`, `resolution: 2K`).
2. Assemble original photos with FFmpeg `overlay` + `zoompan`.
3. Add animated text with `drawtext` in the **bottom third** (never over faces).
4. Add thematic border.
5. Generate or source music.
6. Mux with FFmpeg.

## Key rules

- Text goes in bottom third, never across faces.
- Use original photos, not generated references.
- Offer the user a choice: synthesized beat or their own MP3.
- Venice has no `/audio/music` endpoint.

## Reference session

2026-07-04 anniversary dance battle: Kling R2V with 4 face crops invented a 5th
person and generic faces; final deliverable used still-photo composite with
patriotic flag background, side-by-side couples, flying text, and procedural
music.

## See also

- `venice-video-class` for the broader Venice video umbrella.
