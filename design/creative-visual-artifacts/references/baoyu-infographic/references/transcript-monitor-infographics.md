# Infographics from transcript-monitor CSV rows

Use this when a scheduled YouTube/video monitor needs a visual summary of new rows.

## Input shaping

Image generators perform better with a compact brief than with raw CSV/transcript dumps. Build a prompt from each new row using:

- title;
- `core_lesson`;
- top 3-5 `new_or_emerging_topics`;
- top 3-4 `actionable_takeaways`;
- top 2-3 `mistakes_to_avoid`;
- named tools/models/methods.

Do not include full transcripts. Save the prompt as `.prompt.txt` next to the generated image for auditability.

## Recommended visual recipe

- Layout: `dense-modules`.
- Style: `technical-schematic` / blueprint.
- Aspect: 16:9 landscape.
- Modules:
  - Executive lesson radar;
  - New/emerging topic chips;
  - one video card per new video;
  - builder actions checklist;
  - mistakes-to-avoid warning zone;
  - tools/models/methods matrix;
  - what-to-watch-next roadmap.

## Prompt constraints

- Tell the model to use exact video titles and not invent source titles.
- Use short text labels; generated infographics can garble long paragraphs.
- Prefer labels, badges, gauges, arrows, checklists, and matrices over dense prose.
- Ask for "NEW" badges on emerging topics and small practicality/novelty gauges when available.

## Verification

Before declaring success:

1. Confirm the image file exists and is non-empty.
2. Use vision review or a screenshot preview to check it is not blank/corrupted.
3. Check the main title and major module headings are legible enough.
4. If text artifacts are severe, regenerate with a shorter prompt and fewer text-heavy modules.