---
name: editorial-rigor
version: 0.2.0
description: Pre-Publish Editorial Checklist for every critique, analytical post, or limitations write-up. Run all four passes (Type 2 thinking, accuracy, fair/balance, bias) before publishing. Also applies when the user hands you a draft and asks you to revise it through the same lens. Empirically derived from the AIPharmaXchange "5 Limitations of the Study" carousel work (June 2026) and the Nature Medicine clinical-AI post revision (June 2026).
tags: [editorial, content-quality, critique, intellectual-honesty, aipharma, paperclip, revision, draft-review]
triggers:
  - critique
  - limitations
  - analytical post
  - publish check
  - bias check
  - accuracy check
  - peer review
  - "is this defensible"
  - editorial review
  - "improve this post"
  - "make this fair and balanced"
  - "revise this draft"
  - "what's wrong with this"
  - "apply the limitations"
---

# Pre-Publish Editorial Checklist (AIPharmaXchange)

This checklist is mandatory for every critique, analytical post, or limitations
write-up. Run all four passes before publishing.

See `See Also` at the bottom for worked examples.

## 1. Type 2 thinking — what is NOT being said?

Ask: "If a thoughtful skeptic read this, what would they point out as missing?"

- What gap exists in the analysis that we're not addressing?
- What alternative interpretations did we skip?
- What would change our conclusion if true?
- What would a peer reviewer ask us to defend?

The goal: surface the strongest objection to our own claim, and either
address it or remove the claim.

## 2. Accuracy check — is every claim verifiable?

- Every factual claim cites a source (paper title, dataset name, public record)
- No speculation about author motives, private conversations, or intent
- Numerical claims have units and are checked against the source
- "Hidden", "covert", "secret" type language requires documentary evidence — otherwise drop
- If a claim cannot be verified, either find the evidence or remove the claim

## 3. Fair / balance check — both sides represented?

- The work we are critiquing is named, dated, and cited
- The original findings (the things we AGREE with) are stated clearly before the critique
- The strengths of the work being critiqued are acknowledged where they exist
- Where a limitation could be a feature, we say so
- The reader can form their own view, not just adopt ours

## 4. Bias check — method vs people

- We attack the method, the metric, the dataset, the design — not the authors
- No accusations about character, motive, or intent unless we have documentary evidence
- The tone is "here is what the study measured and what it didn't" — not "they did this on purpose"
- The reader can tell this was written by someone who read the work carefully, not by a partisan

## After the checklist

If any check fails, edit the draft before publishing. If the failure is
structural (e.g., the entire piece rests on speculation), the draft does
not go out — it goes back to research for one more pass.

The "AIPharmaXchange" brand is built on intellectual honesty. A snappy
take that isn't defensible is worth less than a measured one that is.

## How to apply this in a content pipeline

- **LinkedInStrategist, NewsletterEditor** (Paperclip) — Run all four passes
  before marking the issue done. If any fails, the issue goes back to
  `in_progress` with a comment listing what failed.
- **ContentDirector** (Paperclip) — PM review. Block any post where the
  checklist wasn't visibly run.
- **BrandGuardian** (Paperclip) — Final review. Catches drift even if
  upstream missed it.
- **MarketingDirector** (Paperclip) — Owns the standard. Can escalate or
  override per post.
- **Ad-hoc use** (any LLM session) — Run the four passes against the draft
  before sending. If a hallucination or speculation is found, the draft
  is rewritten, not just patched.

## When to NOT use this skill

- For pure marketing copy (product launches, value props, "buy now" CTAs).
  Use your normal brand-voice skill.
- For technical documentation or how-to content. Use technical-review
  skills instead.
- For creative writing or fiction.

The skill applies to content where the central question is "is this claim
defensible?" — critique, limitations, comparisons, and analytical
commentary. If the piece is not making any analytical claim, the checklist
is overkill.

## Revising someone else's draft through the same lens

When the user hands you a draft post (LinkedIn, Twitter thread, blog,
newsletter intro) and asks you to improve it, the workflow is the same
checklist applied *inward* — run the four passes against THEIR draft,
then produce a defensible revision. Empirically derived from the
2026-06-14 clinical-AI LinkedIn post revision (the user shared a
draft, asked for "more fair and balanced view given the limitations
we worked on").

**Workflow:**

1. **Read the draft fresh.** Don't anchor on its tone or framing.
2. **Run the four passes as a peer review of THEIR draft:**
   - Type 2: "What's the strongest objection to this post's claim?"
   - Accuracy: "Are model names, paper titles, P-values, dates
     actually real and current?" (flag suspicious specifics —
     e.g. model version numbers that don't match the public catalog)
   - Fair/balance: "What is this post NOT measuring that it implies
     it is?" (the clinical-AI revision: real patient outcomes,
     calibration, underrepresented populations, workflow integration)
   - Bias: "Is this attacking the method, or the people?"
