# Agent folder naming conventions — ask before you map

When more than one AI agent runs on a machine, you have to decide how to organize their backups. There are at least three conventions in active use:

| Convention | Folder names | Example on user's `~/OneDrive/AI Agents/` |
|---|---|---|
| **Per-agent** | one folder per running agent | `Hermes/`, `OpenClaw/`, `Paperclip/` |
| **Sanskrit / Indic personas** | Sanskrit-named folders, often stable across machines | `Agni/`, `Paridhi/`, `Netrak/`, `Katha/`, `Dhristi/` |
| **Mirror-of-other-computer** | folder names from a different host, used to keep cross-machine navigation consistent | user might name folders here after agents that don't run locally |

The pitfall: a folder name on the backup destination does NOT necessarily match a running agent on the source machine. **Always confirm the mapping in plain language before writing files.**

## The conversation that taught this

User asked for nightly backups for "all of you" (referring to agents running on this computer). The user-supplied spec listed three folder names: `Netrak/`, `Katha/`, `Dhristi/`. The agent assumed those were running-agent names.

Three mid-turn messages were needed to clarify:

1. "those agents are from my other computer. I want to back up all of you onto there as well in a similar form"
2. "Agni is you (Hermes), you have Paridhi (openclaw)"
3. "that is a wonderful folder that I have created on the computer. Did you find it?"

Without those corrections, the first mapping would have been wrong. The cost: wasted installer code + a non-recoverable directory tree if files were already written.

## When to ask

Before writing any file under a per-agent folder name, ASK ONCE in plain language. Suggested phrasing:

> "On this machine I see two agents running: [A] and [B]. The folder layout you mentioned uses these names: [X], [Y], [Z]. Which agent maps to which folder? Some users use mirror-of-other-computer folder names — please confirm."

Three seconds of asking beats three messages of correction.

## When NOT to ask

If the user has clearly named the agent folder the same as a running agent *and* there's a 1:1 mapping (e.g. user says "RAG agent lives in `~/RAG/`"), don't ask. Just bind them.

If the user has left the destination empty and you have full ambiguity, ASK before scaffolding any directories.

## Recommended way to encode the mapping

Keep it in **one file** (a `_lib.py` constants block) with clear labels. Future sessions will read this same file first and not have to ask again. Example shape:

```python
AGENT_MAPPING = {
    "Netrak": {                         # ← the destination folder name
        "agent_label": "<running-agent-name> — <description>",
        "kind": "state",
        "dest_subdir": "Backups",
        "sources": [
            "~/.agent/config.yaml",
            "~/.agent/agents/<name>/plugins",
        ],
    },
    # …other destinations
}
```

This single block drives:
- Where state files go (`<BACKUP>/<Netrak>/<dest_subdir>`)
- Where artifacts go (mirrored under `<BACKUP>/<Netrak>/Agent-Outputs`, `Research`, `Projects`)
- Which paths get excluded (per-agent exclude_globs)
- How the summary print aggregates per-agent totals

## If the user uses mirror-of-other-computer naming

That's totally valid. The destination tree exists *for the user's navigation*, not to mirror the running agents topologically. As long as you encode the mapping inside `_lib.py::AGENT_MAPPING` clearly, future sessions will read it and not need to ask again.

Recommend at install-time: write a `setup-documentation.md` addendum with a single table:

```markdown
| Running agent (this machine)  | Destination folder |
|-------------------------------|--------------------|
| <name-1>                      | Netrak/            |
| <name-2>                      | Katha/             |
| <name-3>                      | Dhristi/           |
```

Future agents — human or AI — know instantly which is which without ambiguity.
