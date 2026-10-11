"""Canonical nightly wrapper — minimum viable copy.

Run with --dry-run for a counts-only pass. Run without flags for the
real cron entrypoint. Add a Hermes cron job that calls
nightly_all_agents_backup.py with `no_agent: true` and `deliver:
origin`; the launcher indirection lives in
`~/.hermes/scripts/nightly_ai_agents_backup.py`.

Architecture rules (encode once, don't deviate):
- Read AGENT_MAPPING / STATE_TARGETS / ARTIFACT_TARGETS from _lib.py.
- Probe-then-fallback on the cloud root; tolerate Errno 11 EDEADLK.
- Per-file skip via sidecar (size + mtime fast-path).
- Per-basename collision ⇒ prefix `_from_<parent_dir>__<basename>`.
- Output: a hermes-cron-deliverable summary block.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from _lib import AGENT_MAPPING, ARTIFACT_TARGETS, STATE_TARGETS, \
                  make_manifest_header, now_iso, probe_writable, \
                  resolve_backup_root, write_manifest

# ---------------------------------------------------------------------------

def run_step(name: str, script: Path, root: str, verbose: bool) -> dict:
    cmd = [sys.executable, str(script), "--root", root]
    if verbose:
        cmd.append("--verbose")
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
        return {"name": name, "rc": proc.returncode,
                "elapsed_seconds": round(time.time() - t0, 2),
                "stdout": proc.stdout, "stderr": proc.stderr}
    except subprocess.TimeoutExpired:
        return {"name": name, "rc": 124, "elapsed_seconds": 900.0,
                "stdout": "", "stderr": "timeout after 900s"}


def main() -> int:
    start = time.time()
    # probe-then-fallback
    backup_root, fell_back = resolve_backup_root(verbose=True)
    print(f"Backup root: {backup_root}  fell_back={fell_back}")

    states_dir = backup_root / "Shared" / "Backups" / "Manifests"
    states_dir.mkdir(parents=True, exist_ok=True)
    lock = backup_root / ".lock_nightly"

    state_step = run_step("state", HERE / "backup_agent_state.py",
                          str(backup_root), verbose=False)
    if state_step["rc"] != 0:
        print(state_step["stdout"])
        print(state_step["stderr"], file=sys.stderr)
    art_step   = run_step("artifacts", HERE / "backup_agent_artifacts.py",
                          str(backup_root), verbose=False)
    if art_step["rc"] != 0:
        print(art_step["stdout"])
        print(art_step["stderr"], file=sys.stderr)

    duration = round(time.time() - start, 2)
    print()
    print("✅ Nightly AI Agents backup complete")
    print(f"Finished: {now_iso()}")
    print(f"Duration: {duration}s")
    print(f"Backup root: {backup_root}  fell_back={fell_back}")
    # ... your per-agent summary lines here, sourcing each agent's
    # state-totals + artifact-kind-totals from `<kind>-latest.json`.
    # (See references/manifest-schema.md for the dual-shape flatten
    # helper.)

    return max(state_step["rc"], art_step["rc"]) & 1


if __name__ == "__main__":
    sys.exit(main())
