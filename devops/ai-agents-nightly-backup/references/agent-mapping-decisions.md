# Agent-mapping decisions — the "which folder name" question

When multiple machines run AI agents and you want a shared "AI Agents/"
folder structure that mirrors across them, the question of **which
folder name corresponds to which agent** keeps coming up. This note
captures the decision matrix we hit on macOS and the pattern that
worked.

## Scenario (real, 2026-07-03)

User had:

- **Other machine** with agents named Netrak, Katha, Dhristi.
- **This machine** with two agents: Agni (Hermes) + Paridhi (OpenClaw).
- OneDrive with `AI Agents/{Netrak,Katha,Dhristi,Shared}/` already
  populated by the other machine.
- No matching folder for Agni or Paridhi.

## Wrong answer (initial pass)

We mapped Agni → Netrak + Katha (split because state vs artifacts) and
Paridhi → Dhristi. **This was wrong** because:

1. The other machine's Netrak may later write to `AI Agents/Netrak/`.
   If our local backups also write there, files collide. We have to
   manually avoid the collision, with no way to tell whose is whose.
2. Searching "where is my Paridhi transcript backup" leads to
   `AI Agents/Dhristi/` — confusing. The folder name is the PARENT
   machine's name, not THIS machine's.
3. Adding a new Hermes profile later fills `AI Agents/Katha/` with
   state that doesn't belong to either Netrak OR Katha on the other
   machine.

## Right answer (revised)

Create **parallel folder names matching the actually-running agents on
each machine**. Each machine writes to its own agent-named folders.
Cross-machine folder structure stays uniform (Backups/Agent-Outputs/
Research-or-Projects subdir), but folder names describe this machine.

For our scenario: create `AI Agents/{Agni,Paridhi}/` in addition to
the existing Netrak/Katha/Dhristi shells. Migrate any data already
written into Netrak/Katha/Dhristi to its rightful home (Agni or
Paridhi). Keep the Empty Netrak/Katha/Dhristi folders for
cross-machine mirror compatibility, but route live backups only to
Agni/Paridhi.

## Decision matrix

When user has Two+ machines writing to one shared cloud folder:

| Question | Answer |
|---|---|
| Should folder names match running-agent names? | **YES** on each machine. |
| Should you delete legacy folders? | **NO unless the user asks**. Empty shells are useful as cross-machine anchors. |
| What if the user wants ONE folder per agent across machines? | Each machine runs the SAME agent names. Use those. If they DIFFER, keep them separate. |
| How do I migrate data from wrong-name folders? | `mv` from old folder to new, but **watch out for shell `*` glob skipping dotfiles** — see `templates/` for a Python-based dotfile-aware migrator. |

## Edge case: dropping legacy folder names

If the user explicitly says "I want exactly these three folder
names, regardless of running agents", then map EVERY agent on
every machine into those three slots. This is harder to debug but
matches explicit user intent. Confirm before doing this.

## Edge case: zero prior structure

If the cloud folder is empty, just create the agent-named folders
matching the local running agents. No migration needed.

## Checklist before committing to a mapping

1. List the running agents on this machine. (`openclaw agents list`
   + `hermes profile list`.)
2. List the agents the OTHER machines run (ask, or read setup docs).
3. Decide: agent-keyed (preferred) or designated-slot (user
   preference).
4. Create the per-agent folders first, THEN move any pre-existing
   data into them.
5. Update the registry dict in `_lib.py::AGENT_MAPPING` to reflect
   the new mapping.
6. Re-run a dry-run; verify file counts match the migrated
   destinations, not the legacy ones.
