# Carousel Prompt Patterns — Boutique Agency Style

## Prompt Template (Flux 2 Max / GPT Image 2)

```
Professional infographic slide for LinkedIn carousel, boutique marketing agency style (Pentagram/Instrument). BRAND_COLOR background (#HEXCODE) with cream text elements. [TOPIC] — [SLIDE PURPOSE]. [DATA/CONTENT]. Clean typography, generous whitespace, subtle geometric patterns. Minimalist data visualization. Watercolor texture overlays. [ADDITIONAL STYLE NOTES]. No photos of people. 1024x1024.
```

## AIPharmaXchange Brand Standards

- **Brand color**: #00D4AA (teal)
- **Secondary**: #1A1A2E (dark navy)
- **Background**: cream/off-white (#FFF8F0) or dark navy
- **Typography**:
  - **Title**: bold **condensed** sans-serif (Druk Wide / Anton / Avenir Next Condensed style). NOT serif.
  - **Body**: humanist sans-serif (Inter / Helvetica)
  - **Tagline / brand mark**: italic serif
- **Visual style**: Watercolor texture, geometric patterns, boutique agency aesthetic
- **No photos of people** — use icons, data viz, and abstract elements instead

## Slide Types and Prompt Variations

### Title Slide
```
Professional infographic TITLE SLIDE for LinkedIn carousel, boutique marketing agency style. Teal #00D4AA background with cream #FFF8F0 bold typography. "[TITLE]" in large bold sans-serif. Subtitle: "[SUBTITLE]". Geometric accent lines. Watercolor texture overlay. Clean, premium, gallery-quality layout. No photos of people. 1024x1024.
```

### Data Slide (Chart/Comparison)
```
Professional infographic DATA SLIDE for LinkedIn carousel, boutique agency style. Dark navy #1A1A2E background with teal #00D4AA accents. "[HEADING]". Side-by-side comparison bars showing [MODEL_A] at [SCORE_A]% vs [MODEL_B] at [SCORE_B]%. Clean geometric bars, no grid lines. Cream text labels. Watercolor texture. Minimalist data visualization. 1024x1024.
```

### Key Statistic Slide
```
Professional infographic STAT SLIDE for LinkedIn carousel, boutique agency style. Cream #FFF8F0 background with teal #00D4AA geometric accents. Large bold number: "[STAT]%" in teal. Label: "[DESCRIPTION]". Subtle neural network pattern in background. Clean, modern typography. No photos of people. 1024x1024.
```

### Summary/Takeaway Slide
```
Professional infographic TAKEAWAY SLIDE for LinkedIn carousel, boutique agency style. Dark navy #1A1A2E background. Three key takeaway points with teal #00D4AA bullet icons: 1) [POINT_1] 2) [POINT_2] 3) [POINT_3]. Bold heading: "[HEADING]". Clean sans-serif typography. Geometric dividers. Watercolor accent. 1024x1024.
```

## Content Calendar JSON Schema

```json
[
  {
    "day": 1,
    "timeSlot": "Morning|Afternoon|Evening",
    "postType": "Statistic spotlight|Quote graphic|Data comparison carousel|Infographic summary|Expert commentary|Poll question|Myth busting|Case study|Behind the scenes|Research highlight|Thought leadership|UGC prompt|Quick tip|Industry news|Video snippet|Slide deck preview|FAQ|Key takeaway|Controversial take|Resource roundup|Call for collaboration",
    "hook": "Opening line / hook",
    "bullets": ["Point 1", "Point 2", "Point 3"],
    "visualDesc": "Description of the visual to generate",
    "hashtags": ["#tag1", "#tag2"],
    "cta": "Call to action"
  }
]
```

## Post Type Distribution (21 posts / 7 days)

Recommended mix per day:
- **Morning**: Data-driven (stat, research highlight, infographic)
- **Afternoon**: Engagement (poll, expert commentary, thought leadership)
- **Evening**: Community (FAQ, UGC prompt, resource roundup, collaboration)

## Generation Workflow

1. Generate all carousel slides with `flux-2-max` (fast ~30s each)
2. Review output quality — identify the hero/key slide
3. Re-render hero slide with `gpt-image-2` (slow ~225s, best text rendering)
4. Save all to `visuals/` with descriptive filenames:
   - `carousel_1_title.png`
   - `carousel_2_[topic].png`
   - `hero_[concept].png`
