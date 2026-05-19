# Case 1: 使用 Motion `layoutId` 实现导航切换动效与内容过渡

## 目标

使用 Motion 的 `layoutId` 实现活跃态指示器在多个导航项之间的平滑过渡，并为内容区域添加方向感知的进入/退出动画。

重点解决：

- 用 `layoutId` 实现活跃背景/边框在多个导航项之间滑动
- 避免 `layoutId` 动画元素在切换过程中遮挡其他导航项
- 让内容切换有方向感知的过渡动画
- 稳定产出可维护的 Motion 动效代码

---

## 适用场景

典型需求表述：

- 「给设置页 nav 切换加 Motion 动效」
- 「用 layoutId 做 tabs / nav / segmented control 的活跃态动画」
- 「切换左侧菜单时，右侧内容也要有过渡效果」
- 「实现活跃背景在多个按钮之间滑动」
- 「修复 layoutId 动画遮挡其他选项的问题」

典型 UI：设置页侧边栏、Tabs、Segmented Control、Filter Pills、Dashboard 二级导航、Account / Preference 页面分区切换。

---

## 核心设计原则

### 1. 活跃态不要直接写在按钮本体上

不要只通过 `className` 给 active 按钮切换背景色/边框/阴影。

推荐做法：在 active 项内部渲染一个独立的 `motion.div` 作为活跃指示器，设置相同的 `layoutId`，让 Motion 负责位置过渡。

```tsx
{active && (
  <motion.div
    layoutId="setting-nav-indicator"
    className="absolute inset-0 rounded-lg bg-accent border border-foreground/15"
    transition={{ type: "spring", duration: 0.35, bounce: 0.15 }}
  />
)}
```

### 2. 按钮内容必须浮在 indicator 之上

活跃指示器是 `absolute inset-0`，按钮里的文字、图标需要放在它上方：

```tsx
<button className="relative">
  {active && <motion.div className="absolute inset-0" layoutId="..." />}
  <span className="relative z-10 flex items-center gap-2">
    <Icon />
    <span>General</span>
  </span>
</button>
```

### 3. Nav 容器要创建隔离的层叠上下文

在使用 `layoutId` 的 nav / tabs 容器上加 `isolate`：

```tsx
<nav className="relative isolate flex flex-col gap-1">
  {/* nav items */}
</nav>
```

### 4. 修复 layoutId 切换时遮挡中间选项

**这是最常见的坑。**

当从上方选项切到下方选项时，`layoutId` 元素渲染在新的 active 项内部，如果该项 DOM 顺序更靠后，过渡过程中会绘制在中间选项之上，遮挡中间按钮的文字/图标。

修复策略 — 让 indicator 从其他选项「背后」滑过：

- active 项：`z-0`
- inactive 项：`z-[1]`
- nav 容器：`isolate`
- 按钮内容：`relative z-10`

```tsx
<nav className="relative isolate flex flex-col gap-1">
  {items.map((item) => {
    const active = item.key === activeKey;
    return (
      <button
        key={item.key}
        type="button"
        onClick={() => setActiveKey(item.key)}
        className={cn(
          "relative rounded-lg px-3 py-2 text-sm transition-colors",
          active ? "z-0 text-foreground" : "z-[1] text-muted-foreground hover:text-foreground"
        )}
      >
        {active && (
          <motion.div
            layoutId="setting-nav-indicator"
            className="absolute inset-0 rounded-lg bg-accent border border-foreground/15"
            transition={{ type: "spring", duration: 0.35, bounce: 0.15 }}
          />
        )}
        <span className="relative z-10 flex items-center gap-2">
          <item.icon className="size-4" />
          <span>{item.label}</span>
        </span>
      </button>
    );
  })}
</nav>
```

---

## 推荐实现模板

### 1. 定义导航项

```tsx
const settingNavItems = [
  { key: "general", label: "General", icon: SettingsIcon },
  { key: "account", label: "Account", icon: UserIcon },
  { key: "billing", label: "Billing", icon: CreditCardIcon },
] as const;

type SettingNavKey = (typeof settingNavItems)[number]["key"];
```

### 2. 定义内容过渡曲线

```tsx
const EASE_OUT_QUAD = [0.25, 0.46, 0.45, 0.94] as const;
```

