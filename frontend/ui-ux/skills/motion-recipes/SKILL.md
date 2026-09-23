---
name: motion-recipes
description: >-
  Motion (framer-motion) 动效案例集。用于实现或修复 layoutId 导航、AnimatePresence
  内容切换、测量式 auto-height、列表增删重排、容器变形、鼠标分层视差，以及连续布局过渡。
  用户描述“折叠内容淡入淡出并撑开空间”“下面元素不要瞬移”“外框平滑但里面还闪”
  “有始有终地移动”时优先读 Case 9；涵盖退出保留、间距、草稿、嵌套与 reduced motion。
  也匹配 Motion recipes、layout animation、dynamic height、auto to auto、ResizeObserver、
  popLayout、layoutDependency、shared element、container transform、pointer parallax。
  用于具体动效实现与排障；仅询问效果名称或全站动效审计时使用对应命名或评审 Skill。
---

# Motion Recipes — 动效案例集

经过实战验证的 Motion 动效实现方案集合。每个 case 提供完整的模板代码、设计原则、常见坑位与修复策略，让 AI Agent 在类似场景下能快速、稳定地产出可维护的动效代码。

## 使用方式

本 Skill 是索引型文档，具体实现细节在 `cases/` 子目录中。

**Agent 执行流程：**

1. 根据用户需求，在下方「案例索引」中匹配最相关的 case。若同时要求内容显隐、空间伸缩与周围元素连续移动，先读 Case 9；无需逐篇拼读全部案例。
2. 使用 Read 工具阅读对应 case 文件的完整内容。
3. 按 case 中的「AI Agent 执行步骤」逐步实施。
4. 完成后按 case 中的「验收清单」逐项检查。

如果没有完全匹配的 case，选择最接近的 case 作为基础，结合通用原则进行调整。

---

## 通用原则

以下原则适用于所有 Motion 动效场景，各 case 不再重复说明：

### 依赖与导入

```tsx
// Motion v11+ (推荐)
import { motion, AnimatePresence } from "motion/react";

// 旧版 framer-motion（仅在项目已使用时保持一致）
import { motion, AnimatePresence } from "framer-motion";
```

不要混用两个包。优先检查项目现有导入路径。

### Spring 参数速查

| 风格 | 参数 | 适用场景 |
|---|---|---|
| 克制 | `{ type: "spring", duration: 0.28, bounce: 0.08 }` | 管理后台、设置页 |
| 标准 | `{ type: "spring", duration: 0.35, bounce: 0.15 }` | 通用 UI |
| 活泼 | `{ type: "spring", duration: 0.42, bounce: 0.22 }` | 营销页、趣味交互 |

### Ease 常量定义

TypeScript 中 ease 数组需要 `as const` 避免类型推断为 `number[]`：

```tsx
const EASE_OUT_QUAD = [0.25, 0.46, 0.45, 0.94] as const;
```

### 层叠上下文隔离

使用 `layoutId` 的容器务必加 `isolate`，避免 z-index 与外部布局互相影响：

```tsx
<nav className="relative isolate ...">
```

### CSS transition 与 Motion 不要打架

同一个视觉属性不要同时由 CSS transition 和 Motion 控制。将动效属性（背景、边框、阴影）交给 Motion，按钮本体只保留文字颜色等 transition。

---

## 案例索引

