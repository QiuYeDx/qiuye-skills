# Case 9：连续布局过渡（Flow-aware content transitions）

## 目标与约定名称

**内容淡入淡出，真实占位逐渐展开和收回，周围元素连续让位，外框跟随内容。**

「连续布局过渡」是本 Skill 的可检索约定名，不是 Motion API 或行业标准术语。用户说「这里按 Case 9 做连续布局过渡」时，应按下方效果契约实现和验证，不能只给最外层弹窗加尺寸动画就交付。

| 层次 | 需要保证的结果 | 常用负责人 |
|---|---|---|
| 主动变化的内容 | 不首帧闪现、不末帧突消，保留完整进入与退出 | opacity；语义内容替换时 Presence |
| 局部占位 | 真实 height 连续变化，裁剪与条件间距一起收回 | 变化来源附近的尺寸层 |
| 被动受影响的内容 | 文档流中的相邻项连续移动，文字不被缩放 | 自然布局；离散重排按需 layout |
| 弹窗 / 卡片外框 | 跟随最终内容，不追着内层再缓动一次 | 外框尺寸层与嵌套协调 |

常见表述：「展开内容不要突然挤开下面」「弹窗已经变高但里面还闪」「折叠淡出且收回空隙」「所有元素有始有终地移动」「flow-aware content transitions」。适用折叠设置、条件字段、异步提示、不同高度的步骤、带下方操作区的列表。

**最短调用：**

```text
按 motion-recipes Case 9 做连续布局过渡：内容淡入淡出、真实占位伸缩、
相邻元素连续让位；保留退出与草稿，验证快速反向及嵌套变化。
```

## 先选择最小方案

本 case 把效果与动画归属组合起来，不要求每次把所有 case 拼一遍。

| 实际需求 | 选择 |
|---|---|
| 单层静态折叠，尺寸只在开合时变化 | 局部 `height: 0 ↔ auto` + opacity 已满足契约时即可，不强制 Observer |
| 自然高度会因校验、异步内容、换行继续变化 | 下方 `FlowRegion` 或 [Case 5](measured-auto-height-content.md) 的自然内层测量 |
| 空 → 提示 → 空；预览 / 错误 / 步骤互换 | `FlowSwap`：Presence 管生命周期，局部尺寸层管占位；概念见 [Case 2](animate-presence-auto-height-popover.md) |
| 有草稿的页签、折叠表单 | 保留面板子树或提升草稿状态；不要靠更换 key 重建表单 |
| 列表增删、排序、跨行重排 | [Case 6](list-presence-layout-reorder.md)；列表后还有按钮时额外验证列表总占位 |
| 普通 `layout` 已满足内容、位置与文字质量要求 | 沿用现有方案，无需引入整套测量模板 |
| 鼠标视差、共享元素迁移、容器变形 | 读对应 Case 3 / 7 / 8，不因“平滑”一词套此方案 |

先读本文件；只有遇到表中具体分支，再读被引用的 case。外层的 `width` / `height` 动画不会自动修复内层文档流跳动。

## 核心结构：在变化发生的地方改变占位

```text
稳定父容器（可为弹窗）
├─ 标题 / 触发器
├─ 局部尺寸层：motion.div，真实 height，overflow: hidden
│  └─ 自然内容层：ref + ResizeObserver，opacity，条件 padding
│     └─ 保留的表单 / Presence 内容阶段
└─ 后续操作区：随真实占位移动
```

1. Observer 读取自然内层，Motion 动画外层；不要测量正在被限高的同一个节点。
2. 外层避免 padding、border、固定 height/max-height 与 CSS 高度 transition。将这些空间纳入自然内层或单独的视觉包裹。
3. 自然内层保持正常排版，不能用 `height: 100%` 反过来依赖动画外层。`flow-root` 可阻止子元素 margin 逸出测量边界。
4. 内容透明度与高度分层控制，不缩放文本。普通文档流兄弟无需逐个加 `layout`；真实高度已经逐帧推动它们。
5. 单个连续占位变化只有一个补间负责人。`layout` 仍适用于离散重排，不能用禁用所有 layout 来修复协调问题。

### 初次显示与后续出现必须区分

- `null` 表示还没测量，`0` 是有效高度。
- 弹窗首次打开已经有内容：默认 `initial={false}`，首轮自然高度可为 `auto`，避免先塌陷再长开。
- 已显示界面中新插入内容：从 `height: 0` 开始，必须看得到首态。
- `ResizeObserver` 读实际自然尺寸；除非确有性能证据，不再叠加一层 requestAnimationFrame 延迟。防止自激测量与每帧无变化的 setState。

