# 接入与框架适配

## 选择接入层级

简单项目可直接使用安装版本的 Lenis 官方基础方案。`smoothWheel: true` 平滑 wheel；`syncTouch: false` 保留原生触摸。CSS `scroll-behavior: smooth` 不能单独解决离散滚轮步进。

需要本案例同等锁定处理、按需 RAF、原生交接时，复制 assets 中两个 TS 文件到项目通用逻辑目录，合并必要 CSS。控制器只支持 window 根滚动，须在 DOM 可用后调用；调用前确保没有其他根 Lenis/平滑引擎实例。

模板默认 `nativeScrollInterop: false`，不会包装全局方法，但此模式也不能保证异步原生 smooth 请求能打断尚未结束的 Lenis 惯性。根据 [native-handoff.md](native-handoff.md) 做出选择，不要只把开关留在默认值就宣称兼容完成。

## 普通 TypeScript

```ts
import { createSmoothPageScroll } from "./smooth-page-scroll";

// 以下示例已选择维护既有原生滚动调用，启用方法包装。
const dispose = createSmoothPageScroll({ nativeScrollInterop: true });

// 应用卸载时调用；重复初始化之前必须先 dispose。
// dispose();
```

无 SSR 时可在 DOMContentLoaded 后调用；有 SSR 时仅在客户端挂载阶段调用。模板不自动安装依赖，按项目包管理器添加/复用 Lenis，维护原锁文件格式；不要复制某个开发机的 Node/pnpm 路径。

## React

在现有组件目录新增薄客户端组件，不把服务端页面整体改成 Client Component：

```tsx
"use client";

import { useEffect } from "react";
import { createSmoothPageScroll } from "./smooth-page-scroll";

export function SmoothPageScroll() {
  useEffect(
    () => createSmoothPageScroll({ nativeScrollInterop: true }),
    [],
  );
  return null;
}
```

根布局挂载一次 `<SmoothPageScroll />`，不需要包裹 children。正常 cleanup 支持 React Strict Mode 的 setup→cleanup→setup；它不支持多个组件同时初始化全局引擎。观察页面是否已有第三方 provider 管理同一个实例。

## Next.js App Router

在上述组件中使用 `usePathname()`，将 pathname 加入 effect 依赖，在路径变化后清理/重建。不要主动 scrollTo(0)：滚动恢复和 hash 导航仍由路由器/浏览器管理。搜索参数变化通常不必重建，按项目分页和恢复策略验证。

如果合并了 assets 中的 `html { scroll-behavior: smooth }`，需核对所用 Next.js 版本的处理。案例 Next.js 15 在根 html 上设置 `data-scroll-behavior="smooth"`，让导航流程识别原生平滑行为。其他框架无需机械复制该属性。

## CSS 与锚点

[基础样式](../assets/smooth-scroll.css) 是根滚动所需的最小子集。只在非减少动态效果模式启用 CSS 平滑；保留项目已有 scroll-margin/scroll-padding。

模板 `anchors: false`，点击捕获阶段先释放惯性，浏览器负责锚点 URL、焦点与历史。不要再同时启用另一套锚点拦截器。若选择 Lenis 的 anchors 功能，应以安装版本实际行为验证 URL、焦点、修饰键点击、路由同路径不同 query 和不可见目标。

不要不加审查地叠加完整 Lenis CSS：其中 stopped overflow 和滚动时 iframe pointer-events 规则可能影响既有弹窗滚动条补偿与嵌入内容。若采用 autoToggle，则使用该功能要求的样式并核对目标浏览器支持。

## 锁定与嵌套容器

模板识别 root/body 的 overflow hidden/clip、Radix/react-remove-scroll 的 `data-scroll-locked`，以及通用 `data-smooth-scroll-locked`。其他库应通过实际锁定机制适配，而不是任意存在一个 dialog 就禁止整页滚动。

对原本只用事件 preventDefault 的自定义图片预览，可将以下计数纳入现有锁定 effect；这个标记只负责通知平滑引擎，不能代替原有阻止背景滚动的实现：

```ts
// 在原有锁定逻辑启用时执行。
const body = document.body;
body.dataset.smoothScrollLocked = String(
  Number(body.dataset.smoothScrollLocked || 0) + 1,
);

// 在该次锁定的 cleanup 中执行，确保只调用一次。
function releaseSmoothScrollLock() {
  const count = Number(body.dataset.smoothScrollLocked || 0) - 1;
  if (count > 0) body.dataset.smoothScrollLocked = String(count);
  else delete body.dataset.smoothScrollLocked;
}
```

多个 overlay 必须使用相同计数协议，或接入项目已有的集中锁管理器。不要在嵌套弹窗关闭时直接移除别人的锁。

一般内部容器由 `allowNestedScroll` 识别；有独立 wheel 语义的图表、地图或面板可用 `data-lenis-prevent-wheel`，按需添加 overscroll-behavior。验证容器中部与边界处的滚动链行为。

## Motion、GSAP 与特殊根容器

Motion 的 window `useScroll` 和普通 scroll listeners 读取真实位置，无需代理。使用 `container` 参数的 hooks 应继续指向原来的容器，不要改成 window 来迎合模板。

GSAP ScrollTrigger 等按其官方适配方案验证；如果统一到 GSAP ticker，取消本模板独立 RAF，只保留一个推进 Lenis 的时钟。不要既 autoRaf 又手动 raf。自定义滚动根需同步改造坐标读取、锁定检查、尺寸和原生交接作用域，不能只替换 wrapper 一项。
