---
name: qiuye-edge-gradient-mask
description: >-
  Implement edge gradient fade masks for scrollable areas, viewports, sections,
  and visual elements. Use when adding soft fade-out edges to scroll containers,
  page borders, infinite scroll strips, card edges, or any area that needs a
  smooth gradient transition instead of a hard clip. Covers scroll-aware
  show/hide, horizontal/vertical fades, CSS mask-image, and overlay div
  approaches. Triggers on: "edge fade", "gradient mask", "scroll fade",
  "fade edge", "edge mask", "soft edge", "gradient overlay", "scroll shadow",
  "overflow fade", "mask-image gradient", "edge blur".
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
  className="pointer-events-none fixed bottom-0 left-0 right-0 z-[1] isolate h-24 w-full"
  style={{
    background: "oklch(from var(--background) l c h / 90%)",
    backdropFilter: "blur(4px)",
    maskImage: "linear-gradient(transparent 0%, black 100%)",
    WebkitMaskImage: "linear-gradient(transparent 0%, black 100%)",
  }}
  aria-hidden="true"
/>
```

**关键点**：
- `mask-image` 控制遮罩元素自身的透明度渐变（顶部透明 → 底部不透明）
- `background` 使用 `oklch(from var(--background) ...)` 从主题变量派生颜色
- `isolate` 创建独立层叠上下文，避免 `backdrop-blur` 影响范围溢出
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

```tsx
<div ref={containerRef} className="relative overflow-auto">
  {children}

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
- `bg-gradient-to-b from-background to-transparent`：从实色到透明的渐变
- `AnimatePresence` + `motion.div` 实现平滑的淡入淡出
- 父容器需 `relative` + `overflow-auto/hidden/scroll`
- 遮罩高度（`h-10`）按场景调整，通常 24px–56px

### 简化版（不需要动画）

当不需要平滑过渡动画时，可直接用条件渲染：

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
      "radial-gradient(ellipse 80% 50% at center top, transparent 0%, black 80%)",
    WebkitMaskImage:
      "radial-gradient(ellipse 80% 50% at center top, transparent 0%, black 80%)",
  }}
/>
```

**关键点**：
- `mask-image` 作用于元素自身，控制哪些区域可见（`black` = 可见，`transparent` = 不可见）
- 渐变形状用 `radial-gradient(ellipse ...)` 或 `linear-gradient(...)` 按需选择
- 始终同时写 `maskImage` 和 `WebkitMaskImage`（Safari 兼容）

---

## 颜色与主题适配

| 优先级 | 方式 | 示例 |
|---|---|---|
| 1 | Tailwind 语义 token | `from-background to-transparent` |
| 2 | CSS 变量派生 | `oklch(from var(--background) l c h / 90%)` |
| 3 | 亮/暗分别指定 | `from-[#fcfcfc] dark:from-[#121212]` |

优先使用方式 1；需要透明度控制时使用方式 2；仅在语义 token 无法精确匹配时使用方式 3。

---

## 常见陷阱

- **缺少 `pointer-events-none`**：遮罩会拦截下方元素的点击
- **缺少 `aria-hidden="true"`**：屏幕阅读器会读到空的装饰性元素
- **忘记 `WebkitMaskImage`**：Safari 需要带前缀的版本
- **z-index 不当**：遮罩需要高于内容、低于交互控件
- **背景色不匹配**：渐变的实色端必须与容器/页面背景一致，否则会出现色差
- **容器缺少 `relative`**：`absolute` 定位的遮罩需要最近的 `relative` 父级
- **容器缺少 `overflow-hidden`**：遮罩可能溢出容器可见范围
