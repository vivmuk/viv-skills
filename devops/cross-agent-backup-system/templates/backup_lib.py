#!/usr/bin/env python3
"""
backup_lib.py — canonical library for the cross-agent nightly backup system.

Keep this file small, stdlib-only (Python 3.9+), and `'repr forever'` (the
shape of AGENT_MAPPING, ARTIFACT_EXTENSIONS, SECRET_KEY_PATTERNS is part of
the public surface — don't churn it for cosmetic reasons).

To roll-out on a new machine:

1. Copy `_lib.py`, `backup_agent_state.py`, `backup_agent_artifacts.py`,
   `nightly_all_agents_backup.py` into `<BACKUP>/Shared/Scripts/`.
2. Drop the Hermes-side launcher at `~/.hermes/scripts/<basename>.py`.
3. Set AGENT_MAPPING for the running agents on that box.
4. Run a `--dry-run` first.
5. Then a real run, then a re-run to verify skip detection.

The dashed numbered comments show which block of SKILL.md to read first.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Tuple

# -- (1) Primary + fallback roots. See SKILL.md "Critical patterns" §2. --
PRIMARY_BACKUP_ROOT = "/Users/<USERNAME>/OneDrive/AI Agents"
LOCAL_FALLBACK_ROOT = "/Users/<USERNAME>/output/AI Agents"

# -- (2) Agent mapping. Edit this in ONE place. See SKILL.md "agent-folder-naming-conventions". --
AGENT_MAPPING = {
    "<agent_folder_1>": {
        "agent_label": "<running agent name> — short description",
        "kind": "state",                       # or "mixed"
        "dest_subdir": "Backups",
        "sources": [
            "~/.agent/config.yaml",
            # add paths you want backed up; secrets are excluded by name
        ],
        "exclude_globs": [".env", "auth.json", "*.key", "*.pem", ".secret*"],
    },
    # Add more per the running agents on your machine
}

# -- (3) Allowlist for artifacts. Solid portable formats only. --
ARTIFACT_EXTENSIONS = {
    ".md", ".txt", ".json", ".jsonl", ".yaml", ".yml", ".toml",
    ".csv", ".tsv", ".pdf", ".html", ".htm", ".pptx", ".docx", ".xlsx",
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg",
    ".mp4", ".mov", ".webm", ".mp3", ".wav", ".ogg", ".m4a",
    ".zip", ".py", ".ipynb",
    ".js", ".jsx", ".ts", ".tsx", ".css", ".scss",
    ".sql", ".xml",
}

# -- (4) Always excluded (caches, transient locks, env, git). --
GLOBAL_EXCLUDE_NAMES = {
    ".env", ".envrc", "auth-profiles.json",
    ".git", ".hg", ".svn", "node_modules",
    "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache",
    ".venv", "venv", "env",
    ".DS_Store", ".Trash", "Thumbs.db",
    ".jobs.lock", ".tick.lock", ".lock", ".write_probe",
}
GLOBAL_EXCLUDE_GLOBS = [
    ".git/**", "node_modules/**", "__pycache__/**",
    ".venv/**", "venv/**", "env/**",
    "*.log", "*.tmp", "*.swp", "*.bak",
    "**/.env", "**/.envrc", "**/auth-profiles.json",
    "**/*.lock", "**/.tick.lock", "**/.jobs.lock",
]

# -- (5) Patterns that, if seen as VALUES in JSON/YAML/.env, get "<REDACTED>". --
SECRET_KEY_PATTERNS = [
    "key", "secret", "password", "passwd", "token", "apikey", "api_key",
    "access_token", "auth", "credential", "cred", "private_key",
    "venice_api_key", "openai_api_key", "minimax_api_key",
    "anthropic_api_key", "hf_token", "gh_token", "github_token",
]

# ---------------------------------------------------------------------------
# (A) Probe + resolve
# ---------------------------------------------------------------------------

def probe_writable(root: Path, probe_name: str = ".write_probe") -> Tuple[bool, str]:
    """EdeADLK-tolerant writability probe. See SKILL.md Critical patterns §1."""
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
        return False, f"write_open_failed: errno={e.errno} {e.strerror}"


def resolve_backup_root(verbose: bool = False) -> Tuple[Path, bool]:
    """Return (root, fell_back). See SKILL.md Critical patterns §2."""
    primary = Path(PRIMARY_BACKUP_ROOT)
    ok, why = probe_writable(primary)
    if ok:
        if verbose:
            print(f"[backup-root] PRIMARY OK: {primary}", file=sys.stderr)
        return primary, False
    if verbose:
        print(f"[backup-root] PRIMARY unreachable ({why}); "
              f"using FALLBACK: {LOCAL_FALLBACK_ROOT}", file=sys.stderr)
    fallback = Path(LOCAL_FALLBACK_ROOT)
    fallback.mkdir(parents=True, exist_ok=True)
    ok2, why2 = probe_writable(fallback)
    if not ok2:
        raise RuntimeError(f"PRIMARY unreachable ({why}) "
                           f"AND FALLBACK unreachable ({why2})")
    return fallback, True


# ---------------------------------------------------------------------------
# (B) File lock — atomic O_CREAT|O_EXCL with stale-detection
# ---------------------------------------------------------------------------

@contextmanager
def file_lock(lock_path: Path, *, blocking: bool = False,
              stale_after: int = 6 * 3600):
    """Cross-process advisory lock with stale-lock detection."""
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps({
        "pid": os.getpid(),
        "host": os.uname().nodename,
        "started_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
    })
    try:
        fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.write(fd, payload.encode("utf-8"))
        os.close(fd)
    except FileExistsError:
        try:
            age = time.time() - lock_path.stat().st_mtime
        except OSError:
            age = 0
        if age > stale_after:
            lock_path.unlink()
            try:
                fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                os.write(fd, payload.encode("utf-8"))
                os.close(fd)
            except FileExistsError as e:
                raise RuntimeError(
                    f"lock contended after stale-replace: {lock_path}") from e
        elif not blocking:
            raise RuntimeError(f"backup already running (lock held): {lock_path}")
        else:
            while True:
                time.sleep(0.5)
                try:
                    fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                    os.write(fd, payload.encode("utf-8"))
                    os.close(fd)
                    break
                except FileExistsError:
                    continue
    try:
        yield
    finally:
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


# ---------------------------------------------------------------------------
# (C) Skip detection via size+mtime+sha256 sidecar (Critical patterns §3, §5)
# ---------------------------------------------------------------------------

def sha256_file(path: Path, chunk: int = 65536) -> str:
    import hashlib
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def copy_with_skip_or_redact(
    src: Path, dst: Path, *, redact: bool,
) -> Tuple[str, int]:
    """Returns (status ∈ {copied, copied_redacted, skipped, error}, size)."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        src_stat = src.stat()
    except OSError:
        return "error", 0
    size, mtime = src_stat.st_size, int(src_stat.st_mtime)

    sidecar = dst.with_suffix(dst.suffix + ".sha256")
    if dst.exists() and sidecar.exists():
        try:
            meta = json.loads(sidecar.read_text())
            if meta.get("size") == size and meta.get("mtime") == mtime:
                return "skipped", size
        except (json.JSONDecodeError, OSError):
            pass

    try:
        if redact and dst.suffix.lower() in {".json", ".yaml", ".yml", ".toml", ".env", ".txt", ".md"}:
            raw = src.read_text(errors="replace")
            redacted = redact_secrets_in_text(raw)
            tmp = dst.with_suffix(dst.suffix + ".tmp")
            tmp.write_text(redacted)
            os.replace(tmp, dst)
            status = "copied_redacted"
        else:
            shutil.copy2(src, dst)
            status = "copied"
    except OSError:
        return "error", 0

    try:
        sha = sha256_file(dst)
    except OSError:
        sha = None
    sidecar.write_text(json.dumps({
        "size": size, "mtime": mtime, "sha256": sha,
        "src": str(src),                                # <-- key for collision detection
        "copied_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
    }))
    return status, size


