---
name: ai-video-production
version: 0.1.0
description: 'End-to-end agent-driven AI video production on Venice: paper-summary reels, talking-head explainers, brand-strip series. Covers the full stack — Seedance 2.0 four-workflow R2V (Reference / Edit / Extend / Stitch), voice cloning with Chatterbox HD, music / SFX / TTS, ffmpeg-overlay + cut-qa finishing pipeline, and adoption of the community-maintained Venice Video Harness. Use when the user asks for a video reel, paper reel, paper summary video, explainer video, talking head video, brand video, AI video pipeline, Venice video, Seedance, reference-to-video, paper trailer, or research narration.'
tags:
  - video
  - venice
  - seedance
  - ai-video
  - reels
  - talking-head
  - paper-explainer
  - tts
  - voice-cloning
  - ffmpeg
  - harness
  - mini-drama
triggers:
  - video reel
  - paper reel
  - paper summary video
  - explainer video
  - talking head video
  - brand video
  - ai video pipeline
  - venice video
  - seedance
  - reference to video
  - paper trailer
  - research narration
related-skills:
  - model-routing
  - editorial-rigor
  - social-carousel-generation
---

# AI Video Production (Venice-first)

## What this skill covers

Agent-driven production of vertical 9:16 social videos (Instagram Reels, YouTube Shorts, X, LinkedIn 1:1) AND long-form cinematic content, using Venice's video-generation stack end-to-end.

Core use case — paper-explainer / paper-summary reels (the `@vaibhavsisinty.explain` format):
- Real OR cloned-voice narration over a 90-second vertical
- Talking-head portrait anchored bottom of frame
- B-roll clips (paper figures, citations, headline graphics) cycle through the upper ~70% with hard cuts synced to narration sentences
- Background music + transition SFX
- Lower-thirds + CTA card overlay

Also covers: brand-strip series, talking-head explainers without B-roll, lifestyle reels, storyboard-to-video workflows.

## Stack overview (June 2026)

| Layer | What | Source |
|---|---|---|
| Video gen | seedance-2-0-{text,image,reference}-to-video + seedance-2-0-fast-* + Grok Imagine Private | Venice `/api/v1/video/queue` |
| Voice cloning | tts-chatterbox-hd — upload 5–10s sample → `vv_…` handle (zero-shot, 7-day expiry) | Venice `/api/v1/audio/voices` + `/audio/speech` |
| Off-the-shelf TTS | tts-kokoro (50+ voices), tts-qwen3, elevenlabs-tts-v3 | Venice `/api/v1/audio/speech` |
| Music | minimax-music-v2, ace-step-15, stable-audio-25, elevenlabs-music | Venice `/api/v1/audio/queue` |
| SFX | elevenlabs-sound-effects-v2, mmaudio-v2-text-to-audio | Venice `/api/v1/audio/queue` |
| Topaz upscale | 2× / 4× resolution on generated videos | Venice `/api/v1/video/queue` model `topaz-video-upscale` |
| Image (still) | grok-imagine-image-quality (slides), seedream-v5-lite (character panels), nano-banana-pro (atmosphere) | Venice `/api/v1/image/generate` |
| Finishing | ffmpeg concat + drawtext lower-thirds + 30ms audio fades + Remotion (animated overlays) | local |
| QA | cut-qa: 6 programmatic checks per cut (aspect, audio peaks, lighting, caption overlap, VO truncation, frame hash) | harness `src/editing/` |
| Meta-orchestration | Venice Video Harness (community, MIT) — wraps 50+ models with 19 commands, 10 agents, 7 skills | github.com/jordanurbs/venice-video-harness |

This stack is **complete** — no external video API is required. Adopt the harness as the spine; build only the domain-specific adapter on top.

## When to use each video model (decision tree)

1. Character anchor / talking head across shots → `seedance-2-0-reference-to-video` (R2V Reference workflow). Lock face via `reference_image_urls`.
2. 3+ characters in one shot → `kling-o3-standard-reference-to-video` (auto-fallback in harness; structured `elements` keeps identities separate).
3. Establishing / mood / atmosphere with no characters → `seedance-2-0-image-to-video`. Drive from a still (e.g. `seedream-v5-lite` panel).
4. Pure B-roll from a prompt only → `seedance-2-0-text-to-video` (cheapest option).
5. Cheap draft / preview → `seedance-2-0-fast-*` variants (lower fidelity, faster).
6. Lip-sync to a specific voiceover → R2V with `reference_audio_urls` paired with `reference_image_urls` (audio-only is rejected).
7. Polish / extend an existing clip → R2V with `Extend <Video 1>, …` workflow.
8. Stitch 2–3 clips with AI transitions → R2V with `<Video 1> + <transition> + followed by <Video 2> + …`.
9. Modify one element of a clip → R2V with `Strictly edit <Video 1>, changing its …`.

