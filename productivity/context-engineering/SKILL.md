---
name: "context-engineering"
description: "Context engineering best practices for advanced AI models — trim overconstraining rules, use progressive disclosure, design tool interfaces over examples."
status: proposal
version: "v1"
date: "2026-07-28T20:33:40.274Z"
---

# Context Engineering for Advanced Models

> Source: Anthropic blog post "The new rules of context engineering for Claude 5 generation models" by Thariq Shihipar (Jul 24, 2026). Anthropic removed 80%+ of Claude Code's system prompt for Claude Opus 5 / Fable 5 with no measurable loss on coding evals.

## When to Apply

- Trimming or revising AGENTS.md, SOUL.md, CLAUDE.md, or any system/context files
- Designing new skills or tool descriptions
- Reviewing context files for bloat or conflicting instructions
- Building agent harnesses or multi-step workflows
- User asks to "simplify" or "clean up" context/prompt files

## The Six Shifts

### 1. Rules → Judgment
**Then:** Give Claude explicit rules to avoid worst-case scenarios (e.g., "never write comments," "never create planning docs").
**Now:** Let the model use judgment. Replace rigid rules with one-liners that trust the model's discretion.
- Example: Instead of "DO NOT add comments. Never write multi-paragraph docstrings. Don't create planning documents unless asked" → "Write code that reads like the surrounding code: match its comment density, naming, and idiom."
- **Keep hard safety rails** (e.g., "don't exfiltrate private data," "ask before external actions"). Cut behavioral rules that a capable model already handles.

### 2. Examples → Interface Design
**Then:** Give Claude examples of how to use tools.
**Now:** Design tool parameters to be self-explanatory. Good interface design teaches usage better than examples.
- Example: Instead of showing sample tool calls, use enum values like `pending | in_progress | completed` that hint at the intended workflow.
- Make tool parameters more expressive rather than adding usage examples to the system prompt.

### 3. Upfront → Progressive Disclosure
**Then:** Put all instructions in the system prompt because Claude might need them.
**Now:** Load context at the right time. Move detailed guidance into skills that load on demand.
- Use a tree of files that can be loaded when needed, not a single monolithic file.
- Deferred loading: tools that don't appear in context until searched for.
- For CLAUDE.md/AGENTS.md: reference skills for detailed workflows instead of inlining everything.

### 4. Repetition → Tool Descriptions
**Then:** Repeat instructions in both the system prompt AND tool descriptions.
**Now:** Put instructions in the tool description only. One source of truth.
- Older models needed repetition and paid more attention to end-of-context instructions. Newer models don't.

### 5. Manual Memory → Auto-Memory
**Then:** Users manually save memories to CLAUDE.md via hotkeys or explicit commands.
**Now:** Claude auto-saves relevant memories. Focus manual memory on curated long-term context, not transient notes.
- For OpenClaw: MEMORY.md should be curated wisdom, not a log. Daily files are raw notes. Auto-curate during heartbeats.

### 6. Simple Specs → Rich References
**Then:** Store plans and specs as simple markdown files.
**Now:** Use higher-fidelity references — HTML mockups, test suites, code from other repos, function signatures.
- Code references produce better results than prose descriptions.
- Rubrics can be used to spin up verifier agents that check taste/quality dynamically.
- @ mention files instead of describing them in prose.

## Context File Hierarchy

| Layer | Purpose | Token Budget |
|-------|---------|-------------|
| System prompt | Product context, identity, hard constraints | Spend the most time here |
| CLAUDE.md / AGENTS.md | What the repo is + gotchas | Keep lightweight. Spend tokens on gotchas, not on what's obvious from the filesystem |
| Skills | Load-on-demand guides for specific workflows | Lightweight, opinionated, progressively disclosed |
| References | Specs, mockups, test suites, code | @ mention files instead of describing them |

## Practical Audit Checklist

When reviewing context files, ask:

- [ ] **Is this a gotcha or a rule?** Gotchas = things you'd never know from looking at the filesystem. Rules = behavioral constraints. Keep gotchas, cut rules the model can figure out.
- [ ] **Is this duplicated?** If it's in both the system prompt and a tool description, keep it in the tool description only.
- [ ] **Is this situational?** If it only applies sometimes, move it to a skill that loads on demand.
- [ ] **Is this an example?** Consider whether the tool's interface design could teach the same thing without an example.
- [ ] **Is this obvious?** If a capable model would know this from context, don't say it.
- [ ] **Are there conflicting instructions?** Read the full context stack and check for contradictions between system prompt, AGENTS.md, skills, and tool descriptions.
- [ ] **Could this be a file reference instead?** If you're describing something that exists as code or a file, @ mention it instead.

## Anti-Patterns to Remove

- "Never do X" when X is sometimes correct — replace with judgment-based guidance
- Detailed behavioral taxonomies (when to react, when to stay silent) — trust the model
- Repeating tool usage instructions in the system prompt
- Inlining detailed workflow steps that only apply sometimes
- Describing files/code that could be @ mentioned instead
- Saving transient notes to long-term memory files
- Making CLAUDE.md a central repository for every known practice

## What to Keep

- Hard safety rails (don't exfiltrate, ask before external actions, trash > rm)
- Genuine gotchas specific to the codebase/setup
- Preferences the model would never infer (user's timezone, naming conventions, specific tool configs)
- Curated long-term memory (decisions, lessons learned, project context)
- Tool interface design (parameters, enums, descriptions)
