"""
Pillow-overlay hybrid infographic generator.
- Tries grok-imagine-image-quality (preferred SOTA) for the background
- Falls back to procedural Pillow watercolor wash if all image models fail
- Composes title, subtitle, 5 numbered cards, and brand mark with PIL

Usage:
    python3 pillow_infographic.py

Output:
    /Users/vivgatesai/.paperclip/workspaces/aipharmaxchange/output/critical_limits_4x5.png

Customize CARDS, TITLE, SUBTITLE to use this for any infographic. The 4:5
aspect ratio matches the AIPharmaXchange LinkedIn carousel spec. Change
W, H, aspect_ratio, and margin_x to adapt.
"""
import os, json, urllib.request, base64, io, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import glob, random

# ============ LOAD VENICE KEY ============
# Read from Paperclip's .env via a shell helper (works around bash literal
# mangling that affects inline strings).
key = subprocess.check_output(["/tmp/load_venice_key.sh"]).decode().strip()
print(f"key loaded: {bool(key)} len={len(key)}")

# ============ CONFIG ============
W, H = 1080, 1350  # 4:5 — LinkedIn carousel
TITLE_L1 = "5 Gaps in the"
TITLE_L2 = '"General AI > Specialized AI" Study'
SUBTITLE = "Why benchmark wins do not translate to clinical practice."
BRAND = "AIPharmaXchange"

CARDS = [
    ("1", "Hidden Conflict of Interest",
     "The study authors run a competing medical AI. They asked OpenEvidence for an API to power it. The paper appeared shortly after the request was declined."),
    ("2", "Contaminated Benchmarks",
     "General LLMs have seen the test questions in pretraining. A benchmark win can be memorization, not reasoning."),
    ("3", "Style Is Not Substance",
     "HealthBench rewards formatting like email headers. Wrong answer with right format can outscore a right answer with wrong format."),
    ("4", "No Clinical Outcomes",
     "The study measures answer-matching, not patient outcomes. A 95 percent benchmark score with 5 percent hallucination is dangerous in practice."),
    ("5", "Static Questions Are Not Clinical Decisions",
     "Multiple-choice benchmarks do not capture time pressure, ambiguous data, multi-turn reasoning, or the cost of a wrong answer."),
]

# Brand palette (AIPharmaXchange)
CREAM = (254, 252, 248)       # #FEFCF8
TEAL = (0, 212, 170)          # #00D4AA
TEAL_DARK = (0, 134, 108)
INK = (28, 42, 46)
INK_SOFT = (78, 90, 94)
CARD_BG = (255, 253, 250)

# ============ GENERATE BACKGROUND ============
bg_prompt = (
    "Soft, painterly abstract background. Cream #FEFCF8 base with a single "
    "gentle teal #00D4AA watercolor wash flowing from the top-right corner, "
    "softly blurred, organic edges, no hard lines. Subtle paper-grain texture. "
    "Minimal, editorial, magazine-quality. No text, no people, no objects. "
    "Negative space dominating, the wash covers at most 30 percent of the canvas."
)

