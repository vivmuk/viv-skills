"""
patch-venice-plugin.py

Idempotent plugin-manifest patcher for adding/updating a Venice model
entry in the OpenClaw bundled plugin manifest.

USAGE
    cp templates/patch-venice-plugin.py /tmp/patch.py
    # Edit NEW_ENTRY to match the model you want to register, then:
    python3 /tmp/patch.py

AFTERWARDS
    rm -rf /var/folders/*/T/node-compile-cache/openclaw /private/tmp/openclaw
    pkill -f openclaw
    openclaw gateway install --force
    openclaw gateway start

WHY THIS EXISTS
    The OpenClaw bundled plugin catalog (models.json / catalog.json) is
    ephemeral — it's rebuilt from openclaw.plugin.json on every agent
    invocation. Editing those files directly loses your changes.

    The persistent source is openclaw.plugin.json under the bundled
    extensions directory. Edit IT, not the catalog files.

    Reasoning-effort plumbing for Venice goes through
    `compat.supportsReasoningEffort` + `compat.thinkingLevelMap` in
    the entry. Without those, reasoning silently doesn't fire.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# EDIT THIS for the model you're registering.
# The thinkingLevelMap below is Venice-specific (4 valid values:
# none/low/medium/high). "max" and "xhigh" are NOT valid Venice values
# — we collapse them to "high".
NEW_ENTRY = {
    "id": "REPLACE-ME-MODEL-ID",  # e.g. "xiaomi-mimo-v2-5"
    "name": "REPLACE-ME Display Name",
    "reasoning": True,
    "input": ["text", "image"],
    "contextWindow": 1000000,
    "maxTokens": 65536,
    "compat": {
        "supportsUsageInStreaming": False,
        "supportsReasoningEffort": True,
        "thinkingLevelMap": {
            "off":     "none",
            "minimal": "low",
            "low":     "low",
            "medium":  "medium",
            "high":    "high",
            "xhigh":   "high",
            "max":     "high",
        },
    },
}

PLUGIN_PATH = Path(
    "/Users/vivgatesai/.hermes/node/lib/node_modules/openclaw/"
    "dist/extensions/venice/openclaw.plugin.json"
)


def main() -> int:
    if NEW_ENTRY["id"] == "REPLACE-ME-MODEL-ID":
        print("ERROR: edit NEW_ENTRY first (model id + name)", file=sys.stderr)
        return 2

    if not PLUGIN_PATH.exists():
        print(f"ERROR: plugin manifest not found at {PLUGIN_PATH}", file=sys.stderr)
        return 2

    with PLUGIN_PATH.open() as f:
        d = json.load(f)

    models = d["modelCatalog"]["providers"]["venice"]["models"]
    existing_idx = next(
        (i for i, m in enumerate(models) if m["id"] == NEW_ENTRY["id"]),
        -1,
    )

    if existing_idx >= 0:
        models[existing_idx] = NEW_ENTRY
        print(f"REPLACED at index {existing_idx}: {NEW_ENTRY['id']}")
    else:
        # Insert just after the LAST existing entry that shares "reasoning":
        # true, so we don't end up between a non-reasoning model and a
        # reasoning one — keeps the file visually grouped.
        last_reasoning_idx = max(
            (i for i, m in enumerate(models) if m.get("reasoning")),
            default=len(models) - 1,
        )
        models.insert(last_reasoning_idx + 1, NEW_ENTRY)
        print(f"INSERTED at index {last_reasoning_idx + 1}: {NEW_ENTRY['id']}")

    with PLUGIN_PATH.open("w") as f:
        json.dump(d, f, indent=2)
        f.write("\n")

    print(f"FINAL_MODEL_COUNT: {len(models)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
