# Case 8: 鼠标驱动的分层 2.5D 视差

## 目标

让卡片内的装饰插画跟随鼠标位置产生轻微倾斜与不同深度的位移，形成有前后关系的层次感。移出时平滑归位，文字、点击区域和页面布局保持稳定。

## 适用场景

- 「配图跟随卡片里的鼠标，有一点 2.5D / 立体层次感」
- 「前后几层纸张、玻璃面板或图形移动幅度不同」
- 产品入口、功能卡片、展示卡片、Hero 中的局部装饰插画。

本案例处理 **pointer-driven layered parallax**。页面滚动驱动的视差应使用滚动进度；需要真实遮挡、相机和光照的场景另选 3D 渲染。单张不可拆分的位图只能整体倾斜或平移，不能凭空获得独立内部图层；先确认素材是否可拆分，不为此强制重画已有素材。

## 核心设计原则

### 1. 感应区域稳定，装饰层运动

以静止的卡片根节点测量坐标、监听 Pointer Events。只对内部插画施加 transform；默认不移动标题、正文、焦点环或点击区域。

将鼠标位置映射到 `[-1, 1]`，中心为零，边缘饱和：

```ts
const nx = clamp((event.clientX - rect.left) / rect.width * 2 - 1);
const ny = clamp((event.clientY - rect.top) / rect.height * 2 - 1);
```

零尺寸不计算。不要用 `offsetX / offsetY`，它们可能随着命中的子节点改变基准。不要测量正在旋转的插画，否则鼠标不动也可能发生反馈抖动。若感应节点的祖先有旋转 / 倾斜变换，轴对齐的 `getBoundingClientRect()` 不再等于局部坐标系，应将感应层移出该变换或单独做逆矩阵映射。

### 2. 一组弹簧坐标，派生多个深度

`useSpring` 平滑两个归一化坐标，`useTransform` 派生各层位移。后层移动较小或轻微反向，前层移动较大；全图可叠加低角度的 `rotateX / rotateY`。

不要让每次 `pointermove` 触发 React state 重渲染，也不要给每个图层叠加不同延迟的 spring。共享坐标能让方向反转时整幅图仍像一个物体。深度值控制幅度，不等于 `z-index`：SVG 的遮挡关系仍由绘制顺序决定。

### 3. 静态构图与动态变换分层

推荐结构为：静止感应卡片 → 静态定位外壳 → 整体倾斜层 → 分层位移 → 原有图形。

外壳持有 `translateY(-50%)` 等布局变换，Motion 只控制内层。SVG 原有 `translate / skew / rotate` 放在独立 `<g>` 上，避免 Motion 写入 CSS transform 后覆盖构图。决定动态层在静态变换内还是外：内层位移沿倾斜后的局部轴运动，外层位移沿插画坐标轴运动，两者视觉不同。

属于同一实体的底板、文字、图标和阴影一起分组。不要让标签与承载它的面板漂移分离。使用现有 SVG 时保留渐变、滤镜和 ID 唯一性；需要重用 ID 的组件用 `useId()`。

### 4. 生命周期属于交互的一部分

- `pointerleave / pointercancel`、窗口失焦、滚动或 resize：回到零位。滚动时归位是简单默认策略；若产品要求持续跟随，则重测卡片边界并用最后一个有效指针位置更新目标。
- 设备不支持精确悬停、触摸输入、系统要求减少动态效果：维持静态构图。
- 运行时切换减少动态效果：用 `jump(0)` 立即停止现有 spring；只禁止下一次事件会留下倾斜姿态。
- 卸载：移除事件、媒体查询监听以及自行创建的 observer / animation frame。

## 推荐实现模板与最小代码骨架

下面是一份可放在单个 `.tsx` 文件中的通用示例，使用 React、Motion 和 Tailwind。`ParallaxCard` 接收链接与文案；矩形和圆形仅示意图层，实际接入时替换为项目已有插画与视觉样式。已有路由组件时复用它的链接语义。

