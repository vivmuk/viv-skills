# Daily Post Generator — Automated Pipeline Template

Pattern for a Hermes cron job that generates a daily LinkedIn post (carousel + text), builds a DOCX report, and emails it.

## Pipeline Stages

1. **ResearchAnalyst** — Find trending pharma AI topic via Venice chat
2. **ResearchSynthesizer** — Create content brief (hook, 3 key points, CTA, slide prompts)
3. **ContentDirector** — Generate 5 carousel slides via Venice image API
4. **LinkedInStrategist** — Write post text with hashtags and engagement question
5. **BrandGuardian** — Verify brand compliance (colors, tone, evidence-first)
6. **Distribution** — Build DOCX → email → Telegram → wipe credentials

## Venice API Calls

### Chat (topic research + content brief)

**Use `grok-4-20` for premium authoring and `gemma-4-uncensored` for raw
research.** `openai-gpt-55-pro` is in the catalog but the user has flagged
it as too expensive for any agent or pipeline on this account — don't
default to it even when the prompt looks "premium." See the `venice-api`
skill for the full model-routing table.

```python
import json, urllib.request

payload = json.dumps({
    "model": "grok-4-20",  # premium authoring, 2M ctx, much cheaper than gpt-55-pro
    "messages": [
        {"role": "system", "content": "You are a pharma AI research analyst. Evidence-based, cite sources."},
        {"role": "user", "content": prompt}
    ],
    "temperature": 0.7,
    "max_tokens": 2000
}).encode()

req = urllib.request.Request(
    "https://api.venice.ai/api/v1/chat/completions",
    data=payload,
    headers={"Authorization": f"Bearer {VENICE_KEY}", "Content-Type": "application/json"}
)
result = json.loads(urllib.request.urlopen(req, timeout=120).read())
text = result["choices"][0]["message"]["content"]
```

### Image (carousel slides)

```python
payload = json.dumps({
    "model": "grok-imagine-image-quality",
    "prompt": prompt[:1499],  # Gateway caps at 1500 chars
    "aspect_ratio": "4:5",   # LinkedIn carousel format
    "format": "png",
    "hide_watermark": True,
    "safe_mode": False
}).encode()

req = urllib.request.Request(
    "https://api.venice.ai/api/v1/image/generate",  # Venice-native endpoint
    data=payload,
    headers={"Authorization": f"Bearer {VENICE_KEY}", "Content-Type": "application/json"}
)
result = json.loads(urllib.request.urlopen(req, timeout=300).read())

# ⚠️ grok-imagine-image-quality returns images[] as plain base64 strings
images = result.get("images", [])
img_bytes = base64.b64decode(images[0])
with open(out_path, "wb") as f:
    f.write(img_bytes)
```

## 5-Slide Carousel Structure

| Slide | Purpose | Content |
|-------|---------|---------|
| 1 | Hook/Cover | Bold title, provocative subtitle, brand logo, swipe arrow |
| 2 | Key Data | Strongest statistic, bar chart with 4-6 items |
| 3 | Second Data | Different angle, gap/contrast visualization |
| 4 | Insight/Myth-bust | Challenge assumption with data |
| 5 | CTA/Summary | 3 numbered takeaways + follow prompt |

## Watercolor Professional Style Base Prompt

Append to each slide prompt for brand consistency:

```
Professional watercolor illustration style. Soft teal #00D4AA watercolor wash accents, cream #FEFCF8 background, dark navy #1A1A2E text. Elegant watercolor bleeding edges. Clean Inter font. Medical research presentation.
```

## DOCX Report Structure

```python
from docx import Document
from docx.shared import Inches, Pt, RGBColor

doc = Document()
# Brand-styled title
title = doc.add_heading('Daily Post — [Date]', level=1)
for run in title.runs:
    run.font.color.rgb = RGBColor(0x00, 0xD4, 0xAA)

# Post text section
doc.add_heading('LinkedIn Post Text', level=2)
doc.add_paragraph(post_text)

# Embedded carousel slides
doc.add_heading('Carousel Slides', level=2)
for i, path in enumerate(slide_paths):
    doc.add_picture(path, width=Inches(5.5))
    doc.add_paragraph(f'Slide {i+1}')

# Research brief
doc.add_heading('Research Brief', level=2)
doc.add_paragraph(research_text[:2000])

doc.save(report_path)
```

## Email Delivery (himalaya)

```python
# Build MIME with attachment
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

msg = MIMEMultipart()
msg['From'] = 'sender@gmail.com'
msg['To'] = 'recipient@example.com'
msg['Subject'] = 'Daily AI Pharma Post — [Date]'
msg.attach(MIMEText('See attached report.', 'plain'))

with open(report_path, 'rb') as f:
    part = MIMEApplication(f.read(), _subtype='docx')
    part.add_header('Content-Disposition', 'attachment', filename='report.docx')
    msg.attach(part)

with open('/tmp/email_mime.txt', 'w') as f:
    f.write(msg.as_string())
```

Then:
```bash
cat /tmp/email_mime.txt | himalaya message send

# CRITICAL: Wipe credentials immediately
cat > ~/.config/himalaya/config.toml << 'WIPE'
# Credentials removed after use.
WIPE
```

## Image Compression for Telegram

Telegram has upload size limits. Compress before sending:

```bash
sips -s format jpeg -s formatOptions 85 /tmp/slide1.png --out /tmp/slide1.jpg
```

Then send via `send_message` with `MEDIA:/tmp/slide1.jpg`.

## Brand Guidelines Reference

- **Colors**: #00D4AA (teal), #FEFCF8 (cream), #1A1A2E (navy)
- **Fonts**: Inter (body), Fraunces (headings)
- **Tone**: Evidence-first, no hype, always cite sources
- **Hashtags**: #AIinPharma #PharmaAI #AIPharmaXchange
- **Post length**: Under 200 words, end with engagement question
