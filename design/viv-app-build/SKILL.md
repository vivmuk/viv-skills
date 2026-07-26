---
name: viv-app-build
description: Use when the user asks to build, develop, scaffold, design, prototype, implement, or ship an application — full-stack web app, mobile app, CLI app, dashboard, SaaS product, internal tool, MVP, side project. **Always starts with `grilling` interview (relentless questions, one at a time, with my recommended answer) until the user confirms shared understanding, then applies `viv-design` doctrine for the UI portion. Never begin coding before the interview sign-off.** Sub-commands chain the same 22 viv-design commands but with grilling as a hard precondition. Not for one-off bug fixes, copy edits, infra work, backend-only tasks, or pure marketing / landing / portfolio pages — those go straight to `viv-design`.
version: 1.0.0
author: Viv (Hermes Agent, packaged for Vivek M)
license: MIT
metadata:
  hermes:
    tags: [app-build, full-stack, mvp, grilling, interview, viv-design, frontend, scaffold, prototype]
    related_skills: [grilling, grill-me, grill-with-docs, viv-design, plan, writing-plans]
    category: creative
---

# Viv App Build — Application Development Workflow

## Overview

`viv-app-build` is the **first thing that loads when the user asks to build or develop an application**. It orchestrates two existing skills — neither is replaced:

1. **`grilling`** (peer skill — do not modify) — the relentless interview primitive. Walks every branch of the decision tree, asks ONE question at a time with the agent's recommended answer, waits for user feedback, never enacts the plan until the user confirms shared understanding.
2. **`viv-design`** (peer skill — this profile) — the unified frontend craft doctrine (brief inference → three dials → register pick → color/typography/layout/motion → anti-slop preflight).

The two compose in this order **without exception** for any application-build request.

## When to Use

**Load automatically:**
- User asks to **build / develop / scaffold / prototype / implement / ship / launch / make** an application.
- Common trigger phrases: "build me X," "develop X," "let's make X," "ship X," "I want to build X," "create an app for Y."
- Catches: full-stack web apps, mobile apps, dashboards, SaaS products, internal tools, MVPs, prototypes, side-project experiments, CLI tools with a UI surface, marketing sites that ship as a Next.js/Astro app (app surface, not pure brand surface).

**Don't load:**
- One-off bug fixes ("why is this button broken").
- Copy-only edits with no visual surface.
- Infra / DevOps / backend-only work.
- Pure marketing sites, landing pages, portfolios, brand sites, editorial — those are viv-design territory directly.
- Specific small UI component adjustments on existing apps ("make this button prettier", "audit this single page") — viv-design territory directly.

**When in doubt, load.** The grilling interview is short if the brief is clear.

## The App-Build Workflow (mandatory)

**Hard rule: never begin coding on an app-build request without grilling sign-off. Never. No exceptions.**

The workflow has two phases.

### Phase 1 — Grilling interview

