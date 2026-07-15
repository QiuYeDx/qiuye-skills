---
name: geometric-mask-transition
description: >-
  Design, implement, debug, and validate geometric reveal transitions for UI
  state changes, route handoffs, loading exits, modals, media, and scene
  changes. Use for circular or elliptical apertures, directional and diagonal
  wipes, clip-path reveals, CSS mask-image transitions, SVG masks, View
  Transition API reveals, and canvas/WebGL mattes. Covers choosing the correct
  layer architecture, computing coverage from any origin, synchronizing DOM
  swaps, handling interruption and cleanup, reduced motion, browser fallbacks,
  performance, and frame-by-frame visual QA. Do not use for static scroll-edge
  fades or routine opacity/slide micro-interactions. Triggers on: "reveal
  transition", "geometric mask", "mask transition", "clip-path reveal",
  "radial wipe", "aperture reveal", "shape wipe", "loading reveal", "scene
  transition", "page reveal", "mask-image animation", "transition matte",
  "view transition reveal", "几何遮罩", "揭幕", "遮罩过渡", "图形过渡",
  "圆形揭幕", "渐变遮罩过渡", "页面转场遮罩".
---

# Geometric Mask Transition

把几何转场当作一次有明确起点、内容提交点和终点的视觉事务。先选对图层架构，再选 CSS、SVG 或 Canvas 技术；不要从一个顺眼的 `clip-path` 片段开始拼实现。

## 执行契约

1. 先检查项目现有的框架、动画库、路由、样式方案、浏览器范围和 reduced-motion 处理。沿用已有依赖和组件约定，不要为一个转场擅自安装新库。
2. 明确 source、target、转场作用域、几何原点、运动方向、内容提交时机、输入策略和中断策略。信息不全时，根据现有交互保守推断并记录假设。
3. 先选择图层架构，再选择技术原语。`clip-path`、CSS mask、覆盖层和 View Transition 不是可随意互换的写法。
4. 在实现前阅读 [references/technique-selection.md](references/technique-selection.md)。涉及代码时再阅读 [references/implementation-recipes.md](references/implementation-recipes.md)。完成前必须按 [references/validation.md](references/validation.md) 验收。
5. 让初始帧在浏览器首次绘制前成立，让完成帧在清理前稳定。把取消、重复触发、resize、卸载和异常路径都纳入同一生命周期。
6. 在真实浏览器中检查中间帧和最终帧。只通过类型检查、lint 或最终截图，不能证明转场正确。

## 先定义转场

编码前回答以下问题：

- **谁被揭示**：target 内容、source 内容，还是一个纯色/品牌色覆盖层？
- **形状内外分别显示什么**：圆内是 target、圆外是 source，还是反过来？
- **DOM 何时变化**：动画全程共存、完全遮住后交换，还是由浏览器快照 old/new 状态？
- **坐标属于谁**：viewport、容器 border box、触发器中心，还是媒体自身坐标？
- **结束后保留谁**：target 必须成为普通、可交互且未被 mask 的内容，临时层必须移除或隐藏。
- **重复触发怎么办**：忽略、排队、反向播放，还是取消旧事务后从当前可见状态继续？

若这些问题没有答案，不要先写动画参数。

## 选择正确架构

| 需求 | 首选架构 | 关键原因 |
|---|---|---|
| 路由/状态必须在不可见时安全交换 | 覆盖层 `cover -> commit -> uncover` | 不要求 source 与 target 同时存在，最稳健 |
| target 从某点以硬边界展开 | 对 target 使用 `clip-path` | 语义直接，几何简单，通常比逐像素 mask 便宜 |
| source 外圈保留、中心逐渐露出 target，或需要软边 | 对 source 使用 alpha mask 挖洞 | CSS mask 支持透明度过渡和反向孔洞 |
| 已有页面/路由适合浏览器快照 | View Transition API | 自动提供 old/new 快照，但必须处理默认 crossfade 与回退 |
| 复杂矢量形状、路径或多孔洞 | SVG `clipPath` / `mask` | 坐标和组合能力强，但必须显式控制 units 与 mask 类型 |
| 噪声、流体、粒子或视频 matte | Canvas/WebGL 覆盖层或媒体合成 | 仅在逐像素动态效果确有必要时使用 |

优先级通常是：变换覆盖层 > 简单 `clip-path` > CSS mask > SVG > Canvas/WebGL。这里的“优先”表示在满足视觉目标时选择故障面更小的方案，不表示后者效果更高级。

## 不得混淆的语义

- `clip-path` 裁剪它所在的元素：形状内可见，形状外不可见。把它放在 target 上，才是“target 从形状内出现”。
- CSS alpha mask 也作用于它所在的元素：透明像素隐藏，非透明像素显示。在 alpha 模式下黑白颜色都不重要，alpha 才重要。
- 给纯色 overlay 做“透明圆孔”，露出的是 overlay 背后的内容；它不能自动代表旧页面。若圆外必须显示真实 source，就对 source 层做反向 mask，或使用 old/new 快照。
- CSS gradient mask 与 SVG `<mask>` 的默认模式可能不同。需要透明度语义时显式使用 `mask-mode: alpha`；SVG 也显式设置 `mask-type="alpha"`。
- Canvas 覆盖在 DOM 上只能遮盖或露出 DOM，不能直接成为 DOM 的 CSS mask。需要像素级合成时必须复制/渲染视觉内容，并保留真实 DOM 负责语义和交互。

## 生命周期

### Reveal-only

用于 target 已挂载且只需被揭示的场景：

