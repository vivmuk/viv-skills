# Sources

This bundle packages four high-craft upstream sources into a unified frontend-craft + interview-driven build workflow.

## Frontend-craft triumvirate (everyone feeds `viv-design/`)

| Source | Repo | Contribution |
|---|---|---|
| Emil Kowalski | `github.com/emilkowalski/skills` | Animation decision framework, before/after review format, brutal review standards & standards table, animation vocabulary glossary, ease curves, ten non-negotiable animation standards |
| pbakaus | `github.com/pbakaus/impeccable` | Brand vs product register split, scene-sentence register pick, anti-AI-slop bans, command taxonomy (22 commands), live browser iteration scaffold, fonts reflex-reject list, premium-consumer palette rotation, two-stage category-reflex check |
| Leonxlnx | `github.com/Leonxlnx/taste-skill` (skill name: `design-taste-frontend`) | Brief inference ("design read"), three dials (VARIANCE / MOTION / DENSITY), brief-to-design-system map, production-test LLM tells, hero discipline, layout-family vocabulary, em-dash ban, poly-rule preflight matrix |

## Interview primitive (feeds the grilling step)

| Source | Repo | Contribution |
|---|---|---|
| Matt Pocock | `github.com/mattpocock/skills` (skills: `grilling`, `grill-me`, `grill-with-docs`) | Relentless interview primitive — walks every branch of the decision tree, one question at a time with recommended answer, facts from codebase, decisions from user, no coding before sign-off |

## What was unified vs preserved

Unified (consolidated into single source of truth):
- Animation standards (Emil) → `viv-design/references/animation-rules.md`
- Font / color / motion / layout bans from pbakaus → split into `viv-design/references/brand-register.md` and `vival-design/references/product-register.md`
- Anti-slop checks from pbakaus + production-test LLM tells from Leonxlnx → `vival-design/references/anti-slop-checks.md`
- Design-system install map from Leonxlnx → `viv-design/references/design-systems-map.md`

Preserved verbatim:
- The before/after table review format (Emil) — `viv-design/SKILL.md`
- The ten non-negotiable animation standards (Emil) — `viv-design/SKILL.md`
- The animation vocabulary glossary (Emil) — `viv-design/references/animation-vocabulary.md`
- The em-dash ban (Leonxlnx) — `viv-design/SKILL.md` anti-slop
- The cream-monoculture guard (pbakaus) — `viv-design/SKILL.md` color
- The grilling interview rules (Matt) — `mattpocock-grilling/SKILL.md` (verbatim from upstream)

Adjudicated conflicts:
- **Font choice as defaults:** pbakaus allows single-family pages; Leonxlnx discourages serif reflex; Emil wants brand-distinctive. Resolution: brand = distinctive procedure applies; product = one well-tuned sans is fine; serif-by-reflex banned.
- **Pre-flight structure:** pbakaus covers brand slop tests at first+second order; Leonxlnx preflight is 80+ boxes. Resolution: `viv-design/SKILL.md` preflight merges both; mechanical boxes from Leonxlnx + the two reflex-checks from pbakaus.
- **Command taxonomy:** pbakaus has 22 commands (craft/shape/audit/polish/...); Leonxlnx's hierarchy maps differently. Resolution: viv-design uses pbakaus's 22-command taxonomy (most-cited, most-tested).

## License

| Source | License | Notes |
|---|---|---|
| `emilkowalski/skills` | repo `LICENSE` file | Generally MIT-equivalent; check upstream |
| `pbakaus/impeccable` | repo `LICENSE` file | Check upstream |
| `Leonxlnx/taste-skill` | repo `LICENSE` file | Check upstream |
| `mattpocock/skills` | repo `LICENSE` file | MIT |
| `viv-design` (this bundle) | MIT | Packaged by Viv |
| `viv-app-build` (this bundle) | MIT | Packaged by Viv |

## Re-sync strategy

When any source lands a meaningful change:

1. `cd /tmp && rm -rf <repo-name>-skills && git clone --depth=1 https://github.com/<org>/<repo>.git <repo-name>-skills`
2. Re-read what's changed. Compare against the corresponding folder under this bundle.
3. Update via `patch` (small change) or `write_file` (full rewrite).
4. Re-zip and re-deliver.

### Cosmetic-only updates

If an upstream source ships wording or doc polish but no new rule, skip the resync. The doctrine, not the prose, is the source of truth.

### Conflicting updates

If two sources disagree after a resync:
- Pick the more recent of the two.
- Note the conflict at the top of the relevant section.
- Apply user judgment if the conflict affects shipping output.

## What this bundle is NOT

- A replacement for upstream CLI tools / browser-extension detectors (those live upstream and have their own version cadence).
- A domain skill (e.g. brand for an auth-tool). It is register-aware and presets a few common cases in `viv-design/references/design-systems-map.md`, but a deep brand redesign for a specific company is still the user's brief to brief out.
- A front-end framework skill (no specific React/Vue/Svelte/Next.js recipe). Framework-agnostic — the same doctrine applies.
- A replacement for the user's design judgement. It sharpens the defaults, not the answers.
