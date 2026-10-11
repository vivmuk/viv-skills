---
title: AIPharmaXchange paper-reel pipeline blueprint
parent: ai-video-production
audience: agents producing paper-summary reels for the AI Pharma Xchange
---

# AIPharmaXchange paper-summary reel pipeline

**Empirical session**: 2026-07-02, planning against reference reel `vaibhavsisinty.explain` Nature Medicine summary.
**Plan file**: `~/.hermes/plans/aipharmaxchange-paper-reel-pipeline.md` (~25 KB, 600 lines, fully detailed).
**Status**: Plan approved (pending 7 decisions from user); Sprint 0 setup commands ready.

## Reference format (what we copy)

| Spec | Value |
|---|---|
| Format | 9:16 vertical, 720×1280 |
| Length | ~90s typical; reference reel was 102.65s |
| Layout | Talking head bottom ~30%; B-roll cycle upper ~70% |
| Cuts | Hard cuts every 4–7s, synced to narration sentence boundaries |
| Audio | Original VO + light BGM |
| CTA | "Comment [KEYWORD] and I'll DM the paper" |

The reference creator posts 1-3 reels/week on research papers with this exact format — a known-good template for "AI news for busy pharma pros."

## Six stages

### Stage 1 — Ingest ($0.01/paper)
- Input: arXiv ID / DOI / PDF URL / `pubmed:…` link
- Output: extracted Markdown + figure list + table data
- Source: Venice `/augment/text-parser` (PDFs, DOCX, XLSX, plain text) — runs in-memory with zero retention
- For arXiv: also call `/augment/scrape` on the abstract page for cite metadata

### Stage 2 — Analyze (1 LLM call, deepseek-v4-pro)
- Input: extracted text + figure captions
- Output: structured JSON via `response_format: json_object`:

```jsonc
{
  "title": "…",
  "authors": ["…"],
  "venue_year": "Nature Medicine 2026",
  "key_claim": "…",
  "supporting_evidence": [
    { "claim": "…", "section": "§3.2", "figure": "fig 4" }
  ],
  "implications": "…",
  "storyboard_seed": 42,
  "aesthetic": {
    "style": "scientific, clean",
    "palette": "navy + teal",
    "lighting": "soft chiaroscuro",
    "lens": "50mm cinematic",
    "film_stock": "warm Kodachrome-ish"
  }
}
```

Editorial rigor check: every `claim` in `supporting_evidence` must trace back to a `section` or `figure` in the source paper (per `editorial-rigor` skill — Type 2 thinking pass, accuracy pass, fair/balance pass, bias pass).

### Stage 3 — Storyboard (1 LLM call, deepseek-v4-pro)
- Input: analysis JSON + paper figures + series brand-aesthetic.json
- Output two files in parallel:
  - `episode.json` — shot list (see harness schema extension above)
  - `vo_script.json` — line-by-line narration:

```jsonc
{
  "lines": [
    {
      "id": "vo-1",
      "shot_ids": ["shot-1", "shot-2"],
      "text": "Hospitals pay serious money for specialized medical AI tools.",
      "duration_s": 4.5,
      "intensity": "neutral",
      "delivery_cue": "informative, slight edge"
    },
    { "id": "vo-2", "text": "…", "duration_s": 5.5, "intensity": "rising" }
  ],
  "total_duration_s": 90.0
}
```

The `shot_ids` field keys each line back to the B-roll shots that visually carry it — same as the harness `episode.json` `vo_segment_id`.

### Stage 4 — Generate (parallel where possible)
- For each non-talking-head shot in `episode.json`, infer the cheapest Spawn model:
  - I2V from paper figure → `seedance-2-0-image-to-video` (best for figure-callout shots where the figure IS the visual)
  - T2V from natural-language description → `seedance-2-0-text-to-video` (best for atmosphere / stat-card shots)
  - R2V when continuity matters (paper-logo lower-third, brand intro/outro) → `seedance-2-0-reference-to-video`
- Face anchor (Path A or B): R2V with `reference_image_urls` of the host portrait + audio donor.
- Stitch transitions between shots that share a visual thread → R2V `<Video 1> + dissolve + followed by <Video 2>`.
- Music: `minimax-music-v2` with prompt built from paper mood (e.g. "contemplative piano, warm low-pass filter, scientific curiosity, 90bpm").
- SFX: 2-4 `elevenlabs-sound-effects-v2` per reel — soft whoosh on cut, gentle chime on stat reveal, etc.
- All generations return `queue_id` → poll `/video/retrieve` until `video/mp4` or `application/json status=COMPLETED`.

