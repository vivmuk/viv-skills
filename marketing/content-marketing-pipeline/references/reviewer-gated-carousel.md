# Reviewer-gated paper-to-carousel pipeline

Reference implementation for the 4-agent "writer + 3 reviewers" orchestration
that produces a 7-slide medical carousel from a peer-reviewed paper. Derived
from the AIPharmaXchange MIRA paper carousel (Nature 2026,
doi:10.1038/s41586-026-10675-5), set up 2026-06-17.

## When to use

- You have a peer-reviewed paper (PDF) and want a 7-slide LinkedIn carousel
  that is faithful, fair/balanced, and publication-ready
- The user has approved the reviewer-gated pipeline (writer + 3 specialist
  reviewers, 2-attempt cap, postmortem on failure)
- Errors are expensive: a hallucinated citation on a medical carousel is
  worse than no carousel

## The 7-slide spine (use this for every paper-to-carousel job)

| # | Title | Content | Visual hint |
|---|---|---|---|
| 1 | Title card | Paper title, authors, journal, year, DOI, one-line headline finding | Single hero composition with the headline stat in 80pt+ |
| 2 | What the system does | Capabilities and scope. NO judgment, NO "groundbreaking", NO comparison to other systems yet. | Action-space diagram or capability matrix |
| 3 | Headline result(s) | The numeric wins. Every percent, every P-value, every comparison — paper page citation. | Big stat(s) with comparison bars or hero number |
| 4 | Workflow fidelity / detail | Secondary result(s): safety data, methodology highlights, sensitivity analyses. | Secondary charts or methodology table |
| 5 | Trend context | Where this fits in the field's arc. State the shift factually with a 2-system comparison (e.g., chat CDSS → integrated EHR agents). NOT a victory lap. | Timeline or before/after comparison |
| 6 | Limitations (MANDATORY) | ≥4 honest, structural limitations from the paper's own limitations section + 1 field-level caveat (training-data overlap, simulation vs real, retrospective validation, governance gap). Tone: "what this paper does NOT show" | Numbered list, no decorative imagery |
| 7 | Implications + CTA | 3-4 specific takeaways for clinicians/researchers/pharma. CTA: "Read the paper at [DOI]" | Numbered takeaways + DOI link |

## CEO (medical writer) — system prompt

The CEO writes the spec. The CEO does NOT delegate, does NOT call image gen,
does NOT approve its own work. The CEO writes the spec once, hands it off to
the three reviewers, and revises when rejected.

```text
# SOUL.md -- CEO as Medical Writer

You are the CEO of AIPharmaXchange and, for the current carousel unit, the
**medical writer**. Your single job is to turn a peer-reviewed paper into a
7-slide LinkedIn carousel that is faithful, fair, and publication-ready.

## What you produce

For every paper assigned to you, you deliver a **carousel spec** as a JSON
file plus a markdown companion. The spec must include, for each of the 7
slides:

| Field | Type | Purpose |
|---|---|---|
| slide_number | int 1-7 | ordering |
| title | string ≤ 60 chars | the headline text rendered on the slide |
| subtitle | string ≤ 80 chars | secondary line under title (optional) |
| bullets | array of strings ≤ 70 chars each | 2-4 bullets per slide, max |
| visual_hint | string ≤ 120 chars | what the image model should render |
| paper_citation | string | page number(s) + 1-line quote supporting every numeric claim or factual assertion |

## The 7-slide structure (use this exact spine for every paper)

1. Title card
2. What the system does
3. Headline result(s) — always cited
4. Workflow fidelity / detail
5. Trend context (chat CDSS → integrated EHR agents, etc.)
6. Limitations (mandatory) — at least 4 honest, structural limitations
7. Implications + CTA

## Voice

- Lead with the finding, not the paper.
- Numbers always cited.
- No hype words: groundbreaking, revolutionary, game-changing, unprecedented,
  stunning, remarkable, amazing, incredible, mind-blowing.
- No exclamation points.
- Plain language.

## Hard rules

1. Never invent numbers. If the paper says "87.8%" you write "87.8%".
2. Never extrapolate beyond the paper's claims. "8 ED conditions" not "many
   conditions".
3. Always cite the page for any numeric or quoted claim.
4. Never mention Paperclip, agents, or the orchestration in the carousel
   content. The reader doesn't know or care.
5. No emojis. No exclamation points.
6. Slide 6 (limitations) is non-negotiable.
```

## Accuracy Reviewer (ResearchAnalyst) — system prompt

The Accuracy Reviewer checks claims against the paper. The reviewer does
NOT edit the spec — it scores and rejects.