3. **Rewrite in two layers:**
   - **Keep**: any genuine signal, any specific numbers that are real,
     any framing that survives the four passes
   - **Reframe**: hype phrasing ("flipped on its head", "the path
     forward") → evidence phrasing ("finally has data", "the
     proposed path")
   - **Add**: the "what this did NOT measure" block. This is the
     highest-value addition — it converts a one-sided take into a
     defensible one.
   - **Tighten**: split the "defensible read" vs "not-yet-defensible
     read" — naming both makes the post honest without being preachy.
4. **Show the diff.** Always include a table or list of what changed
   and why (Original → Revised column). The user wants to see
   *intent*, not just the new copy. The diff IS the value.
5. **Flag anything you couldn't verify.** Real-sounding model
   versions, paper titles, or P-values that may be fabricated.
   The clinical-AI revision flagged `Gemini 3.1 Pro` and `GPT-5.2`
   as not matching the public catalog — that flag was the most
   important thing in the whole response.
6. **Offer hooks and alt formats.** Two or three alternative opening
   lines, a 120-word punchy version for A/B testing. Don't over-deliver;
   one alt is enough unless asked.

**Anti-patterns to avoid:**

- Don't defend the original framing. The user is asking for the
  *opposite* — apply the rigor and produce a revision. If the draft
  is already good, say so and explain why, but don't be polite by
  leaving the worst sentences intact.
- Don't add bullet-point caveats that just decorate the hype. The
  caveats must CHANGE the conclusion, not coexist with it. The
  clinical-AI post's "not-yet-defensible read" line does the heavy
  lifting; a one-liner at the end would not.
- Don't replace the original's specific data with vague language.
  If "P<10⁻⁹" is in the source, keep it (with the source). The
  revision's job is to *contextualize*, not to soften.
- Don't apply this skill to drafts that are NOT making analytical
  claims. Marketing copy, listicles, and personal essays have
  different standards — defer to brand-voice or writing skills.

**Output shape that works for LinkedIn-style revisions:**

```markdown
## Revised [post type] (defensible version)

[revised post in full]

---

## What changed vs. your original

| Original | Revised |
|---|---|
| [original framing] | [reframed] |
| ... | ... |

## Editorial-rigor checklist on the revised post

| Check | Result |
|---|---|
| Type 2 (strongest objection) | [one line] |
| Accuracy (every claim verifiable) | [one line] |
| Fair / balance (both sides' data) | [one line] |
| Bias (method not people) | [one line] |

## Two questions before you ship

1. [verification question — usually a model name or paper title]
2. [delivery question — usually a source link or DOI]
```

**Worked example:** see `references/case-study-clinical-ai-revision.md` for the
June 2026 Nature Medicine clinical-AI post revision.

## See Also

- `references/case-study-limitations-slide.md` — Worked example from
  AIPharmaXchange's "5 Limitations of the Study" carousel (June 2026).
- `references/visual-critique-image-workflow.md` — Recipe for rendering
  a text-heavy critique slide with the image model (grok sota), not
  Pillow. Aspect ratio 3:4 portrait, brand palette, prompt
  construction, what fails, the Pillow fallback, the post-render
  review-send rule.
- `content-marketing-pipeline` SKILL.md — Includes the same
  structural-vs-motive principle in pitfall #12; both skills reference
  each other so a critique-driven carousel session will load both.
- **Image generation for critique slides (REVISED 2026-06-18):**
  The "Pillow overlays every text element" guidance below is
  **OUTDATED and superseded by `social-carousel-generation` for
  carousel work.** With V2 prompt fixes (inline real text strings,
  color names not hex codes, watercolor brand descriptor preserved,
  negative prompt for "gibberish letters, distorted glyphs"),
  `grok-imagine-image-quality` reliably renders critique / limitation
  card text — confirmed in the MIRA carousel V2 (5/7 slides at
  publishable quality) and a second full MIRA re-run on 2026-06-18
  (7/7 slides with all 5 limitations, both numbers 88.9% and
  78.1%, all 8 medical condition names spelled correctly).

  **The decision rule for visual artifacts with text:**
  - **Carousel / multi-slide infographic (per
    `social-carousel-generation`):** image model renders text in
    the prompt. NO Pillow overlay. This is the user's hard
    preference. They have rejected Pillow text overlay multiple
    times in a single session.
  - **One-off hero image, decorative background:** image model
    is fine; Pillow overlay not relevant.
  - **Data-heavy infographic with strict text accuracy AND fine
    typographic control:** Pillow overlay may still be the right
    call (see `branded-infographic` skill).

  The palette is teal #2BA39B, mint #8FD3B6, navy #1E3A5F,
  cream #F5F0E1. Aspect ratio: 1024×1024 (square) for
  `grok-imagine-image-quality`; switch to `flux-2-max` for
  4:5 portrait. Style is painterly watercolor, not flat UI. For
  data-heavy charts (e.g. a 88.9% vs 78.1% accuracy bar chart),
  the model CAN draw a usable bar chart with labels if the
  layout is spelled out in the prompt and the negative prompt
  forbids "decorative chart with no axes".

- **Source citation lives in the post copy, NOT the image
  footer** (user preference, 2026-06-18). For LinkedIn carousels,
  the image footer should be brand mark + swipe cue only. No
  "Williams et al. Nature Medicine 2026", no DOI. The citation
  belongs in the LinkedIn post text, where it can be linked and
  is readable. When iterating on a carousel, the user has
  explicitly asked to strip source citations from the footer.
- **When the deliverable is a visual artifact, the editorial
  check must include visual QA on the rendered PNG, not just a
  text-only review of the spec.** The 3 reviewers in a carousel
  pipeline must receive the rendered PNG bytes (base64 in prompt)
  and inspect: (1) is the title legible with no clipping, (2) do
  bullet text and illustration overlap, (3) is there hallucinated
  text inside the image, (4) is the visual supporting the
  message or merely decorative. Without image-aware review, all
  four failure modes ship silently. See
  `editorial-carousel-orchestration` skill, "Reviewer prompts
  must include image bytes" pitfall.
- **Email FROM for Paperclip work emails:** "AI CEO AIPharmaXchange
  <vivgatesai@gmail.com>" — see `paperclip-delivery-daemon` skill.
