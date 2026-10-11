#!/usr/bin/env python3
"""
AIPharmaXchange Carousel Orchestrator — Web Article Source
=============================================================
Adapted from `scripts/v2_carousel_orchestration.py` for sources that
are NOT PDFs (web articles, engineering blogs, news posts).

Pipeline (8 slides):
  1. Load article text from a .txt file
  2. CEO (google-gemma-4-31b-it) writes 8-slide spec + LinkedIn post copy
  3. CEO writes per-slide image prompts (watercolor style)
  4. Render all 8 slides via grok-imagine-image-quality (1024x1024)
  5. 3 reviewers per slide (Accuracy, Alignment, Brand) — grok-4-3
  6. Vision QA pass via qwen3-vl-235b-a22b (optional but recommended)
  7. Assemble PDF + ZIP
  8. Email + Telegram delivery

Locked v2 model stack (2026-06-19):
  - CEO:    google-gemma-4-31b-it + venice_parameters.disable_thinking=True
  - Reviewers: grok-4-3
  - Image:  grok-imagine-image-quality
  - Vision QA: qwen3-vl-235b-a22b

Footer rule (every slide): bottom-left "AIPharmaXchange" brand mark +
bottom-right "swipe →" cue. NO source URL/DOI/author in footer.

Usage:
    python3 web_article_orchestrator.py <article.txt> [--source-label LABEL]
                                              [--source-url URL]
                                              [--out-dir DIR]

Example:
    python3 web_article_orchestrator.py visuals/doximity_ask.txt \\
        --source-label "Doximity Technology Blog" \\
        --source-url "https://technology.doximity.com/articles/doximity-ask" \\
        --out-dir output/doximity_ask_carousel
"""
import os, sys, json, time, base64, zipfile, re, argparse, smtplib, ssl
from pathlib import Path
from email.message import EmailMessage
from email.utils import formatdate
from datetime import datetime
import mimetypes

# ---- Defaults (locked v2 stack) ----
KEY         = os.environ.get('VENICE_KEY',
                  'VENICE_INFERENCE_KEY_c5diyYrdrrKLbenzadX4CP7CueQN--urN3zxUYEXNE')
BASE        = 'https://api.venice.ai/api/v1'
MODEL_CEO   = 'google-gemma-4-31b-it'
MODEL_REV   = 'grok-4-3'
MODEL_IMG   = 'grok-imagine-image-quality'
MODEL_VIS   = 'qwen3-vl-235b-a22b'
W, H        = 1024, 1024

NEG = ('blurry text, gibberish letters, distorted glyphs, misspelled words, '
       'hex codes, hashtags, watermarks, signatures, blurry, low quality, '
       'off-brand colors, pink tint, purple, red, '
       'Nature journal branding, NEJM, JAMA, Lancet, journal logos, footer URL, '
       'author names, DOI in footer, page citations')

# ---- Spend ledger ----
SPEND_DIR  = Path('/tmp/aipharmaxchange_spend')
SPEND_DIR.mkdir(exist_ok=True)
SPEND_FILE = SPEND_DIR / f'spend_{datetime.now():%Y-%m-%d}.json'
DAILY_CAP  = 10.00

metrics = {'llm_in': 0, 'llm_out': 0, 'images': 0, 'retries': 0,
           'reviewer_calls': 0, 'vision_calls': 0, 'errors': []}


# ---- Helpers ----
def log(msg, **kv):
    ts = datetime.now().strftime('%H:%M:%S')
    if kv:
        msg = f'{msg} ' + ' '.join(f'{k}={v}' for k,v in kv.items())
    print(f'[{ts}] {msg}', flush=True)


def load_spend():
    if SPEND_FILE.exists():
        try: return json.loads(SPEND_FILE.read_text())
        except: pass
    return {'date': datetime.now():%Y-%m-%d, 'cost_usd': 0.0, 'runs': []}


def record_spend(amount, label):
    s = load_spend()
    s['cost_usd'] = round(s.get('cost_usd', 0) + amount, 6)
    s['runs'].append({'ts': time.time(), 'amount': round(amount, 6), 'label': label})
    SPEND_FILE.write_text(json.dumps(s, indent=2))


