# PDF Generation from Markdown on macOS

Generate styled PDF reports from markdown content using fpdf2 with macOS system fonts.

## Installation

```bash
pip3 install fpdf2 markdown
```

## Key Lessons

### Use System Fonts for Unicode Support

fpdf2's built-in fonts (Helvetica, Courier, Times) only support Latin-1. Any Unicode character (em dashes `—`, bullets `•`, superscripts `²`, arrows `→`, Greek `α`) will crash with `FPDFUnicodeEncodingException`.

**macOS solution:** Use Arial Unicode.ttf from system fonts:

```python
from fpdf import FPDF

pdf = FPDF()
# Register the Unicode font family
pdf.add_font("AUni", "", "/System/Library/Fonts/Supplemental/Arial Unicode.ttf")
pdf.add_font("AUni", "B", "/System/Library/Fonts/Supplemental/Arial Bold.ttf")
pdf.add_font("AUni", "I", "/System/Library/Fonts/Supplemental/Arial Italic.ttf")
# Use it
pdf.set_font("AUni", "B", 16)
```

**Font paths on macOS:**
- Regular: `/System/Library/Fonts/Supplemental/Arial Unicode.ttf` (23MB, full Unicode)
- Bold: `/System/Library/Fonts/Supplemental/Arial Bold.ttf`
- Italic: `/System/Library/Fonts/Supplemental/Arial Italic.ttf`
- Bold Italic: `/System/Library/Fonts/Supplemental/Arial Bold Italic.ttf`

### Register All Variants You Use

If you call `pdf.set_font("AUni", "B", 12)` without registering the "B" variant, fpdf2 throws `Undefined font: arialuniB`. Register regular, bold, italic, and bold-italic if you use any of those styles.

### Deprecated `uni=True` Parameter

In fpdf2 >= 2.5.1, the `uni=True` parameter on `add_font()` is deprecated and ignored. Just omit it:

```python
# Old (deprecated warning)
pdf.add_font("AUni", "", path, uni=True)
# New (correct)
pdf.add_font("AUni", "", path)
```

### Markdown → HTML → PDF vs Direct Markdown → PDF

Two approaches:

1. **markdown + weasyprint** (markdown → HTML → PDF): Produces beautiful output but requires system libraries (`libgobject-2.0`, pango, etc.) that may not be installed. On macOS these are NOT available by default. Requires Homebrew `pango` + `glib`.

2. **fpdf2 direct** (markdown → PDF via Python): Pure Python, no system deps. You must write your own markdown parser/renderer. More work but more portable and reliable.

**Recommendation:** Use fpdf2 direct for reliability. Use markdown+weasyprint only if you know the system libraries are installed.

### Report PDF Template Structure

```python
class ReportPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=25)
        # Register fonts here
    
    def header(self):
        if self.page_no() > 1:
            # Page header with document title
            self.set_font("AUni", "", 7.5)
            self.set_text_color(150, 150, 150)
            self.cell(0, 8, "Report Title", align="C")
            self.ln(4)
            self.set_draw_color(200, 200, 200)
            self.line(15, self.get_y(), self.w - 15, self.get_y())
            self.ln(4)
    
    def footer(self):
        self.set_y(-20)
        # Page numbers
        self.set_font("AUni", "", 7.5)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")
```

### Styling Tips

- **Title page:** Use `pdf.add_page()` then `pdf.ln(55)` to push content down, add title, decorative line, metadata
- **Section headings:** Use `pdf.set_draw_color()` + `pdf.line()` for underlines
- **Blockquotes:** Left border line + light gray fill background
- **Tables:** `pdf.cell()` with `border=1` and `fill=True`, alternating row colors
- **Bullet points:** Use `"\u2022 "` (Unicode bullet) with `multi_cell()` for wrapping
- **Page numbering:** `pdf.alias_nb_pages()` then use `{nb}` placeholder in footer