### 3. 定义方向感知的内容 variants

```tsx
const contentVariants = {
  initial: (dir: number) => ({
    opacity: 0,
    y: dir * 8,
  }),
  animate: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.15,
      ease: EASE_OUT_QUAD,
    },
  },
  exit: (dir: number) => ({
    opacity: 0,
    y: dir * -4,
    transition: {
      duration: 0.1,
      ease: EASE_OUT_QUAD,
    },
  }),
};
```

设计解释：

- 从上往下切换：内容从下方轻微滑入（`dir = 1`，`y: 8`）
- 从下往上切换：内容从上方轻微滑入（`dir = -1`，`y: -8`）
- 进入位移较大：`8px`；退出位移较小：`4px`
- 退出更快 `0.1s`，进入稍慢 `0.15s` — 适合设置页，不会过于花哨

### 4. 计算切换方向

```tsx
const [activeKey, setActiveKey] = useState<SettingNavKey>("general");
const [direction, setDirection] = useState(1);

const handleNavChange = (nextKey: SettingNavKey) => {
  if (nextKey === activeKey) return;
  const currentIndex = settingNavItems.findIndex((item) => item.key === activeKey);
  const nextIndex = settingNavItems.findIndex((item) => item.key === nextKey);
  setDirection(nextIndex > currentIndex ? 1 : -1);
  setActiveKey(nextKey);
};
```

### 5. Nav layoutId 动效

```tsx
<nav className="relative isolate flex flex-col gap-1">
  {settingNavItems.map((item) => {
    const active = item.key === activeKey;
    return (
      <button
        key={item.key}
        type="button"
        onClick={() => handleNavChange(item.key)}
        className={cn(
          "relative rounded-lg px-3 py-2 text-left text-sm transition-colors",
          active
            ? "z-0 text-foreground"
            : "z-[1] text-muted-foreground hover:text-foreground"
        )}
      >
        {active && (
          <motion.div
            layoutId="setting-nav-indicator"
            className="absolute inset-0 rounded-lg bg-accent border border-foreground/15"
            transition={{ type: "spring", duration: 0.35, bounce: 0.15 }}
          />
        )}
        <span className="relative z-10 flex items-center gap-2">
          <item.icon className="size-4" />
          <span>{item.label}</span>
        </span>
      </button>
    );
  })}
</nav>
```

### 6. 内容面板过渡

```tsx
<AnimatePresence mode="wait" custom={direction}>
  <motion.div
    key={activeKey}
    custom={direction}
    variants={contentVariants}
    initial="initial"
    animate="animate"
    exit="exit"
  >
    {renderSettingContent(activeKey)}
  </motion.div>
</AnimatePresence>
```

要点：

- `key={activeKey}` 是必须的，否则不会触发退出/进入动画
- `mode="wait"` 避免新旧内容同时出现
- `custom={direction}` 需要同时传给 `AnimatePresence` 和 `motion.div`，让 exit 动画也能拿到方向

---

## AI Agent 执行步骤

### Step 1: 检查依赖和已有导入

确认项目是否已安装 Motion。常见导入：

```tsx
import { AnimatePresence, motion } from "motion/react";
```

如果项目使用旧版 framer-motion：

```tsx
import { AnimatePresence, motion } from "framer-motion";
```

不要混用两个包。

### Step 2: 找到 active 状态和 nav 渲染区域

确认：

- 当前 active key / active tab 是什么状态控制的
- nav items 是否有稳定 key
- 内容区域是否根据 active key 条件渲染

### Step 3: 改造 active 样式

把 active 按钮本体上的背景/边框样式迁移到 `motion.div layoutId` 上。

避免：

```tsx
className={active ? "bg-accent border" : ""}
```

推荐：

```tsx
{active && <motion.div layoutId="xxx" className="absolute inset-0 bg-accent border" />}
```

### Step 4: 处理层级

必须检查并处理层级问题，推荐默认结构：

```tsx
<nav className="relative isolate ...">
  <button className={active ? "relative z-0" : "relative z-[1]"}>
    {active && <motion.div className="absolute inset-0" layoutId="..." />}
    <span className="relative z-10">...</span>
  </button>
</nav>
```

**这是本 case 的关键坑位。**

### Step 5: 给内容区加 AnimatePresence

