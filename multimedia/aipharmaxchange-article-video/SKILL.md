---
name: aipharmaxchange-article-video
description: Produce polished AIPharmaXchange LinkedIn explainers from a pharma or health-AI paper, PDF, or research link. Use when creating or revising a lip-synced host-and-data-slide social video for AIPharmaXchange, especially when the host stays on the left and image-generated watercolor data slides appear on the right.
---

# AIPharmaXchange Article Video

Create a four-part, evidence-led LinkedIn explainer. Preserve the approved host clips and their embedded audio whenever only layout or slide design changes.

## Workflow

1. Read the supplied paper with the PDF skill. Extract only verified claims, metrics, limitations, and citation details. Write four short spoken beats; a 40-second cut uses four 10-second segments.
2. Lock the host and lip sync. Generate narration with Venice speech, then create each host clip with Venice/Seedance reference audio and an approved host reference. Keep the downloaded host clip's embedded audio in the final edit. Do not replace it with independently rendered TTS after video generation.
3. Generate four slides with the built-in image model. Use [assets/watercolor-style-reference.jpg](assets/watercolor-style-reference.jpg) as a style reference. Put all metrics and labels inside the image; do not create text overlays in the editor. Require 3:2 landscape, verbatim on-image text, a visible source line, and generous safe margins.
4. Inspect every generated slide at full size. Regenerate a slide if any required text, metric, title, source, or brand label is wrong or cropped.
5. Assemble at 35% host / 65% slide with the bundled script. The script center-crops the existing host footage only to fill the narrow panel, preserves its audio stream, and centers the full 3:2 slide in the right panel.

```powershell
python scripts/assemble_linkedin_35_65.py `
  --slides-dir <landscape-slide-folder> `
  --host-dir <downloaded-host-video-folder> `
  --output <final-mp4>
```

6. Verify a 1920x1080, 30 fps export. Sample one frame per segment for complete slide text, stable host identity, and no letterboxing on the host. Compare audio and video duration; target a difference of 0.05 seconds or less.

Read [references/production-workflow.md](references/production-workflow.md) before drafting narration or image prompts. It contains the slide prompt template, lip-sync rules, and acceptance checks.

## Guardrails

- Frame the research accurately; never imply clinical validation or deployment readiness unless the paper establishes it.
- Keep narration, slide claims, and citations consistent with the paper.
- Use current Venice model capabilities and pricing rather than assuming an old model ID or parameter is still available.
- Treat the host reference as user-owned media. Do not substitute or alter the presenter without explicit approval.
- Keep Venice API keys out of prompts, scripts, source files, and email bodies.
