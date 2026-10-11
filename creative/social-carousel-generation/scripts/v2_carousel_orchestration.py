#!/usr/bin/env python3
"""
MIRA-style Carousel Orchestration (Option 2, V2).
Single image model (grok-imagine-image-quality) for all slides, no Pillow.
3 reviewers per slide. PDF + ZIP assembly.

Usage:
    python3 v2_carousel_orchestration.py <path-to-source.pdf>

Output:
    <output_dir>/slide_01.png ... slide_07.png
    <output_dir>/MIRA_carousel_v2.pdf
    <output_dir>/MIRA_carousel_v2.zip
    <output_dir>/spec.json, reviews.json, metrics.json
"""
import os, sys, json, time, base64, zipfile, re
from pathlib import Path

# Force the workspace venv (where pymupdf, reportlab, PIL live)
sys.path.insert(0, '/Users/vivgatesai/.paperclip/workspaces/aipharmaxchange/.venv/lib/python3.14/site-packages')
import urllib.request
import pymupdf
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# ---- Config ----
# IMPORTANT: this is the working Venice inference key. If it 402s (DIEM
# cap), check ~/.paperclip/instances/default/.env for an alternate key.
KEY = os.environ.get('VENICE_KEY',
    'VENICE_INFERENCE_KEY_c5diyYrdrrKLbenzadX4CP7CueQN--urN3zxUYEXNE')
BASE = 'https://api.venice.ai/api/v1'
MODEL_LLM = 'minimax-m3'
MODEL_IMG = 'grok-imagine-image-quality'
W, H = 864, 1152  # 3:4 portrait

# Negative prompt for grok-imagine. Critical for text fidelity.
NEG = ('blurry text, gibberish letters, distorted glyphs, misspelled words, '
       'hex codes, hashtags, watermarks, signatures, blurry, low quality, '
       'off-brand colors, pink tint, purple, red, '
       'Nature journal branding, NEJM, JAMA, Lancet')

# ---- Metrics ----
metrics = {'stages': [], 'errors': [], 'total_in': 0, 'total_out': 0,
           'images': 0, 'retries': 0}


def strip_fences(s):
    s = s.strip()
    if s.startswith('```'):
        s = s.split('```')[1]
        if s.startswith('json'):
            s = s[4:]
    return s.strip()


def safe_parse_json(s):
    """Strict JSON parse, then attempt quote/brace repair for truncation."""
    s = strip_fences(s)
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass
    # Fix: unterminated string — close all open quotes and try again
    in_string, escape, fixed = False, False, []
    for ch in s:
        if escape:
            escape = False
        elif ch == '\\':
            escape = True
        elif ch == '"':
            in_string = not in_string
        fixed.append(ch)
    if in_string:
        fixed.append('"')
        open_b = fixed.count('{') - fixed.count('}')
        open_s = fixed.count('[') - fixed.count(']')
        fixed.append('}' * open_b + ']' * open_s)
        try:
            return json.loads(''.join(fixed))
        except Exception:
            pass
    return None


def call_llm(prompt, system='', max_tokens=4000, retry=True, response_format=None):
    """LLM call with empty-response retry. Returns (content, usage, elapsed)."""
    msgs = []
    if system:
        msgs.append({'role': 'system', 'content': system})
    msgs.append({'role': 'user', 'content': prompt})

    body = {'model': MODEL_LLM, 'messages': msgs,
            'max_tokens': max_tokens, 'temperature': 0.4}
    if response_format:
        body['response_format'] = response_format

    for attempt in range(3 if retry else 1):
        t0 = time.time()
        req = urllib.request.Request(
            f'{BASE}/chat/completions',
            data=json.dumps(body).encode(),
            headers={'Authorization': f'Bearer {KEY}',
                     'Content-Type': 'application/json'},
            method='POST')
        try:
            r = urllib.request.urlopen(req, timeout=180)
            resp = json.loads(r.read())
            content = resp['choices'][0]['message'].get('content', '') or ''
            usage = resp.get('usage', {})
            metrics['total_in'] += usage.get('prompt_tokens', 0)
            metrics['total_out'] += usage.get('completion_tokens', 0)
            if not content.strip() and retry and attempt < 2:
                metrics['retries'] += 1
                time.sleep(2 ** attempt)
                continue
            return content, usage, time.time() - t0
        except urllib.error.HTTPError as e:
            metrics['errors'].append(f'LLM {e.code}: {e.read().decode()[:200]}')
            if retry and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            return '', {}, time.time() - t0
        except Exception as e:
            metrics['errors'].append(f'LLM: {e}')
            return '', {}, time.time() - t0
    return '', {}, 0


