# Paperclip carousel wrapper — operational notes (2026-06-27)

Live states for `~/.hermes/scripts/paperclip_wrap_carousel.py` after the OE
carousel (PMC12033599) run.

## Three invocation modes

| Mode | When to use |
|---|---|
| `--paper=<pdf>` | One PDF you want fully rendered + delivered. Wrapper calls `carousel_orchestration.py` from `~/.paperclip/workspaces/aipharmaxchange/`. Wall-time ~5–7 min, ~$0.40–0.50. |
| `--input-dir=<dir>` | Batch: scan the dir for unprocessed `*.pdf/*.html/*.htm/*.txt/*.md` files (anything already in `~/.paperclip/state/processed_carousels.txt` is skipped). |
| `--from-existing=<staged_dir>` | **Fast path.** Skip the orchestration step; reuse already-rendered artifacts in `staged_dir`. Use this when you've already generated slides via a custom pipeline (e.g. for non-PDF sources like web HTML articles, or when iterating prompts without re-rendering every time). |

## Expected layout for `--from-existing`

```
<staged_dir>/
├── slide_01.png ... slide_08.png      # PNG, not JPEG. 864x1152.
├── carousel.pdf                       # PDF combining all 8 PNGs (Pillow or reportlab)
├── carousel.zip                       # ZIP containing PNGs + post + spec + reviews
├── post_copy.txt                      # LinkedIn post copy (CEO-authored)
├── spec.json                          # spec with source.doi, source.journal, slides[]
├── reviews.json                       # list of per-slide reviewer scores
└── <source>.txt or .pdf               # used for issue title extraction; required
```

Venice image gen returns JPEG by default — convert with Pillow
during staging:

```python
from PIL import Image as PILImage
PILImage.open('slide.jpg').convert('RGB').save('slide.png', 'PNG', optimize=True)
```

The wrapper's `attach_assets()` globs `slide_*.png` and silently
ignores `*.jpg`. Stale files in `staged_dir` should be removed
explicitly because the wrapper does not clean the directory.

## Hardcoded legacy paper_path bug (pre-patch)

`~/.hermes/scripts/paperclip_wrap_carousel.py` line ~350 (in the
`if existing:` branch, before the inline fix) hardcodes:

```python
paper_path = f"/Users/vivgatesai/.hermes/cache/documents/doc_53b65edd5784_2503.06074v1.pdf"
```

This means `--from-existing=/tmp/mira_final/PMC12033599` will set
`paper_path` to that 2025 arXiv slug and the issue title will
become "Carousel — doc_53b65edd5784_2503.06074v1 — YYYY-MM-DD"
instead of the real paper. **Patch** by replacing the hardcode with
auto-detection:

```python
staged = Path(out_dir)
candidates = list(staged.glob('*.txt')) + list(staged.glob('*.pdf'))
paper_path = str(candidates[0]) if candidates else <fallback>
```

This patch was applied to `~/.hermes/scripts/paperclip_wrap_carousel.py`
on 2026-06-27 during the OE carousel delivery.

### Worked example (PMC12033599)

Source: `https://pmc.ncbi.nlm.nih.gov/articles/PMC12033599/`

```bash
# Stage the outputs (renames + JPEG->PNG conversion):
python3 /tmp/stage_outputs.py
# -> /tmp/mira_final/PMC12033599/  (slide_01.png ... carousel.zip etc.)

# Run the wrapper:
python3 ~/.hermes/scripts/paperclip_wrap_carousel.py \
  --from-existing=/tmp/mira_final/PMC12033599
```

## `--paper` mode env overrides (legacy behavior)

The wrapper sets these in the subprocess env when invoking
`carousel_orchestration.py`:

```python
env["VENICE_INFERENCE_KEY"] = "VENICE_INFERENCE_KEY_mlgJHlfrxLOzIP7C41rHfZltoX6a3WFe_j76g64uMr"
env["VENICE_MODEL"] = "google-gemma-4-31b-it"
env["CAROUSEL_NO_EMAIL"] = "1"
```

That key may be DIEM-capped or stale; if image generation fails
with HTTP 402 from the standalone `~/.paperclip/workspaces/...`
orchestrator, fall back to the working key in
`~/.hermes/config.yaml` (`VENICE_INFERENCE_KEY_c5diyY...`).
`--from-existing` mode does NOT invoke those subprocess env
overrides — only paper/input-dir mode routes through
`run_orchestration()`.

## Paperclip server health pre-check

Before running, sanity-check the Paperclip API:

```bash
lsof -i :3100                 # port listener
curl --max-time 3 http://127.0.0.1:3100/api/health
```

If connection refused: do not block on starting the server
(no CLI exposed). Continue with chat-side delivery (`MEDIA:`
attachments) and surface the cache miss to the user. Past OE
run (2026-06-27): wrapper cleanly hit `Connection refused` at
step 3/6 — issue creation never happened.

## Delivery daemon routing

The daemon at `~/.paperclip/delivery-daemon.py` reads
`~/.paperclip/delivery-config.json` to know which companies
to watch. Confirmed working config (post 2026-06-27 cleanup):

```json
{
  "pollIntervalSeconds": 15,
  "deliverStatuses": ["done", "closed"],
  "companies": [
    { "id": "a0289fcb-a853-4582-b64c-6ad062127e06",
      "name": "AIPharmaXchange", "to": ["vivek@live.de"], "cc": [] },
    { "id": "c9240459-d91e-415d-8f91-94510e827915",
      "name": "Paperclip Inc",   "to": ["vivek@live.de"], "cc": [] }
  ]
}
```

The v1 AIPharmaXchange company (`05f511f6-0e22-4d8a-ae55-fc17202944c4`)
was removed 2026-06-27 because all v1 generators
(daily/eod/weekly/newsletter + paperclip_wrap_daily/eod/weekly) are
archived/dead. Only the carousel pipeline on v2 is live.

## LinkedIn post copy char budget

Observed ranges from past runs:

| Run | Chars | Status |
|---|---|---|
| MIRA (2026-06-18) | ~1,700 | within 1,500–1,800 target ✓ |
| Doximity Ask (2026-06-24) | ~1,650 | within target ✓ |
| OE/PMC12033599 (2026-06-27) | 2,998 | **over budget**, contributed nothing extra; trim back to 1,800 |

Trim emergent over-length posts in pass 2 — split sentences
across paragraphs instead of cutting meaning.