```tsx
"use client";

import { useEffect, useRef, type ReactNode } from "react";
import { motion, useSpring, useTransform, type MotionValue } from "motion/react";

const SPRING = { stiffness: 240, damping: 28, mass: 0.7 };
const clamp = (value: number) => Math.max(-1, Math.min(1, value));

function usePointerParallax<T extends HTMLElement>() {
  const ref = useRef<T>(null);
  const x = useSpring(0, SPRING);
  const y = useSpring(0, SPRING);

  useEffect(() => {
    const host = ref.current;
    if (!host) return;
    const media = window.matchMedia(
      "(hover: hover) and (pointer: fine) and (prefers-reduced-motion: no-preference)",
    );
    const reset = () => { x.set(0); y.set(0); };
    const stop = () => { x.jump(0); y.jump(0); };
    const onVisibility = () => { if (document.hidden) stop(); };
    const move = (event: PointerEvent) => {
      if (!media.matches || event.pointerType !== "mouse") {
        stop();
        return;
      }
      const rect = host.getBoundingClientRect();
      if (rect.width <= 0 || rect.height <= 0) return;
      x.set(clamp((event.clientX - rect.left) / rect.width * 2 - 1));
      y.set(clamp((event.clientY - rect.top) / rect.height * 2 - 1));
    };

    host.addEventListener("pointerenter", move);
    host.addEventListener("pointermove", move);
    host.addEventListener("pointerleave", reset);
    host.addEventListener("pointercancel", reset);
    window.addEventListener("blur", reset);
    window.addEventListener("resize", reset);
    // Capture also observes nested scrolling containers.
    window.addEventListener("scroll", reset, true);
    document.addEventListener("visibilitychange", onVisibility);
    media.addEventListener("change", stop);
    return () => {
      host.removeEventListener("pointerenter", move);
      host.removeEventListener("pointermove", move);
      host.removeEventListener("pointerleave", reset);
      host.removeEventListener("pointercancel", reset);
      window.removeEventListener("blur", reset);
      window.removeEventListener("resize", reset);
      window.removeEventListener("scroll", reset, true);
      document.removeEventListener("visibilitychange", onVisibility);
      media.removeEventListener("change", stop);
    };
  }, [x, y]);

  return { ref, x, y };
}

function ParallaxLayer({ x, y, depth, children }: {
  x: MotionValue<number>;
  y: MotionValue<number>;
  depth: number;
  children: ReactNode;
}) {
  const offsetX = useTransform(x, value => value * depth);
  const offsetY = useTransform(y, value => value * depth * 0.65);
  return (
    <motion.g data-parallax-depth={depth} style={{ x: offsetX, y: offsetY }}>
      {children}
    </motion.g>
  );
}

export function ParallaxCard({ href, title, description }: {
  href: string;
  title: string;
  description: string;
}) {
  const { ref, x, y } = usePointerParallax<HTMLAnchorElement>();
  const rotateX = useTransform(y, value => -value * 4);
  const rotateY = useTransform(x, value => value * 6);

  return (
    <a ref={ref} href={href}
      className="relative isolate block min-h-64 w-full max-w-xl rounded-3xl border border-slate-200 bg-slate-50 p-6 text-slate-900 outline-offset-4 focus-visible:outline-2 focus-visible:outline-sky-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100">
      <div className="relative z-10 w-[56%]">
        <h2 className="text-xl font-semibold">{title}</h2>
        <p className="mt-3 text-sm leading-6 opacity-70">{description}</p>
      </div>
      <div aria-hidden="true"
        className="pointer-events-none absolute right-4 top-1/2 w-[38%] max-w-56 -translate-y-1/2 text-sky-600 dark:text-sky-400">
        <motion.svg viewBox="0 0 240 260" fill="none" focusable="false"
          className="block h-auto w-full overflow-visible"
          style={{ rotateX, rotateY, transformPerspective: 800 }}>
          <ParallaxLayer x={x} y={y} depth={-5}>
            <g transform="translate(28 16) skewY(-10)">
              <rect width="144" height="182" rx="12"
                fill="currentColor" fillOpacity=".1" stroke="currentColor" strokeOpacity=".2" />
            </g>
          </ParallaxLayer>
          <ParallaxLayer x={x} y={y} depth={5}>
            <g transform="translate(48 46) skewY(-10)">
              <rect width="144" height="182" rx="12"
                fill="currentColor" fillOpacity=".15" stroke="currentColor" strokeOpacity=".3" />
              <path d="M22 38h64M22 56h96M22 84h80M22 102h96"
                stroke="currentColor" strokeOpacity=".5" strokeWidth="4" strokeLinecap="round" />
            </g>
          </ParallaxLayer>
          <ParallaxLayer x={x} y={y} depth={16}>
            <g transform="translate(24 158)">
              <rect width="68" height="56" rx="12" fill="currentColor" />
              <circle cx="34" cy="28" r="11" stroke="white" strokeWidth="3" />
            </g>
          </ParallaxLayer>
        </motion.svg>
      </div>
    </a>
  );
}
```

调用示例：`<ParallaxCard href="/example" title="示例入口" description="替换为项目文案。" />`。hook 与感应节点一起挂载；若感应节点稍后才出现或被替换，使用 callback ref 跟踪节点并重绑监听，不要假设修改 `ref.current` 会重跑 effect。

## 参数建议

以下是调试起点，不是必须复制的设计 token。幅度要按实际插画尺寸、文字距离和窗口宽度复核。

| 参数 | 建议起点 | 调整依据 |
|---|---|---|
| Spring | stiffness 180–280、damping 24–32、mass 0.5–0.9 | 少回弹、约 200–350ms 内主要响应完成；反复横扫不拖尾 |
| 整体倾斜 | 每轴 3–7° | 保持文字和细线可读，不追求翻转效果 |
| Perspective | 600–1000 CSS px | 观察透视是否与原有构图协调 |
| 后 / 中 / 前景 | 约 -5 / 5 / 16 个 SVG 单位 | 根据图层间距与 viewBox 比例调整 |
| 纵向位移 | 横向的 0.6–0.8 倍 | 避免上下接近卡片文案或边界 |

