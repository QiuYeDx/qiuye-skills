---
name: qiuye-smooth-corners
description: >-
  Implement Figma/iOS-style smooth corners for frontend UI using progressive
  enhancement with CSS corner-shape: superellipse(...), border-radius fallback,
  and optional size-aware computation. Use when users ask for smooth corners,
  corner smoothing, continuous corners, superellipse/squircle corners, iOS-like
  rounded corners, Figma corner smoothing, 平滑圆角, 圆角平滑, 超椭圆圆角,
  连续圆角, 柔和圆角, or want shadcn/ui components to reuse smooth corner
  effects. Covers QiuYe UI registry installation, @qiuyedx/smooth-corners npm
  usage, no-dependency inline helpers, ResizeObserver/observer patterns,
  Tailwind/shadcn integration, and validation.
---

# Smooth Corners

Use this skill to implement smooth, continuous, Figma/iOS-like rounded corners in frontend projects. Treat progressive enhancement as the core invariant: supported browsers get `corner-shape: superellipse(...)`; unsupported browsers keep a correct `border-radius` fallback.

## Routing Decision

Start by inspecting the target project:

1. Check framework and component system: React/Next, Vue, Svelte, vanilla, shadcn/ui, Tailwind.
2. Check whether `components.json` exists and whether QiuYe UI registry aliases can be used.
3. Check package manager and lockfile version before installing dependencies.
4. Check whether the user allows dependencies or asks for an inline/no-dependency implementation.
5. Check whether element dimensions are dynamic or the radius approaches half of the shortest side.

Choose the implementation route with this priority:

| Scenario | Preferred route |
|---|---|
| shadcn/ui project that can use QiuYe UI registry | Install `@qiuye-ui/smooth-corners` first |
| React/Vue/vanilla project, dependencies allowed, not using shadcn registry | Use `@qiuyedx/smooth-corners` |
| Dynamic element size or large radius near half the short side | Use size-aware compute/observer |
| Dependencies disallowed | Use inline helper + CSS `@supports` |
| Only global design-token radius needs changing | Prefer theme tokens; do not force this skill |

Hard rule: if the project can use shadcn/ui registry, prefer QiuYe UI's `@qiuye-ui/smooth-corners` component instead of manually installing the lower-level `@qiuyedx/smooth-corners` package. Use the npm package directly only for non-shadcn projects, lower-level APIs, or QiuYe UI component internals.

## QiuYe UI Route

For shadcn/ui projects, add the QiuYe UI registry alias when missing:

```json
{
  "registries": {
    "@qiuye-ui": "https://ui.qiuyedx.com/registry/{name}.json"
  }
}
```

Then install:

```bash
pnpm dlx shadcn@latest add @qiuye-ui/smooth-corners
```

Direct URL fallback:

```bash
pnpm dlx shadcn@latest add https://ui.qiuyedx.com/registry/smooth-corners.json
```

After installation, use the component rather than reimplementing the algorithm:

```tsx
import { SmoothCorners } from "@/components/qiuye-ui/smooth-corners";

export function Example() {
  return (
    <SmoothCorners
      radius={28}
      smoothing={0.7}
      className="bg-primary p-6 text-primary-foreground"
    >
      Smooth corner card
    </SmoothCorners>
  );
}
```

Use `asChild` for existing semantic elements such as buttons, links, cards, and images. Use `observeSize` only for dynamic sizes or very large radii; do not enable ResizeObserver by default for large lists.

## Package Route

Use `@qiuyedx/smooth-corners@0.1.0` when the project is not using shadcn/ui registry or needs the lower-level API.

```bash
pnpm add @qiuyedx/smooth-corners
```

Core API:

```tsx
import { smoothCorners, smoothCornersCSS } from "@qiuyedx/smooth-corners";

const style = smoothCorners(30, 0.6);
```

Make sure the CSS is injected globally or added to the app stylesheet. Do not set inline `borderRadius` for the same element after applying the generated CSS variables; that can override the progressive enhancement.

## Inline Route

When dependencies are not allowed, read `references/implementation-recipes.md` and copy the minimal helper + CSS pattern. Keep the behavior aligned with the package API:

- `--sc-r`: original fallback radius.
- `--sc-i`: compensated radius used only inside `@supports`.
- `--sc-s`: `superellipse(K)` value.
- `@supports (corner-shape: superellipse(2))`: feature detection.

Do not use UA sniffing or browser-version tables. Do not promise true superellipse rendering in unsupported browsers; the fallback is a normal circular `border-radius`.

## Size-Aware Route

Use size-aware logic when:

- width/height changes after render,
- the element is responsive or animated,
- radius is close to `min(width, height) / 2`,
- corners visually collide or become pill-like.

Prefer the package observer for low-volume dynamic elements:

```tsx
import { observe, unobserve } from "@qiuyedx/smooth-corners/observer";
```

For custom framework wrappers, use `computeSmoothCorners` or the inline equivalent from `references/implementation-recipes.md`. Always clean up `ResizeObserver`.

## Tailwind And shadcn Notes

- Avoid combining Tailwind `rounded-*` with `.smooth-corners` on the same element unless the generated class wins intentionally.
- Put `overflow-hidden` on the same element when clipping children or images is required.
- Keep focus rings visible; for `asChild` buttons, ensure the child still receives focus classes.
- Do not wrap cards inside decorative cards just to show the effect; apply the effect to the real surface.
- Prefer semantic color tokens such as `bg-card`, `text-card-foreground`, `bg-primary`.

## Common Mistakes

- Using inline `style={{ borderRadius: ... }}` after smooth-corner variables.
- Forgetting to include the `.smooth-corners` CSS.
- Defaulting every list item to `observeSize`.
- Assuming unsupported browsers can render continuous corners.
- Replacing all design-system radius tokens when only one surface needs smoothing.
- Installing `@qiuyedx/smooth-corners` manually in a shadcn project where `@qiuye-ui/smooth-corners` is available.

## Validation

Before finishing:

1. Verify the element has fallback `border-radius: var(--sc-r)`.
2. Verify the enhanced rule is guarded by `@supports (corner-shape: superellipse(2))`.
3. Check that `radius`, `smoothing`, disabled state, and `asChild`/wrapper behavior work.
4. For size-aware usage, resize the element and confirm variables update without observer leaks.
5. Check light/dark theme, hover/focus states, and clipping of children.
6. Run the project's relevant lint/build/test command using its existing package manager.
7. If a dev server was started for visual verification, stop it before responding.

## Detailed Recipes

Read `references/implementation-recipes.md` when you need package setup details, inline helper code, React wrapper code, Vue/vanilla examples, or ResizeObserver templates. Keep `SKILL.md` as the decision guide and use the reference only for implementation details.