def redact_secrets_in_text(text: str) -> str:
    """Replace values aligned to SECRET_KEY_PATTERNS with '<REDACTED>'.
    Best-effort; not a guarantee."""
    import re
    keys = "|".join(sorted(SECRET_KEY_PATTERNS, key=len, reverse=True))
    patterns = [
        re.compile(r'("(' + keys + r')"\s*:\s*)"[^"]*"', re.IGNORECASE),
        re.compile(r'(^(\s*)(' + keys + r')\s*:\s*)"[^"]*"', re.IGNORECASE | re.MULTILINE),
        re.compile(r'(^(\s*)((?:[A-Z][A-Z0-9_]*_)?(' + keys + r'))\s*=\s*)"[^"]*"',
                   re.IGNORECASE | re.MULTILINE),
        re.compile(r'(^(\s*)((?:[A-Z][A-Z0-9_]*_)?(' + keys + r'))\s*=\s*)[^\s"\']+',
                   re.IGNORECASE | re.MULTILINE),
    ]
    for pat in patterns:
        text = pat.sub(r'\1"<REDACTED>"', text)
    return text


# ---------------------------------------------------------------------------
# (D) Discovery helpers
# ---------------------------------------------------------------------------

def looks_like_secrets(path: Path) -> bool:
    n = path.name.lower()
    return n in {".env", ".envrc", "auth.json", "auth-profiles.json"} or \
        any(s in n for s in ("secret", "credential", ".key", ".pem"))


