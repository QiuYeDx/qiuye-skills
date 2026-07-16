# Staggered Grid and Matrix Transitions

## 目录

- [先区分三种架构](#先区分三种架构)
- [建立等尺寸网格](#建立等尺寸网格)
- [用距离场生成波前](#用距离场生成波前)
- [架构 A：tile cover-swap-uncover](#架构-atile-cover-swap-uncover)
- [架构 B：target staggered grid reveal](#架构-btarget-staggered-grid-reveal)
- [架构 C：source staggered grid exit](#架构-csource-staggered-grid-exit)
- [首帧、取消与 resize](#首帧取消与-resize)
- [性能与无障碍](#性能与无障碍)
- [验收清单](#验收清单)

## 先区分三种架构

用户说“方块矩阵转场”“像素块涟漪”或“马赛克揭示”时，先问中间帧里方块显示什么。

### A. Tile cover

```text
最上层    independent tile cover matrix
最下层    source，完整遮挡帧后替换为 target
```

方块是纯色或装饰 cover。它们依次入场，全部覆盖后提交 target，再依次退场。这是 `cover-swap-uncover`，适合 source/target 不能共存或必须在不可见时提交的状态切换。

### B. Target tile reveal

```text
最上层    target，受 multi-tile clip/mask 约束
最下层    source，直到 reveal 完成
```

方块内部直接显示 target，方块外继续显示 source。这是 `reveal-only`、`staggered grid reveal` 或 `tile reveal`。target 必须提前 ready，完成后移除 clip/mask 并成为普通内容层。

不要用纯色 tile cover 模拟 target tile reveal；也不要为每个 tile 复制整棵 target DOM。前者中间帧语义不对，后者会放大 DOM、图片、焦点和辅助技术成本。

### C. Source tile exit

```text
最上层    source，受 multi-tile alpha mask 约束
最下层    ready target，直到 exit 完成
```

方块表示 source 的可见区域，并按波前从完整尺寸缩到 `0`。消失处直接露出 target。这是 `source-exit`、`outgoing-view mask-out` 或 `staggered tile exit`，不是把 target reveal 随意倒放。

| 需求 | 首选实现 |
|---|---|
| 纯色方块依次遮挡并在完整帧交换内容 | DOM/CSS tile cover，动画 `transform` |
| 单个 target 按大量互不相连的硬边 tile 显现 | SVG `clipPath` 或 alpha `mask` 作用于 target |
| 单个 source 按大量 tile 退出并露出下层 target | SVG alpha `mask` 作用于 source，rect 从完整缩到 `0` |
| tile 需要透明度、羽化或 alpha 组合 | SVG alpha mask，显式 `mask-type="alpha"` |
| 只有少量大块，项目已使用 snapshot | 命名 View Transition 或少量 clipped target layers |
| 噪声/像素溶解而非规则网格 | Canvas/WebGL matte；真实 DOM 保留语义和最终交互 |

## 建立等尺寸网格

若所有 tile 必须保持正方形，容器尺寸通常不能被 cell size 整除。让矩阵略微超出容器并由 stage 裁剪，比拉伸最后一行/列更稳定。

```ts
type Point = { x: number; y: number };

type GridCell = {
  row: number;
  column: number;
  x: number;
  y: number;
  centerX: number;
  centerY: number;
};

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

export function buildSquareGrid(
  width: number,
  height: number,
  origin: Point,
  minCell = 42,
  maxCell = 68,
) {
  const ideal = Math.min(width / 11, height / 7);
  const cellSize = Math.round(clamp(ideal, minCell, maxCell));
  const columns = Math.ceil(width / cellSize);
  const rows = Math.ceil(height / cellSize);
  const matrixWidth = columns * cellSize;
  const matrixHeight = rows * cellSize;
  const offsetX = (width - matrixWidth) / 2;
  const offsetY = (height - matrixHeight) / 2;
  const originColumn = clamp(
    Math.floor((origin.x - offsetX) / cellSize),
    0,
    columns - 1,
  );
  const originRow = clamp(
    Math.floor((origin.y - offsetY) / cellSize),
    0,
    rows - 1,
  );
  const maxDistance = Math.max(
    originColumn + originRow,
    columns - 1 - originColumn + originRow,
    originColumn + rows - 1 - originRow,
    columns - 1 - originColumn + rows - 1 - originRow,
    1,
  );
  const cells: GridCell[] = [];

  for (let row = 0; row < rows; row += 1) {
    for (let column = 0; column < columns; column += 1) {
      const x = offsetX + column * cellSize;
      const y = offsetY + row * cellSize;
      cells.push({
        row,
        column,
        x,
        y,
        centerX: x + cellSize / 2,
        centerY: y + cellSize / 2,
      });
    }
  }

  return {
    cellSize,
    columns,
    rows,
    matrixWidth,
    matrixHeight,
    offsetX,
    offsetY,
    originColumn,
    originRow,
    maxDistance,
    cells,
  };
}
```

注意：

- 用被遮罩元素自己的 border-box 坐标，不要用 viewport 尺寸生成局部网格。
- 矩阵完整尺寸必须 `>=` 容器尺寸；offset 可以为负数。
- stage 需要稳定尺寸和明确 `overflow`。圆角容器通常应裁剪矩阵。
- 完整帧给 tile 约 `0.5-1px` overlap，或把最终 scale 设为约 `1.01-1.03`，并在高 DPR 下检查内部交点。

## 用距离场生成波前

常用顺序：

| 目标感觉 | 距离/顺序 |
|---|---|
| 左上到右下的对角波前 | `row + column`，等价于左上 origin 的 Manhattan distance |
| 从任意 origin 向外扩散的菱形 | Manhattan：`abs(dx) + abs(dy)` |
| 近似圆形涟漪 | Euclidean：`hypot(dx, dy)` |
| 方形同心环 | Chebyshev：`max(abs(dx), abs(dy))` |
| 严格逐格扫描 | `row * columns + column` |

把距离归一化成 `delay`，再从一个全局 progress 推导每个 tile 的 local progress：

```ts
function tileDelay(
  row: number,
  column: number,
  originRow: number,
  originColumn: number,
  maxDistance: number,
) {
  const distance =
    Math.abs(column - originColumn) + Math.abs(row - originRow);
  return maxDistance === 0 ? 0 : distance / maxDistance;
}

function localProgress(progress: number, delay: number, spread = 0.58) {
  return clamp(
    (progress - delay * spread) / (1 - spread),
    0,
    1,
  );
}
```

`spread` 控制启动时间分散程度。用一个 RAF、WAAPI timeline 或 Motion value 更新所有 tile；不要创建 N 个 timer。缓动作用于 local progress，delay 通常保持线性，才能维持可预测的波前速度。

## 架构 A：tile cover-swap-uncover

1. 生成独立 cover matrix，所有 tile 以 `scale(0)` 或离场 transform 同步建立首帧。
2. 用距离 delay 让 tile 依次进入；source 始终保留在下层。
3. 在所有 tile 都达到无缝完整态后提交 target。
4. 等待 target 至少完成一次 paint；关键图片/字体需要显式 ready。
5. 让 tile 按产品定义的顺序退场，最后移除整个 matrix。

进入和退出不必使用相反顺序：

- 同一 origin 入场和退场：target 从同一波前后方出现。
- 进入顺序的 reverse：形成闭合后再从远端打开的方向感。
- 不同 origin：适合 forward/back，但要明确导航语义。

中断策略：

- 提交前取消：移除 matrix，保留 source。
- 提交后取消：保留 target，立即移除 matrix。
- resize：最稳健做法是同步落到完整 source 或完整 target；不要继续使用旧 rows/columns。

## 架构 B：target staggered grid reveal

大量 tile 直接显示 target 时，用单个 target + SVG multi-rect mask/clip。不要创建几十到几百份 target subtree。

首帧顺序：

1. 创建唯一 mask id，并写明 `maskUnits="userSpaceOnUse"`、`maskContentUnits="userSpaceOnUse"` 和 `mask-type="alpha"`。
2. 创建所有 `<rect>`，在 defs 中先写入 `scale(0)` transform。
3. 把 defs 挂到稳定 stage，并把标准和 `-webkit-` mask 引用绑定到尚未插入 DOM 的 target。
4. 在隐藏几何已经成立后，把 target 放到 source 上方，再检查 computed mask；实际为 `none` 时立即走隐藏态 fallback。
5. 用单一 timeline 更新 rect transform；完成后先移除 target 的 mask，再移除 SVG defs。

```ts
const svgNS = "http://www.w3.org/2000/svg";

function setRectScale(
  rect: SVGRectElement,
  center: Point,
  scale: number,
  angle = 0,
) {
  rect.setAttribute(
    "transform",
    `translate(${center.x} ${center.y}) ` +
      `rotate(${angle}) scale(${scale}) ` +
      `translate(${-center.x} ${-center.y})`,
  );
}
```

约束：

- mask 的像素坐标属于 target；target/stage border 差异必须计入覆盖余量。
- alpha mask 里透明背景隐藏 target，非透明 rect 显示 target。颜色黑白不重要，alpha 才重要。
- SVG id 必须按组件实例/事务唯一，避免多个 demo 或 Strict Mode 实例冲突。
- 完成后清除 `mask`、`mask-image`、`-webkit-mask`、`-webkit-mask-image`、repeat/mode 属性与 defs。
- `CSS.supports()` 只证明语法可接受。必要时检查 target 的 computed mask；实际仍为 `none` 时回退到简单 target opacity/clip reveal。
- 若只需硬边且目标浏览器可靠支持 inline SVG fragment，`clipPath` 也可表达 rect union；需要 alpha、羽化或透明度时使用 mask。

## 架构 C：source staggered grid exit

复用架构 B 的等尺寸网格、唯一 SVG id 和 rect transform，但把 mask 作用到上层 source，并反转每个 rect 的局部可见尺度：

```ts
function rectScale(local: number, entering: boolean, overlap = 1.02) {
  const eased = 1 - Math.pow(1 - clamp(local, 0, 1), 5);
  return (entering ? eased : 1 - eased) * overlap;
}
```

source-exit 的执行顺序：

1. 等待 target ready，以 `aria-hidden`/`inert` 状态挂载到 source 下方。
2. 创建唯一 SVG mask，所有 rect 在首次绘制前设为略微 overscale 的完整尺寸，并把 mask 绑定到 source。
3. 使用与 reveal 相同的距离 delay，让 rect 从完整尺寸依次缩到 `0`；不需要反转 cell 数组。
4. 完成时提升 target、恢复其语义与交互，并移除 source、mask inline style 和 defs。
5. 提交前取消时清除 source 的 mask/临时层级/opacity，移除 target 和 defs，继续保留 source。

source 是已有的 current layer，不要给它复用“删除本事务节点”的 data attribute。只标记临时 target 和 defs；source 上只挂可恢复 class/style，避免通用 cleanup 把当前页面一起删除。

清理 source 时至少移除 `mask`、`mask-image`、`-webkit-mask`、`-webkit-mask-image`、repeat/mode 属性、临时 opacity、z-index class 和 defs。`CSS.supports()` 之外再检查 computed mask；失败时让上层 source 做 `opacity: 1 -> 0` 或直接提交 target，取消时恢复 source opacity。不要回退成层级语义相反的 target entrance。

## 首帧、取消与 resize

| 情况 | Cover matrix | Target grid reveal | Source grid exit |
|---|---|---|---|
| 首帧 | 所有 cover tile 隐藏，source 可见 | target 已绑定全透明/零面积 mask，source 可见 | source mask rect 全尺寸，target 在下层 |
| 完成帧 | matrix 完整覆盖后才提交 | 所有 mask rect 完整覆盖 target | 所有 source mask rect 为 `0`，target 完整可见 |
| 提交前取消 | 保留 source | 移除 masked target，保留 source | 恢复 source，移除 target/defs |
| 提交后取消 | 保留 target，移除 matrix | 通常已完成；保留 target 并清除 mask | 保留 target，清除 source effect/defs |
| resize | 完成到确定状态或重建 matrix | 完成 target 或按当前 progress 重建 mask | 完成 target 或按当前 progress 重建 source mask |
| reduced motion | 直接 commit | 直接显示 target 并清除 mask/defs | 直接提交 target 并清除 source effect/defs |

每个 `await` 后检查事务 ownership。旧事务的 `finally` 只能删除带自身 token/id 的 tile、target 和 defs。

## 性能与无障碍

- 规则 cover 优先用 DOM/CSS transform；它通常比大面积 SVG/gradient mask 更容易合成。
- SVG mask 会更新大量 rect 并对 masked target/source 做逐像素合成。限制 cell 数量，并在真实移动设备/Safari 检查 paint 和帧率。
- 不要默认给几百个 tile 加 `will-change` 或 `translateZ(0)`；这可能制造过多图层和纹理内存。
- 纯视觉 tile matrix/defs 使用 `aria-hidden="true"` 和 `pointer-events: none`。
- reveal/exit 期间 target 使用 `inert`/`aria-hidden`，source 保持语义当前；完成后原子切换。
- CSS/SVG mask 不自动改变辅助技术可见性，也不能代替业务输入锁。

## 验收清单

- 在 `0% / 25% / 50% / 75% / 100%` 固定 progress，确认 target reveal 的可见 tile 单调增加，source exit 的可见 tile 单调减少且 `100%` 全部为 `0`。
- 在中心、四角和边界 origin 检查 Manhattan/Euclidean/Chebyshev 结果是否符合设计。
- 在窄手机、常规 desktop、宽且矮 viewport 检查 rows/columns、等尺寸 tile 和 edge clipping。
- 在完整 cover/reveal 帧取样四角、四边和多个内部交点；高 DPR 下无发丝缝或底色。
- 快速切换两个 target，分别在最早 tile、半完成、完整 cover/完整 reveal 后制造取消。
- source-exit 在最早 tile 与半完成帧取消时必须完整恢复 source；完成/resize 路径必须只保留 target。
- 动画中 resize/orientation change 后只停在完整 source 或 target，没有旧矩阵露角。
- 完成和取消后没有残留 tile、masked target/source、SVG defs、mask/opacity inline style、RAF 或 running animation。
- 检查 DOM 数量不会随重复触发增长，SVG mask id 在同页所有实例中唯一。
- 模拟 reduced motion 和 mask/clip feature fallback，确认业务提交和焦点策略仍执行。
