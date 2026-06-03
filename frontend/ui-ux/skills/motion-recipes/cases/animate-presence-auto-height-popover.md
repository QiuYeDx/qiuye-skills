# Case 2: AnimatePresence 内容切换与 Popover 高度平滑过渡

## 目标

修复 Popover / Card / Wizard Step 内容切换时，因新旧内容高度不同导致容器高度突然跳变的问题。

重点解决：

- `AnimatePresence mode="wait"` 在 auto-height 容器中造成高度突变
- 内容行数变化时，父级 Popover 高度没有被 Motion 平滑接管
- 旧内容淡出和新内容淡入之间出现一帧同步重排
- 保持内容过渡、容器高度过渡和外层 layoutId 迁移协调

---

## 适用场景

典型需求表述：

- 「Popover 上一步/下一步切换时，高度突然跳了一下」
- 「Content 行数不同，旧内容淡出后新高度突然出现」
- 「AnimatePresence mode wait 慢放能看到高度突变」
- 「Tour / Stepper / Wizard 内容切换时，卡片高度要平滑」
- 「修复 auto-height 内容过渡」

典型 UI：Tour Popover、Onboarding Stepper、Wizard Card、Command Palette Detail、Tooltip Help Card、设置页说明卡片。

---

## 核心设计原则

### 1. auto-height 内容不要默认使用 `mode="wait"`

`mode="wait"` 会等旧内容退出完成后再挂载新内容。对于自动高度容器，新内容挂载的那一帧会立即改变父级高度，因此慢放会看到高度突变。

```tsx
// 避免：内容高度不同且父级依赖 auto-height 时容易跳变
<AnimatePresence mode="wait">
  <motion.div key={activeStep}>{content}</motion.div>
</AnimatePresence>
```

### 2. 让父容器和内容容器都参与 layout 动画

父级 Popover、本体 padding 容器、内容区域都加 `layout`，让 Motion 捕获旧尺寸和新尺寸并补间。

```tsx
<motion.div layout className="rounded-lg border bg-popover">
  <motion.div layout className="space-y-4 p-4">
    <motion.div layout className="relative overflow-hidden">
      {/* AnimatePresence 放这里 */}
    </motion.div>
  </motion.div>
</motion.div>
```

### 3. 内容切换用 `mode="popLayout"`

`popLayout` 会把退出元素从布局流中弹出，让新内容立即进入布局。父级 layout 动画能从旧高度平滑过渡到新高度，旧内容则继续淡出。

```tsx
<AnimatePresence mode="popLayout" initial={false}>
  <motion.div key={activeKey} layout>
    {content}
  </motion.div>
</AnimatePresence>
```

### 4. 内容区域加 `overflow-hidden`

高度过渡期间旧内容和新内容可能短暂交叠或越界，内容区加 `overflow-hidden` 可以避免文字露出容器边界。

```tsx
<motion.div layout className="relative overflow-hidden">
  ...
</motion.div>
```

### 5. 外层定位依赖尺寸时，ResizeObserver 仍要保留

如果 Popover 位置计算依赖自身高度（例如 collision / placement fallback），保留 `ResizeObserver` 更新 popover 尺寸。layout 动画解决视觉过渡，测量更新解决最终定位。

---

## 推荐实现模板

### 1. 定义统一 transition

```tsx
const layoutTransition = {
  type: "spring" as const,
  duration: 0.5,
  bounce: 0,
};

const contentTransition = {
  type: "spring" as const,
  duration: 0.5,
  bounce: 0,
};
```

### 2. 外层 Popover 参与 layout

```tsx
<motion.div
  layout
  layoutId="tour-popover"
  className="fixed rounded-lg border bg-popover shadow-2xl"
  style={{ top, left, width }}
  transition={layoutTransition}
>
  {/* inner layout */}
</motion.div>
```

### 3. Header / Content / Footer 都参与 layout

