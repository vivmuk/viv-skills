#!/usr/bin/env python3
"""
Carousel Pipeline — Paper → 7-slide deck (PNG + PDF + ZIP).

Stage 1: Extract paper text via pymupdf
Stage 2: CEO writes 7-slide spec (LLM with response_format=json_object)
Stage 3: Render each slide — grok-imagine bg + Pillow text overlay
Stage 4: 3 reviewers score each slide (with image bytes in prompt)
Stage 5: Assemble PDF + ZIP

Environment:
- Uses the venv at /Users/vivgatesai/.paperclip/workspaces/aipharmaxchange/.venv/
  (pymupdf, reportlab, PIL preinstalled)
- Reads VENICE_API_KEY from env (DIEM cap awareness: see venice-api skill)

Run:
  /Users/vivgatesai/.paperclip/workspaces/aipharmaxchange/.venv/bin/python3 \\
    carousel_pipeline.py /path/to/paper.pdf /tmp/output_dir

Cost baseline (MIRA run, 2026-06-18): ~7 min wall-clock, ~$0.40.
"""
import os
import sys
import json
import time
import base64
import zipfile
import urllib.request
from pathlib import Path
from io import BytesIO

import pymupdf
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.utils import ImageReader


# ---- Config ----
VENICE_BASE = "https://api.venice.ai/api/v1"
VENICE_KEY = os.environ.get("VENICE_API_KEY", "")
if not VENICE_KEY:
    sys.exit("VENICE_API_KEY env var required")

# Brand palette (AIPharmaXchange)
BRAND = {
    "teal":  (43, 163, 155),   # #2BA39B
    "mint":  (143, 211, 182),  # #8FD3B6
    "navy":  (30, 58, 95),     # #1E3A5F
    "cream": (245, 240, 225),  # #F5F0E1
    "white": (255, 255, 255),
    "dark":  (20, 35, 60),
}
W, H = 864, 1152  # 3:4 portrait

# Model selection
CEO_MODEL = os.environ.get("CEO_MODEL", "minimax-m3")
REVIEWER_MODEL = os.environ.get("REVIEWER_MODEL", "minimax-m3")
IMAGE_MODEL = os.environ.get("IMAGE_MODEL", "grok-imagine-image-quality")


# ---- LLM call with response_format=json_object ----
def call_llm_json(system, prompt, model=None, max_tokens=2000, temperature=0.3):
    """Call Venice chat with response_format=json_object. Returns (dict, usage, seconds)."""
    model = model or CEO_MODEL
    t0 = time.time()
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "response_format": {"type": "json_object"},  # critical
    }
    req = urllib.request.Request(
        f"{VENICE_BASE}/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {VENICE_KEY}", "Content-Type": "application/json"},
        method="POST",
    )
    resp = urllib.request.urlopen(req, timeout=180)
    body = json.loads(resp.read())
    content = body["choices"][0]["message"]["content"]
    usage = body.get("usage", {})
    try:
        return json.loads(content), usage, time.time() - t0
    except json.JSONDecodeError as e:
        return {"_raw": content, "_parse_error": str(e)}, usage, time.time() - t0


def call_llm_vision(system, text_prompt, image_path, model=None, max_tokens=1000):
    """Call Venice chat with an image for vision review. Returns (dict, usage, seconds)."""
    model = model or REVIEWER_MODEL
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()
    t0 = time.time()
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": [
                {"type": "text", "text": text_prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
            ]},
        ],
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }
    req = urllib.request.Request(
        f"{VENICE_BASE}/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {VENICE_KEY}", "Content-Type": "application/json"},
        method="POST",
    )
    resp = urllib.request.urlopen(req, timeout=180)
    body = json.loads(resp.read())
    content = body["choices"][0]["message"]["content"]
    usage = body.get("usage", {})
    try:
        return json.loads(content), usage, time.time() - t0
    except json.JSONDecodeError as e:
        return {"_raw": content, "_parse_error": str(e)}, usage, time.time() - t0


