# Case Study: The "5 Limitations of the Study" Carousel (June 2026)

Empirical derivation of the Pre-Publish Editorial Checklist from a real
piece of work. Use this as a worked example when applying the skill.

## Background

The user asked for a "limitations" image to accompany a 5-slide carousel on
a Nature Medicine 2026 study that claimed "general AI beats specialized
clinical AI." The first draft of the limitations slide had **6 cards**,
including a "Hidden Conflict of Interest" card. The user pushed back: the
COI was speculative, not documented. They wanted the piece to be
"scientific and intellectually honest" and to capture the **true
limitations**.

## The original 6 cards vs the final 5 cards

| # | Original (rejected) | Final (shipped) |
|---|---|---|
| 1 | Hidden Conflict of Interest (speculative) | **No Clinical Outcomes Measured** (structural) |
| 2 | Contaminated Benchmarks (overstated) | Static Q&A Is Not a Clinical Decision (structural) |
| 3 | Style Is Not Substance (correct, kept) | HealthBench Weights Style Alongside Correctness (kept, renamed) |
| 4 | No Clinical Outcomes (kept) | No Baseline Comparison to Standard Care (added — Type 2 thinking revealed this was missing) |
| 5 | Static Q&A (kept) | Training-Data Contamination Is Unverified (added — defensible framing) |
| 6 | — | (removed) |

The final 5 cards were chosen by running the four checklist passes against
the original draft:

## How each checklist pass changed the draft

### Type 2 thinking

The original draft had "Contaminated Benchmarks" as a card. On Type 2 review,
this was too strong: not all benchmark items are contaminated, and
`gpt-image-2`'s reviewers had pushed back on this in earlier posts. Replaced
with "Training-Data Contamination Is Unverified" — the *risk* is real and
defensible; the *claim* of contamination is not.

Also: the original draft had nothing about the missing baseline comparison
(AI alone vs. clinician + UpToDate). This is arguably the most important
limitation and the one that maps to "what would a fair study look like."
Added as card 4.

### Accuracy

The "Hidden Conflict of Interest" card was based on a screenshot the user
shared that described authors asking for an API, being declined, and then
publishing the paper. The *timing* is a fact, the *motive* is speculation.
Per checklist pass #2 (no speculation about author motives), the card had
to go.

"Contaminated Benchmarks" was a similar problem — it asserts that
contamination happened, which can't be verified without the training-data
audit. Re-framed as "Unverified" rather than asserted as fact.

### Fair / balance

The original draft said nothing about the study's actual findings. A
defensible critique acknowledges the contribution first, then the gaps.
The final version's title and subtitle are more measured
("5 Limitations of the Study" / "What the Nature Medicine 2026 paper
missed") — they critique the work, not the people, and frame the limitations
as "what wasn't measured" rather than "what's wrong."

### Bias

The COI card was the obvious bias violation. "Hidden" is an editorial
verb that requires documentary evidence. Removing it made the rest of the
piece publishable. The user explicitly said: *"Don't include the conflict of
interest. Be as scientific and intellectually honest as possible based on
the study and true limitations."*

## What this case teaches

1. **The conflict-of-interest card is the canary.** When a draft includes
   speculative claims about author motives, removing them makes the rest of
   the analysis defensible. The piece wasn't fundamentally broken — it just
   had one card that didn't pass the accuracy check, and that card was
   poisoning the whole draft's credibility.

2. **Type 2 thinking surfaces the missing card.** The single best addition
   (baseline comparison) wasn't in the original draft at all. It emerged
   only when we asked "what would a peer reviewer say is missing?"

3. **Re-framing > removing.** "Contaminated" became "Contamination Is
   Unverified" — the same concern, but stated as a structural observation
   rather than a factual claim. This is a general pattern: when a claim is
   too strong, downgrade it to "the risk exists and we can't audit it"
   rather than dropping it.

4. **The carousel itself stays uncritical.** The 5-slide *companion*
   carousel was the original Nature Medicine writeup — *that* piece can
   present the study's findings as the user understands them. The
   limitations slide is the *separate* critical companion. The two serve
   different purposes and use different checklists.

## The final 5-card set (canonical)

These are the defensible limitations for any "general AI > specialist AI"
benchmark study. Reuse them when the same critique applies:

1. **No Clinical Outcomes Measured** — answer-matching ≠ patient benefit
2. **Static Q&A Is Not a Clinical Decision** — real bedside reasoning is
   multi-turn, time-pressured, with incomplete data
3. **HealthBench Weights Style Alongside Correctness** — the rubric
   conflates form with substance
4. **No Baseline Comparison to Standard Care** — the missing comparison is
   AI alone vs clinician + UpToDate
5. **Training-Data Contamination Is Unverified** — closed datasets make
   this hard to audit; the *risk* is real, the *claim* isn't

## How this connects to the other skills

- `content-marketing-pipeline` SKILL.md pitfall #12 documents the same
  structural-vs-motive distinction. That pitfall was written because of
  this case study.
- `content-marketing-pipeline` references `editorial-rigor` implicitly
  through the same pitfall. If a future session loads the marketing skill
  for a critique, it should also load this skill.
