#!/usr/bin/env python3
"""
Branded infographic template (AIPharmaXchange).

Pillow-only — for data-heavy infographics where the image model would
fabricate the numbers. See `branded-infographic` skill.

Usage:
    python3 templates/pillow_infographic_aipharma.py

Customize:
    - TITLE / SUBTITLE / TAGLINE (header)
    - ORG_TREE (list of (name, role, parent, model, is_llm))
    - COST_TABLE (list of (model_name, in_price, out_price, role))
    - MONTHLY (list of (activity, cost_string))
    - CALLOUT (text shown in mint callout box)
    - FOOTER (text shown in bottom band)
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ----- Canvas -----
W, H = 864, 1296
OUT = "/Users/vivgatesai/.paperclip/workspaces/aipharmaxchange/output/_template_infographic.png"

# ----- Brand palette -----
TEAL   = (0, 212, 170)
MINT   = (143, 211, 182)
NAVY   = (26, 26, 46)
CREAM  = (254, 252, 248)
INK    = (28, 32, 40)
LIGHT_MINT = (220, 240, 232)
WARM_CREAM = (250, 246, 236)
DARK_TEAL = (0, 156, 126)

# ----- Data (replace with your own) -----
TITLE = "AIPharmaXchange"
SUBTITLE = "Section subtitle here"
TAGLINE = "10 items · 3 highlighted · 7 standard"

COST_TABLE = [
    # (model_name, in_price, out_price, role)
    ("Model A", 0.50, 2.00, "primary use"),
    ("Model B", 0.20, 0.80, "secondary"),
    ("Model C", 0.10, 0.40, "fallback"),
]

MONTHLY = [
    # (activity, cost_string)
    ("Activity 1", "$0.50"),
    ("Activity 2", "$1.65"),
    ("TOTAL", "$2.15"),
]

CALLOUT = "Budget callout: $X / month"
FOOTER = "Agni Agent Report — topic · 2026-06-14"

# ----- Font helper -----
def find_font(size):
    paths = [
        "/System/Library/Fonts/Supplemental/Avenir Next Condensed.ttc",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size=size)
            except Exception:
                continue
    return ImageFont.load_default()

F_TITLE   = find_font(32)
F_SUB     = find_font(22)
F_TAG     = find_font(16)
F_H2      = find_font(22)
F_TABLE   = find_font(14)
F_TOTAL   = find_font(18)
F_FOOT    = find_font(11)
F_CALLOUT = find_font(14)

# ----- Build canvas -----
img = Image.new("RGB", (W, H), CREAM)

# Watercolor wash (subtle, no bleed-through)
wash = Image.new("RGB", (W, H), CREAM)
wd = ImageDraw.Draw(wash)
for i in range(20):
    mix = (
        MINT[0] * i // 20 + TEAL[0] * (20 - i) // 20,
        MINT[1] * i // 20 + TEAL[1] * (20 - i) // 20,
        MINT[2] * i // 20 + TEAL[2] * (20 - i) // 20,
    )
    wd.ellipse([W - 200 - i*30, -100 - i*30, W + 100 + i*30, 200 + i*30], fill=mix)
    wd.ellipse([-100 - i*30, H - 200 - i*30, 200 + i*30, H + 100 + i*30], fill=mix)
img = Image.blend(img, wash, alpha=0.5)

# Paper grain
noise = Image.effect_noise((W, H), 8).convert("L")
grain = Image.merge("RGB", (noise, noise, noise)).filter(ImageFilter.GaussianBlur(0.4))
img = Image.blend(img, Image.blend(img, grain, 0.04), 1.0)

draw = ImageDraw.Draw(img)

# ----- Header -----
y = 50
bbox = draw.textbbox((0, 0), TITLE, font=F_TITLE)
draw.text(((W - (bbox[2]-bbox[0])) // 2, y), TITLE, font=F_TITLE, fill=NAVY)
y += bbox[3] - bbox[1] + 8
bbox = draw.textbbox((0, 0), SUBTITLE, font=F_SUB)
draw.text(((W - (bbox[2]-bbox[0])) // 2, y), SUBTITLE, font=F_SUB, fill=NAVY)
y += bbox[3] - bbox[1] + 8
bbox = draw.textbbox((0, 0), TAGLINE, font=F_TAG)
draw.text(((W - (bbox[2]-bbox[0])) // 2, y), TAGLINE, font=F_TAG, fill=DARK_TEAL)
y += bbox[3] - bbox[1] + 6
draw.line([(80, y + 4), (W - 80, y + 4)], fill=TEAL, width=2)
y += 18

# ----- Cost table -----
draw.text((60, y), "COST TABLE", font=F_H2, fill=NAVY)
y += 36
col_x = [60, 530]
row_h = 30
for i, (name, inp, out, role) in enumerate(COST_TABLE):
    fill = LIGHT_MINT if i % 2 == 0 else WARM_CREAM
    draw.rectangle([(50, y), (W - 50, y + row_h)], fill=fill)
    draw.text((col_x[0], y + 7), name, font=F_TABLE, fill=INK)
    draw.text((col_x[1], y + 7), f"${inp:.3f} / ${out:.3f}", font=F_TABLE, fill=NAVY)
    y += row_h
y += 20

# ----- Monthly cost -----
draw.text((60, y), "MONTHLY COST", font=F_H2, fill=NAVY)
y += 36
for i, (act, cost) in enumerate(MONTHLY):
    is_total = i == len(MONTHLY) - 1
    if is_total:
        draw.rectangle([(50, y), (W - 50, y + row_h)], fill=TEAL)
        draw.text((col_x[0], y + 6), act, font=F_TOTAL, fill=NAVY)
        draw.text((col_x[1], y + 6), cost, font=F_TOTAL, fill=NAVY)
    else:
        fill = LIGHT_MINT if i % 2 == 0 else WARM_CREAM
        draw.rectangle([(50, y), (W - 50, y + row_h)], fill=fill)
        draw.text((col_x[0], y + 7), act, font=F_TABLE, fill=INK)
        draw.text((col_x[1], y + 7), cost, font=F_TABLE, fill=NAVY)
    y += row_h
y += 14

# ----- Callout -----
draw.rounded_rectangle([(50, y), (W - 50, y + 38)], radius=10, fill=MINT)
bbox = draw.textbbox((0, 0), CALLOUT, font=F_CALLOUT)
draw.text(((W - (bbox[2]-bbox[0])) // 2, y + 10), CALLOUT, font=F_CALLOUT, fill=NAVY)
y += 38 + 18

# ----- Footer (dedicated band, doesn't overlap data) -----
fb_y = H - 60
draw.rectangle([(0, fb_y), (W, H)], fill=CREAM)
bbox = draw.textbbox((0, 0), FOOTER, font=F_FOOT)
draw.text(((W - (bbox[2]-bbox[0])) // 2, fb_y + 18), FOOTER, font=F_FOOT, fill=NAVY)
brand = "● AIPharmaXchange"
bbox = draw.textbbox((0, 0), brand, font=F_FOOT)
draw.text((W - bbox[2] - 20, fb_y + 36), brand, font=F_FOOT, fill=DARK_TEAL)

# ----- Save -----
os.makedirs(os.path.dirname(OUT), exist_ok=True)
img.save(OUT, "PNG", optimize=True)
print(f"saved {OUT} ({os.path.getsize(OUT)} bytes)")
