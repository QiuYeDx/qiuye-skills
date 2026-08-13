# Case 4: 用 `layoutDependency` 隔离无关布局变化

## 目标

让 Segmented Control、Tabs、Filter Pills 等控件的共享选中指示器只在选中值变化时执行布局动画，避免祖先内容增减或页面重排时，未交互控件的胶囊背景出现上下漂移。

保留正常选项切换时的横向 spring 动画，不使用固定高度占位或关闭全部 layout 动画。

---

## 适用场景

典型现象：

- 切换上方配置后，某行条件输入框立即消失，下面的内容整体上移。
- 下方 Segmented Control 本体和文字随文档流立即上移，但其白色高亮胶囊仍从旧位置缓动到新位置。
- 该 Segmented Control 的选中值没有变化，用户也没有操作它。
- 正常切换该控件的选项时，仍需要保留高亮胶囊的滑动效果。

典型 UI：动态设置面板、条件表单、折叠面板、侧栏配置、Tabs、Segmented Control、Filter Pills。

---

## 先判断是哪一类问题

### A. 无关重排误触发布局动画

同时满足以下条件时，优先使用本 case：

1. indicator 使用 `layout` 或 `layoutId`。
2. indicator 的业务状态未变。
3. 祖先或兄弟内容变化让控件在页面中的坐标改变。
4. 只有 indicator 在追赶新位置，控件其余内容已到达新位置。

根因不是上层内容缺少高度动画，而是 Motion 在 React 更新后重新测量了 layout 元素，并把外部重排产生的坐标差也当成该元素需要投影的动画。

### B. 整个内容区本来就应该平滑改变高度

如果需求是让 Popover、Card 或设置区域的外框和全部内容共同平滑伸缩，读取 Case 2，给真正负责高度的容器设计 auto-height 过渡。不要用 `layoutDependency` 掩盖应该存在的容器动画。

### C. indicator 的几何位置确实受多个状态控制

如果方向、尺寸、密度、字体加载、选项列表或容器宽度变化后，indicator 也必须补间到新几何位置，不要只依赖选中值。将所有决定动画目标的离散状态组合为 dependency，或保留默认 layout 测量行为。

---

## 核心设计原则

### 1. dependency 表达“何时允许重新做 layout 动画”

当选中胶囊的预期动画目标只由当前值决定时，把解析后的选中值传给 `layoutDependency`：

```tsx
<motion.span
  layoutId={`${instanceId}-segmented-control-indicator`}
  layoutDependency={resolvedValue}
  initial={false}
  transition={transition}
  className="pointer-events-none absolute inset-0 rounded-full"
/>
```

效果：

- `resolvedValue` 变化：Motion 测量新旧选项，执行正常的 indicator 滑动。
- 仅祖先内容高度变化：dependency 不变，不为该 indicator 创建无关的 layout 投影动画。

### 2. 使用解析后的真实状态

受控与非受控组件通常会合并出一个实际选中值。dependency 应绑定这个最终值，而不是只绑定 `value` prop：

```tsx
const resolvedValue = valueProp ?? internalValue;
```

```tsx
layoutDependency={resolvedValue}
```

否则非受控模式下 `valueProp` 一直是 `undefined`，正常选项切换也可能无法触发预期测量。

### 3. 修复放在拥有动画语义的层级

如果共享组件定义了 indicator 和它的 `layoutId`，并且“只在选中值变化时滑动”是组件的稳定语义，应在共享组件内部修复。这样所有动态表单、折叠面板和设置页都会获得一致行为。

只有当某个使用方主动编排整个区域的 layout 动画，或它传入的额外属性改变 indicator 的真实目标几何时，才在使用层组合 dependency 或调整外层动画。

### 4. 不要用视觉占位绕过测量问题

以下做法会改变页面语义或牺牲正常动画，不作为默认修复：

- 为条件内容保留固定高度或隐藏占位。
- 给每个动态表单区硬编码 `min-height`。
- 移除 `layoutId`，让 indicator 瞬移。
- 把整个设置面板都改成缓慢的高度动画，只为遮盖胶囊漂移。
- 用 CSS `transition: all` 同时过渡控件本体。

---

## 推荐实现模板

```tsx
import * as React from "react";
import { motion } from "motion/react";

type Item = {
  label: string;
  value: string;
};

type SegmentedControlProps = {
  items: Item[];
  value?: string;
  defaultValue?: string;
  onValueChange?: (value: string) => void;
};

export function SegmentedControl({
  items,
  value: valueProp,
  defaultValue,
  onValueChange,
}: SegmentedControlProps) {
  const instanceId = React.useId();
  const [internalValue, setInternalValue] = React.useState(
    defaultValue ?? items[0]?.value ?? "",
  );
  const resolvedValue = valueProp ?? internalValue;

  const selectValue = (nextValue: string) => {
    if (valueProp === undefined) setInternalValue(nextValue);
    onValueChange?.(nextValue);
  };

  return (
    <div role="radiogroup" className="relative isolate flex rounded-full bg-muted p-1">
      {items.map((item) => {
        const active = item.value === resolvedValue;

        return (
          <button
            key={item.value}
            type="button"
            role="radio"
            aria-checked={active}
            onClick={() => selectValue(item.value)}
            className="relative min-w-0 flex-1 px-3 py-1.5 text-sm"
          >
            {active && (
              <motion.span
                layoutId={`${instanceId}-indicator`}
                layoutDependency={resolvedValue}
                initial={false}
                transition={{ type: "spring", duration: 0.28, bounce: 0.08 }}
                className="pointer-events-none absolute inset-0 rounded-full bg-background shadow-sm"
              />
            )}
            <span className="relative z-10">{item.label}</span>
          </button>
        );
      })}
    </div>
  );
}
```

