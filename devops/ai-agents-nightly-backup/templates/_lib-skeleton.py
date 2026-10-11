"""
Skeleton _lib.py for the AI Agents nightly backup pipeline.

This is the minimum a working library needs. Drop in via:
    cp templates/_lib-skeleton.py <backup_root>/Shared/Scripts/_lib.py

Then edit:
  - PRIMARY_BACKUP_ROOT, LOCAL_FALLBACK_ROOT
  - AGENT_MAPPING (see templates/AGENT_MAPPING-py-constants.py-snippet.py)
  - ARTIFACT_EXTENSIONS (already complete)
  - GLOBAL_EXCLUDE_GLOBS (already complete; add per-machine)
"""
from __future__ import annotations

import errno
import hashlib
import json
import os
import shutil
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

PRIMARY_BACKUP_ROOT = "~/OneDrive/AI Agents"
LOCAL_FALLBACK_ROOT = "~/output/AI Agents"

# === EDIT THIS BLOCK ON FIRST INSTALL ===
AGENT_MAPPING: dict[str, dict] = {}  # See templates/AGENT_MAPPING-... for shape

ARTIFACT_EXTENSIONS = {
    ".md", ".txt", ".json", ".jsonl", ".yaml", ".yml", ".toml",
    ".csv", ".tsv", ".pdf", ".html", ".htm", ".pptx", ".docx", ".xlsx",
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg",
    ".mp4", ".mov", ".webm", ".mp3", ".wav", ".ogg", ".m4a",
    ".zip", ".py", ".ipynb",
    ".js", ".jsx", ".ts", ".tsx", ".css", ".scss",
    ".sql", ".xml",
}

GLOBAL_EXCLUDE_NAMES = {
    ".env", ".envrc", "auth-profiles.json",
    ".git", ".hg", ".svn", "node_modules",
    "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache",
    ".venv", "venv", "env",
    ".DS_Store", ".Trash", "Thumbs.db",
    # transient runtime locks (we use these too)
    ".jobs.lock", ".tick.lock", ".lock", ".lock_nightly",
    ".lock_state", ".lock_artifacts", ".write_probe",
}
GLOBAL_EXCLUDE_GLOBS = [
    ".git/**", "node_modules/**", "__pycache__/**",
    ".venv/**", "venv/**", "env/**",
    "*.log", "*.tmp", "*.swp", "*.bak",
    "**/.env", "**/.envrc", "**/auth-profiles.json",
    "browser-state/**", ".openclaw/browser/**",
    "**/*.lock", "**/.tick.lock", "**/.jobs.lock",
]
SECRET_KEY_PATTERNS = [
    "key", "secret", "password", "passwd", "token", "apikey", "api_key",
    "access_token", "auth", "credential", "cred", "private_key",
    "venice_api_key", "openai_api_key", "minimax_api_key",
    "anthropic_api_key", "hf_token", "gh_token", "github_token",
]


def expand_home(p):
    return Path(os.path.expanduser(p))


def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def probe_writable(root, probe_name=".write_probe"):
    """Atomic mkdir+write+unlink that distinguishes EDEADLK from real errors."""
    try:
        root.mkdir(parents=True, exist_ok=True)
        probe = root / probe_name
        try:
            probe.write_text("ok")
            probe.unlink()
            return True, "ok"
        except OSError as e:
            return False, f"write_failed: errno={e.errno} ({errno.errorcode.get(e.errno, '?')}) {e.strerror}"
    except OSError as e:
        return False, f"mkdir_failed: errno={e.errno} ({errno.errorcode.get(e.errno, '?')}) {e.strerror}"


def resolve_backup_root(verbose=False):
    primary = expand_home(PRIMARY_BACKUP_ROOT)
    primary_ok, primary_reason = probe_writable(primary)
    if primary_ok:
        if verbose:
            print(f"[backup-root] PRIMARY OK: {primary}", file=sys.stderr)
        return primary, False
    fallback = expand_home(LOCAL_FALLBACK_ROOT)
    fallback.mkdir(parents=True, exist_ok=True)
    fallback_ok, fb_reason = probe_writable(fallback)
    if not fallback_ok:
        raise RuntimeError(
            f"PRIMARY unreachable ({primary_reason}) AND FALLBACK unreachable ({fb_reason})"
        )
    if verbose:
        print(
            f"[backup-root] PRIMARY unreachable ({primary_reason}); "
            f"using FALLBACK: {fallback}",
            file=sys.stderr,
        )
    return fallback, True