def is_artifact(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in ARTIFACT_EXTENSIONS


def discover_state_files(sources: Iterable[str]) -> list:
    """Expand source paths, return every non-excluded file under them."""
    out = []
    for src in sources:
        p = Path(os.path.expanduser(src))
        if not p.exists():
            continue
        if p.is_file():
            out.append(p)
        else:
            for child in p.rglob("*"):
                if child.is_file():
                    out.append(child)
    return sorted(set(out))


def discover_artifact_files(sources: Iterable[str]) -> list:
    """Same as discover_state_files but applies the allowlist + global excludes."""
    out = []
    for src in sources:
        p = Path(os.path.expanduser(src))
        if not p.exists():
            continue
        if p.is_file():
            if is_artifact(p):
                out.append(p)
        else:
            for child in p.rglob("*"):
                if is_artifact(child):
                    out.append(child)
    return sorted(set(out))


# ---------------------------------------------------------------------------
# (E) Manifest emission (Critical patterns §8)
# ---------------------------------------------------------------------------

def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def make_manifest_header(kind: str, backup_root: Path) -> dict:
    return {
        "kind": kind,
        "agent": "<combined-agent-label>",      # e.g. "Agni (Hermes) + Paridhi (OpenClaw)"
        "machine": os.uname().nodename,
        "user": os.environ.get("USER", "?"),
        "backup_root": str(backup_root),
        "fell_back": False,
        "started_at": now_iso(),
        "completed_at": None,
        "duration_seconds": None,
        "totals": {
            "files_copied": 0, "files_skipped": 0,
            "files_redacted": 0, "bytes_copied": 0, "errors": 0,
        },
        "per_agent": {},
        "files": [],
        "errors": [],
    }


def write_manifest(manifest: dict, root: Path, kind: str) -> Path:
    manifests_dir = root / "Shared" / "Backups" / "Manifests"
    manifests_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    out = manifests_dir / f"{kind}-{stamp}.json"
    out.write_text(json.dumps(manifest, indent=2, default=str))
    latest = manifests_dir / f"{kind}-latest.json"
    try:
        if latest.is_symlink() or latest.exists():
            latest.unlink()
        os.symlink(out.name, str(latest))
    except OSError:
        shutil.copy2(out, latest)  # symlinks unsupported on some FS
    return out