**Aspect ratio**: T2V / R2V accept `aspect_ratio`. I2V derives from input image — pass it width × height to match.

## Pricing snapshot (USD per generation)

Re-quote live before every batch — never cache. Sanity defaults:

| Model family | 5s | 10s | 15s |
|---|---|---|---|
| Seedance 480p | ~$0.44 | ~$0.88 | ~$1.32 |
| Seedance 720p | ~$0.95 | ~$1.89 | ~$2.84 |
| Seedance 1080p | ~$2.34 | ~$4.68 | ~$7.02 |
| Seedance R2V (≈ +22%) | 5s 720p $1.16 | 10s 720p $2.09 | 15s 720p $3.13 |
| Grok Imagine Private | $0.44 / $0.89 / $1.33 | — | — |

Full matrix + quote procedure in `references/seedance-2-pricing.md`.

**Cost levers** (priority order):
1. Drop clip count from 9 → 6 (~30% cheaper) before downgrading resolution.
2. Stay at 720p for IG-native sizes; 1080p only when platform demands.
3. Reuse one music bed across an entire series — first creation only.
4. Reuse one cloned-voice handle (free; expires after 7 days, re-upload).
5. Use `seedance-2-0-fast-*` for previews/drafts, full-quality for final render.

## Talking-head paths (which to ship first)

| Path | What | Cost per reel | Quality | Effort per paper |
|---|---|---|---|---|
| A. Real recorded VO | You read the script; Seedance 2.0 i2v animates a static portrait of you synced to your audio | ~$13 at 720p | ★★★★★ | ~10 min recording |
| B. Cloned voice + R2V face | Clone your voice once (5–10s sample) → Chatterbox HD TTS → Seedance 2.0 R2V with `reference_audio_urls` for lip-sync | ~$13.30 at 720p | ★★★★☆ | ~0 min (hands-off) |
| C. Pure TTS + dense B-roll, no face | TTS narration only, drop on-camera | ~$11 | ★★★☆☆ | ~0 min |

**Default**: ship Path A first to validate format; switch to Path B once the motion and aesthetic are signed off. Path C is the always-on fallback.

## Pipeline pattern (paper → reel)

Six stages that always apply:

```
[paper.pdf/URL]
   ↓ Stage 1 — Ingest
   Venice /augment/text-parser → extracted Markdown + figure list ($0.01)
   ↓ Stage 2 — Analyze
   LLM → { title, key_claim, evidence, implications }
   ↓ Stage 3 — Storyboard
   LLM → episode.json (shot list) + vo_script.json (line-by-line VO with durations)
   ↓ Stage 4 — Generate (parallel where possible)
   Venice /video/queue: T2V/I2V/R2V per shot + face shot + transitions
   Venice /audio/queue: TTS (cloned VO) + music bed + 2-4 SFX
   ↓ Stage 5 — Assemble
   LLM reads takes_packed.txt, emits EDL JSON
   ffmpeg concat: B-roll strips + face PiP bottom + VO track + music (-12 dB) + lower-thirds + callouts + CTA
   cut-qa 6-check pass
   ↓ Stage 6 — Deliver
   final.mp4 720×1280 AAC ~8 Mbps + sidecar (storyboard.json, edl.json, qa_report.json, cost.json)
```

Concrete AIPharmaXchange blueprint (EDL shape, aesthetic prefix / book-end, voice clone onboarding, brand-aesthetic.json shape, cut-qa integration, cost optimization passes) lives in `references/paper-reel-pipeline.md`.

## Always do these (workflow gates)

