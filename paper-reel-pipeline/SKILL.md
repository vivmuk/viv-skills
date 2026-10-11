---
name: paper-reel-pipeline
version: 1.0.0
description: Produce vertical 9:16 paper-summary Instagram-style reels. Uses Venice API (Seedance 2.0 T2V/I2V/R2V + Grok Imagine Private + chatterbox voice-cloning) over the Venice Video Harness as orchestration backbone. ONLY runs when the user provides an explicit paper + go signal — never auto-generates.
tags: [video, venice, paper-summary, insta-reels, talking-head, seedance, harn]
triggers:
  - paper reel
  - paper video
  - paper trailer
  - explainer video
  - make a reel
  - video for this paper
  - aipharmaxchange reel
  - run paper-reel
  - vaibhavsisinty-style
  - paperclip video
  - talking head reel
---

# AIPharmaXchange Paper Reel Pipeline

A pre-approved, ready-to-run pipeline for producing **90-second vertical paper-summary reels** in the style of `@vaibhavsisinty.explain` (research-paper explainers with talking head at bottom + B-roll cycle above, 4–7s hard cuts synced to narration).

> **Hard rule: do not generate anything until the user provides a paper AND an explicit go signal** (e.g. "make it", "ship it", "render the reel"). This skill is a recipe — not a scheduler.

---

## 1. Reference format (the target)

| Spec | Value |
|---|---|
| Resolution | 720 × 1280 (9:16 vertical) |
| Length | 90–105 s |
| Layout | Talking head anchored bottom ~30% of frame; B-roll cycles upper ~70% |
| Cut cadence | Hard cuts every 4–7 s, aligned to sentence boundaries in the VO |
| Audio | Original VO + light BGM bed + 2–3 transition SFX |
| CTA | "Comment [KEYWORD] for the paper" overlay in last 6–8 s |
| Bottom-third | "Journal · Year" + paper title visible at start |

Plan file (long-form, ~25 KB): `~/.hermes/plans/aipharmaxchange-paper-reel-pipeline.md`

---

## 2. Pipeline architecture (5 stages)

```
paper.pdf / arxiv-id / journal-URL
    │
    ▼ [Venice /augment/text-parser, $0.01]
Stage 1 — INGEST    extracted Markdown + figure URLs + table data
    │
    ▼ [model: deepseek-v4-pro]
Stage 2 — ANALYZE   JSON: title, authors, venue_year, key_claim,
                    supporting_evidence, implications
    │
    ▼ [model: deepseek-v4-pro, plus aesthetic.json]
Stage 3 — STORYBOARD 9–12 shot episode.json + line-by-line vo_script.json
    │
    ▼ [Venice /video/queue]
Stage 4 — GENERATE  B-roll (T2V / I2V / R2V-Stitch),
                    Face-anchor (R2V i2v audio donor for talking head),
                    TTS (chatterbox-cloned voice),
                    music bed (minimax-music-v2),
                    SFX transitions (elevenlabs-sound-effects-v2)
    │
    ▼ [Harness video-editing skill + ffmpeg concat + cut-qa]
Stage 5 — ASSEMBLE  EDL JSON → ffmpeg concat: clips + face PiP +
                    VO + music + lower-thirds + callouts + CTA + subtitles.
                    cut-qa runs 6 programmatic pre-flight checks.
    │
    ▼
final.mp4 720×1280 + storyboard.json + vo_script.json + edl.json +
qa_report.json + cost.json
```

---

## 3. Venice API — confirmed endpoints + pricing (live 2026-06)

`docs.venice.ai` reference + `/video/quote` numbers (cloned at `/tmp/api-docs/`).

| Endpoint | Model | Use | 9:16 pricing (USD) |
|---|---|---|---|
| `POST /video/queue` | `seedance-2-0-text-to-video` | Pure B-roll clips | 5s/720p: $0.95 · 10s: $1.89 · 15s: $2.84 |
| `POST /video/queue` | `seedance-2-0-image-to-video` | Animate a figure/screenshot | identical to T2V |
| `POST /video/queue` | `seedance-2-0-reference-to-video` | One model, **4 workflows** (Reference / Edit / Extend / **Stitch**) inferred from prompt shape | 5s/720p: $1.16 · 10s: $2.09 |
| `POST /video/queue` | `grok-imagine-text-to-video-private` | Cheap fallback B-roll (private download URL) | 5s: $0.44 · 10s: $0.89 · 15s: $1.33 |
| `POST /video/quote` | any video model | Always quote before batch — never cache | returns `{"quote": <USD>}` |
| `POST /video/retrieve` | `model` + `queue_id` | Poll until `Content-Type: video/mp4` | included in queue cost |
| `POST /video/complete` | `model` + `queue_id` | Cleanup (optional) | — |
| `POST /audio/speech` | `tts-kokoro` / `tts-qwen3` / `elevenlabs-tts-v3` | Narration VO (off-the-shelf voices) | TTS-tier |
| `POST /audio/voices` (multipart) | `tts-chatterbox-hd` | **Clone your voice**: 5-10s sample → `vv_…` handle | zero-shot; 7-day expiry |
| `POST /audio/speech` | `tts-chatterbox-hd` + cloned `voice` | Use cloned handle to generate | TTS-tier |
| `POST /audio/queue` | `minimax-music-v2` | Background music bed | quote per call |
| `POST /audio/queue` | `elevenlabs-sound-effects-v2` | Transition SFX (2–3 per reel) | quote per call |
| `POST /image/generate` | `grok-imagine-image-quality` | Static title cards, citation graphics | known good |
| `POST /augment/text-parser` | — | Paper PDF → Markdown | $0.01/call |
| `GET /api_keys/rate_limits` | — | **Run before every batch** (user mandate 2026-06-28) | free |

