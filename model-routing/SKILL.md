---
name: model-routing
version: 0.3.0
description: Per-agent model routing and Venice feature configuration for AIPharmaXchange Paperclip agents. Updated 2026-06-14 with the minimax-m3 / deepseek-v4-pro / grok-4-20-multi-agent routing tier; rate-limit pre-flight mandate added 2026-06-28.
tags: [venice, model-routing, paperclip, agents, ai-pharma, editorial-rigor, rate-limits, venus-api]
triggers:
  - which model
  - model assignment
  - agent model
  - minimax-m3
  - deepseek-v4-pro
  - grok-4-20-multi-agent
  - venice tier
  - venus api
  - venice rate limit
  - rate_limits
  - api budget
  - daily spend cap
---

# Model routing for AIPharmaXchange agents

## Tier mapping (June 2026)

| Tier | Model | Context | $ per 1M (in/out) | Use for |
|---|---|---|---|---|
| `ceo_local_model` | `minimax-m3` | 500K | $0.20 / $0.80 | CEO + CTO — the local Hermes model, fast + cheap |
| `research_long_context` | `grok-4-20-multi-agent` | 2M | $1.42 / $2.83 | CMO editorial review + any 2M-ctx task |
| `long_horizon` | `deepseek-v4-pro` | 1M | $1.73 / $3.80 | Multi-step reasoning, careful planning |
| `raw_scraped_text` | `gemma-4-uncensored` | 256K | $0.16 / $0.50 | News harvester extraction (no input filter) |
| `cheap_fast` | `deepseek-v4-flash` | 1M | $0.17 / $0.35 | Bulk LLM tasks where quality is secondary |

**Standing rule**: NEVER route to `openai-gpt-55-pro` — too expensive (user directive 2026-06-14).

## Per-agent config (current as of 2026-06-14)

| Agent | Model | Venice features |
|---|---|---|
| CEO | `nvidia-nemotron-3-ultra-550b-a55b` | web=auto, citations=1, scrape=1, reasoning=medium |
| CTO | `minimax-m3` | web=auto, citations=1, scrape=1, reasoning=medium |
| CMO (MarketingDirector) | `grok-4-20-multi-agent` | web=auto, citations=1, scrape=1, reasoning=medium, disable_thinking=1 |
| ContentDirector / LinkedInStrategist / NewsletterEditor / BrandGuardian / ResearchAnalyst / ResearchSynthesizer / GitHubOSSLead | (none — script-only) | n/a |

### Standing rule — do not churn the CEO

The CEO is intentionally left on `nvidia-nemotron-3-ultra-550b-a55b` (the legacy default). When the user says "use the right model for the right job" or "we're overdue on right-model-for-right-job", this does **not** apply to the CEO. Reason: the CEO has been on Nemotron since the AIPharmaXchange company was built out, the agent's prompt + tool-calling patterns are tuned to it, and swapping introduces risk for a marginal cost gain. CTO and CMO are the agents where right-model-for-right-job applies; CEO stays on Nemotron. (User directive 2026-06-14: "Keep the CEO as Nemotron.")

## How to set the model in the venice-adapter

Three ways (in priority order):
1. `VENICE_MODEL` env var — direct model ID
2. `VENICE_MODEL_TIER` env var — tier name from MODEL_TIERS dict in `model_pricing.py` (resolved at startup)
3. `model_override` arg to `call_venice()` — per-call model ID for agents that want to route specific subtasks to a different model

## Venice features we use (set in build_venice_parameters())

| Feature | Param | Used by |
|---|---|---|
| Web search | `enable_web_search: "auto"` | CEO, CTO, CMO + newsletter generator |
| Web scraping | `enable_web_scraping: true` | CEO, CTO, CMO |
| Web citations | `enable_web_citations: true` | CEO, CTO, CMO |
| X (xAI) search | (auto via enable_web_search) | All web-search-enabled agents |
| Character persona | `character_slug: "venice"` | Optional — for branded responses |
| Disable thinking | `disable_thinking: true` | CMO only — clean marketing copy |
| Reasoning effort | `reasoning_effort: "high"` / "medium" | CEO=high, CTO/CMO=medium |
| E2EE | `e2ee: true` | Optional — for confidential research |

## Carousel pipeline — specific model picks (2026-06-18)

The paper-to-carousel orchestration (see
`social-carousel-generation` and `editorial-carousel-orchestration`)
makes LLM calls directly via Venice REST, not through Paperclip's
agent loop. Model selection for those calls:

| Call | Model | Why |
|---|---|---|
| CEO outline (1 call, 7 slides) | `nvidia-nemotron-3-ultra-550b-a55b` | Returns reliable JSON. `minimax-m3` returns empty content for this prompt (`finish_reason: length`, content is `""` despite full token usage — model burns tokens on hidden reasoning it never surfaces). `minimax-m3` also rejects `response_format: {"type": "json_object"}` with HTTP 400. |
| CEO image-prompt (1 call per slide × 7) | `nvidia-nemotron-3-ultra-550b-a55b` | Same reasoning. |
| 3 reviewers per slide (21 calls) | `nvidia-nemotron-3-ultra-550b-a55b` | Same reasoning. JSON output is reasoning-then-JSON, requires a `safe_parse_json` with regex extraction (extract the `{...}` block containing `"slides"` after the reasoning prose). |
| Image generation (7 calls) | `grok-imagine-image-quality` | Won 4-model bake-off on both chart and card slides. $0.05/image, 6.7s/image, 92% brand match. See `social-carousel-generation` for the full matrix. |

