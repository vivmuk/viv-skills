---
name: novel-business-ideas
description: Use when asked for novel, never-before-launched business ideas built on free public APIs (github.com/public-apis/public-apis), optionally combined with the Venice API for intelligence, with a concrete monetization plan. Includes the bundled 2,003-API catalog index, the anti-repeat ideas log, and the daily 10pm ET cron workflow.
version: 1.1.0
author: Kriya
license: MIT
metadata:
  hermes:
    tags: [business-ideas, public-apis, ideation, monetization, venice-api, cron]
    related_skills: [creative-ideation, venice-api-overview, venice-router, hermes-cron-ops, free-inference-apis]
---

# Novel Business Ideas (public-apis + Venice)

## Overview

Generate **one deeply thought-out, genuinely novel business idea** per run, built on free/freemium APIs from the [public-apis catalog](https://github.com/public-apis/public-apis), combined with the **Venice.ai API** (LLM inference, embeddings, image generation, web search) where it adds real intelligence. Every idea must include who pays and how.

This is **not** generic brainstorming. The bar:

- Uses 1–3 APIs from **different categories** in the public-apis catalog (cross-category combos are where novelty lives — e.g., finance + weather + government, health + geocoding + news).
- Venice fills the "intelligence" slot: reasoning, generation, embeddings, or search — not decoration.
- Novelty is **checked with web search**, not asserted. If a near-identical product exists, iterate.
- Never claim certainty that something has "never existed"; frame novelty based on the searches performed.
- **Quality over quantity:** ONE deep idea beats five shallow ones.

## When to Use

- "Give me a new business idea" / daily idea request
- Running or debugging the **daily 10pm ET cron job** (job name: *Daily Novel Business Idea (public-apis + Venice)*)
- Any ideation brief that specifies public APIs + Venice as the building blocks

## Bundled Assets

This skill is self-contained — no network needed to browse the API catalog.

| Path | What it is |
|---|---|
| `references/public-apis-index.json` | **Primary.** Machine-readable index: 2,003 APIs across 51 categories, with `name`, `description`, `auth`, `keyless` (bool), `https`, `cors`, `link`. 934 are keyless. |
| `references/public-apis-catalog.md` | Raw upstream README snapshot (288 KB) — human-readable fallback, exact source formatting. |
| `references/ideas-log.md` | Anti-repeat log of every idea previously generated. Seed with your own history before first run. |
| `scripts/build_api_index.py` | Rebuilds the JSON index. `python3 scripts/build_api_index.py` fetches live; pass a local `.md` path to parse a snapshot. |

**Selecting APIs:** use the JSON index. Filter `keyless: true` first (no signup friction), then read across at least two different `categories` to find a non-obvious pairing.

Refresh the catalog monthly with `scripts/build_api_index.py` (the upstream README is updated continuously).

## Procedure

1. **Pick APIs.** Read `references/public-apis-index.json`. Choose 1–3 APIs from **different categories**. Prefer `keyless: true`, then easy-key freemium. If you need to verify an entry is still live, `web_fetch` its `link` or fall back to `references/public-apis-catalog.md`.
2. **Read the log.** Read `references/ideas-log.md` (or the workspace copy at `business-ideas/ideas-log.md` if present). Never repeat a previously used API combination or core concept.
3. **Design the combo.** The idea must *depend* on the API combination — each API should do something essential. Add Venice where an LLM/embeddings/image/search step creates the differentiated value (unstructured → structured, synthesis, personalization, generation).
4. **Novelty check.** Search for the concept and near-identical products. If something close exists, iterate (different angle, customer, or data combo) before settling. When search tooling is unavailable, say so and frame novelty as "not found in the searches I could run" — never as proof.
5. **Log it.** Append to the ideas log: date, name, APIs used, one-line summary, and the novelty-check result. Create the file/dir if missing. **This is the mechanism that prevents repeats across runs — a run without a log entry is broken.**
6. **Deliver** in the output format below.

## Output Format (Telegram-friendly: no tables, no headers, bold + bullets)

```
🚀 Daily Business Idea — <date>

Name: <catchy working name>
The idea: 2–3 sentences, concrete.
APIs used: which public-apis entries + how each is used; how Venice fits in (LLM/embeddings/image/search).
Why it's novel: what gap it fills, why nobody's done it (based on searches).
Who pays & how: target customer, pricing/monetization model.
MVP sketch: what you'd build in a weekend to test it.
Risks: 1–2 honest ones.
```

Keep the final message under ~2000 characters so it delivers cleanly in Telegram.

## Daily Cron Setup

- **Schedule:** `0 22 * * *`, tz `America/New_York`
- **Target:** isolated session, `agentTurn` payload, delivery `announce` → Telegram
- **Timeout:** ~900s
- **Failure rule:** if web fetch/search tools fail, say so briefly and skip — **never fabricate API details** that couldn't be verified.

## Hard Rules

- No "yet another ChatGPT wrapper" and no clones of existing products.
- Cross-category API combos only; single-API ideas need an exceptional angle.
- Monetization must be concrete (who pays, roughly how much, how) — not "ads" hand-waving.
- Every run appends to the log. No log entry = broken run.
- Verify APIs are live before building the pitch on them; catalog entries rot (dead links, now-required keys). Say which you checked.

## Installing Into Another Agent

1. Copy this directory into the target agent's skills path, preserving the layout:
   `skills/novel-business-ideas/{SKILL.md,references/,scripts/}`
2. Seed `references/ideas-log.md` with that agent's prior ideas (or an empty file) so it doesn't repeat itself.
3. Rebuild the index if it's older than a month: `python3 scripts/build_api_index.py`
4. Schedule with that agent's own scheduler — cron expression `0 22 * * *` in the target timezone — pointing at the same procedure.
