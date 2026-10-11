---
name: ai-agents-nightly-backup
description: "Build a nightly, file-locked, incremental Python backup pipeline for AI agent state + artifacts on macOS, with cloud-sync primary destination and an auto-fallback local mirror when the cloud filter blocks writes (OneDrive EDEADLK, Files-On-Demand lag, NFS hang, etc.). Schedules via Hermes cron under a Hermes-side launcher (filename only, no_agent:true) so no LLM tokens are burned on routine backups."
version: 1.0.0
triggers:
  - nightly agent backup
  - hermes state backup
  - openclaw state backup
  - onedrive agent backup
  - backup destination fallback
  - ai agents backup
  - agent outputs archive
platforms: [macos, linux]
metadata:
  hermes:
    tags: [backup, hermes, openclaw, cron, onedrive, ai-agents, snapshot]
---

# AI Agents Nightly Backup

Build a small Python backup pipeline that snapshots:

- **Agent STATE / CONFIG** (one folder per agent, under `Backups/`)
- **Agent ARTIFACTS** (incremental copies of generated files, under
  `Agent-Outputs/` plus a thematic subfolder like `Research/` or `Projects/`)

…into a destination that **defaults to a cloud-synced folder** (OneDrive,
iCloud Drive, Dropbox, NFS share) but **falls back to a local mirror** when
the destination can't accept writes (OneDrive's `EDEADLK`, cloud-pending
metadata, read-only filesystem, etc.). Schedule via Hermes cron with
`no_agent:true` so the cron path runs as a script invocation, not an
agent loop.

This is class-level: the design applies to ANY machine running one or more
local AI agents and wanting a cheap nightly portability snapshot.

## When to use

- You have Hermes (or any profile-based agent runtime) AND/OR OpenClaw (or
  any isolated-agents runtime) on a single machine and want a portable
  backup of state + artifacts.
- You have a OneDrive / iCloud / Dropbox-mounted folder you want as
  primary, with the camera-roll "files on demand" caveats.
- You want the backup to be **incremental**, with size+mtime skip
  detection so nightly runs only copy changed files.
- You want scheduled runs that survive flaky cloud sync without manual
  babysitting.

## Procedure (operator-runnable outline)

