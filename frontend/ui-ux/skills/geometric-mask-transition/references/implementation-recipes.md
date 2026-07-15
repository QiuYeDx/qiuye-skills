# Implementation Recipes

## 目录

- [通用准备](#通用准备)
- [Recipe 1：任意原点的 target circular reveal](#recipe-1任意原点的-target-circular-reveal)
- [Recipe 2：可取消的 cover-swap-uncover](#recipe-2可取消的-cover-swap-uncover)
- [Recipe 3：CSS alpha-mask 软边 aperture](#recipe-3css-alpha-mask-软边-aperture)
- [Recipe 4：View Transition circular reveal](#recipe-4view-transition-circular-reveal)
- [Motion 与框架适配](#motion-与框架适配)
- [首帧、提交和清理](#首帧提交和清理)

## 通用准备

先复用这些几何函数。输入 origin 必须已经转换到目标元素的 border-box 坐标：

```ts
type Point = { x: number; y: number };

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

export function localPoint(
  element: Element,
  clientPoint: Point,
): Point {
  const rect = element.getBoundingClientRect();
  return {
    x: clamp(clientPoint.x - rect.left, 0, rect.width),
    y: clamp(clientPoint.y - rect.top, 0, rect.height),
  };
}

export function radiusToCover(
  width: number,
  height: number,
  point: Point,
): number {
  const { x, y } = point;
  return Math.ceil(
    Math.max(
      Math.hypot(x, y),
      Math.hypot(width - x, y),
      Math.hypot(x, height - y),
      Math.hypot(width - x, height - y),
    ) + 2,
  );
}

export function prefersReducedMotion() {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function assertNotAborted(signal?: AbortSignal) {
  if (signal?.aborted) {
    throw new DOMException("Transition aborted", "AbortError");
  }
}
```

如果设计允许 origin 在容器外，不要 clamp；公式仍然成立。先明确产品语义，再决定是否约束到边界。

## Recipe 1：任意原点的 target circular reveal

适用于 source 和 target 能同时挂载、target 应从点击点向外展开的场景。

```html
<div class="reveal-stage">
  <section class="reveal-source"><!-- old UI --></section>
  <section class="reveal-target"><!-- new UI --></section>
</div>
```

```css
.reveal-stage {
  position: relative;
  isolation: isolate;
  overflow: hidden;
  overflow: clip;
}

.reveal-source,
.reveal-target {
  position: absolute;
  inset: 0;
}

.reveal-source { z-index: 0; }
.reveal-target { z-index: 1; }
```

给 stage 明确的稳定高度、`min-block-size` 或 `aspect-ratio`。两个子层都绝对定位时不会撑开父元素；不要让动画开始后容器才从 `0` 高度跳到目标高度。

使用 WAAPI 控制动画，并把取消纳入函数契约：

```ts
type RevealOptions = {
  clientPoint: Point;
  duration?: number;
  signal?: AbortSignal;
};

export async function revealTarget(
  target: HTMLElement,
  {
    clientPoint,
    duration = 520,
    signal,
  }: RevealOptions,
) {
  const rect = target.getBoundingClientRect();
  const point = localPoint(target, clientPoint);
  const radius = radiusToCover(rect.width, rect.height, point);
  const hidden = `circle(0px at ${point.x}px ${point.y}px)`;
  const visible = `circle(${radius}px at ${point.x}px ${point.y}px)`;

  if (
    prefersReducedMotion() ||
    !CSS.supports("clip-path", hidden)
  ) {
    target.style.clipPath = "none";
    return;
  }

  assertNotAborted(signal);

  // Call from a layout effect or immediately after DOM insertion so this
  // hidden state exists before the browser can paint the target.
  target.style.clipPath = hidden;
  const animation = target.animate(
    [{ clipPath: hidden }, { clipPath: visible }],
    {
      duration,
      easing: "cubic-bezier(.22, 1, .36, 1)",
      fill: "forwards",
    },
  );
  const abort = () => animation.cancel();
  signal?.addEventListener("abort", abort, { once: true });

  try {
    await animation.finished;
    assertNotAborted(signal);
  } finally {
    signal?.removeEventListener("abort", abort);
    animation.cancel();
    // The cancellation policy for this recipe keeps the target visible.
    target.style.clipPath = "none";
  }
}
```

调用约束：

- 在 React 中从 `useLayoutEffect` 调用，并确保 render 时 target 已带 hidden `clip-path`；否则 effect 前可能出现完整 target 闪帧。
- 动画期间把 target 设为视觉当前层，但按产品策略控制 source/target 的 `inert` 和 `aria-hidden`。
- resize 期间使用 `ResizeObserver` 重新计算。最稳健策略是 resize 时立即完成 reveal 并清除 clip；若必须继续动画，按当前进度重启到新半径。
- 完成后移除 source，或恢复正常布局。不要永久保留两个绝对定位页面。

## Recipe 2：可取消的 cover-swap-uncover

适用于在完全遮挡时提交路由或互斥状态。overlay 应 portal 到不会随 route 卸载的稳定节点：

```html
<div data-transition-cover hidden aria-hidden="true"></div>
```

```css
[data-transition-cover] {
  position: fixed;
  inset: 0;
  z-index: var(--transition-z, 100);
  background: var(--transition-color, var(--background));
  transform: scaleX(0);
  pointer-events: none;
}
```

```ts
type CoverTransitionOptions = {
  cover: HTMLElement;
  commit: () => void | Promise<void>;
  signal?: AbortSignal;
  duration?: number;
};

function nextPaint() {
  return new Promise<void>((resolve) => {
    requestAnimationFrame(() => requestAnimationFrame(() => resolve()));
  });
}

async function play(
  element: HTMLElement,
  keyframes: Keyframe[],
  options: KeyframeAnimationOptions,
  signal?: AbortSignal,
  persistFinalState?: () => void,
) {
  assertNotAborted(signal);
  const animation = element.animate(keyframes, options);
  const abort = () => animation.cancel();
  signal?.addEventListener("abort", abort, { once: true });
  try {
    await animation.finished;
    assertNotAborted(signal);
    // Write the final state inline before canceling a fill-mode animation.
    persistFinalState?.();
  } finally {
    signal?.removeEventListener("abort", abort);
    animation.cancel();
  }
}

export async function coverSwapUncover({
  cover,
  commit,
  signal,
  duration = 360,
}: CoverTransitionOptions) {
  assertNotAborted(signal);

  if (prefersReducedMotion()) {
    await commit();
    return;
  }

  cover.hidden = false;
  cover.style.transformOrigin = "left center";
  cover.style.transform = "scaleX(0)";

  try {
    await play(
      cover,
      [{ transform: "scaleX(0)" }, { transform: "scaleX(1)" }],
      { duration, easing: "cubic-bezier(.65, 0, .35, 1)", fill: "forwards" },
      signal,
      () => { cover.style.transform = "scaleX(1)"; },
    );

    await commit();
    assertNotAborted(signal);
    await nextPaint();
    assertNotAborted(signal);

    // Changing origin at scaleX(1) is visually stable.
    cover.style.transformOrigin = "right center";
    await play(
      cover,
      [{ transform: "scaleX(1)" }, { transform: "scaleX(0)" }],
      { duration, easing: "cubic-bezier(.65, 0, .35, 1)", fill: "forwards" },
      signal,
      () => { cover.style.transform = "scaleX(0)"; },
    );
  } finally {
    cover.getAnimations().forEach((animation) => animation.cancel());
    cover.hidden = true;
    cover.style.removeProperty("transform");
    cover.style.removeProperty("transform-origin");
  }
}
```

`commit()` 必须在 promise resolve 前完成目标 DOM 的必要提交。双 RAF 只保证一次提交后的绘制机会，不会自动等待图片、字体、数据或异步组件。关键资源必须由调用方提供显式 ready 条件。

`pointer-events: none` 只保证 cover 不吞掉命中，不会阻止用户操作底层。若事务期间不能接受输入，调用方还必须禁用触发器或建立可恢复的交互状态守卫。

共享同一个 cover 时必须串行化 ownership。下面采用“最新请求获胜”：新请求先取消当前事务，等待其 `finally` 清理，再启动新的事务，避免旧事务把新事务的 cover 隐藏。

```ts
let requestId = 0;
let running: AbortController | null = null;
let tail: Promise<void> = Promise.resolve();

function transitionTo(commit: () => void | Promise<void>) {
  const id = ++requestId;
  running?.abort();

  const task = tail.catch(() => {}).then(async () => {
    if (id !== requestId) return;

    const controller = new AbortController();
    running = controller;
    try {
      await coverSwapUncover({ cover, commit, signal: controller.signal });
    } catch (error) {
      if (!controller.signal.aborted) throw error;
    } finally {
      if (running === controller) running = null;
    }
  });

  tail = task;
  return task;
}
```

取消发生在 `commit` 之后时，保留已提交的新内容并立即清掉 cover。不要在通用控制器里擅自回滚导航。

## Recipe 3：CSS alpha-mask 软边 aperture

把 target 放下层、source 放上层。对 source 挖透明孔：

```css
.aperture-source {
  --x: 50%;
  --y: 50%;
  --r: 0px;
  --feather: 4px;
  -webkit-mask-image: radial-gradient(
    circle at var(--x) var(--y),
    transparent 0 var(--r),
    #000 calc(var(--r) + var(--feather))
  );
  mask-image: radial-gradient(
    circle at var(--x) var(--y),
    transparent 0 var(--r),
    #000 calc(var(--r) + var(--feather))
  );
  mask-mode: alpha;
}
```

若项目已有 Motion，直接用 motion values 更新局部 CSS 变量；不要每帧 set React state：

```tsx
const radius = useMotionValue(0);
const maskImage = useMotionTemplate`radial-gradient(
  circle at ${x}px ${y}px,
  transparent 0 ${radius}px,
  #000 calc(${radius}px + 4px)
)`;

<motion.div
  className="aperture-source"
  style={{ maskImage, WebkitMaskImage: maskImage }}
/>
```

按项目已安装的包导入：新项目可能使用 `motion/react`，旧项目可能使用 `framer-motion`。不要混用两套 Motion 实例。

如果 Motion 对 `WebkitMaskImage` 的类型或 MotionValue 支持不稳定，订阅单个 motion value 并对 source 的 `style.setProperty("--r", `${value}px`)` 做局部写入；在 cleanup 中 unsubscribe。

mask 完成后移除 source 或清空 mask。不要给 target 加同一张反向 mask，否则形状内外会一起消失。

## Recipe 4：View Transition circular reveal

适用于同文档更新且框架能在 callback 内可靠提交 DOM 的场景：

```css
::view-transition-old(root),
::view-transition-new(root) {
  animation: none;
  mix-blend-mode: normal;
}

::view-transition-group(root) { animation: none; }

::view-transition-image-pair(root) { isolation: auto; }

::view-transition-old(root) { z-index: 1; }

::view-transition-new(root) {
  z-index: 2;
  clip-path: circle(0 at var(--vt-x) var(--vt-y));
  animation: reveal-new var(--vt-duration) cubic-bezier(.22, 1, .36, 1) both;
}

@keyframes reveal-new {
  to {
    clip-path: circle(var(--vt-r) at var(--vt-x) var(--vt-y));
  }
}

@media (prefers-reduced-motion: reduce) {
  ::view-transition-old(root),
  ::view-transition-new(root) {
    animation-duration: 1ms;
  }
}
```

```ts
type ViewTransitionLike = {
  finished: Promise<void>;
};

type ViewTransitionDocument = Document & {
  startViewTransition?: (
    update: () => void | Promise<void>,
  ) => ViewTransitionLike;
};

export async function viewTransitionReveal(
  updateDOM: () => void | Promise<void>,
  origin: Point,
) {
  const viewDocument = document as ViewTransitionDocument;

  if (
    typeof viewDocument.startViewTransition !== "function" ||
    prefersReducedMotion()
  ) {
    await updateDOM();
    return;
  }

  const root = document.documentElement;
  const radius = radiusToCover(
    window.innerWidth,
    window.innerHeight,
    origin,
  );
  root.style.setProperty("--vt-x", `${origin.x}px`);
  root.style.setProperty("--vt-y", `${origin.y}px`);
  root.style.setProperty("--vt-r", `${radius}px`);
  root.style.setProperty("--vt-duration", "520ms");

  const transition = viewDocument.startViewTransition(updateDOM);

  try {
    await transition.finished;
  } finally {
    root.style.removeProperty("--vt-x");
    root.style.removeProperty("--vt-y");
    root.style.removeProperty("--vt-r");
    root.style.removeProperty("--vt-duration");
  }
}
```

这段代码假定 origin 是 viewport client coordinate。若来自键盘触发，使用触发器 rect 中心或页面语义中心，不要使用不存在的 pointer 坐标。

框架注意事项：

- React 中，只有在现有架构允许时使用 `flushSync` 让 callback 内的 state 更新同步提交；优先采用路由/框架官方 View Transition 集成。
- 不要把异步数据请求塞进 snapshot callback 里长期阻塞。先准备数据，再启动 transition 提交已准备的 target。
- 页面包含固定 header、播放器等不应跟随 root snapshot 的元素时，为它们分配唯一 `view-transition-name`，并分别定义 old/new 行为。
- update callback 抛错时浏览器会跳过 transition。保留业务层错误处理，不要吞掉提交错误只为了动画完成。

## Motion 与框架适配

- 先检查现有导入路径、Motion 版本和组件惯例。不要在 `motion/react` 与 `framer-motion` 之间迁移项目。
- 使用 Motion 时让一个 `animate()` 或一组 motion values 独占几何属性，并在 effect cleanup 中 `stop()`/unsubscribe。
- `AnimatePresence` 只解决 React 节点的进退场，不会自动保证 target 数据、图片和布局 ready，也不会自动解决 route commit。
- 使用 `useLayoutEffect` 建立首帧几何；SSR 项目需要稳定的服务端 fallback 样式，避免 hydration 前完整 target 闪现。
- React Strict Mode 会在开发环境重放 effect。controller 必须可重复 cleanup，不能假设 effect 只运行一次。
- Vue/Svelte 中使用对应的 before-paint 生命周期和 onDestroy cleanup，保持同一状态机，不要照搬 React 时序假设。

## 首帧、提交和清理

### 首帧

- 让隐藏几何来自同步 render style、CSS class 或 layout effect。
- 启动前读取一次 rect 并写入相同坐标系，不要在一次 frame 内交替多次读写布局。
- target 未 ready 时保持 source 或 cover，不要用透明 target 等待数据。

### 提交

- 用业务层 ready promise 表示数据和关键资源准备完成。
- DOM 提交与像素绘制不是同一事件。必要时等下一 paint；图片/字体必须另行等待。
- 只在完整 cover frame 提交互斥视图。reveal-only 架构则应提前同时挂载两层。

### 清理

在 `finally` 中恢复：

- inline `clip-path`、mask、transform、transform-origin 和 CSS variables；
- `hidden`、`inert`、`aria-hidden`、临时 tab/focus 状态；
- RAF、timeout、ResizeObserver、matchMedia listener、Motion subscription；
- WAAPI animation、View Transition 状态、Canvas/WebGL buffers 和 context listeners；
- 临时 source/target/cover DOM。

只清理当前事务拥有的资源。用 token/controller 检查 ownership，避免旧事务的 finally 把新事务刚写入的状态删掉。
