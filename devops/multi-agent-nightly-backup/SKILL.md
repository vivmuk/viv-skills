---
name: multi-agent-nightly-backup
description: Nightly backup orchestration for multi-agent workstations. Covers the shape of incrementally backing up multiple AI agents' state + portable artifacts to a cloud destination (OneDrive / iCloud / Dropbox / Google Drive) with a local mirror that auto-falls-back when the cloud is degraded. Triggers on "back up my agents", "mirror agent state", "AI agents backup", "nightly agent backup", "agent data portability", "agent mirror to OneDrive", "sync agent workspace", or "cross-machine agent migration".
version: 1.0.0
license: MIT
category: devops
metadata:
  hermes:
    triggers:
      - back up my agents
      - nightly ai agent backup
      - mirror agent state
      - cross-machine agent migration
      - sync agent workspace
    related:
      - hermes-agent
      - openclaw
      - self-hosted-agent-deployment
      - macos-computer-use
---

# Multi-Agent Nightly Backup (Incremental, Cloud + Local Mirror)

The class of work: on a single workstation, multiple AI agents run in
parallel (e.g., Hermes + OpenClaw, Claude Code + Codex + Gemini CLI).
You want a nightly cron that snapshots each agent's **state
files** (configs, auth, registries, sqlite) and **portable
artifacts** (generated text / images / markdown), into a destination
laid out by the agent that produced the data — so the result mirrors
the workstation's *actual agent names*, not a generic folder scheme.

The shape is repeatable: an `AGENT_MAPPING` constant names each agent
and its source files; a sidecar skip-detection scheme makes nightly
runs cheap; a probe-then-fallback layer keeps the cloud-write working
when the cloud's filesystem filter is degraded (OneDrive in particular
can hit `EDEADLK` after a long uptime). The class-level recipe (script
shape) is here; the install-time destinations, manifest schema, and
the specific Hermes-cron entrypoint are session-specific detail that
lives in `references/`.

## When this skill fits (and when it doesn't)

