---
name: qiuye-edge-gradient-mask
description: >-
  Implement edge gradient fade masks so content softly fades out at the edges of
  scroll containers, viewports, marquees, cards and background patterns instead
  of hard clipping. Covers scroll-aware top/bottom fades, horizontal marquee
  fades, fixed viewport edge fades with blur, mask-image on the scroller itself,
  and pattern fade-outs. Use for edge fade, scroll fade, overflow fade, gradient
  mask, mask-image gradient, 边缘渐隐、滚动渐隐遮罩、跑马灯两侧淡出.
  Not for text readability scrims over images (use qiuye-soft-text-backdrop) or
  shape reveal transitions (use geometric-mask-transition).
---

# Edge Gradient Mask (边缘渐变遮罩)

在容器、视口或视觉元素的边缘叠加一层渐变遮罩，使内容柔和地淡出，避免锋利的裁切线。

## 核心原则

- **必须** `pointer-events-none` + `aria-hidden="true"`，遮罩不应拦截点击或干扰无障碍
- **主题适配**：颜色使用 `from-background` 等语义 token（Tailwind）或 CSS 变量，确保亮/暗模式一致
- **z-index**：遮罩要高于被遮内容，但低于操作按钮/控件
- 静态遮罩用纯 CSS；需要根据滚动进度动态显隐时才引入 JS

---

## 场景决策

| 场景 | 推荐方案 | 参考模板 |
|---|---|---|
| 页面/视口固定边缘（如底部常驻遮罩） | A. mask-image + backdrop-blur | 模板 A |
| 小型滚动容器边缘（如 Dialog/列表/Tag 区域） | B. overlay div + 滚动感知显隐 | 模板 B |
| 水平无限滚动条/跑马灯两侧 | C. 左右静态 overlay | 模板 C |
| Section/卡片的装饰性渐变（纯视觉，不涉及滚动） | D. overlay div 或 pseudo-element | 模板 D |
| 纹理/图案的柔和消失 | E. CSS mask-image（遮罩纹理本身） | 模板 E |

---

## 模板 A — 页面/视口固定边缘遮罩

固定在视口底部（或顶部），结合半透明背景 + `backdrop-blur` + `mask-image`，让页面内容柔和淡出。

```tsx
<div
  className="pointer-events-none fixed bottom-0 left-0 right-0 z-[1] h-24 w-full"
  style={{
    // --background 为完整颜色值（如 oklch(...) / #fff）时可用；shadcn + Tailwind v3 的
    // HSL 分量变量（"0 0% 100%"）需改为 "hsl(var(--background) / 0.9)"
    background: "color-mix(in oklab, var(--background) 90%, transparent)",
    backdropFilter: "blur(4px)",
    WebkitBackdropFilter: "blur(4px)",
    maskImage: "linear-gradient(transparent 0%, black 100%)",
    WebkitMaskImage: "linear-gradient(transparent 0%, black 100%)",
  }}
  aria-hidden="true"
/>
```

**关键点**：
- `mask-image` 控制遮罩元素自身的透明度渐变（顶部透明 → 底部不透明）
- `background` 用 `color-mix()` 从主题变量派生半透明色（比 `oklch(from ...)` 相对颜色语法支持更广）；先确认 `--background` 存的是完整颜色还是 HSL 分量
- `mask-image` 同时作用于自身背景和 `backdrop-filter` 的结果，模糊会随渐变一起淡出；模糊只采样元素自身矩形下方的内容，不需要 `isolate` 来“限制范围”
- `backdrop-filter` 需同时写 `WebkitBackdropFilter`（Safari 18 以前只认前缀版）；祖先上的 `filter` / `opacity < 1` / `mask` 等会让它失效，排查见 frontend-pitfalls 的 backdrop-filter case
- 顶部遮罩则 `top-0` + 渐变方向反转：`linear-gradient(black 0%, transparent 100%)`

---

## 模板 B — 滚动容器边缘遮罩（滚动感知显隐）

在可滚动容器的顶部/底部显示渐变遮罩，根据滚动位置动态显隐。

### 1. 滚动状态检测

