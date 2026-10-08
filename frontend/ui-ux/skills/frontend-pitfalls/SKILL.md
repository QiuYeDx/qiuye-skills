---
name: frontend-pitfalls
description: >-
  前端避坑 case 集合：沉淀真实项目中容易被 AI Agent 或开发者误用的 UI/CSS/交互实现坑位，
  并给出稳定结构、排查顺序、推荐模板与验收清单。Use when fixing or implementing
  tricky frontend UI behavior, CSS rendering issues, browser compatibility
  problems, animation glitches, Tailwind/shadcn UI pitfalls, glassmorphism,
  backdrop-filter/backdrop-blur, stacking context, overflow clipping, opacity
  compositing, mobile header dropdowns, transparent navbars, HUD/tool overlays,
  Radix/shadcn ScrollArea sizing and positioning, scrollbars that appear after
  a transition and reflow content, shadow jumps when a container-transform
  overlay lands on its card, or when the user asks for "前端避坑",
  "避坑 case", "背景模糊失效", "backdrop-filter", "backdrop-blur", "玻璃态",
  "毛玻璃", "Safari 模糊", "移动端菜单模糊", "透明导航栏", "浮层动画闪烁",
  "ScrollArea 滚不动", "滚动条挤占宽度", "滚动条出现内容重排",
  "阴影突然消失", "收起时阴影跳变", "展开浮层阴影".
---

# Frontend Pitfalls — 前端避坑 Case 集合

沉淀真实项目中高频、隐蔽、容易重复踩的前端实现坑位。每个 case 以「现象 → 原因 → 稳定结构 → Agent 执行步骤 → 验收清单」组织，优先帮助 Agent 在代码里做出正确结构，而不是只解释概念。

## 使用方式

1. 根据用户描述，在「案例索引」中匹配最相关的 case。
2. 阅读对应 `cases/` 文件的完整内容。
3. 先按 case 的「排查顺序」确认问题根因，再按「推荐结构」修改代码。
4. 完成后执行 case 的「验收清单」，尤其检查浏览器兼容、层叠上下文、动画离场状态和移动端表现。

如果没有完全匹配的 case，选择最接近的 case 作为参考，并把新踩到的坑补充为新的 case。

## 案例索引

| # | Case | 文件 | 关键词 / 适用场景 |
|---|---|---|---|
| 1 | backdrop-filter 背景模糊与玻璃态浮层 | [cases/backdrop-filter-glass-blur.md](cases/backdrop-filter-glass-blur.md) | `backdrop-filter`、`backdrop-blur`、玻璃态、毛玻璃、移动端 Header 菜单、透明导航栏、HUD 浮层、Safari 模糊失效、入场后才突然变模糊 |
| 2 | Radix / shadcn ScrollArea 的定位、尺寸与内容宽度 | [cases/radix-scroll-area-layout.md](cases/radix-scroll-area-layout.md) | `ScrollArea`、内联 `position: relative` 覆盖定位 class、`display: table` 横向撑宽、Viewport 内联 overflow、原生滚动条挤占宽度导致重排、弹窗 / Sheet 内部滚动 |
| 3 | 容器变形过渡中的阴影交接 | [cases/morph-shadow-handoff.md](cases/morph-shadow-handoff.md) | 卡片展开浮层 / 灯箱 / FAB → Dialog、收起落地时重阴影突变、展开首帧阴影满强度、共享静止阴影、`--lift` 变量、WAAPI `opacity` 过期帧 |

## 场景匹配指南

### backdrop-filter 背景模糊与玻璃态浮层 → Case 1

- 「Header 下拉菜单背景没有真正模糊」
- 「移动端菜单 backdrop-blur 写了但看起来只是透明」
- 「玻璃态浮层动画结束后才突然出现强模糊」
- 「离场时边框/玻璃层最后一帧硬消失」
- 「父元素和子浮层都用了 backdrop-blur，子层失效」
- 「Chrome / Safari / 移动端浏览器的毛玻璃表现不一致」
- 透明导航栏、移动端菜单、Command Palette、HUD 工具条、搜索浮层、悬浮面板

### Radix / shadcn ScrollArea 的定位、尺寸与内容宽度 → Case 2

- 「弹窗展开完成后，右侧突然出现滚动条，内容跳了一下」
- 「Windows 上滚动条挤占宽度，Mac 上看不出来」
- 「用了 ScrollArea 以后滚不动 / 内容被裁掉一截」
- 「ScrollArea 里横向滚动的截图条把整个面板撑宽了」
- 「写了 `absolute inset-0` 但 ScrollArea 还是被内容撑高」
- 「动画期间想禁止滚动，给 Viewport 写 overflow: hidden 不生效」
- 卡片展开浮层、Sheet、Dialog、Header 下拉目录、侧栏等内部滚动容器

### 容器变形过渡中的阴影交接 → Case 3

- 「卡片展开的浮层收起到最后，重阴影突然变成卡片的轻阴影」
- 「展开一开始阴影就很重，不是慢慢浮起来的」
- 「几何动画已经很连续，但落地那一帧还是闪一下」
- 「柔影层淡出后卸载，最后一帧阴影闪回」
- 卡片 → 详情浮层、缩略图 → 灯箱、FAB → Dialog、列表项 → 居中面板

## 新增 Case 维护约定

新增 case 时：

1. 在 `cases/` 下创建小写英文连字符文件名，如 `css-sticky-overflow.md`。
2. 在本文件「案例索引」和「场景匹配指南」中注册。
3. case 文件至少包含：目标、适用场景、排查顺序、推荐结构、常见坑与修复、AI Agent 执行步骤、验收清单。
4. 只记录实战中非显而易见、容易误判或容易被 Agent 写错的内容；基础 API 教程不要放进来。
