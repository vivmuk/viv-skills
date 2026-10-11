# Carousel Prompt Templates

Reusable prompt skeletons for the 7 standard slide types. Copy, fill in the data, send to the appropriate Venice model.

**Universal preamble** (prepend to every prompt):

> A clinical infographic slide (3:4 portrait, 864x1152 pixels) for AIPharmaXchange, a medical publication. Style: editorial medical, clean, professional. Background: cream #F5F0E1. Primary colors: teal #2BA39B and navy #1E3A5F. Secondary: mint #8FD3B6. No pink, no grey-green. No decorative watercolor. Typography: clean sans-serif, all text legible.

**Universal footer** (append to every prompt):

> Footer text in small teal italic at bottom: "[paper citation]". Brand wordmark "AIPharmaXchange" in top-left corner, slide indicator "Slide N/7" in top-right.

---

## Slide 1: Title Card

**Model:** `qwen-image-2`

**Prompt body:**

> Centered title in large bold navy text: "[PAPER TITLE]".
>
> Below title, 3-4 bullet points in dark navy, teal dot markers, each ≤15 words:
> - [bullet 1: lead author + institution]
> - [bullet 2: one-line finding/hook]
> - [bullet 3: one-line method]
> - [bullet 4: DOI]
>
> A small visual element in the center: a single clean icon representing the topic (e.g., hospital building + circuit board for clinical AI, pill bottle for drug study, microscope for basic science). Style: flat minimal vector, teal and navy only.
>
> Footer text in teal small print: "[one-line key claim with page citation]".

---

## Slide 2: Process / Method Diagram

**Model:** `qwen-image-2`

**Prompt body:**

> Subtitle in bold navy: "[METHOD NAME]".
>
> Below, a horizontal flow diagram with 5 nodes connected by arrows, left to right. Each node has a teal circle with a white icon inside, and a label below in navy:
> 1. "[step 1]" — [icon description]
> 2. "[step 2]" — [icon description]
> 3. "[step 3]" — [icon description]
> 4. "[step 4]" — [icon description]
> 5. "[step 5]" — [icon description]
>
> The connecting arrows are navy. Background: cream. No additional decoration.
>
> Footer text in teal small print: "[method citation]".

---

## Slide 3: Headline Results Chart

**Model:** `recraft-v4-pro`

**Prompt body:**

> A clean grouped bar chart on cream background.
>
> Title in bold navy: "[STUDY NAME]: [X.X%] vs [Y.Y%] [METRIC]".
>
> Bar chart with [N] groups on x-axis, two bars per group (teal and navy).
>
> Group labels (x-axis): [condition 1], [condition 2], ..., [condition N]
>
> Bar values (printed at end of each bar):
> - [condition 1]: teal [X.X]%, navy [Y.Y]%
> - [condition 2]: teal [X.X]%, navy [Y.Y]%
> - ... (all values)
>
> Y-axis labeled "[METRIC] (%)" with ticks at 60, 70, 80, 90, 100.
>
> Legend at bottom: teal square labeled "[GROUP A]", navy square labeled "[GROUP B]".
>
> Footer text in small teal print: "n=[sample size] | [statistical test] p[value] | [venue, year]".

**Critical reminder:** values in the prompt must be EXACT and match the source paper. Models like `recraft-v4-pro` will fabricate values that aren't quoted — the accuracy reviewer must verify.

---

## Slide 4: Secondary Metrics / Coverage

**Model:** `qwen-image-2`

**Prompt body:**

> Subtitle in bold navy: "[SECONDARY METRIC TITLE]".
>
> 4 metric tiles in a 2×2 grid. Each tile has a teal border, cream background, large navy number on top, small label below.
>
> Tile 1 (top-left): "[XX.X]%" — "[label 1, ≤4 words]"
> Tile 2 (top-right): "[XX.X]%" — "[label 2, ≤4 words]"
> Tile 3 (bottom-left): "[XX.X]%" — "[label 3, ≤4 words]"
> Tile 4 (bottom-right): "[XX.X]%" — "[label 4, ≤4 words]"
>
> Below the tiles, 2-3 bullet points in navy with teal dot markers summarizing context for the metrics.
>
> Footer text in teal small print: "[secondary metrics citation]".

---

## Slide 5: Trend Context / Timeline

**Model:** `qwen-image-2`

**Prompt body:**

> Subtitle in bold navy: "[TREND TITLE]: [Past paradigm] to [New paradigm]".
>
> A horizontal timeline with 4 labeled stages, left to right, connected by navy arrows. Each stage has a small icon above the label.
>
> Stage 1 (leftmost, faded/translucent): "[system 1]" — "[one-line description]"
> Stage 2: "[system 2]" — "[one-line description]"
> Stage 3: "[system 3]" — "[one-line description]"
> Stage 4 (rightmost, bold/highlighted with teal glow): "[system 4, current/future]" — "[one-line description]"
>
> Below the timeline, 2-3 bullets in navy explaining the progression.
>
> Footer text in teal small print: "[trend context citation]".

---

## Slide 6: Honest Limitations (Fair/Balance)

**Model:** `qwen-image-2`

**Prompt body:**

> Title in bold navy: "[N] Honest Limits of the [STUDY]".
>
> A 2×2 grid of 4 cards. Each card has a teal header bar with white bold text, and a cream body with navy text.
>
> Card 1 (top-left):
>   Header: "[limit 1, 2-3 words]"
>   Body: "[one-sentence honest description, ≤20 words]"
>
> Card 2 (top-right):
>   Header: "[limit 2, 2-3 words]"
>   Body: "[one-sentence honest description, ≤20 words]"
>
> Card 3 (bottom-left):
>   Header: "[limit 3, 2-3 words]"
>   Body: "[one-sentence honest description, ≤20 words]"
>
> Card 4 (bottom-right):
>   Header: "[limit 4, 2-3 words]"
>   Body: "[one-sentence honest description, ≤20 words]"
>
> Each card may have a small icon in the top-right corner of the header (e.g., laptop, database, clock, microscope).
>
> Footer text in teal small print: "[authors' own caveat or 'Authors call for prospective trials' with citation]".

**Critical reminder:** the limitations MUST be honest and defensible. Per the editorial-rigor skill, no speculative claims. If the paper doesn't acknowledge a limitation, don't fabricate it.

---

## Slide 7: Implications + CTA

**Model:** `qwen-image-2`

**Prompt body:**

> Title in bold navy: "[IMPLICATIONS TITLE]".
>
> 3-4 implication tiles stacked vertically. Each tile has a teal left border, cream background, navy heading on top, navy body text below.
>
> Tile 1: "[implication 1 heading, ≤6 words]" — "[body, ≤20 words]"
> Tile 2: "[implication 2 heading, ≤6 words]" — "[body, ≤20 words]"
> Tile 3: "[implication 3 heading, ≤6 words]" — "[body, ≤20 words]"
> Tile 4: "[implication 4 heading, ≤6 words]" — "[body, ≤20 words]"
>
> Below tiles, a CTA box with teal background, white text: "Read the full study: [DOI URL]".
>
> Footer text in navy small print: "AIPharmaXchange | [date]".