| # | Case | 文件 | 关键词 / 适用场景 |
|---|---|---|---|
| 1 | layoutId 导航切换 + 内容过渡 | [cases/layout-id-nav-switch.md](cases/layout-id-nav-switch.md) | `layoutId`、Nav / Tabs / Segmented Control 活跃态滑动、方向感知内容过渡、indicator 遮挡修复 |
| 2 | AnimatePresence 内容切换 + Popover 高度平滑过渡 | [cases/animate-presence-auto-height-popover.md](cases/animate-presence-auto-height-popover.md) | `AnimatePresence`、`popLayout`、Popover / Tooltip / Card 内容行数变化、auto-height 高度突变修复 |
| 3 | 共享元素迁移 + 辅助内容编排切换 | [cases/shared-element-orchestrated-view-switch.md](cases/shared-element-orchestrated-view-switch.md) | `layoutId` shared element、Header / Toolbar 模式切换、卫星内容错峰进退、深色文字与扫光污染修复 |
| 4 | 用 layoutDependency 隔离无关布局变化 | [cases/layout-dependency-isolate-indicator.md](cases/layout-dependency-isolate-indicator.md) | `layoutDependency`、Segmented Control / Tabs 选中指示器、祖先高度变化、未交互控件上下漂移 |
| 5 | 测量内容高度并平滑动画 auto → auto | [cases/measured-auto-height-content.md](cases/measured-auto-height-content.md) | `useMeasure`、`ResizeObserver`、同一内容树动态增减、异步内容 / 校验信息 / 响应式换行、精确高度裁剪 |
| 6 | 列表增删、Presence 与位置重排 | [cases/list-presence-layout-reorder.md](cases/list-presence-layout-reorder.md) | `AnimatePresence`、`popLayout`、`layout="position"`、Flex/Grid 批量增删、旧坐标退出快照、首帧 paint、快速切换 |
| 7 | 容器变形过渡（Container Transform） | [cases/container-transform-morph.md](cases/container-transform-morph.md) | 触发器原地扩展成面板、卡片飞向视口中央变浮层、占位 + 视觉克隆、相位状态机、遮罩 / 柔影 / 焦点管理、hover 底色残块与描边遮挡 |
| 8 | 鼠标驱动的分层 2.5D 视差 | [cases/pointer-layered-parallax.md](cases/pointer-layered-parallax.md) | 卡片配图跟随鼠标、SVG / 图片分层、共享弹簧坐标、轻微倾斜、退出归位、减少动态效果；不用于滚动视差 |
| 9 | 连续布局过渡（Flow-aware content transitions） | [cases/continuous-layout-transitions.md](cases/continuous-layout-transitions.md) | 内容淡入淡出、真实占位伸缩、相邻元素让位、退出与草稿保留、条件间距、嵌套跟随；附独立组件模板 |

> 更多 case 持续补充中。新增 case 请参考 [CONTRIBUTING.md](CONTRIBUTING.md)。

---

## 场景匹配指南

当用户的需求描述匹配以下关键词时，Agent 应阅读对应 case：

### 内容与周围元素一起连续变化 → 优先 Case 9

- 「按 Motion Case 9 做连续布局过渡」
- 「内容一边淡入，一边逐渐撑开；收起时淡出并收回空间」
- 「弹窗外框已经平滑，但折叠内容还是瞬间出现，下面元素瞬移」
- 「主动变化和被动让位都要有始有终」「间距最后不要突然消失」
- 「嵌套展开时外层不要拖尾，快速反向与输入草稿也要正确」

**可直接复制：**「按 motion-recipes 的连续布局过渡实现：内容淡入淡出、真实占位伸缩、相邻元素连续让位；保留完整退出和草稿，验证中途反向与嵌套变化。」

这是本 Skill 的效果约定名，不是 Motion API。先读 [Case 9](cases/continuous-layout-transitions.md)，按变化类型选择最小实现；需要组合能力时使用 [组件模板](assets/flow-transition.tsx)。Case 5 解决自然尺寸测量，Case 2 解决内容替换，Case 6 解决离散列表重排；它们单独使用时不必读取 Case 9。

### layoutId 导航切换 + 内容过渡 → Case 1

- 「给设置页 nav 切换加 Motion 动效」
- 「用 layoutId 做 tabs / nav / segmented control 的活跃态动画」
- 「切换左侧菜单时，右侧内容也要有过渡效果」
- 「实现活跃背景在多个按钮之间滑动」
- 「修复 layoutId 动画遮挡其他选项的问题」
- 设置页侧边栏、Tabs、Filter Pills、Dashboard 二级导航

### AnimatePresence 内容切换 + Popover 高度平滑过渡 → Case 2

- 「popover 切换内容时高度突然跳变」
- 「上一步/下一步时 content 行数不同，高度突变」
- 「AnimatePresence mode wait 导致新内容挂载时高度闪一下」
- 「修复 auto-height / 动态内容高度过渡」
- Tour、Onboarding Popover、Tooltip Card、Command Palette、Stepper、Wizard、Help Bubble

### 共享元素迁移 + 辅助内容编排切换 → Case 3

- 「滚动后品牌 Header 变成操作栏，品牌名要平滑移动」
- 「两个视图共有一个标题，其余按钮需要自然进退场」
- 「layoutId 过渡态文字在深色模式下变黑」
- 「新操作区第一帧闪现，旧操作区最后突然消失」
- 「共享渐变文字 / 金色扫光过渡时重影或颜色异常」
- 品牌 Header、响应式 Toolbar、搜索框展开、Mini / Full 模式、卡片到详情标题迁移

### 用 layoutDependency 隔离无关布局变化 → Case 4