a. Load `grilling` (it's already in the peer skill tree; `skill_view(name='grilling')` if you need to re-read).

b. Run the relentless interview, per the upstream rules:
- Walk every branch of the design tree.
- Resolve dependencies between decisions one-by-one (parent decisions before dependent children).
- For each question: state **the agent's recommended answer first**, then the question, then wait.
- **Ask ONE question at a time.** Multi-question dumps are bewildering.
- Where a **fact** can be answered from the codebase, explore rather than ask.
- Where a **decision** is needed, put it to the user and wait.

c. Continue until the user explicitly confirms shared understanding is reached. Do not end early on "ok let's start building" — that's a signal to keep grilling branches open.

d. Output a short **grilling recap** (3-5 bullets) capturing: scope, audience, primary surface, key constraints, chosen stack/architecture. This becomes the brief that Phase 2 builds from.

### Phase 2 — viv-design doctrine

Once grilling is signed off, transition to viv-design doctrine:

a. **State the design read** in one line ("Reading this as: …").
b. **Set the three dials** (VARIANCE / MOTION / DENSITY) from the inference table.
c. **Pick the register** (brand vs product) and load the matching reference: brand → `~/.hermes/skills/creative/viv-design/references/brand-register.md`; product → `~/.hermes/skills/creative/viv-design/references/product-register.md`.
d. **Apply viv-design doctrine in order**: color → typography → layout → motion → anti-slop.
e. **Run the preflight checklist** before delivering. Anything that fails gets fixed or flagged.
f. **Use the before/after review table** for any reviews or rewrites: `| Before | After | Why |` — never a "Before: … / After: …" list.

If the build crosses into multiple stacks (e.g. backend API + frontend SPA), apply viv-design to the UI portion only. For the non-UI portion, follow the requirements surfaced by grilling.

## Sub-Command Routing (composable with viv-design's 22 commands)

If the user invokes `viv-app-build <viv-design-command> [target]`, run grilling first, then the named viv-design sub-command.

| Command | Behavior |
|---|---|
| `craft [feature]` | Grilling on the feature → shape → build end-to-end with viv-design. |
| `shape [feature]` | Grilling on the feature → plan UX/UI before writing code. |
| `audit [target]` | Light grilling on audit scope → viv-design audit (a11y, perf, responsive). |
| `polish [target]` | Light grilling on what's being polished → viv-design polish. |
| `critique [target]` | Grilling on what's being critiqued → viv-design critique with heuristic scoring. |
| `animate`, `typeset`, `layout`, `colorize`, `clarify`, `bolder`, `quieter`, `distill`, `harden`, `onboard`, `adapt`, `optimize`, `extract`, `document`, `init` | Grilling on the focus → viv-design sub-command. |

For `viv-design` sub-commands not listed above (`delight`, `overdrive`, etc.), see `~/.hermes/skills/creative/viv-design/SKILL.md` and apply grilling as a precondition.

## Explicit Bypass

For very clear, well-specified feature work, the user can override grilling with the `no-grill` flag:

```
viv-app-build polish auth-modal no-grill
```

Use sparingly — only when the brief is unambiguous, the user knows exactly what they want, and the change scope is small. If the user later surfaces "I missed something," reminding the agent with "please grill me" re-engages the interview.

## Pitfalls

1. **Skipping grilling because the brief "looks clear."** Clear briefs still have hidden branches. Grilling is fast and unlocks better decisions.
2. **Running grilling but jumping to code before sign-off.** Don't. Wait for the explicit "shared understanding" confirmation per the grilling skill rules.
3. **Running grilling once and treating it as done.** Grilling is a tree, not a checklist. Branch down until leaves are hit or the user says stop.
4. **Treating grilling as a list dump.** Walk the tree. One node → one question → one answer → next node.
5. **Asking multiple questions at once.** "Asking multiple questions at once is bewildering." Per the upstream skill: ask one at a time, wait for feedback.
6. **Skipping the codebase exploration step.** If a fact can be answered from the codebase, look it up. Save the question for the decision.
7. **Treating the grilling recap as optional.** It is the brief for Phase 2. Without it, the viv-design phase operates on an unstated spec.
8. **Letting viv-design doctrine override the user's grilled decisions.** Grilling's output is the source of truth. viv-design is the craft-layer that applies on top.

## Verification Checklist

Before delivering any application build:

- [ ] Grilling interview completed and user confirmed shared understanding?
- [ ] Grilling recap (3-5 bullets) shipped in the conversation as the brief?
- [ ] viv-design front door executed: design read + dials + register pick?
- [ ] viv-design preflight checklist run (front-door + color + typography + layout + motion + anti-slop + imagery + production)?
- [ ] If UI surfaced, before/after review table used for any found issues?
- [ ] Reduction: skill-loaded contracts from grilling respected across the build?

## Cross-Skill Reference

| Skill | Path | Role |
|---|---|---|
| `grilling` | `~/.hermes/skills/creative/grilling/` (peer) | Interview primitive |
| `grill-me` | `~/.hermes/skills/creative/grill-me/` (peer) | User-invoked `/grill-me` shim |
| `viv-design` | `~/.hermes/skills/creative/viv-design/` (this profile) | Frontend craft doctrine |
| `viv-app-build` | `~/.hermes/skills/creative/viv-app-build/` (this profile) | This file — orchestrator |

## Re-sync from upstream

The grilling skill evolves upstream. Re-pull periodically:

```bash
cd /tmp && rm -rf mattpocock-skills
git clone --depth=1 https://github.com/mattpocock/skills.git mattpocock-skills
diff <(curl -sL https://raw.githubusercontent.com/mattpocock/skills/main/skills/productivity/grilling/SKILL.md) \
     ~/.hermes/skills/creative/grilling/SKILL.md
```

If the upstream `grilling` changes its rules (e.g. loops-count cap, decision tree guidance), update this orchestrator's reference accordingly.
