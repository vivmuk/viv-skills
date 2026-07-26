# Animation Vocabulary

Turn a vague description of a motion or effect into its precise term. Use when the user asks "what's it called when…" or describes a motion effect without naming it.

Output format:

```
**Term** — Verbatim definition from the glossary.
```

If several terms could fit, list the best match first, then 1-2 alternates with a one-line note on how they differ.

## Glossary

### Entrances & Exits — how elements appear and disappear

- **Fade in / Fade out** — Element appears or disappears by changing opacity.
- **Slide in** — Element enters by sliding in from off-screen (left, right, top, or bottom).
- **Scale in** — Element grows from smaller to full size as it appears, often paired with a fade.
- **Pop in** — Element appears with a slight overshoot, like it bounces into place.
- **Reveal** — Content is uncovered gradually, often by animating a clip-path or mask.
- **Enter / Exit** — The animation an element plays when it's added to or removed from the screen.

### Sequencing & Timing — coordinating multiple elements or moments

- **Keyframes** — Defined points in an animation (0%, 50%, 100%) that the browser fills the gaps between.
- **Interpolation / Tween** — Generating all the in-between frames between a start and end value, so motion is continuous.
- **Stagger** — Animate several items one after another with a small delay between each, creating a cascade.
- **Orchestration** — Deliberately timing multiple animations so they feel like one coordinated motion.
- **Delay** — Time before an animation starts.
- **Duration** — How long an animation takes.
- **Fill mode** — Whether an element keeps its first or last frame's styles before the animation starts or after it ends (e.g. forwards).
- **Stepped animation** — An animation that is divided into discrete steps, like a countdown timer.

### Movement & Transforms — changing an element's position, size, or angle

- **Translate** — Move an element along the X or Y axis.
- **Scale** — Make an element bigger or smaller.
- **Rotate** — Spin an element around a point.
- **Skew** — Slant an element along the X or Y axis, shearing it out of its rectangular shape.
- **3D tilt / Flip** — Rotate in 3D space (rotateX / rotateY) to add depth.
- **Perspective** — How strong the 3D effect looks — a lower value exaggerates depth, like the viewer is closer.
- **Transform origin** — The anchor point a scale or rotation grows or spins from.
- **Origin-aware animation** — An element animates out of its trigger, like a popover growing from the button that opened it instead of from its own center which is the default in CSS.

### Transitions Between States — connecting one state, view, or element to another

- **Crossfade** — One element fades out as another fades in, in the same spot.
- **Continuity transition** — A change that keeps the user oriented by visually connecting before and after. For example, making the same rectangle bigger and smaller.
- **Morph** — One shape smoothly turns into another shape, e.g. Dynamic Island.
- **Shared element transition** — An element travels and transforms from one position into another, like a thumbnail expanding into a card.
- **Layout animation** — When an element's size or position changes, it animates to the new spot instead of snapping.
- **Accordion / Collapse** — A section smoothly expands and collapses its height to show or hide content.
- **Direction-aware transition** — Content slides one way going forward and the opposite way going back, so navigation has a sense of direction.

### Scroll — motion tied to scrolling or navigating between views

- **Scroll reveal** — Elements fade or slide into place as they enter the viewport.
- **Scroll-driven animation** — An animation whose progress is tied directly to scroll position.
- **Parallax** — Background and foreground move at different speeds while scrolling, creating depth.
- **Page transition** — An animation that plays when navigating from one page or route to another.
- **View transition** — The browser morphs between two states or pages, connecting shared elements.

### Feedback & Interaction — responding to the user's actions

- **Hover effect** — Visual change when the cursor moves over an element.
- **Press / Tap feedback** — A subtle scale-down when an element is clicked, so it feels physical.
- **Hold to confirm** — A progress effect that fills up while the user holds a button.
- **Drag** — Moving an element by grabbing it, often with momentum when released.
- **Drag to reorder** — Dragging items in a list to rearrange them, while the others shift to make room.
- **Swipe to dismiss** — Dragging an element off-screen to close it, like a drawer or toast.
- **Rubber-banding** — Resistance and snap-back when you drag past a boundary (the iOS overscroll feel).
- **Shake / Wiggle** — A quick side-to-side jitter signaling an error or rejected input.
- **Ripple** — A circle expanding from the point of a tap, confirming the press.

### Easing — how speed changes over an animation

- **Easing** — The rate at which an animation speeds up or slows down.
- **Ease-out** — Starts fast, ends slow. The default for most UI and anything responding to the user.
- **Ease-in** — Starts slow, ends fast. Usually avoided; can feel sluggish.
- **Ease-in-out** — Slow, fast, slow. Good for elements already on screen moving from A to B.
- **Linear** — Constant speed. Avoid for UI; reserve for spinners or marquees.

## Notes on disambiguation

- **Clip-path vs Mask**: clip-path defines a geometric visible region; mask allows alpha-based transparency. Reach for clip-path first for performance.
- **Pop in vs Bounce**: Pop in is a single overshoot on entrance, then settles. Bounce implies multiple oscillations (deprecated for UI).
- **Shared element transition vs Layout animation**: Shared-element travels AND transforms (e.g. thumbnail → expanded card). Layout animation moves to a new size/position without preserving identity.
- **Spring vs Tween**: Spring settles on physics parameters; no fixed duration. Tween runs a fixed duration with an interpolation curve.

## When nothing matches exactly

Name the closest term, say plainly it's an approximation, or describe the effect using the vocabulary above (e.g. "that's a stagger of scale-in entrances"). Stay within this glossary — don't invent a term.