def check_cap():
    return load_spend().get('cost_usd', 0) < DAILY_CAP


def strip_fences(s):
    s = s.strip()
    if s.startswith('```'):
        s = s.split('```', 1)[1]
        if s.startswith('json'): s = s[4:]
        s = s.split('```', 1)[0]
    return s.strip()


def safe_parse_json(s):
    s = strip_fences(s)
    try: return json.loads(s)
    except json.JSONDecodeError: pass
    in_string, escape, fixed = False, False, []
    for ch in s:
        if escape: escape = False
        elif ch == '\\': escape = True
        elif ch == '"': in_string = not in_string
        fixed.append(ch)
    if in_string:
        fixed.append('"')
        ob = fixed.count('{') - fixed.count('}')
        osq = fixed.count('[') - fixed.count(']')
        fixed.append('}' * ob + ']' * osq)
        try: return json.loads(''.join(fixed))
        except: pass
    return None


def call_llm(model, prompt, system='', max_tokens=4000, response_format=None,
             disable_thinking=True, retries=3):
    msgs = []
    if system: msgs.append({'role':'system','content':system})
    msgs.append({'role':'user','content':prompt})
    body = {'model': model, 'messages': msgs, 'max_tokens': max_tokens,
            'temperature': 0.4}
    if response_format: body['response_format'] = response_format
    if model == MODEL_CEO and disable_thinking:
        body['venice_parameters'] = {'disable_thinking': True}

    for attempt in range(retries):
        t0 = time.time()
        req = urllib.request.Request(f'{BASE}/chat/completions',
            data=json.dumps(body).encode(),
            headers={'Authorization': f'Bearer {KEY}', 'Content-Type':'application/json'},
            method='POST')
        try:
            r = urllib.request.urlopen(req, timeout=180)
            resp = json.loads(r.read())
            content = resp['choices'][0]['message'].get('content','') or ''
            usage = resp.get('usage', {})
            metrics['llm_in']  += usage.get('prompt_tokens', 0)
            metrics['llm_out'] += usage.get('completion_tokens', 0)
            if not content.strip() and attempt < retries - 1:
                metrics['retries'] += 1; time.sleep(2**attempt); continue
            return content, usage, time.time() - t0
        except urllib.error.HTTPError as e:
            metrics['errors'].append(f'LLM {e.code}: {e.read().decode()[:200]}')
            if e.code == 429:
                wait = 5 * (attempt + 1)
                log(f'429 rate limit, sleeping {wait}s')
                time.sleep(wait); continue
            if attempt < retries - 1: time.sleep(2**attempt); continue
            return '', {}, time.time() - t0
        except Exception as e:
            metrics['errors'].append(f'LLM: {e}')
            if attempt < retries - 1: time.sleep(2**attempt); continue
            return '', {}, time.time() - t0
    return '', {}, 0


def call_img(prompt, seed=None):
    body = {'model': MODEL_IMG, 'prompt': prompt,
            'negative_prompt': NEG, 'width': W, 'height': H,
            'hide_watermark': True}
    if seed is not None: body['seed'] = seed
    req = urllib.request.Request(f'{BASE}/image/generate',
        data=json.dumps(body).encode(),
        headers={'Authorization': f'Bearer {KEY}', 'Content-Type':'application/json'},
        method='POST')
    try:
        r = urllib.request.urlopen(req, timeout=180)
        resp = json.loads(r.read())
        if 'images' in resp and resp['images']:
            metrics['images'] += 1
            return base64.b64decode(resp['images'][0]), 0
    except urllib.error.HTTPError as e:
        metrics['errors'].append(f'IMG {e.code}: {e.read().decode()[:200]}')
        if e.code == 429:
            log('IMG 429 — sleeping 8s'); time.sleep(8)
    except Exception as e:
        metrics['errors'].append(f'IMG: {e}')
    return None, 0


