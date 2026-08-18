# Case 5: 测量内容高度并平滑动画 `auto -> auto`

## 目标

让同一个容器在内容增删、异步数据返回、校验信息出现、图片加载或响应式换行后，从一个自然高度平滑过渡到另一个自然高度。

Motion 可以直接处理 `0 -> auto`，但不能可靠地在两个未知的 `auto` 高度之间补间。这个 case 使用双层结构：测量保持自然布局的内层，把得到的像素高度交给外层 `motion.div` 动画。

---

## 适用场景

典型需求表述：

- 「展开额外说明后，卡片高度要平滑变化」
- 「表单错误出现时，不要把下面的操作区突然顶下去」
- 「异步详情加载后，抽屉 / 面板高度要自然长开」
- 「内容还是同一个组件，没有 key 切换，但高度会动态变化」
- 「需要用 `useMeasure` / `ResizeObserver` 动画 dynamic height」
- 「Motion 怎么做 `auto -> auto` 高度动画」

典型 UI：设置卡片、Family Drawer、FAQ 详情、表单帮助区、可变文案按钮附近的说明面板、异步预览、筛选摘要、内联错误区。

以下场景优先使用其他方案：

| 场景 | 优先方案 |
|---|---|
| 单纯展开 / 收起 | 直接动画 `height: 0 <-> "auto"`，无需持续测量 |
| 带 `key` 的两块内容互换，且需要退出动画 | 读取 Case 2，使用 `AnimatePresence mode="popLayout"` + `layout` |
| 只需让外框和相邻元素跟随普通 React 重排 | 先尝试 `layout`；效果足够时不要增加 observer |
| 同一个内容树会反复变高 / 变矮，需要精确裁剪高度 | 使用本 case 的测量方案 |

---

## 核心设计原则

### 1. 分离“自然高度测量层”和“动画裁剪层”

不要在同一个元素上同时设置 `ref` 和动画后的 `height`。一旦外层被固定为某个像素高度，再测量它只会读回被动画约束的高度，无法发现内容的新自然高度。

```tsx
<motion.div animate={{ height: measuredHeight }} className="overflow-hidden">
  <div ref={measureRef}>{children}</div>
</motion.div>
```

- 外层：接收像素高度、执行动画、裁剪过渡期间的溢出。
- 内层：始终保持 `height: auto`，由 `ResizeObserver` 读取真实尺寸。

### 2. 首次测量前保持 `auto`

Observer 要在首次布局后才会返回尺寸。不要把初始的 `0` 当成真实高度，否则服务端渲染或首次挂载时会先塌陷再展开。

```tsx
animate={{ height: bounds.height > 0 ? bounds.height : "auto" }}
```

如果合法内容可能真的是 `0px`，使用下方原生 hook 的 `number | null` 状态区分“未测量”和“测量结果为 0”。

### 3. 把 padding 放在被测量的内层

外层只负责高度和裁剪。将 padding 放在内层，Observer 才能把完整视觉高度纳入目标值。

```tsx
<motion.div className="overflow-hidden">
  <div ref={measureRef} className="p-4">
    {children}
  </div>
</motion.div>
```

被测量根节点避免使用会逸出边界的垂直 margin；优先使用 `padding`、`gap` 或 `space-y-*`。

### 4. Observer 负责追踪目标值，Motion 负责补间

`ResizeObserver` 能捕获的不只是 React state 变化，还包括：

- 容器宽度变化导致的文字换行
- Web Font 替换后的行高变化
- 图片、图表或异步组件加载后的尺寸变化
- 子组件内部状态改变

不要只在业务状态变化时手动读取一次 `scrollHeight`，否则这些变化会漏掉。

### 5. 只对离散变化做高度动画

高度动画会触发布局计算，适合低频、用户可感知的内容变化。实时日志、逐 token 输出、拖拽 resize 或每帧变化的图表不要持续跑 spring；这些场景让高度立即更新，或只在变化结束后动画一次。

---

## 推荐实现模板

### 方案 A：项目已有 `react-use-measure`

先检查依赖；项目已经使用时优先复用，不要仅为一个简单容器盲目新增依赖。