```tsx
<motion.div layout className="space-y-4 p-4" transition={layoutTransition}>
  <motion.div layout className="flex items-start justify-between gap-3" transition={layoutTransition}>
    <h2>{title}</h2>
    <span>{index + 1} / {total}</span>
  </motion.div>

  <motion.div layout className="relative overflow-hidden" transition={layoutTransition}>
    <AnimatePresence mode="popLayout" initial={false}>
      <motion.div
        key={stepKey}
        layout
        initial={{ opacity: 0, y: 4 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -4 }}
        transition={contentTransition}
      >
        {content}
      </motion.div>
    </AnimatePresence>
  </motion.div>

  <motion.div layout className="flex items-center justify-between gap-2" transition={layoutTransition}>
    {/* actions */}
  </motion.div>
</motion.div>
```

### 4. 减少动态效果时只保留 opacity

```tsx
const prefersReducedMotion = useReducedMotion();

<motion.div
  initial={prefersReducedMotion ? { opacity: 0 } : { opacity: 0, y: 4 }}
  animate={{ opacity: 1, y: 0 }}
  exit={prefersReducedMotion ? { opacity: 0 } : { opacity: 0, y: -4 }}
/>
```

---

## AI Agent 执行步骤

### Step 1: 定位高度突变来源

检查是否满足以下条件：

- 内容由 `AnimatePresence` 根据 `key` 切换
- 父容器高度是 auto，而不是固定高度
- 新旧内容行数或控件数量不同
- 当前使用 `mode="wait"` 或旧内容退出后才渲染新内容

### Step 2: 把等待式切换改成布局式切换

将：

```tsx
<AnimatePresence mode="wait">
```

替换为：

```tsx
<AnimatePresence mode="popLayout" initial={false}>
```

### Step 3: 给高度相关容器加 `layout`

至少给这些元素加：

- 外层 Popover / Card 容器
- padding 内容壳
- 内容区域容器
- key 变化的内容元素

### Step 4: 给内容裁剪容器加 `overflow-hidden`

如果内容高度过渡时文字露出边界，给包裹内容的 layout 容器加：

```tsx
className="relative overflow-hidden"
```

### Step 5: 保留或补充尺寸测量

如果定位算法依赖 popover 高度，保留 `ResizeObserver`。不要用固定高度掩盖问题，除非设计明确要求固定尺寸。

### Step 6: 用慢放或 DevTools 验收

重点观察：

- 旧内容淡出到新内容淡入之间是否还有高度跳变
- Popover 外框是否平滑变高/变矮
- Footer 是否跟随高度过渡平滑移动
- 外层 `layoutId` 位置迁移是否仍流畅

---

## 常见坑与修复

### 坑 1: `mode="wait"` 造成 auto-height 跳变

**现象**：旧内容淡出结束后，popover 高度突然变成新内容高度，然后新内容淡入。

**原因**：`wait` 会推迟新内容挂载，父级 auto-height 在新内容挂载那一帧同步重排。

**修复**：

```tsx
<AnimatePresence mode="popLayout" initial={false}>
  <motion.div key={stepKey} layout>
    {content}
  </motion.div>
</AnimatePresence>
```

### 坑 2: 只给外层加 `layout`，内部仍跳

**原因**：内部 header/content/footer 的布局变化没有被 Motion 细分捕获。

**修复**：给 padding 壳、内容壳、footer 都加 `layout`。

### 坑 3: 退出内容影响新内容布局

**原因**：退出元素仍占据布局空间。

**修复**：使用 `mode="popLayout"`，让退出元素从布局流中弹出。

### 坑 4: 内容淡出时露出容器边缘

**修复**：

```tsx
<motion.div layout className="relative overflow-hidden">
```

### 坑 5: CSS transition 与 Motion layout 叠加

不要同时给同一容器写 `transition-all` / `transition-[height]` 和 Motion `layout`。高度和位置交给 Motion，颜色 hover 等非布局属性才交给 CSS transition。

---

## 动效参数建议

### Popover layout

```tsx
{
  type: "spring" as const,
  duration: 0.5,
  bounce: 0,
};
```

适合 Tour / Popover：响应快慢适中、过渡稳，不会拖泥带水。

### 内容淡入淡出

