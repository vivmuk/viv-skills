---
name: cross-agent-backup-system
description: "Install and maintain a nightly state+artifact backup system for multiple AI agents on one machine (e.g. Hermes + OpenClaw + Paperclip together). Covers the standard 8-step install: filesystem layout, source discovery by agent, allowlist/exclude rules, redaction, manifest emission, Hermes cron no-agent scheduling, and the OneDrive CloudStorage-EDEADLK fallback-mirror pattern that recovers gracefully when cloud-sync is degraded. Use when the user says 'set up nightly backups for my agents', 'back up Hermes + Paridhi/Agni/OpenClaw', 'install AI Agents nightly backup', 'cross-agent state + artifact backup', 'mirror my agents to OneDrive', or any variant of cross-agent persistence orchestration."
version: 1.0.0
author: Hermes Agent (auto-authored, 2026-07-03)
license: MIT
platforms: [macos, linux]
triggers:
  - nightly ai agents backup
  - backup hermes + openclaw
  - cross agent state backup
  - cross-agent backup system
  - install agent backup orchestrator
  - mirror agents to onedrive
  - onedrive EDEADLK fallback
metadata:
  hermes:
    tags: [backup, onedrive, agents, hermes-cron, no-agent, orchestration, EDEADLK]
    related_skills: [hermes-agent, openclaw, self-hosted-agent-deployment]
---

# Cross-Agent Nightly Backup System

End-to-end recipe for backing up **state + artifacts** of every AI agent on one machine to a destination tree (default: OneDrive `AI Agents/`, with an auto-fall-back to a local mirror when the cloud sync is degraded). Class-level coverage — applies to Hermes, OpenClaw, Paperclip, Claude Code, Codex, OpenCode, and any future agent that lands in `~/.X/`.

---

## When to use this

The user is running **2+ AI agents on one machine** and wants them snapshot-style persisted to a version-stable location (typically `~/OneDrive/AI Agents/` or `~/output/AI Agents/`). Triggers:

- "set up nightly backups for my agents"
- "back up Hermes + Paridhi / Agni / my OpenClaw"
- "mirror my agent workspace to OneDrive"
- "I have multiple agents, set up cross-agent backup"
- Reports of `EDEADLK` from OneDrive's CloudStorage filter (this skill explains how to handle it gracefully — see `references/onedrive-cloudstorage-quirks.md`)

**Do NOT use this for**:
- VM-hosted agent backups (see `self-hosted-agent-deployment` for cloud-VM persistence)
- Per-session transcript backups only — those belong in `state.db` itself; this skill is for the *agent filesystem footprint* (config + generated outputs)
- "I want to git-backup my agent workspace" — that's a `git` workflow, not a file-copy

---

## Critical patterns (must carry forward)

### 1. Probe before commit — OneDrive CloudStorage filter is fragile

OneDrive's macOS CloudStorage filter (`/Users/<u>/Library/CloudStorage/OneDrive-Personal/`) returns `OSError: [Errno 11] Resource deadlock avoided` on `mkdir/open/stat` for sub-trees that are mid-sync or that have been unused for hours — even when top-level reads still work. **Never trust a directory listing; probe writability surgically before each operation**:

```python
def probe_writable(root: Path, probe_name: str = ".write_probe") -> tuple[bool, str]:
    try:
        root.mkdir(parents=True, exist_ok=True)
        probe = root / probe_name
        try:
            probe.write_text("ok")
            probe.unlink()
            return True, "ok"
        except OSError as e:
            return False, f"write_open_failed: errno={e.errno} {e.strerror}"
    except OSError as e:
        return False, f"mkdir_failed: errno={e.errno} {e.strerror}"
```

The launcher runs this at every backup pass and silently routes writes to the local mirror when OneDrive rejects. Full discussion + recovery recipe: `references/onedrive-cloudstorage-quirks.md`.

### 2. Two layers of fallback, not silent failure

