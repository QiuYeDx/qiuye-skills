# Case 2: Radix / shadcn ScrollArea 的定位、尺寸与内容宽度

## 目标

用 Radix `ScrollArea`（含 shadcn/ui 的 `ScrollArea` 封装）实现浮层、弹窗、侧栏、详情面板里的内部滚动，并避免它自带的三类坑：

- 定位 class 写了但不生效，根节点被内容撑高，视口根本无法滚动。
- 横向滚动的子元素（截图条、标签行、代码块）把整个滚动区撑宽，而不是在自身内部滚动。
- 视口 `overflow` 由内联样式控制，按状态切换「可滚动 / 禁止滚动」时 class 不生效。

同时说明何时应该用它替代原生滚动条：滚动区在动画结束后才开启滚动，原生滚动条出现时占用布局宽度，内容瞬间重排。

## 适用场景

- 弹窗、Sheet、卡片展开浮层、Header 下拉目录等需要内部滚动的容器。
- 用户反馈「展开后右侧突然冒出滚动条，内容跳了一下」「Windows 上滚动条挤占宽度」。
- 用了 `ScrollArea` 后「滚不动」「内容被裁掉一截」「整个面板被横向撑宽」。
- 需要在动画期间禁止滚动、动画结束后再允许滚动。

## 核心判断

Radix `ScrollArea` 不是「带样式的 `overflow: auto`」。它渲染三层结构，并且关键样式都写在**内联 style** 上（以 `@radix-ui/react-scroll-area@1.2.10` 源码为准）：

| 节点 | 内联样式 | 后果 |
| --- | --- | --- |
| Root | `position: relative`（`...props.style` 合并在其后） | `absolute` / `fixed` 等定位 class 会被覆盖 |
| Viewport | `overflowX` / `overflowY`: `scroll` 或 `hidden` | 想用 class 切换 overflow，必须 `!important` |
| Viewport 内的内容包裹 div | `display: table; min-width: 100%` | 宽度按内容最大宽度计算，横向滚动子元素会撑宽整个区域 |

另外，它注入全局规则 `[data-radix-scroll-area-viewport]{scrollbar-width:none}` 隐藏原生滚动条，再叠加自己绘制的滚动条。所以**原生滚动条宽度恒为 0**，开关滚动不会改变内容宽度。这正是它能解决「滚动条出现导致重排」的原因。

## 排查顺序

1. 在 DevTools 查看 Root 的 computed `position`：期望 `absolute` 却是 `relative`，就是内联样式覆盖了 class（坑 1）。
2. 比较视口的 `clientHeight` 与 `scrollHeight`：两者相等且内容明显超出容器，说明 Root 没有被约束高度，被内容撑高了（坑 1）。
3. 检查视口下第一层 div 的 computed `display`：`table` 时，横向 `overflow-x: auto` 的子元素会把整体撑宽（坑 2）。
4. 比较横向子元素的 `clientWidth` 与 `scrollWidth`：子元素自身不滚动、外层却变宽，说明 `display: table` 生效了（坑 2）。
5. 想按状态禁止滚动时，检查视口 computed `overflow` 是否仍是 `scroll`：class 没有压过内联样式（坑 3）。
6. 原生滚动容器出现重排时，比较 `offsetWidth - clientWidth`：大于 0 即原生滚动条占用了宽度（坑 4）。

## 推荐结构

```text
定位容器（fixed / 动画几何，overflow: hidden，负责圆角裁切）
└── ScrollArea Root      ← 通过 style 设置 absolute + inset: 0（不要靠 class）
    └── Viewport         ← size-full；需要时用 !important 覆盖 overflow
        └── 内容包裹 div  ← 覆盖为 display: block
            └── 真实内容（可含横向滚动子元素）
```

- 定位 / 尺寸约束交给 Root 的 `style`，Viewport 用 `size-full` 跟随 Root。
- 「动画期间禁止滚动」用状态选择器 + `!important` 覆盖 Viewport 的内联 overflow。
- 页面接入了 Lenis 等全局平滑滚动时，在 Root 上加 `data-lenis-prevent`（或项目约定的豁免属性）。