```tsx
const containerRef = useRef<HTMLDivElement>(null);
const [showTopFade, setShowTopFade] = useState(false);
const [showBottomFade, setShowBottomFade] = useState(false);

const checkScroll = useCallback(() => {
  const el = containerRef.current;
  if (!el) return;
  const { scrollTop, scrollHeight, clientHeight } = el;
  const maxScroll = scrollHeight - clientHeight;
  setShowTopFade(scrollTop > 1);
  setShowBottomFade(maxScroll > 0 && scrollTop < maxScroll - 1);
}, []);

useEffect(() => {
  const el = containerRef.current;
  if (!el) return;
  el.addEventListener("scroll", checkScroll, { passive: true });
  const ro = new ResizeObserver(checkScroll);
  ro.observe(el);
  checkScroll();
  return () => {
    el.removeEventListener("scroll", checkScroll);
    ro.disconnect();
  };
}, [checkScroll]);
```

### 2. 渐变遮罩渲染

遮罩必须是滚动容器的**兄弟节点**，由不滚动的外层 `relative` 包裹定位。若把 `absolute` 遮罩放进 `overflow-auto` 容器内部，它会跟随内容一起滚走：顶部遮罩滚出视野，底部遮罩停在内容中段。

```tsx
import { AnimatePresence, motion } from "motion/react";

<div className="relative">
  <div ref={containerRef} className="max-h-80 overflow-auto">
    {children}
  </div>

  <AnimatePresence>
    {showTopFade && (
      <motion.div
        aria-hidden="true"
        className="pointer-events-none absolute left-0 right-0 top-0 z-[5]
                   h-10 bg-gradient-to-b from-background to-transparent"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.2, ease: "easeOut" }}
      />
    )}
  </AnimatePresence>

  <AnimatePresence>
    {showBottomFade && (
      <motion.div
        aria-hidden="true"
        className="pointer-events-none absolute left-0 right-0 bottom-0 z-[5]
                   h-10 bg-gradient-to-t from-background to-transparent"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.2, ease: "easeOut" }}
      />
    )}
  </AnimatePresence>
</div>
```

**关键点**：
- `bg-gradient-to-b from-background to-transparent`：从实色到透明的渐变（Tailwind v4 写作 `bg-linear-to-b`）
- `AnimatePresence` + `motion.div` 实现平滑的淡入淡出
- 外层 `relative` 不滚动，负责定位遮罩；内层负责 `overflow-auto`
- 有常驻滚动条时，遮罩会盖住滚动条：给遮罩设 `right` 等于滚动条宽度，或改用下方的 mask 方案
- 遮罩高度（`h-10`）按场景调整，通常 24px–56px

### 变体：直接在滚动容器上加 `mask-image`

内容下方是图片、渐变或半透明背景，找不到可匹配的实色时，不用 overlay，直接让滚动容器自身淡出。mask 跟随容器盒而非内容，不会滚走；代价是滚动条也会一起被淡化。

```tsx
const FADE = 40;
const mask = `linear-gradient(to bottom,
  transparent 0, black ${showTopFade ? FADE : 0}px,
  black calc(100% - ${showBottomFade ? FADE : 0}px), transparent 100%)`;

<div
  ref={containerRef}
  className="max-h-80 overflow-auto"
  style={{ maskImage: mask, WebkitMaskImage: mask }}
>
  {children}
</div>
```

### 简化版（不需要动画）

当不需要平滑过渡动画时，可直接用条件渲染（同样放在外层 `relative` 中、滚动容器之外）：

```tsx
{showTopFade && (
  <div
    aria-hidden="true"
    className="pointer-events-none absolute left-0 right-0 top-0 z-[5]
               h-10 bg-gradient-to-b from-background to-transparent"
  />
)}
```

### 折叠/展开场景的底部遮罩

对于"展开查看更多"的场景（如 Tag 列表折叠态），仅在折叠时显示底部遮罩：

```tsx
<AnimatePresence>
  {needsExpansion && !isExpanded && (
    <motion.div
      aria-hidden="true"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.1 }}
      className="absolute -bottom-px left-0 right-0 z-30 pointer-events-none"
    >
      <div className="h-10 bg-gradient-to-t from-background to-transparent" />
    </motion.div>
  )}
</AnimatePresence>
```

---

## 模板 C — 水平无限滚动/跑马灯两侧遮罩

覆盖横向滚动内容的左右两侧，使内容柔和消失于容器边缘。

