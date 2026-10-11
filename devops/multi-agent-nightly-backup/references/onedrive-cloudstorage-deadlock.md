# OneDrive CloudStorage `EDEADLK` (errno 11) — diagnostic + recovery

Reproducible transcript from the install session
(2026-07-03 06:25 EDT, host macOS 26.5, OneDrive Personal).

## Symptoms

- OneDrive process has been up ~24h without a sync deferral.
- `os.listdir` / `ls -la` on a directory under
  `~/Library/CloudStorage/OneDrive-Personal/<root>/<subdir>/` **hangs**
  for 30+ seconds (cloud roundtrip synchronously). Sometimes
  minutes.
- New `mkdir` or `write` ops on a sub-tree under the OneDrive root
  start returning `Errno 11 Resource deadlock avoided` instead of
  ENOENT or EACCES.
- Top-level paths (`/<root>/<file>.md`) usually still succeed.
- Eventually the filter cools down — `os.path.getsize(f)` /
  `f.open()` start returning again, but the cooldown can be 5 min to
  several hours.

## Why the filter cools down

macOS OneDrive uses the CloudStorage provider framework. After a
prolonged uptime the filter can hit Apple's `Resource deadlock
avoided` errno 11 (a soft signal that the kernel is asking the filter
to back off). The filter's cooldown is automatic but slow — restarts
or manual pauses via the menubar shortcut (`Cmd-click → Pause`)
clear it faster.

## Diagnostic probe (paste into a `python3 -c`)

```python
import os, time

p = "/Users/YOU/Library/CloudStorage/OneDrive-Personal/<root>/<file>"
t = time.time()
try:
    with open(p) as f:
        data = f.read()
    print(f"read OK in {time.time()-t:.2f}s, {len(data)} bytes")
except OSError as e:
    print(f"FAIL: errno={e.errno} ({e.strerror})")
```

Three possible outcomes (from an actually-running session):

| Outcome | Meaning |
|---|---|
| `read OK in 0.04s, 12345 bytes` | Filter healthy; proceed |
| `FAIL: errno=11 (Resource deadlock avoided)` | Filter in cooldown; skip this OneDrive write window |
| Timeout (any `terminal(60s)`) | Cloud-metadata fetch hung; the *parent* of the target is also stuck. Probe a sibling path first to confirm scope. |

## Recovery recipe

1. **Don't keep retrying** — `sleep 5 && retry` doesn't unstick
   the filter; it just spends more sync quota.
2. **Pause + Resume** in the OneDrive menubar — fastest
   cold-clear (often clears in <30 seconds).
3. **Quit + relaunch** the OneDrive app:
   - `pkill -f OneDrive`
   - `open -a OneDrive`
   - Wait for first sync to settle (~30-120s depending on backlog).
4. **As a fallback for scheduled jobs**: any script that writes to
   OneDrive with a `mkdir + write_probe` precheck **must** treat
   `Errno 11` as "fall back to local mirror" — never as a hard
   error. See `templates/nightly_wrapper.py` for the canonical
   try/except shape.

## What stops working during a deadlock

- `os.listdir` on the OneDrive root (hangs)
- `os.path.exists` if the parent path triggers sync (usually OK
  for known-cached paths)
- `os.mkdir`/`open(..., 'w')` on a sub-directory (EDEADLK)
- `xattr -l` to inspect hydration state (hangs)

## What keeps working

- `open()` on a file already hydrated (recently-touched)
- `cp` on a single file at the OneDrive root (top-level Only)
- Writes via the OneDrive menubar GUI

## Worked-around pattern (paste-ready)

```python
def probe_writable(root: Path) -> tuple[bool, str]:
    """mkdir + write + unlink probe — tolerates Errno 11 EDEADLK."""
    try:
        root.mkdir(parents=True, exist_ok=True)
        probe = root / ".write_probe"
        probe.write_text("ok")
        probe.unlink()
        return True, "ok"
    except OSError as e:
        return False, f"errno={e.errno} ({e.strerror})"
```

If the probe returns False, the script's `resolve_backup_root()`
should fall through to a local mirror — do NOT raise, do NOT loop
retry. The mirror is the canonical safe destination during
cooldowns; the cloud will sync it back once the filter clears.

## Why this is a class-level gotcha, not just one bad day

- Apple CloudStorage provider filters have a documented "cooling"
  behavior on long uptimes (no public bug number; behavior
  observed across at least three macOS 14/15/26 minor versions
  here).
- Any unattended script that writes to `~/Library/CloudStorage/*`
  needs this probe, not just OneDrive: iCloud Drive can exhibit
  similar `EDEADLK` windows; Google Drive's Backup-and-Sync
  occasionally hangs `os.listdir` for the same root cause.
- The pattern does NOT apply to S3-direct or rsync-over-SSH
  destinations — those don't go through CloudStorage filters.
