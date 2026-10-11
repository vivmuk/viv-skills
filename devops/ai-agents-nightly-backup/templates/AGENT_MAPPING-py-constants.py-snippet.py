"""
Reference template for _lib.py::AGENT_MAPPING.

Replace the agent names + source paths with the actual agents running
on this machine. The structure below is what the rest of the pipeline
expects; do NOT rename keys.
"""
from __future__ import annotations

AGENT_MAPPING = {
    # === Agent A: <replace with your Hermes / MiniMax / Claude / Codex> ===
    "<agent_name>": {
        "agent_label": "human-readable description",
        "kind": "mixed",  # one of: "state" | "mixed"
        "dest_subdir": "Backups",

        # STATE / CONFIG files (small, redact-friendly) → <agent>/Backups/
        "sources_state": [
            "~/.hermes/config.yaml",
            "~/.hermes/auth.json",                  # keys REDACTED on write
            "~/.hermes/skills/.usage.json",         # curator telemetry only
            "~/.hermes/cron/jobs.json",             # cron REGISTRY (NOT output)
            "~/.hermes/plugins",
            "~/.hermes/mcp.json",
            "~/.hermes/curator.json",
            "~/.hermes/profiles",                   # per-profile state
            "~/.hermes/memory",
            "~/.hermes/state.db",
        ],

        # ARTIFACT outputs (large, often binary) → <agent>/Agent-Outputs/
        "sources_outputs": [
            "~/.hermes/cron/output",
            "~/.hermes/audio_cache",
            "~/.hermes/sessions",
        ],

        # Optional thematic subdir for research-style outputs.
        # If empty, Agent-Outputs is enough.
        # Rename "sources_research" to "sources_projects" for project-flavored agents.
        "sources_research": [
            "~/.hermes/profiles/*/youtube_intelligence",
            "~/.hermes/profiles/*/research",
        ],

        # Per-agent exclusions on top of the GLOBAL_EXCLUDE_GLOBS.
        "exclude_globs": [".env", "auth.json", "*.key", "*.pem", ".secret*"],
    },

    # === Agent B: <OpenClaw / Paridhi / another isolated agent> ===
    "<another_agent>": {
        "agent_label": "another-agent description",
        "kind": "mixed",
        "dest_subdir": "Backups",

        "sources_state": [
            "~/<other-runtime>/openclaw.json",
            "~/<other-runtime>/agents",            # agent configs (auth REDACTED)
            # workspace docs
        ],

        "sources_outputs": [
            "~/<other-runtime>/workspace",
            "~/<other-runtime>/media",
            "~/<other-runtime>/agents/main/sessions",
        ],

        "sources_projects": [
            "~/<other-runtime>/workspace/projects",
            "~/<other-runtime>/workspace/<project-name>",
        ],

        "exclude_globs": [
            ".env", "*.key", "*.pem", ".secret*",
            "auth-profiles.json",
            "__pycache__", ".git",
        ],
    },
}

# === Runtime checks ===
# These keys MUST also appear in STATE_TARGETS and ARTIFACT_TARGETS in the
# working scripts. If you add a new agent here, add to both:
#
#   backup_agent_state.py::STATE_TARGETS = {"<agent>": "<agent>/Backups"}
#   backup_agent_artifacts.py::ARTIFACT_TARGETS = {"<agent>": {"outputs": ..., ...}}
#
# And add the per-agent wire-up to `nightly_all_agents_backup.py`'s
# summary printer's `for agent in (..., ...)`.