如果 indicator 的目标还受方向或尺寸控制，组合依赖：

```tsx
const indicatorLayoutDependency = `${resolvedValue}:${orientation}:${size}`;

<motion.span
  layoutId={`${instanceId}-indicator`}
  layoutDependency={indicatorLayoutDependency}
/>
```

只加入真正改变 indicator 目标几何或必须触发布局补间的状态。不要把整个 props 对象或每次 render 都新建的对象传进去，否则会失去隔离效果。

---

## AI Agent 执行步骤

### Step 1: 做最小复现

保持目标 Segmented Control 的选中值不变，只切换它上方的条件内容、折叠区或动态输入行。确认是 indicator 单独上下追赶，而不是整个控件一起动画。

### Step 2: 定位 layout 元素与状态源

搜索 `layout`、`layoutId`、`LayoutGroup`，找到 indicator。继续确认受控值、非受控值和最终 `resolvedValue` 的计算方式。

### Step 3: 判断修复归属

- 多个页面都会遇到，且 indicator 的动画语义由共享组件定义：修共享组件。
- 只有某个页面故意改变 indicator 的几何规则：在使用层补齐 dependency 或调整该页面的 layout 编排。
- 整个动态区域都应平滑伸缩：转用 Case 2 的容器高度方案。

### Step 4: 添加最小 dependency

优先使用稳定的字符串、数字或布尔值：

```tsx
layoutDependency={resolvedValue}
```

如果多项状态共同决定目标，构造稳定的原始值。不要传不稳定对象。

### Step 5: 验证两条路径

1. 不改变目标控件值，只改变祖先高度：indicator 不应单独漂移。
2. 改变目标控件值：indicator 仍应在选项之间平滑移动。

使用慢速录屏或逐帧截图检查中间帧；仅看动画结束后的静态截图无法发现该问题。

---

## 常见坑与修复

### 坑 1: 把 `layoutDependency` 绑到上层表单状态

**现象**：切换任意配置仍会触发 indicator 的 layout 动画。

**原因**：dependency 与无关重排同步变化，等于重新允许了这次测量。

**修复**：绑定 indicator 自己的选中值，或绑定真正决定其目标几何的最小状态集合。

### 坑 2: 传入每次 render 都变化的对象

```tsx
layoutDependency={{ value: resolvedValue }}
```

对象引用每次 render 都变，无法稳定隔离无关更新。改用原始值或稳定序列化键：

```tsx
layoutDependency={resolvedValue}
```

### 坑 3: 只修某一个动态表单页面

如果同一个共享 Segmented Control 在任意祖先重排时都可能漂移，页面级占位只能修一个触发点。应在组件层表达其动画依赖。

### 坑 4: dependency 过窄

如果 `orientation` 从水平变垂直、`size` 改变或选项集合重排时也需要 indicator 动画，只绑定 `resolvedValue` 会跳过这些布局变化。把确实需要动画的离散状态加入稳定组合键，或保留默认行为。

### 坑 5: 用 `layout="position"` 代替 dependency

`layout="position"` 控制布局动画处理位置还是尺寸，但祖先重排仍然改变位置，不能表达“这次更新不应触发布局动画”。本问题需要限制触发条件，而不是只限制动画属性类别。

---

## 验收清单

- [ ] 目标控件值不变时，切换上方条件内容不会让 indicator 单独上下漂移
- [ ] 折叠/展开祖先区域时，indicator 与文字、外框保持同步
- [ ] 正常切换选项时，indicator 的横向或纵向滑动仍存在
- [ ] 受控模式和非受控模式都绑定最终 `resolvedValue`
- [ ] 多个组件实例的 `layoutId` 保持唯一
- [ ] dependency 没有使用每次 render 新建的对象
- [ ] 方向、尺寸、选项集合等真实几何依赖没有被遗漏
- [ ] 已用逐帧录屏、截图或像素位置检查验证动画中间帧
- [ ] TypeScript 和相关组件测试通过
- [ ] 未引入固定高度占位、`transition: all` 或页面级补偿动画

---

## 推荐回答格式

说明这是共享 layout indicator 对无关祖先重排做了投影动画，并交代修复边界：

```text
问题属于共享组件的动画依赖缺失。indicator 只应在选中值变化时滑动，因此为它添加了 layoutDependency={resolvedValue}。现在祖先内容高度变化不会触发胶囊的无关纵向补间，正常选项切换的滑动仍保留。已同时验证静态重排和真实选项切换两条路径。
```
