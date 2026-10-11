"""
smoke-test-reasoning-fires.py

Quick verification that the model you're using actually does reasoning
when called. Useful before/after patching the plugin manifest to
confirm whether the change had the desired effect.

Reads the Venice API key from ~/.openclaw/openclaw.json (env.VENICE_API_KEY).
Override with the VENICE_API_KEY environment variable if needed.

USAGE
    python3 templates/smoke-test-reasoning-fires.py [model-id]

EXAMPLE
    python3 templates/smoke-test-reasoning-fires.py xiaomi-mimo-v2-5

EXIT CODES
    0 = reasoning_content length > 0, OK
    1 = reasoning_content is empty (model isn't reasoning)
    2 = API call failed
    3 = couldn't load VENICE_API_KEY
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request


def load_venice_key() -> str:
    env_key = os.environ.get("VENICE_API_KEY")
    if env_key:
        return env_key
    cfg_path = os.path.expanduser("~/.openclaw/openclaw.json")
    if not os.path.exists(cfg_path):
        return ""
    try:
        with open(cfg_path) as f:
            c = json.load(f)
        return c.get("env", {}).get("VENICE_API_KEY", "")
    except Exception:
        return ""


def main() -> int:
    model = sys.argv[1] if len(sys.argv) > 1 else "xiaomi-mimo-v2-5"

    key = load_venice_key()
    if not key:
        print("ERROR: VENICE_API_KEY not in env or ~/.openclaw/openclaw.json",
              file=sys.stderr)
        return 3

    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "user", "content": "What is 2+3? Answer with just the number."},
        ],
        "max_tokens": 60000,
        "stream": False,
    }).encode()

    req = urllib.request.Request(
        "https://api.venice.ai/api/v1/chat/completions",
        data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            resp = json.loads(r.read())
    except Exception as e:
        print(f"ERROR: API call failed: {e!r}", file=sys.stderr)
        return 2

    choice = resp["choices"][0]
    reasoning = choice["message"].get("reasoning_content", "") or ""
    content = choice["message"].get("content", "") or ""
    finish = choice.get("finish_reason")

    print(f"model: {model}")
    print(f"finish_reason: {finish}")
    print(f"usage: {resp.get('usage')}")
    print(f"reasoning_content length: {len(reasoning)}")
    print(f"reasoning_content[:200]: {reasoning[:200]!r}")
    print(f"content[:200]: {content[:200]!r}")

    if not reasoning:
        print("FAIL: reasoning is empty — model isn't reasoning at all.",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