def generate_bg():
    payload = {"model": "grok-imagine-image-quality", "prompt": bg_prompt, "aspect_ratio": "4:5"}
    req = urllib.request.Request(
        "https://api.venice.ai/api/v1/image/generate",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            data = json.loads(r.read())
        if "images" in data and len(data["images"]) > 0:
            img_b = base64.b64decode(data["images"][0])
            bg = Image.open(io.BytesIO(img_b)).convert("RGB")
            bg = bg.resize((W, H), Image.LANCZOS)
            print(f"bg from grok-imagine-image-quality: {bg.size}")
            return bg.filter(ImageFilter.GaussianBlur(2))
    except Exception as e:
        print(f"image model failed: {e} — using procedural fallback")
    return procedural_bg()

def procedural_bg():
    bg = Image.new("RGB", (W, H), CREAM)
    wash = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    wd = ImageDraw.Draw(wash)
    random.seed(7)
    for _ in range(30):
        cx = random.randint(int(W*0.55), W + 200)
        cy = random.randint(-150, int(H*0.4))
        r = random.randint(80, 220)
        a = random.randint(10, 22)
        wd.ellipse((cx-r, cy-r, cx+r, cy+r), fill=((0, 212, 170, a)))
    wash = wash.filter(ImageFilter.GaussianBlur(28))
    bg.paste(wash, (0, 0), wash)
    return bg.convert("RGB")

bg = generate_bg()
img = bg.copy()
draw = ImageDraw.Draw(img, "RGBA")

# ============ FONTS ============
SERIF = "/System/Library/Fonts/NewYork.ttf"
SERIF_IT = "/System/Library/Fonts/NewYorkItalic.ttf"
SANS = "/Library/Fonts/Helvetica.ttc"
for c in glob.glob("/System/Library/Fonts/*Serif*.ttf") + glob.glob("/System/Library/Fonts/*Serif*.ttc"):
    if "Bold" in c and "Italic" not in c: SERIF = c
    elif "Italic" in c and "Bold" not in c: SERIF_IT = c

font_title   = ImageFont.truetype(SERIF, 64)
font_subtitle = ImageFont.truetype(SERIF_IT, 28)
font_card_h  = ImageFont.truetype(SERIF, 32)
font_card_b  = ImageFont.truetype(SANS, 22)
font_num     = ImageFont.truetype(SERIF, 44)
font_brand   = ImageFont.truetype(SERIF_IT, 22)

# ============ TITLE BLOCK ============
def draw_text_centered(d, text, y, font, fill, lh=None):
    if lh is None: lh = int(font.size * 1.15)
    bbox = d.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    d.text(((W - tw) // 2, y), text, font=font, fill=fill)
    return y + lh

y = 80
y = draw_text_centered(draw, TITLE_L1, y, font_title, INK)
y = draw_text_centered(draw, TITLE_L2, y, font_title, TEAL_DARK)
y += 6
bbox = draw.textbbox((0, 0), SUBTITLE, font=font_subtitle)
sw = bbox[2] - bbox[0]
draw.text(((W - sw) // 2, y), SUBTITLE, font=font_subtitle, fill=INK_SOFT)
y += bbox[3] - bbox[1] + 44

# ============ CARDS ============
def wrap_text(text, font, max_w):
    words = text.split()
    lines, cur = [], []
    for w in words:
        test = " ".join(cur + [w])
        bbox = font.getbbox(test)
        if bbox[2] - bbox[0] <= max_w: cur.append(w)
        else:
            if cur: lines.append(" ".join(cur))
            cur = [w]
    if cur: lines.append(" ".join(cur))
    return lines

margin_x = 80
card_x = margin_x
card_w = W - 2 * margin_x
card_h = 138
card_gap = 14
card_y0 = y

for i, (num, head, body) in enumerate(CARDS):
    y0 = card_y0 + i * (card_h + card_gap)
    draw.rounded_rectangle(
        (card_x, y0, card_x + card_w, y0 + card_h),
        radius=14, fill=(*CARD_BG, 240), outline=(*TEAL, 90), width=1
    )
    cx = card_x + 50
    cy = y0 + card_h // 2
    cr = 32
    draw.ellipse((cx-cr, cy-cr, cx+cr, cy+cr), fill=TEAL)
    bbox = draw.textbbox((0, 0), num, font=font_num)
    nw = bbox[2] - bbox[0]; nh = bbox[3] - bbox[1]
    draw.text((cx - nw//2 - bbox[0], cy - nh//2 - bbox[1] - 4), num, font=font_num, fill=(255, 255, 255))

    hx = card_x + 105
    hy = y0 + 22
    draw.text((hx, hy), head, font=font_card_h, fill=INK)
    body_y = hy + 42
    body_w = card_w - (hx - card_x) - 24
    lines = wrap_text(body, font_card_b, body_w)[:3]
    for j, line in enumerate(lines):
        draw.text((hx, body_y + j * 28), line, font=font_card_b, fill=INK_SOFT)

# ============ BRAND MARK ============
bbox = draw.textbbox((0, 0), BRAND, font=font_brand)
bw = bbox[2] - bbox[0]
draw.text((W - bw - 60, H - 70), BRAND, font=font_brand, fill=TEAL_DARK)
draw.ellipse((W - bw - 85, H - 65, W - bw - 75, H - 55), fill=TEAL)

# ============ SAVE ============
out = "/Users/vivgatesai/.paperclip/workspaces/aipharmaxchange/output/critical_limits_4x5.png"
os.makedirs(os.path.dirname(out), exist_ok=True)
img.save(out, "PNG", optimize=True)
print(f"saved: {out}  ({os.path.getsize(out)} bytes)")
