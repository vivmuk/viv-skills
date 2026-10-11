# MIRA Carousel — Measurement Run Transcript (2026-06-18)

The first end-to-end measurement of the editorial-carousel-orchestration
pipeline. Used to derive the cost, wall-clock, and quality baselines
captured in the parent SKILL.md.

## Inputs
- Source paper: `s41586-026-10675-5.pdf` (MIRA — "Towards autonomous
  medical artificial intelligence agents", Nature 2026, Ferber et al.,
  Heidelberg / TU Dresden, Hippocratic AI Polaris 2.1 base)
- 142,417 chars of paper text extracted via pymupdf in 0.34s
- Models: CEO + reviewers on `minimax-m3`; image gen on
  `grok-imagine-image-quality`; all calls via the working Venice
  key in `~/.hermes/config.yaml`

## Wall-clock per stage (sequential)

| Stage | Time |
|---|---|
| Paper extract | 0.34s |
| CEO writes 7-slide spec | 31.9s |
| 7× image gen (sequential) | ~180s |
| 21 reviewer calls (3 per slide × 7 slides) | ~200s |
| Pillow render + PDF assembly | <2s |
| **Total sequential** | **~7 min** |
| **If images parallelized (7 concurrent)** | **~3.5 min** |

## Token + cost

- CEO: 14,725 in / 2,660 out → $0.005
- Reviewers (21 calls): ~75K in / ~22K out → $0.040
- Image gen (7 images): ~$0.35
- **Total: ~$0.40 per carousel** at minimax-m3 + grok-imagine pricing

## What worked

- **CEO as medical writer.** Spec was excellent. Caught the paper's
  actual 88.9% diagnostic accuracy (vs the 87.8% I had earlier
  guessed), included 8 named conditions, page citations on every
  key claim, the trend context with named systems (AMIE / MAI-DxO /
  OpenAI-Penda), and 4 honest limitation cards.
- **Pillow text overlay.** Title + bullets + key-claim footer
  always rendered cleanly, no clipping, palette correct.
- **3 reviewers caught the alignment and brand issues** that
  would have shipped (5-9/10 scores with specific feedback).

## What broke (and the fixes)

1. **Hallucinated text inside illustrations.** Slide 6's
   limitations cards contained "One mec coce card feels slightly
   tilted." and "One mec coce card feels cocd opbasteri." —
   gibberish AI-generated strings inside the visual. The
   `grok-imagine-image-quality` model rendered these despite
   the visual_hint in the spec saying the cards should contain
   the 4 limitation names. **Fix:** force the image model to
   render ONLY the visual/background (with "no text, no
   letters, no words, no characters, no labels" in the
   prompt), and let Pillow overlay ALL text.

2. **Decorative-only "bar chart" on slide 3.** The image model
   rendered watercolor bars with no axes, no labels, no
   legend, no scale. The reader cannot extract any value.
   The "88.9% vs 78.1%" claim in the title is supported by
   the body text but not by the visual. **Fix:** draw the
   chart in Pillow with explicit bars + value labels.

3. **Z-order collisions on slides 3 and 5.** The image model's
   bars and illustrations bled into the bullet text. The
   MIRA bullet "admissions inside a standards-compliant EHR
   sandbox" was partially obscured by the hospital-bed
   illustration. **Fix:** constrain the image to the lower
   50% of the slide (via prompt direction), and ensure
   bullets have a solid cream background plate behind them.

4. **15/21 reviewer calls returned unparseable content.**
   The model produced prose preamble ("Here's my review: ...")
   or markdown fences around the JSON. **Fix:** add
   `response_format: {"type": "json_object"}` to all
   reviewer calls. With it, parsing always succeeds.

5. **Reviewers only saw the slide spec, not the rendered PNG.**
   So hallucinated text inside the image, decorative chart
   problems, and z-order collisions all shipped silently.
   **Fix:** include the rendered PNG bytes (base64 in
   `image_url`) in every reviewer prompt.

## Spec produced (slide-by-slide)

```json
{
  "slides": [
    {
      "slide_num": 1,
      "title": "MIRA: First Autonomous AI Agent Operates Inside the EHR, Matches Physician Diagnosis",
      "key_claim": "First EHR-integrated autonomous AI agent evaluated on 500+ real emergency department cases (p.1)"
    },
    {
      "slide_num": 3,
      "title": "MIRA Scores 88.9% Diagnostic Accuracy, Beating Board-Certified Physicians at 78.1%",
      "key_claim": "88.9% vs 78.1% diagnostic accuracy on n=574 cases, McNemar P<0.001 (p.3, Fig.3a)"
    },
    {
      "slide_num": 5,
      "title": "From Chat-Only Advisors to EHR-Acting Agents: MIRA Closes the Workflow Gap",
      "key_claim": "Prior LLM tools stayed in chat or vignettes; MIRA turns clinical intent into structured FHIR operations (p.1-2)"
    },
    {
      "slide_num": 6,
      "title": "Four Honest Limits: Sandbox EHR, Retrospective Data, Narrow Case Set, No Live Oversight",
      "key_claim": "Authors explicitly call for prospective trials and active monitoring before deployment (p.1, p.7)"
    }
  ]
}
```

The full spec is in `/tmp/mira_carousel_measurement/spec.json` from
the original run; the full reviews in `reviews.json`; the rendered
PNGs in `slide_01.png` through `slide_07.png`; the assembled
deliverables in `MIRA_carousel.pdf` (10.2 MB) and
`MIRA_carousel.zip` (6.5 MB).

## Visual QA findings (vision model inspection)

| Slide | Score | Issues |
|---|---|---|
| 1 (title) | 5.3/10 | Reveals thesis in headline; duplicate DOI; "Hook:" labeled bullet; page-notations (p.1) inappropriate for LinkedIn |
| 2 (method) | 7.0/10 | Clean, bullets support method |
| 3 (headline) | 5.5/10 | Bar chart has no axes/labels/legend; z-order collision with bullets 3-4 |
| 4 (workflow) | 6.5/10 | Reasonable, but illustrations not labeled |
| 5 (trend) | 5.0/10 | Stages unlabeled (can't map to AMIE/MAI-DxO/Penda); MIRA not visually elevated; chat bubble is largest (inverts message) |
| 6 (limits) | 4.0/10 | **Hallucinated text inside cards**; text collision; cards unlabeled |
| 7 (implications) | 6.0/10 | Acceptable, page-notations present |

Average: 5.6/10. **Reason for low score: image-model-generated
visuals are the bottleneck, not the spec text.** Iteration 2
should: (a) suppress text in image gen prompts explicitly,
(b) draw charts in Pillow, (c) include image bytes in
reviewer prompts, (d) require reviewer scores to gate the
slide before assembly.

## Iteration 2 plan (not yet run)

1. Force "no text" in every image prompt
2. Draw slide 3's bar chart in Pillow with explicit bars + labels
3. Constrain image area to lower 50% of slides 3 and 5 (avoid bullet collision)
4. Add `response_format: {"type": "json_object"}` to all reviewer calls
5. Include rendered PNG bytes in every reviewer prompt
6. Gate: any reviewer score < 7 → regenerate that slide (max 2 attempts)
7. Re-measure wall-clock and cost

Expected improvement: average visual QA score from 5.6/10 to 7.5+/10.
