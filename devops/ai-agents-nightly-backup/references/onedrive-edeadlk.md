# OneDrive CloudStorage EDEADLK — diagnosis and recovery

## Symptom

Operations on a OneDrive-mounted path return instantly with:

```
OSError: [Errno 11] Resource deadlock avoided
```

This happens **non-deterministically** after OneDrive's been running for
hours (typically 18+ hours of uptime) and begins rejecting mkdir/open on
specific sub-trees. Top-level file CREATE often still works; sub-trees
under any non-rooted directory begin failing.

The CloudStorage driver is `FUSEProvider`; the kernel returns EDEADLK
when the filter's internal lock state is "cooling" from a previous
metadata-fetch hang. There's no upstream-visible cause.

## Diagnosis (probe script)

```python
import os, errno
def probe(root: Path) -> tuple[bool, str]:
    try:
        root.mkdir(parents=True, exist_ok=True)
        probe = root / ".write_probe"
        try:
            probe.write_text("ok"); probe.unlink()
            return True, "ok"
        except OSError as e:
            return False, f"write_failed: errno={e.errno} ({errno.errorcode.get(e.errno, '?')}) {e.strerror}"
    except OSError as e:
        return False, f"mkdir_failed: errno={e.errno} ({errno.errorcode.get(e.errno, '?')}) {e.strerror}"
```

`errno.errorcode[11]` is `'EDEADLK'`. Distinguish from ENOSPC (28),
EROFS (30), EACCES (13) — all have different recovery semantics:

- **EDEADLK (11)**: transient, retry-with-fallback is correct.
  Recovery is "wait + retry". Don't fail-loud; defer to local mirror.
- **ENOSPC (28)**: real disk full. Fail-loud; abort the backup.
- **EROFS (30)**: read-only filesystem. Fail-loud; the operator picked
  the wrong destination.
- **EACCES (13)**: permission. Fail-loud; chmod / sudo needed.

## Recovery steps (operator or self-service)

1. **Pause OneDrive sync** from the macOS menu bar (right-click the
   OneDrive icon → "Pause syncing"). The CloudStorage filter's lock
   cooldown begins to release.
2. **Wait 30 seconds**.
3. **Resume OneDrive sync** (same menu). The filter's internal state
   restarts fresh; previously rejected operations should succeed again.
4. **Verify** by re-running the probe.

If the probe still fails after resume, the CloudStorage provider is
in a worse state than usual and the only reliable fix is:

```bash
# Force-quit OneDrive, restart
osascript -e 'quit app "OneDrive"'
sleep 3
open -a OneDrive
```

After this, OneDrive does a sweep of the on-disk cache and usually
clears the EDEADLK.

## Why probe-at-every-run vs probe-at-install

A one-time at-install writability check looks fine because OneDrive
isn't yet in EDEADLK when the script is first configured. Hours later,
the filter enters the stuck state. Backup runs that day FAIL or
INCORRECTLY REPORT SUCCESS (because the meta-state was cached).

Always probe at script start. The cost is one mkdir+write+unlink per
run — negligible.

## Pattern: deferred-mirror resolution

In `_lib.py`:

```python
def resolve_backup_root(verbose=False):
    primary = Path(PRIMARY_BACKUP_ROOT)
    primary_ok, reason = probe_writable(primary)
    if primary_ok:
        if verbose: print(f"[backup-root] PRIMARY OK: {primary}", file=sys.stderr)
        return primary, False
    fallback = Path(LOCAL_FALLBACK_ROOT)
    fallback.mkdir(parents=True, exist_ok=True)
    fallback_ok, fb_reason = probe_writable(fallback)
    if not fallback_ok:
        raise RuntimeError(f"PRIMARY unreachable ({reason}) AND FALLBACK unreachable ({fb_reason}). Cannot proceed.")
    if verbose: print(f"[backup-root] PRIMARY unreachable ({reason}); using FALLBACK: {fallback}", file=sys.stderr)
    return fallback, True
```

The `fell_back` boolean propagates through the manifest + summary
print so operators can see when the local mirror was used. Once
OneDrive recools, the next backup writes to OneDrive again — and the
local-mirror subtree OneDrive will pick up via its own lazy sync.
