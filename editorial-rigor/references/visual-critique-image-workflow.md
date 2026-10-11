# Visual Critique Slide Workflow (June 2026)

How to render a critique / limitations slide where the text is dense
(5+ cards with title + body) using an image model — not a UI mockup
tool. Empirically derived from the AIPharmaXchange "5 Limitations of
the Study" carousel.

## The core pattern

For text-heavy critique slides, **push the image model to render the
text itself** rather than rendering the visual and overlaying text with
Pillow. This was a hard-won lesson: the user explicitly preferred the
image-model-rendered version over a Pillow-overlaid version because
the painterly aesthetic was preserved, while the Pillow version looked
like a UI mockup.

**The image model to use:** `grok-imagine-image-quality` (Venice,
called "grok sota"). It renders text significantly better than
`flux-2-max` and `gpt-image-2` for the kinds of dense cards used in
critique slides.

**Aspect ratio:** 3:4 portrait (864x1152). Match the rest of the
carousel series so they look like siblings. NOT square (1024x1024)
unless the user explicitly wants that.

## Prompt construction (the recipe that worked)

The prompt that nailed it had four explicit blocks. Be specific.

```text
A 3:4 portrait editorial infographic with [5] numbered cards
arranged vertically. Style: soft watercolor illustration, painterly,
organic edges, muted saturation, with subtle paper-grain texture
throughout the background.

Palette: teal #2BA39B, mint #8FD3B6, navy #1E3A5F, cream #F5F0E1.
Background is cream with teal watercolor wash splashes.

Title at the top in bold navy serif, all caps, ~30pt:
  "5 LIMITATIONS OF THE STUDY"

Subtitle just below in italic teal serif, ~14pt:
  "What the [paper name] missed"

For each card, a thin teal horizontal divider, then:
  Card [N]: [HEADING IN QUOTES]
  Body text in dark navy sans-serif, ~10pt:
    "[One-sentence body explanation, max 18 words]"

Add a small simple line-art icon at the left of each card heading
(heart-pulse, question-mark, ruler, clipboard, brain — one per card).

Bottom footer: italic navy "[year] [venue]"  |  bold teal
"AIPharmaXchange"  |  italic navy "swipe →"

The text MUST be exactly as shown above, no garbled words, no
rephrasing. Use explicit quotation marks to anchor each text block.
```

The four things that made the model actually render the text right:

1. **All caps for the title** — the model handles all-caps better
   than mixed-case for short titles.
2. **Quoted strings in the prompt** — anchor the exact text by
   wrapping it in `"double quotes"` inside the prompt body. The model
   will preserve quoted text faithfully.
3. **Explicit word count per body** ("max 18 words") — prevents the
   model from over-writing the body and eating the next card.
4. **"No garbled words, no rephrasing"** — the model will try to
   "improve" the text; this instruction stops it.

## What does NOT work

- **`flux-2-max`** for text rendering — mangles body copy, runs words
  together, drops characters. Pass on it for text-heavy slides.
- **Pillow overlay on a generated background** — works but the user
  read it as a UI mockup, not a watercolor. Breaks the carousel
  aesthetic.
- **Pushing the model to render the EXACT brand color as a hex
  code in the brand mark** — the model will include the literal
  `#00D4AA` text in the corner. Don't put hex codes near text
  strings you want rendered.
- **Wide aspect ratios (16:9) for critique slides** — 3:4 portrait
  works because the slide is read top-to-bottom (intro → 5 cards →
  CTA). 16:9 would force either 2-3 columns (cramped) or larger
  fonts (inconsistent with carousel siblings).

## The Pillow fallback (only when image model fails twice)

If the image model genuinely cannot render the text correctly after
2-3 iterations (each iteration takes ~30-60s + paperclip round-trip),
fall back to:

1. Generate a clean watercolor BACKGROUND ONLY with the image model
   (no text in the prompt).
2. Use Pillow to overlay the text using **Avenir Next Condensed
   Bold** for titles and **Avenir Next** (or **Lato** if Avenir is
   unavailable) for body. Both are on macOS by default.
3. **Surgical fix only** — don't try to blend Pillow text with paper
   texture; cover the text area with a flat cream rectangle first,
   then redraw the text on top. Acceptable in the corner brand mark,
   NOT acceptable for the main content cards (the eye will catch the
   flat patch).

The Pillow fallback is the LAST resort, used ~5% of the time. The
default is: iterate the prompt until the model gets it right.

## Iterating the prompt

The model will get it close on the first try. Issues to watch for:

| Symptom | Fix in next iteration |
|---|---|
| Body text wraps weirdly or runs off card | Reduce body word count, increase card height |
| Title rendered as italic when you wanted bold | Add "bold" / "black weight" to title description |
| Missing card or duplicate card | Be explicit about "5 cards" and number them 1, 2, 3, 4, 5 |
| Random icon appears that you didn't ask for | Say "no extra illustrations" in the prompt |
| Brand mark has the wrong word | Quote the brand name in the prompt: `"AIPharmaXchange"` |
| Hex code appears as text | Move the hex code out of any quoted text region |

## The reusable palette prompt block

Drop this into any critique-slide prompt verbatim:

```text
Palette: teal #2BA39B, mint #8FD3B6, navy #1E3A5F, cream #F5F0E1.
Background: cream with teal watercolor wash splashes and paper-grain
texture. Style: painterly, organic, hand-illustrated, not flat UI.
```

## Sending the result for review

The image goes to `vivek@live.de` from `AI CEO AIPharmaXchange
<vivgatesai@gmail.com>` via:

- **Production path (after wrapper migration):** create a Paperclip
  issue, attach the image, mark done, the delivery daemon emails.
  See `paperclip-delivery-daemon` skill.
- **Ad-hoc path (one-off, no cron):** Python smtplib direct. Use
  subject prefix "Agni Agent Report — [topic]". Don't CC anyone.
  See `send-gmail-attachment` skill.

The user expects the proactive email without prompting — this was a
correction the user made in June 2026 ("you should have sent this
to the vivek@live.de email for human review"). Send after every
critique slide is ready, not after a checklist of "should I send
this."