```tsx
"use client";

import useMeasure from "react-use-measure";
import { motion, useReducedMotion } from "motion/react";

const heightTransition = {
  type: "spring" as const,
  duration: 0.36,
  bounce: 0,
};

export function AnimatedAutoHeight({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  const [measureRef, bounds] = useMeasure();
  const prefersReducedMotion = useReducedMotion();

  return (
    <motion.div
      initial={false}
      animate={{ height: bounds.height > 0 ? bounds.height : "auto" }}
      transition={prefersReducedMotion ? { duration: 0 } : heightTransition}
      className={`box-content overflow-hidden ${className ?? ""}`}
    >
      <div ref={measureRef}>{children}</div>
    </motion.div>
  );
}
```

用法：

```tsx
<AnimatedAutoHeight className="rounded-lg border bg-background">
  <div className="space-y-3 p-4">
    <h2 className="text-sm font-medium">Family drawer</h2>
    <p className="text-sm text-muted-foreground">基础说明内容。</p>
    {showExtraContent ? (
      <p className="text-sm text-muted-foreground">动态出现的额外内容。</p>
    ) : null}
  </div>
</AnimatedAutoHeight>
```

`box-content` 让测得的内层高度对应外层 content box；即使调用方把 border 放在动画层，也不会因全局 `border-box` 少算边框宽度。

### 方案 B：不增加依赖，使用原生 `ResizeObserver`

用 `null` 表示首次测量尚未发生，因此真实的 `0px` 也可以被正确处理。

```tsx
"use client";

import { useEffect, useRef, useState } from "react";
import { motion, useReducedMotion } from "motion/react";

function useElementHeight<T extends HTMLElement>() {
  const ref = useRef<T>(null);
  const [height, setHeight] = useState<number | null>(null);

  useEffect(() => {
    const element = ref.current;
    if (!element || typeof ResizeObserver === "undefined") return;

    const update = () => {
      const nextHeight = element.getBoundingClientRect().height;
      setHeight((currentHeight) =>
        currentHeight !== null && Math.abs(currentHeight - nextHeight) < 0.5
          ? currentHeight
          : nextHeight,
      );
    };

    update();
    const observer = new ResizeObserver(update);
    observer.observe(element);

    return () => observer.disconnect();
  }, []);

  return [ref, height] as const;
}

export function AnimatedAutoHeight({ children }: { children: React.ReactNode }) {
  const [measureRef, measuredHeight] = useElementHeight<HTMLDivElement>();
  const prefersReducedMotion = useReducedMotion();

  return (
    <motion.div
      initial={false}
      animate={{ height: measuredHeight ?? "auto" }}
      transition={
        prefersReducedMotion
          ? { duration: 0 }
          : { type: "spring", duration: 0.36, bounce: 0 }
      }
      className="box-content overflow-hidden"
    >
      <div ref={measureRef} className="space-y-3 p-4">
        {children}
      </div>
    </motion.div>
  );
}
```

如果组件可能在不支持 `ResizeObserver` 的环境运行，加载 polyfill，或在 fallback 中保持 `height: auto`。不要轮询尺寸。

---

## AI Agent 执行步骤

### Step 1: 判断是不是 `auto -> auto`

确认内容在变化前后都依赖自然高度，而不是简单的展开 / 收起。搜索当前实现中的 `height: "auto"`、`scrollHeight`、`ResizeObserver`、`useMeasure`、`layout` 和 CSS `transition-[height]`。

### Step 2: 先选择最轻方案

按以下顺序决策：

1. 单次 `0 <-> auto`：直接使用 Motion target。
2. 普通重排：先尝试 `layout`。
3. keyed 内容互换：读取 Case 2。
4. 同一内容树需要连续得到明确高度：使用双层测量结构。

### Step 3: 建立双层 DOM

新增外层 `motion.div`，把现有内容与 padding 移入内层普通元素。只给内层挂测量 ref，只给外层设置动画高度。

### Step 4: 接入已有依赖或原生 Observer

项目已有 `react-use-measure` 时直接复用；否则优先使用小型原生 hook。Observer 必须在 effect cleanup 中 `disconnect()`。

### Step 5: 处理首帧、裁剪和 reduced motion

- 未测量时使用 `height: auto`
- 外层使用 `overflow-hidden`
- `initial={false}`，避免挂载时多做一次高度入场
- reduced motion 下把 duration 设为 `0`

### Step 6: 验证所有尺寸来源

至少验证：内容变高、内容变矮、容器宽度变化。涉及图片、Web Font 或异步组件时，也要验证资源加载后的高度更新。

---

## 常见坑与修复

