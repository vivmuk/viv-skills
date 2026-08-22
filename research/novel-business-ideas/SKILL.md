---
name: novel-business-ideas
description: Use when Vivek asks for novel, never-before-launched business ideas built on free public APIs (github.com/public-apis/public-apis), optionally combined with the Venice API for intelligence, with a concrete monetization plan. Includes the daily 10pm ET cron workflow and the anti-repeat ideas log.
version: 1.0.0
author: Kriya
license: MIT
metadata:
  hermes:
    tags: [business-ideas, public-apis, ideation, monetization, venice-api, cron]
    related_skills: [creative-ideation, venice-api-overview, venice-router, hermes-cron-ops]
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

## Procedure

1. **Fetch the catalog.** `web_fetch` `https://raw.githubusercontent.com/public-apis/public-apis/master/README.md` (fallback: `https://github.com/public-apis/public-apis`). Pick 1–3 APIs from **different categories**. Prefer free/freemium entries with no key or an easy key.
2. **Read the log.** Check `business-ideas/ideas-log.md` in the active workspace (e.g., `~/.openclaw/workspace-kriya/business-ideas/ideas-log.md`). Never repeat a previously used API combination or core concept.
3. **Design the combo.** The idea must depend on the API combination — each API should do something essential. Add Venice where an LLM/embeddings/image/search step creates the differentiated value (e.g., unstructured → structured, synthesis, personalization, generation).
4. **Novelty check.** `web_search` for the concept and near-identical products. If something close exists, iterate (different angle, customer, or data combo) before settling.
5. **Log it.** Append to `business-ideas/ideas-log.md`: date, name, APIs used, one-line summary. Create the file/dir if missing. This is what prevents repeats across runs.
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
- **Target:** isolated session, `agentTurn` payload, delivery `announce` → Telegram (Vivek's chat)
- **Timeout:** ~900s
- **Failure rule:** if web fetch/search tools fail, say so briefly and skip — **never fabricate API details** that couldn't be verified.

## Hard Rules

- No "yet another ChatGPT wrapper" and no clones of existing products.
- Cross-category API combos only; single-API ideas need an exceptional angle.
- Monetization must be concrete (who pays, roughly how much, how) — not "ads" hand-waving.
- Every run appends to the log. No log entry = broken run.