def vision_qa(image_path, question, model=MODEL_VIS, max_tokens=400):
    """Run vision QA on a rendered slide. Returns the model's response."""
    with open(image_path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode()
    body = {'model': model,
        'messages':[{'role':'user','content':[
            {'type':'text','text': question},
            {'type':'image_url','image_url':{'url': f'data:image/png;base64,{b64}'}}]}],
        'max_tokens': max_tokens}
    req = urllib.request.Request(f'{BASE}/chat/completions',
        data=json.dumps(body).encode(),
        headers={'Authorization': f'Bearer {KEY}', 'Content-Type':'application/json'})
    try:
        r = urllib.request.urlopen(req, timeout=120)
        d = json.loads(r.read())
        metrics['vision_calls'] += 1
        return d['choices'][0]['message']['content']
    except urllib.error.HTTPError as e:
        return f'ERR {e.code}: {e.read().decode()[:200]}'
    except Exception as e:
        return f'ERR: {e}'


# ---- Step 1: Load article ----
def load_article(path):
    text = Path(path).read_text()
    log(f'Step 1: loaded {len(text)} chars from {path}')
    return text


# ---- Step 2: CEO outline ----
CEO_SYS = ("You are the CEO of AIPharmaXchange, a senior medical writer who "
           "publishes fair, balanced explainers for pharma/clinical professionals. "
           "No hype words. Output strict JSON only — no markdown fences, no preamble.")

CEO_OUTLINE = """Read this article and produce an 8-slide LinkedIn carousel outline.

ARTICLE:
{article}

SOURCE LABEL: {label}
SOURCE URL: {url}

SLIDE STRUCTURE (8 slides: 7 content + 1 Follow CTA):
1. Title card — article one-line hook, source + date, headline preview
2. What the system/topic does — core method / architecture / key concept
3. Headline result — primary metrics, MANDATORY chart (bar/line/timeline with 4+ data points)
4. Workflow fidelity — Instant vs Thinking (or: comparative mode/process), MANDATORY side-by-side comparison or 2x2 metric grid
5. Trend context — evolution or arc (3-4 stages), MANDATORY horizontal timeline
6. Limitations — ≥4 honest limits, 2x2 grid of cards
7. Implications + URL CTA — broader implications + visible article URL in a CTA box (NOT in footer)
8. Follow CTA — "THANKS FOR READING" + Join AIPharmaXchange on LinkedIn (channel growth)

AUDIENCE: pharma/clinical experts (R&D, regulatory, safety, medical, commercial) who may NOT be AI experts. Soften jargon. Use plain terms ("the AI assistant" beats "agentic RAG system"). One analogy per slide max.

For each slide return:
- slide_num (1-8)
- title (8-14 words, NO leading number like "1. ")
- bullets (3-5, each ≤18 words)
- key_claim (one line, no (p.X) citations)
- doi_or_url (the article URL: {url})

Return STRICT JSON: {{"slides": [...], "post_copy": "1500-1800 char LinkedIn post, fair/balance, no hype, pharma-expert voice"}}

Post copy rules:
- 1500-1800 chars
- Open with a hook that frames the question
- 3-4 short paragraphs summarizing the article fairly
- No hype words ("groundbreaking", "revolutionary", "amazing", "incredible")
- No exclamation marks
- End with the source URL on its own line
- Plain text only — no markdown"""


def ceo_outline(text, label, url):
    log('Step 2: CEO outline (8 slides + post copy)')
    prompt = CEO_OUTLINE.format(article=text[:40000], label=label, url=url)
    content, usage, elapsed = call_llm(MODEL_CEO, prompt, system=CEO_SYS,
                                       max_tokens=5500,
                                       response_format={'type':'json_object'})
    log(f'  CEO outline: {elapsed:.1f}s, '
        f'{usage.get("prompt_tokens",0)} in / {usage.get("completion_tokens",0)} out')
    spec = safe_parse_json(content)
    if not spec or not spec.get('slides'):
        log(f'  PARSE FAIL — first 500: {content[:500]}')
        return None
    log(f'  Parsed {len(spec["slides"])} slides, post_copy={len(spec.get("post_copy",""))} chars')
    return spec


# ---- Step 3: Image prompts ----
IMG_PROMPT_TEMPLATE = """You are designing an image-generation prompt for grok-imagine-image-quality (1024x1024 square) for a clinical infographic slide. Style: watercolor / painterly with editorial polish.

Slide outline:
Title: {title}
Bullets: {bullets}
Key claim: {claim}
URL: {url}
Slide number: {slide_num}

Write ONE single, complete prompt that the image model will use to generate this slide. Include:
- Visual layout (what goes where)
- Color palette in NATURAL LANGUAGE (teal, navy, cream, mint — NOT hex codes)
- All text strings quoted explicitly with "double quotes"
- Style: watercolor / painterly, editorial medical, soft brushwork, clean
- Background: cream / warm off-white

UNIVERSAL FOOTER (every slide): bottom-left small teal italic "AIPharmaXchange" brand mark. Bottom-right small teal italic "swipe →" cue. NO source URL, NO author name, NO DOI in the footer. NO journal branding (no Nature/NEJM/JAMA/Lancet logos).

SLIDE-SPECIFIC RULES:
- Slide 1 (title): hero composition, large title, ONE small icon, painterly watercolor texture
- Slide 3 (headline result): MUST include a clear bar/line chart with 4+ data points visible as data labels. Chart dominates 40%+ of canvas.
- Slide 4 (workflow fidelity): MUST include a side-by-side comparison or 2x2 metric grid.
- Slide 5 (trend context): MUST include a horizontal timeline or arc of 3-4 stages.
- Slide 6 (limitations): MUST be a 2x2 grid of 4 cards, each with a teal header bar and cream body. NO vertical list, NO single-column layout.
- Slide 7 (implications): vertical stack of 3-4 implication tiles with teal left border. Bottom CTA box with the article URL. URL goes in a body CTA box, NOT in the footer.
- Slide 8 (Follow CTA): centered painterly composition, "THANKS FOR READING" headline, "Join AIPharmaXchange on LinkedIn" subtext.

CRITICAL RULES:
- Quote every text string exactly with "double quotes"
- DO NOT use hex color codes (#XXXXXX) anywhere — describe colors naturally
- DO NOT include slide numbers (1., 2., etc.) in the rendered title
- DO NOT include author names anywhere on the slide
- DO NOT include any logo (Nature, NEJM, JAMA, Doximity logo) — only the AIPharmaXchange brand mark in footer

Return ONLY the prompt string. No JSON wrapper, no markdown fences, no preamble."""


def ceo_image_prompts(spec):
    log('Step 3: CEO image prompts (8 slides)')
    slides = []
    for slide in spec['slides'][:8]:
        sn = slide.get('slide_num', len(slides)+1)
        prompt = IMG_PROMPT_TEMPLATE.format(
            title=slide.get('title',''),
            bullets=json.dumps(slide.get('bullets',[])),
            claim=slide.get('key_claim',''),
            url=slide.get('doi_or_url',''),
            slide_num=sn,
        )
        content, usage, elapsed = call_llm(MODEL_CEO, prompt, max_tokens=1200)
        img_prompt = strip_fences(content).strip()
        title = re.sub(r'^\d+[\.\)]\s*', '', slide.get('title',''))
        log(f'  slide {sn}: prompt {len(img_prompt)} chars, {elapsed:.1f}s')
        slides.append({
            'slide_num': sn, 'title': title,
            'body': slide.get('bullets', []),
            'key_claim': slide.get('key_claim', ''),
            'doi_or_url': slide.get('doi_or_url', ''),
            'image_prompt': img_prompt,
        })
    return slides


# ---- Step 4: Render ----
def render_slides(slides, out_dir):
    log('Step 4: Render 8 slides')
    paths = []
    for slide in slides:
        sn = slide['slide_num']
        success = False
        for seed in [None, 42, 7, 99]:
            img_bytes, _ = call_img(slide['image_prompt'], seed=seed)
            if img_bytes:
                path = out_dir / f'slide_{sn:02d}.png'
                with open(path, 'wb') as f: f.write(img_bytes)
                paths.append(path)
                log(f'  slide {sn}: {len(img_bytes)//1024} KB (seed={seed})')
                success = True; break
            time.sleep(2)
        if not success:
            log(f'  slide {sn}: ALL ATTEMPTS FAILED')
    return paths


# ---- Step 5: Reviewers ----
REV_SYS = {
    'accuracy': "You are the Accuracy Reviewer for AIPharmaXchange. Verify every numerical/factual claim against the source. Be precise. Output strict JSON only.",
    'alignment': "You are the Alignment Reviewer for AIPharmaXchange. The slide image is the central deliverable. Verify the rendered PNG matches the spec: title text, bullet content, hierarchy, no clipping. Output strict JSON only.",
    'brand': "You are the Brand Reviewer for AIPharmaXchange. Palette: teal, navy, cream, mint. Style: watercolor / painterly editorial. No hype words. No journal logos. Footer must be 'AIPharmaXchange' + 'swipe →' only. Output strict JSON only.",
}

REV_PROMPTS = {
    'accuracy': """Verify every numerical/factual claim in this slide against the source article.

ARTICLE EXCERPT:
{paper}

SLIDE TITLE: {title}
SLIDE BODY: {body}
KEY CLAIM: {claim}

Return STRICT JSON: {{"score": N, "issues": [{{"text": "...", "verdict": "SUPPORTED|UNSUPPORTED|PARTIAL", "fix": "..."}}], "summary": "1-line"}}

Score 0-10. (We clamp to 10 in post-processing.)""",

    'alignment': """Check the rendered slide PNG at: {img_path}

SLIDE TITLE: {title}
SLIDE BODY: {body}

Verify in the rendered image:
- Title text rendered (correct spelling, no slide number prefix)
- Body bullets rendered (all of them visible)
- No text clipping or overflow
- Chart/diagram present (if spec requires one)
- Hierarchy: title > bullets > footer

Return STRICT JSON: {{"score": N, "title_ok": true/false, "bullets_ok": true/false, "chart_ok": true/false, "issues": ["..."], "summary": "1-line"}}""",

    'brand': """Audit the rendered slide PNG at: {img_path}

SLIDE TITLE: {title}
SLIDE BODY: {body}

Verify:
- Palette: teal + navy + cream + mint (NO pink/purple/red wash)
- Style: watercolor / painterly editorial medical
- No hype words, no exclamation marks
- Footer is ONLY 'AIPharmaXchange' (brand mark, bottom-left) + 'swipe →' (bottom-right)
- NO source URL/DOI/author/journal-logo in footer
- Tone: fair, balanced, clinical

Return STRICT JSON: {{"score": N, "tone_ok": true/false, "palette_ok": true/false, "footer_ok": true/false, "no_source_in_footer": true/false, "hype_words": ["..."], "issues": ["..."], "summary": "1-line"}}""",
}


def review_slides(slides, text, out_dir):
    log('Step 5: 3 reviewers per slide')
    reviews = []
    for slide in slides:
        sn = slide['slide_num']
        img_path = out_dir / f'slide_{sn:02d}.png'
        if not img_path.exists(): continue
        slide_review = {'slide_num': sn, 'title': slide['title'], 'reviewers': {}}
        log(f'  slide {sn}:')
        for rname, tmpl in REV_PROMPTS.items():
            prompt = tmpl.format(
                paper=text[:8000],
                title=slide['title'],
                body=json.dumps(slide['body']),
                claim=slide['key_claim'],
                img_path=str(img_path),
            )
            content, usage, elapsed = call_llm(MODEL_REV, prompt,
                system=REV_SYS[rname], max_tokens=700,
                response_format={'type':'json_object'},
                disable_thinking=False)
            metrics['reviewer_calls'] += 1
            data = safe_parse_json(content) or {'score': -1, 'parse_error': True,
                                                 'raw': content[:200]}
            # Clamp out-of-range scores (Pitfall #23)
            if isinstance(data.get('score'), (int, float)):
                data['score'] = min(data['score'], 10)
            slide_review['reviewers'][rname] = {
                'score': data.get('score', -1),
                'summary': data.get('summary', ''),
                'issues': data.get('issues', []),
            }
            log(f'    {rname}: {data.get("score","?")}/10, {elapsed:.1f}s')
        reviews.append(slide_review)
    return reviews


# ---- Step 6: Vision QA pass ----
VISION_QA_PROMPT = """Slide QA. Answer in <120 words:
(1) Title legible & correct (no "1." prefix)?
(2) All bullets/diagram visible?
(3) Footer ONLY "AIPharmaXchange" (bottom-left) + "swipe ->" (bottom-right) — NO URL/DOI/extra text?
(4) Any hallucinated journal logos, DOIs, URLs, or gibberish text?
(5) Palette teal/navy/cream (no pink/red wash)?
(6) Publishable as LinkedIn slide? Score 1-10."""

VISION_QA_PROMPT_CHART = """Slide QA. Answer in <120 words:
(1) Title legible?
(2) Clear bar/line chart with 4+ data points visible as labels?
(3) Footer ONLY "AIPharmaXchange" + "swipe ->"?
(4) Any hallucinated numbers, logos, DOIs?
(5) Palette teal/navy/cream?
(6) Publishable? Score 1-10."""


def vision_qa_pass(slides, out_dir):
    log('Step 6: Vision QA (qwen3-vl-235b-a22b)')
    qa = []
    for slide in slides:
        sn = slide['slide_num']
        img = out_dir / f'slide_{sn:02d}.png'
        if not img.exists(): continue
        # Use chart variant for slide 3, otherwise universal
        prompt = VISION_QA_PROMPT_CHART if sn == 3 else VISION_QA_PROMPT
        verdict = vision_qa(str(img), prompt)
        score_line = next((l for l in verdict.split('\n') if 'Score' in l or '/10' in l), '')
        log(f'  slide {sn}: {score_line.strip()}')
        qa.append({'slide_num': sn, 'verdict': verdict})
    return qa


# ---- Step 7: Assemble PDF + ZIP ----
def assemble(slides, slide_paths, reviews, qa, post_copy, out_dir):
    log('Step 7: Assemble PDF + ZIP')
    if not slide_paths: return None, None
    pdf_path = out_dir / 'carousel.pdf'
    # Use reportlab if available, else use PIL
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.utils import ImageReader
        c = canvas.Canvas(str(pdf_path), pagesize=(W, H))
        for sp in slide_paths:
            c.drawImage(ImageReader(str(sp)), 0, 0, W, H)
            c.showPage()
        c.save()
    except ImportError:
        from PIL import Image as PILImage
        imgs = [PILImage.open(p).convert('RGB') for p in slide_paths]
        imgs[0].save(pdf_path, save_all=True, append_images=imgs[1:])
    log(f'  PDF: {pdf_path.name} ({pdf_path.stat().st_size//1024} KB)')

    (out_dir / 'spec.json').write_text(json.dumps(
        {'slides': slides, 'post_copy': post_copy}, indent=2))
    (out_dir / 'reviews.json').write_text(json.dumps(reviews, indent=2))
    (out_dir / 'post_copy.md').write_text(post_copy)
    if qa:
        (out_dir / 'vision_qa.json').write_text(json.dumps(qa, indent=2))

    zip_path = out_dir / 'carousel.zip'
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for sp in slide_paths:
            zf.write(sp, sp.name)
        zf.write(out_dir / 'spec.json', 'spec.json')
        zf.write(out_dir / 'reviews.json', 'reviews.json')
        zf.write(out_dir / 'post_copy.md', 'post_copy.md')
        if qa: zf.write(out_dir / 'vision_qa.json', 'vision_qa.json')
    log(f'  ZIP: {zip_path.name} ({zip_path.stat().st_size//1024} KB)')
    return pdf_path, zip_path


# ---- Step 8: Deliver ----
def send_email(subject, body_md, attachments):
    msg = EmailMessage()
    msg['From'] = 'AI CEO AIPharmaXchange <vivgatesai@gmail.com>'
    msg['To'] = 'vivek@live.de'
    msg['Subject'] = subject
    msg['Date'] = formatdate(localtime=True)
    msg.set_content(body_md)
    for fpath in attachments:
        if not Path(fpath).exists(): continue
        ctype, _ = mimetypes.guess_type(fpath)
        if ctype is None: ctype = 'application/octet-stream'
        maintype, subtype = ctype.split('/', 1)
        with open(fpath, 'rb') as f:
            msg.add_attachment(f.read(), maintype=maintype, subtype=subtype,
                               filename=Path(fpath).name)
    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP('smtp.gmail.com', 587, timeout=60) as s:
            s.starttls(context=ctx)
            s.login('vivgatesai@gmail.com', 'lopp dmgq sddo snxy')
            s.send_message(msg)
        return True
    except Exception as e:
        log(f'email FAILED: {e}')
        return False


# ---- Main ----
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('article', help='Path to .txt article file')
    ap.add_argument('--source-label', default='Article',
                    help='Source label (e.g., "Doximity Technology Blog")')
    ap.add_argument('--source-url', required=True,
                    help='Source article URL')
    ap.add_argument('--out-dir', default=None,
                    help='Output directory (default: ./carousel_<ts>)')
    ap.add_argument('--skip-vision-qa', action='store_true',
                    help='Skip the qwen3-vl-235b vision QA pass (faster)')
    ap.add_argument('--no-email', action='store_true',
                    help='Skip email delivery')
    args = ap.parse_args()

    if not check_cap():
        log(f'DAILY CAP ${DAILY_CAP} REACHED — aborting'); sys.exit(1)

    out_dir = Path(args.out_dir or f'/tmp/carousel_{int(time.time())}')
    out_dir.mkdir(parents=True, exist_ok=True)

    t_start = time.time()
    text = load_article(args.article)
    spec = ceo_outline(text, args.source_label, args.source_url)
    if not spec: log('CEO outline failed — aborting'); sys.exit(1)
    slides = ceo_image_prompts(spec)
    slide_paths = render_slides(slides, out_dir)
    reviews = review_slides(slides, text, out_dir)
    qa = [] if args.skip_vision_qa else vision_qa_pass(slides, out_dir)
    pdf_path, zip_path = assemble(slides, slide_paths, reviews, qa,
                                   spec.get('post_copy',''), out_dir)

    cost_llm = (metrics['llm_in']/1e6)*0.20 + (metrics['llm_out']/1e6)*0.80
    cost_img = metrics['images'] * 0.05
    metrics['est_cost'] = cost_llm + cost_img
    metrics['wall_clock'] = time.time() - t_start
    record_spend(metrics['est_cost'], f'web_article:{Path(args.article).stem}')
    (out_dir / 'metrics.json').write_text(json.dumps(metrics, indent=2, default=str))

    # Deliver
    if pdf_path and not args.no_email:
        body = f"Carousel: {args.source_label}\n\n{spec.get('post_copy','')}\n\nSource: {args.source_url}"
        send_email(f'AIPharmaXchange Carousel — {args.source_label}',
                   body, [pdf_path, zip_path])

    print('\n' + '='*70)
    print('METRICS')
    print('='*70)
    print(f'LLM tokens: {metrics["llm_in"]:,} in / {metrics["llm_out"]:,} out')
    print(f'Reviewer calls: {metrics["reviewer_calls"]}')
    print(f'Vision QA calls: {metrics["vision_calls"]}')
    print(f'Images: {metrics["images"]}')
    print(f'Errors: {len(metrics["errors"])}')
    print(f'Cost: ${metrics["est_cost"]:.4f}')
    print(f'Wall-clock: {metrics["wall_clock"]:.0f}s')
    print(f'\nArtifacts: {out_dir}')


if __name__ == '__main__':
    main()
