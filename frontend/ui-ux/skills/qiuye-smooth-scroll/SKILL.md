---
name: qiuye-smooth-scroll
description: >-
  Implement or debug page-level smooth wheel scrolling while preserving native
  scroll coordinates, Motion useScroll, sticky layouts, programmatic scrolling,
  modal locks, nested scrollers, and router restoration. Use for Windows wheel
  stepping, Lenis integration, smooth scrolling, scroll-driven animation jitter,
  全局平滑滚动、滚轮逐格跳动、平滑滚动兼容。Not for merely easing a component animation
  or adding CSS smooth behavior to a single anchor link.
---

# QiuYe Smooth Scroll

让离散滚轮输入变成连续的真实页面滚动，同时保留已有滚动消费者的行为。优先利用现有引擎；新接入可使用 Lenis，额外兼容层按项目需要选择。本 Skill 提供项目接入能力，不要求创建或发布 npm 包。

## 先检查再选方案

检查框架、包管理器及锁文件、已有 Lenis/其他平滑滚动实例、根滚动容器、浏览器范围；搜索 `useScroll`、scroll listeners、`scrollTo/scrollBy/scrollIntoView`、sticky、scroll-snap、overflow、弹窗锁定和路由恢复。

| 项目情况 | 做法 |
| --- | --- |
| 已有平滑滚动引擎 | 优先修复或配置现有实例，同一滚动根不要安装第二个引擎 |
| 只需锚点平滑 | 使用原生 CSS/scrollTo；不必引入全局滚轮拦截 |
| 需要平滑滚轮，原生滚动驱动 Motion/3D | 使用真实文档滚动的 Lenis；不要 transform 整个页面制造代理坐标 |
| 已有外部程序化滚动 | 阅读交接说明，决定显式取消惯性还是启用原生 API 包装 |
| 根是自定义容器、已有 scroll-snap 或多个引擎 | 先明确滚动所有权；本 Skill 的 window 模板不能直接套用 |

用户已指定技术栈时尊重选择，不为本 Skill 擅自替换滚动引擎、升级依赖树或更改整站布局。

## 实施入口

1. 阅读 [接入与框架适配](references/integration.md)，选择基础 Lenis 接入或带按需 RAF/锁定处理的模板。
2. 若需要维护已有程序化滚动，阅读 [控制权交接与边界](references/native-handoff.md)。原生 API 包装必须作为明确的技术选择说明，不称其为零侵入或任意库无条件兼容。
3. 按需复制 [控制器模板](assets/smooth-page-scroll.ts)、[交接模板](assets/native-scroll-handoff.ts) 和 [基础样式](assets/smooth-scroll.css)，修改 import、项目锁信号和框架挂载点。资产是可适配的起点，不是通用 npm 库；不携带博客品牌、Hero 选择器或内容路由。
4. 按 [浏览器验收](references/validation.md) 验证。报告已测环境和未覆盖项，区分构建成功、真实滚动验证和主观手感。

## 保持的行为

- 更新真实 `scrollY/scrollTop`，保留原生 scroll 事件与文档流；现有 Motion hooks、IntersectionObserver、sticky 使用同一坐标体系。
- 默认只平滑纵向 wheel；触摸保持原生惯性，Ctrl 缩放、Shift/横向手势和已被其他控件消费的事件不抢占。
- 键盘、指针按下、锚点、导航和外部程序化滚动可以打断惯性；不强制等待动画结束，也不擅自重置路由位置。
- 遵守动态变化的 reduced motion；后台和弹窗锁定时取消残余惯性，恢复时从真实位置重建。
- 区分内部滚动容器与页面滚动；弹窗内能滚动不代表背景可以继续滚动。
- 一棵应用树只有一个根控制器。SSR 时不访问 DOM；挂载、Strict Mode 重挂载、路由变化和卸载均清理监听、observer 与 RAF。

## 动效与性能

`lerp: 0.16`、`wheelMultiplier: 1` 是本案例起点，不是普遍最佳值。通过实际鼠标和触控板调整：输入总距离不变、及时响应、能反向、不长时间拖尾。平台无法可靠区分所有 wheel 来自鼠标还是触控板，不要声称已精确识别硬件。

基础 `autoRaf: true` 接入更简单；只有选择按需 RAF 时才承担其时钟与唤醒逻辑。模板使用 `autoRaf: false`，输入被接受后唤醒，收敛后停止；重启将 Lenis `time = 0`，使用 RAF 自身时间戳建立基准。不要混用同帧 `performance.now()` 导致负时间步长。升级 Lenis 后复核这些 API 行为。

`allowNestedScroll` 会在输入时检查 DOM；复杂页面可使用明确的 prevent 标记。只观察 root/body 的相关属性，不在每帧遍历整棵树。不要给 Motion 再叠加无必要的平滑进度，造成滚动与视觉响应延迟。

## 来源与适用范围

模板基于 QiuVision 中 Lenis 1.3.23 的实际实现：Windows Chromium 上验证了滚轮、原生 API、路由、嵌套容器和图片预览，另有移动视口触摸模拟。它不等于 Safari、Firefox 或真实 iOS 已验收。

依赖以目标项目安装版本和 [Lenis 官方文档](https://github.com/darkroomengineering/lenis) 为准；不要将版本基线、Next.js 配置、原项目包管理器或窗口尺寸推广为所有项目的硬性规则。
