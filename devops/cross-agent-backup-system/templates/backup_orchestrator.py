#!/usr/bin/env python3
"""
backup_orchestrator.py — minimal orchestrator that combines state +
artifact backup in one pass with the prescribed summary block.

This is a TEMPLATE — copy it to <BACKUP>/Shared/Scripts/nightly_all_agents_backup
on your machine, edit AGENT_MAPPING in backup_lib.py, and run. See the SKILL.md
file for the full install recipe.

Purpose:
  1. Acquire a global lock so only one backup runs at a time.
  2. Run backup_agent_state.py (subprocess).
  3. Run backup_agent_artifacts.py (subprocess).
  4. Read the resulting -latest manifests and print the prescribed summary.

If you need to ADD a third step (e.g. an upload sanity-check), append another
`run_step(...)` between #2 and #3.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from contextlib import suppress
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from backup_lib import file_lock, now_iso, resolve_backup_root


def run_step(name, script: Path, root: str, verbose: bool) -> dict:
    cmd = [sys.executable, str(script), "--root", root]
    if verbose:
        cmd.append("--verbose")
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
        return {
            "name": name, "rc": proc.returncode,
            "elapsed_seconds": round(time.time() - t0, 2),
            "stdout_tail": proc.stdout[-2000:],
            "stderr_tail": proc.stderr[-2000:] if proc.stderr else "",
        }
    except subprocess.TimeoutExpired:
        return {"name": name, "rc": 124, "elapsed_seconds": 900.0,
                "stdout_tail": "", "stderr_tail": "timeout after 900s"}


def summarize_manifest(path: Path) -> dict:
    """Read the latest manifest. Handles BOTH:
      state     → per_agent[agent].totals  (flat)
      artifacts → per_agent[agent][kind].totals  (nested per destination kind)
    """
    try:
        with path.open() as f:
            m = json.load(f)
        out = {"manifest_path": str(path)}
        totals = m.get("totals", {})
        out["totals"] = {
            "copied": totals.get("files_copied", 0),
            "skipped": totals.get("files_skipped", 0),
            "size": totals.get("bytes_copied", 0),
            "errors": totals.get("errors", 0),
        }
        agg = {}
        for agent, sub in m.get("per_agent", {}).items():
            cell = {"copied": 0, "skipped": 0, "size": 0, "errors": 0}
            if isinstance(sub, dict):
                for k, v in sub.items():
                    if isinstance(v, dict) and isinstance(v.get("totals"), dict):
                        t = v["totals"]
                        for key in cell:
                            cell[key] += t.get(key, 0)
                    elif k == "totals" and isinstance(v, dict):
                        for key in cell:
                            cell[key] += v.get(key, 0)
            agg[agent] = cell
        out["per_agent"] = agg
        return out
    except Exception as e:
        return {"manifest_path": str(path), "error": str(e)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=str, default=None,
                    help="Override the resolved backup root (for testing).")
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args()

    start = time.time()
    if args.root:
        backup_root = Path(args.root)
        backup_root.mkdir(parents=True, exist_ok=True)
        fell_back = False
    else:
        backup_root, fell_back = resolve_backup_root(verbose=True)
    print(f"Backup root: {backup_root}  fell_back={fell_back}")

    manifests_dir = backup_root / "Shared" / "Backups" / "Manifests"
    manifests_dir.mkdir(parents=True, exist_ok=True)
    lock_path = backup_root / ".lock_nightly"

    state_script = HERE / "backup_agent_state.py"
    art_script = HERE / "backup_agent_artifacts.py"

    with file_lock(lock_path, blocking=False):
        print(f">> state: {state_script.name}")
        state_step = run_step("state", state_script, str(backup_root), args.verbose)
        print(state_step.get("stdout_tail", ""))
        if state_step.get("stderr_tail"):
            print(f"[state-stderr]\n{state_step['stderr_tail']}", file=sys.stderr)
        latest_state = manifests_dir / "state-latest.json"
        state_summary = summarize_manifest(latest_state) if latest_state.exists() else {}

        print(f">> artifacts: {art_script.name}")
        art_step = run_step("artifacts", art_script, str(backup_root), args.verbose)
        print(art_step.get("stdout_tail", ""))
        if art_step.get("stderr_tail"):
            print(f"[artifacts-stderr]\n{art_step['stderr_tail']}", file=sys.stderr)
        latest_art = manifests_dir / "artifacts-latest.json"
        art_summary = summarize_manifest(latest_art) if latest_art.exists() else {}

    duration = round(time.time() - start, 2)
    n = lambda s, k: (s.get("totals", {}) or {}).get(k, 0) if isinstance(s, dict) else 0
    pa = lambda s, agent: (s.get("per_agent", {}) or {}).get(agent, {}) if isinstance(s, dict) else {}

    print()
    print("✅ Nightly AI Agents backup complete")
    print(f"Finished: {now_iso()}")
    print(f"Duration: {duration}s")
    print(f"Backup root: {backup_root}  fell_back={fell_back}")
    print(f"State: copied {n(state_summary, 'copied')}, "
          f"size {(state_summary.get('totals', {}) or {}).get('size', 0)}, "
          f"errors {n(state_summary, 'errors')}")
    print(f"Artifacts: copied {n(art_summary, 'copied')}, "
          f"skipped {n(art_summary, 'skipped')}, "
          f"size {(art_summary.get('totals', {}) or {}).get('size', 0)}, "
          f"errors {n(art_summary, 'errors')}")
    for agent in ("<agent_folder_1>", "<agent_folder_2>", "<agent_folder_3>"):
        ps = pa(state_summary, agent)
        pa_ = pa(art_summary, agent)
        sc = ps.get("copied", 0) + pa_.get("copied", 0)
        ss = ps.get("skipped", 0) + pa_.get("skipped", 0)
        sz = ps.get("size", 0) + pa_.get("size", 0)
        print(f"{agent}: copied {sc}, skipped {ss}, size {sz}")
    print(f"State manifest:   {state_summary.get('manifest_path', '<none>')}")
    print(f"Artifact manifest: {art_summary.get('manifest_path', '<none>')}")

    rc = max(state_step.get("rc", 0), art_step.get("rc", 0))
    return min(rc, 1)


if __name__ == "__main__":
    with suppress(KeyboardInterrupt):
        sys.exit(main())
