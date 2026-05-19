---
name: motion-recipes
description: >-
  Motion 动效案例集：提供经过验证的 Motion (framer-motion) 动效实现方案与最佳实践。
  涵盖 layoutId 导航切换、AnimatePresence 内容过渡、手势交互、列表动画等常见场景。
  每个 case 包含完整模板代码、常见坑位修复与验收清单，确保 AI Agent 能稳定复刻高质量动效。
  Triggers on: "motion", "framer-motion", "layoutId", "AnimatePresence",
  "layout animation", "nav 切换动效", "tabs 动画", "活跃态滑动",
  "内容过渡动画", "方向感知动画", "spring animation", "motion 最佳实践",
  "motion recipes", "动效案例", "layout 动画遮挡".
---

# Motion Recipes — 动效案例集

经过实战验证的 Motion 动效实现方案集合。每个 case 提供完整的模板代码、设计原则、常见坑位与修复策略，让 AI Agent 在类似场景下能快速、稳定地产出可维护的动效代码。

## 使用方式

本 Skill 是索引型文档，具体实现细节在 `cases/` 子目录中。

**Agent 执行流程：**

1. 根据用户需求，在下方「案例索引」中匹配最相关的 case。
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

> 更多 case 持续补充中。新增 case 请参考 [CONTRIBUTING.md](CONTRIBUTING.md)。

---

## 场景匹配指南

当用户的需求描述匹配以下关键词时，Agent 应阅读对应 case：

### layoutId 导航切换 + 内容过渡 → Case 1

- 「给设置页 nav 切换加 Motion 动效」
- 「用 layoutId 做 tabs / nav / segmented control 的活跃态动画」
- 「切换左侧菜单时，右侧内容也要有过渡效果」
- 「实现活跃背景在多个按钮之间滑动」
- 「修复 layoutId 动画遮挡其他选项的问题」
- 设置页侧边栏、Tabs、Filter Pills、Dashboard 二级导航

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
   - `AnimatePresence mode="wait"` 避免新旧内容重叠
   - 方向感知：根据索引变化计算方向，传入 `custom` prop
4. 完成后检查：TypeScript 类型、z-index 层级、是否有重复样式冲突。
