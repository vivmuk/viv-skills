---
name: software-development-workflow
description: "Use when planning, spiking, debugging, implementing, testing, reviewing, or delegating software changes with disciplined verification."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [software-development, planning, debugging, tdd, code-review, subagents, verification]
    related_skills: [github-operations, ai-coding-agents]
---

# Software Development Workflow

## Overview

Use this umbrella for disciplined software work from idea to verified change. It consolidates planning, implementation-plan writing, throwaway spikes, systematic debugging, test-driven development, pre-commit review, and subagent-driven execution.

The class-level rule is simple: choose the right mode for the uncertainty, keep changes small and inspectable, and verify with real tool output before claiming success.

## Mode Selection

- **Plan mode**: user wants a plan, not execution. Inspect read-only context and write a concrete markdown plan under `.hermes/plans/`.
- **Implementation plan**: complex feature needs bite-sized tasks, paths, code sketches, tests, risks, and handoff-quality detail.
- **Spike**: feasibility is uncertain and the experiment is disposable. Build only enough to validate the question, then throw it away.
- **Systematic debugging**: something is failing. Reproduce and find root cause before fixing.
- **TDD**: behavior change or bug fix needs tests. Watch the test fail, then pass, then refactor.
- **Pre-commit review**: changes are ready to ship. Scan security, lint/tests, diff hygiene, and preferably fresh-context review.
- **Subagent-driven development**: a plan has independent tasks and benefits from fresh workers plus two-stage review.
- **Simplify/recent-change cleanup**: the user explicitly asks to simplify, clean up, or review recent changes. Use `references/simplify-code/legacy-skill.md` for the three-parallel-reviewer pattern (reuse, quality, efficiency), risk-tiered findings, scoped application, and verification.
- **Dogfood / exploratory QA**: a web app or feature needs evidence-backed bug discovery, severity triage, repro steps, screenshots/logs, and a concise report. Use `references/dogfood/legacy-skill.md` and its report template.

## Planning and Plan Files

When the user asks for a plan only, do not implement. Do not mutate project files except the plan document. Save under `.hermes/plans/` with goal, context, approach, task list, likely files, tests, risks, and open questions.

A good implementation plan assumes the implementer has little context. Include exact paths, concrete code or pseudo-code where helpful, dependency notes, validation commands, and bite-sized tasks. If someone must guess, the plan is incomplete.

## Spikes

Use spikes for "is this possible?", "compare A vs B", "quick prototype", or unknown technical feasibility. Do not spike when documentation/code inspection can answer the question or when the work is already production-bound.

Spike workflow:

1. Decompose the uncertainty into one or more experiments.
2. Research just enough to avoid wasting time.
3. Build in scratch space or an isolated branch.
4. Observe real output.
5. Return a verdict: VALIDATED, PARTIAL, or INVALIDATED, with surprises and a recommendation for the real build.

## Systematic Debugging

Iron law: no fixes without root cause investigation first.

Four phases:

1. **Root cause investigation**: read errors, reproduce consistently, inspect recent changes, trace data flow, gather evidence.
2. **Pattern analysis**: compare with working paths and similar code.
3. **Fix design**: choose the smallest change that addresses root cause, not just symptoms.
4. **Verification**: run the failing case, targeted tests, and regression checks.

If the first fix fails, return to evidence gathering; do not stack guesses.

## Test-Driven Development

Use RED-GREEN-REFACTOR for behavior changes whenever practical.

```text
RED: write the failing test and run it; confirm it fails for the expected reason.
GREEN: implement the smallest code to pass; run the specific test.
REFACTOR: clean up without changing behavior; rerun targeted and broader tests.
```

If you did not watch the test fail, you do not know whether it tests the right behavior.

## Pre-Commit Review

Before commit/push/ship after non-trivial edits:

1. Inspect `git status` and `git diff`.
2. Scan for secrets, shell injection, unsafe eval/deserialization, SQL string formatting, debug logs, and merge markers.
3. Run relevant tests/lint/build.
4. Self-review for scope creep, generated files, and backward compatibility.
5. Use an independent reviewer/subagent for substantial changes when available.
6. Fix findings and rerun verification.

Skip only for clearly documentation-only or when the user explicitly says to skip verification.

## Subagent-Driven Development

Use when a plan has independent tasks and quality gates matter. The owning Hermes session remains responsible.

Per-task workflow:

1. Read the plan and create a todo list.
2. Delegate one bounded task with relevant files, constraints, and verification commands.
3. Review the subagent's output against the spec.
4. Run quality/security verification.
5. Accept, revise, or redo before moving to the next task.
6. Run final full verification and summarize changed files/results.

Subagents cannot ask the user; pass all required context up front. Their summaries are self-reports until verified.

## Common Pitfalls

1. Planning mode accidentally mutates the repo.
2. Plans are too coarse; each task should be independently executable.
3. Spikes leak into production code without review.
4. Debugging starts with plausible fixes instead of reproduction.
5. TDD skips the RED step.
6. Review is performed only by the same context that wrote the code.
7. Subagent output is accepted without reading diffs or running tests.

## Dogfood / Exploratory QA

Use `references/dogfood/legacy-skill.md` when the work is web-app QA rather than code editing. Preserve its evidence standard: classify issues, capture repro steps and artifacts, avoid speculative bugs, and produce the report shape from `references/dogfood/templates/dogfood-report-template.md` when a written report is requested.

## Verification Checklist

- [ ] Correct workflow mode chosen for the user's request.
- [ ] Mutability constraints respected (plan/spike/production).
- [ ] Root cause or acceptance criteria identified before code changes.
- [ ] Tests or other verification run with real output.
- [ ] Diff reviewed for scope, security, and quality.
- [ ] Final response reports exact verification and blockers.