## 推荐实现模板

shadcn 默认的 `ScrollArea` 不暴露 Viewport 的 ref 与 className。需要程序化滚动（如关闭时滚回顶部）或给 Viewport 加样式时，先在项目的 `components/ui/scroll-area.tsx` 增加 `viewportRef` / `viewportClassName` 透传，再使用：

```tsx title="DetailSheet.tsx"
import { ScrollArea } from "@/components/ui/scroll-area";

<motion.div className="detail-sheet" data-phase={phase} /* 定位与几何动画 */>
  <ScrollArea
    className="detail-sheet-scroll"
    // Radix 给 Root 写了内联 position: relative；props.style 合并在后，能覆盖它。
    style={{ position: "absolute", inset: 0 }}
    viewportRef={scrollRef}
    viewportClassName="detail-sheet-viewport"
    type="scroll" // 只在滚动时显示叠加滚动条，接近 macOS 覆盖式滚动条
    data-lenis-prevent
  >
    {children}
  </ScrollArea>
</motion.div>
```

```css title="detail-sheet.css"
/* Radix 用 display: table 包裹内容，横向滚动的子元素会撑宽整个区域。 */
.detail-sheet-viewport > div {
  display: block !important;
}

/* 动画期间禁止滚动；必须 !important 才能压过 Viewport 的内联 overflow。 */
.detail-sheet:not([data-phase="open"]) .detail-sheet-viewport {
  overflow: hidden !important;
}

/* 叠加滚动条：避开大圆角，并保证在深色插画和浅色正文上都可见。 */
.detail-sheet-scroll [data-slot="scroll-area-scrollbar"] {
  padding-block: 18px;
}
.detail-sheet-scroll [data-slot="scroll-area-thumb"] {
  background: color-mix(in oklab, var(--foreground) 38%, transparent);
  box-shadow: 0 0 0 1px color-mix(in oklab, var(--background) 45%, transparent);
}
```

## 常见坑与修复

### 坑 1: 用 class 给 Root 定位，结果被内容撑高、无法滚动

错误模式：

```tsx
<ScrollArea className="absolute inset-0">{longContent}</ScrollArea>
```

原因：

- Radix 在 Root 上写了内联 `position: relative`，优先级高于 `.absolute` 等 class。
- Root 变回普通文档流，高度由内容决定；Viewport 的 `size-full` 跟着变高，`clientHeight === scrollHeight`，没有可滚动的距离。
- 外层容器若有 `overflow: hidden`，超出部分被直接裁掉，表现为「内容少了一截且滚不动」。

修复：

- 通过 `style={{ position: "absolute", inset: 0 }}` 设置（Radix 把 `props.style` 合并在内联默认值之后）。
- 或者外包一个负责定位的普通 div，让 Root 以 `h-full w-full` 填满它。
- 验收时确认 Root computed `position` 正确，且 Viewport `clientHeight < scrollHeight`。

### 坑 2: 横向滚动子元素把整个滚动区撑宽

错误模式：

```tsx
<ScrollArea>
  <div className="flex overflow-x-auto">{/* 一排截图 */}</div>
</ScrollArea>
```

原因：

- Viewport 内的包裹 div 是内联 `display: table; min-width: 100%`。
- table 布局按内容的最大宽度计算，带 `overflow-x: auto` 的子元素无法被压到容器宽度，于是整行内容撑开了包裹层。
- 现象是子元素自身 `clientWidth === scrollWidth`，外层却比容器宽，甚至出现横向滚动或内容被裁切。

修复：

```css
[data-radix-scroll-area-viewport] > div {
  display: block !important;
}
```

- 建议限定在具体组件的 Viewport class 下，不全局覆盖，以免影响依赖 table 宽度行为的其它用法（例如需要横向滚动整块宽内容的表格）。

### 坑 3: 用 class 切换 Viewport 的 overflow 不生效

错误模式：

