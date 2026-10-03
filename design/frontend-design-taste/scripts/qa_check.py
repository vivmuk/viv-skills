#!/usr/bin/env python3
"""QA gate for the frontend-design-taste skill package.

Verifies every file referenced by SKILL.md exists, frontmatter is valid,
and the package tree is complete. Run: python3 scripts/qa_check.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
failures = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" - {detail}" if detail else ""))
    if not ok:
        failures.append(name)


print(f"QA check: {ROOT}")

# 1. Frontmatter validity
skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
fm = re.match(r"^---\n(.*?)\n---\n", skill, re.DOTALL)
check("SKILL.md has YAML frontmatter", bool(fm))
if fm:
    fields = dict(re.findall(r"^(\w+):\s*(.+)$", fm.group(1), re.MULTILINE))
    check("name present", "name" in fields, fields.get("name", ""))
    check("description present", "description" in fields)
    desc = fields.get("description", "")
    check("description has trigger phrasing", "Use when" in desc)

# 2. Every referenced file exists
refs = sorted(set(re.findall(r"`(references/[^`]+)`", skill)))
check("SKILL.md references something", len(refs) > 0, f"{len(refs)} paths")
for ref in refs:
    check(f"exists: {ref}", (ROOT / ref).exists() or (ROOT / ref).is_dir())

# 3. Directory structure
for d in ["references", "references/design-md-exemplars", "references/playwright-cli-references", "scripts"]:
    check(f"directory: {d}", (ROOT / d).is_dir())

# 4. The five core modules
for f in ["taste-skill.md", "vercel-web-interface-guidelines.md", "design-md-index.md", "image-to-code.md", "playwright-cli.md"]:
    check(f"core module: {f}", (ROOT / "references" / f).is_file())

# 5. Curated exemplars
exemplars = list((ROOT / "references" / "design-md-exemplars").glob("*.md"))
check("8 design-md exemplars vendored", len(exemplars) == 8, f"{len(exemplars)} found")

# 6. No placeholder or empty reference files
empty = [f for f in ROOT.rglob("*.md") if f.stat().st_size < 200]
check("no empty/truncated reference files", not empty, ", ".join(map(str, empty)))

# 7. Zip artifact (created by build; absent during dev is fine)
z = ROOT.parent.parent / "frontend-design-taste.zip"
print(f"  [INFO] zip artifact expected at {z}" + (" (present)" if z.exists() else " (not built yet)"))

print()
if failures:
    print(f"RESULT: {len(failures)} FAILURES")
    sys.exit(1)
print("RESULT: ALL CHECKS PASSED")
