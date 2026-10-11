---
name: editorial-carousel-orchestration
version: 0.5.0
description: Orchestrate a multi-agent pipeline that turns a research paper (PDF) into an 8-slide editorial carousel (PNG deck + PDF + ZIP) — 7 content slides + 1 Follow-AIPharmaXchange CTA — with no source citations on the slide, brand wordmark + "swipe →" cue on every slide, CEO-authored fair/balanced LinkedIn post copy tuned for pharma experts who may not be AI experts, and full Paperclip integration (issue creation, attachments, daemon delivery). Use when the user says "make a carousel for paper X", "turn this paper into a LinkedIn carousel", "create a slide deck for paper Y", "carousel of paper Z", "summarize paper X as slides", or any variant of paper-to-carousel. Empirically derived from the MIRA (2026-06-18) and AMIE (2026-06-18) carousel runs and the v2 company rebuild (2026-06-19).
tags: [editorial, carousel, multi-agent, paperclip, paper-to-slides, content-pipeline, aipharma, audience-fit, pharma-experts] 
triggers:
  - "carousel for paper"
  - "LinkedIn carousel"
  - "Instagram carousel from paper"
  - "7 slides from"
  - "summarize paper as slides"
  - "paper to carousel"
  - "make a slide deck"
  - "deck from PDF"
---

# Editorial Carousel Orchestration (Paper → 8-slide deck)

