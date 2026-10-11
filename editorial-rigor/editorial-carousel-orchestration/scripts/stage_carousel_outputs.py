#!/usr/bin/env python3
"""
Stage already-rendered carousel artifacts into the layout that
`paperclip_wrap_carousel.py --from-existing=<dir>` expects, then push
through Paperclip + daemon delivery without re-running the full pipeline.

Use cases:
- Rendered slides in one place (e.g. `~/state/aipharmaxchange/<date>/slides/`),
  want to deliver without re-rendering
- Hand-tuned slides you'd like to push to Paperclip + email
- Outputs from a non-standard orchestrator (custom render script, manual
  touches) that need to flow through the canonical delivery path

Expected layout produced in <stage_dir>:
    carousel.pdf       # 8-slide portrait PDF
    carousel.zip       # auto-built by paperclip_wrap, NOT staged
    post_copy.txt      # LinkedIn post copy
    spec.json          # full spec (slides, source metadata, etc.)
    reviews.json       # per-slide reviewer scores (3 reviewers)
    slide_01.png ... slide_08.png   # 864x1152 PNGs
    <slug>.txt or <slug>.pdf        # source paper (for title extraction)

Usage:
    python3 stage_carousel_outputs.py \
        --slides-dir /Users/.../state/aipharmaxchange/2026-06-27/slides \
        --pdf       /Users/.../PMC12033599_OE_carousel.pdf \
        --zip       /Users/.../PMC12033599_OE_carousel.zip \
        --post-copy /Users/.../linkedin_post.md \
        --spec      /Users/.../spec.json \
        --reviews   /Users/.../pipeline_report.json \
        --source    /Users/.../article.txt \
        --out       /tmp/mira_final/PMC12033599

    # Then:
    python3 /Users/vivgatesai/.hermes/scripts/paperclip_wrap_carousel.py \
        --from-existing=/tmp/mira_final/PMC12033599
"""
import argparse, base64, json, shutil, sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slides-dir", required=True,
                    help="dir with slide_NN.jpg or slide_NN.png files")
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--zip", required=True)
    ap.add_argument("--post-copy", required=True,
                    help=".md or .txt; will be renamed to post_copy.txt")
    ap.add_argument("--spec", required=True)
    ap.add_argument("--reviews", required=True,
                    help="reviews.json OR a pipeline_report.json with "
                         "'reviews' / 'vision_qa' keys — converted automatically")
    ap.add_argument("--source", required=True,
                    help="source paper (.txt or .pdf); used by wrapper "
                         "for title extraction")
    ap.add_argument("--out", required=True,
                    help="stage directory — basename becomes the slug")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    src_slides = Path(args.slides_dir)

    # 1. Slide PNGs (re-encode JPG → PNG so the wrapper's glob matches)
    try:
        from PIL import Image
    except ImportError:
        sys.exit("Pillow required: pip install Pillow")
    slide_paths = sorted(
        list(src_slides.glob("slide_*.[jpJP][npNP][egEG]")),
        key=lambda p: int(p.stem.split('_')[1])
    )
    if not slide_paths:
        sys.exit(f"No slide_*.jpg/png in {src_slides}")
    if len(slide_paths) != 8:
        print(f"  WARN: only {len(slide_paths)} slides (expected 8)",
              file=sys.stderr)
    for sp in slide_paths:
        n = int(sp.stem.split('_')[1])
        dp = out / f"slide_{n:02d}.png"
        Image.open(sp).convert('RGB').save(dp, 'PNG', optimize=True)
        print(f"  {sp.name} -> {dp.name} ({dp.stat().st_size//1024} KB)")

    # 2. PDF + ZIP
    shutil.copy(args.pdf, out / "carousel.pdf")
    shutil.copy(args.zip, out / "carousel.zip")
    print(f"  PDF + ZIP copied")

    # 3. Post copy (renamed)
    shutil.copy(args.post_copy, out / "post_copy.txt")

    # 4. Spec
    shutil.copy(args.spec, out / "spec.json")

    # 5. Reviews — adapt if it's a pipeline_report.json
    rev_src = Path(args.reviews)
    rev = json.loads(rev_src.read_text())
    if "vision_qa" in rev and "reviews" in rev:
        # it's a pipeline_report.json — extract + adapt
        adapted = []
        for sn_key, r in rev["reviews"].items():
            sn = int(sn_key)
            qa = rev["vision_qa"].get(sn_key, {})
            adapted.append({
                "slide_num": sn,
                "reviewers": {
                    "accuracy": {"score": max(0, min(10, r.get("accuracy", 0))),
                                 "summary": r.get("summary", {}).get("accuracy", "")},
                    "alignment": {"score": max(0, min(10, r.get("alignment", 0))),
                                  "summary": r.get("summary", {}).get("alignment", "")},
                    "brand":     {"score": max(0, min(10, r.get("brand", 0))),
                                  "summary": r.get("summary", {}).get("brand", "")},
                    "vision_qa": {"score": max(0, min(10, qa.get("overall_score", qa.get("score", 0)))),
                                  "summary": qa.get("summary", ""),
                                  "issues": qa.get("issues", []),
                                  "visible_text_count": len(qa.get("visible_text", [])),
                                  "footer_ok": qa.get("footer_ok", True),
                                  "swipe_cue_ok": qa.get("swipe_cue_ok", True)},
                },
            })
        (out / "reviews.json").write_text(json.dumps(adapted, indent=2, default=str))
        print(f"  reviews.json rebuilt from pipeline_report.json "
              f"({len(adapted)} slides)")
    else:
        shutil.copy(args.reviews, out / "reviews.json")
        print(f"  reviews.json copied")

    # 6. Source paper (txt or pdf — wrapper auto-discovers)
    src = Path(args.source)
    shutil.copy(src, out / src.name)
    print(f"  source: {src.name}")

    print(f"\nStaged at: {out}")
    print(f"Files: {sorted(p.name for p in out.iterdir())}")
    print(f"\nNext step:\n"
          f"  python3 /Users/vivgatesai/.hermes/scripts/paperclip_wrap_carousel.py "
          f"--from-existing={out}")


if __name__ == '__main__':
    main()