@contextmanager
def file_lock(lock_path, *, blocking=False, stale_after=6 * 3600):
    """Atomic O_CREAT|O_EXCL advisory lock with stale detection."""
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps({
        "pid": os.getpid(),
        "host": os.uname().nodename,
        "started_at": now_iso(),
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
                raise RuntimeError(f"lock contended after stale-replace: {lock_path}") from e
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


def is_artifact(path):
    return path.is_file() and path.suffix.lower() in ARTIFACT_EXTENSIONS


def is_excluded(rel_path):
    name = rel_path.rsplit("/", 1)[-1]
    if name in GLOBAL_EXCLUDE_NAMES:
        return True
    import fnmatch
    for pat in GLOBAL_EXCLUDE_GLOBS:
        if pat.endswith("/**"):
            seg = pat[:-3]
            if seg in rel_path.split("/") or rel_path.startswith(seg + "/"):
                return True
        elif pat.startswith("**/"):
            tail = pat[3:]
            if rel_path.endswith(tail) or ("/" + tail) in rel_path:
                return True
        elif "*" in pat and fnmatch.fnmatch(name, pat):
            return True
    return False


def looks_like_secrets(path):
    n = path.name.lower()
    return n in (".env", ".envrc", "auth.json", "auth-profiles.json") or any(
        s in n for s in ("secret", "credential", ".key", ".pem")
    )


def redact_secrets_in_text(text):
    """Best-effort regex redaction for JSON / YAML / .env / .md text."""
    import re
    keys = "|".join(sorted(SECRET_KEY_PATTERNS, key=len, reverse=True))
    PATTERNS = [
        re.compile(r'("(' + keys + r')"\s*:\s*)"[^"]*"', re.IGNORECASE),
        re.compile(r'(^(\s*)(' + keys + r')\s*:\s*)"[^"]*"', re.IGNORECASE | re.MULTILINE),
        re.compile(r'(^(\s*)((?:[A-Z][A-Z0-9_]*_)?(' + keys + r'))\s*=\s*)"[^"]*"', re.IGNORECASE | re.MULTILINE),
        re.compile(r'(^(\s*)((?:[A-Z][A-Z0-9_]*_)?(' + keys + r'))\s*=\s*)[^\s"\']+', re.IGNORECASE | re.MULTILINE),
    ]
    for p in PATTERNS:
        text = p.sub(r'\1"<REDACTED>"', text)
    return text


def redact_secrets_in_json(obj):
    if isinstance(obj, dict):
        return {
            k: ("<REDACTED>" if any(s in k.lower() for s in SECRET_KEY_PATTERNS) else redact_secrets_in_json(v))
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [redact_secrets_in_json(x) for x in obj]
    return obj


def sha256_file(path, chunk=65536):
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def copy_with_skip_or_redact(src, dst, *, redact):
    """Incremental copy with sidecar-based skip and optional redaction."""
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
            # Try structural JSON redaction first; fall back to regex text.
            try:
                obj = json.loads(raw)
                redacted = json.dumps(redact_secrets_in_json(obj), indent=2)
            except (json.JSONDecodeError, ValueError):
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
    sidecar.write_text(json.dumps({"size": size, "mtime": mtime, "sha256": sha, "src": str(src), "copied_at": now_iso()}))
    return status, size


def make_manifest_header(kind, backup_root):
    return {
        "kind": kind,
        "agent": "Agni (Hermes) + Paridhi (OpenClaw)",  # EDIT
        "machine": os.uname().nodename,
        "user": os.environ.get("USER", "?"),
        "backup_root": str(backup_root),
        "started_at": now_iso(),
        "completed_at": None,
        "duration_seconds": None,
        "totals": {"files_copied": 0, "files_skipped": 0, "files_redacted": 0, "bytes_copied": 0, "errors": 0},
        "per_agent": {},
        "files": [],
        "errors": [],
    }


def write_manifest(manifest, root, kind):
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
        shutil.copy2(out, latest)
    return out


def discover_state_files(sources):
    out = []
    for src in sources:
        p = expand_home(src)
        if not p.exists():
            continue
        if p.is_file():
            if not is_excluded(str(p)):
                out.append(p)
        else:
            for child in p.rglob("*"):
                if child.is_file() and not is_excluded(str(child)):
                    out.append(child)
    return sorted(set(out))


def discover_artifact_files(sources):
    out = []
    for src in sources:
        p = expand_home(src)
        if not p.exists():
            continue
        if p.is_file():
            if is_artifact(p) and not is_excluded(str(p)):
                out.append(p)
        else:
            for child in p.rglob("*"):
                if child.is_file() and is_artifact(child) and not is_excluded(str(child)):
                    out.append(child)
    return sorted(set(out))