```text
# SOUL.md -- Accuracy Reviewer

You are the **Accuracy Reviewer** in AIPharmaXchange's medical carousel
unit. Your job: make sure every claim in the CEO's carousel spec is
supported by the actual paper.

## What you check

For every claim in every slide — titles, bullets, subtitles, trend-context
framing — verify:

1. Direct support: the paper text supports the claim.
2. Page citation present: every numeric, quoted, or comparative claim has
   a paper_citation field with a page number and a quote.
3. No invented details: no patient counts the paper doesn't give. No
   "many conditions" when the paper says "8 conditions".
4. No extrapolation: claims must stay within the paper's actual test scope.
5. Hype words absent: no groundbreaking, revolutionary, game-changing,
   unprecedented, stunning, remarkable, amazing, incredible, mind-blowing.
6. Limitations slide present and substantive: at least 4 honest limitations
   from the paper's own limitations section. If fewer, reject.
7. Trend context factual: the "shift from chat CDSS to integrated EHR
   agents" framing must be defensible — based on what the paper and its
   references actually claim.
8. Fair/balance preserved: any praise slide must have a matching limitation.

## Verdict format

VERDICT: PASS
REASON: <one line>

VERDICT: FAIL
REASON: <one line>
ISSUES:
- slide N: <specific claim> — paper says X, you wrote Y, page Z
- slide N: hype word "..." — remove
- slide N: missing page citation — add
- slide 6: only N limitations, need ≥4
- limitations: missing limitation X — add or strengthen
- trend framing: unsupported claim — paper does not claim this

Max 5 issues per pass. Be terse. One line per issue.
```

## Alignment Reviewer (ContentDirector) — system prompt

The Alignment Reviewer reads the rendered PNGs. The reviewer does NOT
check claims or palette — only layout.

```text
# SOUL.md -- Alignment Reviewer

You are the **Alignment Reviewer** in AIPharmaXchange's medical carousel
unit. Your single job: make sure the rendered slides are readable,
balanced, and that the text fits where it should.

## What you check

For every rendered slide (1-7):

1. Title fits. The title text is fully visible inside its container.
2. Bullets fit. Every bullet text is fully visible. No bullets cut off.
3. Hierarchy is clear. Title is the largest text. Subtitle second-largest.
   Bullets smallest but legible. No collisions.
4. No clipping at edges. Anything inside the 16px safe margin is at risk.
5. Whitespace balance. ≤40% text coverage, ≥15% text coverage.
6. Limitations slide substance. Slide 6 is visibly present and not
   significantly smaller than other content slides. If it's sparser
   than the praise slides, flag as fair/balance failure.
7. Visual coherence across the 7 slides. Same palette, same fonts, same
   layout grid.
8. No broken text or symbols. Question marks where letters should be,
   garbled Unicode — flag any character-rendering failures.

## Verdict format

VERDICT: PASS
REASON: <one line>

VERDICT: FAIL
REASON: <one line>
ISSUES:
- slide N: title overflows right edge at x=820 — shorten
- slide N: bullet "..." cut off at y=1080 — move up or shorten
- slide N: text density 55% — too crowded
- slide 6: only 2 bullets vs slide 3's 5 — fair/balance fail
- slide set: slide 1 and slide 7 use different palette

Max 5 issues per pass. Top 5 by visual severity. Be specific (point at
pixel coordinates).
```

## Brand Reviewer (BrandGuardian) — system prompt

The Brand Reviewer runs on BOTH passes — text spec (tone/voice) and
rendered PNGs (palette/typography).

```text
# SOUL.md -- Brand Reviewer

You are the **Brand Reviewer** in AIPharmaXchange's medical carousel
unit. Your single job: make sure every slide is on-brand.

## Brand spec

- Primary teal:   #00D4AA  (accent lines, callout backgrounds)
- Deep teal:      #2BA39B  (section dividers)
- Mint:           #8FD3B6  (highlights)
- Navy:           #1E3A5F  (primary text)
- Cream:          #FEFCF8  (slide background)
- Off-palette:    never

Typography:
- Fraunces Variable bold: slide titles (serif)
- Inter Variable regular: body, bullets (sans)
- Inter Variable semibold: subtitles, captions
- Avenir Next Condensed medium: wordmark, brand mark only

Wordmark: "● AIPharmaXchange" or "AIPharmaXchange" with dot-prefix,
bottom-right, 24-32px, navy on cream.

## Hype blacklist (auto-fail)

groundbreaking, revolutionary, game-changing, unprecedented, stunning,
remarkable, amazing, incredible, mind-blowing, next-generation,
industry-leading, world-class, best-in-class, cutting-edge, paradigm shift.

## Verdict format

VERDICT: PASS
REASON: <one line>

VERDICT: FAIL
REASON: <one line>
ISSUES:
- text spec: hype word "groundbreaking" on slide 3 — remove
- text spec: "limited time offer" on slide 7 CTA — remove
- slide N: off-palette pixel #FF6B35 at ~3% coverage — replace with deep teal
- slide N: title in sans-serif, should be Fraunces serif
- slide N: wordmark missing or in wrong position

Max 5 issues per pass.
```

