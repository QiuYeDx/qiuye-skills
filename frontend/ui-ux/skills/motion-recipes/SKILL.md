---
name: motion-recipes
description: >-
  Motion (motion/react, framer-motion) 动效实现案例集：layoutId 导航与共享元素、AnimatePresence
  内容切换、auto-height 与连续布局过渡、列表增删重排、容器变形（卡片 / 按钮展开成面板）、
  鼠标分层视差。每个 case 含模板代码、坑位与验收清单。Use when implementing or fixing a concrete
  Motion animation such as layout animation, dynamic height, popLayout, layoutDependency,
  shared element, container transform or pointer parallax, including “内容撑开时下面元素不要瞬移”.
  Not for naming an effect or auditing motion across an app.
---

# Motion Recipes — 动效案例集

经过实战验证的 Motion 动效实现方案集合。每个 case 提供完整的模板代码、设计原则、常见坑位与修复策略，让 AI Agent 在类似场景下能快速、稳定地产出可维护的动效代码。

## 使用方式

本 Skill 是索引型文档，具体实现细节在 `cases/` 子目录中。

**Agent 执行流程：**

1. 用下方「选择 case」表定位**一个**主 case；只有主 case 内明确引用时再读其他 case，不要逐篇拼读。
2. 使用 Read 工具阅读对应 case 文件的完整内容。
3. 按 case 中的「AI Agent 执行步骤」逐步实施。
4. 完成后按 case 中的「验收清单」逐项检查。

如果没有完全匹配的 case，选择最接近的 case 作为基础，结合通用原则进行调整。

---

## 选择 case

高度、内容替换、列表这几类需求最容易选错，按“变化的是什么”判断：

| 变化 | 主 case |
|---|---|
| 单层静态折叠，内容只在开合时变化 | 无需 case：局部 `height: 0 ↔ auto` + opacity |
| 同一内容树的自然高度持续变化（校验信息、异步内容、换行） | Case 5 |
| keyed 内容互换（步骤 / 预览 / 错误态），容器高度随之变化 | Case 2 |
| 离散列表项增删、排序、跨行重排 | Case 6 |
| 以上任一，且同时要求“内容淡入淡出 + 真实占位伸缩 + 下方兄弟连续让位”，或有嵌套展开、草稿保留、条件间距 | Case 9（按其中的最小分支回到 2 / 5 / 6） |
| Nav / Tabs 活跃态滑块 | Case 1；祖先重排导致指示器漂移见 Case 4 |
| 两个视图共有元素迁移，其余内容错峰进退 | Case 3 |
| 小元素变形成面板 / 卡片飞到中央成浮层 | Case 7 |
| 卡片插画跟随鼠标的分层视差 | Case 8 |

---

## 通用原则

以下原则适用于所有 Motion 动效场景，各 case 不再重复说明：

### 依赖与导入

```tsx
// motion 包（11.11 起提供 motion/react 入口，12.x 及以后同样适用）
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
| 7 | 容器变形过渡（Container Transform） | [cases/container-transform-morph.md](cases/container-transform-morph.md) | 触发器原地扩展成面板、卡片飞向视口中央变浮层、占位 + 视觉克隆、相位状态机、遮罩 / 阴影交接 / 焦点管理、hover 底色残块与描边遮挡 |
| 8 | 鼠标驱动的分层 2.5D 视差 | [cases/pointer-layered-parallax.md](cases/pointer-layered-parallax.md) | 卡片配图跟随鼠标、SVG / 图片分层、共享弹簧坐标、轻微倾斜、退出归位、减少动态效果；不用于滚动视差 |
| 9 | 连续布局过渡（Flow-aware content transitions） | [cases/continuous-layout-transitions.md](cases/continuous-layout-transitions.md) | 内容淡入淡出、真实占位伸缩、相邻元素让位、退出与草稿保留、条件间距、嵌套跟随；附独立组件模板 |

> 更多 case 持续补充中。新增 case 请参考 [CONTRIBUTING.md](CONTRIBUTING.md)。

---

## 场景匹配指南

用户常见说法 → case（完整场景见各 case 的「适用场景」）：

| 用户说法 | Case |
|---|---|
| 「nav / tabs 活跃背景要滑过去」「切菜单时右侧内容也要过渡」「layoutId 遮住了其他选项」 | 1 |
| 「popover 换步骤时高度突然跳」「mode wait 新内容挂载闪一下」 | 2 |
| 「滚动后 Header 变操作栏，品牌名平滑移动」「layoutId 过渡中文字在暗色下变黑」 | 3 |
| 「没动过的 Segmented Control 高亮在别处重排时上下漂」 | 4 |
| 「内容增加后卡片 / 抽屉要平滑长开」「useMeasure / ResizeObserver 做 auto height」 | 5 |
| 「删掉的标签原地淡出，其他平滑补位」「批量增删分两批消失」「快速筛选残留副本」 | 6 |
| 「筛选按钮原地展开成面板」「卡片飞到中央变详情浮层」「layoutId 包整卡导致文字拉伸」 | 7 |
| 「配图跟随鼠标有立体层次」「layered / pointer parallax、card tilt」 | 8 |
| 「内容一边淡入一边撑开，下面元素别瞬移」「外框平滑但里面还闪」「间距最后不要突然消失」「主动变化和被动让位都要有始有终」 | 9 |

Case 9 是本 Skill 的效果约定名（连续布局过渡），不是 Motion API；组合实现可用 [组件模板](assets/flow-transition.tsx)。

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
