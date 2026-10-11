---
name: nano-pdf
description: "Create and edit PDFs: generate styled reports from markdown via fpdf2, or edit existing PDFs via nano-pdf CLI."
version: 1.1.0
author: community
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [PDF, Documents, Editing, NLP, Productivity, Generation, Reports]
    homepage: https://pypi.org/project/nano-pdf/
---

# PDF Workflow: Generation & Editing

This skill covers two PDF workflows:

1. **Generating PDFs from markdown** — Creating styled reports, documents, and deliverables from markdown content using fpdf2
2. **Editing existing PDFs** — Fixing text, typos, and titles in existing PDFs via nano-pdf CLI

## References

- `references/pdf-generation.md` — Full guide: fpdf2 setup, Unicode font handling on macOS, markdown-to-PDF pipeline, styling tips
- `references/docx-generation.md` — DOCX reports with embedded images and tables via python-docx (when the deliverable needs to be editable Word format)

---

## Part 1: Generating PDFs from Markdown

Use fpdf2 (pure Python, no system deps) to convert markdown content into professionally styled PDF reports.

**Quick start:** See `references/pdf-generation.md` for the complete pipeline including Unicode font registration, markdown parsing, and styling.

**Key gotcha:** fpdf2's built-in fonts only support Latin-1. On macOS, register Arial Unicode.ttf for full Unicode support (em dashes, Greek letters, arrows, etc.).

---

## Part 2: Editing Existing PDFs

Edit PDFs using natural-language instructions via nano-pdf CLI.

## Prerequisites

```bash
# Install with uv (recommended — already available in Hermes)
uv pip install nano-pdf

# Or with pip
pip install nano-pdf
```

## Usage

```bash
nano-pdf edit <file.pdf> <page_number> "<instruction>"
```

## Examples

```bash
# Change a title on page 1
nano-pdf edit deck.pdf 1 "Change the title to 'Q3 Results' and fix the typo in the subtitle"

# Update a date on a specific page
nano-pdf edit report.pdf 3 "Update the date from January to February 2026"

# Fix content
nano-pdf edit contract.pdf 2 "Change the client name from 'Acme Corp' to 'Acme Industries'"
```

## Notes

- Page numbers may be 0-based or 1-based depending on version — if the edit hits the wrong page, retry with ±1
- Always verify the output PDF after editing (use `read_file` to check file size, or open it)
- The tool uses an LLM under the hood — requires an API key (check `nano-pdf --help` for config)
- Works well for text changes; complex layout modifications may need a different approach