> **Note (2026-06-18, updated 2026-06-27):** This skill is the canonical
> class-level workflow for the AIPharmaXchange paper-to-carousel pipeline.
> It overlaps with `social-carousel-generation` (creative) which has more
> of the model-bake-off details and the "no Pillow for text overlay"
> hard constraint; **load BOTH for new work** — this skill owns:
> 1. The 8-slide spine (7 content + 1 Follow CTA)
> 2. The "no source citation on the slide" rule + strip_citations()
> 3. The brand wordmark + "swipe →" footer mandate
> 4. The CEO-writes-post-copy contract (post copy is in the spec, not
>    generated downstream)
> 5. **The Paperclip wrapper integration** (canonical wrapper at
>    `/Users/vivgatesai/.hermes/scripts/paperclip_wrap_carousel.py`,
>    issue creation + attachments + daemon delivery + `--from-existing`
>    flow for re-runs and ad-hoc stages). **Don't grep under
>    `~/.paperclip/workspaces/`** for this wrapper — that path is for
>    Paperclip-company agents, not the v2 carousel wrapper.
> 6. The direct-SMTP fallback when the Paperclip daemon or Paperclip
>    API is unreachable (load `send-gmail-attachment` for the canonical
>    Python smtplib pattern; don't reimplement it inline).

## Load order

When a user asks for a carousel and you intend to wire it through
Paperclip + daemon delivery, the load order matters:

1. **This skill first** (`editorial-carousel-orchestration`) — it owns
   the 8-slide spine, the wrapper integration, the SMTP fallback, and
   the budget cap.
2. **Then** `social-carousel-generation` — it owns the model bake-off
   matrix, the image-prompt template, the 23-pitfall detail.
3. **Before any direct SMTP code** load `send-gmail-attachment` — it has
   the canonical Python smtplib + EmailMessage template with the
   vivkatesai-vs-vivgatesai typo pitfall, the persistent credential rule,
   and the HTML body pattern (`set_content` + `add_alternative`).

A class-level workflow: turn one research paper into an 8-slide
LinkedIn/Instagram carousel with full editorial review, assembled
as a PDF + ZIP, ready to send for human review. The 8th slide is
a brand-CTA slide ("Join AIPharmaXchange on LinkedIn"), NOT a
content slide. This is locked; do not negotiate it down to 7.

Empirically derived from the MIRA (2026-06-18, ~7 min wall-clock,
~$0.40 cost) and AMIE (2026-06-18, ~5 min, ~$0.44 cost) runs on
`nvidia-nemotron-3-ultra-550b-a55b` + `grok-imagine-image-quality`.

## When to use

The user has a single source (a PDF, a URL, or a citation) and
wants a carousel. The class of work is "one paper → one deck, with
editorial review baked in." If the user wants a thread or a blog
post instead, use a different skill.

**Mandatory sections** (the user has corrected the omission
multiple times):
- **Slide 5: Trend context** — how this paper fits the shift from
  earlier approaches to this one. Without it, the deck reads as
  one-off, not as part of an ongoing narrative.
- **Slide 6: Limitations** — fair/balance slide with ≥4 honest
  cards. Without it, the deck is a press release, not editorial.
  See `editorial-rigor` skill for the limitations content
  requirements.
- **Slide 8: Follow CTA** — "THANKS FOR READING" + "JOIN
  AIPharmaXchange ON LINKEDIN" + brand-marked pill button +
  LinkedIn icon + "swipe done ✓". This is the growth loop for
  the channel. Do not omit, do not move into slide 7.

## The 8-slide spine (locked)

1. **Title card** — paper one-line hook, journal/year, headline preview
2. **Method / architecture** — what the system does
3. **Headline result** — primary endpoint, MANDATORY chart (per-condition
   or per-cohort bar/line graph)
4. **Workflow fidelity** — secondary metrics, MANDATORY chart (small-
   multiples, metric grid, or comparison)
5. **Trend context** — 4-stage timeline or arc of similar systems
6. **Limitations** — ≥4 honest limits, fair/balance slide
7. **Implications + DOI CTA** — broader implications, paper DOI
8. **Follow CTA** — "THANKS FOR READING" + Join AIPharmaXchange on
   LinkedIn. Generated by a dedicated CTA prompt, NOT derived from
   the spec.

## Architecture: 4 agents, 1 pipeline

The user explicitly wants **4 agents**, no more:

| Role | Agent | What it does |
|---|---|---|
| **CEO (medical writer)** | Repurpose the Paperclip CEO | Reads the paper, drafts the 7-slide spec (title, 3-5 bullets, key claim) AND authors the LinkedIn post copy (1500-1800 chars, fair/balanced). Both are written in one CEO responsibility — no downstream generation. |
| **Reviewer 1 — Accuracy** | Repurpose the Paperclip ResearchAnalyst | Verifies every numerical/factual claim against the source paper, demands page-level citations, flags hallucinations |
| **Reviewer 2 — Alignment** | Repurpose the Paperclip ContentDirector | Inspects the rendered PNG: text fits, no clipping, hierarchy is clear, bullet count matches spec |
| **Reviewer 3 — Brand** | Repurpose the Paperclip BrandGuardian | Checks tone (clinical/editorial, no hype), palette (teal #2BA39B, mint #8FD3B6, navy #1E3A5F, cream #F5F0E1), citations present |

The other Paperclip agents (CTO, CMO/MarketingDirector,
ResearchSynthesizer, NewsletterEditor, LinkedInStrategist,
GitHubOSSLead) are **not** in the carousel unit — they handle
their other responsibilities in separate streams. For the
carousel pipeline, they are paused via
`PATCH /api/issues/{id} {"status": "paused"}` (do NOT
`DELETE` — that breaks company config).

## Pipeline steps (the actual sequence)

1. **Extract paper text.** `pymupdf` (`fitz`) on the source PDF.
   Truncate to ~50K chars for the CEO prompt. Carousel-relevant
   sections: abstract, methods, results (with effect sizes and
   CIs/P-values), discussion/limitations, conclusion.

2. **CEO writes 7-slide spec + LinkedIn post copy (single source
   of truth).** Use **`nvidia-nemotron-3-ultra-550b-a55b`** as
   the LLM. Two consecutive LLM calls in the orchestration:
   - Call A: 7-slide spec (strict JSON). The CEO writes
     `title`, `bullets`, `key_claim` per slide.
   - Call B: LinkedIn post copy (1500-1800 chars, plain text).
     The CEO writes the post copy from the same paper evidence
     the slides cite, with the same fair/balance, no-hype,
     page-cited discipline. The post copy is the CEO's
     responsibility as medical writer; it is NOT a downstream
     task. Stored as `linkedin_post_copy` in the spec and
     saved to `post_copy.txt`.
   - `minimax-m3` returns empty content for some prompts
     (`finish_reason: length` with 0 chars out — the model burns
     tokens on hidden reasoning it never surfaces) and **does not
     support `response_format: {"type": "json_object"}`** (returns
     HTTP 400). Nemotron emits reasoning-then-JSON; use a
     `safe_parse_json` with regex extraction to handle the
     pattern. For the post-copy call, set `max_tokens=4000`
     because Nemotron includes chain-of-thought before the
     final post; if the response ends mid-paragraph, extract the
     last "Hook:" block and re-attribute.

3. **Strip source citations from spec.** Before any slide text
   goes to the image prompt, run `strip_citations()` on
   `title`, every `bullet`, and `key_claim`. Strips
   `(p.1)`, `(Fig.2)`, `[p.X]`, `p.4`, `et al.`, and similar
   page/figure references. **Citations NEVER appear on the
   rendered slide** — the user explicitly corrected this with
   "can't have that" and "no source citation" multiple times.
   Citations live only in `spec.md` for the editorial team.
   ```python
   def strip_citations(text):
       # remove (p.X), (Fig.X), [p.X], page X, fig X, etc.
       s = re.sub(r'\s*\((?:p\.|pp\.|page|pages|fig\.|figure|...)\s*[^)]+\)', '', s, flags=re.I)
       s = re.sub(r'\s*\[(?:p\.|pp\.|page|pages|fig\.|figure|...)\s*[^\]]+\]', '', s, flags=re.I)
       s = re.sub(r'\s*,?\s*(?:p\.|pp\.|page|fig\.|figure)\s*\d+(?:[\-–]\d+)?\.?\s*', '', s, flags=re.I)
       s = re.sub(r'\s+', ' ', s).strip()
       return s
   ```

4. **CEO writes per-slide image prompts (watercolor style).**
   The image-prompt template now MANDATES:
   - At least one data-visualization element per slide
     (chart, line graph, scatter, pie, timeline, comparison
     grid, small-multiples, icon row)
   - Slides 3 (headline) and 4 (workflow) — chart should
     DOMINATE at least 35% of canvas
   - **MANDATORY FOOTER (bottom-left):** "AIPharmaXchange"
     brand wordmark, "AI" in teal, "PharmaXchange" in dark navy
   - **MANDATORY FOOTER (bottom-right):** "swipe →" cue
     (slides 1-7) or "swipe done ✓" (slide 8) — this is the
     LinkedIn carousel indicator
   - NEVER include "(p.1)", "(Fig.2)", "et al.", author/journal/year

5. **Render slides 1-7.** `grok-imagine-image-quality` is the
   single-model choice. Won the 4-model bake-off (vs `ideogram-v4`,
   `recraft-v4-pro`, `qwen-image-2`) on both chart slides and card
   slides. Score: 9.75 chart, 8.5 cards, 92% brand match,
   6.7s/image, $0.05/image. Single-model orchestration across all
   slides.
   - **Inline the actual text strings in the image prompt** — do
     NOT pass `{title}` / `{bullets}` / `{claim}` placeholders.
     The CEO will sometimes leave them as literal placeholders,
     and the image model will then hallucinate. Safety net:
     programmatically replace any leftover `{title}`,
     `{bullets}`, `{claim}` tokens; if the image prompt is
     still < 200 chars or contains `"Your Title"`,
     `"First bullet"`, etc., build a hard fallback prompt that
     embeds the real content.
   - **Watercolor is the brand style.** Anchor the style in the
     prompt with phrases like "painterly watercolor illustration
     aesthetic with visible brushstrokes", "soft cream
     watercolor washes with subtle teal and navy splashes",
     "all text zones remain pure white for full legibility".
     Don't drop this descriptor when rewriting the prompt — the
     watercolor IS the brand identity. If you change anything
     else, preserve the watercolor block.
   - **Size: 1024×1024 (LinkedIn square).** `grok-imagine-image-quality`
     caps both axes at 1024 (NOT 1280 as previously thought).
     Requests for 1024×1280 silently return 1024×1024. LinkedIn
     square carousels work fine; this is the cleanest carousel
     format. If you need true 4:5 portrait, use `flux-2-max` (up
     to 2048 each axis) or compose in Pillow.
   - **Color names, not hex codes.** The model interprets hex
     codes as vibe-words, drifts to warm pinks or grey-greens.
     Use "teal", "navy", "cream" — and explicitly forbid hex
     codes in the negative prompt: `"blurry text, gibberish
     letters, distorted glyphs, hex codes, hashtags,
     watermarks, signatures, off-brand colors, pink tint,
     purple, red, Nature, JAMA, NEJM, Lancet, external
     journal branding, page references, author names"`.

6. **Render slide 8 (Follow CTA).** Dedicated CTA prompt, NOT
   derived from the spec. The CTA prompt is hard-coded:
   ```
   THANKS FOR READING
   Join us on LinkedIn for more clinical AI analysis
   JOIN AIPharmaXchange ON LINKEDIN
   [pill button: AIPharmaXchange] [LinkedIn icon]
   More papers decoded every week
   [bottom-right: swipe done ✓]
   ```
   The orchestration appends a `slides.append({slide_num: 8, ...})`
   entry with the CTA's image_prompt so the spec is self-
   describing, but the actual render call happens ONCE in
   Step 3b and the loop in Step 4 dedupes by slide_num.

7. **3 reviewers score each slide.** Each reviewer call includes
   **the rendered PNG bytes** (base64 in prompt), not just the
   slide spec. Reviewers must inspect:
   - **Accuracy**: every claim is supported by the paper;
     page-level citations required
   - **Alignment**: text fits, no clipping, no z-order
     collision, has data-visualization element,
     **swipe cue present**, **source citation absent**
   - **Brand**: tone is clinical/editorial, palette is on-brand,
     no hype words ("groundbreaking", "revolutionary",
     "amazing"), no exclamation marks, no external journal
     branding, **no source citation in the rendered text**
   - **All three**: hallucinated text inside the image is a
     hard fail (see `editorial-rigor` skill, revised 2026-06-18).
     Slide 8 (CTA) is exempt from the paper-accuracy check —
     the reviewers correctly note "unrelated to source paper" is
     expected for a brand CTA.

8. **Assemble PDF + ZIP.** Pillow reads the 8 PNGs (slides 1-8);
   `reportlab.Canvas(pagesize=(W, H))` stacks them; ZIP
   contains the PNGs + `spec.json` + `reviews.json` +
   `post_copy.txt`.

9. **Send to the user.** Three delivery paths, in this order
   of preference:
   - **Paperclip wrapper** (`paperclip_wrap_carousel.py`):
     creates Paperclip issue, attaches all assets, marks done,
     the daemon emails `vivek@live.de` from "AI CEO
     AIPharmaXchange" with all attachments. This is the
     production path.
   - **Direct SMTP** (Python smtplib): used as a fallback or
     for ad-hoc one-offs.
   - **Telegram**: for visual review during the run, send
     slides here as a parallel channel.
   When called by the Paperclip wrapper, the orchestration
   skips its own email (env flag `CAROUSEL_NO_EMAIL=1`).

## Hard limits

- **Max 2 attempts.** After attempt 2, post a postmortem and
  stop. The user has explicitly said: *"otherwise we make it no
  more than two times."*
- **Daily budget cap: $10/day** for the workspace (Paperclip
  + Hermes). The carousel costs ~$0.40 in minimax-m3 tokens +
  ~$0.35 in image gen = ~$0.75 total. Multiple carousels per day
  fit comfortably; track spend in
  `/tmp/aipharmaxchange_spend/spend_{date}.json`.

## Pitfalls

- **Reviewer prompts must include image bytes (not just spec
  text).** In the MIRA run, the reviewers only saw the slide
  spec as text. They scored the *content* 7-9/10 (legitimate),
  while the *rendered PNG* had hallucinated text inside the
  limitations cards, decorative-only bar charts with no axes,
  and z-order collisions between bullets and illustrations. All
  three failure modes shipped silently because no one was
  looking at the PNG. Fix: include `image_url: {url:
  "data:image/png;base64,..."}` in the reviewer user message
  along with the spec.
- **Pillow text overlay is REJECTED for carousels** (2026-06-18
  user correction). The user has stated this three times in a
  single session, the most emphatic being *"don't use pillow,
  no option b"*. The image model (`grok-imagine-image-quality`)
  is reliable enough at rendering text on infographic-style
  prompts (9.75/10 on a chart slide) to be the canonical
  pattern. For other image deliverables (hero images,
  decorative illustrations, data-heavy infographics), see the
  `branded-infographic` skill — Pillow overlay may still be
  the right call there.
- **The image model's "bar chart" is decorative-only.** No
  axes, no labels, no legend, no scale. The reader cannot
  extract a value. For any claim that needs the reader to
  read a number off the chart, draw the chart in Pillow.
  Same applies to slide 6 (limitations): if you need a 2×2
  card grid, lock the layout in the prompt literally
  (`"a 2×2 grid of 4 cards"`) and add `"no vertical list, no
  single-column layout"` to the negative prompt. Otherwise the
  model may decide to render a numbered list instead.
- **The image model fabricates numbers not in the prompt.**
  On the MIRA slide 3, `recraft-v4-pro` rendered
  "UTI physician = 88.0%" when the paper says 68.9%. The
  accuracy reviewer must catch this; do not trust the model
  to copy numbers verbatim. Always pass the spec JSON to
  the accuracy reviewer and require them to flag any
  number that doesn't match.
- **Inline the actual text strings in the image prompt** — do
  NOT pass `{title}` / `{bullets}` / `{claim}` placeholders.
  On the MIRA V2 run, the CEO left `{title}` etc. as
  literal placeholders, and the image model rendered slide 6
  as a generic template ("Your Title Here", "First bullet
  point"). Safety net: programmatic `{title}` /
  `{bullets}` / `{claim}` substitution + hard fallback
  prompt if the image prompt is still < 200 chars or
  contains placeholder text.
- **`grok-imagine-image-quality` will hallucinate external
  journal branding** ("NATURE — CLINICAL INFOGRAPHIC SERIES"
  footer on MIRA slide 7) and DOIs that aren't in the
  prompt. Add to the negative prompt: `"Nature, JAMA, NEJM,
  Lancet, external journal branding"`. Pre-fill the real DOI
  from the source paper into the spec — don't let the model
  generate it.
- **Don't `DELETE` Paperclip agents to "clean up."** Use
  `PATCH /api/issues/{id} {"status": "paused"}`. `DELETE`
  breaks the company config and creates orphaned child issues.
  Status `paused` is reversible; DELETE is not.
- **The image model returns `images[]` as plain base64 strings
  for `grok-imagine-image-quality`**, not the OpenAI
  `data[].b64_json` wrapper. Parse defensively. See
  `venice-api` skill, "Image response format compat."
- **`grok-imagine-image-quality` caps image dimensions at 1024×1024.**
  Requests for taller images (e.g. 1024×1280) silently get
  downsized to 1024×1024. For true 4:5 portrait, switch models
  (e.g., `flux-2-max`) or compose portrait in Pillow.
- **Use `nvidia-nemotron-3-ultra-550b-a55b` as the CEO LLM,
  not `minimax-m3`.** `minimax-m3` returns empty content for
  some prompts (`finish_reason: length`, content is empty
  string despite full token usage — model burns tokens on
  hidden reasoning) and does not support
  `response_format: {"type": "json_object"}` (HTTP 400).
  Nemotron emits reasoning-then-JSON; use a `safe_parse_json`
  with regex extraction for the JSON block, falling back to
  brace/quote repair.
- **Don't drop the watercolor style descriptor when rewriting
  prompts.** This was a real failure mode in MIRA V2: I
  rewrote the image prompt to add a negative_prompt and
  dropped "watercolor", the model defaulted to clean
  editorial clinical, and the user immediately noticed and
  asked what happened to the watercolor style. The watercolor
  is the brand identity. If you change anything else in the
  image prompt template, preserve the watercolor block.
- **No source citations on the rendered slide, period** (AMIE
  run 2026-06-18, user correction: "can't have that",
  "no source citation"). Even when the paper is cited in
  the spec for the editorial team's reference, the rendered
  slide must NOT contain "(p.1)", "(Fig.2)", "p.X", "et al.",
  author names, journal name, year, or DOI. Strip them
  with `strip_citations()` before the text goes to the
  image prompt. The `grok-imagine-image-quality` negative
  prompt must include "page references, author names,
  external journal branding" to prevent the model from
  re-introducing them. Reviewers must check
  `source_citation_found: []` and flag if any leak through.
- **Maximize data visualizations — text-only slides are not
  acceptable** (AMIE run 2026-06-18, user correction:
  "Maximize graphs charts and visuals"). Slides 3 and 4
  MUST contain a chart/graph/timeline/grid (not just text
  bullets). The image-prompt template now MANDATES at least
  one data-visualization element per slide, with slides 3
  and 4 dominating at least 35% of the canvas. Reviewers
  check `has_visual: true/false`. If a slide comes back
  text-only, regenerate with a stronger prompt.
- **Slide 8 Follow CTA is non-negotiable** (AMIE run 2026-06-18,
  user correction: "the last eighth page should be 'Join AI
  pharma exchange on LinkedIn'"). The 8-slide spine is locked
  at 7 content + 1 CTA. The CTA is generated by a dedicated
  hard-coded prompt, NOT derived from the spec. The CTA
  contains: "THANKS FOR READING" headline, "JOIN
  AIPharmaXchange ON LINKEDIN" call-to-action, brand-marked
  pill button with "AIPharmaXchange" handle, LinkedIn icon,
  "More papers decoded every week" tagline, "swipe done ✓"
  bottom-right cue. The accuracy reviewer correctly notes
  the CTA is "unrelated to source paper" — this is expected
  and not a fail.
- **Brand wordmark + swipe cue are MANDATORY footers on every
  slide** (MIRA run 2026-06-18, AMIE run 2026-06-18). The
  image-prompt template explicitly requires:
  - bottom-left: "AIPharmaXchange" wordmark, "AI" in teal,
    "PharmaXchange" in dark navy
  - bottom-right: "swipe →" (slides 1-7) or "swipe done ✓"
    (slide 8) in italic dark teal
  The reviewers check `swipe_cue_present: true/false`.
  Without these footers, the slide is unfinished and looks
  like a one-off image, not a LinkedIn carousel entry.
- **`response_format: {"type": "json_object"}` is NOT supported
  by Venice chat models in this configuration** (June 2026).
  The API returns HTTP 400 with "Unrecognized key". The
  orchestrator must rely on `safe_parse_json` with regex
  extraction of the JSON block from model output, NOT the
  OpenAI-style `response_format` parameter. Nemotron's
  pattern is reasoning-then-JSON; the regex
  `\{[^{]*"slides"\s*:\s*\[.*?\]\s*\}` extracts the slides
  array.
- **`minimax-m3` burns tokens on hidden reasoning and returns
  empty content** (June 2026). For complex structured tasks
  like CEO spec or post copy, use
  `nvidia-nemotron-3-ultra-550b-a55b` instead — it produces
  actual content. `minimax-m3` may be fine for short chat
  completions but fails on tasks requiring 3000+ completion
  tokens of structured output.
- **Always attach the original source PDF to the delivery email**
  (2026-06-18, AMIE run, user directive: *"Send it and always
  attach the original PDF to the email"*). The slide text is
  citation-stripped by `strip_citations()` for visual cleanliness,
  so the recipient needs the source paper to verify any specific
  claim. Without it, they have to ask you back for it. Locked into
  `paperclip_wrap_carousel.py::attach_assets()` as the `source_pdf_path`
  parameter — every carousel issue ships with a `Source paper —
  <stem>.pdf` work-product marked `isPrimary: true`. The direct-SMTP
  fallback script attaches it as `<paper_short>_source_paper.pdf`
  to the email. This applies to cron runs too (`job_id c16cdb5da1af`,
  daily 10am).
- **Direct SMTP fallback when the Paperclip daemon races OR Paperclip
  API is down** (2026-06-18 AMIE v2; updated 2026-06-27). Two distinct
  triggers now:
  - **Daemon race** — wrapper's PATCH-to-done loop doesn't land status
    `done` before the daemon's poll cycle. Check
    `~/.paperclip/delivery-state.json` for `sent_at` within 30s of
    marking done. If missing, fall back to direct `python3 smtplib`
    from `/tmp/send_carousel_email.py` — read artifacts from
    `/tmp/mira_final/<slug>/` and ship the same email yourself.
  - **Paperclip API or daemon unreachable** — `lsof -i :3100` returns
    empty (server didn't start), or `curl http://127.0.0.1:3100/api/health`
    fails. Skip the wrapper entirely; ship via direct SMTP. Belongs in
    the **same** direct-SMTP path as the daemon-race case. **Don't fall
    back to himalaya** (the static build's sender config is broken; see
    `send-gmail-attachment` skill for why).
  - **Don't reimplement the SMTP pattern inline.** Load
    `send-gmail-attachment` first — it owns the canonical
    Python-`smtplib` + `EmailMessage` template, the vivkatesai typo
    pitfall, and the persistent-credential rule. The Paperclip daemon
    will eventually also send (no harm in double-send), so direct SMTP
    is a belt-and-braces not a replacement.
- **`paperclip_wrap_carousel.py --from-existing` has a hardcoded
  paper-path bug** (2026-06-27, OE run). The `--from-existing` branch
  defaulted `paper_path` to
  `/Users/vivgatesai/.hermes/cache/documents/doc_53b65edd5784_2503.06074v1.pdf`
  regardless of what's actually staged. **Fixed in this repo** — the
  branch now globs `*.txt` / `*.pdf` inside the staged `--from-existing`
  directory and uses the first match. If you downgrade the wrapper or
  see a wrapper report a wrong source-paper name, check this line
  first. Always stage at least one `.txt` or `.pdf` in the
  `--from-existing` dir so the auto-discovery has something to find.
- **Company DELETE fails with FK violation on `budget_policies`** (2026-06-19,
  AIPharmaXchange v1 → v2 rebuild). When the user says "wipe and rebuild
  the company", `paperclipai company delete <id> --yes --confirm <id>`
  returns HTTP 500 with `update or delete on table "companies" violates
  foreign key constraint "budget_policies_company_id_companies_id_fk"`.
  **Don't try to brute-force the DB connection** (postgres password
  isn't readable from process env under Hermes's secret-redaction).
  **Use `paperclipai company archive <id>` instead** — soft-deletes the
  company (status=archived, preserves data), frees the issue prefix
  for a new company with the same name. Then `paperclipai company
  create --payload-json '{...}'` to spin up the fresh company. The
  archived company's data is recoverable if you ever need it.
- **Carousel-only company rebuild pattern** (2026-06-19, user
  directive: "remove everything else that is currently being done").
  The AIPharmaXchange v1 had 10 agents and 200+ issues (CTO, CMO,
  ResearchSynthesizer, NewsletterEditor, LinkedInStrategist,
  GitHubOSSLead, BrandGuardian, ContentDirector, ResearchAnalyst,
  CEO) — most of them paused but still receiving auto-continuation
  wake-ups on the carousel issue tree. Rebuild is the right call when
  the user wants ONLY the carousel unit and zero historical debt.
  Steps:
  1. `paperclipai company archive <old-id>` (NOT delete).
  2. `paperclipai company create --payload-json '{name, issuePrefix,
     budgetMonthlyCents, description}'` — the issue prefix auto-suffixes
     if the original prefix is taken (AIP → AIPA). Accept that.
  3. Create exactly 4 agents with role=ceo/researcher/pm/designer.
     Set `reportsTo` to the CEO so org chart looks right.
  4. Wire `VENICE_API_KEY` (the user-provided new key) into every
     agent's `adapterConfig.env`. Use `nvidia-nemotron-3-ultra-550b-a55b`
     for CEO, `minimax-m3` (or user-chosen model) for reviewers.
  5. Write SOUL.md / AGENTS.md / HEARTBEAT.md to each agent via
     `paperclipai agent instructions-file:put <id> --path <file>
     --content-file <local-path> --clear-legacy-prompt-template`.
     Avoid the raw API PUT (curl with JSON) — quoting issues bite you;
     the CLI handles nested quotes cleanly.
  6. Update `paperclip_wrap_carousel.py::COMPANY_ID` and `CEO_AGENT_ID`
     constants to point at the new IDs.
  7. Update `carousel_orchestration.py::KEY` default to the new Venice
     key (or read from env).
  8. Update the CEO_PROMPT in the orchestration to include the
     audience-fit rule (see LinkedIn post copy rules — pharma experts
     who may not know AI, soften jargon, keep pharma terms native).
  The new company ships clean: 4 agents, 0 issues, 0 historical
  productivity reviews, no auto-continuation on stale duplicate
  children. Cron `c16cdb5da1af` (daily 10am) automatically uses the
  new wrapper constants.
- **User prefers "remove everything else" over "pause everything
  else"** when rebuilding a Paperclip company (2026-06-19). Pausing
  the old agents doesn't stop the auto-continuation on their existing
  issue tree — they still wake up on heartbeat, still loop on duplicate
  triage, still generate the "scraping and other tasks 5 hours ago"
  user complaint. A clean wipe-and-rebuild is the only way to get a
  truly focused 4-agent carousel unit. Confirm with the user before
  doing this (it's destructive), but default to recommending it when
  the user says "remove everything else".

## Measurement baseline (MIRA run, 2026-06-18)

| Stage | Time | Tokens (in/out) | Cost |
|---|---|---|---|
| Paper extract (pymupdf) | 0.34s | — | — |
| CEO spec | 31.9s | 14,725 / 2,660 | $0.005 |
| 7× image gen (sequential) | ~180s | — | $0.35 |
| 21 reviewer calls | ~200s | ~75K / ~22K | $0.040 |
| Pillow render + PDF | <2s | — | — |
| **Total sequential** | **~7 min** | | **~$0.40** |
| **If images parallelized** | **~3.5 min** | | **~$0.40** |

A second-pass visual QA on the rendered PNGs (vision model
inspection) added ~30s and would have caught the hallucinated
text, decorative chart, and z-order collisions before delivery.

## LinkedIn post copy rules (CEO writes this as part of the spec)

The `linkedin_post_copy` field is the **single source of truth** for the
post text. The orchestration never generates post copy independently.
The CEO writes it under these constraints:

- **Tone**: editorial, scholarly-critique. Not promotional, not alarmist.
- **Length**: 1500-1800 chars. LinkedIn truncates above ~2100, and
  1500-1800 is the sweet spot for engagement.
- **Audience balance** (2026-06-19, user correction: "audience that may
  or may not be an AI expert... pharma experts, so make it relatable
  to them while also providing enough technical pieces"): pharma
  experts (R&D, clinical, regulatory, safety, medical, commercial) who
  are NOT necessarily AI experts. The audience knows their domain
  deeply. They may not know "RxQA", "retrieval-augmented generation",
  "non-inferiority margin", "Gemini 1.5 Flash", "OSCE", "RLHF", or
  "transformer". So:
  - **Keep pharma terms native** — "primary endpoint", "IRB",
    "indication", "AKI", "ECG", "PCP", "NICE guideline" — no
    translation needed.
  - **Soften AI jargon** — drop AI terms when a plain phrase works
    ("the AI assistant" beats "the LLM-powered conversational agent").
    When you keep an AI term, gloss it once in plain English on first
    use ("retrieval-augmented generation — pulling in relevant
    guidelines on demand").
  - **Make it relatable to their day** — connect the AI method to a
    workflow they recognize: "like having a junior resident who has
    read every NICE guideline and never sleeps", "a 24/7 medical
    librarian that never loses focus", "the same way a senior
    reviewer cross-checks your IND filing". One analogy per slide is
    enough — don't make every sentence an analogy.
  - **Do NOT over-explain pharma** — the audience already knows it.
    "The kidney — the organ that filters blood" is wrong (audience
    knows kidneys). Translation should target the AI half, not the
    pharma half.
- **Structure**:
  1. **Hook** (1 sentence, ≤200 chars). State the finding, not "excited
     to share". End with a period or em-dash, never an exclamation.
  2. **Body** (2-3 short paragraphs, each ≤400 chars). Cover: what was
     tested, what the headline means, what the limitations are. Cite
     headline number(s) with paper context.
  3. **Close** (1-2 sentences). Forward-looking question that invites
     clinical/technical discussion. NOT "what do you think?" — make it
     specific (e.g., "What prospective validation framework would move
     this from benchmark to bedside?").
- **Headlines use specific numbers**, not vague claims. "88.9%
  diagnostic accuracy" beats "high accuracy".
- **Fair/balance baked in**: the body must mention both the result
  AND at least 2 honest limitations. If the slides say "X% better than
  physicians", the post must name the validation gap (simulated
  patients, retrospective design, single-dataset, no outcome measure,
  etc.).
- **Hype-word blacklist**: no "groundbreaking", "revolutionary",
  "game-changing", "disruptive", "unprecedented", "stunning",
  "amazing", "remarkable", "excited to announce", "huge step",
  "this changes everything".
- **No DOI in the post copy** — DOI lives on slide 7 as a visual CTA.
- **No source citation in the post copy** — never author names, never
  "et al.", never journal+year. The post is about the finding.
- **No "we/our"** — brand is "AIPharmaXchange", use third person.
- **No emojis in the body**; at most one emoji in hashtags.
- **Attribution**: end with "— AIPharmaXchange".
- **Hashtags**: 3-5 max, healthcare AI relevant.

Validation: post copy passes if length 1500-1800, zero hype words from
blacklist, ≥2 limitations mentioned, ends with "— AIPharmaXchange",
no "we"/"our", no author names, no DOI, no journal+year, **AI jargon
glossed on first use** (audience-fit check).

## Paperclip wrapper integration (the production path)

`/Users/vivgatesai/.hermes/scripts/paperclip_wrap_carousel.py` is the
production entry point. It mirrors the daily/newsletter wrapper pattern
(grep `paperclip_wrap_*.py` for the family):

```bash
# Manual run on a specific paper
python3 paperclip_wrap_carousel.py --paper=/path/to/paper.pdf

# Pick the newest unprocessed paper from a directory
python3 paperclip_wrap_carousel.py --input-dir=/Users/vivgatesai/.hermes/cache/documents/

# Re-run from existing artifacts (skips the orchestration; just creates
# the issue, attaches assets, marks done)
python3 paperclip_wrap_carousel.py --from-existing=/tmp/mira_final/<slug>
```

The wrapper:
1. Loads env from `~/.paperclip/instances/default/.env`
2. Sets the working Venice key (third key from Hermes config)
3. Sets `CAROUSEL_NO_EMAIL=1` so the orchestration skips its SMTP send
4. Calls the orchestration with a paper-specific output dir
   (`/tmp/mira_final/<paper-stem>/`) so multiple runs don't clobber
   each other
5. Reads `spec.json`, `reviews.json`, `post_copy.txt` from that dir
6. Creates a Paperclip issue (`/api/companies/{id}/issues`) with
   description listing paper title, headline, slide count, post-copy
   length, model, cost
7. PATCHes the issue to `done` with a 90s retry loop (Paperclip's
   auto-continuation flips status back to "blocked" for 30-90s — see
   `paperclip-status-transition` skill)
8. Posts a summary comment with all reviewer scores
9. Attaches all assets as work products (PNG, PDF, ZIP, post copy,
   spec.json, reviews.json)
10. Marks the paper stem in `~/.paperclip/state/processed_carousels.txt`
    so `--input-dir` mode skips it next time

The Paperclip delivery daemon then emails `vivek@live.de` from
"AI CEO AIPharmaXchange" with the issue + attachments.

A daily cron at 10am (`job_id c16cdb5da1af`) runs the same wrapper
with `--input-dir=/Users/vivgatesai/.hermes/cache/documents/`. If no
new papers are present, exits silently with no email.

## See also

- `social-carousel-generation` SKILL.md (creative) — the newer
  carousel skill. Use this for new work. Has the model-selection
  matrix, the "no Pillow for text overlay" hard constraint, the
  watercolor + 1024×1280 size guide, and the 15-pitfall list.
  This skill (`editorial-carousel-orchestration`) is the older
  one and is kept for the 4-agent Paperclip orchestration
  pattern and the budget context.
- `editorial-rigor` SKILL.md — pre-publish editorial checklist
  (Type 2, accuracy, fair/balance, bias) that this pipeline
  bakes into the 3 reviewers
- `branded-infographic` SKILL.md — the watercolor + brand-palette
  reference. Where this skill says "use image model for text",
  `branded-infographic` says "use Pillow overlay for data-heavy
  infographics" — those are different deliverables, follow
  whichever skill covers the artifact you're making.
- `venice-api` SKILL.md — Venice API endpoints, image response
  format compat, JSON-mode requirement
- `paperclip-delivery-daemon` SKILL.md — how the carousel
  reaches the user (email routing, FROM display name, daemon
  state)
- `references/mira-measurement-run.md` — the 2026-06-18
  measurement transcript with the exact prompt templates and
  reviewer prompts
- `references/v2-company-rebuild-2026-06-19.md` — the wipe-and-rebuild
  transcript for AIPharmaXchange v1 → v2 (archived old company, created
  fresh 4-agent carousel unit, new Venice key, audience-fit rule
  injected). Includes the DELETE FK violation, the archive-not-delete
  pattern, and the new agent IDs.
- `scripts/carousel_pipeline.py` — reusable single-file
  pipeline (CEO → render → 3 reviewers → PDF + ZIP)
- `scripts/stage_carousel_outputs.py` (2026-06-27) — stage an
  already-rendered carousel (PNGs + PDF + ZIP + post + spec + reviews)
  into the `/tmp/mira_final/<slug>/` layout that
  `paperclip_wrap_carousel.py --from-existing=<dir>` expects. Use
  after running the orchestration in a separate context, or when you've
  hand-rendered slides and want to push them through Paperclip + email
  delivery without re-running the full pipeline.
