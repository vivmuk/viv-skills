# Brand Register

When **design IS the product**: brand sites, landing pages, marketing surfaces, campaign pages, portfolios, long-form content, about pages, event pages. The deliverable is the design itself; a visitor's impression is the thing being made.

The register spans every genre — a tech brand (Stripe / Linear / Vercel), a luxury brand (a hotel / fashion house), a consumer product (a restaurant / travel site / CPG page), a creative studio, an agency portfolio, a band's album page. They share the stance (*communicate, not transact*) and diverge wildly in aesthetic. Don't collapse them into a single look.

## The brand slop test

If someone could look at this and say "AI made that" without hesitation, it's failed. The bar is distinctiveness; a visitor should ask "how was this made?", not "which AI made this?"

Brand is not a neutral register. AI-generated landing pages have flooded the internet; average is no longer findable. Restraint without intent now reads as mediocre, not refined. Brand surfaces need a POV, a specific audience, a willingness to risk strangeness. Go big or go home.

**The second slop test: aesthetic lane.** Before committing, name the reference. A Klim specimen page is one lane; Stripe-minimal is another; Liquid-Death-acid-maximalism is another. Don't drift into editorial-magazine aesthetics on a brief that isn't editorial. A hiking brand with Cormorant italic drop caps has the wrong register within the register.

Then the inverse test: in one sentence, describe what you're about to build the way a competitor would describe theirs. If that sentence fits the modal landing page in the category, restart.

## Typography

### Font selection procedure

Every project. Never skip.

1. **Read the brief.** Write three concrete brand-voice words. Not "modern" or "elegant," but "warm and mechanical and opinionated" or "calm and clinical and careful." Physical-object words.
2. **List the three fonts** you'd reach for by reflex. If any appear in the reflex-reject list, dismiss them; they are training-data defaults and they create monoculture.
3. **Browse a real catalog** (Google Fonts, Pangram Pangram, Future Fonts, Adobe Fonts, ABC Dinamo, Klim, Velvetyne) with the three words in mind. Find the font for the brand as a *physical object*: a museum caption, a 1970s terminal manual, a fabric label, a cheap-newsprint children's book, a concert poster, a receipt from a mid-century diner. Reject the first thing that "looks designy."
4. **Cross-check.** "Elegant" is not necessarily serif. "Technical" is not necessarily sans. "Warm" is not Fraunces. If the final pick lines up with the original reflex, start over.

### Reflex-reject fonts (training-data defaults — ban list for new design choices)

Fraunces · Newsreader · Lora · Crimson · Crimson Pro · Crimson Text · Playfair Display · Cormorant · Cormorant Garamond · Syne · IBM Plex Mono · IBM Plex Sans · IBM Plex Serif · Space Mono · Space Grotesk · Inter · DM Sans · DM Serif Display · DM Serif Text · Outfit · Plus Jakarta Sans · Instrument Sans · Instrument Serif

### Reflex-reject aesthetic lanes (parallel to the font list)

- **Editorial-typographic.** Display serif (often italic) + small mono labels + ruled separators + monochromatic restraint. Klim-influenced, magazine-cover affectation. By 2026, every Stripe-adjacent and Notion-adjacent brand has landed here. The fingerprint: three rule-separated columns, an italic Fraunces/Recoleta/Newsreader headline, lowercase track-spaced metadata, no imagery.

Removing entries when they fall back below saturation is fine. The lists apply to **new design choices**. When the existing brand has already committed to a font or a lane, identity-preservation wins; variants on an existing surface don't second-guess what's already shipping.

### Pairing and voice

Distinctive + refined is the goal. The specific shape depends on the brand, not on its category. A category ("restaurant" / "dev tool" / "magazine" / "fintech") is not a recipe; treating it as one is the first-order reflex. Two families minimum is the rule *only* when the voice needs it. A single well-chosen family with committed weight/size contrast is stronger than a timid display+body pair.

### Scale

- Modular scale, fluid `clamp()` for headings, ≥1.25 ratio between steps. Flat scales (1.1× apart) read as uncommitted.
- Light text on dark backgrounds: add 0.05–0.1 to line-height. Light type reads as lighter and needs more breathing room.
- Display letter-spacing floor ≥ -0.04em.
- Display `clamp()` ceiling ≤ 6rem (~96px).