For a concrete reference implementation, see `references/onedrive-edeadlk.md`
(this session's actual deployed code at `~/output/AI Agents/Shared/Scripts/`).

### Step 1 — Decide the destination root

- Pick `PRIMARY_BACKUP_ROOT` (cloud mount, e.g. `~/OneDrive/AI Agents/`).
- Pick `LOCAL_FALLBACK_ROOT` (`~/output/AI Agents/` style mirror).
- `resolve_backup_root()` probes writability at every run, not just at
  install. If the primary is in EDEADLK or read-only, fall back to local
  mirror and continue. OneDrive will sync the local-mirror subtree back
  upstream once the cloud filter clears.

### Step 2 — Define the agent → folder mapping (single source of truth)

Edit ONE Python dict in `_lib.py`:

```python
AGENT_MAPPING = {
    "<agent_name>": {
        "agent_label": "human readable",
        "sources_state":   ["...", "..."],   # → <agent>/Backups/
        "sources_outputs": ["..."],          # → <agent>/Agent-Outputs/
        "sources_research"|"sources_projects": ["..."],   # thematic subdir
        "exclude_globs": [".env", "*.key", ...],
    },
}
```

**Use the **actual running-agent names** as folder names** when the user's
agents have stable identities. Don't reuse names from another machine's
folder layout — even if those folders already exist on the cloud mount,
creating parallel folders named after the actually-running agent(s) makes
diagnostics trivial.

### Step 3 — Run-target folder layout (canonical pattern)

```
<BACKUP_ROOT>/
├── <AgentA>/Backups/             ← config, cron registry, plugins
├── <AgentA>/Agent-Outputs/       ← cron output, audio, sessions
├── <AgentA>/Research/             ← (optional) research-style outputs
├── <AgentB>/Backups/
├── <AgentB>/Agent-Outputs/
├── <AgentB>/Projects/            ← (optional) project files
└── Shared/Scripts/  +  Shared/Backups/Manifests/
```

This matches two constraints at once:
- The cloud-side folder is **agent-keyed** (one folder per actually-
  running agent).
- The sub-shape is uniform across machines (`Backups/`, `Agent-Outputs/`,
  a single thematic subdir).

### Step 4 — Implement the shared library `_lib.py`

Functions the library MUST provide:

- `expand_home(p)` — `~/.hermes/...` resolution.
- `now_iso()`, `today_stamp()` — manifest timestamps.
- `probe_writable(root) -> (ok, reason)` — atomic mkdir+write+unlink probe
  that **catches `OSError` errno 11 (EDEADLK) and treats it as "unreachable"
  not "fatal"**.
- `resolve_backup_root() -> (Path, fell_back)` — primary probe, fallback
  on failure, with verbose stderr logging.
- `file_lock(lock_path, blocking=False, stale_after=6*3600)` — atomic
  `O_CREAT|O_EXCL` advisory lock with stale-detection (so a crashed prior
  run doesn't block the next one).
- `is_artifact(path)` — extension allowlist check (`.md`, `.json`, `.png`,
  etc.).
- `is_excluded(rel_path)` — global exclusions (`.git`, `node_modules`,
  `.venv`, `__pycache__`, `*.lock`, `.env`, `.envrc`, `auth*.json`).
- `redact_secrets_in_text(text)` and `redact_secrets_in_json(obj)` —
  best-effort redaction of fields matching `key/secret/password/token/api*`
  patterns; **NOT a guarantee**, but enough to make accidental publication
  less catastrophic.
- `copy_with_skip_or_redact(src, dst, redact=bool)` — incremental copy
  using a `.sha256` sidecar next to `dst`. Sidecar records size+mtime+
  sha256; skip if size+mtime unchanged.
- `make_manifest_header(kind, root)`, `write_manifest(manifest, root, kind)`
  — write a per-run JSON manifest and a `-latest.json` symlink.

### Step 5 — Implement the three pipelines

`backup_agent_state.py` — for each agent, gather `sources_state`, redact
config-shaped files, copy with `copy_with_skip_or_redact(redact=True)`.
**Hard-skip filenames that match `looks_like_secrets(src)`** (`auth.json`,
`auth-profiles.json`, `.env`) — record as `skipped-secret-name` in the
manifest; do NOT copy even with redaction.

Avoid collision logic that duplicates files on every run. Use the
sidecar's recorded `prev_src` to detect "same source, redo" vs "different
source, basename collision". Only the latter gets a `_from_<parent>_<name>`
disambiguating prefix.

`backup_agent_artifacts.py` — for each agent + destination kind
(`outputs`, `research`, `projects`), gather `sources_*`, walk the
allowlist, preserve relative path layout under
`<agent>/<Agent-Outputs|Research|Projects>/<source-relative-path>`. NEVER
redact artifacts (they're mine, raw).

`nightly_all_agents_backup.py` — wrapper. Acquires a global lock
(`.lock_nightly`); runs state + artifacts; reads both manifests;
prints the prescribed summary block:

```
✅ Nightly AI Agents backup complete
Finished: <iso-ts>
Duration: <s>
Backup root: <path>  fell_back=<bool>
State: copied <n>, size <b>, errors <n>
Artifacts: copied <n>, skipped <n>, size <b>, errors <n>
<Agent>: copied <n>, skipped <n>, size <b>
<Agent>: copied <n>, skipped <n>, size <b>
State manifest: <path>
Artifact manifest: <path>
```

### Step 6 — Hermes-side launcher (`~/.hermes/scripts/`)

`hermes cron` requires the script to be a FILENAME in
`~/.hermes/scripts/`. Write a thin wrapper:

```python
#!/usr/bin/env python3
PRIMARY = Path("<cloud>/AI Agents/Shared/Scripts/nightly_all_agents_backup.py")
FALLBACK = Path("<local>/AI Agents/Shared/Scripts/nightly_all_agents_backup.py")
# Probe in order; tolerate OSError (EDEADLK on cloud mount).
# Call the resolved path with the same argv as the launcher.
```

Make the launcher executable: `chmod +x ~/.hermes/scripts/<name>.py`.

### Step 7 — Schedule with Hermes cron

```
hermes cron create \
  --schedule "0 1 * * *" \
  --script <launcher-filename>.py \
  --no-agent \
  --deliver origin \
  --name "Nightly AI Agents backup" \
  --prompt "<short prompt that just acknowledges the run>"
```

Runbook prefers `01 * * * *` local; use that unless the user named a
specific hour. Delivery target `origin` posts the launcher's stdout into
this chat. Don't add an LLM prompt — `no_agent:true` skips the agent
loop entirely.

### Step 8 — Test before finalizing

1. `python3 -m py_compile` against every script (5 files: `_lib.py`, two
   backup scripts, wrapper, launcher).
2. `backup_agent_state.py --root <path> --dry-run` then
   `backup_agent_artifacts.py --root <path> --dry-run`. Expect
   non-zero candidate counts in every category.
3. First real run: expect `copied > 0` for state and artifacts,
   `errors == 0`.
4. **Second** real run immediately after: expect ALL files to show
   `"action": "skipped"` and totals like `copied=0 skipped=N`. This
   proves the sidecar skip detection works.
5. Verify `state-latest.json` and `artifacts-latest.json` symlinks
   exist and are valid JSON.

## Pitfalls

- **OneDrive CloudStorage filter EDEADLK (errno 11).** OneDrive's mount
  filter enters a cooldown lockout after long uptime (20+ hours) or
  after mid-tree metadata fetches hang. Symptoms: mkdir/open on ANY
  sub-tree under the mount fails instantly with `Resource deadlock
  avoided`, while top-level file CREATE works fine. The fix is a
  **probe-and-fallback** at every run, not at install. Don't trust a
  one-time writability check at install — OneDrive status changes hourly.
  Recovery: pause OneDrive sync, wait 30 seconds, resume. Saves the
  whole tree's filter cooldown.
- **Shell `*` glob skips dotfiles.** When mv-ing backup contents to a
  new directory, `mv src/* dst/` silently skips `*.sha256`, `.usage.json`,
  and hidden subdirs like `.openclaw/`. Use either explicit dotfile
  globs (`shopt -s dotglob` in bash) or `find -mindepth 1 -maxdepth 1
  -exec mv {} dst/ \;`.
- **Per-model/per-agent schema is restrictive.** Trying to set fields
  you remember from a different version of the schema silently fails
  validation. ALWAYS run `openclaw config validate` (or whatever the
  runtime's equivalent is) after every config edit.
- **JSON manifest schema split across state vs artifacts.** State
  manifest stores `per_agent[agent].totals` (flat); artifacts stores
  `per_agent[agent][kind].totals` (nested). When summarizing, sum
  BOTH shapes correctly — don't assume flat.
- **`auth.json` / `auth-profiles.json` are NEVER copied raw.** Hard-skip
  these by filename (don't even copy with redaction). The reasoning:
  real `key`/`secret` fields nest under provider-specific keys that
  redaction regex doesn't catch — one missed redaction leaks secrets
  silently. Better to skip than to redact imperfectly. Document the
  skip explicitly in the manifest so the operator can see what was
  intentionally not backed up.
- **Per-channel Telegram bot-fingerprinted image compression.** Telegram
  downscales images to ~96px, making them unreadable by vision models.
  If the user asks you to look at a Telegram-sent image and it fails,
  ask for the original URL + paste text instead. (Mirrors the openclaw
  skill's gotcha; relevant when uploading to ANY backup pipeline that
  reads from Telegram.)
- **Hermes cron script paths are FILENAME ONLY, not absolute.** Place
  the launcher in `~/.hermes/scripts/<name>.py`; reference it by name.

## Verification

After implementing:

```bash
# Smoke test (writes to whatever root resolves correctly)
python3 ~/.hermes/scripts/nightly_ai_agents_backup.py

# Force a specific root (debug helper)
python3 ~/.hermes/scripts/nightly_ai_agents_backup.py --root /Users/vivgatesai/OneDrive/AI\ Agents

# Manual cron next-tick (don't wait for 01:00)
hermes cron run <job_id>

# Inspect a manifest
jq '{totals, per_agent}' <backup_root>/Shared/Backups/Manifests/state-latest.json
```

If `copied=0 skipped=N` on the second consecutive run, skip detection
is working. If `errors > 0`, look at the manifest's `files[].error`
entries — usually a transient OSError (EDEADLK window during OneDrive
dehydration). Re-running usually fixes it.

## Support files

- `references/onedrive-edeadlk.md` — diagnosis + recovery for OneDrive
  CloudStorage filter stuck-locks. Includes a Python probe that
  distinguishes "EDEADLK" from "ENOSPC" from "read-only", essential
  to the resolve_backup_root() fallback decision.
- `references/agent-mapping-decisions.md` — decisions to make about
  destination folder names when the user's other machine uses one set
  of names and the local machine uses another. Includes the
  "mirror-but-not-reroute" pattern (reuse folder shells for cross-
  machine mirror compatibility, route live backups elsewhere).
- `templates/AGENT_MAPPING-py-constants.py-snippet.py` — starter
  Python constant block for `_lib.py::AGENT_MAPPING` with the canonical
  shape and per-source-place annotations.
- `templates/nightly_all_agents_backup.py` — wrapper script template
  with the prescribed summary block, lock acquisition, and per-agent
  output formatting.
- `templates/_lib-skeleton.py` — minimal `_lib.py` skeleton with the
  probe-and-fallback resolve function, decrypt-aware copy, sidecar
  skip detection, and redact helpers ready for USE_CASES to be slotted
  in.
