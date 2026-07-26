# Origin Notes — Provenance & Re-Sync Strategy

`viv-design` packages three high-craft upstream sources into one unified frontend doctrine.

## Sources

| Source | Repo | Version / Date | Contribution |
|---|---|---|---|
| Emil Kowalski | `github.com/emilkowalski/skills` | current main (animations.dev era) | Animation decision framework, before/after review format, brutal review standards & standards table, animation vocabulary glossary, ease curves, ten non-negotiable animation standards |
| pbakaus | `github.com/pbakaus/impeccable` | v3.9.1 | Brand vs product register split, scene-sentence register pick, anti-AI-slop bans (shared + codex-specific), command taxonomy (craft / shape / audit / polish / critique / animate / typeset / layout / colorize / clarify / bolder / quieter / distill / harden / onboard / adapt / optimize / extract / document / init), live browser iteration scaffold, fonts reflex-reject list, premium-consumer palette rotation, two-stage category-reflex check |
| Leonxlnx (`design-taste-frontend`) | `github.com/Leonxlnx/taste-skill` | v2 (current main) | Brief inference ("design read"), three dials (VARIANCE / MOTION_INTENSITY / VISUAL_DENSITY) with inference tables, brief→design-system map (official packages), production-test LLM tells (informally maintained list), hero discipline rules, layout-family vocabulary, em-dash ban, poly-rule pre-flight matrix |

## What was unified vs preserved

Unified (consolidated into single source of truth):
- Animation standards (emil) → `references/animation-rules.md`
- Font / color / motion / layout bans from impeccable → split into `references/brand-register.md` and `references/product-register.md` for register-aware lookup
- Anti-slop checks from impeccable + production-test LLM tells from Leonxlnx → `references/anti-slop-checks.md`
- Design-system install map from Leonxlnx → `references/design-systems-map.md`

Preserved verbatim (overlapping but author-tested):
- The before/after table review format (emil) — SKILL.md
- The ten non-negotiable animation standards (emil) — SKILL.md
- The animation vocabulary glossary (emil) — `references/animation-vocabulary.md`
- The em-dash ban (Leonxlnx) — SKILL.md anti-slop
- The cream-monoculture guard (impeccable) — SKILL.md color

Adjudicated conflicts:
- Conflict: pbakaus allows single-family pages; Leonxlnx discourages serif as default; emil wants brand-distinctive. **Resolution:** brand = distinctive procedure applies; product = one well-tuned sans is fine; serif-by-reflex banned.
- Conflict: pbakaus pre-flight covers brand slop tests at first+second order; Leonxlnx preflight is 80+ boxes. **Resolution:** SKILL.md preflight merges both; mechanical boxes from Leonxlnx, the two reflex-checks from pbakaus.
- Conflict: pbakaus's commands (craft/shape/audit/polish/...) and Leonxlnx's hierarchy (animate / animate-as-enhance in product) overlap heavily. **Resolution:** SKILL.md uses pbakaus's 22-command taxonomy (most-cited, most-tested).

## Re-sync strategy

When any of the three upstream sources lands a meaningful change:

1. Pull the source: `cd ~/tmp/design-skills-research/<source> && git pull`
2. Re-read what's changed. Compare against the corresponding section in this skill.
3. Update the SKILL.md or relevant `references/*.md` file via `patch` (small change) or `write_file` (full rewrite).
4. If a ·new· runbook was added (e.g. pbakaus adds a 23rd command), add it to SKILL.md's command table.
5. If a font or palette was added to a reflex-reject list, update `references/anti-slop-checks.md` or the corresponding register file.
6. Commit/save with a dated changelog entry: "resync from <source> on YYYY-MM-DD".

### Cosmetic-only updates

If an upstream source ships wording or doc polish but no new rule, skip the resync. The doctrine, not the prose, is the source of truth.

### Conflicting updates

If two sources disagree after a resync:
- Pick the **more recent** of the two.
- Note the conflict at the top of the relevant section.
- Apply user judgment if the conflict affects shipping output (e.g. Leonxlnx softens the em-dash ban → keep it hard; pbakaus reorders command priorities → merge in the most useful layering).

## Licensing & attribution

- Each upstream source brings its own license; **viv-design does not republish their LICENSE files** but respects attribution in this document. Review each repo's LICENSE before redistributing viv-design.
- viv-design itself is MIT-licensed. Re-distribute freely with attribution.

## What this skill is NOT

`viv-design` is not:

- A replacement for the upstream `impeccable` CLI / browser-extension detector. Those tooling primitives live upstream and have their own version cadence.
- A domain skill (e.g. brand for an auth-tool, brand for a DTC restaurant). It is register-aware and presets a few common cases in `references/design-systems-map.md`, but a deep brand redesign for a specific company is still the user's brief to brief out.
- A front-end framework skill (no specific React/Vue/Svelte/Next.js recipe). It is framework-agnostic — the same doctrine applies.
