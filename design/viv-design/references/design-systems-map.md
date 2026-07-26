# Design Systems Map — Brief to Official Package

When the brief reads as requiring a real (existing, official) design system, install the official package and use it. Don't reinvent its CSS by hand. Don't import a system's tokens but override 90% of them. One system per project.

## Reach for an official package

| Brief reads as… | Reach for | Why |
|---|---|---|
| Microsoft / enterprise SaaS / dashboards | `@fluentui/react-components` or `@fluentui/web-components` | Official Fluent UI, MS tokens, a11y done |
| Google-ish UI, Material-flavored product | `@material/web` + Material 3 tokens | Official, themeable via Material Theming |
| IBM-style B2B / enterprise analytics | `@carbon/react` + `@carbon/styles` | Official Carbon, mature data-density patterns |
| Shopify app surfaces | `polaris.js` web components / Polaris React | Required for Shopify admin UI |
| Atlassian / Jira-style product | `@atlaskit/*` + `@atlaskit/tokens` | Official Atlassian DS |
| GitHub-style devtool / community page | `@primer/css` or `@primer/react-brand` | Official Primer; Brand variant for marketing |
| Public-sector UK service | `govuk-frontend` | Legally / regulatorily expected |
| US public-sector / trust-first | `uswds` | Same |
| Fast local-business / agency MVP | Bootstrap 5.3 | Boring, fast, works |
| Modern accessible React foundation | `@radix-ui/themes` | Primitives + polished theme |
| Modern SaaS where you own the components | `shadcn/ui` (`npx shadcn@latest add ...`) | You own the code; never ship default state — customize radii, colors, shadows, typography |
| Tailwind-based modern SaaS / AI marketing | Tailwind v4 utilities + `dark:` variant | Default for indie + small team builds |

**Honesty rule:** if the brief reads as one of these systems, install and use the **official** package. Do not recreate its CSS by hand.

**One system per project.** Do not mix Fluent React with Carbon in the same tree. Do not import shadcn/ui components into a Material 3 app.

## Aesthetic families (no official package; build honestly)

For these, there is **no single official package**. Build with native CSS + Tailwind + a maintained component library. Be honest in code comments about what is borrowed inspiration vs official material.

| Aesthetic | Honest implementation |
|---|---|
| Glassmorphism / "frosted glass" | `backdrop-filter`, layered borders, highlight overlays. Provide solid-fill fallback for `prefers-reduced-transparency`. |
| Bento (Apple-style tile grids) | CSS Grid with mixed cell sizes. No single library owns this. |
| Brutalism | Native CSS, monospace, raw borders. No library. |
| Editorial / magazine | Serif type, asymmetric grid, generous whitespace. No library. |
| Dark tech / hacker | Mono + accent neon, terminal motifs. No library. |
| Aurora / mesh gradients | SVG or layered radial gradients. No library. |
| Kinetic typography | Native CSS animations, scroll-driven animations, GSAP for hijacks. No library. |
| **Apple Liquid Glass** | Apple documents this for Apple platforms only. **There is no official `liquid-glass.css`.** Web implementations are approximations using `backdrop-filter` + layered borders + highlights. Label clearly as approximation. |

## Install commands per system (most common)

```bash
# Tailwind v4 (modern SaaS baseline)
npm i -D tailwindcss@latest @tailwindcss/vite

# shadcn/ui (you own the components after install)
npx shadcn@latest init
npx shadcn@latest add button card input dialog sheet tabs

# Radix UI primitives (foundation, no styling)
npm i @radix-ui/themes @radix-ui/react-popover @radix-ui/react-dialog

# Material Web Components
npm i @material/web

# Fluent UI React
npm i @fluentui/react-components

# Carbon (IBM)
npm i @carbon/react

# GOV.UK Frontend
npm i govuk-frontend

# USWDS
npm i @uswds/uswds

# Bootstrap 5
npm i bootstrap@5.3

# Motion (Framer Motion successor)
npm i motion

# GSAP (for scroll-magic, kinetic type, hijacks)
npm i gsap
```

## Component libraries vs Design systems

A design system is **more than a component library**:

| Concern | Component library | Design system |
|---|---|---|
| Buttons, inputs, modals | ✅ | ✅ |
| Tokens (colors, spacing, type) | partial | ✅ |
| Accessibility primitives | partial | ✅ |
| Documented patterns | rare | ✅ |
| Voice + brand expression | never | ✅ |

Reach for a real **design system** when the brief fits one of the official packages above. Reach for a component library + your own tokens otherwise.

## Tailwind caveat

Tailwind v4 is the modern baseline for indie + small-team SaaS landings, but it ships with a defined aesthetic. The defaults are not wrong, they are just defaults:

- **Don't ship default Tailwind colors as brand.** Configure the theme with `theme.extend.colors = { brand: { ... } }` and use those tokens everywhere.
- **Don't ship default Tailwind typography as brand.** Configure `theme.extend.fontFamily = { display: [...], body: [...] }` and use those.
- **Don't ship default `rounded-lg` / `rounded-xl` as radius.** Configure one radius scale and stick to it (see hero discipline in SKILL.md).

Tailwind is a utility framework, not a design system. Treat it as the substrate; supply the brand through configuration.