```tsx
<AnimatePresence mode="wait" custom={direction}>
  <motion.div key={activeKey} custom={direction} variants={contentVariants} />
</AnimatePresence>
```

### Step 6: 运行类型检查 / lint

重点检查：

- `ease` 是否被 TypeScript 推断成不兼容的 `number[]`
- `layoutId` 是否唯一
- `key` 是否稳定
- 是否仍残留 active 背景样式导致双重背景
- 是否出现内容切换闪烁或重叠

---

## 常见坑与修复

### 坑 1: indicator 遮挡中间选项

**现象**：从上方 nav 切换到下方 nav 时，活跃背景滑动过程中盖住中间选项的文字/图标。

**原因**：`layoutId` 元素渲染在新的 active 项内部；新的 active 项 DOM 顺序更靠后，默认绘制层级更高。

**修复**：

```tsx
<nav className="relative isolate ...">
```

```tsx
active ? "z-0" : "z-[1]"
```

```tsx
<span className="relative z-10">...</span>
```

### 坑 2: 按钮文字被 active 背景盖住

**原因**：indicator 是 absolute 元素，文字没有设置相对层级。

**修复**：

```tsx
<span className="relative z-10">按钮内容</span>
```

### 坑 3: active 背景跳变，没有 layout 动画

**可能原因**：

- `layoutId` 字符串不一致
- active indicator 不在同一个 React tree / Motion layout 上下文中
- 条件渲染结构变化过大
- nav item 的 `key` 不稳定

**修复**：

- 确保所有 active indicator 使用完全相同的 `layoutId`
- 必要时用 `LayoutGroup` 包裹相关 nav 区域
- item key 使用业务 key，不要使用数组 index

```tsx
import { LayoutGroup } from "motion/react";

<LayoutGroup id="settings-nav">
  <nav>...</nav>
</LayoutGroup>
```

### 坑 4: 内容切换时新旧内容重叠

**修复**：

```tsx
<AnimatePresence mode="wait">
```

并确保内容容器有 `key={activeKey}`。

### 坑 5: TypeScript 报 ease 类型错误

**现象**：`ease: [0.25, 0.46, 0.45, 0.94]` 类型不兼容。

**修复**：

```tsx
const EASE_OUT_QUAD = [0.25, 0.46, 0.45, 0.94] as const;
```

### 坑 6: CSS transition 与 Motion 动画打架

不要让同一个视觉属性同时由 CSS transition 和 Motion 控制。

active 背景已交给 `motion.div layoutId` 后，按钮本身不要继续切换 `bg-* border-* shadow-*`。按钮本体可保留文本颜色 transition、hover 文本颜色、focus ring。

---

## 动效参数建议

### Nav indicator

| 风格 | transition |
|---|---|
| 设置页/后台（推荐） | `{ type: "spring", duration: 0.35, bounce: 0.15 }` |
| 更稳重 | `{ type: "spring", duration: 0.28, bounce: 0.08 }` |
| 更活泼 | `{ type: "spring", duration: 0.42, bounce: 0.22 }` |

### 内容面板

设置页推荐：

```tsx
initial: { opacity: 0, y: 8 }
animate: { opacity: 1, y: 0, duration: 0.15 }
exit: { opacity: 0, y: -4, duration: 0.1 }
```

位移范围通常 `4px ~ 12px` 就足够，不要让设置页内容大幅位移。

---

## 变体模式

### 横向 Tabs

把内容位移从 `y` 改成 `x`：

```tsx
const tabContentVariants = {
  initial: (dir: number) => ({ opacity: 0, x: dir * 12 }),
  animate: { opacity: 1, x: 0, transition: { duration: 0.16, ease: EASE_OUT_QUAD } },
  exit: (dir: number) => ({ opacity: 0, x: dir * -8, transition: { duration: 0.1, ease: EASE_OUT_QUAD } }),
};
```

### 只有淡入淡出

如果页面内容高度差较大，位移动画可能产生跳动，可以只使用 opacity：

```tsx
const fadeVariants = {
  initial: { opacity: 0 },
  animate: { opacity: 1, transition: { duration: 0.15 } },
  exit: { opacity: 0, transition: { duration: 0.1 } },
};
```

### Indicator 带阴影

如果活跃态需要更强识别：

