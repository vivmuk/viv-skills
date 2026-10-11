---
name: content-marketing-pipeline
version: 0.2.0
description: AI-driven content marketing pipeline — research → strategy → content calendar → visuals → distribution. Multi-agent orchestration for LinkedIn, newsletters, websites, and GitHub. Includes the reviewer-gated 4-agent pipeline (writer + 3 reviewers) for high-stakes deliverables.
tags: [marketing, content-calendar, linkedin, newsletter, multi-agent, carousel, visual-content]
triggers:
  - content calendar
  - marketing pipeline
  - linkedin posts
  - newsletter content
  - content strategy
  - social media calendar
  - post ideas
  - carousel
  - marketing arm
  - reviewer-gated
  - writer-reviewer pipeline
  - paper-to-carousel
---

# Content Marketing Pipeline

Orchestrate an AI-driven content marketing machine: research a topic, generate a multi-day content calendar, create visual assets (carousels, infographics, hero images), and prepare distribution to LinkedIn, newsletters, website, and GitHub.

## When to Use

Trigger this skill when the user asks to:
- Create a content calendar or posting schedule
- Build a marketing arm for a brand/community
- Generate social media posts from research/papers/articles
- Produce LinkedIn carousels or visual content at scale
- Set up a content pipeline from research to distribution
- Generate N post ideas for X days

## Core Workflow

### Phase 1: Research & Intelligence

1. **Gather source material** — Accept PDFs, URLs, papers, or raw text. Extract key findings, statistics, quotes, and implications.
2. **Scan online conversation** — Use web search to find what people are saying about the topic: reactions, critiques, hot takes, industry commentary. This grounds the content in real discourse.
3. **Synthesize into a research brief** — Distill into: key findings, counter-arguments, industry implications, and 3-5 "angles" that would resonate with the target audience.

### Phase 2: Content Calendar Generation

1. **Define cadence** — Default: 3 posts/day × 7 days (21 posts). Adjust to user preference.
2. **Mix post types** across the calendar for variety and engagement:
   - Statistic spotlight / Data visualization
   - Quote graphic / Expert commentary
   - Comparison carousel / Myth-busting
   - Thought leadership / Controversial take
   - Quick tip / FAQ
   - Poll question / UGC prompt
   - Case study / Behind-the-scenes
   - Resource roundup / Call for collaboration
3. **Each post entry should include**: day, time slot, post type, hook (opening line), 3 bullet points, visual description, hashtags, CTA.
4. **Save as structured JSON** — `content_calendar.json` for programmatic downstream use.

### Phase 3: Visual Asset Production

Use Venice API for image generation. Two-tier approach:

1. **Draft tier** — `flux-2-max` (~20-50s per image). Use for iterations, concept testing, and bulk carousel slides.
2. **Final tier** — `gpt-image-2` (~225s per image). Use for hero images, key slides with text rendering, and final deliverables.

### Carousel design pattern (5-slide LinkedIn carousel)

Optimal structure for LinkedIn carousels that drive engagement:

1. **Slide 1 — Hook/Cover**: Bold title, provocative subtitle, brand logo, swipe indicator. "The results will surprise you" style hooks work well.
2. **Slide 2 — Key Data Point**: One chart or comparison with the strongest statistic. Bar charts with 4-6 items work best.
3. **Slide 3 — Second Data Point**: Different angle on the same topic. Gap/contrast visualization is powerful.
4. **Slide 4 — Insight/Myth-bust**: Challenge an assumption with data. "Specialized ≠ Safer" style reveals drive saves/shares.
5. **Slide 5 — CTA/Summary**: 3 numbered takeaways + follow prompt + community size.

**Carousel prompt consistency rules:**
- Each slide prompt must specify the same color palette, font family, and visual style
- Include `SLIDE N of 5` in every prompt for coherent multi-image generation
- Specify the brand name in each prompt (e.g., "AIPharmaXchange in teal" at bottom)
- Use 4:5 aspect ratio for LinkedIn carousels
- Keep each prompt under 1499 chars (Venice API gateway cap)

**Watercolor professional style base prompt** (append to each slide prompt):
```
Professional watercolor illustration style. Soft teal #2BA39B watercolor wash accents, mint #8FD3B6 secondary washes, cream #F5F0E1 background, dark navy #1E3A5F text. Elegant watercolor bleeding edges. Clean Inter font. Medical research presentation.
```

