# Runbook output style — the format the user prefers for procedural asks

Confirmed 2026-06-27, reinforced 2026-07-03. When the user asks for a procedure, system to set up, install routine, or "how do I do X", use the runbook format. Prose walkthroughs are wrong format — even when exhaustive, they make the operator hunt for the actual command to copy.

The format:

1. **Lead with a Markdown task-list** (`- [ ]` items at status=cancelled/completed where appropriate).
2. **Exact shell commands per step**, not paraphrases. The user is operator-running these.
3. **Per-phase time estimates** ("≈ 5 min", "instant", "<1 min") so the user knows when to expect a wait.
4. **Daily-driver cheat-sheet** at the end (`## Daily driver`) with the 5-7 most common commands the user will actually re-run.

## Anti-pattern (do NOT do this)

> Here's a paragraph explaining how I set things up. The first thing I did was run the probe. Then I created the directory structure. After that I wrote three scripts. The scripts handle state backup and artifact copying. The state backup is the simpler one and is responsible…

The user has to scanline-search for the actual clipboards-and-paste commands. This wastes minutes every time it happens.

## Right pattern

```markdown
## Runbook

| # | Step | Status |
|---|---|---|
| 1 | Install deps | ☐ |
| 2 | Create directory skeleton | ☐ |
| 3 | Author scripts | ☐ |

## Daily driver

\`\`\`bash
python3 ~/output/AI\ Agents/Shared/Scripts/backup_agent_state.py --root ~/output/AI\ Agents --dry-run
\`\`\`
```

## Rationale

The user runs many of these procedures repeatedly. The format rewards re-use: each step is shorter to verify, the user can `tick off` items in their mental model, and the daily driver is the only section they re-visit.

If the user wants prose depth (e.g. a blog writeup), they will say "explain", "describe", or "walk me through". When they say "set up", "install", "configure", "build", or just describe a task, default to runbook.

## Use this skill's deliverables list specifically

The cross-agent backup installer produces a numbered list of "deliverables". Use the runbook table format for it:

```markdown
| # | Item | Path |
|---|---|---|
| 1 | OneDrive root | `/Users/<u>/OneDrive/AI Agents/` |
| 2 | Local mirror | `/Users/<u>/output/AI Agents/` |
| 3 | Backup scripts | `~/output/AI Agents/Shared/Scripts/{...}.py` |
| 4 | Hermes launcher | `~/.hermes/scripts/nightly_ai_agents_backup.py` |
| 5 | Cron job | `hermes cron list` shows `Nightly AI Agents backup` |
| 6 | First launch | I ran it manually tonight. Next auto-run: 2026-07-04T01:00 EDT |
```

Plus a "skipped folders / issues" section enumerating anything that didn't go exactly to plan. Be honest about blockers — do NOT hide issues invent plausible "it worked" sounding output if it didn't actually run.

## Pair this with the existing memory entry

The memory already encodes this preference. The skill embeds it so future sessions start new and *already know* the format, no memory-fetch needed.