**Seedance 2.0 reference-to-video canonical prompt prefixes (case-sensitive):**
- Reference: `Refer to <Subject N> in <Image N> to generate ...`
- Edit: `Strictly edit <Video 1>, changing its ...`
- Extend: `Extend <Video 1>, generate ...` (or `Extend <Video 1> backward, ...`)
- **Stitch**: `<Video 1> + <transition description> + followed by <Video 2> + ...`

**Seedance face rule**: face-bearing input images must originate from `seedream-v5-lite` or `seedream-v5-lite-edit`, or the request is rejected. Always pipe character work through Seedream first.

---

## 4. Tool stack

| Layer | What | Where |
|---|---|---|
| Orchestration backbone | **Venice Video Harness** v2.3 (MIT) | `~/.venice-video-harness/` (clone from `github.com/jordanurbs/venice-video-harness`) |
| Stitching / concat / drawtext | `ffmpeg` + `ffprobe` | `brew install ffmpeg` |
| Local transcription (VO timing alignment) | `whisper-cpp` + `ggml-base.en.bin` | `brew install whisper-cpp` + HuggingFace model download |
| Reference clip download (if needed) | `yt-dlp` | `brew install yt-dlp` |
| Capture / scoring | `browser` tool + `yt-dlp` | already on Hermes |
| LLM (analysis, storyboard, EDL) | `deepseek-v4-pro` ($1.73/$3.80 per 1M, 1M ctx) | routed via Venice |
| Image gen (carousels, title cards) | `grok-imagine-image-quality` ($0.05/img, 6.7s) | routed via Venice |
| Image gen (face-bearing, Seedance-compatible) | `seedream-v5-lite` or `seedream-v5-lite-edit` | routed via Venice |

Already on the Hermes box (verified 2026-07-02): `brew`, `python3 3.11.15`, `node`. Confirmed missing and now installed: `ffmpeg`, `yt-dlp`, `node (managed)`.

---

## 5. The hidden gem — Harness pieces we adopt

`/tmp/venice-video-harness/` (cloned for inspection) contains:

- `.claude/commands/` — 19 workflow commands; **`produce-episode`** + a custom **`paper-reel.md`** we will author
- `.claude/agents/` — **`cut-qa`** (6 pre-flight checks: aspect, audio peaks, lighting continuity, caption overlap, VO truncation, frame hash), **`ffmpeg-overlay`** + **`remotion-overlay`**, **`overlay-designer`** (parallel sub-agents), **`prompt-engineer`**, **`art-director`**, **`screenplay-reader`**
- `.claude/skills/` — **`venice-ui-production`** (shot-listing convention), **`video-editing`** (text-first EDL; LLM reads `takes_packed.md`, never raw video), **`burn-in-subtitles`** (caption overlay + text-safety rules), **venice-api**, **venice-video-model-routing**, **character-consistency**, **shot-composition**

**Bypass**: `venice-ui-production` is for the manual web-UI flow — we drive everything through `src/venice/queue.ts` instead.

---

## 6. Talking-head path — three options

| Path | Workflow | Pros | Cons |
|---|---|---|---|
| **A. Real-recorded VO + animated still face** (default) | You record the script → drop onto your static portrait → Seedance 2.0 R2V i2v with audio donor animates lips/head | Highest quality, on-brand, audience trust | You record every script (~10 min/paper) |
| **B. Voice clone (`tts-chatterbox-hd`) + Seedance R2V still face with audio donor** | Upload 5-10s sample once → clone handle valid 7 days → TTS each script → Seedance drives lip-sync from `<Audio 1>` donor | Fully hands-off, scale 5+ reels/day | ~10% quality gap vs recorded |
| **C. TTS voice-only (no face) + dense B-roll** | TTS only, omit face PiP | Fastest, lowest cost | No on-camera anchor = lower IG engagement |

**Recommended order: A → B → C.** Switch A→B once you trust the pipeline. C is the always-on fallback.

---

## 7. Cost per reel (720p, 9 B-rolls + face + stitch + music + SFX)

