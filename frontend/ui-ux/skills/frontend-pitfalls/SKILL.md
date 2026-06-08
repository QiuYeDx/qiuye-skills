---
name: frontend-pitfalls
description: >-
  前端避坑 case 集合：沉淀真实项目中容易被 AI Agent 或开发者误用的 UI/CSS/交互实现坑位，
  并给出稳定结构、排查顺序、推荐模板与验收清单。Use when fixing or implementing
  tricky frontend UI behavior, CSS rendering issues, browser compatibility
  problems, animation glitches, Tailwind/shadcn UI pitfalls, glassmorphism,
  backdrop-filter/backdrop-blur, stacking context, overflow clipping, opacity
  compositing, mobile header dropdowns, transparent navbars, HUD/tool overlays,
  or when the user asks for "前端避坑", "避坑 case", "背景模糊失效",
  "backdrop-filter", "backdrop-blur", "玻璃态", "毛玻璃", "Safari 模糊",
  "移动端菜单模糊", "透明导航栏", "浮层动画闪烁".
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

## 场景匹配指南

### backdrop-filter 背景模糊与玻璃态浮层 → Case 1

- 「Header 下拉菜单背景没有真正模糊」
- 「移动端菜单 backdrop-blur 写了但看起来只是透明」
- 「玻璃态浮层动画结束后才突然出现强模糊」
- 「离场时边框/玻璃层最后一帧硬消失」
- 「父元素和子浮层都用了 backdrop-blur，子层失效」
- 「Chrome / Safari / 移动端浏览器的毛玻璃表现不一致」
- 透明导航栏、移动端菜单、Command Palette、HUD 工具条、搜索浮层、悬浮面板

## 新增 Case 维护约定

新增 case 时：

1. 在 `cases/` 下创建小写英文连字符文件名，如 `css-sticky-overflow.md`。
2. 在本文件「案例索引」和「场景匹配指南」中注册。
3. case 文件至少包含：目标、适用场景、排查顺序、推荐结构、常见坑与修复、AI Agent 执行步骤、验收清单。
4. 只记录实战中非显而易见、容易误判或容易被 Agent 写错的内容；基础 API 教程不要放进来。