```tsx
initial: { opacity: 0, y: 4 }
animate: { opacity: 1, y: 0 }
exit: { opacity: 0, y: -4 }
transition: {
  type: "spring" as const,
  duration: 0.5,
  bounce: 0,
};
```

位移保持在 `4px` 左右，避免内容切换和高度动画互相抢注意力。

---

## 变体模式

### 固定高度内容

如果内容区域固定高度，`mode="wait"` 仍然可以使用：

```tsx
<div className="h-48 overflow-hidden">
  <AnimatePresence mode="wait">
    ...
  </AnimatePresence>
</div>
```

### 只做高度过渡，不做内容位移

```tsx
<motion.div
  key={stepKey}
  layout
  initial={{ opacity: 0 }}
  animate={{ opacity: 1 }}
  exit={{ opacity: 0 }}
/>
```

### 外层还有 spotlight / shared layout

如果外层同时有 spotlight 或 modal `layoutId` 迁移，用 `LayoutGroup` 包住相关 motion 节点，避免共享布局彼此割裂：

```tsx
<LayoutGroup id="tour-layout">
  <motion.div layoutId="tour-spotlight" />
  <motion.div layout layoutId="tour-popover">...</motion.div>
</LayoutGroup>
```

---

## 验收清单

- [ ] 新旧内容行数不同，popover 高度没有突然跳变
- [ ] 旧内容淡出和新内容淡入期间，外框高度平滑变化
- [ ] Footer 跟随内容高度变化平滑移动
- [ ] 内容没有在高度过渡中露出容器边界
- [ ] 外层 popover 的位置 / placement 计算最终正确
- [ ] 外层 `layoutId` 迁移动画仍然正常
- [ ] TypeScript 无 Motion 类型错误
- [ ] 没有用 CSS `transition-height` 和 Motion `layout` 控制同一高度
- [ ] 开启 reduced motion 时，没有明显位移动画

---

## 推荐回答格式

Agent 完成修复后，简要说明：

1. 把内容切换从 `mode="wait"` 改为 `mode="popLayout"`
2. 给 popover 内部高度相关容器加了 `layout`
3. 内容壳加了 `overflow-hidden`
4. 已验证 lint/build，并同步 registry（如果组件库需要）

示例：

```text
已修复。根因是 auto-height 容器里使用 `AnimatePresence mode="wait"`，旧内容退出后新内容挂载导致父级高度同步跳变。

现在内容区使用 `mode="popLayout"`，新内容立即进入布局，旧内容弹出淡出；popover、内容壳和 footer 都参与 `layout`，高度会由 Motion 平滑补间。
```

---

## 最小代码骨架

```tsx
import { AnimatePresence, motion, useReducedMotion } from "motion/react";

const layoutTransition = {
  type: "spring" as const,
  duration: 0.5,
  bounce: 0,
};

export function AnimatedPopoverContent({
  stepKey,
  title,
  content,
  footer,
}: {
  stepKey: string;
  title: React.ReactNode;
  content: React.ReactNode;
  footer: React.ReactNode;
}) {
  const prefersReducedMotion = useReducedMotion();

  return (
    <motion.div layout className="rounded-lg border bg-popover" transition={layoutTransition}>
      <motion.div layout className="space-y-4 p-4" transition={layoutTransition}>
        <motion.div layout transition={layoutTransition}>
          {title}
        </motion.div>

        <motion.div layout className="relative overflow-hidden" transition={layoutTransition}>
          <AnimatePresence mode="popLayout" initial={false}>
            <motion.div
              key={stepKey}
              layout
              initial={prefersReducedMotion ? { opacity: 0 } : { opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={prefersReducedMotion ? { opacity: 0 } : { opacity: 0, y: -4 }}
              transition={
                prefersReducedMotion
                  ? { duration: 0.18, ease: "easeOut" }
                  : {
  type: "spring" as const,
  duration: 0.5,
  bounce: 0,
};
              }
            >
              {content}
            </motion.div>
          </AnimatePresence>
        </motion.div>

        <motion.div layout transition={layoutTransition}>
          {footer}
        </motion.div>
      </motion.div>
    </motion.div>
  );
}
```