| Component | Cost | Cumulative |
|---|---|---|
| 9 B-roll (R2V 5s/720p) | $10.44 | $10.44 |
| Face anchor (R2V 5s/720p i2v audio donor) | $1.16 | $11.60 |
| R2V Stitch transition (5s/720p) | $1.16 | $12.76 |
| Music (minimax-music-v2, ~90s) | ~$0.50 | $13.26 |
| 4 SFX transitions | ~$0.80 | $14.06 |
| TTS narration (Path A) | n/a | $14.06 |
| TTS narration (Path B) | ~$0.30 | $14.36 |
| LLM calls (3 × deepseek-v4-pro) | ~$0.15 | $14.51 |
| **Total Path A** | | **~$14.50/reel** |
| **Total Path B** | | **~$14.80/reel** |

Optimized (6 B-rolls, reused music, Fast variants where applicable): **<$8/reel**.

**Hard ceiling: `~/.hermes/config.yaml → custom_providers → venice → api_key` daily ledger at `/tmp/aipharmaxchange_spend/spend_{date}.json`** — user directive 2026-06-28 caps Venice spend at **$10/day**. Throttle to **2–3 reels/week**. Use `/api_keys/rate_limits` headroom tests + re-pool when **any `remaining` counter drops below 10%**.

---

## 8. Build sprints (executed only when the user gives a paper + green-light)

| Sprint | Time | Goal | Gate to next |
|---|---|---|---|
| **0. Setup** | ~45 min | `git clone` harness, `brew install whisper-cpp + cpp`, `npm install && npm run build`, sanity-check Venice `/video/quote` | Toolchain boots |
| **1. Vertical slice** | ~3–4 h | One paper → one finished 90s reel (3 B-rolls only) | User reviews smoke reel, signs off aesthetic |
| **2. Harness integration** | ~4–6 h | Author `paper_to_storyboard.py`, extend `episode.json` schema (`kind` field), add `.claude/commands/paper-reel.md` | Re-run Sprint 1 through new command |
| **3. Editorial + ops** | ~3–4 h | Hook `editorial-rigor` checklist, rate-limit pre-flight, spend ledger, kanban integration | "Drop paper ID, walk away" |

---

## 9. Trigger phrases — what the user pastes next time

If you want to start a reel, just say any of:

- `make a reel for <arxiv-id | DOI | PDF URL | journal-article-URL>`
- `paper-reel on <paper>`
- `build the video for this paper: <link>`
- `video-summary this for me: <paper-title>`
- `run the paper-reel pipeline on <paper>`
- `ship a reel for <id>`

…and follow-on decisions to make in the first message if you can:

| Decision | Default if you don't specify |
|---|---|
| Talking-head path | A (you record) |
| Output resolution | 720p (IG-native; skip 1080p) |
| Reel length | match reference: ~90–105s, 9–12 shots |
| Aesthetic | navy/teal palette, soft chiaroscuro, 50mm cinematic — tweakable per paper |
| Music / SFX | auto |
| Cadence | on-demand (no auto-batch) |
| Platforms auto-cut | IG Reels only (others: say "also LinkedIn 1:1" etc.) |
| Publish target | deliver MP4 to chat — **never auto-publish** |

If you specify Path B, record a 5–10s sample of your voice before Sprint 1 starts.

---

## 10. Pre-flight hook order (every batch)

Per user mandate 2026-06-28 — run **before** any >5-call Venice job:

```bash
KEY="$(awk '/^- name: venice/{f=1} f && /api_key:/{print $2; exit}' ~/.hermes/config.yaml)"
curl -s https://api.venice.ai/api/v1/api_keys/rate_limits \
  -H "Authorization: Bearer *** | python3 -m json.tool
# then quote every /video/queue payload via /video/quote for an exact USD number
# and increment /tmp/aipharmaxchange_spend/spend_{date}.json per spend
```

If any `remaining` counter is below 10%, downgrade tier (model-routing skill) or pause.

---

## 11. Snapshot of state on 2026-07-02

- Plan long-form: `~/.hermes/plans/aipharmaxchange-paper-reel-pipeline.md` ✅ saved
- Harness source: `/tmp/venice-video-harness/` ✅ cloned (latest = v2.3.0)
- Venice docs source: `/tmp/api-docs/` ✅ cloned from `github.com/veniceai/api-docs`
- Toolchain: ffmpeg + yt-dlp + node ✅ installed (via `brew`)
- Venice `/video/quote` ✅ returns clean data for Seedance T2V/I2V/R2V + Grok Private
- Harness: **not yet installed at `~/.venice-video-harness/`** — that is Sprint 0 work; the user must trigger it

## 12. References

- [Venice Video Generation Guide](https://docs.venice.ai/guides/media/video-generation)
- [Seedance 2.0 Guide](https://docs.venice.ai/guides/media/seedance-2-0)
- [Reference-to-Video Guide](https://docs.venice.ai/guides/media/reference-to-video)
- [Voice Cloning Guide](https://docs.venice.ai/guides/media/voice-cloning)
- [Venice Video Harness](https://github.com/jordanurbs/venice-video-harness) (community, MIT)
- Related in repo: `model-routing` skill (per-agent + tier decisions), `social-carousel-generation` skill (the static-image sibling we already have), `editorial-rigor` skill (pre-publish checklist to fold into Stage 5)