## 可复用模板与最小接入

完整独立模板：[assets/flow-transition.tsx](../assets/flow-transition.tsx)。依赖 React 19+ 与 `motion/react`，不依赖项目工具函数或 Tailwind；复制到项目的共享组件目录后按实际导入路径使用。Next.js Client Component 入口需要 `"use client"`。React 18 项目需适配 `inert` 的类型和写入方式，不能直接声称兼容。

| 导出 | 责任 / 关键参数 |
|---|---|
| `FlowRegion` | `open` 控制真实高度；`fade` 同时淡入淡出；`enterFromZero` 区分后插入与初始内容；`innerClassName` 放内部 padding |
| `FlowSwap` | `transitionKey` 为语义阶段；空内容完整退场后卸载；`stageClassName` 放随阶段消失的间距 |
| `useNaturalHeight` / `hasMovingFlow` | 自然测量与活动后代检测，供已有尺寸外框接入 |
| `useReducedMotionPreference` | 响应运行时系统偏好变更的 SSR 安全 hook |
| `flowSizeTransition` / `flowContentTransition` | 默认尺寸约 0.3s、无回弹；进入淡入约 0.18s，退出约 0.16s |

### 折叠区域：保留子树与草稿

```tsx
"use client";

import { useId, useState } from "react";
import { FlowRegion } from "./flow-transition";

export function AdvancedSettings() {
  const [open, setOpen] = useState(false);
  const id = useId();
  return (
    <section>
      <button type="button" aria-expanded={open} aria-controls={id}
        onClick={() => setOpen(value => !value)}>高级选项</button>
      <div id={id}>
        <FlowRegion open={open} fade>
          <div style={{ paddingTop: 12 }}>
            <label>备注 <input defaultValue="草稿保留" /></label>
          </div>
        </FlowRegion>
      </div>
      <div style={{ paddingTop: 16 }}><button type="button">保存</button></div>
    </section>
  );
}
```

需要首次展开才加载的重内容，可维护 `hasOpened`，首次打开后保留子树直到所属页面 / 弹窗销毁。不要写 `{open && <Form />}`：它会在关闭的第一帧删除视觉内容和局部状态，外层动画无从弥补。

### 条件提示与语义阶段：退出与占位一起结束

```tsx
// 稳定分组没有 gap；条件间距放到 Presence 阶段里面。
<div>
  <RequiredFields />
  <FlowSwap transitionKey={error ? "error" : "empty"}>
    {error ? <div style={{ paddingTop: 12 }}><p role="alert">{error}</p></div> : null}
  </FlowSwap>
</div>
```

- key 表示 `preview/error/step-2` 等语义状态，不使用输入文本、字符数或每次 render 生成的随机值。
- 空字符串也应视作没有内容。模板会等 **Presence 退出完成和占位高度收回都完成** 后移除 wrapper；只等较短的淡出会在高度尚未归零时跳走最后一段空间。
- `popLayout` 的退出节点立即脱离文档流，仍需要局部高度层或相关兄弟的布局动画接管空间变化。直接子组件必须把 ref 传给真实 DOM；模板已处理。
- 已被现有固定高度 / `h-full` 外框约束的整个内容阶段可用 `animateHeight={false}`，只保留 Presence；避免自然内层和外层高度循环依赖。
- 草稿页签不应直接采用会卸载页面的 keyed swap。可以常驻已访问面板：活动面板参与流，退出面板临时绝对定位淡出，完成后隐藏并禁用交互。

### 列表之后还有按钮：位置重排与总占位分别处理

Case 6 的 `popLayout` + `layout="position"` 接管标签之间的离散重排；自然测量层接管列表总高度，让列表外的按钮随真实占位移动。同一行删标签但没有缩行时，按钮保持不动才是正确结果。

```tsx
const { ref, height } = useNaturalHeight();
const reduce = useReducedMotionPreference();
const target = height ?? "auto";

// 结构示意：items 使用稳定业务 id；退出项的 inert / focus 由 ItemStage 处理。
<motion.div initial={false}
  animate={{ height: reduce ? [target, target] : target }}
  transition={reduce ? { duration: 0 } : flowSizeTransition}
  style={{ overflow: "visible" }}>
  <div ref={ref} className="relative flex flex-wrap gap-2">
    <AnimatePresence mode="popLayout" initial={false}>
      {items.map(item => <ItemStage key={item.id} item={item} />)}
    </AnimatePresence>
  </div>
</motion.div>
```

