---
name: geometric-mask-transition
description: >-
  Design and implement geometric mask and reveal transitions for UI state
  changes, route transitions, loading screens, hero reveals, overlays, modals,
  media reveals, and scene changes. Use when an interface should transition
  through a moving shape, expanding aperture, wipe, clip-path, mask-image,
  SVG mask, canvas/WebGL matte, or layered geometric overlay instead of a
  simple fade/slide. Covers choosing the geometric metaphor, separating content
  and mask layers, driving CSS variables with Motion/CSS/RAF, theme-safe
  contrast, reduced motion, accessibility, performance, and validation.
  Triggers on: "reveal transition", "geometric mask", "mask transition",
  "clip-path reveal", "radial wipe", "aperture reveal", "shape wipe",
  "loading reveal", "scene transition", "page reveal", "mask-image animation",
  "transition matte", "几何遮罩", "揭幕", "遮罩过渡", "图形过渡",
  "圆形揭幕", "渐变遮罩过渡".
---

# Geometric Mask Transition

Use this skill to build transitions where a geometric layer, matte, or mask carries the visual story: a circle opening, a diagonal wipe, a polygon sweep, a gradient veil, an SVG path morph, a shutter, a spotlight, or any shape-based reveal.

The core idea: keep the real UI/content layer stable, then animate a separate geometric mask layer above it. Drive a small set of geometry variables over time, and remove the mask only after it has fully revealed the target state.

## When To Use

- Loading or boot sequences that reveal the app content.
- Route/page transitions where the old and new screens should feel connected.
- Modal/drawer/overlay entrances that need a more designed transition than fade/slide.
- Hero/media/product reveals, before/after transitions, spotlight focus, spotlight search.
- State changes where the user's attention should move through a shape or direction.

Avoid this pattern for routine UI micro-interactions, dense forms, frequent table updates, or anything that would slow repeated work. A simple opacity/translate transition is often better for low-stakes UI.

## Design Workflow

1. **Choose the metaphor before the technique.**
   Decide what the transition should communicate: opening, scanning, folding, spotlighting, wiping, consuming, focusing, or handing off. Pick geometry that matches this narrative.

2. **Separate the layers.**
   Use at least three conceptual layers:
   - Source/content layer: the old or underlying UI.
   - Mask/matte layer: the animated geometric overlay or clip.
   - Target/content layer: the new UI, already mounted or ready behind the mask.

3. **Make the mask do one job.**
   Do not stack multiple progress indicators unless each has a different purpose. The shape should usually be the primary motion; text, counters, icons, and tracks are secondary.

4. **Animate geometry, not layout.**
   Drive CSS variables such as `--reveal-radius`, `--wipe-x`, `--angle`, `--edge`, or `--gradient-stop`. Avoid reflow-heavy width/height animation unless the element is isolated and simple.

5. **Plan the exit frame.**
   A good reveal has a stable completion frame, then cleanup. Do not remove the mask at the same instant the target UI appears; wait until the mask has fully covered or uncovered the necessary area.

## Geometry Choices

| Shape | Best for | Implementation |
|---|---|---|
| Circle / ellipse aperture | boot screens, spotlight, focus from center or element | `clip-path: circle()`, radial `mask-image`, SVG mask |
| Diagonal wipe | energetic page/section transitions | `clip-path: polygon()`, transformed overlay |
| Linear curtain | simple directional handoff | `mask-image: linear-gradient()`, translated overlay |
| Rounded rect / card aperture | card-to-detail, modal reveal | CSS `clip-path: inset(... round ...)` or SVG mask |
| Polygon shard | editorial/game/expressive UI | `clip-path: polygon()` or SVG |
| Gradient veil | soft reveal, background/media transition | CSS `mask-image` with gradient stops |
| Noise / texture matte | cinematic media reveal | canvas/WebGL or CSS/SVG mask image |

Choose the simplest primitive that preserves the intended feeling. If CSS can express it cleanly, prefer CSS over canvas/WebGL.

## Implementation Pattern

### 1. DOM Structure

```tsx
<div className="relative isolate overflow-hidden">
  <div className="relative z-0">{targetContent}</div>

  <div
    aria-hidden="true"
    className="pointer-events-none absolute inset-0 z-10"
    style={{
      "--reveal-radius": `${radius}px`,
      "--reveal-edge": `${radius + 1}px`,
    } as React.CSSProperties}
  >
    <div className="absolute inset-0 bg-background mask-reveal" />
  </div>
</div>
```

Key rules:
- `isolate` or an equivalent stacking context keeps blend/mask effects contained.
- The mask layer is `pointer-events: none` and `aria-hidden="true"`.
- The target UI should be mounted before the reveal starts when possible.

### 2. CSS Mask Example

```css
.mask-reveal {
  -webkit-mask-image: radial-gradient(
    circle at center,
    transparent 0 var(--reveal-radius),
    #000 var(--reveal-edge)
  );
  mask-image: radial-gradient(
    circle at center,
    transparent 0 var(--reveal-radius),
    #000 var(--reveal-edge)
  );
  will-change: -webkit-mask-image, mask-image;
}
```

