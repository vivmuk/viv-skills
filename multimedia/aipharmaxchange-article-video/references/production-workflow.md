# Production workflow

## Shot bible

- Format: four 10-second clips, assembled to a 40-second 1920x1080 LinkedIn video.
- Layout: host panel is 672px wide (35%); slide panel is 1248px wide (65%).
- Slide: 3:2 landscape; center it in the right panel on warm ivory (#fbf8f0). Do not crop slide content.
- Host: reuse approved Venice/Seedance clips and their embedded audio. Center-crop only enough to fill 672x1080.
- Visual style: warm ivory paper, navy serif type, navy/teal/lavender watercolor washes, restrained gold flourishes, botanical accents, medically literate illustrations.

## Narration and lip sync

1. Draft approximately one natural spoken sentence per 10-second beat.
2. Create each narration file with Venice speech.
3. Use each narration file as the reference audio for the matching Venice/Seedance host-video generation; use the same approved host reference for all clips.
4. Download approved host clips promptly and archive the queue IDs, model, settings, prompts, and source paths.
5. In the final assembly, map audio from the host video (`1:a:0`). This retains the provider's audio/video timing and is the default lip-sync safeguard.

## Image-model prompt template

Use this structure for each slide. Replace only the quoted text and the visual layout.

```text
Use case: productivity-visual
Asset type: 3:2 landscape LinkedIn video data slide, placed on the right 65% of a 16:9 video.
Input image: Image 1 is a STYLE REFERENCE ONLY. Match its refined healthcare watercolor presentation: warm ivory paper, navy serif type, watercolor clouds in navy/teal/lavender, fine gold flourishes, small botanical leaves, balanced scientific card layout.
Primary request: Create a polished 3:2 LANDSCAPE watercolor infographic slide about [PAPER].
Text (verbatim, exact capitalization and punctuation):
"[TITLE]"
"[FACT OR METRIC]"
"AIPharmaXchange"
"Source: [CITATION]"
Visual layout: [ONE CONCRETE HORIZONTAL LAYOUT].
Constraints: all listed text must be verbatim, crisp, large, and readable on a 1920x1080 video; no people; no extra facts; no watermark; no cropped text.
```

## Acceptance checklist

- Every metric, range, title, source, and brand label is visibly correct in the generated image.
- Slide aspect is 3:2 landscape and retains the footer after assembly.
- The host remains the same person, wardrobe, set, and microphone arrangement across clips.
- The host mouth motion agrees with the embedded clip audio; no independent TTS replaces it in the final edit.
- Final audio/video duration difference is no more than 0.05 seconds.
- Claims describe the paper as research unless its evidence supports a stronger statement.
