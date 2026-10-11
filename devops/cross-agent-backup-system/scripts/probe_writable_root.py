#!/usr/bin/env python3
"""Surgical probe of writability for a backup root, with EDEADLK tolerance.

Use when the destination may be a cloud-mounted filesystem (OneDrive
CloudStorage, Google Drive for Desktop, Dropbox Smart Sync, iCloud Drive)
that can return `EDEADLK` (errno 11) from `os.listdir`, `os.stat`, and even
`os.path.exists` after extended uptime.

The right way to verify writability in such environments is *not* to call
`os.listdir(root)` — that triggers remote metadata fetch and may hang or
return EDEADLK. The right way is: try to write-and-remove a tiny probe file.
If that succeeds, the path is writable.

Usage:
    # Default: probe the user's OneDrive AI Agents + local mirror.
    python3 scripts/probe_writable_root.py

    # Custom paths:
    python3 scripts/probe_writable_root.py \
        --primary /Users/u/OneDrive/AI\ Agents \
        --fallback /Users/u/output/AI\ Agents \
        --verbose
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Tuple

DEFAULT_PRIMARY = "/Users/vivgatesai/OneDrive/AI Agents"
DEFAULT_FALLBACK = "/Users/vivgatesai/output/AI Agents"


def probe_writable(root: Path, probe_name: str = ".write_probe",
                   timeout: float = 5.0) -> Tuple[bool, str]:
    """Return (ok, reason) after attempting write/remove of a probe file.

    Tolerates OSError[Errno 11] (Resource deadlock) as 'unreachable'."""
    t0 = time.time()
    try:
        # mkdir with exist_ok=True first (so we surface EDEADLK on the op
        # rather than on subsequent stat lookups).
        root.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        return False, f"mkdir_failed: errno={e.errno} {e.strerror}"
    if time.time() - t0 > timeout:
        return False, f"mkdir_took_too_long: {time.time()-t0:.1f}s"

    probe = root / probe_name
    try:
        probe.write_text("ok")
    except OSError as e:
        return False, f"write_failed: errno={e.errno} {e.strerror}"
    if time.time() - t0 > timeout:
        # If write succeeded but orthogonal stat was slow: still treat as OK
        # (we already wrote the bytes through to whatever FS layer is active).
        try:
            probe.unlink()
        except OSError:
            pass
        return True, f"slow_but_wrote ({time.time()-t0:.1f}s)"

    try:
        probe.unlink()
    except OSError as e:
        return True, f"wrote_but_unlink_failed: errno={e.errno} {e.strerror} (probably OK; clean up later)"
    return True, "ok"


def safe_exists(path: Path) -> bool:
    """os.path.exists with EDEADLK tolerance — returns False on any OSError."""
    try:
        return path.exists()
    except OSError:
        return False


def resolve(primary: Path, fallback: Path | None, verbose: bool = False
            ) -> Tuple[Path, bool, str]:
    """Probe primary first, then fallback, returning (chosen_root, fell_back, why)."""
    if verbose:
        print(f"[probe] primary:  {primary}", file=sys.stderr)

    # Don't call os.listdir — that's the operation that hangs. Just probe.
    ok, why = probe_writable(primary)
    if ok:
        if verbose:
            print(f"[probe] primary OK: {primary} ({why})", file=sys.stderr)
        return primary, False, why

    if verbose:
        print(f"[probe] primary UNREACHABLE: {primary} ({why})", file=sys.stderr)

    if fallback is None:
        raise RuntimeError(f"no fallback configured; primary unreachable: {why}")

    if verbose:
        print(f"[probe] fallback: {fallback}", file=sys.stderr)
    ok, why2 = probe_writable(fallback)
    if not ok:
        raise RuntimeError(
            f"PRIMARY and FALLBACK both unreachable.\n  primary:  {why}\n  fallback: {why2}"
        )
    if verbose:
        print(f"[probe] fallback OK: {fallback} ({why2})", file=sys.stderr)
    return fallback, True, why2


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Surgical probe for backup-root writability.")
    ap.add_argument("--primary", default=DEFAULT_PRIMARY,
                    help=f"Primary destination root (default: {DEFAULT_PRIMARY})")
    ap.add_argument("--fallback", default=DEFAULT_FALLBACK,
                    help=f"Local fallback root (default: {DEFAULT_FALLBACK})")
    ap.add_argument("--no-fallback", action="store_true",
                    help="Probe only --primary; fail loudly if unreachable.")
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args()

    primary = Path(args.primary)
    fallback = None if args.no_fallback else Path(args.fallback)

    try:
        chosen, fell_back, why = resolve(primary, fallback, args.verbose)
    except RuntimeError as e:
        print(f"PROBE FAILED: {e}", file=sys.stderr)
        return 2

    print(json := __import__("json").dumps({
        "primary": str(primary),
        "fallback": str(fallback) if fallback else None,
        "chosen_root": str(chosen),
        "fell_back": fell_back,
        "reason": why,
    }, indent=2))
    return 0 if not fell_back else 0  # non-zero only on hard failure, not on fallback


if __name__ == "__main__":
    sys.exit(main())