```tsx
<div className="relative">
  {/* 左侧渐变遮罩 */}
  <div
    className="pointer-events-none absolute top-0 bottom-0 left-0 z-10
               w-24 sm:w-32 bg-gradient-to-r from-background via-background/80 to-transparent"
    aria-hidden="true"
  />
  {/* 右侧渐变遮罩 */}
  <div
    className="pointer-events-none absolute top-0 bottom-0 right-0 z-10
               w-24 sm:w-32 bg-gradient-to-l from-background via-background/80 to-transparent"
    aria-hidden="true"
  />

  {/* 横向滚动内容 */}
  <div className="overflow-hidden">
    {children}
  </div>
</div>
```

**关键点**：
- `via-background/80` 添加中间色阶，让渐变更柔和、渐变带更宽
- 宽度用 `w-24 sm:w-32` 做响应式，移动端窄一些
- 父容器需 `relative`；内容区可以是 `overflow-hidden`

---

## 模板 D — 装饰性渐变边缘

用于卡片、Section 等的纯视觉装饰，不涉及滚动逻辑。

### Overlay div 方式

```tsx
<div className="relative overflow-hidden">
  {/* 内容 */}
  {children}

  {/* 底部装饰渐变 */}
  <div
    className="pointer-events-none absolute bottom-0 left-0 right-0 h-20
               bg-gradient-to-t from-background to-transparent"
    aria-hidden="true"
  />
</div>
```

### Pseudo-element 方式（Tailwind）

适合在单个元素的 className 中完成，不增加 DOM 层级：

```tsx
<div
  className="relative after:absolute after:bottom-0 after:left-0 after:right-0
             after:h-20 after:bg-gradient-to-t after:from-background
             after:to-transparent after:pointer-events-none after:content-['']"
>
  {children}
</div>
```

---

## 模板 E — CSS mask-image 遮罩纹理/图案

让纹理、网格等背景图案在边缘柔和消失，而不是在容器边界硬切。

```tsx
<div
  className="absolute inset-0"
  style={{
    backgroundImage: `linear-gradient(to right, currentColor 1px, transparent 1px),
                      linear-gradient(to bottom, currentColor 1px, transparent 1px)`,
    backgroundSize: "48px 48px",
    maskImage:
      "radial-gradient(ellipse 80% 50% at center top, black 0%, transparent 100%)",
    WebkitMaskImage:
      "radial-gradient(ellipse 80% 50% at center top, black 0%, transparent 100%)",
  }}
/>
```

**关键点**：
- `mask-image` 作用于元素自身，控制哪些区域可见（`black` = 可见，`transparent` = 不可见）
- 渐变形状用 `radial-gradient(ellipse ...)` 或 `linear-gradient(...)` 按需选择
- 上例让网格在顶部中央清晰、向四周淡出；若要反过来在中央挖空（例如给标题让位），交换 `black` 与 `transparent`
- 同时写 `maskImage` 和 `WebkitMaskImage`：无前缀版在 Chrome 120+、Safari 15.4+、Firefox 53+ 可用，前缀版兜底更旧的 Chromium / Safari

---

## 颜色与主题适配

| 优先级 | 方式 | 示例 |
|---|---|---|
| 1 | Tailwind 语义 token | `from-background to-transparent` |
| 2 | CSS 变量派生 | `color-mix(in oklab, var(--background) 90%, transparent)`；HSL 分量变量用 `hsl(var(--background) / 0.9)` |
| 3 | 亮/暗分别指定 | `from-[#fcfcfc] dark:from-[#121212]` |

优先使用方式 1；需要透明度控制时使用方式 2；仅在语义 token 无法精确匹配时使用方式 3。

---

## 常见陷阱

- **缺少 `pointer-events-none`**：遮罩会拦截下方元素的点击
- **缺少 `aria-hidden="true"`**：屏幕阅读器会读到空的装饰性元素
- **忘记 `WebkitMaskImage` / `WebkitBackdropFilter`**：较旧的 Chromium（<120）与 Safari 只认前缀版本
- **遮罩放进了滚动容器内部**：`absolute` 遮罩会随内容滚走，应作为滚动容器的兄弟节点
- **z-index 不当**：遮罩需要高于内容、低于交互控件
- **背景色不匹配**：渐变的实色端必须与容器/页面背景一致，否则会出现色差
- **容器缺少 `relative`**：`absolute` 定位的遮罩需要最近的 `relative` 父级
- **容器缺少 `overflow-hidden`**：遮罩可能溢出容器可见范围
