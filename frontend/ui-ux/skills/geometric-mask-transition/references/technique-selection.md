# Technique Selection and Correct Semantics

## 目录

- [先选图层关系](#先选图层关系)
- [打开、关闭与导航方向](#打开关闭与导航方向)
- [A. Transform 覆盖层](#a-transform-覆盖层)
- [B. 对 target 使用 clip-path](#b-对-target-使用-clip-path)
- [C. 对 source 使用 CSS alpha mask](#c-对-source-使用-css-alpha-mask)
- [D. View Transition API](#d-view-transition-api)
- [E. SVG clipPath 与 mask](#e-svg-clippath-与-mask)
- [F. Canvas 和 WebGL matte](#f-canvas-和-webgl-matte)
- [G. Staggered grid / matrix transition](#g-staggered-grid--matrix-transition)
- [浏览器能力与回退](#浏览器能力与回退)
- [性能判断](#性能判断)

## 先选图层关系

先画出中间帧，而不是只画首尾帧。最少标明：

```text
最上层    transition decoration / cover（可选）
中间层    target 或 source（被 clip/mask 的那一层）
最下层    source 或 target（稳定底层）
```

按目标选择关系：

| 中间帧目标 | 被动画的层 | 技术 |
|---|---|---|
| 圆内 target、圆外 source | 上层 target | `clip-path: circle(...)` 从小到大 |
| 圆内 target、圆外 source，边缘需羽化 | 上层 source | alpha mask 在 source 中挖透明孔，target 放下层 |
| 先被品牌色完全遮住，再显示新页面 | 独立 cover | `transform`/`clip-path` cover-swap-uncover |
| 纯色 tile 依次覆盖，完整后交换内容 | 独立 tile matrix | DOM/CSS transform cover-swap-uncover |
| target 按互不相连的 tile 直接显现 | 上层 target | 单 target + SVG multi-rect clip/mask |
| source 按互不相连的 tile 依次退出 | 上层 source | 下层 target + source SVG multi-rect alpha mask |
| 浏览器保存真实 old/new 页面快照 | `::view-transition-old/new(...)` | View Transition API |

不要把纯色 cover 误写成 source。纯色 cover 的孔洞只能露出背后内容，孔洞外不会继续显示旧页面细节。

## 打开、关闭与导航方向

不要把所有退出动画都实现成进入动画的数组反转。先重新确认退出时谁在上层：

- modal/detail 打开时，可让上层 target 的 `clip-path` 从 `0 -> coverRadius`；关闭时只有在 source 仍稳定挂载于下层时，才把同一个 target 从 `coverRadius -> 0`，完成后再卸载 target。
- cover-swap-uncover 的 forward/back 都在完整 cover 帧提交内容。根据导航语义交换 cover 的进入边与退出边，不要在半覆盖状态提交。
- View Transition forward reveal 通常裁剪 `::view-transition-new(root)` 从小到大。back/close 若要让当前页面收缩离场，应把 `::view-transition-old(root)` 放在 new 上面并从完整形状缩到 `0`；不要让 new 先完整闪现再缩回 old。
- 方向性 wipe 使用产品的逻辑方向。RTL 下“forward”不一定是视觉上的 left-to-right；读取 `dir` 或复用项目的方向工具。
- 中断后的反向播放只在几何、DOM 和业务状态都仍可逆时使用。路由/数据已经提交后，优先完成到确定终态，再启动新的事务。

## A. Transform 覆盖层

把独立覆盖层从一侧扩展到全屏，在完全覆盖时提交内容，再从另一侧收起。优先用于路由、主题大切换、互斥视图和无法同时挂载 source/target 的场景。

```css
.transition-cover {
  position: fixed;
  inset: 0;
  z-index: var(--transition-z, 100);
  background: var(--transition-color, var(--background));
  transform: scaleX(0);
  transform-origin: left center;
}
```

执行顺序：

1. 在同一任务中显示 cover 并启动 `scaleX(0) -> scaleX(1)`。
2. 动画完成后，把 `scaleX(1)` 固化为 inline/computed 状态并取消旧 animation，避免两个 fill animation 竞争。
3. 提交 target，等待其布局和绘制准备完成。
4. 在 cover 仍为完整尺寸时切换 `transform-origin`，再执行 `scaleX(1) -> scaleX(0)`。
5. 隐藏 cover，清空 transform、origin 和 animation。

优点：只动画 transform，性能和兼容性最可控。缺点：中间会完全看不到内容，不适合必须持续看到 source 细节的 aperture。

制作斜向 wipe 时，优先让一个超出 viewport 的矩形 cover 做 rotate/skew + translate/scale。必须根据旋转后包围盒验证所有角，不要只加一个拍脑袋的负 inset。

## B. 对 target 使用 clip-path

把 target 放在 source 上面，并直接裁剪 target：

```css
.reveal-stage {
  position: relative;
  isolation: isolate;
  overflow: hidden;
  overflow: clip;
}

.reveal-source,
.reveal-target {
  position: absolute;
  inset: 0;
}

.reveal-target {
  clip-path: circle(var(--reveal-r) at var(--reveal-x) var(--reveal-y));
}
```

给 stage 设置稳定尺寸。若 source 和 target 都绝对定位，它们不会撑开 stage；也可以让稳定的 source 保持普通流布局，只把 target 绝对定位。

这会得到“圆内 target、圆外 source”的硬边 reveal。target 的圆外区域通常不参与命中测试，但它的 DOM 仍存在；必须另外处理 tab 顺序、`aria-hidden` 或 `inert`。

适用限制：

- `circle()`、`ellipse()`、`inset()` 和低点数 polygon 适合 CSS `clip-path`。
- `clip-path` 没有羽化。需要软边时改用 alpha mask，不要叠 blur 伪造边缘；blur 会扩大绘制区域并污染内容。
- polygon 的点数和顺序必须在关键帧间一致，否则插值可能离散跳变。
- 圆形终点必须用实际容器和 origin 算到四角最大距离。
- 完成后设置 `clip-path: none`，避免长期创建裁剪、层叠或命中边界。

## C. 对 source 使用 CSS alpha mask

当 target 在下层且需要“中心 target + 外圈 source + 软边”时，把反向 radial mask 放在 source 上：

```css
.reveal-source {
  --reveal-r: 0px;
  --reveal-feather: 2px;
  -webkit-mask-image: radial-gradient(
    circle at var(--reveal-x) var(--reveal-y),
    transparent 0 var(--reveal-r),
    #000 calc(var(--reveal-r) + var(--reveal-feather))
  );
  mask-image: radial-gradient(
    circle at var(--reveal-x) var(--reveal-y),
    transparent 0 var(--reveal-r),
    #000 calc(var(--reveal-r) + var(--reveal-feather))
  );
  mask-mode: alpha;
}
```

在 alpha mask 中：

- `transparent` 的 alpha 为 0，隐藏 source，于是露出下层 target。
- `#000` 的 alpha 为 1，保留 source。换成白色在 alpha 模式下视觉结果相同。
- feather 是透明到不透明的插值区。硬边用 `0-1px`，软边按设计调整，但要检查低端设备 repaint。

显式写标准属性和 `-webkit-` 前缀。不要依赖 `mask-mode` 去改变一张 SVG mask 的历史默认值；在 SVG `<mask>` 本身也显式写 `mask-type="alpha"`。

不要假设浏览器能高效插值整个 gradient 字符串。可选择：

- 使用 Motion value 或局部 RAF 每帧只写 `--reveal-r`。
- 用 `@property --reveal-r { syntax: "<length>"; ... }` 注册后交给 CSS transition/animation，并为不支持注册属性的浏览器提供无动画回退。
- 对简单硬边直接改用 `clip-path`。

完成后移除 source，或清除它的 mask。不要让已不可见的 source 继续占据交互和合成资源。

这类“上层 source 自身消失、逐渐露出下层 target”的结构属于 `source-exit` / `outgoing-view mask-out`。target 必须先 ready；提交前取消时恢复 source，完成时移除 source 并提升 target。若复杂 mask 不可用，优先让 source 淡出或直接提交，保持 source-over-target 语义，不要偷偷换成 incoming target reveal。

## D. View Transition API

使用浏览器快照 source/target，适合 document 内状态切换、框架已提供集成的 route transition，或显式启用的 same-origin cross-document transition。

基本流程：

```ts
if (!document.startViewTransition) {
  await updateDOM();
  return;
}

const transition = document.startViewTransition(updateDOM);
await transition.ready;
// 此时 ::view-transition-old(root) / new(root) 已可动画。
await transition.finished;
```

必须处理默认动画。浏览器默认会给 old/new root 快照做 crossfade；若再叠一个 clip reveal，常见结果是 source 提前变淡或 target 透出：

```css
::view-transition-old(root),
::view-transition-new(root) {
  animation: none;
  mix-blend-mode: normal;
}

::view-transition-group(root) {
  animation: none;
}

::view-transition-image-pair(root) {
  isolation: auto;
}

::view-transition-old(root) {
  z-index: 1;
}

::view-transition-new(root) {
  z-index: 2;
  clip-path: circle(0 at var(--vt-x) var(--vt-y));
  animation: vt-reveal var(--vt-duration, 520ms) cubic-bezier(.22, 1, .36, 1)
    both;
}

@keyframes vt-reveal {
  to {
    clip-path: circle(var(--vt-radius) at var(--vt-x) var(--vt-y));
  }
}
```

注意：

- 在启动 transition 前，把 viewport 坐标和覆盖半径写入 root CSS variables。
- `updateDOM` 必须在 promise resolve 前真正提交目标 DOM。不要假设 `await router.navigate()` 等价于“目标已绘制”；使用框架官方集成或同步提交机制。
- `transition.ready` 可能在 update callback 失败或 transition 被跳过时 reject。`finished` 用于最终清理 CSS variables 和状态。
- 新 transition 可能跳过正在运行的旧 transition。若业务不允许并发，仍要在调用层串行化；`skipTransition()` 只跳过动画，不会跳过 update callback。
- reduced-motion 或能力不支持时直接更新 DOM。不要为了强行动画引入屏幕截图方案。
- 命名 view transition 元素时保证活动文档内 `view-transition-name` 唯一；重复名称会让 transition 跳过。
- 跨文档 transition 还需要浏览器支持和 `@view-transition { navigation: auto; }` 等导航配置。不要把同文档示例直接宣称为所有路由通用。

## E. SVG clipPath 与 mask

在以下条件下选择 SVG：

- 需要复杂 path、多个孔洞、非规则矢量边缘或可复用形状。
- 需要 `objectBoundingBox` 或 `userSpaceOnUse` 的明确坐标控制。
- 路径 morph 的起终点可以使用兼容的命令结构和点数。

约束：

- 为每个组件实例生成唯一 id，避免多个 SVG defs 冲突。
- 明确 `clipPathUnits`、`maskUnits` 和 `maskContentUnits`。不要把 `0..1` 的 objectBoundingBox 坐标与像素坐标混用。
- 对透明度 mask 写 `mask-type="alpha"`。若确实使用 luminance mask，再根据亮度语义设计黑白值。
- 引用外部 SVG/CSS mask 时确认同源和 CORS；失败时 mask 可能把元素完全隐藏。
- path morph 前验证命令类型、顺序和数量一致。否则改为 transform、crossfade 两个形状，或使用已存在的 morph 工具。

## F. Canvas 和 WebGL matte

仅在 CSS/SVG 无法表达逐像素变化时选择：噪声溶解、流体、粒子聚合、视频 matte、大量独立图形。

先决定 Canvas 的职责：

1. **视觉 cover**：Canvas 位于 DOM 上方，画不透明像素遮住内容，清除像素露出 DOM。实现简单，但它不是 DOM mask。
2. **像素合成器**：把 source/target 纹理送入 shader 或 2D compositing。只能用于可合法绘制的图片/视频/canvas；跨源媒体会 taint canvas，DOM 也不能被无损自动捕获。
3. **媒体内部 mask**：只裁剪 Canvas/WebGL 场景，不影响外部 DOM。

始终让真实 DOM 负责语义、焦点和最终交互。处理 devicePixelRatio、resize、context loss、暂停后台渲染和卸载资源。若只需要一个圆或线性 wipe，退回 CSS。

## G. Staggered grid / matrix transition

先确认 tile 是独立 cover，还是 target 的可见区域：

- **Tile cover**：tile 内是纯色/装饰层。全部 tile 完整覆盖后提交 target，再让 tile 退场。这是 transactional `cover-swap-uncover`。
- **Target tile reveal**：tile 内直接显示 target，tile 外保留 source。把 multi-rect SVG clip/mask 作用于单个 target，这是 `reveal-only`。
- **Source tile exit**：上层 source 被切片后依次消失，target 在下层。这是 outgoing/source exit，不要误称 target entrance。

大量 tile 共享一个全局 progress，并根据 index 或距离场生成 delay。不要为每个 tile 创建 timer，也不要复制几十到几百份 source/target subtree。

涉及方块矩阵、mosaic、wavefront 或 distance-based stagger 时，阅读 [staggered-grid-transitions.md](staggered-grid-transitions.md) 获取等尺寸网格、波前公式、SVG mask 与生命周期实现。

## 浏览器能力与回退

使用 feature detection，不使用 UA sniff：

```ts
const supportsClipCircle = CSS.supports(
  "clip-path",
  "circle(1px at 0px 0px)",
);

const supportsMask =
  CSS.supports("mask-image", "linear-gradient(#000, #000)") ||
  CSS.supports("-webkit-mask-image", "linear-gradient(#000, #000)");

const supportsViewTransition = "startViewTransition" in document;
```

回退顺序：

1. 保证内容提交和交互正确。
2. 使用与原架构同层级语义的简短 opacity/transform transition，例如 source-exit 回退为上层 source 淡出。
3. 最后才是立即切换。

不要用 polyfill 模拟完整 View Transition snapshot，除非项目已经采用且用户明确要求。

## 性能判断

- Transform cover 通常故障面最小，但超大旋转/缩放图层仍可能占用大量纹理内存。
- 简单 `clip-path` 经常表现良好，但是否合成取决于浏览器、形状和内容；不要承诺“必定 GPU 加速”。
- Gradient/SVG mask 通常需要逐像素合成或 repaint。软边越宽、面积越大、下层内容越复杂，代价越高。
- 大量 DOM tile transform 与 SVG multi-rect mask 的成本模型不同。前者可能制造过多图层，后者可能触发大面积逐像素合成；按实际架构和目标设备测量。
- `filter`、`backdrop-filter`、mix-blend-mode 与 mask 叠加时尤其需要真机检查。
- 用浏览器 Performance/Layers 工具验证长任务、paint 和内存。只在测量证明有益时加临时 `will-change`。