```css
.sheet:not(.is-open) [data-slot="scroll-area-viewport"] {
  overflow: hidden;
}
```

原因：

- Viewport 的 `overflowX` / `overflowY` 是内联样式（启用对应方向滚动条时为 `scroll`）。

修复：

- 覆盖时加 `!important`，并用明确的状态选择器限定范围。
- 原生滚动条已被 Radix 隐藏，`hidden` 与 `scroll` 之间切换不会改变布局宽度。

### 坑 4: 原生滚动条在过渡结束后出现，挤占宽度导致内容重排

错误模式：

```css
.sheet-scroll { overflow: hidden; }
.sheet[data-phase="open"] .sheet-scroll { overflow-y: auto; }
```

原因：

- Windows / Linux 的传统滚动条占用布局宽度（常见约 15px，`scrollbar-width: thin` 约 8–11px）。
- 动画期间禁止滚动、结束后才开启，滚动条在最后一刻出现，内容区突然变窄并重新换行，看起来像闪烁。macOS 默认的覆盖式滚动条不占宽度，所以在 Mac 上容易漏测。

修复（按场景选择）：

- **首选**：改用 `ScrollArea` 的叠加滚动条，原生滚动条宽度恒为 0（注意处理坑 1–3）。
- `scrollbar-gutter: stable`：始终预留滚动条槽位，不再重排。但内容区会比外框窄一条，**不适合**需要与触发元素像素对齐的容器变形 / 共享元素过渡，第一帧和最后一帧会出现一条空白。
- 隐藏原生滚动条：不重排，但失去滚动位置提示，只适合内容很短或有其它提示的场景。

## AI Agent 执行步骤

1. 确认问题属于哪一类：滚不动 / 被撑高（坑 1）、被横向撑宽（坑 2）、状态切换无效（坑 3）、滚动条出现导致重排（坑 4）。
2. 打开项目的 `components/ui/scroll-area.tsx`，确认是否透传了 `viewportRef` / `viewportClassName`；需要时最小化补充，不改动 Radix 默认行为。
3. Root 的定位与 inset 写进 `style`，不要只写 class；Viewport 使用 `size-full`。
4. 视口内含横向滚动内容时，为该组件的 Viewport 包裹层覆盖 `display: block !important`。
5. 需要按状态禁止滚动时，用状态选择器 + `!important` 覆盖 Viewport overflow。
6. 页面有全局平滑滚动库时，为 Root 添加豁免属性（如 `data-lenis-prevent`）。
7. 调整叠加滚动条的内边距与颜色，避开圆角，在深浅背景上都可见。
8. 在真实浏览器中按验收清单测量；至少检查一个会显示传统滚动条的环境（Windows Chrome/Edge，或开启「始终显示滚动条」的 macOS）。

## 验收清单

- Root computed `position` 与预期一致（如 `absolute`），Root 高度等于容器高度，而不是内容高度。
- Viewport `clientHeight < scrollHeight`，滚轮与触摸能滚动，且不带动背后页面。
- Viewport `offsetWidth === clientWidth`：原生滚动条不占宽度；可滚动与禁止滚动两种状态下内容宽度一致。
- 横向滚动子元素在自身内部滚动（`clientWidth < scrollWidth`），外层宽度不变，页面无横向溢出。
- 动画 / 禁止滚动期间无法滚动，进入可滚动状态时没有任何重排。
- 叠加滚动条在滚动时出现，不压住关闭按钮、圆角或关键内容。
- 程序化滚动（如关闭前滚回顶部）作用在 Viewport 上且生效。
- 至少在一个显示传统滚动条的环境中复验。

## 推荐回答格式

完成修复后向用户说明：

- 问题属于哪一类，以及对应的 Radix 内联样式根因。
- 用了哪些覆盖（`style` 定位、`display: block`、`overflow !important`），作用范围限定在哪里。
- 测量了哪些指标（`position`、`clientHeight/scrollHeight`、`offsetWidth/clientWidth`），在哪些浏览器 / 视口验证。