## Color

Brand surfaces have permission for Committed, Full palette, and Drenched strategies. Use them. A single saturated color spread across a hero is not excess; it's voice. A beige-and-muted-slate landing page ignores the register.

- Name a real reference before picking a strategy: "Klim Type Foundry orange drench," "Stripe purple-on-white restraint," "Liquid Death acid-green full palette," "Mailchimp yellow full palette," "Condé Nast Traveler muted navy restraint," "Vercel pure black monochrome." Unnamed ambition becomes beige.
- Palette IS voice. A calm brand and a restless brand should not share palette mechanics.
- When the strategy is Committed or Drenched, color carries the brand; don't hedge with neutrals.
- Don't converge across projects. Each brand surface differentiates from the last.
- When a cultural-symbol palette is the obvious pull (Italian = terracotta, Japan = crimson), reach past it. Let the cultural reading come from typography, imagery, and copy, not the palette.

## Layout

- Asymmetric compositions are one option. Break the grid intentionally for emphasis.
- Fluid spacing with `clamp()` that breathes on larger viewports. Vary for rhythm: generous separations, tight groupings.
- For image-led briefs (hotels, restaurants, magazines, photography), full-bleed hero imagery with overlaid menu and centered headline is a canonical move. Let the photograph be the design.
- When cards ARE the right affordance, use `grid-template-columns: repeat(auto-fit, minmax(280px, 1fr))` for breakpoint-free responsiveness.

## Imagery

Brand surfaces lean on imagery. A restaurant, hotel, magazine, or product landing page without any imagery reads as incomplete, not as restrained. A solid-color rectangle where a hero image should go is worse than a representative stock photo.

**When the brief implies imagery, you must ship imagery.** Zero images is a bug, not a design choice. "Restraint" is not an excuse.

- For greenfield work without local assets, use stock imagery. Unsplash is the default. URL shape: `https://images.unsplash.com/photo-{id}?auto=format&fit=crop&w=1600&q=80`. Verify the URLs before referencing them.
- Search for the brand's physical object, not the generic category: "handmade pasta on a scratched wooden table" beats "Italian food."
- One decisive photo beats five mediocre ones. Hero imagery should commit to a mood.
- Alt text is part of the voice: "Coastal fettuccine, hand-cut, served on the terrace" beats "pasta dish."

"Imagery" here is broader than stock photography: product screenshots, custom data visualizations, generated SVG, and canvas/WebGL scenes are all imagery. Text-only pages where typography alone carries the entire visual weight are the failure mode.

## Motion

Brand surfaces afford things product surfaces don't:

- **One well-orchestrated page-load beats scattered micro-interactions**, when the brand invites it. Some brands skip entrance motion entirely; the restraint is the voice.
- Ambitious first-load motion: reveals and typographic choreography that earn their place, not fade-on-scroll on every section.
- Art direction per section: different sections can have different visual worlds if the narrative demands it. Consistency of voice beats consistency of treatment.

## Brand bans (on top of the shared absolute bans)

- Monospace as lazy shorthand for "technical / developer."
- Large rounded-corner icons above every heading.
- Single-family pages that picked the family by reflex, not voice. (A single family chosen deliberately is fine.)
- All-caps body copy. Reserve caps for short labels and headings.
- Timid palettes and average layouts. Safe = invisible.
- Zero imagery on a brief that implies imagery.
- Defaulting to editorial-magazine aesthetics on briefs that aren't magazine-shaped.
- Repeated tiny uppercase tracked labels above every section heading. A single strong kicker can be voice; repeating it as section grammar is AI scaffolding.

## Brand permissions (take these)

- Ambitious first-load motion.
- Single-purpose viewports: one dominant idea per fold, long scroll, deliberate pacing.
- Unexpected color strategies.
- Art direction per section.

## Live variant mode

For element-level iteration in the browser (designer's pick, generate alternatives), see the upstream `impeccable` skill's `reference/live.md`. viv-design inherits that capability but it's not auto-invoked here.