| Fits | Doesn't fit |
|---|---|
| Two or more AI agent workloads on one workstation (Hermes, OpenClaw, Paperclip, Codex, Claude Code, etc.) | A single agent on a single VM (use `self-hosted-agent-deployment` if it's already on cloud) |
| You want portable artifact portability (markdown, json, png, mp4) over to a cloud drive | You want application-level data (Postgres / Mongo / S3) — different shape |
| Recovery story is *file-level* (re-restore an agent's workspace, configs, conversations) | You want cross-region HA — adding vLLM, Postgres failover, etc. is overkill |
| 99% of nights the backup is "nothing changed", must run quickly | Real-time sync to every edit (use a sync client, not a cron) |

## The naming rule (and why it matters)

> **Always name destination folders after the agent that *produced*
> the data — never after a legacy schema or a *different* machine's
> agent names.**

User-confirmed 2026-07-03: when the destination convention arrived
(carried over from the user's *other* machine, where agents were
named Netrak/Katha/Dhristi), the first instinct was to map the local
agents *into* those folders. **That was wrong.** On a workstation
with two real agents (Agni/Paridhi or any other pair), the live
pipeline should write into folders named after the actual running
agents. Legacy shells stay on disk for cross-machine mirroring, but
the live backup pipeline ignores them.

This is a **first-class user-preference signal** — encode it in
`_lib.py::AGENT_MAPPING` so the next session doesn't relearn it.

## The shape (six layers)

1. **AGENT_MAPPING constant** (the heart). One Python dict per
   agent, each with three list keys: `sources_state` (config files
   → `Backups/`), `sources_outputs` (working artifacts → `Agent-Outputs/`),
   and a per-agent-thematic list (`sources_research`,
   `sources_projects`, etc., depending on the agent). Plus
   `exclude_globs` listing secret filenames (`.env`,
   `auth-profiles.json`, `*.key`, `.secret*`).
2. **Sidecar skip-detection**. Every copied file gets a sibling
   `*.sha256` sidecar containing `{size, mtime, sha256, src, copied_at}`.
   On the next run, fast-path: if `size + mtime` match the sidecar,
   skip. The sha256 is recorded for safety; reuse it only on
   `--verify` mode.
3. **Collision handling**. If two source files have the same
   basename from different parents, prefix the second copy with
   `_from_<parent_dir_name>__<basename>`. **Do NOT** silently
   overwrite — the disambiguation preserves provenance.
4. **Probe-then-fallback cloud root**. The script probes the
   primary destination by `mkdir + write_probe_file`; if the
   probe raises `OSError` (especially `Errno 11 EDEADLK` from
   OneDrive CloudStorage after long uptime), fall back to the
   local mirror at `~/output/<root>/`. The fallback is automatic
   and silent (logged once via stderr so cron-delivery has it).
5. **Three-script orchestration**:
   - `backup_agent_state.py` — config + sqlite + plugin manifests
   - `backup_agent_artifacts.py` — generated files matched against
     an explicit allowlist of extensions
   - `nightly_all_agents_backup.py` — wrapper with a global lock,
     two subprocess steps, and the prescribed summary block
6. **Hermes-side launcher**. Schedule ONE cron job running
   `~/.hermes/scripts/<basename>.py` with `no_agent: true`.
   The launcher resolves the canonical script (prefer primary,
   tolerate EDEADLK, fall back to local mirror) and forwards its
   output. **NEVER** pass an absolute script path to Hermes
   cron — the cron subsystem rejects it.

## Cloud-root probing (the OneDrive EDEADLK recipe)

The recurring failure mode on macOS:

- OneDrive has been up ~24h without a sync deferral.
- New `mkdir` or `write` ops on a sub-tree under the OneDrive root
  start returning `Errno 11 Resource deadlock avoided`.
- `os.listdir`/`ls -la` of the OneDrive root **hangs** on metadata
  fetch (cloud roundtrip) for 30+ seconds.
- Top-level writes (`/Users/<u>/OneDrive/<root>/<file>.md`) usually
  succeed.

Recovery: probe at every script entry; never trust a previous-run
"succeeded" status. The probe is cheap:

```python
def probe_writable(root: Path) -> tuple[bool, str]:
    try:
        root.mkdir(parents=True, exist_ok=True)
        probe = root / ".write_probe"
        probe.write_text("ok")
        probe.unlink()
        return True, "ok"
    except OSError as e:
        return False, f"errno={e.errno} {e.strerror}"
```

Wrap things that read paths from OneDrive in `try/except OSError`
so a stuck filter returns "primary unreachable" — never a hard
crash. Full detail in `references/onedrive-cloudstorage-deadlock.md`.

## Skip-detection correctness

A nightly backup of 200+ files completes in <1 second because most
of those files are unchanged. The fast-path is `size + mtime` from
the sidecar, which is correct when:

- The source file's mtime accurately reflects content change.
- The destination's mtime after `os.replace` is recorded in the
  sidecar (write sidecar **immediately after** the copy).
- Tools that "touch" files on read (rare) don't trigger spurious
  re-copies.

Tradeoff: sidecar trust on mtime means a source whose mtime ticks
but content is unchanged (the Curator daemon touches
`skills/.usage.json` periodically here) gets re-copied harmlessly.
**Skip full-content sha256 verification by default** — it turns a
quick run into a slow one. Keep it as an opt-out flag
(`--verify`) for paranoid weeks.

## Manifest schema (minimal but queryable)

```json
{
  "kind": "state" | "artifacts",
  "agent": "<human label>",
  "machine": "<uname -n>",
  "user": "$USER",
  "backup_root": "<resolved path>",
  "fell_back": false,
  "started_at": "<iso8601>",
  "completed_at": "<iso8601>",
  "duration_seconds": 0.41,
  "totals": {
    "files_copied": 86, "files_skipped": 0,
    "files_redacted": 10, "bytes_copied": 119866365,
    "errors": 0
  },
  "per_agent": {
    "Agni": {
      "state": { "totals": {...} },
      "outputs": { "totals": {...} },
      "research": { "totals": {...} }
    },
    "Paridhi": { ... }
  },
  "files": [...],
  "errors": [...]
}
```

Two manifest shapes co-exist: **state** has flat per-agent
(`per_agent[agent].totals`), **artifacts** has per-agent-per-kind
(`per_agent[agent][kind].totals`). The summary printer must
descend into both — a flatten-bug here masked copy counts for the
better part of an iteration during the original install.

## Run modes (always include all four)

| Mode | Flags | Behavior |
|---|---|---|
| `--dry-run` | yes | Counts only, no writes, no lock. Safe to run interactively any time. |
| Normal | none | Acquires lock, runs both stages, writes manifests, prints summary. |
| `--verbose` | yes | + per-file copy/skip lines |
| `--root PATH` | yes | Force a specific destination (for testing alternate mirrors) |

A first-run + second-run pair is the canonical verification recipe:

```bash
rm -rf <root>/Netrak <root>/Katha <root>/Dhristi <root>/Agni <root>/Paridhi     # fresh
python3 backup_agent_state.py    --root <root>     # wait for "copied=85"
python3 backup_agent_artifacts.py --root <root>    # wait for "copied=242"
python3 nightly_all_agents_backup.py --root <root> # total = 86 + 242 = 328
python3 nightly_all_agents_backup.py --root <root> # rerun: expect 0 / 328 skipped
```

If the second run shows `copied > 0`, investigate:

- Curator daemon / source mtime ticking (expected for `.usage.json`)
- A source under `node_modules` or `.git/` that escaped the
  exclude list

## Scheduling (Hermes cron recipe)

```bash
# Cron scripts MUST live in ~/.hermes/scripts/ and be referenced by
# filename. Pass an absolute path and the tool rejects with:
#   "Script path must be relative to ~/.hermes/scripts/"
#
# The launcher itself is ~30 lines; it probes PRIMARY → FALLBACK and
# invokes the canonical nightly_all_agents_backup.py with appropriate
# env (BACKUP_ROOT). The canonical script lives in PRIMARY scripts/
# tree; when primary is unreachable, fallback mirror wins.

hermes cron create 0 1 '* * *' \
  --name 'Nightly AI Agents backup' \
  --script nightly_ai_agents_backup.py \
  --no-agent \
  --deliver origin
```

`--no-agent` prevents an LLM token-burn just to print a summary.
`--deliver origin` posts to the user's current chat (Telegram in
this configuration).

## Output convention (Telegram-friendly)

When the script's stdout is what the user reads in chat, format it
like a runbook:

```
✅ Nightly AI Agents backup complete
Finished: 2026-07-03T06:47:10-04:00
Duration: 0.16s
Backup root: /Users/vivgatesai/output/AI Agents  fell_back=False
State: copied 0, size 120003346, errors 0
Artifacts: copied 0, skipped 242, size 86651041, errors 0
Agni:    copied 0, skipped 79,  size 91397702
Paridhi: copied 0, skipped 249, size 115256685
State manifest: <path>
Artifact manifest: <path>
```

Per-agent count is on its own line — easier to scan than a table
in 4-inch Telegram rendering.

## Security / policy gates (encode these into the script)

- [ ] Skip raw `.env`, `auth-profiles.json`, `auth.json` outright
- [ ] Redact `api_key/secret/password/token` field VALUES in
      YAML/JSON/.env (best-effort)
- [ ] Exclude `node_modules`, `.git`, `.venv`, `__pycache__`, `*.log`,
      `*.lock`-family
- [ ] **Never** delete destination files
- [ ] **Never** copy raw secrets — error-bias toward skipping
- [ ] Use `O_CREAT|O_EXCL` for lock files; auto-clear stale locks
      after `6h` (one stale-night tolerance)

## Pitfalls (cross-cutting)

1. **Mapping into legacy folder names because the user has a "looks
   similar" structure elsewhere.** — user told me off for this in
   session (Netrak/Katha/Dhristi vs. Agni/Paridhi). Default to
   naming destination folders after the *actual* agents on the
   workstation. Legacy shells can stay on disk for cross-machine
   mirroring.
2. **Trusting OneDrive after long uptime.** Probe on every run.
   Never hard-code "primary is reachable" from a previous successful
   run.
3. **Filenames with leading dots get skipped by `*` shell globs.**
   When migrating a backup tree, `mv src/* dst/` skips
   `.usage.json` and hidden directories. Either use `mv src/.[!.]*
   dst/` explicitly or use Python `shutil.move` recursion.
4. **Hermes cron scripts must have filename-only `script` arg.**
   Passing `/Users/<me>/.hermes/scripts/x.py` is rejected. The
   tool enforces the convention. Use the launcher pattern as the
   indirection layer.
5. **Hidden imports from helper modules.** `_lib.py` defines the
   constants and helpers; the working scripts do
   `sys.path.insert(0, HERE)` and `from _lib import …`. Adding the
   import mid-file is fine but skipping it via `py_compile` does
   not catch it — the missing import only fires at first runtime.
6. **`os.replace` updates mtime.** During redaction, a file's mtime
   changes even though content is structurally similar. Record
   sidecar's mtime from the **source** stat, not from the
   destination. (Default behavior; just don't accidentally read
   dst.mtime into the sidecar.)
7. **Sub-directory vs file basename collision.** Two `catalog.json`
   from different plugins (ollama plugin vs. venice plugin). The
   `_from_<parent>__<file>` prefix keeps both copies. **Never**
   overwrite silently.
8. **Profile-empty workstation.** `~/.hermes/profiles/<name>/` may
   not exist. Use `discover_state_files` which no-ops for missing
   sources rather than exploding on `rglob` of a non-existent
   directory.

## Files (this skill)

- `references/onedrive-cloudstorage-deadlock.md` — full EDEADLK
  diagnostic transcript + retry-after pattern + the recreation
  recipe used here
- `references/manifest-schema.md` — the JSON shape with worked
  example, including how state (flat) and artifacts (per-kind
  nested) co-exist
- `templates/agent_mapping_skeleton.py` — starter `AGENT_MAPPING`
  with all the constants commented out so a future installer
  fills them in
- `templates/nightly_wrapper.py` — minimalist
  `nightly_all_agents_backup.py` with the print-summary block (the
  shape, not the full implementation — pull that from
  `~/output/AI Agents/Shared/Scripts/` to copy verbatim)
- `scripts/probe_backup_root.py` — standalone probe script that
  can be cron'd on its own as a "is the cloud reachable today?"
  health check

## See also

- `hermes-agent` (PROTECTED) — `hermes cron create` CLI; `-p <profile>`
  for cross-profile data; the schedule-format grammar
- `openclaw` — for OpenClaw-specific config paths (`openclaw.json`,
  `agents/<name>/agent/auth-profiles.json`, `~/.openclaw/workspace`)
- `self-hosted-agent-deployment` — outbound direction (deploy agents
  to cloud); this skill is the inbound mirror of that one
- `macos-computer-use` — for OneDrive menubar interaction when the
  EDEADLK deadlock needs a manual app restart to clear
