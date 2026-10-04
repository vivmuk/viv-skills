#!/usr/bin/env python3
"""
Build a machine-readable index of the public-apis catalog.

Source: https://github.com/public-apis/public-apis (README.md)
Output: references/public-apis-index.json

Usage:
    python3 scripts/build_api_index.py            # fetch live, then parse
    python3 scripts/build_api_index.py FILE.md    # parse a local snapshot
"""

import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SOURCE = "https://raw.githubusercontent.com/public-apis/public-apis/master/README.md"
REPO = "https://github.com/public-apis/public-apis"
HERE = Path(__file__).resolve().parent.parent

ROW_RE = re.compile(
    r"^\|\s*\[(?P<name>[^\]]+)\]\((?P<link>[^)]+)\)\s*"
    r"\|\s*(?P<desc>.*?)\s*"
    r"\|\s*(?P<auth>[^|]*?)\s*"
    r"\|\s*(?P<https>[^|]*?)\s*"
    r"\|\s*(?P<cors>[^|]*?)\s*\|\s*$"
)
CAT_RE = re.compile(r"^###\s+(?P<name>.+?)\s*$")


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "novel-business-ideas-skill/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse(md: str):
    categories = []
    current = None
    for line in md.splitlines():
        cat = CAT_RE.match(line)
        if cat:
            name = cat.group("name").strip()
            # skip non-catalog sections that use ### headings
            if name.lower().startswith("apis covered under"):
                current = None
                continue
            current = {"name": name, "apis": []}
            categories.append(current)
            continue
        if current is None:
            continue
        row = ROW_RE.match(line)
        if row:
            auth = row.group("auth").strip().strip("`") or "No"
            current["apis"].append(
                {
                    "name": row.group("name").strip(),
                    "description": row.group("desc").strip(),
                    "auth": auth,
                    "keyless": auth.lower() in ("no", "none", ""),
                    "https": row.group("https").strip().lower() == "yes",
                    "cors": row.group("cors").strip(),
                    "link": row.group("link").strip(),
                }
            )
    categories = [c for c in categories if c["apis"]]
    return categories


def main():
    if len(sys.argv) > 1:
        md = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
    else:
        md = fetch(SOURCE)

    categories = parse(md)
    total = sum(len(c["apis"]) for c in categories)
    keyless = sum(1 for c in categories for a in c["apis"] if a["keyless"])

    payload = {
        "source": REPO,
        "raw_readme": SOURCE,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "category_count": len(categories),
        "api_count": total,
        "keyless_count": keyless,
        "categories": categories,
    }

    out = HERE / "references" / "public-apis-index.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=1), encoding="utf-8")

    print(f"categories: {len(categories)}")
    print(f"apis:       {total}")
    print(f"keyless:    {keyless}")
    print(f"written:    {out} ({out.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
