---
title: Venice Video Harness inventory
parent: ai-video-production
audience: agents wrapping or extending the harness
---

# Venice Video Harness (jordanurbs/venice-video-harness)

Community-maintained MIT-licensed Node.js + TypeScript toolkit that wraps 50+ Venice video / image / audio / music models with production-tested agent workflows. The user pointed at this on 2026-07-02 ("You have access to all of this GitHub repo") as ground truth for our AI video pipeline.

| Item | Value |
|---|---|
| Repo | github.com/jordanurbs/venice-video-harness |
| License | MIT |
| Current version | 2.3.0 (April 2026 routing defaults; check updates) |
| Required | Node 20+, ffmpeg + ffprobe, VENICE_API_KEY |
| Optional | whisper-cpp (for the text-first editing pipeline's local transcription) |

## Install

```bash
git clone https://github.com/jordanurbs/venice-video-harness.git ~/.venice-video-harness
cd ~/.venice-video-harness && cp .env.example .env
# Add VENICE_API_KEY=*** to .env
brew install whisper-cpp
curl -L -o ~/.cache/whisper.cpp/ggml-base.en.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin
npm install && npm run build
```

## 19 workflow commands (`.claude/commands/`)

| Command | Purpose | Use case |
|---|---|---|
| `new-series` | Create a new series with locked aesthetics | Spin up a recurring brand strip |
| `add-character` / `lock-character` / `lock-characters` | Character + voice locking | One-time identity lock; reuse across shots |
| `workshop-episode` | Collaborative episode scripting | Multi-agent draft-and-refine before storyboard |
| `storyboard-all` / `storyboard-scene` / `storyboard-episode` | Storyboard one episode or scene | Two-pass panel generation |
| `qa-storyboard` | Vision QA on panels | Pre-video continuity check |
| `generate-videos` / `generate-episode-videos` / `generate-trailer` | Video generation | After storyboard approved |
| `assemble-episode` | Final assembly — ffmpeg concat + overlays + audio | Last step before publish |
| `audition-voices` | Voice comparisons for TTS voice choice | Pick a series-wide narrator |
| `edit-footage` | Text-first editing pipeline for existing media | Cut real raw footage |
| `ingest-screenplay` | Ingest a Fountain or PDF screenplay | Adapt scripts to harness format |
| `set-aesthetic` / `explore-aesthetic` | Lock / iterate series aesthetics | Brand consistency |

Our custom command for AIPharmaXchange will live alongside these — `paper-reel.md`. It wraps: ingest → analyze → storyboard → generate → assemble.

## 10 specialized agents (`.claude/agents/`)

| Agent | Role | Notes |
|---|---|---|
| `art-director` | Aesthetic, palette, lighting, composition decisions | Drives `series.json` updates |
| `prompt-engineer` | Venice image prompts, character consistency | Routes to correct image model |
| `storyboard-assembler` | Stitch panels into a coherent narrative assembly | Mid-step before video gen |
| `storyboard-qa` | Panel QA for continuity and character checks | Vision pass against panel set |
| `cut-qa` | Post-render quality gate (6 checks per cut, max 3 iterations) | **Always run before delivery** — wrap our schema with `kind` field |
| `overlay-designer` | Branded motion graphics, parallel sub-agents | Hands off to ffmpeg-overlay OR remotion-overlay |
| `ffmpeg-overlay` | drawtext-based callouts, lower thirds, chapter markers | Static overlays; one invocation = one spec |
| `remotion-overlay` | Animated overlays (logo bugs, motion typography) | Use when drawtext can't (letter-spacing, animated logos, brand-critical typography) |
| `screenplay-reader` | Parses ingest inputs | Used by `ingest-screenplay` |
| `trailer-curator` | Trailer shot selection and anti-spoiler rules | Used by `generate-trailer` |

## 7 production skills (`.claude/skills/`)

| Skill | Purpose | Use in API-driven mode? |
|---|---|---|
| `venice-api` | Venice REST API usage and defaults | Yes — core routing |
| `venice-video-model-routing` | R2V-first routing, decision trees | Yes — what to pick per shot |
| `character-consistency` | Multi-shot character consistency guidance | Yes |
| `shot-composition` | Shot composition and camera guidance | Yes — composes the prompt prefix |
| `screenplay-parsing` | Screenplay parsing workflows | Optional — only if ingesting scripts |
| `video-editing` | Text-first editing philosophy + EDL format + cut-qa loop | Yes — use for our EDL emission |
| `burn-in-subtitles` | Caption overlay with text-safety rules | Yes |
| `venice-ui-production` | Manually-driven web-UI workflow | **Skip this one for agent runs** — it plans the click-paste loop, not the API path |

## `src/` layout

```
src/
├── assembly/         # layered audio post, subtitle burn-in, final concat
├── characters/       # character reference image generation + face-rule pre-flight
├── editing/          # EDL renderer, whisper.cpp integration, frame-hash QA
├── editing/providers/
├── output/           # NLE round-trip (Final Cut / Premiere / DaVinci XML)
├── parsers/          # screenplay / Fountain / PDF / text ingestion
├── series/           # series.json schema and lockers
├── storyboard/       # two-pass panel generation + multi-edit refinement
└── venice/
    ├── client.ts     # VeniceClient (auth + base URL helpers)
    ├── video.ts      # generateVideo / quoteVideo / listVideoModels
    ├── models.ts     # 50+ model registry with model-aware parameter builders
    ├── audio.ts      # TTS / music / SFX
    └── image.ts
```

**For our paper-reel custom command**, drive `src/venice/video.ts` and `src/venice/audio.ts` directly via Node import. Do NOT use `venice-ui-production` — it's the manual UI path.

## Programmatic usage example

```typescript
import { VeniceClient } from "./src/venice/client.js";
import { generateVideo, quoteVideo } from "./src/venice/video.js";

const client = new VeniceClient({ apiKey: process.env.VENICE_API_KEY });

const quote = await quoteVideo(client, {
  model: "seedance-2-0-reference-to-video",
  duration: "5s", audio: true,
});
console.log(`Estimated: $${quote.quote}`);

const result = await generateVideo(client, {
  model: "seedance-2-0-reference-to-video",
  prompt: "Refer to <Subject 1> in <Image 1> to generate …",
  duration: "5s",
  referenceImageUrls: ["data:image/png;base64,…"],
  aspectRatio: "9:16",
  resolution: "720p",
  outputPath: "output/shot-001.mp4",
});
```

## NLE round-trip (when you want a human polish pass)

```bash
mini-drama export-timeline -p output/<project> -e 1 --format fcpxml    # Final Cut Pro X
mini-drama export-timeline -p output/<project> -e 1 --format premiere  # Adobe Premiere
mini-drama export-timeline -p output/<project> -e 1 --format davinci   # DaVinci Resolve
```

Each shot, VO clip, SFX, music cue lands on its own track — no re-edit work.

## Text-first editing pipeline (the key insight)

The harness's `cut-qa` and `video-editing` skills run a **text-first** cut strategy: local `whisper.cpp` produces per-source `*.words.json` + a 12 KB `takes_packed.md`, the LLM forms a cut strategy from text alone (no frame-dumping), proposes the strategy, then renders an EDL JSON → ffmpeg concat with 30ms audio fades. Orig archive first, never overwrite.

The 6 cut-qa checks (goal zero regressions):
1. Aspect ratio consistency (9:16 throughout)
2. No audio peaks above −6 dBFS
3. No lighting-continuity jumps inside a sentence
4. Caption text doesn't overlap shot text
5. VO never truncates mid-word
6. Frame-hash stays stable inside any single word boundary

Up to 3 fix iterations before fail.

## Schema hooks for AIPharmaXchange (`episode.json`)

The harness's standard `episode.json` is designed for the **mini-drama narrative** format. We extend it with one new top-level field, `kind`, that classifies each shot and lets our analytics distinguish paper-reel shots from narrative:

```jsonc
{
  "shot_kind": "establishing | figure-callout | stat-card | cta-quote | talking-head",
  "face_anchor_visible": true,   // true ONLY for talking-head shots
  "face_anchor_geometry": "bottom-30pct",  // see overlay-designer anchor set
  "vo_segment_id": "vo-3",       // matches vo_script.json segment id
  "transcript_traceback": "paper §3.2, fig 4",  // editorial-rigor compliance
  "model": "seedance-2-0-reference-to-video",
  "prompt": "…",
  "duration_s": 5,
  "reference_image_urls": ["…"],
  "reference_audio_urls": [],
  "aspect_ratio": "9:16",
  "resolution": "720p",
  "transition": "cut | match-cut | fade | dissolve",
  "output_path": "output/reels/2026-07-02-reel-N01/shot-03.mp4"
}
```

For our domain, **most shots are `figure-callout` or `stat-card`**; `talking-head` shots are rare (usually one for the host if Path A or B is chosen). `cta-quote` is the closing card.

## Model defaults from the harness (April 2026 routing)

| Role | Default model | When |
|---|---|---|
| Character shots (1-2 characters) | `seedance-2-0-reference-to-video` | Default R2V with flat `reference_image_urls`, `@Image` tags, up to 15s |
| Character shots (3+ characters) | `kling-o3-standard-reference-to-video` | Auto-fallback with structured `elements` |
| Establishing / mood / action | `seedance-2-0-image-to-video` | No characters; epic cinematic quality |

Our paper-reel shots largely fall into "no characters" → I2V or T2V from text. R2V is reserved for the face anchor (Path A or B) and for thumbnail-grade continuity across related B-roll cuts.

## What we add on top of the harness

1. **paper-ingest adapter** — convert arXiv / PubMed / DOI → `episode.json` + `vo_script.json`. Implements the Venice `/augment/text-parser` call + LLM analyze/storyboard steps. Lives at `~/.hermes/plans/aipharmaxchange-paper-reel-pipeline/paper_to_storyboard.py` (out-of-tree but importable).
2. **`episode.kind` schema extension** — appears above.
3. **`paper-reel` custom command** at `~/.venice-video-harness/.claude/commands/paper-reel.md` — one command, end-to-end from a paper URL/ID.
4. **AIPharmaXchange `aesthetic.json`** — palette / lighting / lens locked once, threaded into every shot's prompt prefix + book-end.

The harness solves ~90% of the plumbing. We add 10% on top.
