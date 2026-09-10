---
name: book-writing-mastery
description: Use when writing, editing, or reviewing book chapters for Vivek's Medical Affairs Singularity — multi-judge quality system (coherence, continuity, quality, accuracy, voice) plus chapter workflow.
version: 1.0.0
author: Hermes Agent (Pani)
license: MIT
metadata:
  hermes:
    tags: [book, writing, editing, judging, medical-affairs]
    related_skills: [sciwrite, clarity, writing-style-skill, paper-writing-skill]
---

# Book Writing Mastery — Medical Affairs Singularity

## Book state (always check first)
- Corpus: `~/book-medical-affairs-singularity/` (sources/, chapter-guide/, drafts/)
- Thesis: Medical Affairs Singularity — everything that CAN be done is now POSSIBLE; the constraint moved to adoption, trust, and role evolution. 23-month lens; challenge abstraction; ExO framework; agents as core customers; trust as throne.

## The Five Judges (run on every drafted chapter)

Invoke each judge as a separate internal pass with its own rubric. Score 1-10 with specific, line-referenced evidence. Never aggregate into one fuzzy score.

### Judge 1 — Coherence
- Does the chapter's argument hold together start to finish?
- Does each section logically require the next?
- Rubric: every paragraph must advance the chapter's single claim. Flag any paragraph that could be deleted without loss.
- Check: does the chapter answer the question the chapter title asks?

### Judge 2 — Continuity
- Cross-chapter consistency: terminology (singularity, abstraction, trust layer, context kings, agents-as-customer), claims, timeline (23 months), and numbers must not contradict other chapters.
- Method: before editing chapter N, re-read the endings of chapters N-1 and N+1 and the master outline.
- Flag: any term used with two meanings; any claim in ch5 that ch9 refutes.

### Judge 3 — Quality (prose craft)
- Sentence variety; no paragraph longer than 7 sentences; strong verbs; concrete over abstract.
- Ban list: "delve", "landscape", "tapestry", "in today's world", "it is important to note", "revolutionize" (unless quoted), "game-changer", em-dash chains (max 1/paragraph), rule-of-three padding.
- Every chapter must open with a concrete scene, story, or statistic — never a definition.
- Read aloud test: if a sentence cannot be spoken in one breath, split it.

### Judge 4 — Accuracy
- Every factual claim sourced from the corpus (`sources/linkedin/`, `sources/research/`) or a verifiable external source.
- No invented statistics. If a number appears, it must exist in a source file or cited public source.
- Medical/pharma claims: label level of evidence. Never overstate regulatory facts.
- Method: extract all claims > list them > verify each against corpus. Unverifiable claims get flagged [NEEDS SOURCE].

### Judge 5 — Voice (Vivek)
- First person, practitioner authority, direct. Short declarative sentences mixed with longer builds.
- Patterns from his actual writing: "Let me make this concrete...", "The difference is stark...", numbered takeaways, bold key phrases, honest disclosures ("I have spent 12 years in Medical Affairs...").
- Never: corporate hedging, consultant-speak, passive constructions hiding agency.
- Method: compare draft against `sources/linkedin/article-*.md` voice samples. Score similarity of rhythm and stance.

## Workflow per chapter
1. Read chapter-guide entry + all source files tagged for that chapter
2. Draft
3. Run all five judges; collect findings with line refs
4. Revise; re-run judges 1-3 (fast pass)
5. Save to `~/book-medical-affairs-singularity/chapters/NN-slug.md` with judge report frontmatter
6. Human review: email vivek with the draft + specific questions (see ghostwriter-interview skill)

## Rules
- Never invent statistics, quotes, or anecdotes
- Vivek's stories/positions come from the corpus — if the corpus doesn't support a claim, ask him
- One chapter = one argument. If two arguments, split the chapter.
- Target: 2,500-4,000 words per chapter, 4/10 density (delete before you add)