```tsx
<motion.div
  layoutId="nav-indicator"
  className="absolute inset-0 rounded-lg bg-background border shadow-sm"
/>
```

阴影更容易暴露层级问题，更要使用 `isolate` 和 z-index 策略。

---

## 验收清单

完成实现后，必须逐项检查：

- [ ] 点击不同 nav 项时，活跃背景/边框平滑移动
- [ ] 从上往下切换时，indicator 没有遮挡中间选项
- [ ] 从下往上切换时，indicator 没有遮挡中间选项
- [ ] active 项文字/icon 始终在背景之上
- [ ] 非 active 项 hover 仍正常
- [ ] 内容区有进入和退出动画
- [ ] 内容切换时没有重叠、闪烁、错位
- [ ] TypeScript 无 Motion 类型错误
- [ ] active 背景样式只由 indicator 控制，没有重复样式
- [ ] layoutId 具有足够唯一性，不会与页面其他 layoutId 冲突

---

## 推荐回答格式

Agent 完成实现后，简要说明：

1. Nav 使用了 `motion.div + layoutId` 实现活跃指示器滑动
2. 内容区使用 `AnimatePresence mode="wait"` 和方向感知 variants
3. 已处理 layoutId 层级问题：`nav isolate`、active `z-0`、inactive `z-[1]`、内容 `z-10`
4. 如有未解决的 lint warning，要明确说明是否为原有问题、是否影响功能

示例：

```
已完成。核心改动：

- Nav active 背景改为 `motion.div layoutId="setting-nav-indicator"`，切换时使用 spring 动画平滑移动。
- 右侧内容区增加 `AnimatePresence mode="wait"`，根据 nav 索引变化做方向感知淡入/轻微位移。
- 修复了 layoutId 过渡时遮挡中间选项的问题：`nav` 使用 `isolate`，active 项为 `z-0`，inactive 项为 `z-[1]`，按钮内容为 `relative z-10`。
- TypeScript ease 类型通过 `as const` 处理。
```

---

## 最小代码骨架

```tsx
import { AnimatePresence, motion } from "motion/react";
import { useState } from "react";

const EASE_OUT_QUAD = [0.25, 0.46, 0.45, 0.94] as const;

const contentVariants = {
  initial: (dir: number) => ({ opacity: 0, y: dir * 8 }),
  animate: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.15, ease: EASE_OUT_QUAD },
  },
  exit: (dir: number) => ({
    opacity: 0,
    y: dir * -4,
    transition: { duration: 0.1, ease: EASE_OUT_QUAD },
  }),
};

export function SettingsPage() {
  const [activeKey, setActiveKey] = useState("general");
  const [direction, setDirection] = useState(1);

  const handleChange = (nextKey: string) => {
    if (nextKey === activeKey) return;
    const currentIndex = items.findIndex((item) => item.key === activeKey);
    const nextIndex = items.findIndex((item) => item.key === nextKey);
    setDirection(nextIndex > currentIndex ? 1 : -1);
    setActiveKey(nextKey);
  };

  return (
    <div className="grid grid-cols-[220px_1fr] gap-6">
      <nav className="relative isolate flex flex-col gap-1">
        {items.map((item) => {
          const active = item.key === activeKey;
          return (
            <button
              key={item.key}
              type="button"
              onClick={() => handleChange(item.key)}
              className={cn(
                "relative rounded-lg px-3 py-2 text-left text-sm transition-colors",
                active ? "z-0 text-foreground" : "z-[1] text-muted-foreground hover:text-foreground"
              )}
            >
              {active && (
                <motion.div
                  layoutId="settings-nav-indicator"
                  className="absolute inset-0 rounded-lg bg-accent border border-foreground/15"
                  transition={{ type: "spring", duration: 0.35, bounce: 0.15 }}
                />
              )}
              <span className="relative z-10 flex items-center gap-2">
                <item.icon className="size-4" />
                <span>{item.label}</span>
              </span>
            </button>
          );
        })}
      </nav>

      <AnimatePresence mode="wait" custom={direction}>
        <motion.div
          key={activeKey}
          custom={direction}
          variants={contentVariants}
          initial="initial"
          animate="animate"
          exit="exit"
        >
          {renderContent(activeKey)}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
```