### Stage 5 — Assemble
- The `video-editing` skill (from harness) reads `takes_packed.md` (~12 KB for 90s reel) and emits an EDL JSON. Snapshot of our EDL shape:

```jsonc
{
  "version": "v1",
  "created_at": "2026-07-02T14:30:00Z",
  "input": {
    "shots": ["shot-1.mp4", "shot-2.mp4", "shot-3.mp4", "talking_head.mp4"],
    "vo": "vo.wav",
    "music": "music_bed.mp3",
    "sfx": ["whoosh-1.mp3", "chime-1.mp3"]
  },
  "tracks": [
    {
      "id": "video-main",
      "kind": "video",
      "clips": [
        { "file": "shot-1.mp4", "in": 0.0, "out": 4.5, "transition": "cut" },
        { "file": "shot-2.mp4", "in": 0.0, "out": 5.0, "transition": "match-cut" },
        { "file": "shot-3.mp4", "in": 0.0, "out": 6.5, "transition": "cut" }
      ]
    },
    {
      "id": "video-talking-head",
      "kind": "video",
      "geometry": { "x": "(W-w)/2", "y": "H-h-H/4", "w": "W*0.7", "h": "H*0.28" },
      "clips": [
        { "file": "talking_head.mp4", "in": 0.0, "out": 90.0 }
      ]
    },
    {
      "id": "vo",
      "kind": "audio",
      "clips": [{ "file": "vo.wav", "in": 0.0, "out": 90.0, "gain_db": 0 }]
    },
    {
      "id": "music-bed",
      "kind": "audio",
      "clips": [{ "file": "music_bed.mp3", "in": 0.0, "out": 90.0, "gain_db": -12, "fade_in": 1.5, "fade_out": 3.0 }]
    }
  ],
  "overlays": [
    { "kind": "lower-third", "from": 1.0, "to": 4.0, "text": "Nature Medicine · 2026" },
    { "kind": "callout", "from": 35.0, "to": 41.0, "text": "100 real clinical questions" }
  ],
  "captions": [
    { "from": 0.5, "to": 5.0, "text": "Hospitals pay serious money for specialized medical AI tools.", "style": "subtitle-bar" }
  ],
  "cta_card": {
    "from": 84.0, "to": 90.0,
    "text": "Comment PAPER for the link",
    "style": "primary-cta"
  }
}
```

The harness `ffmpeg-overlay` agent renders the lower-thirds / callouts / CTA as `drawtext` filters; the geometry block above encodes what `f=…` expressions it should produce.

- The harness `cut-qa` agent then runs the 6 programmatic checks (aspect, audio peaks, lighting, caption overlap, VO truncation, frame hash). Max 3 fix iterations before fail.

### Stage 6 — Deliver
- `output/reels/<YYYY-MM-DD>-<slug>.mp4` — 720×1280, AAC audio, ~8 Mbps
- Sidecar files (always written):
  - `storyboard.json` — episode-level plan
  - `vo_script.json` — narration line-by-line with delivery cues
  - `edl.json` — the rendered edit decision list
  - `qa_report.json` — cut-qa results + editorial-rigor traces
  - `cost.json` — every USD spent (drives the spend ledger)
- Optional second/third auto-cuts:
  - YouTube Shorts: same 9:16 source, no re-cut
  - LinkedIn 1:1 video: re-frame top 70% B-roll, drop face PiP (use `ffmpeg crop=in_w/2:in_h/2:in_w/4:in_h/4`)
  - LinkedIn 1:1 carousel: render a static `grok-imagine-image-quality` poster per shot (~10x matches our existing carousel pipeline)

## Aesthetic prefix / book-end

From the harness's `venice-ui-production` mental model — but for our use case, `aesthetic.json` is the single source of truth. One file, threaded into every prompt:

```jsonc
{
  "version": "aipharmaxchange-default-v1",
  "style": "scientific, modern, clean editorial",
  "palette": ["navy #1a2942", "teal #2c7a7b", "off-white #f8f4e9", "warm accent #c08552"],
  "lighting": "soft chiaroscuro, key from upper-left, fill from below",
  "lens": "50mm cinematic, shallow DoF",
  "film_stock": "warm Kodachrome, gentle grain",
  "frame_chaining": {
    "default_transition": "match-cut-on-subject",
    "longest_pause_s": 4.5
  },
  "caption_style": "subtitle-bar",
  "lower_third_palette": ["f8f4e9", "1a2942"],
  "cta_card": {
    "background": "#1a2942",
    "text": "Comment PAPER for the link",
    "font": "/Library/Fonts/Arial Unicode.ttf",
    "fontsize": 36
  }
}
```

