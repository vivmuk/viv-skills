# Product Register

When **design SERVES the product**: app UIs, admin dashboards, settings panels, data tables, tools, authenticated surfaces — anything where the user is in a task. Familiarity is often a feature here.

## The product slop test

Not "would someone say AI made this." Familiarity is often the point. The test is: would a user fluent in the category's best tools (Linear, Figma, Notion, Raycast, Stripe, GitHub) sit down and trust this interface, or pause at every subtly-off component?

Product UI's failure mode isn't flatness, it's **strangeness without purpose**: over-decorated buttons, mismatched form controls, gratuitous motion, display fonts where labels should be, invented affordances for standard tasks. The bar is earned familiarity. The tool should disappear into the task.

## Typography

- **One family is often right.** Product UIs don't need display/body pairing. A well-tuned sans carries headings, buttons, labels, body, data.
- **Fixed rem scale, not fluid.** `clamp()`-sized headings don't serve product UI. Users view at consistent DPI, and a fluid h1 that shrinks in a sidebar looks worse, not better.
- **Tighter scale ratio:** 1.125–1.2 between steps is typical. More type elements here than on brand surfaces; exaggerated contrast creates noise.
- **Line length still applies for prose** (65–75ch). Data and compact UI can run denser; tables at 120ch+ are fine.
- **System fonts are appropriate here.** Inter / SF Pro / system-ui stacks earn their place in product UI. (They are still banned from brand new-design choices.)

## Color

Product defaults to **Restrained**. A single surface can earn Committed (a dashboard where one category color carries a report; an onboarding flow with a drenched welcome screen), but Restrained is the floor.

- **State-rich semantic vocabulary:** hover, focus, active, disabled, selected, loading, error, warning, success, info. Standardize these.
- **Accent color used for primary actions, current selection, and state indicators only**, not decoration.
- A second neutral layer for sidebars, toolbars, and panels (slightly cooler or warmer than the content surface).

## Layout

- Responsive behavior is structural (collapse sidebar, responsive table, breakpoint-driven columns), not fluid typography.
- **Density is a virtue.** Tables with many rows, panels with many labels, dense information when users need it.
- Consistency over surprise. The same visual vocabulary screen to screen is the virtue; delight is saved for moments, not pages.

## Components

Every interactive component has: default, hover, focus, active, disabled, loading, error. Don't ship with half of these.

- **Skeleton states for loading**, not spinners in the middle of content.
- **Empty states that teach the interface**, not "nothing here."
- **Consistent affordances across the surface.** Same button shape. Same form-control vocabulary. Same icon style.

## Motion

- **150–250ms on most transitions.** Users are in flow; don't make them wait for choreography.
- **Motion conveys state, not decoration.** State change, feedback, loading, reveal — nothing else.
- **No orchestrated page-load sequences.** Product loads into a task; users don't want to watch it load.
- See `references/animation-rules.md` for the full doctrine (easing, durations, springs, performance).

## Product bans (on top of the shared absolute bans)

- Decorative motion that doesn't convey state.
- Inconsistent component vocabulary across screens.
- Display fonts in UI labels, buttons, data.
- Reinventing standard affordances for flavor (custom scrollbars, weird form controls, non-standard modals).
- Heavy color or full-saturation accents on inactive states.
- Modal as first thought. Modals are usually laziness. Exhaust inline / progressive alternatives first.

## Product permissions

- System fonts and familiar sans defaults (Inter, SF Pro, system-ui stacks).
- Standard navigation patterns: top bar + side nav, breadcrumbs, tabs, command palettes.
- Density.
- Consistency over surprise.

## Accessibility (product surfaces prioritize this)

- Keyboard navigation for every interactive element.
- Focus rings visible (not removed "for cleanliness").
- Screen reader labels on icons + icon-only buttons.
- WCAG AA contrast throughout.
- Skip-to-content link on long surfaces.
- Live regions for dynamic content (toasts, async loaders).
- Form labels above inputs, error text below inputs, helper text present in markup.