`ItemStage` 是转发真实 DOM ref 的 `motion.div`，用 `layout="position"` 补位、opacity 退出；按 Case 6 实现。这里不直接使用固定裁剪的 `FlowRegion`：缩行时旧行标签仍可能在原位置退场，`overflow: hidden` 会提前裁掉它。需要裁剪的弹窗祖先也应检查，必要时把退场视觉放到合适的覆盖层。不要为这个普通需求默认启用旧坐标快照。

## 间距也是动画的一部分

`height: 0` 不保证零占位。父级 gap、`space-y`、相邻 margin 和 `:last-child` 规则可能在 wrapper 最终卸载时突然切换。

推荐稳定分组，将“仅在条件内容存在时需要的间距”放进可变区域自然内层的 padding。折叠标题与内容间距也放内层。关闭后 wrapper 若继续保留，确认它不会额外计入父级 gap；若需要卸载，确认移除前后相邻元素位置连续。

不要为所有调用点统一加负 margin 猜测补偿。分别检查水平 / 垂直布局、末项删除、多块同时退出和空列表。

## 嵌套与外框：避免重复缓动

局部真实高度每帧变化时，祖先的 Observer 会收到一串已经插值后的值。祖先每帧再启动 spring 会产生追赶、拖尾，甚至短暂裁切。

模板用局部 `data-flow-animating` 标记识别仍在文档流中的变化来源：

1. **稳定展开的祖先**发现后代正在改变占位：直接跟随测量值（尺寸 transition duration 为 0），不再叠加弹簧。
2. **祖先自己收到开合 / 反向操作**：本地操作优先，保留祖先自己的过渡，不能因后代在动而跳到 0。
3. 排除 `data-flow-exiting` / `data-dialog-exiting` 的脱流退出节点。标记在实际完成或组件清理时移除，不用固定计时器。
4. 完成回调校验当前位置是否达到最新目标，防止旧动画回调结束新的开合。

已有弹窗外框只需接入这个归属协议；无需为使用本 case 重写整套 Dialog。外框可以保留已有宽度测量 / 滚动上限，跟随局部连续高度。独立的离散宽度变化仍可动画，但其引起的换行应实际验证，不承诺仅加本模板就修复所有响应式宽高联动。

## Radix / shadcn 与交互生命周期

优先保留原语提供的语义、键盘操作和视觉样式。简单情况继续使用原语的 CSS 尺寸变量即可。

复杂测量过渡需要常驻内容时，结构通常为：

```tsx
<Collapsible.Content forceMount>
  <FlowRegion open={open} fade>
    <div style={{ paddingTop: 12 }}><SettingsForm /></div>
  </FlowRegion>
</Collapsible.Content>
```

检查实际安装版本：部分 Radix Collapsible 实现会在状态切换时暂时禁用其 Content 节点动画并读取尺寸。因此不要未经验证，把外部 CSS / Motion 尺寸动画直接叠在原语内部测量的同一节点上。独立的原生 motion 尺寸层能隔离这类冲突。该实现细节不是稳定 API，不能推断所有版本必然如此。

模板在关闭时立即设 `inert` / `aria-hidden`；带 fade 的区域完成折叠后才设内层 `visibility: hidden`。若焦点仍在内部，调用方先将焦点还给触发器。模板不替代 Dialog 的焦点陷阱、Escape 处理、滚动锁或语义标签。

`prefers-reduced-motion` 生效时直接到最终尺寸并取消位移，保持内容和操作可用；模板支持挂载后的偏好变更。按产品需要允许极短透明度变化，但不能仍播放大幅位移或弹簧。

运行时切换偏好有三个容易漏掉的边界，模板已处理：

- 只改 `transition.duration` 而目标值不变，已有 spring 可能继续。零时长同终点关键帧显式接管旧动画。
- 零时长完成回调可能先于 DOM 样式落地。完成校验放到可取消的下一帧，检查最新目标；这与给每次 Observer 测量再加一帧延迟不同。
- Presence 已开始的退出也要响应偏好变化。模板用 `usePresence`、命名阶段与 `safeToRemove` 交接退出，防止只更新进入动画或留下空 wrapper。

## AI Agent 执行步骤

