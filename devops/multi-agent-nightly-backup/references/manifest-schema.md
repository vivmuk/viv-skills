# Manifest JSON schema — both shapes co-exist

The nightly backup emits two distinct manifests per run:

- `state-YYYY-MM-DD-HHMMSS.json`
- `artifacts-YYYY-MM-DD-HHMMSS.json`

Both write to `<BACKUP>/Shared/Backups/Manifests/`. A `latest`
symlink points at the most recent file of each kind.

## Common envelope (both manifests)

```json
{
  "kind": "state" | "artifacts",
  "agent": "<human-readable label, e.g. 'Agni (Hermes) + Paridhi (OpenClaw)'>",
  "machine": "<uname -n>",
  "user": "<$USER>",
  "backup_root": "<resolved path>",
  "fell_back": false,
  "started_at": "<iso8601 with offset>",
  "completed_at": "<iso8601 with offset>",
  "duration_seconds": 0.41,
  "totals": {
    "files_copied": 86,
    "files_skipped": 0,
    "files_redacted": 10,
    "bytes_copied": 119866365,
    "errors": 0
  },
  "per_agent": { ... },   // shape varies by kind — see below
  "files": [
    {
      "src": "/Users/<u>/.hermes/config.yaml",
      "dst": "/Users/<u>/output/AI Agents/Agni/Backups/config.yaml",
      "size": 16510,
      "action": "copied" | "copied_redacted" | "skipped" | "skipped-secret-name" | "error"
    }
  ],
  "errors": [
    { "src": "...", "dst": "...", "error": "<message>" }
  ]
}
```

## State manifest — flat `per_agent[agent]`

```json
"per_agent": {
  "Agni": {
    "label": "Agni (Hermes) — state + artifacts + research",
    "kind": "state",
    "totals": {
      "copied": 7, "skipped": 0,
      "size": 88990406, "errors": 0,
      "files": [...]
    }
  },
  "Paridhi": {
    "label": "Paridhi (OpenClaw) — full backup",
    "kind": "state",
    "totals": { "copied": 82, "skipped": 0, "size": 30950890, "errors": 0 }
  }
}
```

`per_agent[agent].totals.copied` is the right key for both reads
and writes here.

## Artifacts manifest — nested per-kind

```json
"per_agent": {
  "Agni": {
    "label": "Agni (Hermes) — state + artifacts + research",
    "outputs": {
      "target": "Agni/Agent-Outputs",
      "totals": { "copied": 75, "skipped": 0, "size": 2345240, "errors": 0 }
    },
    "research": {
      "target": "Agni/Research",
      "totals": { "copied": 0, "skipped": 0, "size": 0, "errors": 0 }
    }
  },
  "Paridhi": {
    "label": "Paridhi (OpenClaw) — full backup",
    "outputs":  { "target": "Paridhi/Agent-Outputs", "totals": {...} },
    "projects": { "target": "Paridhi/Projects",       "totals": {...} }
  }
}
```

Two key shapes — *not* flat.

## The flatten bug (lesson learned)

A naïve summary-printer iterated `per_agent[agent].totals.copied`
but the artifacts manifest doesn't have a `.totals` at that level
(for nested kinds). Got 22 reported when the real number was 242.
The fix: descend into `per_agent[agent][kind].totals.copied` when
the artifacts manifest is detected.

Canonical summary code:

```python
def per_agent_totals(per_agent: dict) -> dict:
    """Sums across nested per-kind entries regardless of manifest kind."""
    out = {}
    for agent, sub in per_agent.items():
        agg = {"copied": 0, "skipped": 0, "size": 0, "errors": 0}
        if isinstance(sub, dict):
            for k, v in sub.items():
                if isinstance(v, dict) and isinstance(v.get("totals"), dict):
                    t = v["totals"]
                    for key in agg: agg[key] += t.get(key, 0)
                elif k == "totals" and isinstance(v, dict):
                    for key in agg: agg[key] += v.get(key, 0)
        out[agent] = agg
    return out
```

Apply this on BOTH manifests before joining summaries — that way
the same code path produces consistent numbers regardless of which
manifest kind it is summing.

## Querying the latest run (jq one-liners)

```bash
# How big was the last state backup?
jq '.totals' <root>/Shared/Backups/Manifests/state-latest.json

# Per-agent breakdown, state manifest
jq '.per_agent' <root>/Shared/Backups/Manifests/state-latest.json

# Per-agent breakdown, artifacts manifest, summing nested kinds
jq '.per_agent | with_entries(.value |= (.outputs.totals // {}) + (.research.totals // {}) + (.projects.totals // {}))' \
   <root>/Shared/Backups/Manifests/artifacts-latest.json

# Did anyone skip because of a secret?
jq '.files[] | select(.action == "skipped-secret-name")' \
   <root>/Shared/Backups/Manifests/state-latest.json
```

## What's stable / what's session-specific

Stable: envelope keys (`kind`, `agent`, `machine`, `user`,
`backup_root`, `fell_back`, `started_at`, `completed_at`,
`duration_seconds`); totals keys; files[] schema.

Session-specific: which agents exist (`Agni`, `Paridhi`, ...); the
per-kind subkeys under `per_agent` (`outputs`, `research`,
`projects`, ...); the `target` strings inside each kind block.
