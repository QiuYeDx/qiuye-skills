# Smooth Corners Implementation Recipes

Use these recipes after `SKILL.md` selects an implementation route. Prefer copying the smallest pattern that fits the target project.

## 1. Shared CSS

```css
.smooth-corners {
  border-radius: var(--sc-r);
}

@supports (corner-shape: superellipse(2)) {
  .smooth-corners {
    border-radius: var(--sc-i);
    corner-shape: var(--sc-s);
  }
}
```

Keep the fallback outside `@supports`; keep `corner-shape` inside `@supports`.

## 2. npm Package API

```tsx
import { smoothCorners, smoothCornersCSS } from "@qiuyedx/smooth-corners";

function Card() {
  return (
    <div
      className="smooth-corners bg-card p-6 text-card-foreground"
      style={smoothCorners(30, 0.6) as React.CSSProperties}
    >
      Smooth corner card
    </div>
  );
}
```

Inject `smoothCornersCSS` once if the project does not already include it:

```tsx
function ensureSmoothCornersCSS() {
  if (typeof document === "undefined") return;
  if (document.getElementById("smooth-corners-style")) return;

  const style = document.createElement("style");
  style.id = "smooth-corners-style";
  style.textContent = smoothCornersCSS;
  document.head.append(style);
}
```

## 3. No-Dependency Helper

```ts
type SmoothCornerVars = Record<"--sc-r" | "--sc-i" | "--sc-s", string>;

const D = 1 - Math.SQRT1_2;

function superellipseK(radius: number, compensatedRadius: number) {
  if (radius <= 0 || compensatedRadius <= radius) return 1;
  const u = 1 - (radius * D) / compensatedRadius;
  if (u <= 0 || u >= 1) return 1;
  const n = Math.log(2) / Math.log(1 / u);
  return Math.log2(Math.max(2, n));
}

export function smoothCorners(
  radius: number,
  smoothing = 0.6,
): SmoothCornerVars {
  const r = Math.max(0, radius);
  const s = Math.max(0, Math.min(1, smoothing));

  if (r < 1e-6 || s < 1e-6) {
    const value = `${r}px`;
    return { "--sc-r": value, "--sc-i": value, "--sc-s": "" };
  }

  const compensatedRadius = r * (1 + s);
  const k = superellipseK(r, compensatedRadius);

  if (k <= 1) {
    const value = `${r}px`;
    return { "--sc-r": value, "--sc-i": value, "--sc-s": "" };
  }

  return {
    "--sc-r": `${r}px`,
    "--sc-i": `${compensatedRadius}px`,
    "--sc-s": `superellipse(${k.toFixed(4)})`,
  };
}
```

This helper intentionally mirrors the public CSS variable shape. Use the official package when exact future compatibility matters.

## 4. Size-Aware Compute

Use this when large radii can collide on narrow elements:

```ts
export function computeSmoothCorners(
  width: number,
  height: number,
  radius: number,
  smoothing = 0.6,
) {
  const maxRadius = Math.max(0, Math.min(width, height) / 2);
  const r = Math.min(Math.max(0, radius), maxRadius);
  const wanted = Math.max(0, Math.min(1, smoothing));
  const extension = Math.min(r * wanted, maxRadius - r);
  const compensatedRadius = r + Math.max(0, extension);
  const effectiveSmoothing = r < 1e-6 ? 0 : Math.max(0, extension) / r;
  const k =
    effectiveSmoothing < 1e-6 ? null : superellipseK(r, compensatedRadius);

  return {
    radius: r,
    compensatedRadius,
    smoothing: effectiveSmoothing,
    k,
  };
}

export function smoothCornersFromSize(
  width: number,
  height: number,
  radius: number,
  smoothing = 0.6,
) {
  const result = computeSmoothCorners(width, height, radius, smoothing);

  return {
    "--sc-r": `${result.radius}px`,
    "--sc-i": `${result.compensatedRadius}px`,
    "--sc-s": result.k ? `superellipse(${result.k.toFixed(4)})` : "",
  } satisfies SmoothCornerVars;
}
```

## 5. React Wrapper

Use this only when the project cannot install QiuYe UI's `SmoothCorners`.

```tsx
"use client";

import * as React from "react";
import { smoothCorners } from "@qiuyedx/smooth-corners";
import { cn } from "@/lib/utils";

type SmoothCornerStyle = React.CSSProperties &
  Partial<Record<"--sc-r" | "--sc-i" | "--sc-s", string>>;

interface SmoothCornersProps extends React.HTMLAttributes<HTMLDivElement> {
  radius?: number;
  smoothing?: number;
  disabled?: boolean;
}

export function SmoothCorners({
  radius = 16,
  smoothing = 0.6,
  disabled = false,
  className,
  style,
  ...props
}: SmoothCornersProps) {
  const vars = disabled
    ? {}
    : (smoothCorners(radius, smoothing) as SmoothCornerStyle);

  return (
    <div
      className={cn(!disabled && "smooth-corners", className)}
      style={{ ...style, ...vars }}
      {...props}
    />
  );
}
```

Add the shared CSS from recipe 1 to a global stylesheet or inject it once.

## 6. ResizeObserver Template

```tsx
function useSmoothCornerObserver(
  ref: React.RefObject<HTMLElement | null>,
  radius: number,
  smoothing = 0.6,
) {
  React.useEffect(() => {
    const el = ref.current;
    if (!el || typeof ResizeObserver === "undefined") return;

    const update = () => {
      const rect = el.getBoundingClientRect();
      const vars = smoothCornersFromSize(
        rect.width,
        rect.height,
        radius,
        smoothing,
      );

      for (const [name, value] of Object.entries(vars)) {
        el.style.setProperty(name, value);
      }
    };

    const observer = new ResizeObserver(update);
    observer.observe(el);
    update();

    return () => observer.disconnect();
  }, [ref, radius, smoothing]);
}
```

Do not attach this observer to hundreds of list items unless there is a measured need.

## 7. Vue And Vanilla

Vue:

```vue
<script setup lang="ts">
import { computed } from "vue";
import { smoothCorners } from "@qiuyedx/smooth-corners";

const props = withDefaults(
  defineProps<{ radius?: number; smoothing?: number }>(),
  { radius: 16, smoothing: 0.6 },
);

const style = computed(() => smoothCorners(props.radius, props.smoothing));
</script>

<template>
  <div class="smooth-corners" :style="style">
    <slot />
  </div>
</template>
```

Vanilla:

```ts
import { smoothCorners } from "@qiuyedx/smooth-corners";

const el = document.querySelector<HTMLElement>(".smooth-corners");
if (el) {
  Object.assign(el.style, smoothCorners(28, 0.7));
}
```

## 8. Quick Checklist

- `border-radius: var(--sc-r)` exists as fallback.
- `corner-shape` is guarded by `@supports`.
- The same element is not also controlled by Tailwind `rounded-*` unintentionally.
- `overflow-hidden` is present when child clipping matters.
- ResizeObserver is opt-in and cleaned up.
- shadcn/ui projects use `@qiuye-ui/smooth-corners` first.
