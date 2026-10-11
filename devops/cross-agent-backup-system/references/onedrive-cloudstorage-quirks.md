# OneDrive CloudStorage filter quirks (macOS XFG / EDEADLK)

OneDrive on macOS (Personal, version ≥ 23.x) mounts the user's OneDrive tree under `~/Library/CloudStorage/OneDrive-Personal/` via a system CloudStorage XPC filter. The filter synchronizes lazily and, after extended uptime or sync glitches, the sub-trees can return `EDEADLK` (errno 11) on `mkdir()`, `stat()`, `cp`, and even pure `os.listdir()` calls. Top-level reads/writes usually still work.

These are **not** transient hangs. They persist for minutes to hours and idempotent retry does not fix them — you need to detect AND fall back.

## Symptoms

```text
$ ls -la /Users/vivgatesai/Library/CloudStorage/OneDrive-Personal/AI\ Agents/
[Command timed out after 90s]
```

```text
$ python3 -c "import os; os.makedirs('/Users/vivgatesai/OneDrive/AI Agents/x', exist_ok=True); print('ok')"
OSError: [Errno 11] Resource deadlock avoided: ...
```

```text
$ cp /tmp/probe.md "/Users/vivgatesai/OneDrive/AI Agents/Shared/Scripts/probe.md"
cp: ...: Resource deadlock avoided
```

```text
$ python3 -c "import os; os.path.exists('/Users/vivgatesai/OneDrive/AI Agents/setup-documentation.md'); print('ok')"
# returns False instead of True even though the file exists
```

The pattern: ops that need *new* metadata fetch fail (mkdir, listdir, read of ghost files). Ops that only need cached metadata (top-level files added before the system went degraded) sometimes still succeed.

## Root cause (best understanding)

The CloudStorage XPC filter holds a global lock when processing a large backlog of syncs (rehydrate-after-restart, big-rename events, file-on-demand hydration requests while the user is on a slow connection). New operations queue behind the lock-holders; the filter's deadlock-avoidance heuristic then **rejects** new operations immediately instead of blocking them, so they fail fast with `EDEADLK`. Once the backlog drains (typically minutes), the lock releases, and `ls`/`mkdir`/`cp` start working again.

After 23 hours of OneDrive uptime on a busy account, expect the filter to enter this state repeatedly. Pausing+resuming sync via the macOS menu bar usually clears it within 30 seconds.

## Recovery recipe — surgical probe

Don't `ls` the directory. Probe with a tiny writable file — that's the only operation that's reliable even when listings are broken:

```python
def probe_writable(root: Path, probe_name: str = ".write_probe") -> tuple[bool, str]:
    """Returns (ok, reason). True means we can safely use this root for writes."""
    try:
        root.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        return False, f"mkdir_failed: errno={e.errno} {e.strerror}"
    probe = root / probe_name
    try:
        probe.write_text("ok")
        probe.unlink()
        return True, "ok"
    except OSError as e:
        return False, f"write_failed: errno={e.errno} {e.strerror}"
```

Caller pattern:

```python
primary = Path("/Users/<u>/OneDrive/AI Agents")
fallback = Path("/Users/<u>/output/AI Agents")
ok, why = probe_writable(primary)
if ok:
    return primary, False
ok, why = probe_writable(fallback)
if not ok:
    raise RuntimeError(f"neither root writable; primary={why}, fallback={why}")
return fallback, True
```

The script must hold EDEADLK tolerance DEEPER than the probe, too. When iterating MP4 files, an `os.path.exists(some_subdir_file).exists()` return may itself throw `EDEADLK`. Wrap exists/stat in try/except and treat `OSError(errno=11)` as "skip" not "fail":

```python
def safe_exists(path: Path) -> bool:
    try:
        return path.exists()
    except OSError:
        return False
```

Refer to the skill's `scripts/probe_writable_root.py` for a fully hardened probe that handles EDEADLK at every layer.

## User-facing message

When the script falls back, emit a clear line in the manifest + log:
```text
[backup-root] PRIMARY unreachable (write_failed: errno=11); using FALLBACK: /Users/<u>/output/AI Agents
backup_root: /Users/<u>/output/AI Agents   fell_back: true
```

The user reads the manifest and knows: cloud is grumpy tonight, local tree has the up-to-date snapshot, OneDrive will sync it upstream lazily when the filter recovers.

## How to clear the deadlock manually (for the operator)

```text
1. Click the OneDrive icon in the macOS menu bar.
2. "Pause syncing" → wait 10s → "Resume syncing".
3. Wait 30-60s for the filter to flush its backlog.
4. Test again: `python3 -c "import os; os.path.exists('/Users/<u>/OneDrive/AI Agents/anything.txt')"`.
```

If menu-bar pause/resume doesn't clear it:
```text
$ killall OneDrive; sleep 5; open -a OneDrive
# Wait for re-login flow in OneDrive.app. Filter re-initializes cleanly.
```

NEVER `kill -9` OneDrive mid-sync — that may corrupt the local cache.

## Once-cleared, what to do

Once the OneDrive filter recovers, your local mirror is already up-to-date. The sync-utility will reconcile upstream lazily (OneDrive shows files in "available online" state briefly, then "synced" once uploaded).

For *script* files inside the cloud tree that you couldn't write earlier: re-run `cp` from the local mirror to the cloud tree; the writes now succeed because the filter no longer holds the EDEADLK lock.