`minimax-m3` is the right CTO/chat model for the regular agent loop
where the agent framework handles retries and the model has time
to surface reasoning. For the carousel pipeline's tight
JSON-only contract, Nemotron is more reliable today. Re-test
periodically — `minimax-m3` may fix the empty-response pattern in
future model versions.

## X (xAI) search — important caveat

X search is **NOT** exposed as a standalone REST endpoint. It's only accessible
via chat completions with `enable_web_search: "auto"` — Venice routes to X
when the prompt indicates social intent (e.g. "what's Twitter saying about X",
"social sentiment on Y"). The `news_harvester.x_search()` function is a stub
that logs this and returns an empty list. For X-aware research, prompt the
chat completions endpoint directly.

## Files implementing this routing

- `~/.paperclip/adapters/venice-adapter.py` — v3 (full feature set, tier routing)
- `~/.paperclip/workspaces/aipharmaxchange/model_pricing.py` — MODEL_TIERS dict
- `~/.paperclip/workspaces/aipharmaxchange/news_harvester.py` — web search + scrape
- `~/.paperclip/workspaces/aipharmaxchange/weekly_newsletter_generator.py` — uses grok-4-20-multi-agent + web search for editorial composition
- `~/.paperclip/workspaces/aipharmaxchange/org_model_map.json` — snapshot of current routing

## Venice API rate limits — live pre-flight (user mandate, 2026-06-28)

Before **any** job that will issue more than ~5 calls against `api.venice.ai/*`,
run this pre-flight and honor the response:

```bash
curl -s https://api.venice.ai/api/v1/api_keys/rate_limits \
  -H "Authorization: Bearer *** | python3 -m json.tool
```

Always respect, in priority order:

1. **Daily $ spend cap** — `$10/day` for AIPharmaXchange ledger at
   `/tmp/aipharmaxchange_spend/spend_{date}.json`. Stop or downgrade tier when
   the running total approaches the cap (typically 80%).
2. **RPD / TPD** (request / token per day) — pick headroom-pool models first.
3. **RPM / TPM** (per minute) — for batch jobs, pace at ≤80% of `remaining`;
   add `sleep(60/remaining_rpm*0.8)` jitter, or use exponential backoff on
   HTTP 429 with `Retry-After`.
4. **Image-pool** — `grok-imagine-image-quality` and other image models draw
   from a separate pool. Count them off the text-pool budget.

### Throttling helpers

- Long-running agents should re-poll `/rate_limits` every 5 min and log the
  delta; if any remaining counter drops below 10%, downgrade tier or pause.
- Carousel batches (`social-carousel-generation`): emit images sequentially
  with 1s jitter; abort at ≤5% of `imageGenerationsPerDay`.
- One-off interactive chat calls: no guard needed. The chat loop itself is
  well below RPM.

### Pitfalls (these have fired at least once)

- **Research queries are not exempt.** Anything that batches ≥5 calls against
  `api.venice.ai/*` is subject to the pre-flight — including one-off pricing
  sweeps, capability audits, model discovery, and doc cross-checks. The
  pre-flight is cheap; burning budget on a `/models` listing plus 12
  `/video/quote` variant queries without it will quietly hit the daily cap.
  Run the pre-flight on the *first* API call, never the last.
- **Image and video pools are separate from the text pool.** `remaining`
  counters in `/rate_limits` describe the text token/request pool. Image and
  video jobs draw from dedicated **imageGenerationsPerDay** /
  **videoGenerationsPerDay** quotas — check them as separate gates.
  `grok-imagine-image-quality` (carousel winner) and Seedance 2.0 video jobs
  each count against their own day caps, not against the text pool.
- **Spending is per-key.** If multiple agents use the same Venice key, the
  ledger at `/tmp/aipharmaxchange_spend/spend_{date}.json` is the *true*
  daily truth — `/rate_limits` only shows Venice's API-key-rate side.
  Reconcile both before declaring a budget green-light.

### Fetching the key without user assist

The Venice key lives at
`~/.hermes/config.yaml → custom_providers → - name: venice → api_key:`.
If a shell call needs the bearer header:

```bash
KEY="$(awk '/^- name: venice/{f=1} f && /api_key:/{print $2; exit}' ~/.hermes/config.yaml)"
curl -s https://api.venice.ai/api/v1/api_keys/rate_limits \
  -H "Authorization: Bearer ***" | python3 -m json.tool
```

If `$VENICE_API_KEY` env var also isn't set, just ask the user to paste the
`/rate_limits` JSON — building bearer headers inline trips the file-write
redaction filter regardless of how the key is staged. Live snapshot lives in
`references/venice-rate-limits.md`.

## User typo note

User types "Venus" for "Venice" consistently. Do not correct in responses;
treat as deliberate shorthand.