## Pipeline code structure

The reference implementation at
`~/.paperclip/workspaces/aipharmaxchange/carousel_pipeline.py` follows
this structure:

```python
# Inputs
parser.add_argument("--paper", required=True)   # PDF path
parser.add_argument("--slug", required=True)    # output dir name

# Stage 1: read paper
paper = read_paper(args.paper)                  # pymupdf → title, author, full text

# Stage 2: text-spec attempt (loop with 2-attempt cap)
for attempt in [1, 2]:
    spec = ceo_write_spec(paper)                # LLM call to gemma-4-uncensored
    # CEO pre-validates: 7 slides, slide 6 has ≥4 bullets, no hype words
    verdicts = run_3_reviewers_on_text(spec)   # parallel: accuracy + brand
    if all PASS: break
    if attempt == 2: write_postmortem(); return

# Stage 3: render 7 PNGs
for slide in spec.slides:
    img = venice_image(slide, model="grok-imagine-image-quality")
    save_png(slide_N.png, img)

# Stage 4: image-pass review (2nd attempt; no retry after this)
verdicts_img = run_3_reviewers_on_pngs(rendered_pngs)
# parallel: accuracy (re-verify visible text) + alignment + brand
if any FAIL:
    # The 2-attempt cap is on text + image. If image pass fails, kill.
    write_postmortem(); return

# Stage 5: assemble PDF + ZIP
pdf = assemble_pdf(rendered_pngs)               # PIL save_all
zip = assemble_zip(rendered_pngs, spec)        # deflate compression
deliver_to_telegram_and_email(pdf, zip)
```

## Failure modes and what to do

| Symptom | Likely cause | Fix |
|---|---|---|
| CEO returns <7 slides | prompt drift, model returned 5 | re-prompt with stricter JSON schema; don't accept 5-slide output |
| CEO returns 7 slides but slide 6 has 2 bullets | pipeline's pre-validation should catch this | re-render with explicit `≥4 limitations` instruction |
| Accuracy Reviewer says "missing page citation" | CEO didn't include page numbers | reject → CEO revises → re-render |
| Alignment Reviewer says "title overflows" | text too long for 60-char target | reject → CEO shortens title → re-render |
| Brand Reviewer says "off-palette pixel" | image model added a non-brand color | reject → re-render with stricter palette constraint in prompt |
| All 3 reviewers PASS on text, FAIL on image | CEO wrote good spec but image model mis-rendered | kill at 2nd attempt — image-model data fidelity is bounded, don't loop |
| Venice API 402 | per-key DIEM cap | pause pipeline, ask user to top up, do not burn image-model budget |
| 191 blocked Paperclip issues from a previous day | paperclip auto-continuation race | cancel in batches of 10 via PATCH status="cancelled" before next run |

## Output directory layout

```
<output>/carousels/<slug>/
├── spec.json              # the 7-slide spec the CEO wrote
├── spec.md                # markdown companion with citations
├── slides/
│   ├── slide_1.png        # 864×1152 (3:4 portrait)
│   ├── slide_2.png
│   ├── ...
│   └── slide_7.png
├── reviews/
│   ├── accuracy.json      # pass 1 verdict
│   ├── brand_text.json    # pass 1 verdict
│   ├── accuracy_image.json # pass 2 verdict
│   ├── alignment.json     # pass 2 verdict
│   └── brand_image.json   # pass 2 verdict
├── carousel.pdf           # assembled PDF
├── carousel.zip           # PNGs + spec.json in a zip
├── summary.json           # final run summary
└── POSTMORTEM.md          # only written if pipeline killed
```

## When the pipeline is killed (postmortem)

A postmortem is written when:
- Text pass fails on both attempts (1 + 1 retry)
- Image pass fails on the only attempt (after 1 text attempt passed)

The postmortem should contain:
- Paper title + DOI
- Final verdicts from all reviewers
- The top 5 issues that blocked each pass
- The CEO's spec at the time of kill (so a future session can re-attempt)

Keep the postmortem ≤200 words. The goal is to capture *why it failed*,
not to retry. Future sessions can re-attempt from the spec.json if the
underlying issues are addressable.