def call_img(prompt, seed=None):
    """Image gen via grok-imagine-image-quality. Returns (bytes, elapsed) or (None, elapsed)."""
    t0 = time.time()
    body = {
        'model': MODEL_IMG, 'prompt': prompt,
        'negative_prompt': NEG,
        'width': W, 'height': H,
        'steps': 30, 'cfg_scale': 7,
        'hide_watermark': True,
    }
    if seed is not None:
        body['seed'] = seed
    req = urllib.request.Request(
        f'{BASE}/image/generate',
        data=json.dumps(body).encode(),
        headers={'Authorization': f'Bearer {KEY}',
                 'Content-Type': 'application/json'},
        method='POST')
    try:
        r = urllib.request.urlopen(req, timeout=180)
        resp = json.loads(r.read())
        if 'images' in resp and resp['images']:
            metrics['images'] += 1
            return base64.b64decode(resp['images'][0]), time.time() - t0
    except urllib.error.HTTPError as e:
        metrics['errors'].append(f'IMG {e.code}: {e.read().decode()[:200]}')
    except Exception as e:
        metrics['errors'].append(f'IMG: {e}')
    return None, time.time() - t0


# ---- Step 1: Extract paper ----
def extract_paper(path):
    print('=== Step 1: Extract paper ===')
    t0 = time.time()
    doc = pymupdf.open(path)
    text = ''.join(p.get_text() + '\n\n--- PAGE BREAK ---\n\n' for p in doc)
    doc.close()
    print(f'  {len(text)} chars in {time.time()-t0:.2f}s')
    return text


# ---- Step 2: CEO outline ----
CEO_SYS = ("You are the CEO of AIPharmaXchange, a senior medical writer. "
           "Output strict JSON only, no markdown fences, no preamble.")

CEO_OUTLINE_PROMPT = """Read this paper excerpt and produce a 7-slide LinkedIn carousel outline.

PAPER:
{paper}

SLIDE STRUCTURE:
1. Title card — paper title, 1-line hook, authors + institution, DOI
2. What MIRA does — core method (5-step action space: history → tests → diagnosis → meds → admit)
3. Headline result — 88.9% MIRA vs 78.1% board-certified vs 71.1% mixed cohort, 8 conditions, McNemar p<0.001
4. Workflow fidelity — 51.1% blood-test ordering coverage, 99.8% prescription dosing accuracy, safety screen before meds, zero major events
5. Trend context — shift from chat-only CDSS (AMIE, MAI-DxO, OpenAI-Penda) toward integrated EHR-resident autonomous agents (MIRA)
6. Four honest limits — sandbox EHR, MIMIC-IV train/test overlap, retrospective only, narrow case set (pneumonia 72.4%, UTI 77.6%)
7. Implications + DOI CTA — public benchmark + framework, next steps, DOI link

For each slide, return:
- title (8-14 words, no leading slide number)
- bullets (3-5, each ≤15 words)
- key_claim (one line with paper page citation like p.X or Fig.X)
- doi (exact DOI string from the paper, if any)

Return strict JSON: {{"slides": [{{"slide_num": N, "title": "...", "bullets": [...], "key_claim": "...", "doi": "..."}}]}}"""


def ceo_outline(text):
    print('\n=== Step 2: CEO outline ===')
    prompt = CEO_OUTLINE_PROMPT.format(paper=text[:40000])
    content, usage, elapsed = call_llm(prompt, system=CEO_SYS,
                                        max_tokens=3000,
                                        response_format={'type': 'json_object'})
    print(f'  CEO outline: {elapsed:.1f}s, {usage.get("prompt_tokens",0)} in / '
          f'{usage.get("completion_tokens",0)} out')
    spec = safe_parse_json(content)
    if not spec or not spec.get('slides'):
        print(f'  PARSE FAIL. First 800: {content[:800]}')
        return {'slides': []}
    print(f'  Parsed {len(spec["slides"])} slides')
    return spec


