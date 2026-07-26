# Blending AI-Generated Illustrations into Editorial Layouts

## Problem

AI-generated images (especially from Venice/Flux) often have a solid background color that does not exactly match the page background. When placed in a split-layout hero, a visible hard edge appears between the illustration and the text area — even if both are "cream" or "off-white." The slight color temperature difference (warmer vs cooler, or presence of paper texture vs flat CSS color) makes the seam obvious.

## Solution: Three-Layer Blend Stack

Use three complementary techniques together. Any single layer alone is usually insufficient.

### Layer 1: CSS `mask-image` on the image itself

Fade the actual pixel edge of the image so it dissolves into transparency. The container's background color shows through the transparent areas, matching the page exactly.

```css
.hero-bg-illustration {
    position: absolute;
    top: 0;
    right: -5%;        /* bleed off-screen so the fade is invisible */
    width: 75%;         /* wider than 50% so the mask fade zone is generous */
    height: 100%;
    z-index: 1;
    background-color: var(--page-cream);  /* matches page bg exactly */
}

.hero-bg-illustration img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    object-position: right 35%;  /* anchor the focal point away from the fade edge */
    
    /* Fade the image's own left edge */
    -webkit-mask-image: linear-gradient(
        to right,
        transparent 0%,
        rgba(0,0,0,0.15) 25%,   /* barely visible */
        rgba(0,0,0,0.5) 40%,    /* halfway dissolved */
        rgba(0,0,0,0.85) 52%,   /* almost solid */
        black 65%,              /* fully opaque */
        black 100%
    );
    mask-image: linear-gradient(
        to right,
        transparent 0%,
        rgba(0,0,0,0.15) 25%,
        rgba(0,0,0,0.5) 40%,
        rgba(0,0,0,0.85) 52%,
        black 65%,
        black 100%
    );
}
```

**Key points:**
- The `mask-image` is applied to the `img` element itself, not a parent div
- The container's `background-color` must match the page background exactly — this is what shows through the transparent mask areas
- `right: -5%` bleeds the image off-screen so the fade zone never looks like it's "inside" the layout
- `object-position: right 35%` keeps the focal point (e.g., a face, a plant) away from the masked edge

### Layer 2: Warm color overlay to harmonize tones

Even with a mask, the image's cream background may have a different color temperature than the CSS cream. A subtle `mix-blend-mode: multiply` overlay tints the image toward the page color.

```css
.hero-bg-illustration::after {
    content: '';
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    background: rgba(245, 241, 232, 0.25);  /* page cream at low opacity */
    mix-blend-mode: multiply;               /* tints the image toward the overlay color */
    pointer-events: none;
}
```

**Key point:** `mix-blend-mode: multiply` darkens the image where the overlay is darker and lightens where it's lighter. A warm cream overlay pulls a cool-white image background toward warm cream. Adjust opacity 0.15–0.35 depending on the image.

### Layer 3: Organic radial gradient overlay

A second, softer transition zone on top of everything. This catches any remaining hard edge and adds an editorial "vignette" feel.

```css
.hero-blend-overlay {
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    z-index: 2;
    pointer-events: none;
    background: radial-gradient(
        ellipse 90% 110% at 45% 50%,
        var(--color-cream) 0%,
        var(--color-cream) 30%,
        rgba(245, 241, 232, 0.92) 40%,
        rgba(245, 241, 232, 0.6) 52%,
        rgba(245, 241, 232, 0.25) 62%,
        transparent 75%
    );
}
```

**Key point:** The radial gradient is centered slightly right of the content zone (45% instead of 30%) so the fade doesn't darken the text area. The ellipse shape (90% width × 110% height) creates a natural organic feel, not a circular spotlight.

### Full stacked structure (HTML)

```html
<section class="hero-section">
    <!-- Layer 1: Image + mask -->
    <div class="hero-bg-illustration">
        <img src="images/hero-illustration.png" alt="...">
    </div>
    <!-- Layer 2: Color overlay (via ::after on .hero-bg-illustration) -->
    <!-- Layer 3: Radial gradient transition -->
    <div class="hero-blend-overlay"></div>
    <!-- Content sits above all layers -->
    <div class="hero-content">
        ...
    </div>
</section>
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Image looks "cut off" with a visible line | Mask gradient is too steep (transparent → black too quickly) | Widen the transition: `transparent 0%, rgba(0,0,0,0.15) 25%, rgba(0,0,0,0.5) 40%, rgba(0,0,0,0.85) 55%, black 70%` |
| Image edge is too faded, content area looks empty | Mask starts fading too early | Shift the mask gradient right: `transparent 10%, rgba(0,0,0,0.15) 30%...` |
| Image has a checkerboard pattern where it should be transparent | Container has no background color | Add `background-color: var(--page-cream)` to `.hero-bg-illustration` |
| Text over the image is hard to read | Radial gradient doesn't extend far enough left | Move gradient center left: `at 35% 50%` instead of `45% 50%` |
| Image color temperature doesn't match page | Image has warm cream, page has cool white (or vice versa) | Adjust the `::after` overlay color and opacity. Try a different blend mode: `overlay` or `soft-light` instead of `multiply` |

## Browser Support

- `mask-image`: Chrome/Edge 120+, Safari 15.4+, Firefox 53+ (with `-webkit-` prefix)
- `mix-blend-mode`: All modern browsers (IE11 excluded, which is irrelevant for 2026)
- Fallback for older browsers: the image still displays, just without the fade. The layout remains functional.

## Cost Impact

None — this is pure CSS. No additional image generation needed. The technique is particularly valuable for AI-generated images where re-generating with a transparent background would cost another $0.08 and may not produce the desired artistic texture.
