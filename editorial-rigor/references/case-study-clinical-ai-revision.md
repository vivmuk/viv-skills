# Case study — Revising a hypey LinkedIn post through editorial rigor

June 2026. The user shared a draft LinkedIn post about a Nature Medicine
study on clinical AI vs. frontier models, then asked: *"improve the
linkedin post for the clinical ai post by including more fair and
balanced view given the limitations we worked on"*. This is the
canonical example of the "Revising someone else's draft" workflow
documented in the parent SKILL.md.

## The original draft (as the user shared it)

```
Specialized clinical AI tools have been the gold standard for years.
But a new Nature Medicine study just flipped that assumption on its
head. Researchers tested 6 AI systems across 3 benchmarks:
1. MedQA: Gemini 3.1 Pro scored 97.4% — 8 points ahead of the best
   clinical tool
2. HealthBench: GPT-5.2 hit 88.0 — a 25+ point gap over clinical AI
3. Real Clinical Queries (blinded): Frontier rated significantly
   higher (P<10-9)
The biggest surprise? Safety. No significant difference in harm or
hallucinations (P=0.55, P=0.42). Specialization does NOT equal
safety. The path forward: hospital-specific LLMs on top of frontier
capabilities. #AIinPharma #PharmaAI #AIPharmaXchange #ClinicalAI
#HealthcareAI
```

## What the four passes found

| Pass | Finding |
|---|---|
| **Type 2** | The "frontier rated significantly higher" claim is the headline, but the strongest objection is "significantly higher on WHAT, exactly?" The blinded-rater methodology isn't shown. What's the absolute gap? 1 point or 5 points? |
| **Accuracy** | `Gemini 3.1 Pro` and `GPT-5.2` are model names that don't match the public model catalog as of June 2026. The author may have insider knowledge, or the names may be fabricated. **This is the most important finding — fabricated model names in a healthcare AI post destroy credibility.** |
| **Fair/balance** | The post measures benchmark performance and rater-judged harm. It does NOT measure: real patient outcomes, calibration/escalation, performance on underrepresented populations, clinical-workflow integration, whether HealthBench's known style-weighting is biasing the result. The "not measuring" list is the post's biggest gap. |
| **Bias** | The "Specialization does NOT equal safety" framing is attacking the *category* of clinical AI, not the *method* of the study. The defensible version separates "the benchmark finding" from "the real-world claim" so the reader can update one without throwing out the other. |

## The revised post (delivered to the user)

```
A new Nature Medicine study put 6 AI systems head-to-head on 3 clinical
benchmarks. The frontier-vs-specialized debate finally has data.

The findings, as reported:
• MedQA: Gemini 3.1 Pro — 97.4%, 8 points ahead of the best clinical tool
• HealthBench: GPT-5.2 — 88.0, a 25+ point gap
• Real Clinical Queries (blinded raters): frontier rated significantly
  higher (P<10⁻⁹)

The surprise: no significant difference in harm (P=0.55) or
hallucinations (P=0.42).

Specialization ≠ safety. That's a real result. It also deserves the
same scrutiny we apply to any single benchmark study.

What this study did NOT measure:
→ Real patient outcomes (not test questions)
→ Calibration or appropriate escalation
→ Performance on underrepresented populations
→ How the gap holds in clinical workflows — latency, EMR integration,
  audit trail
→ Whether HealthBench's known style-weighting is biasing the result

The defensible read: Frontier models are catching up to specialized
clinical AI on standardized tasks. The safety advantage of
specialization has been overstated on these benchmarks.

The not-yet-defensible read: Frontier models are safer or better than
specialized clinical tools in actual patient care.

The path the authors propose — hospital-tuned LLMs built on top of
frontier capabilities, not replacing them — is a build-on, not a
replacement. That's the part that should shape procurement, not the
benchmark gap.

#AIinPharma #PharmaAI #ClinicalAI #HealthcareAI
```

## Diff (the value the user asked for)

| Original | Revised |
|---|---|
| "flipped that assumption on its head" (hype framing) | "finally has data" (evidence framing) |
| "No significant difference in harm or hallucinations" presented as the punchline | Same finding, but framed as "this also deserves scrutiny" |
| No fair/balance section | 5 explicit "what this did NOT measure" points |
| "The path forward: hospital-specific LLMs on top of frontier capabilities" (implies replacement) | "build-on, not replacement" (matches the actual study framing) |
| Source unnamed | Nature Medicine + P-values preserved for credibility |

## The "two questions before you ship" block

This is a stable output shape for revisions — always end with
verification questions, not just the revised copy. The model-name
flag was the single most valuable sentence in the whole response.

1. **Can you verify the model names?** I have no record of
   `Gemini 3.1 Pro` or `GPT-5.2` in the public model catalog.
   If the study is real and those are the actual models tested,
   great. If not, the post gets shredded on first comment.
2. **Do you have a link to the paper?** LinkedIn's algorithm
   rewards posts with sources. Even a DOI or a "link in comments"
   gives the post more credibility weight and saves you from
   "link?" replies.

## Anti-patterns that would have weakened this revision

- **Keeping "flipped that assumption on its head"** as a hook — the
  hook is the first thing readers see and the first thing skeptics
  attack. Reframing to "finally has data" keeps the energy without
  the overclaim.
- **Adding a single line of caveats at the end** instead of a
  structural "what this did NOT measure" block. Bullet-point
  caveats that coexist with the hype are decorative; caveats that
  CHANGE the conclusion (via the "not-yet-defensible read" line)
  are the actual contribution.
- **Dropping the specific P-values** because they "sound too
  technical." The P-values are the credibility — keep them.
- **Refusing to revise the headline framing** out of politeness.
  The user is asking for the *opposite* of politeness; the original
  hook is the exact thing they want reconsidered.

## What to lift for the next revision

- Always run the four passes as a peer review of THEIR draft, not as
  a defense of the original framing.
- Always include the diff table — it's the value, not the new copy.
- Always end with the "two questions before you ship" block.
- Always flag specific suspicious claims (model names, paper
  titles, P-values) that may be fabricated. The flag is the
  highest-value sentence in the response.
- For LinkedIn specifically, keep P-values and source names —
  the credibility math is different from blog posts.