# ---- Step 3: CEO writes image prompt for each slide ----
IMG_PROMPT_TEMPLATE = """You are designing an image-generation prompt for grok-imagine-image-quality. The image will be 864x1152 pixels, 3:4 portrait, for a clinical infographic slide.

Slide outline:
Title: {title}
Bullets: {bullets}
Key claim: {claim}
DOI: {doi}

Write a single, complete prompt that the image model will use to generate this slide. Include:
- Visual layout (what goes where)
- Color palette in NATURAL LANGUAGE (teal, navy, cream — NOT hex codes)
- All text strings quoted explicitly with "double quotes"
- Style descriptors (editorial, professional, medical, clean)

SLIDE-SPECIFIC RULES:
- Slide 7 (implications): explicitly forbid journal names. "Do NOT include Nature, NEJM, JAMA, Lancet, or any other journal name. The DOI is the only citation."
- Slide 6 (limitations): enforce "a 2x2 grid of 4 cards, each card a teal-bordered rectangle with a header bar and body text. Do NOT render a vertical list, single-column layout, or numbered list."
- All slides: "Do NOT include slide numbers (1., 2., etc.) in the rendered title."
- All slides: "Do NOT include any URL except the DOI itself."

CRITICAL RULES:
- Quote every text string exactly as it should appear in the image, using "double quotes"
- Do NOT use hex color codes (#XXXXXX) anywhere — describe colors naturally
- Do NOT include any other commentary or preamble

Return ONLY the prompt string (no JSON wrapper, no markdown fences). The prompt should be self-contained."""


def ceo_image_prompts(spec_outline):
    print('\n=== Step 3: CEO writes image prompts (1 call per slide) ===')
    slides = []
    for i, slide in enumerate(spec_outline.get('slides', [])[:7], 1):
        sn = slide.get('slide_num', i)
        prompt = IMG_PROMPT_TEMPLATE.format(
            title=slide.get('title', ''),
            bullets=json.dumps(slide.get('bullets', [])),
            claim=slide.get('key_claim', ''),
            doi=slide.get('doi', ''),
        )
        img_prompt, usage, elapsed = call_llm(prompt, max_tokens=800)
        img_prompt = strip_fences(img_prompt).strip()
        # Strip leading slide numbers from title (Pitfall 15)
        title = re.sub(r'^\d+\.\s*', '', slide.get('title', ''))
        print(f'  Slide {sn} prompt: {len(img_prompt)} chars, {elapsed:.1f}s')
        slides.append({
            'slide_num': sn,
            'title': title,
            'body': slide.get('bullets', []),
            'key_claim': slide.get('key_claim', ''),
            'doi': slide.get('doi', ''),
            'image_prompt': img_prompt,
        })
    return slides


# ---- Step 4: Render 7 slides ----
def render_slides(slides, out_dir):
    print('\n=== Step 4: Render 7 slides ===')
    paths = []
    for slide in slides:
        sn = slide['slide_num']
        # Try 2 seeds; keep first success (Pitfall 8: 2 variants)
        for seed in [None, 42]:
            img_bytes, elapsed = call_img(slide['image_prompt'], seed=seed)
            if img_bytes:
                path = out_dir / f'slide_{sn:02d}.png'
                with open(path, 'wb') as f:
                    f.write(img_bytes)
                paths.append(path)
                print(f'  Slide {sn}: {len(img_bytes)//1024} KB, {elapsed:.1f}s')
                break
        else:
            print(f'  Slide {sn}: FAILED all attempts')
    return paths


# ---- Step 5: 3 reviewers per slide ----
REV_PROMPTS = {
    'accuracy': """You are the Accuracy Reviewer for AIPharmaXchange. Verify every numerical/factual claim in the slide against the source paper. Output JSON.

Paper excerpt:
{paper}

Slide title: {title}
Slide body: {body}
Key claim: {claim}

Return JSON: {{"score": N, "issues": [{{"text": "...", "verdict": "SUPPORTED/UNSUPPORTED", "evidence": "p.X"}}], "summary": "1-line"}}""",

    'alignment': """You are the Alignment Reviewer for AIPharmaXchange. The rendered PNG is at {img_path}. Check the slide title, body bullets, hierarchy, no clipping.

Slide title: {title}
Slide body: {body}
Key claim: {claim}

Return JSON: {{"score": N, "title_ok": true/false, "bullets_ok": true/false, "issues": ["..."], "summary": "1-line"}}""",

    'brand': """You are the Brand Reviewer for AIPharmaXchange. Palette: teal, navy, cream. Tone: editorial, clinical, fair/balance. No hype words ("groundbreaking", "revolutionary", "amazing"), no exclamation marks.

Slide title: {title}
Slide body: {body}

Return JSON: {{"score": N, "tone_ok": true/false, "hype_words": ["..."], "palette_ok": true/false, "summary": "1-line"}}""",
}


