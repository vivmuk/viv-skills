#!/usr/bin/env python3
"""
Paperclip Tool-Runner Adapter (template)

Invoked by Paperclip for leaf agents that should run a specific script
on heartbeat. No LLM involved. Reads `PAPERCLIP_TASK` to determine the
script, or falls back to `TOOL_DEFAULT_SCRIPT`.

PAPERCLIP_TASK format (single line):
    <script_name>

Or with params (two lines):
    <script_name>
    <json params, optional>

Environment variables (per-agent):
  TOOL_SCRIPTS_DIR    - directory holding the scripts (default: ~/.paperclip/workspaces/<company>)
  TOOL_DEFAULT_SCRIPT - if PAPERCLIP_TASK is empty, run this script
  TOOL_DEFAULT_PARAMS - JSON string of default params (default: "{}")
  TOOL_TIMEOUT        - seconds before killing the script (default: 300)
"""
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime

SCRIPTS_DIR = os.environ.get(
    "TOOL_SCRIPTS_DIR",
    os.path.expanduser("~/.paperclip/workspaces/aipharmaxchange"),
)
DEFAULT_SCRIPT = os.environ.get("TOOL_DEFAULT_SCRIPT", "")
DEFAULT_PARAMS = os.environ.get("TOOL_DEFAULT_PARAMS", "{}")
TASK = os.environ.get("PAPERCLIP_TASK", "")
TIMEOUT = int(os.environ.get("TOOL_TIMEOUT", "300"))


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[tool-runner {ts}] {msg}", file=sys.stderr, flush=True)


def resolve_script(name):
    if not name:
        return None
    if os.path.isabs(name) and os.path.exists(name):
        return name
    candidate = os.path.join(SCRIPTS_DIR, name)
    if os.path.exists(candidate):
        return candidate
    if os.path.exists(candidate + ".py"):
        return candidate + ".py"
    return None


def parse_task(raw):
    raw = (raw or "").strip()
    if not raw:
        return DEFAULT_SCRIPT, json.loads(DEFAULT_PARAMS)
    parts = raw.split("\n", 1)
    name = parts[0].strip()
    if len(parts) > 1 and parts[1].strip():
        try:
            params = json.loads(parts[1])
        except json.JSONDecodeError:
            params = {"raw_args": parts[1].strip()}
    else:
        params = {}
    return name, params


def main():
    log(f"start: task={TASK[:80]!r}")
    name, params = parse_task(TASK)
    if not name:
        print("ERROR: no script specified (set TOOL_DEFAULT_SCRIPT or pass PAPERCLIP_TASK)", file=sys.stderr)
        sys.exit(2)

    script_path = resolve_script(name)
    if not script_path:
        print(f"ERROR: script not found: {name} (looked in {SCRIPTS_DIR})", file=sys.stderr)
        sys.exit(3)

    cmd = [sys.executable, script_path]
    for k, v in params.items():
        cmd += [f"--{k}", str(v)]

    log(f"exec: {' '.join(cmd)}")
    start = time.time()
    try:
        result = subprocess.run(
            cmd,
            cwd=SCRIPTS_DIR,
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        log(f"TIMEOUT after {TIMEOUT}s")
        print(f"Script {name} timed out after {TIMEOUT}s", file=sys.stderr)
        sys.exit(4)
    elapsed = time.time() - start
    log(f"done in {elapsed:.1f}s exit={result.returncode} stdout={len(result.stdout)} chars stderr={len(result.stderr)} chars")

    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
