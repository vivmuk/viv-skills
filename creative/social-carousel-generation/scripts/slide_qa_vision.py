#!/usr/bin/env python3
"""
Slide Vision QA — reusable vision QA tool for rendered carousel PNGs.

Calls Venice's qwen3-vl-235b-a22b (or another vision-capable model)
to verify a rendered slide matches the spec.

Usage:
    python3 slide_qa_vision.py <image_path> [question]

If no question is given, uses a universal slide QA prompt.

Examples:
    # Default universal QA
    python3 slide_qa_vision.py output/doximity_ask/slide_01.png

    # Custom question (URL leak audit for slide 7)
    python3 slide_qa_vision.py output/doximity_ask/slide_07.png \\
        "List every URL on the slide verbatim with position and authenticity."

    # Chart slide
    python3 slide_qa_vision.py output/doximity_ask/slide_03.png \\
        "Slide QA. Is there a clear bar chart with 6 data points visible? Score 1-10."

    # Batch QA all slides in a dir
    python3 slide_qa_vision.py output/doximity_ask/slide_01.png
    python3 slide_qa_vision.py output/doximity_ask/slide_02.png
    ...
"""
import sys, os, json, base64, urllib.request, urllib.error
from pathlib import Path

KEY  = os.environ.get('VENICE_KEY',
       'VENICE_INFERENCE_KEY_c5diyYrdrrKLbenzadX4CP7CueQN--urN3zxUYEXNE')
BASE = 'https://api.venice.ai/api/v1'
MODEL = 'qwen3-vl-235b-a22b'

DEFAULT_PROMPT = """Slide QA. Answer in <120 words:
(1) Title legible & correct (no "1." prefix)?
(2) All bullets/diagram visible?
(3) Footer ONLY "AIPharmaXchange" (bottom-left) + "swipe ->" (bottom-right) — NO URL/DOI/extra text?
(4) Any hallucinated journal logos, DOIs, URLs, or gibberish text?
(5) Palette teal/navy/cream (no pink/red wash)?
(6) Publishable as LinkedIn slide? Score 1-10."""


def vision_qa(image_path: str, question: str = DEFAULT_PROMPT,
              model: str = MODEL, max_tokens: int = 500) -> str:
    """Run vision QA on an image. Returns the model's text response."""
    p = Path(image_path)
    if not p.exists():
        return f'ERR: file not found: {image_path}'
    with open(p, 'rb') as f:
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
        with urllib.request.urlopen(req, timeout=120) as r:
            d = json.loads(r.read())
        return d['choices'][0]['message']['content']
    except urllib.error.HTTPError as e:
        return f'ERR {e.code}: {e.read().decode()[:300]}'
    except Exception as e:
        return f'ERR: {e}'


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    image = sys.argv[1]
    question = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_PROMPT

    print(f'Image: {image}')
    print(f'Model: {MODEL}')
    print(f'Question: {question[:80]}...' if len(question) > 80 else f'Question: {question}')
    print('-' * 70)
    print(vision_qa(image, question))


if __name__ == '__main__':
    main()