def call_image_gen(prompt, w=864, h=1152, model=None):
    """Call Venice image gen. Returns PNG bytes or None."""
    model = model or IMAGE_MODEL
    payload = {
        "model": model,
        "prompt": prompt,
        "width": w,
        "height": h,
    }
    # grok-imagine-image-quality only accepts basic params
    if model != "grok-imagine-image-quality":
        payload["steps"] = 25
        payload["cfg_scale"] = 7
    req = urllib.request.Request(
        f"{VENICE_BASE}/image/generate",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {VENICE_KEY}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req, timeout=180)
        body = json.loads(resp.read())
        if "images" in body and body["images"]:
            img_b64 = body["images"][0]
            if isinstance(img_b64, str):
                return base64.b64decode(img_b64)
    except Exception as e:
        print(f"[image_gen] {model} error: {e}", file=sys.stderr)
    return None


# ---- Stage 1: Extract paper ----
def extract_paper(pdf_path):
    doc = pymupdf.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text() + "\n\n--- PAGE BREAK ---\n\n"
    doc.close()
    return text[:50000]  # truncate for prompt


# ---- Stage 2: CEO writes spec ----
CEO_SYSTEM = """You are the CEO of AIPharmaXchange, an AI-focused pharma publication. You are a senior medical writer with deep expertise in clinical trial design, biostatistics, and FDA regulatory pathways. You read published research papers and translate them into social-media-ready carousel content.

Your output must be strict JSON: a `slides` array of 7 slide objects. No preamble, no markdown fences, no trailing explanation. The schema is enforced by the API."""


def ceo_write_spec(paper_text):
    prompt = f"""Read this research paper excerpt and design a 7-slide LinkedIn/Instagram carousel.

PAPER EXCERPT:
{paper_text}

REQUIREMENTS:
- Exactly 7 slides
- Slide 1: Title card with paper title, short hook, authors' institution, DOI
- Slide 2: What the system does (the core method)
- Slide 3: Headline result (primary endpoint numbers)
- Slide 4: Workflow fidelity (secondary metrics, coverage, safety)
- Slide 5: TREND CONTEXT — how this represents a shift from simple clinical-decision-support chat apps (like AMIE, MAI-DxO, OpenAI-Penda) toward fully integrated EHR-resident autonomous agents
- Slide 6: LIMITATIONS — honest fair/balance. At least 4 cards covering: study design limits, training-data overlap, sandbox vs real EHR, retrospective validation, governance/safety oversight gaps
- Slide 7: Implications + CTA (one DOI link to read the paper)

Each slide must have:
- "slide_num": 1-7
- "title": 8-14 words, number-led or named-entity-led, active voice, no hype
- "body_bullets": 3-5 short bullets, each ≤15 words
- "key_claim": a single factual claim (with citation, e.g., "p.4" or "Table 2")
- "visual_hint": one sentence describing what the visual should show (chart type, icon, diagram)

Return strictly this JSON shape:
{{"slides": [{{"slide_num": 1, "title": "...", "body_bullets": ["...", "..."], "key_claim": "...", "visual_hint": "..."}}, ...]}}"""
    return call_llm_json(CEO_SYSTEM, prompt, max_tokens=4000)


