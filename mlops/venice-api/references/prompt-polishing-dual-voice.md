---
title: Prompt-polishing dual-voice (preservation vs creative) for Venice video
description: When calling Venice chat to polish user prompt text before submitting to a Venice VIDEO model, route the system prompt by model class. Edit-style V2V / reference-to-video models need PRESERVATION voice (resist scene rewrite); T2V / I2V models get CREATIVE elaboration. Empirical finding: complex multi-add prompts force V2V edit models into full scene rewrite (verified on Wan 2.7 in 2026-07).
applies_to: any service that uses Venice chat-completions to improve / rewrite / augment user-supplied prompts before sending them to a Venice `/video/queue` model
related_skills: venice-api
---

# Prompt-polishing dual-voice (preservation vs creative)

When a Venice pipeline collects raw user intent (e.g. "a cowboy joins the dance floor") and tries to "improve" it before sending to `/video/queue`, a single creative-elaboration system prompt silently breaks results for half the model fleet. This is a model-class fork, not a model-level one.

## The empirical finding

From the Venice-Video `feature/v2v-tab` user-session smoke tests (2026-07-12, real Wan 2.7 V2V submissions), with a single "creative elaboration" system prompt:

| User prompt | Wan 2.7 V2V result |
|---|---|
| "add a cowboy to the dance floor" | ✅ Cowboy inserted cleanly, women + lighting preserved |
| "add a cowboy and a second dancer near the falling money" | ❌ Original women replaced by 4 people in a staged tableau; synthetic evenly-spaced falling dollars prop |

The model didn't accept the user's additions and ignore the original. It re-staged the whole scene. Why?

Wan 2.7 video-to-video doesn't "paste" objects into frames. It **adds noise across the whole latent video and re-denoises it toward the prompt**. When the prompt demands multiple discrete additions (2+ characters + props + spatial relations + ethnicities), the model has to recompose to satisfy all the constraints at once. The training data for multi-person party scenes with money falling also pulls toward "male revue" aesthetics, so compound inputs drift further from the original.

This isn't a fix-the-prompt issue. It's a structural limit of the V2V edit-style architecture. The fix is to avoid crossing the complexity threshold in the first place — the polished prompt must not push the model past the threshold.

## How to classify a model

Two signals, both checked:

```js
function isPreserveVoiceNeeded(modelId, constraints = {}) {
  const id = (modelId || '').toLowerCase();
  return /-video-to-video/.test(id)
      || /-reference-to-video/.test(id)
      || constraints.video_input === true;   // also covers Runway Aleph, Topaz
}
```

Per model (verified 2026-07-12):

| Class | Models | Voice |
|---|---|---|
| **EDIT / PRESERVATION** | `wan-2-7-video-to-video`, `grok-imagine-video-to-video-private`, `ltx-2-video-to-video`, `happyhorse-1-0-video-to-video`, `wan-2-7-reference-to-video`, `grok-imagine-reference-to-video-private`,`runway-gen4-aleph`, `topaz-video-upscale` | PRESERVE-FIRST |
| **CREATIVE** | `kling-o3-pro-text-to-video`, `kling-o3-pro-image-to-video`, `wan-2-7-text-to-video`, `veo3.1-text-to-video`, `sora-2-text-to-video`, `pixverse-v5.6-text-to-video` | ELABORATE |
| **MOTION** | `kling-v3-pro-motion-control`, `kling-v3-standard-motion-control` | PRESERVE (the original motion is the asset) |
| **UPSCALE** | `topaz-video-upscale`, `topaz-video-upscale-2` | none (no prompt needed) |

## The two system prompts (verified to work)

```js
function buildSystemPrompt(modelId, kind /* 'user_prompt' or 'motion_prompt' */) {
  const id = (modelId || '').toLowerCase();
  const isPreserveFirst = isPreserveVoiceNeeded(modelId);

  const prefix = isPreserveFirst
    ? [
        'You are a video-direction consultant for an edit-style V2V / reference-to-video model.',
        'The uploaded source video is sacred. Wan-2.7 / Grok / HappyHorse edit-models preserve the original ONLY if your rewritten prompt stays below a complexity threshold.',
        'Multi-add prompts (2+ characters, props, spatial relations, ethnicities) force a full scene rewrite — original people get replaced.',
        'Rule: PRESERVE-FIRST. Add nothing the user did not explicitly request. Prefer minimal phrasing. Avoid cinematic elaboration that adds background detail.',
      ].join(' ')
    : [
        'You are a video-direction consultant for a generative video model.',
        'Rewrite the user intent to be tight, evocative, and concrete.',
        'Use sensory language (light, motion, framing), one camera move, one focal subject.',
      ].join(' ');

  return [
    prefix,
    'Style hint: ' + styleHint(modelId) + '.',
    kind === 'motion_prompt'
      ? 'Preserve the original motion. Describe only what moves and where — not the whole scene.'
      : '',
    'Return only the new prompt — no preamble, no labels, no quotes.',
  ].filter(Boolean).join(' ');
}

function styleHint(modelId) {
  const id = (modelId || '').toLowerCase();
  const hints = [];
  if (/grok|photorealistic/.test(id))    hints.push('photorealistic, natural light, expressive faces');
  if (/kling|cinematic/.test(id))       hints.push('cinematic language: camera movement, lighting, focus pulls');
  if (/sora|veo/.test(id))               hints.push('vivid sensory language, scene-driven');
  if (/wan/.test(id) && !isPreserveVoiceNeeded(modelId)) hints.push('cinematic mood, sense of motion');
  if (/runway/.test(id))                hints.push('cinematic concise language — Runway has a 1000-char budget');
  if (/motion/.test(id))                hints.push('preserve original motion');
  if (/upscale/.test(id))               hints.push('not applicable — no prompt needed for upscale models');
  return hints.join('; ') || 'expand with sensory detail, scene structure, camera direction';
}
```