```text
PRIMARY_BACKUP_ROOT   = ~/OneDrive/AI Agents/    # user-facing destination
LOCAL_FALLBACK_ROOT   = ~/output/AI Agents/      # writable local mirror

# Resolution dance:
backup_root, fell_back = resolve_backup_root(verbose=True)
# If OneDrive mkdir-probe fails with EDEADLK → fall back without raising.
# The launcher records "fell_back=True" in the manifest so the user knows.
```

Always write the local mirror even when OneDrive succeeds — the local tree doubles as your smoke-test backup AND a OneDrive-sync source-of-truth (when OneDrive unstucks, it will sync the local mirror upstream lazily).

### 3. Skip detection via sidecar, EVERYWHERE

```python
# Sidecar lives next to every copied file
sidecar = dst.with_suffix(dst.suffix + ".sha256")
# { "size": N, "mtime": M, "sha256": "abc...", "src": "...", "copied_at": "..." }
```

If `dst.exists() AND sidecar["size"] == src_size AND sidecar["mtime"] == src_mtime`: skip the copy. Add `sidecar["src"]` to that sidecar dict — it powers **collision-detection re-runs** (see #5).

Avoid sha256 on every backup pass for performance: use size+mtime as the fast path. If paranoid correctness is required, do a sha256 sweep on a weekly cron, not nightly.

### 4. Two splits, every destination

For each agent, the destination layout is the same regardless of which agent you're configuring:

```text
<AGENT>/Backups/         state + config files (yaml, json, plugin manifests, db files)
<AGENT>/Agent-Outputs/   generated artifacts (allowlist extensions, preserve relative paths)
<AGENT>/Research/        research-oriented outputs (optional, e.g. youtube_intelligence)
<AGENT>/Projects/        project sub-trees (optional, e.g. workspace/viv-mind-scaffold)
```

Mapping is the user's `AGENT_MAPPING` table in `_lib.py` — one place to retarget everything.

### 5. Collision detection via sidecar.src

When two different sources have the same basename (e.g. two files named `catalog.json` from different plugin sources), don't just `_collision_` prefix unconditionally — use the sidecar to know if the existing destination came from the same source already:

```python
prev_src = None
if dst.exists() and sidecar.exists():
    try:
        prev_src = json.loads(sidecar.read_text()).get("src")
    except (json.JSONDecodeError, OSError):
        pass

if prev_src is not None and prev_src != str(src):
    # Real collision — keep both copies, prefix from prior source's parent
    rel = f"_from_{Path(prev_src).parent.name}__{src.name}"
    dst = dst_root / rel
```

Without this check, every re-run produces spurious `_collision_` siblings. With it, same-source re-copies overwrite normally; only true cross-source collisions get prefixed.

### 6. Hard-skip raw secrets by NAME; redact-by-VALUE for config-shaped files

```python
# Hard-skip these names outright (NEVER copy, not even redacted):
SECRET_FILE_NAMES = {".env", ".envrc", "auth-profiles.json", "auth.json"}

# For YAML/JSON/.env/.toml/.txt/.md, redact by value:
# - Replace values aligned to SECRET_KEY_PATTERNS with "<REDACTED>"
# - Use redact_secrets_in_text() for regex-based (YAML/.env)
# - Use redact_secrets_in_json() for structured JSON traversal
```

The user's spec line "Do not copy raw secrets" is satisfied by both rules. The two-tier approach keeps high-trust files (`auth.json`) entirely absent while still showing config-shaped files with their key schemas visible.

### 7. Allowlist extension for artifacts

Don't try to BACK UP ALL files under `~/.openclaw/workspace/` — that includes `node_modules/`, build artifacts, audio cache, etc. Apply an allowlist of portable extensions:

```python
ARTIFACT_EXTENSIONS = {".md", ".txt", ".json", ".jsonl", ".yaml", ".yml", ".toml",
    ".csv", ".tsv", ".pdf", ".html", ".htm", ".pptx", ".docx", ".xlsx",
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg",
    ".mp4", ".mov", ".webm", ".mp3", ".wav", ".ogg", ".m4a", ".zip",
    ".py", ".ipynb", ".js", ".jsx", ".ts", ".tsx", ".css", ".scss",
    ".sql", ".xml"}
```

Skip everything else. Studies + code + docs + media in; `node_modules`/compiles/venv/transient state out.

### 8. Manifest schema — must be additive across runs

Every run produces one manifest under `Shared/Backups/Manifests/<kind>-YYYY-MM-DD-HHMMSS.json`. Always also write a `<kind>-latest.json` symlink for easy retrieval:

```python
out = manifests_dir / f"{kind}-{stamp}.json"
out.write_text(json.dumps(manifest, indent=2, default=str))
latest = manifests_dir / f"{kind}-latest.json"
try:
    if latest.is_symlink() or latest.exists():
        latest.unlink()
    os.symlink(out.name, str(latest))
except OSError:
    shutil.copy2(out, latest)  # symlinks unsupported on some FS — fall back to copy
```

Manifest fields:
- `kind`, `agent` (combined label), `machine`, `user`, `backup_root`, `fell_back`
- `started_at`, `completed_at`, `duration_seconds`
- `totals`: `files_copied`, `files_skipped`, `files_redacted`, `bytes_copied`, `errors`
- `per_agent`: nested `{agent: {outputs: {totals: {...}}, research: {...}}}` for artifacts; flat `{agent: {totals: {...}}}` for state.
- `files`: per-file list with src/dst/size/action
- `errors`: per-file list with src/error/traceback

The exact schema is enforced at write time — keep it stable across script versions so cross-run diff tools work.

---

## Standard 8-step install

When the user says "install the cross-agent backup system", execute these eight steps. Each has a fixed commit point so a partial install is recoverable.

### Step 1 — Recon

1. Find the destination root. On macOS, check:
   ```bash
   ls -la /Users/<u>/OneDrive 2>/dev/null     # symlink target
   test -d "/Users/<u>/Library/CloudStorage/OneDrive-Personal/<AI Agents>" && echo OK
   ```
2. Read the agent's `HEARTBEAT.md` if present at `~/.openclaw/workspace/HEARTBEAT.md` — it often has persona/identity contextual notes that disambiguate agent naming.
3. Discover the live agents on the machine:
   ```bash
   ls -la ~/.hermes/profiles/ 2>/dev/null           # Hermes profiles
   ls -la ~/.openclaw/agents/ 2>/dev/null           # OpenClaw agents
   # Add more if the user has Claude Code / Codex / OpenCode / Paperclip
   ```
4. **Ask the user once**, plainly, before writing: "I see agent X running as Y. Is that right? Do you have a naming convention for backup destinations (e.g. Netrak/Katha/Dhristi are names on your other machine)?"

This last sentence matters. **Don't assume** — the user often uses `Netrak/Katha/Dhristi`-style Sanskrit-named folders from a different machine. If you assume the running agents map to those folder names, you create the wrong artifacts. Always confirm.

### Step 2 — Probe destination

```python
primary_ok, primary_reason = probe_writable(Path(PRIMARY_BACKUP_ROOT))
fallback_ok, fallback_reason = probe_writable(Path(LOCAL_FALLBACK_ROOT))
# If primary_ok: use primary. else use fallback AND log fell_back=True.
```

### Step 3 — Create directory skeleton

```bash
mkdir -p $BACKUP_ROOT/Shared/Backups/Manifests
mkdir -p $BACKUP_ROOT/Shared/Scripts
mkdir -p $BACKUP_ROOT/{Netrak,Katha,Dhristi}/{Backups,Agent-Outputs}
mkdir -p $BACKUP_ROOT/Katha/Research
mkdir -p $BACKUP_ROOT/Dhristi/Projects
```

Adjust agent names to match the user's confirmed convention.

### Step 4 — Author the four scripts + lib

Write to `Shared/Scripts/`:
1. `_lib.py` — see `templates/backup_lib.py` for the canonical version
2. `backup_agent_state.py` — state+config snapshot
3. `backup_agent_artifacts.py` — incremental artifact port with allowlist
4. `nightly_all_agents_backup.py` — wrapper + summary print

All four are Python stdlib-only, target Python 3.9+, no third-party deps.

### Step 5 — Sync to local mirror if OneDrive is the primary

If `PRIMARY_BACKUP_ROOT` is OneDrive, your scripts ALSO need to live there (the launcher will look there first). If OneDrive is in EDEADLK for `Shared/Scripts/`, retry after a short pause; if still failing, the launcher tolerates the local mirror as the canonical source.

### Step 6 — Hermes-side launcher

Hermes cron jobs invoke scripts by **filename only** — the absolute path is reject-script by the scheduler. The launcher at `~/.hermes/scripts/<basename>.py` is the thin wrapper:

```python
PRIMARY_SCRIPT = Path("/Users/<u>/OneDrive/AI Agents/Shared/Scripts/nightly_all_agents_backup.py")
FALLBACK_SCRIPT = Path("/Users/<u>/output/AI Agents/Shared/Scripts/nightly_all_agents_backup.py")

def find_canonical() -> Path:
    for label, p in (("primary", PRIMARY_SCRIPT), ("fallback", FALLBACK_SCRIPT)):
        try:
            if p.exists():
                return p
        except OSError as e:
            # EDEADLK from OneDrive — fall through to local
            continue
    raise FileNotFoundError(...)
```

The OSError fallback is **specifically** for OneDrive's deadlock-rejection; without it, the launcher dies with `[Errno 11]` whenever OneDrive is degraded.

### Step 7 — Schedule via Hermes cron

For Hermes users, always `no_agent: true` for backup/maintenance:

```bash
# Use the cronjob tool / `hermes cron create`
schedule: "0 1 * * *"      # 01:00 local — least-friction ±hermes cron edit
name:    "Nightly AI Agents backup"
script:  <basename>.py     # FILENAME ONLY — Hermes enforces this
no_agent: true
deliver: "origin"          # current chat; "all" if you want multi-channel
```

For non-Hermes boxes, native schedulers:
- macOS: launchd plist at `~/Library/LaunchAgents/<name>.plist`
- Linux: `/etc/cron.d/<name>` or root crontab
- Windows: Task Scheduler via `Register-ScheduledTask`

### Step 8 — Test, then commit

1. `python3 -m py_compile` each script (5/5 OK).
2. `--dry-run` each script. Confirm counts match expectation.
3. First real run end-to-end.
4. Re-run end-to-end to verify skip detection (count of "skipped" should be ~100% of first run).
5. Update the user's setup documentation with: machine name, OneDrive path, local shortcut paths, backup scripts, schedule, test results, any issues encountered.

---

## Default user preferences this skill encodes

These come from the user's mid-turn feedback during the first install. Embed them so future sessions don't have to rediscover:

- **Runbook format for procedural asks.** When the user asks for an equation to be set up, lead with a Markdown task-list (`- [ ]`), exact shell commands per step, per-phase time estimates, and a `## Daily-driver` cheat-sheet section at the end. Prose walkthroughs are wrong format — user prefers operator-runnable checklists. See `references/runbook-format-preference.md`.

- **Agent naming conventions.** User runs agents under Sanskrit/Indic names (Agni, Paridhi, Netrak, Katha, Dhristi). The folder name on OneDrive does NOT need to match the running agent — the user often uses a "mirror of another computer's folder layout" convention. Always ask once: "Which running agent maps to which destination folder?"

- **The user's machine folder IS the user's preferred destination.** When the user says "that is a wonderful folder that I have created" referring to OneDrive/AI Agents, treat it as the BASELINE canonical location. Don't propose local-only alternatives without checking first.

---

## Known pitfalls (read before installing for someone)

### Pitfall 1 — don't trust OneDrive's `ls`/`stat` after extended uptime
This is the #1 thing that bites installs. Symptom: `terminal ls`/`stat`/`cp` hang for minutes then return `EDEADLK` or nothing. Top-level reads may still work; sub-tree writes usually don't. ALWAYS probe with a tiny writable file (`probe.write_text("ok"); probe.unlink()`) — see `references/onedrive-cloudstorage-quirks.md`.

### Pitfall 2 — Hermes cron blocks absolute script paths
Whatever you do, the `script` field in `hermes cron create` accepts filenames only, no `/`. If you pass `/Users/<u>/.hermes/scripts/foo.py` you'll get `"Script path must be relative to ~/.hermes/scripts/"`. Use `foo.py`.

### Pitfall 3 — collision detection needs sidecar.src, not just `exists()`
Without the sidecar.src check, every re-run produces spurious `_collision_*` siblings even when the same source is being re-copied. Always include `src` in the sidecar payload.

### Pitfall 4 — `manifest["per_agent"]` shape differs between state and artifacts
State writes `per_agent[agent] = {totals}` flat. Artifacts write `per_agent[agent][kind] = {totals}` nested. The summary code in the wrapper script must handle BOTH shapes — see `summarize_manifest()` in `templates/backup_lib.py`.

### Pitfall 5 — daemon files between runs may invalidate skip detection
`skills/.usage.json` (curator), `cron/jobs.json` (if cron is also running), `state.db` (sessions actively writing) all change mtime regularly. Skip detection uses `size+mtime` fast path; if false-positive skips are unacceptable, accept that ~1 state file will re-copy per run. Don't switch to full sha256 by default — that's a 5-10× cost.

### Pitfall 6 — `execute_code` is blocked in some privileged contexts
The Hermes `execute_code` tool may reject calls in cron-context sessions with a "BLOCKED" error about subprocess bypass. That's specific to cron jobs, not the install. For installations, write Python to a temp file and run via `terminal`. Don't rely on `execute_code` — see example probe script in `scripts/probe_writable_root.py`.

### Pitfall 7 — `~/.hermes/profiles/<profile>/cron/output` is a *state* source for many agents but an *artifact* destination for the running one
Confusion source. The `~/.hermes/cron` directory has both — `jobs.json` (state) AND `output/` (artifact). Split them: `state.sources = ["~/.hermes/cron/jobs.json"]`, `artifacts.sources_outputs = ["~/.hermes/cron/output"]`.

---

## Files in this skill

- `SKILL.md` — this file
- `references/onedrive-cloudstorage-quirks.md` — OneDrive `ls` hang / `EDEADLK` patterns + surgical probe recipes
- `references/agent-folder-naming-conventions.md` — the Netrak/Katha/Dhristi convention + when to ask the user
- `references/runbook-format-preference.md` — the runbook format (task list + commands + cheat-sheet) the user prefers
- `scripts/probe_writable_root.py` — surgical probe utility (mtime-stable, doesn't trigger OneDrive metadata fetch)
- `templates/backup_lib.py` — canonical `_lib.py` with file_locking, redaction, manifest emission, skip detection
- `templates/backup_orchestrator.py` — minimal installable starter that combines state + artifacts + summary

---

## Daily driver

```bash
# Dry-run (counts only, no writes)
python3 ~/output/AI\ Agents/Shared/Scripts/backup_agent_state.py --root ~/output/AI\ Agents --dry-run
python3 ~/output/AI\ Agents/Shared/Scripts/backup_agent_artifacts.py --root ~/output/AI\ Agents --dry-run

# Real run (writes to local mirror if OneDrive EDEADLK)
python3 ~/.hermes/scripts/nightly_ai_agents_backup.py

# Force a specific destination
python3 ~/.hermes/scripts/nightly_ai_agents_backup.py --root /Users/<u>/OneDrive/AI\ Agents

# Trigger cron job manually
hermes cron run <job_id>     # lookup via hermes cron list
hermes cron pause  <job_id>  # when OneDrive maintenance is happening
hermes cron resume <job_id>

# Inspect latest manifest results
jq '{totals, per_agent}' "$HOME/output/AI Agents/Shared/Backups/Manifests/state-latest.json"
```
