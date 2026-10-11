# Model Comparison: Text Rendering on MIRA Carousel (2026-06-18)

> ⚠️ **SUPERSEDED by V2 (2026-06-18, same day).** This file recommends
> mixed-model orchestration (`recraft-v4-pro` for charts, `qwen-image-2`
> for cards). The V2 measurement run (`v2-measurement-run.md`) ran a
> single-model head-to-head on the same slides and found that
> `grok-imagine-image-quality` for ALL slides won on cost ($0.05 vs
> $0.08), speed (5-7s vs 26s), and avoided `recraft-v4-pro`'s
> fabricated-numbers bug. **The V2 default is `grok-imagine-image-quality`
> for everything.** This file is kept for historical context and to
> document the empirical test, not as an active recommendation.

## Setup

3 candidate image models on Venice API, tested on 2 representative slide types from the MIRA carousel (Nature 2026, Ferber et al.):

- **Slide 3** — Bar chart with 8 conditions × 2 series = 16 data points, labeled axes, legend, footer citation
- **Slide 6** — 2×2 grid of 4 cards, each with header + body text, plus title and footer

Each slide had explicit text quoted in the prompt. No Pillow text overlay. Models generated 864×1152 PNGs at 30 steps, cfg_scale 7.

## Results

### Slide 3 (bar chart with text)

| Model | Title | Chart labels | Legend | Footer | Score | Brand match |
|---|---|---|---|---|---|---|
| `ideogram-v4` | ✓ perfect | ✗ 7/8 (duplicates, merges) | ✗ hallucinated ("Diagnosif physich") | minor extra text | 5/10 | 88.6% |
| `recraft-v4-pro` | ✓ perfect | ✓ all 8, accurate numbers | ✓ correct | ✓ correct | **9/10** | **98.1%** |
| `qwen-image-2` | ✓ perfect | mostly ✓, one number replaced with "Physician" word | ✓ correct | minor typo ("edprtmen") | 7/10 | 89.4% |

**Issue with recraft:** fabricated UTI physician value (88.0% when paper says 68.9%). The accuracy reviewer must catch this kind of model invention.

### Slide 6 (2×2 limitations cards)

| Model | Card headers | Body texts | Footer | Score | Brand match |
|---|---|---|---|---|---|
| `ideogram-v4` | ✓ all 4 | ✓ all 4 readable | ✓ exact | **10/10** | 93.0% |
| `recraft-v4-pro` | ✓ all 4 | ✗ 2/4 have misspellings ("relininal", "reveil") | minor comma | 5/10 | 97.8% |
| `qwen-image-2` | ✓ all 4 | ✓ all 4 readable | ✓ exact | **10/10** | 82.9% |

**Speed:** `qwen-image-2` 5.7s, `ideogram-v4` 12-19s, `recraft-v4-pro` 26s.

## Verdict

| Model | Slide 3 | Slide 6 | Brand | Speed | Best for |
|---|---|---|---|---|---|
| `qwen-image-2` | 7/10 | 10/10 | 83-89% | 5.7s | **All-rounder** (cards, title, timeline) |
| `ideogram-v4` | 5/10 | 10/10 | 88-93% | 12-19s | Card work, fails on charts |
| `recraft-v4-pro` | **9/10** | 5/10 | **97-98%** | 26s | **Data viz** (charts, brand-perfect) |

**Recommended orchestration:** mixed per slide — `recraft-v4-pro` for chart slides, `qwen-image-2` for everything else.

## Why This Matters

The MIRA carousel V1 used `grok-imagine-image-quality` for all 7 slides. Result:
- Slide 3: bar chart with no axes, no labels, no legend (decorative only)
- Slide 5: 4 unlabeled watercolor stages, reader can't map to AMIE/MAI-DxO/Penda/MIRA
- Slide 6: hallucinated text inside cards ("One mec coce card feels cocd opbasteri")

None of the 3 reviewers caught this because they only saw the slide spec text, not the rendered PNGs. **The model selection is the primary fix; image-aware reviewers are the safety net.**

## Brand Color Drift Detail

Sampling dominant pixel clusters:

| Model | Dominant cream cluster | Drift |
|---|---|---|
| `qwen-image-2` | RGB(250,225,225) | drifts warm/pink |
| `ideogram-v4` | RGB(225,225,225) | drifts neutral grey |
| `recraft-v4-pro` | RGB(250,250,250) | **closest to pure cream** |
| `grok-imagine` (V1) | RGB(240,220,200) | drifts brownish-pink |

**Root cause:** hex codes in prompts (`#F5F0E1`) are interpreted as vibe-words by diffusion models, not literal RGB. Use color names + layout description instead.