**Current AIPharmaXchange carousel palette** (June 2026, set by the user via reference image — supersedes the older #00D4AA / #FEFCF8 spec in earlier carousel work):
- Teal `#2BA39B` (primary accent, circles, borders, watercolor wash)
- Mint `#8FD3B6` (secondary wash, lower-left corner pigment pools)
- Navy `#1E3A5F` (text, headings, title)
- Cream `#F5F0E1` (paper base, card fills)

The earlier teal `#00D4AA` / cream `#FEFCF8` palette is still valid for some other visuals but does NOT match the current carousel. Use `#2BA39B / #8FD3B6 / #1E3A5F / #F5F0E1` for the carousel series unless the user says otherwise.

**Aspect ratio options** (Venice accepts all of these via `aspect_ratio`):
- **1:1** (1024×1024) — default for square data slides
- **4:5** (864×1080) — portrait for in-feed posts
- **3:4** (864×1152) — portrait for carousel cover + cover-style cards. The user uploaded a 3:4 reference image in June 2026 and explicitly said "use this aspect ratio" — match it for the cover/title slide. Previous carousel cover slides were 3:4.
- **16:9** (1536×864) — landscape for hero/banner visuals

**Model choice for carousels:**
- `grok-imagine-image-quality` — **Best for data-heavy infographic slides AND multi-card text layouts.** ⚠️ Unique response format: `images[]` of plain base64 strings (NOT `data[].b64_json`). Only accepts `model`, `prompt`, `aspect_ratio`, `format`, `hide_watermark`, `safe_mode`. **User's preferred SOTA image model.** Can render 5-card layouts with headings + body copy correctly when the prompt is very explicit about exact text, font, and layout — see `venice-api/references/pillow-overlay-hybrid.md` for the prompt pattern.
- `flux-2-max` — Fastest for draft iterations (~20-50s per slide). Use for batch generation first.
- `gpt-image-2` — Best text rendering for single-line titles but very slow (~225s) and **mangles body text in dense compositions** (verified: garbled words like "poverthart", dropped cards). Use only for single-line title overlays on hero slides.

**For text-heavy carousels with multi-line body copy per slide, use the Pillow-overlay hybrid pattern** in the `venice-api` skill (`references/pillow-overlay-hybrid.md` + `scripts/pillow_infographic.py`). Generate the background with grok-imagine-image-quality, then composite the text (title, cards, body, brand) with PIL. 100% text reliability, exact brand fidelity, and the visual richness of a real generation. The `venice-api` skill is the canonical home for this technique; this skill references it rather than duplicating the code.

**Batch generation strategy:**
- Generate all slides with `flux-2-max` first (fast iteration)
- Re-render the hero/key slide with `gpt-image-2` (best quality)
- Save to `visuals/` directory with descriptive filenames

### Phase 4: Distribution Prep

Map each post to its distribution channel:
- **LinkedIn** — Carousels, thought leadership, polls, expert commentary
- **Newsletter** — Deep dives, research highlights, resource roundups
- **Website/Blog** — Full articles, case studies, FAQ pages
- **GitHub** — Open-sourced templates, research reviews, code examples
- **Email** — DOCX reports with embedded visuals, sent via himalaya SMTP

### DOCX Report Generation (python-docx)

When delivering research as a formatted document (for email or download):

1. **Install**: `pip3 install python-docx --break-system-packages`
2. **Structure**: Title → Executive Summary → Key Findings (with embedded slides) → Data Tables → Implications → Limitations → References
3. **Brand colors**: Use `RGBColor(0x00, 0xD4, 0xAA)` for teal headings, `RGBColor(0x1A, 0x1A, 0x2E)` for navy text
4. **Embed images**: `doc.add_picture(path, width=Inches(5.5))` — compress PNG→JPEG with `sips` first for smaller file sizes
5. **Data tables**: `doc.add_table(rows, cols)` with alternating row colors for readability
6. **Send via himalaya**: Build MIME with attachment → pipe to `himalaya message send` → wipe credentials

```python
from docx import Document
from docx.shared import Inches, Pt, RGBColor

doc = Document()
style = doc.styles['Normal']
style.font.name = 'Inter'
style.font.size = Pt(11)

# Teal heading
title = doc.add_heading('Report Title', level=1)
for run in title.runs:
    run.font.color.rgb = RGBColor(0x00, 0xD4, 0xAA)

# Embedded carousel image
doc.add_picture('/tmp/slide1.png', width=Inches(5.5))

# Data table
table = doc.add_table(rows=4, cols=3)
for i, (model, score, status) in enumerate(data):
    table.rows[i].cells[0].text = model
    table.rows[i].cells[1].text = str(score)
    table.rows[i].cells[2].text = status

doc.save('/tmp/report.docx')
```

**Image compression before Telegram/email delivery:**
```bash
# PNG→JPEG for smaller file sizes (Telegram has upload limits)
sips -s format jpeg -s formatOptions 85 /tmp/slide1.png --out /tmp/slide1.jpg
```

### Daily Automated Pipeline (Cron Job — current "thrifty" contract, June 2026)

The current daily pipeline is a **single-pass, single-day deliverable** — not the older 5-slide-with-DOCX-report pattern documented in `references/daily-post-generator.md` (that reference is kept as a historical template for one-off report jobs; the cron path no longer uses it).

**Thrifty defaults (intentional — do not "improve" upward without operator sign-off):**
- **3 AI pharma topics**, 1 scrape each (was 8 topics × 2–3 scrapes = 16–24 Augment calls/day)
- **2 content variants** per day: LinkedIn carousel + Newsletter body. Twitter thread dropped.
- **All agents on `gemma-4-uncensored`** ($0.16 / $0.50 per M tokens). Do NOT route any agent through `openai-gpt-55-pro` or `grok-4-20` for the daily cron — they blow the cost envelope.
- **Images on `flux-2-pro`** ($0.04/img). Was `flux-2-max` ($0.09). The downgrade is acceptable here because carousels are image-prompt-light.
- **Expected daily cost:** $0.25–$0.50.
- **Hard cap: 10 Diem/day.** The pipeline itself enforces a finer-grained internal cap (passed via `--no-budget-cap` because the pre-flight already verified budget headroom).

**Two-step cron contract (the pre-flight is a separate, auditable step):**

```bash
cd /Users/vivgatesai/.paperclip/workspaces/aipharmaxchange \
  && set -a && . /Users/vivgatesai/.paperclip/instances/default/.env && set +a \
  && python3 -c "
import model_pricing
s = model_pricing.check_budget_and_alert()
if s['spent_usd'] >= s['cap_usd']:
    print(f\"ABORT: today's spend \${s['spent_usd']:.4f} already at cap \${s['cap_usd']:.2f}\")
    raise SystemExit(1)
print(f\"OK: \${s['spent_usd']:.4f}/\${s['cap_usd']:.2f}\")
" \
  && python3 daily_post_generator.py --no-budget-cap
```

- The pre-flight calls `model_pricing.check_budget_and_alert()`. If `spent >= cap` it **aborts before any spend**. This is a hard, explicit abort — DO NOT silently retry the pipeline.
- The `--no-budget-cap` flag on the pipeline tells the script to skip its internal cap (the pre-flight is the authoritative gate). The script still logs cost.
- Telegram alerts at **50% / 75% / 90% of the daily cap are automatic inside the pipeline** — do NOT manually send these from the cron agent; they're already wired.
- **Run the entire two-step contract in ONE `terminal()` call** — do NOT split the pre-flight into its own call "to inspect the output before launching" or for any other convenience. Cross-call env persistence from the Hermes `terminal()` tool is unreliable for Python subprocesses spawned from a fresh shell; the second call will see `os.environ` without the `.env`-sourced vars and the pipeline will die instantly on `VENICE_API_KEY not set`. Pitfall #21 below has the full diagnosis.

**Success path (after pipeline returns 0):**

Send a one-line Telegram summary via `hermes send` (NOT the agent's own `send_message` — those are different channels):

```
Daily: variant <X> won from '<source title>', $<Y> cost, $<Z> cumulative today
```

Example: `Daily: variant linkedin_carousel won from 'AI drug repurposing: Phase 2 results', $0.31 cost, $0.31 cumulative today`

**Failure path (pre-flight abort OR pipeline non-zero exit):**

Do NOT send the Telegram summary. Just report the error in the final response — the cron delivery mechanism (Paperclip daemon, Telegram auto-deliver, whatever the cron is wired to) carries the message to the user. Common failure modes:

| Symptom | Root cause | Fix |
|---|---|---|
| `news_harvester returned no items` + HTTP 401 from `api.venice.ai/api/v1/augment/search` | `VENICE_API_KEY` in `.env` is invalid/expired/leaked | Regenerate key at venice.ai → API settings → rewrite `.env`. **First** run the diagnostic in `references/venice-401-diagnostic.md` (persistent-vs-transient check + direct probe) — only persistent ≥3-day outages need a rotation; single-day blips can retry. |
| `DIEM spend limit exceeded (HTTP 402)` on every image call | Per-key DIEM cap hit | Operator raises spend limit OR switches to a different API key |
| Pipeline runs but `ab_judge` returns no winner | All variants scored below threshold | Lower confidence floor in `ab_judge.py` OR add more candidate variants |
| Pre-flight aborts at `spent >= cap` | Yesterday's run already exhausted budget | Skip today, retry tomorrow; do NOT retry today |

**Cron job setup (Hermes CLI):**
```bash
hermes cron create \
  --name "AIPharmaXchange Daily Content" \
  --schedule "0 9 * * *" \
  --no-agent \
  --script paperclip_wrap_daily.py \
  --deliver local \
  --workdir /Users/vivgatesai/.paperclip/workspaces/aipharmaxchange
```

The cron invokes a wrapper (`paperclip_wrap_daily.py`) that runs the pipeline AND routes the result through Paperclip for delivery — see `paperclip-delivery-daemon` for the wrapper pattern. `--no-agent` makes this a script-only cron (no LLM). The script's stdout is the daily summary; the daemon delivers the actual carousel/newsletter artifacts via Gmail.

The cron prompt should embed the brand guidelines (palette, tone, audience-fit rule), the thrifty contract above, the success/failure reporting rules, and the explicit "DO NOT silently retry on pre-flight abort" instruction.

## Reviewer-gated pipeline (writer + N reviewers pattern)

When the deliverable is high-stakes (a published carousel, a paper-to-thread post, a marketing visual that will be reviewed by humans) use a **reviewer-gated pipeline** instead of a single-shot generation. The shape: one writer agent produces the artifact, N specialist reviewers score it against a strict rubric, and the pipeline caps at **2 attempts** before killing the run with a postmortem.

This is the pattern the user adopted for paper-to-medical-carousel work in June 2026, and it generalizes to any artifact that benefits from independent quality gates (post drafts, designs, code reviews).

### The 4-agent shape (canonical example)

For a 7-slide medical carousel generated from a peer-reviewed paper:

| Agent | Role | What it does | What it does NOT do |
|---|---|---|---|
| **CEO (medical writer)** | Writer | Reads the paper, writes a 7-slide spec (title, bullets, paper citation per slide). One pass. | Does not delegate the writing. Does not call image gen. Does not approve its own work. |
| **Researcher (Accuracy Reviewer)** | Gate 1 | Verifies every claim against the paper. Demands page-level citations. Flags hype words. Verifies slide 6 (limitations) has ≥4 honest limitations. | Does not check layout, palette, or tone. Does not write content. |
| **PM (Alignment Reviewer)** | Gate 2 | Reads the rendered PNGs. Checks text fits, no clipping, hierarchy clear, slide set looks coherent. | Does not check claim accuracy or brand palette. |
| **Designer (Brand Reviewer)** | Gate 3 (runs on both passes) | Text spec: tone, hype words, CTA cleanliness. Rendered PNGs: palette compliance, typography, wordmark placement, consistency. | Does not check layout or claim accuracy. |

All three reviewers run **in parallel** on each pass. The pipeline aggregates verdicts. A single FAIL from any reviewer triggers a revision.

### The 2-attempt cap (hard quality gate)

After both reviewers score the text spec → 1st attempt.
After the pipeline renders 7 PNGs → 2nd attempt (all 3 reviewers on the images).
After 2 failed attempts → **kill the carousel, write a short postmortem, stop**. The user explicitly framed this as a quality gate, not a budget: "Otherwise, we make it no more than two times" (2026-06-17, MIRA carousel setup). Better to ship a smaller, correct set of slides than to thrash.

**Pipeline pseudocode:**

```python
# Pass 1: text spec
spec = ceo_write_spec(paper)              # CEO writes 7-slide JSON spec
verdicts_text = run_three_reviewers(spec) # parallel: accuracy, brand
if any FAIL in verdicts_text:
    if attempt >= 2: write_postmortem(); return
    spec = ceo_revise(spec, verdicts_text)
    attempt += 1

# Render
for slide in spec.slides:
    render_with_venice_image(slide)        # 7 PNGs

# Pass 2: rendered images
verdicts_img = run_three_reviewers_on_pngs(rendered_pngs)  # parallel: accuracy, alignment, brand
if any FAIL in verdicts_img:
    if attempt >= 2: write_postmortem(); return
    # otherwise re-revise text spec, re-render (attempt 2)
    spec = ceo_revise(spec, verdicts_img)
    re_render(spec)

# Assemble deliverable
assemble_pdf_zip(spec, rendered_pngs)
deliver_to_telegram_and_email()
```

### The 8-slide spine (paper-to-carousel template, AIPharmaXchange v2)

Use this exact spine for every paper-to-carousel job in the AIPharmaXchange carousel unit. The 8th slide (Follow CTA) is mandatory — it drives follower growth and the user has explicit, repeated demand for it. The MIRA / AMIE carousels shipped in June 2026 used this 8-slide shape.

1. **Title card** — paper title, journal/year, one-line headline finding (number-led), stylized illustration. Strip author names from the rendered slide; the source PDF is attached to the issue for cross-reference, not displayed on the slide.
2. **What the system does** — capabilities and scope, no judgment, no spin. **Audience-fit rule below applies here hardest** — this is where AI jargon lives.
3. **Headline result(s)** — the numeric wins, always cited to paper page. Mandatory chart or per-condition breakdown on this slide.
4. **Workflow fidelity / detail** — secondary results, safety data, methodology. Mandatory chart (small-multiples, metric grid, or comparison).
5. **Trend context** — where this fits in the field's arc (e.g., chat CDSS → integrated EHR agents; Q&A benchmarks → agentic systems). State the shift factually with a 2-system comparison, not as a victory lap. 4-stage timeline works well here.
6. **Limitations (MANDATORY)** — ≥4 honest, structural limitations from the paper's own limitations section + 1 field-level caveat (training-data overlap, simulation vs real, retrospective, governance). Tone is "what this paper does NOT show". **This slide must always exist. It is not optional.**
7. **Implications + DOI CTA** — 3-4 takeaways for clinicians/researchers/pharma, plus the paper DOI as a clickable CTA. The DOI is the only formal reference on any slide.
8. **Follow CTA (MANDATORY)** — "THANKS FOR READING" + "FOLLOW AIPharmaXchange ON LINKEDIN" + brand-marked pill button + "More papers decoded every week" tagline. **This slide is mandatory; it drives follower growth.** No source citations on this slide (it's brand promotion, not paper evidence).

**Footer rules (every slide):** brand wordmark `● AIPharmaXchange` bottom-left. Swipe cue bottom-right: `swipe →` on slides 1-7, `swipe done ✓` on slide 8.

**Audience-fit rule (LOCKED — applies to every slide AND the LinkedIn post copy):**

The audience is **pharma experts who may or may not know AI**. They know R&D, clinical, regulatory, safety, medical, and commercial pharma deeply. They may NOT know what "RxQA", "retrieval-augmented generation", "non-inferiority margin", "Gemini 1.5 Flash", "OSCE", "RLHF", "transformer", "RAG", or "LLM" mean. Apply these three rules on every slide:

- **Keep pharma terms native (no translation needed):** "primary endpoint", "IRB", "indication", "AKI", "ECG", "PCP", "NICE guideline", "OSCE", "AKI", "indication", "label expansion", "Phase III", "AKT inhibitor", etc.
- **Soften AI jargon:** drop the AI term when a plain phrase works ("the AI assistant", "the system" beat "the LLM-powered conversational agent"). When you keep an AI term, gloss it once in plain English on first use inside the bullets ("retrieval-augmented generation — pulling in relevant guidelines on demand").
- **Make it relatable:** connect the AI method to a workflow they recognize. One analogy per slide is enough — don't make every sentence an analogy. Examples that work: "like a junior resident who has read every NICE guideline and never sleeps", "a 24/7 medical librarian that never loses focus", "the same way a senior reviewer cross-checks your IND filing", "imagine a tireless safety reviewer with infinite recall of every FAERS case".

This rule came from a direct user correction (2026-06-19): "make sure that the posts are for an audience that may or may not be an AI expert. I think that was missing from last night's work but are all pharma experts, so make it relatable to them while also providing enough technical pieces to explain the papers around AI." It supersedes the prior "plain language for clinicians" framing — pharma terms no longer need translation, only AI terms do. The rule is also embedded in MEMORY.md user profile so future sessions start already knowing it.

The 8-slide spine pairs with the `editorial-rigor` skill — the limitations slide is the operationalized output of the "Fair / balance check" pass.

### Reviewer verdict format (terse, no prose)

All reviewers respond in this exact format. The pipeline parses the verdict to decide pass/fail:

```
VERDICT: PASS
REASON: <one line, can be empty if trivially passing>

VERDICT: FAIL
REASON: <one line>
ISSUES:
- slide N: <specific claim> — paper says X, you wrote Y, page Z
- slide N: hype word "..." — remove
- slide N: missing page citation — add
- slide M: extrapolation — paper tested on 8 conditions, you wrote "many"
- limitations: missing limitation X — add or strengthen
- trend framing: unsupported claim — paper does not claim this
```

Max 5 issues per pass. Top 5 by severity. No prose explanations.

### Where this pattern lives in the codebase

- **Pipeline script**: `~/.paperclip/workspaces/aipharmaxchange/carousel_pipeline.py` (paper-to-carousel reference implementation)
- **7-slide spine + 3 reviewer system prompts**: `content-marketing-pipeline/references/reviewer-gated-carousel.md`
- **Per-attempt postmortem**: writes to `<output>/carousels/<slug>/POSTMORTEM.md` with the final verdicts and top 5 issues

### When to use this pattern

Use the reviewer-gated pipeline when:
- The deliverable is published under a brand name (LinkedIn carousel, newsletter hero, marketing visual)
- The source material is a peer-reviewed paper, a high-stakes brief, or a piece of writing the user will personally review
- Errors are expensive (a hallucinated citation on a medical carousel is worse than no carousel)

Skip the reviewer-gated pipeline when:
- The deliverable is internal (a draft for the user to revise, a low-stakes ad-hoc visual)
- Speed matters more than correctness
- The user explicitly says "just ship it"

## Paperclip scope: focused orchestration only

The user's standing preference (2026-06-17, MIRA carousel setup): **use Paperclip for focused orchestration units, not for the full content marketing stack.** Research, social posting, newsletter production, and LinkedIn growth are separate work streams handled in the Hermes environment, not delegated to Paperclip agents.

Practical implications:
- When you set up a Paperclip company, disable the agents that aren't in the current orchestration unit (PATCH `status: "paused"`). Keep only the 4 agents in the active unit.
- The default 10-agent org (CEO, CTO, CMO, ContentDirector, ResearchAnalyst, etc.) is a *template*, not a target. Right-size the org to the unit.
- Don't add CMO/MarketingDirector if the unit is just paper-to-carousel. The CEO-as-writer pattern subsumes the CMO's role for that specific unit.
- The same applies to research agents: paper-to-carousel reads the paper directly, no ResearchAnalyst/Synthesizer intermediate needed.

The reason: a 10-agent org with idle CTO + CMO + ResearchAnalyst + NewsletterEditor + 3 others generates 200+ Paperclip issues per day and 0 shipped deliverables. The reviewer-gated 4-agent unit ships 1 carousel per cycle.

## Multi-Agent Orchestration (Paperclip AI)

When Paperclip AI is available, use it to create a persistent org of specialized agents. **Default to the reviewer-gated pipeline shape (above) — a focused 4-agent unit, not the full 10-agent template.**

### Web UI (primary interaction)

Paperclip runs a web UI at `http://127.0.0.1:3100`. The onboarding wizard is at `/onboarding` and is a 4-step modal:

1. **Company** — Name + mission/goal
2. **Agent** — Name, adapter type (Claude Code / Codex / more), model selector, environment check ("Test now" button probes the adapter CLI)
3. **Task** — Title + description for the agent's first task
4. **Launch** — Review summary, then "Create & Open Task"

**Navigation** (left sidebar):
- Dashboard, Inbox, Tasks, Routines, Goals, Artifacts
- Projects (collapsible, per-company)
- Agents (collapsible, lists all agents in current company)
- Org, Skills, Costs, Activity, Settings

**Workspace switcher** — Top of sidebar, shows current company name + initial. Click to switch between companies. The "Create another company" banner with "Start Onboarding" button appears after the first company is set up.

### CLI / API (alternative)

1. **Install & start Paperclip**: `npm install -g paperclipai && paperclipai onboard --yes --run`
2. **Create company**: `POST /api/companies` with name, brandColor, industry
3. **Create agents** with these role mappings:

| Agent Role | Paperclip Role | Purpose |
|------------|----------------|---------|
| CEO/Founder | `ceo` | Strategy, approvals |
| Content Director | `cmo` | Content strategy, editorial |
| LinkedIn Strategist | `pm` | Platform-specific content |
| Newsletter Editor | `designer` | Newsletter curation & layout |
| Research Analyst | `researcher` | Paper scanning, data extraction |
| Research Synthesizer | `researcher` | Trend synthesis, implications |
| GitHub OSS Lead | `engineer` | Open-source use-case docs |
| Marketing Director | `cmo` | Campaign orchestration |

4. **Create projects** and assign agents to goals within each project
5. **Integrate Venice API** via process adapter (shell script that calls Venice chat completions)

### Venice Adapter Pattern (Paperclip)

Create a Python adapter at `~/.paperclip/adapters/venice-adapter.py` that:
- Reads `PAPERCLIP_TASK` env var for the task prompt
- Reads `VENICE_API_KEY` env var for authentication
- Calls `POST https://api.venice.ai/api/v1/chat/completions`
- Returns the response text to stdout

Paperclip invokes this as a "process" type agent. Each agent gets the same adapter but different system prompts via Paperclip's agent config.

## GitHub Open-Source Repo Structure

When the user wants to open-source AI use cases:

```
<org>/use-cases/
├── README.md                    # Mission, how to contribute
├── CONTRIBUTING.md               # PR template, review process
├── CODE_OF_CONDUCT.md
├── LICENSE                       # MIT recommended
├── research/
│   └── <paper-slug>/
│       └── review.md            # Full paper review with data
├── use-cases/
│   ├── rd/                      # R&D use cases
│   ├── clinical/                # Clinical trial use cases
│   ├── regulatory/              # Regulatory/compliance
│   ├── safety/                  # Pharmacovigilance
│   ├── medical-affairs/         # Medical affairs / MSL
│   └── commercial/              # Commercial/market access
└── templates/
    └── use-case-template.md     # Reusable template
```

## Pitfalls

1. **Venice API key mismatch / malformed value / scope-limited** — Three distinct failure modes, all of which surface as `HTTP 401 {"error":"Authentication failed"}` from `/v1/augment/search`:
   - **Mismatch mode (intermittent)**: The key in `~/.hermes/config.yaml` may differ from env vars or other config files. When auth fails, check both: `grep -A2 venice ~/.hermes/config.yaml` AND `. /Users/vivgatesai/.paperclip/instances/default/.env && echo "\${VENI...Y:0:8}"`. Both should match.
   - **Malformed-value mode (permanent — every call fails)**: The `VENICE_API_KEY` value in `.env` is itself invalid — typically a placeholder, a leaked variable-name fragment, or a corrupted copy-paste. Diagnostic: load the env, then `print(f'len={len(v)} first10={v[:10]!r}')`. A valid Venice key is 30+ random alphanumeric chars. Real Venice inference keys have a recognizable prefix **`VENICE_INFERENCE_KEY__`** followed by a base64-ish random tail — that prefix is NOT corruption, it's the actual key format. The corruption signal is one of: (a) the value is truncated (e.g. literal `VENICE_INF` with no `ERENCE_KEY__...` continuation), (b) the value reads as a dictionary word like `your_key_here` or `placeholder`, or (c) `VENICE_API_KEY` and `VENICE_INFERENCE_KEY` hold IDENTICAL values — real deployments use distinct keys or both are leaked from the same session. Fix: regenerate at venice.ai → Settings → API Keys, rewrite both fields. Do NOT retry the pipeline — every call will 401 until the key is fixed.
   - **Scope-limited mode (the silent killer)**: The key IS valid and properly formatted — but it lacks the augment/inference scope that `/v1/augment/*` and `/v1/chat/completions` require. Symptom: same `HTTP 401` on those endpoints, BUT `GET /v1/models` returns 200 with the same key. The pipeline's step [1/7] `refresh_pricing()` (which calls `/v1/models`) succeeds, which masks the scope issue. Diagnostic: run the Step 2.5 probe in `references/venice-401-diagnostic.md` — the `200 | 401 | 401 | 401` row in the discriminator matrix. Resolution path is operator-side: regenerate the key with the augment scope enabled at venice.ai → API settings, OR swap the search backend (Tavily, SerpAPI, Brave) in `news_harvester.py`. This mode is the most common cause after a plan downgrade or scope migration; it can persist for weeks silently because `/v1/models` 200 keeps the pipeline's pricing step green.
2. **`gpt-image-2` timeout** — Default HTTP timeouts (60s) are too short. Set timeout ≥300s when generating with this model. Use `flux-2-max` for drafts first, then only the final image with `gpt-image-2`.
3. **Venice image prompt limit is 1500 chars for ALL models** — The API gateway hard-caps `prompt` at 1500 chars regardless of model (gpt-image-2 spec says 10K, nano-banana-2 says 32K — both are gateway-capped at 1500). Prioritize: section titles > data points > layout > color scheme.
4. **Venice REST API image params** — Use `size` (e.g., `"1024x1024"`) NOT `width`/`height`/`style_preset` when calling the REST endpoint directly. The MCP tool handles the translation, but direct REST calls do not.
5. **Paperclip agent role enum** — Only these values are valid: `ceo, cto, cmo, cfo, security, engineer, designer, pm, qa, devops, researcher, general`. Using anything else returns a validation error.
4. **Paperclip `PATCH /api/agents/:id`** is the right path. Returns 200 with the patched agent. The CLI is the alternative (`paperclipai agent update <id> -C <companyId> --payload-json '{...}'`) but the REST endpoint does work. The actual gotcha is that the API rejects `"REDACTED"` placeholders for secrets and rejects a `permissions` field in the PATCH body (schema is "never" for that field) — for env like `VENICE_API_KEY` you must pass the real value, read from `~/.paperclip/instances/default/.env` if needed.
7. **Content calendar should be JSON** — Not markdown. JSON enables programmatic downstream use (auto-posting, scheduling, template rendering).
8. **Subagent timeouts for image gen** — Image generation with `gpt-image-2` can take 2-4 minutes per image. Delegate with generous timeouts, or use `flux-2-max` in subagents and only `gpt-image-2` in the main thread.
9. **Batch carousel prompts must be consistent** — Each slide prompt should specify the same color palette, font family, and visual style. Without this, slides look like they came from different designers.
10. **Don't use serif fonts for AIPharmaXchange carousel titles** — The actual carousel uses a **bold condensed sans-serif** (Druk Wide / Anton style) for titles, NOT a serif. The original brand brief said "Fraunces + Inter" but the carousel is rendered in the condensed-sans style. If you re-render a slide and use a serif, it breaks visual continuity with the series. Apple system fallback: `Avenir Next Condensed` at heavy weight.
11. **Hex codes in prompt color specs can leak into the brand mark** — When the prompt mentions a color hex code (e.g., "teal #00D4AA"), the image model sometimes includes the literal hex code as part of the bottom-right brand mark text (rendering as `#00D4AA • AIPharmaXchange` instead of `• AIPharmaXchange`). Workaround: in the prompt, explicitly say *"Bottom right corner: ONLY the wordmark 'AIPharmaXchange' preceded by a single small teal dot. No hex codes, no other symbols, no numbers, no other words anywhere in the corner."* Image-edit models (`flux-2-max-edit`, `qwen-image-edit`, etc.) are too aggressive to fix this surgically — they wipe unrelated content. Regenerate with the explicit exclusion.
12. **For scientific critique content, lead with structural/methodological gaps** — When the user asks for a critical take on a study, favor limitations that are *structural* (no clinical outcomes measured, no baseline comparison, contamination is unverifiable, single-turn Q&A ≠ clinical decision) over *motive* claims about the authors (conflict of interest, retaliatory timing, undisclosed competitors). Structural gaps are defensible; motive claims invite counter-accusations about the publisher's own bias. The user has explicitly asked for "scientific and intellectually honest" framing, free of speculation. The five limitations used in the limitations-of-the-study carousel (June 2026) are a reference set: *No Clinical Outcomes Measured / Static Q&A Is Not a Clinical Decision / HealthBench Weights Style Alongside Correctness / No Baseline Comparison to Standard Care / Training-Data Contamination Is Unverified.*
13. **All image models mangle body text in dense scenes** — For 5-card slides with body copy, `gpt-image-2` returns garbled words and sometimes drops entire cards. Don't trust image-gen text rendering for anything beyond single-line titles. Use the Pillow overlay hybrid (see Carousel section above). **EXCEPTION**: `grok-imagine-image-quality` CAN render multi-card text correctly when the prompt is very explicit — include the exact text strings, font family ("bold condensed sans-serif, Druk Wide / Anton style"), and card structure in the prompt. See `venice-api/references/pillow-overlay-hybrid.md` for the prompt-engineering pattern.
14. **Bash mangles `***REDACTED***` literals in source files** — When a Python script (or any file written through bash heredoc / `write_file`) contains the literal string `***REDACTED***`, the closing characters get stripped, leaving an unterminated string literal. Symptom: `SyntaxError: EOL while scanning string literal` at the `***REDACTED***` site. Workarounds in priority order: (a) Build the string at runtime via concatenation — e.g., `prefix = "VENICE_API_KEY=*** + "X" * 16`. (b) Put the API-key prefix detection in a tiny standalone bash helper (`/tmp/load_venice_key.sh`) and call it via `subprocess.check_output`. (c) Use environment variables (read the key into `$VENICE_API_KEY` and read that env var in Python). See `venice-api/references/bash-literal-mangling.md` for the helper script and the diagnosis flow.
15. **DIEM spend limit returns 402 across ALL image models simultaneously** — When the user's per-key DIEM cap is hit, every Venice image model (`grok-imagine-image-quality`, `grok-imagine`, `flux-2-max`, `gpt-image-2`, etc.) returns `HTTP 402 {"error":"API key DIEM spend limit exceeded. Your account may still have DIEM balance, but this API key has reached its..."}`. Don't burn time testing alternative models — the cap is per-key, not per-model. Recovery: ask the user to raise the spend limit on the specific API key (venice.ai → API settings), or to use a different key. The chat/text models (`grok-4-20`, `gemma-4-uncensored`, etc.) keep working through image 402s — so the rest of the pipeline (research, copy) can continue. When the user adds capacity, **re-test with the smallest possible image call first** (1:1, short prompt) to confirm before re-running the full carousel generation.
16. **`grok-imagine-image-quality` can leak prompt color hex codes into the brand mark** — When the prompt specifies a color via hex (e.g., "teal #00D4AA"), the model sometimes includes the literal hex code as part of the bottom-right brand mark text, rendering as `#00D4AA • AIPharmaXchange` instead of `• AIPharmaXchange`. Two fixes: (a) In the prompt, explicitly forbid it: *"Bottom right corner: ONLY the wordmark 'AIPharmaXchange' preceded by a single teal dot. No hex codes, no other symbols, no numbers, no other words anywhere in the corner."* (b) Regenerate. Image-edit models (`flux-2-max-edit`, `qwen-image-edit`, `nano-banana-pro-edit`) are too aggressive to fix this surgically — they wipe unrelated content. **Do NOT use the image-edit endpoint for surgical text fixes** — it always rewrites too much. Always regenerate the full slide with the corrected prompt instead.
17. **Pillow doesn't blend with textured watercolor backgrounds** — If a `grok-imagine-image-quality` slide has a paper-textured background and you try to paint over a region with Pillow (e.g., covering a leaked hex code), the flat color rectangle shows through as a visible "patch" because the texture is missing. The text underneath the patch is also visible as ghosting/doubling. **Fix**: regenerate the whole slide with the corrected prompt (option 16a). Do not attempt surgical Pillow fixes on textured backgrounds.
18. **Carousel image-edit endpoint sometimes returns raw PNG bytes instead of JSON** — `POST /api/v1/image/edit` with some models (e.g. `flux-2-max-edit`) returns `Content-Type: image/png` with raw binary, not `{"images": [...]}`. Other models return JSON. Always handle both — check `Content-Type` and the first 8 bytes (PNG signature is `b"\x89PNG"`). Don't blindly `json.loads()` the response. See `venice-api/SKILL.md` for the dual-format parsing snippet.
19. **Augment-endpoint 401 failures leave a *side-channel* spend trace that is NOT in the Diem ledger** — When the Venice augment/search endpoint returns HTTP 401 for every default topic (typical of the scope-limited failure mode above), `news_harvester.py` still increments a local `sources_cost` counter and writes `{"sources_cost": 0.03, "items": []}` to `/tmp/daily_news_<YYYY-MM-DD>.json`. This is INFORMATIONAL bookkeeping for archive/debugging only — `news_harvester.py` does NOT call `model_pricing.record_spend()`. So `model_pricing.check_budget_and_alert()` still returns `$0.0000 / $10.00` for the day even though the /tmp file shows `sources_cost: 0.03`. They are NOT contradictory — they're independent accounting paths: `/tmp/daily_news_*.json` is "what the harvester TRIED to spend" (informational), `model_pricing` is "what was actually debited to Diem" (authoritative, gates the pre-flight). The pipeline should NEVER burn a real 0.03 against the ledger until a successful API response is received. When reading these two files together, treat a non-zero `sources_cost` in /tmp + zero on the ledger as a **positive signal** that the augment path is failing cleanly without burning the cap — *not* a contradiction that suggests the ledger is wrong.
20. **Augment/search 401 is recurring on a weekly timescale — track cadence before recommending key rotation** — The same `news_harvester returned no items + HTTP 401` fingerprint has now fired every day on this cron since at least 2026-06-19 (≥26 consecutive days as of 2026-07-15). A 401 fingerprint on day 1 is a transient suspicion; a 401 fingerprint lasting >3 days is durable evidence of operator-side scope/key state, NOT a transient flake. The diagnostic in `references/venice-401-diagnostic.md` already covers the discriminator; the operational corollary is *don't ask the user to rotate the key on day 1, but DO escalate on day 3 with a clear "this has been failing for N days, please rotate or swap backend" message*. `for f in $(ls -t /tmp/daily_news_*.json | head -10); do echo "$f $(python3 -c 'import json; print(len(json.load(open(\"$f\")).get(\"items\", [])))') items"; done` gives a quick cadence read.
21. **`terminal()` cross-call env propagation is unreliable — always inline `.env` sourcing into the same call as the consumer script** — The system prompt claims "exported environment variables persist between calls", but in practice a Python subprocess launched from a *second* `terminal()` invocation does NOT inherit vars sourced in a *first* call's `set -a && . .env && set +a` block. Symptom: the pipeline crashes instantly with `PIPELINE FAILED: VENICE_API_KEY not set in environment` (or `PAPERCLIP_AGENT_JWT_SECRET`, `OPENAI_API_KEY`, etc. — anything sourced from `.env`), and the budget pre-flight ran cleanly in the prior call because IT was a child of the same shell that sourced `.env`. The split looks innocuous in a transcript but is a real, reproducible fault. Two structural fixes: **(a)** Run the entire two-step cron contract (pre-flight + pipeline) inside ONE `terminal(...)` call, separated by `&&`, exactly as shown in the "Daily Automated Pipeline" section above. Do NOT extract the pre-flight into its own call for "output inspection" — that creates exactly this trap. **(b)** If you genuinely need two steps (rare), explicitly re-source `.env` at the top of every subsequent `terminal()` call: `set -a; . /Users/vivgatesai/.paperclip/instances/default/.env; set +a; python3 path/to/script.py`. The rule generalizes beyond this pipeline: any cron-style invocation that loads secret-bearing env vars MUST inline-load them every time. Diagnosis shortcut: first failed call's transcript will show pre-flight `OK:` line followed by the consumer script's `KEY not set` line, with no intervening API calls.

## Open Design Integration

When Open Design (`http://127.0.0.1:7456`) is running, use it as the primary design engine instead of raw Venice API image calls. Open Design wraps Venice with 155+ skills that produce production-ready HTML/PNG artifacts enforcing DESIGN.md brand contracts.

### Setup

1. **Install**: `git clone <open-design-repo> /tmp/open-design && cd /tmp/open-design && pnpm install`
2. **Requires Node 24+**: `fnm install 24 && fnm use 24`
3. **Wire Venice as BYOK**: Create `~/.open-design/config.json` with `providers.openai.apiKey` and `base_url` pointing to `https://api.venice.ai/api/v1`
4. **Create DESIGN.md**: Place in `/tmp/open-design/design-systems/<brand>/DESIGN.md` following the `design-md` skill schema
5. **Start daemon**: `pnpm dev --no-open` (runs on port 7456)

### Key Skills for Content Marketing

| Skill ID | Use Case |
|----------|----------|
| `card-twitter` | Social card images (LinkedIn, X) |
| `article-magazine` | Long-form article layouts |
| `ad-creative` | Ad/banner creatives |
| `brandkit` | Brand asset generation |
| `canvas-design` | General canvas layouts |
| `stitch-design-taste` | Design quality review |
| `venice-image-generate` | Direct Venice image gen |
| `venice-image-edit` | Venice image editing |

### Brand Guardian Agent Pattern

Create a dedicated agent with `designer` role that:
1. Has all brand-related Open Design skills (`brandkit`, `brand-guidelines`, `color-expert`, `canvas-design`)
2. Reviews all visual output against the DESIGN.md brand contract before publishing
3. Has the DESIGN.md content injected into its system prompt for reference

## Venice API Quick Reference (Image Generation)

```bash
# Flux 2 Max (fast, ~20-50s)
curl -s -X POST https://api.venice.ai/api/v1/images/generations \
  -H "Authorization: Bearer $VENICE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"flux-2-max","prompt":"...","n":1,"size":"1024x1024"}'

# GPT Image 2 (slow, best text, ~225s)
curl -s -X POST https://api.venice.ai/api/v1/images/generations \
  -H "Authorization: Bearer $VENICE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-image-2","prompt":"...","n":1,"size":"1024x1024"}'
```

Response format: `{"data": [{"b64_json": "..."}]}` — decode base64 and save as PNG.

## See Also

- `venice-api` skill — Full Venice API reference, parameter details, model catalog.
  Also covers the bash literal-mangling workaround (`references/bash-literal-mangling.md`)
  for scripts that read API keys.
- `baoyu-infographic` skill — 21 layouts × 21 styles for infographic generation
- `openclaw` skill — OpenClaw agent platform for persistent bot deployment
- `github-repo-management` skill — GitHub org/repo creation and management
- `editorial-rigor` skill — The Pre-Publish Editorial Checklist that applies to
  every critique, limitations write-up, or analytical comparison. Loaded
  automatically by the LinkedInStrategist, NewsletterEditor, ContentDirector,
  BrandGuardian, and MarketingDirector agents in Paperclip.

For the full automated daily post pipeline (cron job pattern, Venice API calls, DOCX generation, email delivery), see `references/daily-post-generator.md`.
For Paperclip web UI structure, onboarding flow, sidebar navigation, and the AIPharmaXchange workspace layout, see `references/paperclip-web-ui.md`.
For the reviewer-gated paper-to-carousel pipeline (4-agent writer + 3 reviewers, 2-attempt cap, 7-slide spine, reviewer system prompts), see `references/reviewer-gated-carousel.md`.
For the Venice augment/search HTTP 401 diagnostic recipe (the persistent-vs-transient check + direct probe that distinguishes "regenerate the key" from "retry once"), see `references/venice-401-diagnostic.md`.