# ---- Stage 3: Render slides ----
def find_font(size):
    for p in [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def render_slide(slide, slide_num, bg_bytes=None):
    """Render one slide: bg from image gen (no text!) + Pillow overlay for ALL text."""
    img = Image.new("RGB", (W, H), BRAND["cream"])
    if bg_bytes:
        bg = Image.open(BytesIO(bg_bytes)).convert("RGB").resize((W, H), Image.LANCZOS)
        img = Image.blend(img, bg, 0.6)  # 60% bg, 40% cream so text stays readable
    draw = ImageDraw.Draw(img)

    # Header band
    draw.rectangle([(0, 0), (W, 90)], fill=BRAND["navy"])
    draw.text((32, 28), "AIPharmaXchange", fill=BRAND["mint"], font=find_font(18))
    draw.text((W - 130, 28), f"Slide {slide_num}/7", fill=BRAND["mint"], font=find_font(18))

    # Title (word-wrap)
    title_font = find_font(38)
    words = slide["title"].split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if draw.textbbox((0, 0), test, font=title_font)[2] > W - 64:
            lines.append(cur)
            cur = w
        else:
            cur = test
    if cur:
        lines.append(cur)
    y = 130
    for line in lines[:3]:
        draw.text((32, y), line, fill=BRAND["navy"], font=title_font)
        y += 48

    # Bullets
    body_font = find_font(24)
    bullet_y = y + 30
    for bullet in slide.get("body_bullets", [])[:6]:
        draw.ellipse([(32, bullet_y + 10), (44, bullet_y + 22)], fill=BRAND["teal"])
        words = bullet.split()
        line, lines = "", []
        for w in words:
            test = (line + " " + w).strip()
            if draw.textbbox((0, 0), test, font=body_font)[2] > W - 90:
                lines.append(line)
                line = w
            else:
                line = test
        if line:
            lines.append(line)
        for ln in lines[:3]:
            draw.text((54, bullet_y), ln, fill=BRAND["dark"], font=body_font)
            bullet_y += 32
        bullet_y += 8

    # Key claim footer
    claim = slide.get("key_claim", "")
    if claim:
        claim_font = find_font(16)
        words = claim.split()
        line, lines = "", []
        for w in words:
            test = (line + " " + w).strip()
            if draw.textbbox((0, 0), test, font=claim_font)[2] > W - 64:
                lines.append(line)
                line = w
            else:
                line = test
        if line:
            lines.append(line)
        claim_y = H - 80 - (len(lines) * 22)
        draw.rectangle([(32, claim_y - 12), (W - 32, claim_y + len(lines) * 22 + 4)], fill=BRAND["cream"])
        for ln in lines[:2]:
            draw.text((32, claim_y), f"• {ln}", fill=BRAND["teal"], font=claim_font)
            claim_y += 22

    # Bottom band
    draw.rectangle([(0, H - 30), (W, H)], fill=BRAND["navy"])
    return img


def render_all_slides(spec, out_dir):
    """Generate bg + render each slide. Returns list of PNG paths."""
    paths = []
    for slide in spec.get("slides", [])[:7]:
        sn = slide["slide_num"]
        # Image model prompt: NO TEXT, NO LETTERS
        bg_prompt = (
            f"AIPharmaXchange editorial illustration: {slide['visual_hint']}. "
            "Watercolor texture, teal #2BA39B and navy #1E3A5F on cream #F5F0E1, "
            "clean minimal composition, NO TEXT, NO LETTERS, NO WORDS, NO CHARACTERS, "
            "NO LABELS, professional medical/scientific aesthetic, painterly style, "
            "3:4 portrait composition"
        )
        bg_bytes = call_image_gen(bg_prompt)
        slide_img = render_slide(slide, sn, bg_bytes)
        out_path = Path(out_dir) / f"slide_{sn:02d}.png"
        slide_img.save(out_path, "PNG", optimize=True)
        paths.append(out_path)
        print(f"  Slide {sn}: {out_path.name} ({out_path.stat().st_size // 1024} KB)")
    return paths


# ---- Stage 4: 3 reviewers (with image bytes!) ----
REVIEWERS = {
    "accuracy": {
        "system": "You are an Accuracy Reviewer for AIPharmaXchange. Verify every numerical or factual claim in the slide is supported by the source paper excerpt. Be ruthless. Output JSON only.",
        "prompt": """Paper excerpt:
{paper}

Slide spec:
{slide}

You also see the rendered slide image. Check for:
- Numerical claims that match the paper exactly
- Hallucinated text inside the image (gibberish strings)
- Claims that contradict the source

Return JSON:
{{"score": N, "claims": [{{"claim": "...", "verdict": "SUPPORTED/UNSUPPORTED/AMBIGUOUS", "evidence": "p.X"}}], "hallucinated_text_in_image": [...], "summary": "1-line"}}""",
    },
    "alignment": {
        "system": "You are an Alignment Reviewer for AIPharmaXchange. Inspect the rendered slide for layout, hierarchy, and visual coherence. Output JSON only.",
        "prompt": """Slide spec:
{slide}

You see the rendered 864x1152 slide image. Check for:
- Title clipping or overflow
- Bullet text overlapping the illustration
- Z-order collisions (visual elements in front of text)
- Bullet count matches spec
- Hierarchy is clear

Return JSON:
{{"score": N, "title_clipping": true/false, "bullets_overlap_visual": true/false, "z_order_collisions": ["..."], "issues": ["..."], "summary": "1-line"}}""",
    },
    "brand": {
        "system": "You are a Brand Reviewer for AIPharmaXchange. Brand uses teal #2BA39B, mint #8FD3B6, navy #1E3A5F, cream #F5F0E1. Tone: editorial, clinical, fair/balance. No hype words. No exclamation marks. Output JSON only.",
        "prompt": """Slide spec:
{slide}

You see the rendered slide image. Check for:
- Palette is on-brand (teal/mint/navy/cream dominant)
- Tone is clinical/editorial, not promotional
- Hype words present (flag any of: groundbreaking, revolutionary, amazing, game-changing, unprecedented, extraordinary, incredible, awesome)
- Citations present in footer
- Exclamation marks

Return JSON:
{{"score": N, "palette_ok": true/false, "tone_ok": true/false, "hype_words_found": ["..."], "exclamation_marks": N, "summary": "1-line"}}""",
    },
}


def review_all(spec, slide_paths, paper_text):
    """All 3 reviewers per slide, with image bytes in prompt."""
    results = []
    for slide, path in zip(spec.get("slides", [])[:7], slide_paths):
        sn = slide["slide_num"]
        slide_review = {"slide_num": sn, "reviewers": {}}
        for rname, rconf in REVIEWERS.items():
            prompt = rconf["prompt"].format(paper=paper_text[:10000], slide=json.dumps(slide))
            data, usage, elapsed = call_llm_vision(rconf["system"], prompt, path, max_tokens=1000)
            slide_review["reviewers"][rname] = {
                "data": data,
                "tokens": usage,
                "seconds": round(elapsed, 2),
            }
            score = data.get("score", -1) if isinstance(data, dict) else -1
            print(f"  Slide {sn} / {rname}: score={score}, {elapsed:.1f}s")
        results.append(slide_review)
    return results


# ---- Stage 5: Assemble PDF + ZIP ----
def assemble(slide_paths, spec, reviews, out_dir):
    pdf_path = Path(out_dir) / "carousel.pdf"
    c = rl_canvas.Canvas(str(pdf_path), pagesize=(W, H))
    for sp in slide_paths:
        c.drawImage(ImageReader(str(sp)), 0, 0, W, H)
        c.showPage()
    c.save()

    zip_path = Path(out_dir) / "carousel.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for sp in slide_paths:
            zf.write(sp, sp.name)
        zf.writestr("spec.json", json.dumps(spec, indent=2))
        zf.writestr("reviews.json", json.dumps(reviews, indent=2))
    return pdf_path, zip_path


# ---- Main ----
def main(pdf_path, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=== Stage 1: Extract paper ===")
    paper_text = extract_paper(pdf_path)
    print(f"  {len(paper_text)} chars")

    print("\n=== Stage 2: CEO writes spec ===")
    spec, ceo_usage, ceo_sec = ceo_write_spec(paper_text)
    print(f"  {ceo_sec:.1f}s, {ceo_usage.get('prompt_tokens', 0)} in / {ceo_usage.get('completion_tokens', 0)} out")
    print(f"  {len(spec.get('slides', []))} slides parsed")

    print("\n=== Stage 3: Render 7 slides ===")
    slide_paths = render_all_slides(spec, out_dir)

    print("\n=== Stage 4: 3 reviewers per slide (with image bytes) ===")
    reviews = review_all(spec, slide_paths, paper_text)

    print("\n=== Stage 5: Assemble PDF + ZIP ===")
    pdf_path, zip_path = assemble(slide_paths, spec, reviews, out_dir)
    print(f"  PDF: {pdf_path} ({pdf_path.stat().st_size // 1024} KB)")
    print(f"  ZIP: {zip_path} ({zip_path.stat().st_size // 1024} KB)")

    return pdf_path, zip_path


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: carousel_pipeline.py <paper.pdf> <output_dir>")
    main(sys.argv[1], sys.argv[2])