SVG 位移的屏幕距离约为 `depth × 显示宽度 / viewBox宽度`，还会受静态变换影响。不要把 SVG 单位直接当成 CSS px；响应式缩小会自然减小视觉幅度。

大量卡片同时存在时，不要给每张卡片长期保留 `will-change` 或运行空闲循环。模板不使用每帧 React state；先分析性能，再按需将窗口事件集中管理、仅为活跃卡片绑定，或用 rAF 合并高频读数。若缓存边界，滚动、resize 和布局变化后必须失效。

## 常见坑与修复

### 坑 1：鼠标跨过文字时插画跳动

**原因：** 用事件子目标或 `offsetX` 定位。**修复：** 用明确传入的卡片 ref 和 `clientX - rect.left`；`pointerenter` 也设置目标，避免停在边缘时没有响应。

### 坑 2：原来的斜面或垂直居中失效

**原因：** 静态 CSS / SVG transform 与 Motion 控制同一节点。**修复：** 使用独立层，例如 `<motion.g style={{ x }}><g transform="skewY(-10)">…</g></motion.g>`。不要给 Motion 的 transform 再套 CSS transition。

### 坑 3：只是整张图片左右晃，没有层次

**原因：** 所有元素同幅度位移，或只对 SVG 根节点倾斜。**修复：** 按视觉实体拆成 3–5 层，给前后层不同深度；这不是将每条路径独立拆散。单层素材先整体倾斜，明确其能力边界。

### 坑 4：卡片边缘截断、阴影被裁掉或装饰挡住点击

**原因：** 位移超过安全区，SVG 默认裁剪或上层 overflow 隐藏，装饰层拦截输入。**修复：** 收敛幅度并留出边缘空间；需要时只在插画 SVG 设置 `overflow: visible`，检查所有祖先的裁剪，不全局关闭 overflow。纯装饰外壳设置 `pointer-events: none` 与 `aria-hidden`。

### 坑 5：移出或减少动态效果后仍停在倾斜姿态

**原因：** 只监听 move，或禁用输入却没有清理当前值。**修复：** 普通退出使用 `x.set(0); y.set(0)`；禁用动效使用 `x.jump(0); y.jump(0)`。内层滚动容器要用捕获阶段监听或直接绑定实际 viewport。

## 变体模式

- **HTML / 分层透明图片：** 把 `motion.g` 换为 `motion.div`；图层绝对定位，容器显式保留尺寸，depth 使用 CSS px。不要同时控制图片的自然布局尺寸。
- **已有倾斜 SVG：** 保留原静态构图，先加图层平移；只有整体倾斜确实改善空间感时再启用两个旋转轴。
- **整张卡片 tilt：** 用户明确要卡片本体旋转时才采用；增加不动的外层感应节点，内层卡片旋转，避免测量反馈。文字透视与焦点环仍需检查。

## AI Agent 执行步骤

1. 检查素材结构、现有动画库、静态 transform、裁剪和点击语义；确定鼠标感应范围和不应运动的内容。
2. 选出少量视觉实体，明确前后绘制关系、深度幅度和安全边距；先保留原有构图。
3. 用一组 spring 驱动归一化坐标；把动态变换放入独立节点，处理退出、设备条件、减少动态效果和卸载。
4. 在实际运行界面检查中心、四角、跨子节点移动与快速反向；观察中间帧及最后归位，不仅断言 transform 非零。
5. 查看项目支持的主题和窄 / 宽布局。先修复文本遮挡、裁剪或拖尾，再交付；验证后关闭本次创建的临时服务。

## 验收清单

- [ ] 默认构图与禁用动效状态完整；键盘 focus / Enter 不要求或触发鼠标跟随，链接或按钮仍可操作。
- [ ] 从中心向两侧移动时方向对应；前后图层有可观测的位移差，主体文字与布局边界不动。
- [ ] 指针经过卡片内不同子节点不跳变；连续反向移动能平滑追随，无固定延迟队列或明显震荡。
- [ ] 移出、取消、失焦和实际滚动容器滚动后归零，卡片之间不会串动。
- [ ] 运行时开启减少动态效果能立即归零，后续移动保持静态；触摸滚动不触发视差。
- [ ] 四角极值、各支持主题及最窄布局下无文字遮挡、阴影硬裁剪或额外横向滚动。
- [ ] 类型检查通过；没有重复控制 transform、每次 pointermove 重渲染或卸载后的残留监听。
- [ ] 至少检查一段真实连续操作，或一组中间帧与起止帧；静态最终截图只能证明构图，不能证明跟随与归位质量。

## 推荐回答格式

说明哪些图层如何响应、禁用 / 归位规则、实际验证的主题和窗口范围。能提供时附真实运行预览；明确未验证的平台。不把该案例的示例配色、图形、角度或弹簧数值描述成跨项目强制规范。
