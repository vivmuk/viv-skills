"""AGENT_MAPPING skeleton — drop into _lib.py and fill in.

The order is: state sources (→ Backups/), then one or more artifact
kinds (→ Agent-Outputs/, Research/, Projects/, etc.). The matching
entry must also exist in backup_agent_artifacts.py::ARTIFACT_TARGETS
under the same per-kind subkey.

Naming rule (READ FIRST): name the agent after whatever it identifies
as on THIS machine. Don't carry over folder names from a different
machine to use as destinations; the legacy shells stay on disk for
mirror compatibility, but the live pipeline routes into the
actually-running agent names.
"""
from __future__ import annotations

# Path roots (overridable via env var BACKUP_ROOT at script entry)
PRIMARY_BACKUP_ROOT = "/Users/YOU/OneDrive/AI Agents"
LOCAL_FALLBACK_ROOT = "/Users/YOU/output/AI Agents"

# Secret filenames — NEVER copied raw, even with redaction.
SECRET_BASENAMES = {".env", ".envrc", "auth-profiles.json"}

# Artifact extension allowlist. Tighten as you learn what you need.
ARTIFACT_EXTENSIONS = {
    ".md", ".txt", ".json", ".jsonl", ".yaml", ".yml", ".toml",
    ".csv", ".tsv", ".pdf", ".html", ".htm", ".pptx", ".docx",
    ".xlsx", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg",
    ".mp4", ".mov", ".webm", ".mp3", ".wav", ".ogg", ".m4a",
    ".zip", ".py", ".ipynb",
    ".js", ".jsx", ".ts", ".tsx", ".css", ".scss",
    ".sql", ".xml",
}

# Always excluded — caches, venvs, transient state, logs.
GLOBAL_EXCLUDE_NAMES = {
    ".env", ".envrc", "auth-profiles.json",
    ".git", ".hg", ".svn", "node_modules",
    "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache",
    ".venv", "venv", "env",
    ".DS_Store", ".Trash", "Thumbs.db",
    # transient runtime locks:
    ".jobs.lock", ".tick.lock", ".lock",
    ".lock_nightly", ".lock_state", ".lock_artifacts", ".write_probe",
}

# ---------------------------------------------------------------------------
# Per-agent mapping: ADD YOUR AGENTS HERE
# ---------------------------------------------------------------------------

AGENT_MAPPING = {
    # Replace with your actual running agents.
    # Each agent gets:
    #   sources_state    → <Agent>/Backups/
    #   sources_outputs  → <Agent>/Agent-Outputs/
    #   sources_<kind>   → <Agent>/<Kind>/   (e.g. research, projects, media)
    #
    # The end-of-line comment "→ <Agent>/<Dir>/" exists so a future
    # installer can `grep` for the exact destination path when
    # debugging.
    "<AgentName1>": {
        "agent_label": "Human-readable label",
        "kind": "mixed",                 # "state" | "mixed"
        "dest_subdir": "Backups",
        "sources_state": [
            "~/.<agent_config_dir>/config.yaml",
            "~/.<agent_config_dir>/<auth_or_registry_skipped>",
        ],
        "sources_outputs": [
            "~/.<agent_workspace_dir>/generated",
            "~/.<agent_sessions_dir>",
        ],
        # Optional thematic kinds — pair with ARTIFACT_TARGETS below.
        "sources_research": [],
        "sources_projects": [],
        "exclude_globs": [".env", "*.key", "*.pem", ".secret*"],
    },
    "<AgentName2>": {
        "agent_label": "...",
        "kind": "mixed",
        "dest_subdir": "Backups",
        "sources_state":   ["~/.<other_agent>/config.json", ...],
        "sources_outputs": ["~/.<other_agent>/workspace", "~/.<other_agent>/sessions"],
        "sources_projects": ["~/.<other_agent>/projects"],
        "exclude_globs":    [".env", "auth-profiles.json"],
    },
}

# Mirror of AGENT_MAPPING "sources_<kind>" keys. Anything listed here
# must have a matching `sources_<kind>` in AGENT_MAPPING and a
# `<Agent>/<Kind>/` destination directory created on first run.
ARTIFACT_TARGETS = {
    "<AgentName1>": {
        "outputs":  "<AgentName1>/Agent-Outputs",
        "research": "<AgentName1>/Research",
    },
    "<AgentName2>": {
        "outputs":  "<AgentName2>/Agent-Outputs",
        "projects": "<AgentName2>/Projects",
    },
}

# State targets are simpler — always <Agent>/Backups.
STATE_TARGETS = {
    "<AgentName1>": "<AgentName1>/Backups",
    "<AgentName2>": "<AgentName2>/Backups",
}