- 「切换配置后，下方未操作的 Segmented Control 高亮胶囊会短暂上下漂移」
- 「页面内容瞬间重排，只有 layoutId indicator 带位移过渡」
- 「如何避免祖先高度变化触发无关的 layout 动画」
- 「这个问题应该修组件还是修使用层」
- Segmented Control、Tabs、Filter Pills、单选按钮组中的共享选中指示器

### 单层静态 FAQ / 普通折叠 → 最小开合方案

- 内容仅随展开 / 收起变化，没有异步、嵌套或表单状态：局部 `height: 0 ↔ auto` + opacity 即可。
- 不为此默认引入 Observer 或整套组合模板；需要完整效果验收时看 Case 9 的最小分支。

### 测量内容高度并平滑动画 `auto -> auto` → Case 5

- 「内容增加后，卡片 / 抽屉高度要平滑长开」
- 「表单校验信息出现时，不要突然把下面内容顶下去」
- 「同一个组件内容动态变化，没有 key 切换，怎么动画高度」
- 「用 useMeasure / ResizeObserver 实现 auto height 动画」
- 「异步内容、图片加载或响应式换行后高度要平滑更新」
- 设置卡片、Family Drawer、FAQ、内联错误区、异步预览、筛选摘要

### 列表增删、Presence 与位置重排 → Case 6

- 「筛选后删除的标签要原地淡出，其他标签平滑补位」
- 「新增项在最终位置淡入，旧项只重排一次」
- 「Flex / Grid 批量增删时元素分两批消失」
- 「退出项或新增项的首态没有真正显示」
- 「layout 和 scale 一起用导致文字换行或边框拉伸」
- 「快速连续筛选后残留退出副本」
- 筛选标签、可删除 Chip、任务列表、卡片 Grid、排序列表、搜索结果

### 容器变形过渡（Container Transform） → Case 7

- 「点击筛选按钮，让它原地展开成一个筛选面板」
- 「点击卡片后，卡片放大 / 飞到屏幕中央变成详情浮层，背景加遮罩」
- 「按钮变成搜索框，要有变形的连续感」
- 「FAB 点击后变成对话框 / 图片点开变居中灯箱」
- 「用 layoutId 包整个卡片做展开，过渡中文字拉伸、圆角变形」
- 「卡片和详情共用标题 / 徽章，过渡时要跟着飞」
- 「按钮 hover 后展开 / 收起，过渡中出现矩形底色或边框短暂缺失」
- 「容器变形时内容原地淡入淡出有些呆滞，想尝试沿展开 / 收起方向轻移衔接」（Case 7 可选增强，按组件评估）
- 筛选面板、搜索框展开、内联编辑、卡片详情浮层、图片灯箱、FAB → Dialog、通知项 → 通知中心

### 鼠标驱动的分层 2.5D 视差 → Case 8

- 「卡片配图跟随鼠标位置，产生立体层次感」
- 「几层纸张 / 面板前后错动，移出后平滑归位」
- 「实现 layered parallax / pointer parallax / card tilt」
- 「鼠标跟随时 SVG 原有倾斜或居中丢失」「减弱动态效果后插画仍倾斜」
- 功能入口、产品卡片、局部 Hero 插画；页面滚动驱动的视差不按本 case 实现。

<!--
### [未来 Case 名称] → Case N
- 「...」
-->

---

## 没有匹配 case 时的通用策略

如果用户需求没有直接匹配任何 case，Agent 应：

1. 从最接近的 case 中提取可复用的模式（如 `layoutId` 层级策略、`AnimatePresence` 用法）。
2. 结合「通用原则」中的参数和规范。
3. 遵循以下通用动效设计模式：
   - 进入动画：`opacity: 0 → 1` + 轻微位移（4–12px）
   - 退出动画：比进入快 20–30%，位移更小
   - 固定高度内容可用 `AnimatePresence mode="wait"` 避免新旧内容重叠
   - keyed 内容互换导致自动高度变化时读 Case 2，使用参与 layout 的容器 + `mode="popLayout"`
   - 内容、占位、被动兄弟和外框需要共同连续变化时先读 Case 9，按层分配动画责任；不要只动画最外层
   - 同一内容树从一个 `auto` 高度变到另一个 `auto` 高度，且普通 `layout` 效果不足时读 Case 5，测量内层并动画外层数值高度
   - 方向感知：根据索引变化计算方向，传入 `custom` prop
4. 完成后检查：TypeScript 类型、z-index 层级、是否有重复样式冲突。
