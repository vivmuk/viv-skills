#!/usr/bin/env python3
"""Standalone backup-root health probe.

Use this on its own as a smoke check before scheduling a nightly
backup, or to recover from an `EDEADLK` cooldown. Prints the resolved
root + fell-back flag + a single-line summary suitable for cron
delivery.

Usage:
  python3 probe_backup_root.py [--root PATH] [--json]

Exit codes:
  0  primary reachable
  1  unreachable on both primary AND fallback — abort
  2  primary unreachable, fallback OK (still proceeds; not a hard fail)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Make sibling _lib importable.
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from _lib import resolve_backup_root, now_iso


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=str, default=None,
                    help="Override the resolved backup root (testing).")
    ap.add_argument("--json", action="store_true",
                    help="Emit JSON instead of plain text.")
    args = ap.parse_args()

    t0 = time.time() if (time := __import__("time")) else 0

    rc = 0
    if args.root:
        root = Path(args.root)
        root.mkdir(parents=True, exist_ok=True)
        fell_back = False
        # Quick writable probe
        try:
            probe = root / ".write_probe"
            probe.write_text("ok"); probe.unlink()
            primary_ok = True
        except OSError as e:
            primary_ok = False
            print(f"probe failed: errno={e.errno} ({e.strerror})", file=sys.stderr)
            rc = 1
    else:
        try:
            root, fell_back = resolve_backup_root(verbose=False)
            primary_ok = not fell_back
            rc = 0 if primary_ok else 2
        except RuntimeError as e:
            print(f"FATAL: {e}", file=sys.stderr)
            return 1

    payload = {
        "ok": primary_ok,
        "root": str(root),
        "fell_back": fell_back,
        "checked_at": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        status = "OK" if primary_ok else ("FALLBACK_ACTIVE" if fell_back else "FAIL")
        print(f"[{status}] root={root}  fell_back={fell_back}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