- **Rate-limit pre-flight before any batch** (≥5 calls). See `model-routing` skill — `GET /api/v1/api_keys/rate_limits` then `Authorization: Bearer *** then honor RPM / TPM / RPD / TPD + imageGenerationsPerDay + videoGenerationsPerDay. **Even research queries count** — the failure mode is "burned through $13 in pricing probes before the real run."
- **Re-quote at every batch start.** Pricing details are not cached in agents — `/video/quote` is the only authoritative source. Always pass `reference_video_total_duration` if including reference videos, or quote and queue will diverge.
- **Spend ledger.** Increment `/tmp/aipharmaxchange_spend/spend_{date}.json` per successful generation.
- **Editorial rigor.** Every claim in the VO must trace to a paper section/figure (per `editorial-rigor` skill). Trace belongs in `qa_report.json`.
- **cut-qa pass before publishing.** Six checks, max 3 fix iterations. Reroute problem transitions through R2V Stitch or R2V Edit, not hard cuts.

## Pitfalls (these have fired)

- **Seedance face rule**: face-bearing images must be produced by `seedream-v5-lite` or `seedream-v5-lite-edit`, or Seedance rejects them. Harness has a pre-flight gate; if bypassing the harness, route all character images through Seedream first.
- **I2V ignores aspect_ratio** — passing it to `seedance-2-0-image-to-video` returns 400. Output aspect is auto-derived from input image dimensions; pre-crop the input to 9:16 if needed.
- **Reference audio alone is rejected.** R2V requires at least one image OR video reference alongside any `reference_audio_urls`. Pair them — audio-only submissions 400.
- **Prompt routes to wrong workflow.** Inferred from prompt syntax: `Refer to …` → Reference; `Strictly edit …` → Edit; `Extend …` → Extend; `<Video 1> + … + followed by <Video 2>` → Stitch. Wrong prefix = wrong task. Use canonical prefixes verbatim (angle brackets, capital first letter, single space before number).
- **Total reference duration cap is 15s.** Larger clip sets need a Stitch first (3 → 1), then use output as follow-up reference.
- **`reference_video_total_duration` mismatch on quote.** If you forget to pass it to `/video/quote`, the quote and the queued amount diverge.
- **Grok Imagine Private returns `download_url`** that expires in 24h and is single-purpose. Persist it at queue time, `GET` from one network, save locally, then `DELETE` if you want it invalidated.
- **Voice handles expire in 7 days.** Plan re-upload cadence for ongoing series.
- **drawtext anti-patterns** (per harness `ffmpeg-overlay` skill): no `letter_spacing` (rejected by ffmpeg), always escape `%` as `\%`, prefer `textfile=` over `text=` for shell-unsafe characters.

## Venice Video Harness — adopt, don't reinvent

Always **clone** the harness before building bespoke orchestration:

```bash
git clone https://github.com/jordanurbs/venice-video-harness.git ~/.venice-video-harness
cd ~/.venice-video-harness && cp .env.example .env
# Add VENICE_API_KEY=*** to .env
brew install whisper-cpp
curl -L -o ~/.cache/whisper.cpp/ggml-base.en.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin
npm install && npm run build
```

What you get (`venice-video-harness` v2.3+):
- 19 workflow commands (`produce-episode`, `storyboard-episode`, `storyboard-all`, `edit-footage`, `generate-trailer`, `add-character`, `lock-character`, `workshop-episode`, …)
- 10 specialized agents (`art-director`, `prompt-engineer`, `cut-qa`, `overlay-designer`, `ffmpeg-overlay`, `remotion-overlay`, `screenplay-reader`, `storyboard-assembler`, `storyboard-qa`, `trailer-curator`)
- 7 production skills (`venice-api`, `venice-video-model-routing`, `character-consistency`, `shot-composition`, `video-editing`, `burn-in-subtitles`, `venice-ui-production`, `screenplay-parsing`)
- NLE round-trip export to Final Cut Pro XML / Premiere / DaVinci Resolve XML
- Text-first editing pipeline: LLM reads `takes_packed.md` (~12 KB / 40 min audio), never dumps frames

Skip the harness's `venice-ui-production` skill — that is the manual web-UI flow, not applicable to API-driven agent runs. Drive the harness's `src/venice/*` TypeScript directly.

Full inventory in `references/venice-video-harness.md`.

## Files this skill points to

- `references/seedance-2-pricing.md` — full per-resolution/per-variant Seedance 2.0 + Grok Imagine Private pricing matrix, plus the live-quote procedure.
- `references/venice-video-harness.md` — component-by-component inventory: 19 commands, 10 agents, 7 skills, src/ layout, schema names, "skip this skill" callouts.
- `references/paper-reel-pipeline.md` — the AIPharmaXchange paper-reel blueprint: EDL JSON shape, aesthetic prefix / book-end system, voice clone onboarding, brand-aesthetic.json shape, cut-qa integration, cost optimization passes.

## Companion skills (load alongside this one)

- `model-routing` — Venice rate-limit pre-flight and spend ledger (HARD requirement before any batch).
- `editorial-rigor` — Pre-publish checklist (every claim traceable to source).
- `social-carousel-generation` — sibling static-image pipeline; share EDL / aesthetic.json conventions.