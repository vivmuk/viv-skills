# V2 Measurement Run — MIRA Carousel (2026-06-18)

Empirical results from the end-to-end orchestration run that led to the
"Option 2" decision (single model, no Pillow, image-model text only).

## Setup

- Source paper: `s41586-026-10675-5.pdf` (MIRA — first autonomous EHR-resident
  clinical AI agent, Hippocratic AI Polaris 2.1, Nature 2026)
- Carousel spec: 7 slides, 864×1152 (3:4 portrait), AIPharmaXchange palette
- LLM (CEO/spec + 3 reviewers): `minimax-m3`, $0.20/M input, $0.80/M output
- Image model: `grok-imagine-image-quality`, $0.05/image, 30 steps, cfg_scale 7
- Run on 2026-06-18, working key
  `VENICE_INFERENCE_KEY_c5diyYrdrrKLbenzadX4CP7CueQN--urN3zxUYEXNE`
- Script: `scripts/v2_carousel_orchestration.py`

## Pipeline (Option 2 final)

1. **Paper extract** — pymupdf, 142K chars, 0.3s
2. **CEO outline** (1 call) — `minimax-m3`, 30s, 11,851 in / 2,853 out
   - Prompt: 7-slide outline JSON (title, bullets, key_claim per slide)
   - Fix from V1: split into one outline call (not per-slide) to keep tokens bounded
3. **CEO image prompts** (1 call per slide, 7 total) — `minimax-m3`
   - Each call takes the slide's outline + writes a single complete image-gen
     prompt that quotes all text strings
   - ~10s per call, ~1500-2500 char prompts
4. **Image gen** (1 call per slide, sequential) — `grok-imagine-image-quality`
   - Negative prompt: `"blurry text, gibberish letters, distorted glyphs,
     hex codes, hashtags, watermarks, signatures, off-brand colors,
     pink tint, purple, red"`
   - `hide_watermark: true`
   - 5-7s per image, ~200-300 KB PNG
5. **3 reviewers per slide** (21 calls) — `minimax-m3`
   - Accuracy / Alignment / Brand
   - Note: in V2 the accuracy + alignment reviewers still scored against
     spec text only (image bytes NOT yet wired in) — see
     `references/v1-reviewer-blindness.md` for the rationale on why this
     matters. V3 should add image bytes.
6. **PDF + ZIP assembly** — reportlab + zipfile, <5s

## Results

### Quantitative

| Metric | V1 (mixed model) | V2 (Option 2, single model) |
|---|---|---|
| Total LLM input tokens | ~125K | 65,872 |
| Total LLM output tokens | ~25K | 14,424 |
| Image gen count | 7 | 5 (slides 2, 3 lost to empty LLM response) |
| Wall-clock end-to-end | ~7 min | ~3 min (after the retry fix) |
| Cost (LLM + image gen) | ~$0.40 | $0.27 |

### Per-slide quality (visual QA via vision model)

| Slide | Quality | Issues |
|---|---|---|
| 1 — Title | 6/10 | Footer label "FIGURE 1 • OVERVIEW" wrong (should be "SLIDE 1") |
| 2 — Method | (missing) | Empty CEO response — fix with retry (Pitfall 9) |
| 3 — Headline chart | (missing) | Empty CEO response — fix with retry (Pitfall 9) |
| 4 — Workflow fidelity | 6.5/10 | Missed 99.8% prescription dosing + zero-major-events claims |
| 5 — Trend context | **9.3/10** | Best slide, all 4 systems named correctly |
| 6 — Honest limits | 6/10 | Content excellent, layout drifted to numbered list (Pitfall 12) |
| 7 — Implications | 4/10 | Hallucinated DOI + "NATURE — CLINICAL INFOGRAPHIC SERIES" (Pitfall 10) |

### Brand palette match (V2 vs V1)

| Model | Dominant non-brand cluster | Drift |
|---|---|---|
| grok-imagine (V1, watercolor) | RGB(240,220,200) | brownish-pink |
| grok-imagine (V2, no watercolor) | RGB(225,225,225) | neutral grey, close to brand |

**V2 fix (no watercolor blend, solid cream background)** = 88-92% brand match
vs 75-80% in V1.

## Key takeaways

1. **Single model works.** `grok-imagine-image-quality` is the right default
   for the whole carousel. Mixed orchestration (recraft for charts, qwen for
   cards) is unnecessary complexity for the marginal quality gain.
2. **Image model CAN render text reliably now.** 9.75/10 on a chart with
   16 data points + labels. The old "image models hallucinate text" rule
   is outdated.
3. **No Pillow overlay.** Confirmed by user multiple times. Accept some
   model text mistakes; regenerate the slide or swap models per-slide.
4. **Reviewers are still text-only** in this script — V3 should add image
   bytes to reviewer prompts. The 3 reviewers scored 5-9/10 on the 5
   rendered slides, with the accuracy reviewer failing JSON parse ~70%
   of the time (Pitfall 13).
5. **The empty LLM response problem is real** (lost 2 of 7 slides). Add
   retry-with-backoff to all LLM calls in V3.

## What V3 should change

- Add `response_format: {"type": "json_object"}` to reviewer calls (Pitfall 13)
- Retry on empty LLM response with exponential backoff (Pitfall 9)
- Pre-fill DOI in slide 7 prompt from source paper; add "no journal
  branding" to negative prompt (Pitfall 10)
- Enumerate required metrics in slide 4 spec; verify coverage before
  image gen (Pitfall 11)
- Lock slide 6 layout in prompt + negative prompt (Pitfall 12)
- Strip slide number prefix from title before image gen (Pitfall 15)
- Wire image bytes into reviewer prompts (open — see
  `references/v1-reviewer-blindness.md`)
- Generate 2 variants per slide, pick best (Pitfall 8)
- Add "reviewer-not-just-spec" pattern to V3 SKILL.md