1. 以隐藏几何状态挂载 target，初始样式必须在首次绘制前生效。
2. 等待 target 达到可揭示状态；关键图片或布局未稳定时不要启动。
3. 从隐藏几何动画到完整覆盖几何。
4. 把 target 恢复成普通状态，例如移除 `clip-path`，再执行完成回调。

### Transactional handoff

用于路由或互斥状态：

1. `idle -> covering`：覆盖 source。
2. `covering -> covered`：确认 viewport/容器已被完全覆盖。
3. 在 `covered` 内提交 DOM 或路由变化，并等待 target 至少完成一次布局和绘制。
4. `covered -> revealing`：揭开覆盖层。
5. `revealing -> idle`：移除动画、监听器、临时样式和交互锁。

不要用固定延迟猜测 React、Vue 或路由何时提交完成。使用框架提供的 transition 集成、同步提交能力、layout effect、明确的 ready promise，或至少等待提交后的下一次绘制。

### Interruption

- 为每次事务创建唯一 token 或 `AbortController`。新事务开始时使旧事务失效。
- 在每个 `await` 之后检查事务是否仍为当前事务。
- 在 `finally` 中取消 WAAPI/Motion 控制器、RAF、timer、订阅和 observer，并恢复临时 style、`inert`、焦点策略与 overlay 状态。
- 明确取消后的可见状态。若内容已经提交，通常保留新内容并立即移除遮罩；不要回滚一半的异步导航。

## 几何与坐标

所有坐标必须在被裁剪元素自己的坐标系中计算。把 pointer 的 `clientX/clientY` 转为容器坐标时，减去 `getBoundingClientRect().left/top`，并根据需求 clamp 到边界。

从任意原点 `(x, y)` 覆盖宽高为 `(w, h)` 的矩形，正确半径是到四个角距离的最大值：

```ts
function radiusToCover(w: number, h: number, x: number, y: number) {
  return Math.max(
    Math.hypot(x, y),
    Math.hypot(w - x, y),
    Math.hypot(x, h - y),
    Math.hypot(w - x, h - y),
  );
}
```

仅当原点严格位于中心时，才可简化为 `Math.hypot(w, h) / 2`。不要用 viewport 尺寸计算容器 reveal，也不要假设 `100vmax` 总能覆盖偏移原点。为抗锯齿和取整预留约 `1-2px`，不要用几十像素掩盖错误坐标。

在容器 resize、设备旋转或 origin 移动时重新计算。若 resize 发生在动画中，更新终点或立即完成到新的安全终态，不要继续使用旧半径留下露角。

## 动画约束

- 只让一个系统拥有一个属性。不要让 CSS transition、Motion 和 WAAPI 同时控制同一 `transform`、`clip-path` 或 mask 变量。
- 优先动画 `transform` 和简单 `clip-path`。只有软边或逐像素形状确有必要时才动画 `mask-image`。
- 不要通过 React/Vue state 每帧重渲染整个子树。使用动画库的 motion value、WAAPI、CSS 注册属性或局部 RAF 写 style。
- 不要默认写 `will-change: mask-image`。它不保证合成加速，还可能增加内存或绘制开销。仅对实测有效的属性临时使用 `will-change`，完成后移除。
- 不要同时叠加 shape、百分比、进度环、文字扫光和粒子。保留一个主运动，其余只承担必要反馈。
- 对工作型产品保持短促克制；对品牌/媒体场景才使用更长的 hold、软边或复杂形状。hold 必须服务于感知，不得用来掩盖加载不确定性。

## 内容、交互与无障碍

- 把纯视觉层设为 `aria-hidden="true"`。装饰层通常使用 `pointer-events: none`，但不要把它误当作交互锁。
- 如果事务期间不能操作底层，显式禁用触发器或使用可恢复的 `inert`/状态守卫；结束和异常时都要恢复。
- source 与 target 共存时，只让当前有效层参与 tab 顺序和辅助技术。视觉裁剪不会自动隐藏语义节点。
- 路由提交后把焦点移动到符合产品既有约定的位置；不要让焦点留在已卸载的触发器上。
- 尊重 `prefers-reduced-motion`。reduced 模式应直接提交或使用很短的淡入淡出，不要只把复杂 reveal 加速播放。
- 真实进度才使用 `role="progressbar"` 和数值；装饰性 loading reveal 不得向辅助技术伪报进度。

## 层叠与作用域

- 为局部转场建立明确的定位容器和 stacking context，确认 `overflow` 与圆角是否应该裁剪转场。
- 全屏覆盖层优先 portal 到稳定的应用根节点或 `body`。被 transform/filter/perspective 的祖先可能改变 fixed 定位和层叠行为。
- 普通 z-index 无法盖住浏览器 top layer。若 dialog/popover 必须一起过渡，关闭或单独协调它们，不要继续抬高 z-index。
- 避免随意添加 `contain: paint`；它会裁剪阴影、溢出几何和部分定位内容。只在确认视觉边界后使用。

## 完成标准

- 初始帧无闪现，形状内外显示的是定义中的正确内容。
- 任意支持尺寸和 origin 都完整覆盖，无露角、接缝或一帧底色。
- target 未就绪时不会被揭开；完成后没有残留 mask、clip、overlay 或默认 View Transition crossfade。
- 快速重复触发、取消、resize、组件卸载和异常路径都落到确定状态。
- reduced-motion、键盘焦点、pointer、亮暗主题和浏览器回退均可用。
- 在至少一个中间帧做像素级视觉检查，并确认控制台、定时器、动画和临时 DOM 已清理。