For each prompt, build:

```
PREFIX (front-load every image / video prompt):
  STYLE: scientific, modern, clean editorial. navy + teal + off-white + warm accent. soft chiaroscuro, key from upper-left. 50mm cinematic, shallow DoF. warm Kodachrome, gentle grain.

BOOKEND (paste at end every image / video prompt):
  STYLE REMINDER: navy + teal, soft chiaroscuro, 50mm, Kodachrome.
```

## Voice clone onboarding (Path B)

One-time, before the first reel:

```bash
# 1. Record a 10-second sample of neutral narration to /tmp/voice-sample.wav
#    (read a single sentence, neutral tone, clean mic)
# 2. Upload to Venice
VOICE_ID=$(
  curl -s https://api.venice.ai/api/v1/audio/voices \
    -H "Authorization: Bearer *** \
    -F "model=tts-chatterbox-hd" \
    -F "file=@/tmp/voice-sample.wav" | jq -r .id
)
# Save $VOICE_ID to ~/.hermes/voice-clones/<name>.txt — re-upload every 7 days
echo "$VOICE_ID" > ~/.hermes/voice-clones/host-default.txt
```

`voice-cloning` is the right place to note: per-Venice docs, "the model reads the uploaded reference each time you synthesize speech. No persistent voice template is created." So the file on disk is a re-upload trigger, not a model artifact.

## Cost optimization passes (apply after first reels)

1. **Series-level reuse**: build a per-series music bed once via `minimax-music-v2`, reuse the same MP3 across all reels in the series. One-time $0.50 → amortized $0.05/reel over 10 reels.
2. **Shot-count pruning**: figure-callout shots driven by paper figures (I2V from `/augment/text-parser` extracted figure) often look better than ATMO shots driven by text. Aim for ≥50% I2V-from-figure.
3. **Reuse the host voice handle** — one upload covers all reels within a 7-day window.
4. **Drop B-roll count from 9 → 6** if reels feel choppy. Voice timing is what matters most for engagement.
5. **Use `seedance-2-0-fast-*` for previews**, full-quality for the final render only. Saves 50% on draft runs.

## Build sequence (operator-runnable)

Sprint 0 (~45 min, no creative work):

```bash
git clone https://github.com/jordanurbs/venice-video-harness.git ~/.venice-video-harness
cd ~/.venice-video-harness && cp .env.example .env
brew install whisper-cpp
curl -L -o ~/.cache/whisper.cpp/ggml-base.en.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin
npm install && npm run build
# Add VENICE_API_KEY=*** to .env
```

Sprint 1 (vertical slice, ~3-4 hours): three B-roll clips + hand-written EDL + ffmpeg assembly. Reviews produce a `reel-N01-smoke.mp4`. **Sign-off gate** before Sprint 2.

Sprint 2 (~4-6 hours): wire the harness's `produce-episode` to skip its UI-flow and call our `paper_to_storyboard.py` upstream. Add `paper-reel.md` custom command.

Sprint 3 (~3-4 hours): editorial-rigor + spend-ledger + kanban integration. "Drop paper ID, walk away, get a cleared reel."

## 7 decisions still pending user sign-off (from 2026-07-02 plan)

1. Talking-head path: A (recorded VO, ~10 min/paper) or B (cloned voice, fully hands-off)? *Default: A first.*
2. First paper: NYU Langone Nature Medicine paper (`vaibhavsisinty.explain`'s reference) or another open-access pharma paper?
3. Brand aesthetic seed: `aesthetic.json` already exists in `~/.paperclip/workspaces/aipharmaxchange/`? If not, OK with the proposed navy/teal/soft chiaroscuro/50mm defaults?
4. Cadence: 1/week (low-touch), 1/day (heavy), or on-demand?
5. Output platforms: IG Reels is lead. Which auto-cuts? (YouTube Shorts, LinkedIn 1:1 video, LinkedIn 1:1 carousel, X 9:16)
6. Spend posture: is the $10/day ledger cap a hard ceiling? (If yes → throttle to 2-3 reels/week.)
7. Voice clone consent: Path B clones the user's voice from a 5–10s recording. Acceptable?

Once approved, kick Sprint 0 immediately with the install snippet above.
