# AI Pharma Exchange Teaching Kit

Everything another agent needs to reproduce the Jessica-voice AI Pharma Exchange short video pipeline.

## What’s in this kit

| File | Purpose |
|------|---------|
| `SKILL.md` | Full reusable skill: goals, API schema, pipeline steps, prompts, pitfalls |
| `seedance-r2v-api.md` | Validated Venice Seedance API reference |
| `prepare_audio_segment.py` | Slow/pad Jessica TTS so each clip is exactly 15s for Seedance |
| `hostess_reference_frame.jpg` | **Canonical hostess reference image** — use this exact file for consistent identity |
| `sample_jessica.mp3` | Sample of the Jessica voice |
| `queue_host_video.py` | End-to-end script: TTS + queue both Seedance R2V clips |
| `poll.py` | Poll `/video/retrieve` and download both host clips |
| `assemble.py` | Build 30s split-screen final: slide top + host bottom |
| `slide1_intro_cases_watercolor.jpg` | Example watercolor slide for segment 1 |
| `slide2_scores_conclusion_watercolor.jpg` | Example watercolor slide for segment 2 |
| `slide1_intro_cases.jpg` | Example non-watercolor slide for segment 1 |
| `slide2_scores_conclusion.jpg` | Example non-watercolor slide for segment 2 |

## Quick start

1. **Place the hostess reference image** at `~/faces/aipharmaxchange_openevidence_30s/host_video/hostess_reference_frame.jpg`.
2. **Generate/queue host clips:**
   ```bash
   python queue_host_video.py
   ```
   This creates Jessica TTS audio and queues two 15s Seedance R2V clips.
3. **Poll for results:**
   ```bash
   python poll.py host_video/queue_state.json host_video
   ```
4. **Generate your slides** with `gpt-image-2` (prompts in `SKILL.md`), save as `slides/slide1_*.jpg` and `slides/slide2_*.jpg`.
5. **Assemble final video:**
   ```bash
   python assemble.py
   ```
   Output: `final/openevidence_30s_final.mp4`

## Key configuration

- Venice API key is read from `~/.hermes/config.yaml` under `model.api_key`.
- Voice: `tts-elevenlabs-turbo-v2-5`, voice `Jessica`.
- Seedance model: `seedance-2-0-enhanced-reference-to-video`.
- Each clip: `15s`, aspect ratio `3:4`, `720p`.
- Final output: `1536×864` 30 fps, split-screen top slide + bottom host.

## Important rules

1. **Use the canonical hostess image** for every video to keep identity consistent.
2. **Match Seedance duration to audio duration.** If audio is < 14.5s, slow + pad to 15s; if > 15s, speed up or rewrite.
3. **Always provide reference audio** to Seedance for lip-sync.
4. **Do not use** `guidance_scale` or `steps` in the Seedance payload — they return 400.
5. **Verify final duration** with `ffprobe`; audio and video should match within 0.05s.

## Folder layout expected

```
~/faces/aipharmaxchange_openevidence_30s/
├── host_video/
│   ├── hostess_reference_frame.jpg
│   ├── seg1.mp4
│   └── seg2.mp4
├── slides/
│   ├── slide1_intro_cases_watercolor.jpg
│   └── slide2_scores_conclusion_watercolor.jpg
├── audio/
│   ├── seg1.mp3
│   └── seg2.mp3
└── final/
    └── openevidence_30s_final.mp4
```

## Example slide prompt

Use Venice `gpt-image-2` with:

```
Watercolor professional infographic for a healthcare podcast, clean hierarchy, large readable sans-serif text, soft medical palette of teal and lavender. Title "OpenEvidence" at top. Three bullet points: 1) 2,867 real-world clinical cases, 2) specialties: cardiology, infectious disease, oncology, 3) LLM answers with trusted references. Decorative watercolor washes, no photo-realistic faces, modern editorial style, 1536x864 landscape.
```

## Contact

Skill maintained by Vega. For questions, check `SKILL.md` first.