### 坑 1: 在同一个元素上测量并动画

**现象**：第一次动画后高度不再更新，或 observer 持续读到动画中的中间值。

**原因**：测量对象已经被显式 `height` 约束，失去自然高度。

**修复**：内层测量，外层动画；不要合并两个节点。

### 坑 2: 首帧从 0 展开

**原因**：把 observer 的初始占位值 `0` 当成了真实尺寸。

**修复**：首次测量前保持 `auto`，并使用 `initial={false}`。需要支持真实零高度时，用 `null` 表示未测量。

### 坑 3: padding 写在动画外层

**现象**：目标高度少一截、收缩结束时跳动，或内容仍从边缘露出。

**修复**：把影响整体高度的 padding 放到被测量内层。

### 坑 4: 忘记裁剪

**现象**：外框正在变矮，但文字和控件提前穿出边界。

**修复**：外层添加 `overflow-hidden`。如果这会裁掉 focus ring 或阴影，把视觉装饰放到动画裁剪层之外，不要移除必要裁剪。

### 坑 5: CSS 和 Motion 同时控制高度

**现象**：动画迟滞、抖动或时长不可预测。

**修复**：移除外层的 `transition-all`、`transition-[height]` 和 height keyframes，让高度只由 Motion 控制。

### 坑 6: 对高频流式内容持续使用 spring

**现象**：容器一直追赶目标高度，滚动位置不稳定，主线程布局压力升高。

**修复**：流式阶段直接使用 `auto` / 瞬时高度，完成后再恢复动画；或者完全取消该区域的高度动画。

### 坑 7: 外层 border 导致目标高度少 1–2px

**原因**：Tailwind Preflight 默认使用 `box-sizing: border-box`。把内层高度直接写到带 border 的外层后，边框会占用这段高度的一部分。

**修复**：动画层使用 `box-content`，或把 border 放到被测量内层。不要在代码里写死 `+ 2`，边框宽度和主题可能变化。

---

## 动效参数建议

```tsx
// 设置页、表单、数据工具
{ type: "spring", duration: 0.32, bounce: 0 }

// 通用卡片、详情面板
{ type: "spring", duration: 0.36, bounce: 0 }

// 内容变化幅度很小，使用 tween 更克制
{ duration: 0.22, ease: [0.25, 0.46, 0.45, 0.94] as const }
```

高度变化不要使用明显 bounce。过冲会让外框短暂超过内容高度，显得像布局错误。

---

## 验收清单

- [ ] 内容变高时外框连续展开，没有瞬间跳到目标高度
- [ ] 内容变矮时外框连续收回，内容没有穿出边界
- [ ] 首次渲染没有从 `0px` 展开或产生额外 layout shift
- [ ] 调整容器宽度导致文字换行时，高度仍会更新
- [ ] 图片、字体或异步子组件加载后，Observer 能得到新高度
- [ ] 测量 ref 与动画 height 不在同一个 DOM 元素上
- [ ] padding 位于被测量内层，目标高度包含完整间距
- [ ] 动画外层带 border 时使用 `box-content`，没有 1–2px 裁切
- [ ] Observer 在卸载时已断开，没有 Strict Mode 重复订阅
- [ ] CSS transition / keyframes 没有同时控制外层 height
- [ ] reduced motion 下高度立即更新
- [ ] 高频内容变化不会持续触发追赶式 spring
- [ ] TypeScript、lint 和项目构建通过

---

## 推荐回答格式

```text
已把动态内容改为双层 auto-height 动画：内层保持自然布局并由 ResizeObserver 持续测量，外层 Motion 容器只负责从旧像素高度补间到新高度。

首次测量前保留 auto，避免首帧从 0 展开；padding 放在测量层，外层负责 overflow 裁剪，并为 reduced motion 关闭了高度补间。
```

---

## 最小代码骨架

```tsx
import useMeasure from "react-use-measure";
import { motion } from "motion/react";

export function MeasuredHeight({ children }: { children: React.ReactNode }) {
  const [measureRef, bounds] = useMeasure();

  return (
    <motion.div
      initial={false}
      animate={{ height: bounds.height > 0 ? bounds.height : "auto" }}
      transition={{ type: "spring", duration: 0.36, bounce: 0 }}
      className="box-content overflow-hidden"
    >
      <div ref={measureRef} className="p-4">
        {children}
      </div>
    </motion.div>
  );
}
```
