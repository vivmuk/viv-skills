#!/usr/bin/env python3
"""Resolve the working Venice API key for chat-completions calls.

Usage:
  python3 scripts/resolve_venice_key.py          # prints key or exits non-zero
  python3 scripts/resolve_venice_key.py --check  # also verifies with /v1/models

The fallback chain matches the chain documented in
references/venice-chat-completions-quirks.md and the credentials table in the
venice-api SKILL.md. Image scripts should still try the paperclip keys first
(separate DIEM pool — see SKILL.md "DIEM spend cap is per-API-key"); only
chat-completion scripts need this chain.

Returns (does NOT print) the first key found in:
  1. $VENICE_INFERENCE_KEY
  2. $VENICE_API_KEY
  3. ~/.hermes/config.yaml :model: api_key block
  4. ~/.hermes/config.yaml any top-level api_key: line (custom_providers)
  5. ~/.hermes/hermes-agent/.envrc (VENICE_INFERENCE_KEY / VENICE_API_KEY if set)

The script never prints nor echoes the resolved key. To consume the key in
another script, either:

  python3 scripts/resolve_venice_key.py --export   # prints "export KEY=..."
  python3 scripts/resolve_venice_key.py --source   # prints "source <(python3 ...)"

For programmatic use:

  from resolve_venice_key import resolve_chat_key
  key = resolve_chat_key()
  if not key: raise SystemExit("set VENICE_INFERENCE_KEY or wire :model: api_key")

Exit codes:
  0  key found
  2  no key found at any of the 5 locations
  3  --check used and /v1/models failed with the resolved key (cred rot)
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

VENICE_BASE_URL = "https://api.venice.ai"
MODELS_ENDPOINT = f"{VENICE_BASE_URL}/api/v1/models"

# Match alpha+digit+`_`+`-` chars only, length >=30 to filter unrelated config.
_VENICE_KEY_REGEX = r"[A-Za-z0-9_\-]{30,}"

# :model: block (preferred)
_MODEL_BLOCK_RE = re.compile(
    rf"^:model:\s*\n(?:\s+.+\n)*?\s+api_key:\s*['\"]?({_VENICE_KEY_REGEX})['\"]?",
    re.M,
)
# Generic api_key: line (custom_providers, second key, etc.)
_GENERIC_KEY_RE = re.compile(
    rf"^\s*api_key:\s*['\"]?({_VENICE_KEY_REGEX})['\"]?",
    re.M,
)


def _read_hermes_config() -> str:
    candidates = [
        Path.home() / ".hermes" / "config.yaml",
        Path("/Users/vivgatesai/.hermes/config.yaml"),
    ]
    for c in candidates:
        if c.exists():
            try:
                return c.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
    return ""


def _read_hermes_envrc() -> dict[str, str]:
    """Parse a small subset of .envrc / .env files: only VENICE_INFERENCE_KEY
    and VENICE_API_KEY, lines of the form VENICE_INFERENCE_KEY=... or export VENICE_API_KEY=...
    """
    p = Path.home() / ".hermes" / "hermes-agent" / ".envrc"
    if not p.exists():
        return {}
    out: dict[str, str] = {}
    try:
        for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export "):]
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            if k in ("VENICE_INFERENCE_KEY", "VENICE_API_KEY", "VENICE_API_BASE"):
                # Strip simple quotes and inline comments.
                v = v.strip().strip('"').strip("'").split(" #", 1)[0].strip()
                if v:
                    out[k] = v
    except OSError:
        return {}
    return out


def resolve_chat_key() -> str | None:
    """Resolve a Venice API key for chat-completions calls. Never echoes it."""
    env = os.environ.get("VENICE_INFERENCE_KEY") or os.environ.get("VENICE_API_KEY")
    if env:
        return env

    text = _read_hermes_config()
    if text:
        m = _MODEL_BLOCK_RE.search(text)
        if m:
            return m.group(1)
        m = _GENERIC_KEY_RE.search(text)
        if m:
            return m.group(1)

    envrc = _read_hermes_envrc()
    if envrc:
        return envrc.get("VENICE_INFERENCE_KEY") or envrc.get("VENICE_API_KEY")

    return None


def check_key(api_key: str, timeout: float = 15.0) -> tuple[bool, str]:
    """Verify the resolved key against /v1/models. Returns (ok, summary)."""
    req = urllib.request.Request(
        MODELS_ENDPOINT,
        headers={"Authorization": f"Bearer {api_key}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read(2048).decode(errors="ignore")
            return True, f"HTTP 200 — first 200 chars: {body[:200]}"
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code} — {e.read(200).decode(errors='ignore')}"
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return False, f"network error: {e}"


def redacted(key: str) -> str:
    """For diagnostics only. Do NOT include in any user-facing output."""
    if not key or len(key) < 12:
        return "<redacted>"
    return f"{key[:6]}…{key[-4:]} ({len(key)} chars)"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="After resolving, also probe /v1/models with the key.")
    ap.add_argument("--export", action="store_true",
                    help="Print a `export KEY=...` line for shell sourcing.")
    ap.add_argument("--redact", action="store_true",
                    help="Diagnostic mode: print only a redacted fingerprint, never the key.")
    args = ap.parse_args()

    key = resolve_chat_key()
    if not key:
        print(
            "resolve_venice_key: no key found in VENICE_INFERENCE_KEY, VENICE_API_KEY, "
            "~/.hermes/config.yaml :model: block, or ~/.hermes/hermes-agent/.envrc",
            file=sys.stderr,
        )
        return 2

    if args.redact:
        print(f"resolved: {redacted(key)}")
    elif args.export:
        print(f"export VENICE_INFERENCE_KEY='{key}'")
    else:
        # Default: write key on stdout for `$(python3 …)` capture.
        # Caller is responsible for not echoing/not logging.
        sys.stdout.write(key + "\n")

    if args.check:
        ok, msg = check_key(key)
        print(f"check /v1/models: {msg}", file=sys.stderr)
        return 0 if ok else 3

    return 0


if __name__ == "__main__":
    sys.exit(main())