def review_slides(slides, text, out_dir):
    print('\n=== Step 5: 3 reviewers score each slide ===')
    reviews = []
    for slide in slides:
        sn = slide['slide_num']
        img_path = out_dir / f'slide_{sn:02d}.png'
        if not img_path.exists():
            continue
        slide_review = {'slide_num': sn, 'reviewers': {}}
        print(f'  Slide {sn}:')
        for rname, template in REV_PROMPTS.items():
            prompt = template.format(
                paper=text[:8000],
                title=slide['title'],
                body=json.dumps(slide['body']),
                claim=slide['key_claim'],
                img_path=str(img_path),
            )
            content, usage, elapsed = call_llm(
                prompt, max_tokens=600,
                response_format={'type': 'json_object'})
            data = safe_parse_json(content) or {
                'score': -1, 'parse_error': True, 'raw': content[:200]}
            slide_review['reviewers'][rname] = {
                'score': data.get('score', -1),
                'summary': data.get('summary', ''),
                'issues': data.get('issues', []),
            }
            print(f'    {rname}: {data.get("score","?")}/10, {elapsed:.1f}s — '
                  f'{str(data.get("summary",""))[:80]}')
        reviews.append(slide_review)
    return reviews


# ---- Step 6: PDF + ZIP ----
def assemble(slides, slide_paths, reviews, out_dir):
    print('\n=== Step 6: PDF + ZIP ===')
    if not slide_paths:
        print('  No slides rendered, skipping PDF/ZIP')
        return None, None
    pdf_path = out_dir / 'carousel.pdf'
    c = canvas.Canvas(str(pdf_path), pagesize=(W, H))
    for sp in slide_paths:
        c.drawImage(ImageReader(str(sp)), 0, 0, W, H)
        c.showPage()
    c.save()
    print(f'  PDF: {pdf_path.name} ({pdf_path.stat().st_size//1024} KB)')

    zip_path = out_dir / 'carousel.zip'
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for sp in slide_paths:
            zf.write(sp, sp.name)
        with open(out_dir / 'spec.json', 'w') as f:
            json.dump({'slides': slides}, f, indent=2)
        with open(out_dir / 'reviews.json', 'w') as f:
            json.dump(reviews, f, indent=2)
        zf.write(out_dir / 'spec.json', 'spec.json')
        zf.write(out_dir / 'reviews.json', 'reviews.json')
    print(f'  ZIP: {zip_path.name} ({zip_path.stat().st_size//1024} KB)')
    return pdf_path, zip_path


# ---- Main ----
def main():
    if len(sys.argv) < 2:
        print('Usage: v2_carousel_orchestration.py <paper.pdf> [output_dir]')
        sys.exit(1)
    paper_path = Path(sys.argv[1])
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(
        f'/tmp/carousel_{int(time.time())}')
    out_dir.mkdir(exist_ok=True)

    text = extract_paper(paper_path)
    spec_outline = ceo_outline(text)
    slides = ceo_image_prompts(spec_outline)
    slide_paths = render_slides(slides, out_dir)
    reviews = review_slides(slides, text, out_dir)
    assemble(slides, slide_paths, reviews, out_dir)

    # Report
    with open(out_dir / 'metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2, default=str)
    print('\n' + '=' * 60)
    print('METRICS')
    print('=' * 60)
    print(f'LLM tokens: {metrics["total_in"]:,} in / '
          f'{metrics["total_out"]:,} out')
    print(f'Retries on empty response: {metrics["retries"]}')
    print(f'Images generated: {metrics["images"]}')
    cost = ((metrics["total_in"] / 1e6) * 0.20
            + (metrics["total_out"] / 1e6) * 0.80
            + metrics["images"] * 0.05)
    print(f'Cost: ~${cost:.4f}')
    print(f'Errors: {len(metrics["errors"])}')
    for e in metrics['errors'][:5]:
        print(f'  {e[:200]}')
    print(f'\nArtifacts: {out_dir}')


if __name__ == '__main__':
    main()
