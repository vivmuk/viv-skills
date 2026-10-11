# DOCX Report Generation with Embedded Images

When the deliverable needs to be an editable Word document (DOCX) rather than a PDF — especially when embedding data visualization images and tables — use `python-docx`.

## When to use DOCX vs PDF

- **DOCX**: Client needs to edit/annotate, embed high-res images, include data tables, or collaborate in Word/Google Docs
- **PDF**: Final read-only deliverable, strict formatting control, or print-first design

## Setup

```bash
pip3 install python-docx --break-system-packages -q
```

## Pattern: Research Paper → Visualized DOCX Report

This is the reusable pipeline for turning a research paper into a professional DOCX report with data visualization slides:

1. **Extract text** from PDF using pymupdf (`pip3 install pymupdf`)
2. **Identify key data points** — benchmark scores, sample sizes, statistical tests, effect sizes
3. **Generate data visualization slides** via Venice image API (see venice-api skill)
4. **Build DOCX** with python-docx: styled headings, embedded images, data tables, executive summary
5. **Deliver** via `MEDIA:` attachment or email via himalaya

## Full Working Example

```python
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
import os

# Brand colors
TEAL = RGBColor(0x00, 0xD4, 0xAA)
DARK = RGBColor(0x1A, 0x1A, 0x2E)
WHITE = RGBColor(0xFE, 0xFC, 0xF8)

doc = Document()

# --- Style Setup ---
style = doc.styles['Normal']
font = style.font
font.name = 'Calibri'
font.size = Pt(11)
font.color.rgb = DARK

# Title
title = doc.add_heading('Report Title', level=0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
for run in title.runs:
    run.font.color.rgb = TEAL
    run.font.size = Pt(28)

# Subtitle
sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = sub.add_run('Subtitle text | Date')
run.font.size = Pt(12)
run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

doc.add_page_break()

# --- Section with embedded image ---
doc.add_heading('Section Title', level=1)
doc.add_paragraph('Section body text...')

if os.path.exists('/tmp/slide1.png'):
    doc.add_picture('/tmp/slide1.png', width=Inches(6.0))
    last_paragraph = doc.paragraphs[-1]
    last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Caption
    cap = doc.add_paragraph('Figure 1: Caption text')
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in cap.runs:
        run.font.size = Pt(9)
        run.font.italic = True
        run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

# --- Data table ---
doc.add_heading('Data Table', level=2)
table = doc.add_table(rows=1, cols=3)
table.style = 'Light Grid Accent 1'
table.alignment = WD_TABLE_ALIGNMENT.CENTER

# Header row
hdr = table.rows[0].cells
for i, text in enumerate(['Model', 'Score', 'Rank']):
    hdr[i].text = text
    for p in hdr[i].paragraphs:
        for run in p.runs:
            run.font.bold = True

# Data rows
data = [
    ('Gemini 3.1 Pro', '97.4%', '1'),
    ('GPT-5.2', '94.2%', '2'),
]
for model, score, rank in data:
    row = table.add_row().cells
    row[0].text = model
    row[1].text = score
    row[2].text = rank

# --- Save ---
doc.save('/tmp/report.docx')
print(f'Report saved: {os.path.getsize("/tmp/report.docx"):,} bytes')
```

## Key Tips

- **Image sizing**: Use `width=Inches(6.0)` for full-width slides in landscape orientation. The aspect ratio is preserved automatically.
- **Centering images**: After `add_picture()`, set alignment on the last paragraph: `doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER`
- **Table styling**: `Light Grid Accent 1` is the cleanest built-in style. For brand-colored tables, set cell shading manually.
- **Page breaks**: Use `doc.add_page_break()` between major sections — especially before each full-width image.
- **File size**: 8 embedded images (~200-270KB each) + text = ~1.7MB DOCX. Compress images with `sips` if needed: `sips -s format jpeg -Z 1200 /tmp/slide1.png --out /tmp/slide1.jpg`

## Pitfalls

- **python-docx doesn't auto-fit columns**: Set column widths manually if text gets clipped in tables.
- **No markdown parsing**: python-docx takes structured calls only. Build paragraphs, headings, and tables individually — no bulk markdown-to-docx conversion built in.
- **Image paths must exist**: `add_picture()` raises if the file doesn't exist. Always `os.path.exists()` check before embedding.
- **Font availability**: `Calibri` is available on Windows/macOS. For Linux, use `Liberation Sans` or `DejaVu Sans`.