1. 找到实际变化来源及其后续兄弟，列出内容、局部占位、外框各自的动画负责人；先复用项目现有 primitive。
2. 区分“保留状态的开合”“可卸载的语义替换”“离散列表重排”，按最小方案表选择；静态单层折叠不引入整套协议。
3. 将条件间距纳入自然内层；审查 `open &&`、gap、key、`h-full`、CSS transition 是否破坏退出或测量。
4. 需要组合能力时接入模板；只在确有嵌套运动时接入祖先跟随，不盲目给整棵树加 layout。
5. 实际渲染并采样进入、退出和反向过程。静态截图、类型检查只能补充，不能证明运动连续。
6. 按下方与实际场景相关的验收项验证，交付说明实现归属与未覆盖边界，不声称“一次封装自动修复所有动画”。

## 常见失败与定位

| 现象 | 优先检查 |
|---|---|
| 外框平滑，内部按钮先跳走 | 尺寸层是否只在最外面；局部内容是否瞬间改写自然流 |
| 收起一开始就没内容 | 条件渲染抢先卸载；原语是否立即 hidden；opacity 是否写在被卸载节点 |
| 最后一帧跳一小段 | gap / margin / last-child 切换；wrapper 是否只等淡出就卸载 |
| 嵌套外框总在追赶 | 是否多层同时对每帧测量值做 spring |
| 子在展开时父瞬间关闭 | 跟随协议错误覆盖本地显式关闭 |
| 输入草稿消失 / 光标重置 | 语义 key 错误、强制 remount、面板状态没有保留 |
| 初次打开闪一下 | 未测量用 0；已有内容被当作后插入；initial 与挂载边界错误 |
| 内容高度自激或被卡住 | 测了外层；自然内层依赖父高度；CSS / Motion 同时控高 |

## 验收清单

### 必须同时观察

- [ ] 展开与收起均有 `0 < opacity < 1`、起终点之间的局部高度；之后元素的相对 Y 坐标有连续中间值。
- [ ] 采样相对同一个稳定自然父节点；居中弹窗整体移动不能掩盖内部瞬移。
- [ ] 初帧、若干中间帧、末帧都正确；最终没有条件间距突然消失、内容裁切或残留 wrapper。
- [ ] 中途反向从当前位置继续，旧回调不重置新状态；草稿保留，隐藏内容不可交互。
- [ ] 减少动态效果偏好在初始与运行时生效，最终内容完整。

### 按场景追加

- [ ] 有嵌套：子展开 / 收起、父在子动画中关闭，外框没有第二段缓动拖尾。Observer 允许一两帧传播，不能要求同一 paint 中所有测量绝对一致。
- [ ] 有条件内容：`空 → 有 → 空`，包括空字符串与快速切换；Presence 和占位都结束后才清理。
- [ ] 有列表：删除中间 / 末尾 / 全部项，幸存项与列表下方按钮均连续移动；输入行使用稳定身份。
- [ ] 有异步尺寸 / 换行：加载完成、窗口变窄、内容从非零变零，测量均可收敛。
- [ ] 有焦点 / 滚动：收起时焦点归位、滚动容器与弹窗上限正确，控件没有被透明层拦截。

真实 width / height 动画会触发布局工作。将测量与补间限制在局部；长列表、逐字输出、高频日志先评估布局成本，不宣称此方案只走 GPU 或性能必然优于 transform。

## 延伸资料

- [Motion layout animations](https://motion.dev/docs/react-layout-animations)：布局投影与布局协调。
- [Motion AnimatePresence](https://motion.dev/docs/react-animate-presence)：退出保留、popLayout 与 ref 边界。
- [Motion accessibility](https://motion.dev/docs/react-accessibility)：减少动态效果。
- [Radix Collapsible](https://www.radix-ui.com/primitives/docs/components/collapsible)：forceMount、状态与尺寸变量。

该模式来自真实项目的折叠、条件字段、内容切换与弹窗组合修正。模板是经过验证的接入起点，调用方的 DOM、间距、第三方版本和滚动约束仍需按本清单复验。


### 模板验证记录

2026-09-23：模板在 React 19 / Motion 12 的浏览器 fixture 中通过 13 个场景、1066 帧采样与严格 TypeScript 检查；演示以固定 React 19.1.1 / Motion 12.23.12 CDN 另验 13 个场景。运行环境为 Windows / Edge 153，包含中途减少动态效果与退出清理。该记录不是跨浏览器兼容承诺，集成到项目后仍执行上方适用验收项。