For a filled expanding shape instead of a hole, invert the gradient stops or animate a visible overlay's transform/clip-path.

### 3. Drive The Variables

Use the project's existing animation stack. Examples:

```ts
// Motion vanilla
const progress = motionValue(0);
const unsubscribe = progress.on("change", (ratio) => {
  const radius = maxRadius * ratio;
  el.style.setProperty("--reveal-radius", `${radius}px`);
  el.style.setProperty("--reveal-edge", `${radius + 1}px`);
});

animate(progress, 1, {
  type: "spring",
  duration: 0.8,
  bounce: 0,
  onComplete: cleanup,
});
```

```ts
// requestAnimationFrame fallback
const start = performance.now();
const duration = 700;

function frame(now: number) {
  const t = Math.min(1, (now - start) / duration);
  const eased = 1 - Math.pow(1 - t, 3);
  setReveal(eased);
  if (t < 1) requestAnimationFrame(frame);
  else cleanup();
}

requestAnimationFrame(frame);
```

### 4. Compute Coverage

For aperture reveals, compute enough radius to cover the farthest corner:

```ts
const width = window.innerWidth || element.clientWidth;
const height = window.innerHeight || element.clientHeight;
const maxRadius = Math.ceil(Math.sqrt(width * width + height * height) / 2 + 32);
```

If the origin is not the center, compute distance from the origin to each corner and use the maximum.

## Variants

### Shape Overlay

Animate a visible shape that covers/unveils content:

```css
.reveal-disc {
  width: var(--size);
  height: var(--size);
  border-radius: 999px;
  transform: translate(-50%, -50%) scale(var(--scale));
}
```

Best when the shape itself is part of the visual identity.

### Clip-Path

```css
.clip-reveal {
  clip-path: circle(var(--radius) at var(--x) var(--y));
}
```

Best for simple shapes. Validate browser support and performance on the target devices.

### Gradient Mask

```css
.soft-wipe {
  -webkit-mask-image: linear-gradient(
    90deg,
    #000 0 var(--solid-stop),
    transparent var(--fade-stop)
  );
  mask-image: linear-gradient(
    90deg,
    #000 0 var(--solid-stop),
    transparent var(--fade-stop)
  );
}
```

Best when a soft edge is more elegant than a hard geometric cut.

### SVG Mask

Use SVG when the shape is complex, path-based, or needs morphing. Keep the SVG mask as a separate layer and animate path attributes or transforms with the project's animation library.

### Canvas / WebGL Matte

Use canvas/WebGL only when the reveal depends on particles, noise, video, fluid simulation, or many independently animated shapes. Keep DOM UI outside the canvas and use the canvas as a visual matte/overlay.

## Timing Model

Recommended sequence:

1. Prepare target content behind or under the mask.
2. Mount the mask in an initial fully covering state.
3. Animate the mask geometry.
4. Hold 80-180ms if the completion state needs to be perceived.
5. Fade/slide any decorative text or brand marks out if present.
6. Remove the mask DOM and event listeners.

For route transitions, avoid blocking input longer than necessary. For loading transitions, use a synthetic ceiling such as `90-95%`, then converge to `100%` only when the app is actually ready.

## Accessibility And Preferences

- Always respect `prefers-reduced-motion`; use a shorter fade or immediate state switch.
- Keep masks `aria-hidden` and `pointer-events: none`.
- Keep the underlying semantic UI available after the transition; do not trap focus in decorative layers.
- If progress is real, expose it through `role="progressbar"` and `aria-valuenow`; if it is purely decorative, do not present fake progress to assistive tech.

## Performance Rules

- Prefer animating CSS variables consumed by `transform`, `opacity`, `clip-path`, or `mask-image`.
- Avoid animating layout-affecting properties on complex DOM trees.
- Use `contain`, `isolate`, or a small overlay subtree to limit paint cost.
- Add `will-change` only to the animated mask elements, and remove the mask after completion.
- Recompute coverage on resize, orientation change, or container size changes.

## Visual QA Checklist

- The target content is ready before the mask reveals it.
- The mask covers/unveils all corners at every supported viewport size.
- No hard flash occurs at the first frame, completion frame, or cleanup frame.
- Dark/light themes maintain sufficient contrast.
- `prefers-reduced-motion` produces a sane simpler transition.
- Pointers are not blocked after cleanup.
- No stale mask DOM, timers, RAF loops, subscriptions, or dev services remain.

## Common Mistakes

- Adding a percent number, ring, bar, and moving shape all at once. Pick one primary progress metaphor.
- Removing the mask before the target UI paints, causing a blank or flash.
- Animating both CSS transition and JS animation on the same property.
- Using blend modes without `isolate`, causing underlying content to affect colors unpredictably.
- Assuming a centered radius covers all corners when the origin is offset.
- Leaving a full-screen `pointer-events` layer mounted after the transition.