Real outputs from the chat completion endpoint with these voices (2026-07-12):

```
User: "add a cowboy to the dance floor" + Wan 2.7 V2V (PRESERVE):
  → "A lone cowboy in boots and hat joins the dance floor, moving with the crowd."

User: "a samurai enters a bamboo forest at dawn" + Kling T2V (CREATIVE):
  → "Slow dolly push through dense bamboo stalks as a lone samurai steps into frame at dawn — ground-level fog drifts across damp earth, pale gold light filtering through the canopy in thin, god-ray shafts. Tight focus on worn sandals crunching over fallen leaves, then a smooth rack focus up to the warri(or)..."

User: "runner through neon city" + Runway Aleph (PRESERVE because video_input:true):
  → "Lone figure sprints through rain-slicked streets at 3 AM. Neon signs bleed pink and cyan across wet asphalt. Steam erupts from gutter grates. Camera tracks low behind pounding sneakers, then sweeps wide to reveal towering holographic billboards reflected in puddles..."
```

Runway flips to PRESERVE because `constraints.video_input === true` — it doesn't have a T2V mode at all, so the prompt is actually guiding a V2V edit. Kling T2V goes to CREATIVE because there's no source to preserve.

## Required call-site flags

Two flags that must always be paired when calling chat-completions for prompt polishing (verified 2026-07-12 across Venice models):

```js
body: {
  model: 'claude-sonnet-4-6',   // or 'openai-gpt-55-pro' for cheaper; gemma-4 for scraped content
  messages: [{ role: 'system', content: systemPrompt }, { role: 'user', content: prompt }],
  max_tokens: 600,
  temperature: 0.7,
  venice_parameters: { disable_thinking: true, strip_thinking_response: true },
}
```

Without `disable_thinking: true`, reasoning-only models like `gpt-oss-120b` burn the entire output budget on chain-of-thought and return empty `content`. With `disable_thinking: true`, the polished prompt comes back in 1–3 seconds and ~600 tokens with `finish_reason: "stop"`.

## A two-pass decomposition pattern (advanced)

If the user really wants the multi-add scene but the model can't preserve the original, decompose into two single-pass generations and blend afterwards:

```
Round 1: "add a cowboy near the dance floor"  → preserves original women, inserts one cowboy
Round 2: "add a second man on the other side" → two passes, composite in post
```

The LLM polish step can detect candidate decomposable prompts and offer both options to the user before calling Venice twice:

```js
function maybeDecompose(originalPrompt) {
  const hasMultiAdd = /\b(add|place|insert|drop|put)\s+(\w+\s+(and|&|,)\s+\w+)/i.test(originalPrompt);
  return hasMultiAdd ? 'decomposable' : 'single';
}
```

This is an optional UX feature — but worth wiring if the user's typical workflow involves two-character / two-object / scene-with-bystander compositions that V2V edit models consistently flatten.

## Why not just lower `temperature` to 0?

Lower temperature reduces randomness but doesn't reduce the model's *capacity* to interpret the prompt. Wan 2.7 still re-stages when the prompt demands structurally incompatible additions. The dual-voice system prompt affects the *input*, not just the *sampling* — that's the right place to fix this.

## Cost

Verified per-call costs (2026-07-12, Venice pricing):

- `claude-sonnet-4-6`: ~$0.0014/call at 600 max_tokens
- `claude-haiku-4-5` (cheaper alternative): ~$0.0005/call
- `gemma-4-uncensored`: ~$0.0006/call (no input filter, good for creative voice)

For a typical "Improve" button hit by a content-creator user (1 polish per submission), the cost is negligible. Don't over-engineer rate limiting for this.
