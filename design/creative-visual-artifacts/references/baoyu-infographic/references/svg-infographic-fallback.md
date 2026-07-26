# SVG infographic fallback for map-heavy or text-heavy outputs

Use this when the normal image-generation path is unavailable (for example, `FAL_KEY environment variable not set`) or when the deliverable needs precise, readable labels such as maps, schedules, captions, or route cards.

## Trigger signals

- `image_generate` fails due to missing provider credentials or environment variables.
- The user asks for an infographic with a map, itinerary, route, or dense explanatory labels.
- A generated image is likely to hallucinate geography or produce unreadable text.

## Workflow

1. Gather facts and coordinates with the relevant research/maps tools.
2. Create a hand-authored SVG with:
   - explicit canvas size and `viewBox`
   - title/subtitle
   - simplified map or diagram, clearly labeled `not to scale` if applicable
   - large numbered markers instead of tiny paragraphs on the map
   - a side panel for explanations, timings, or key facts
   - generous padding around text blocks
3. Rasterize SVG to PNG:

```bash
npx --yes @resvg/resvg-js-cli input.svg output.png
```

4. Verify output:

```bash
file output.png
```

Then use `vision_analyze` to check: title readability, label cropping, text density, route clarity, and whether side panels are cut off.

5. If cropping/crowding is found, widen the canvas or shorten labels, regenerate, and re-check.

## Pitfalls

- Do not use raw `read_file` content as SVG source if the tool adds line-number prefixes; it can corrupt XML. If necessary, strip prefixes like `     1|` before rasterizing.
- Avoid paragraph text inside the map area. Use numbered pins and put explanations in a side panel.
- For walking-tour maps, simplify geography and disclose `Simplified, not to scale`; provide a Google Maps link separately for live navigation.
- Prefer a wider landscape canvas (e.g. 2400×1350) for route maps plus schedule sidebars; 16:9 can be too tight for dense labels.
- For phone-first delivery of walking tours, use a portrait/mobile canvas (e.g. ~1800×3000) with the map on top and checklist cards below. Landscape map + sidebar layouts often look good on desktop but fail on Telegram/phone due to small text, cropped panels, and crowded sidebars.
- After any QA failure, fix the actual exported SVG canvas dimensions (`width`, `height`, and `viewBox`) as well as element positions. A common bug is adding checklist items below the canvas height, which silently crops the final cards in the PNG.
- Keep map labels short: put only marker codes (`J1`, `K3`, `G1`) on dense clusters, then put full names/descriptions in a separate checklist. This is more legible than trying to label every pin directly on the map.
