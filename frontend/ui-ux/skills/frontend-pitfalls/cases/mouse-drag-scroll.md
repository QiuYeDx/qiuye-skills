# Case 4: 横向滚动行的鼠标拖拽滚动

## 目标

为横向滚动的卡片行、截图条、标签栏等区域补上「按住鼠标拖动即可滚动」的交互，与触屏滑动的手感一致，同时避免：

- 拖拽结束后误触发卡片 / 链接的点击。
- 拖拽时选中文字、拖出图片的原生拖放影子。
- 与 `scroll-snap` 互相拉扯：拖动发涩、松手后瞬间跳到吸附点。
- 普通单击失效，或触屏的原生惯性滚动被接管后变差。

## 适用场景

- `overflow-x: auto` 的轮播行、截图条、横向标签、Chip 列表，尤其是隐藏了滚动条的区域。
- 桌面用户反馈「只有触屏能横向滑，鼠标很难滚」「只能 Shift + 滚轮」。
- 行内元素本身可点击（卡片、链接、按钮），拖拽与点击需要共存。
- 响应式布局中同一个容器在窄屏是横向滚动、宽屏是普通网格。

## 核心判断

浏览器不会让鼠标拖拽滚动元素：按住拖动的默认行为是选中文字或拖出图片。要支持，需要自己处理 pointer 事件。难点不在「改 `scrollLeft`」，而在三件事的边界：

1. **什么时候算拖拽**：按下就接管会吞掉点击；要等移动超过阈值。
2. **拖完的那次 click**：pointerup 之后浏览器仍会派发 click，必须拦截。
3. **scroll-snap**：拖动时吸附会和手写的 `scrollLeft` 互相拉扯；松手时直接恢复吸附又会瞬间跳位。

## 排查顺序

1. 确认容器确实可滚动（`scrollWidth > clientWidth`），以及只在哪些断点可滚动。
2. 查看容器与子元素的 `scroll-snap-type`、`scroll-snap-align`、`scroll-padding`。
3. 列出行内可点击元素及其手势（`onClick`、Motion `whileTap`、链接），确认拖拽后不应触发。
4. 检查是否有平滑滚动库（Lenis 等）或外层手势（下拉关闭、滑动切页）会抢同一组事件。
5. 区分输入类型：触屏已有原生滚动与惯性，只需要处理鼠标。

## 推荐结构

```text
pointerdown（仅鼠标左键、且容器可滚动）
  └─ 记录起点与 scrollLeft，不捕获、不 preventDefault
pointermove
  ├─ 位移 < 4px：什么都不做，保留点击
  └─ 首次超过阈值：setPointerCapture、暂停 scroll-snap、cursor: grabbing
      └─ scrollLeft = 起始值 - dx，并记录速度
pointerup / pointercancel
  ├─ 未拖拽：交给原本的点击
  └─ 已拖拽：标记拦截下一次 click
      ├─ 按速度外推落点，选最近的吸附点
      ├─ scrollTo({ left, behavior: "smooth" })（吸附仍暂停）
      └─ scrollend（或超时兜底）后恢复 scroll-snap
click（捕获阶段）：被标记时 preventDefault + stopPropagation
dragstart：preventDefault；容器 user-select: none
```

## 推荐实现模板

```ts title="hooks/use-drag-scroll.ts"
"use client";

import { useEffect, useRef } from "react";

const DRAG_THRESHOLD = 4;
const MOMENTUM_MS = 220;

/** `scroll-snap-align: start` 的子项在容器中的吸附位置。 */
function snapPositions(el: HTMLElement) {
  const padding = parseFloat(getComputedStyle(el).scrollPaddingLeft) || 0;
  const origin = el.getBoundingClientRect().left - el.scrollLeft;
  const max = el.scrollWidth - el.clientWidth;
  return Array.from(el.children, (child) => {
    const left = child.getBoundingClientRect().left - origin - padding;
    return Math.min(max, Math.max(0, Math.round(left)));
  });
}

export function useDragScroll<T extends HTMLElement>() {
  const ref = useRef<T>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const finePointer = window.matchMedia("(hover: hover) and (pointer: fine)");
    const scrollable = () => el.scrollWidth > el.clientWidth + 1;

    el.style.userSelect = "none";
    const syncCursor = () => {
      el.style.cursor = finePointer.matches && scrollable() ? "grab" : "";
    };
    syncCursor();
    const resize = new ResizeObserver(syncCursor);
    resize.observe(el);

    let pointerId: number | null = null;
    let startX = 0;
    let startScroll = 0;
    let dragging = false;
    let snaps = false;
    let lastX = 0;
    let lastTime = 0;
    let velocity = 0; // scrollLeft px / ms
    let suppressClick = false;
    let restoreTimer: ReturnType<typeof setTimeout> | undefined;

    const restoreSnap = () => {
      clearTimeout(restoreTimer);
      el.removeEventListener("scrollend", restoreSnap);
      el.style.scrollSnapType = "";
    };

    const onPointerDown = (event: PointerEvent) => {
      suppressClick = false;
      if (event.pointerType !== "mouse" || event.button !== 0) return;
      if (!scrollable()) return;
      pointerId = event.pointerId;
      startX = lastX = event.clientX;
      startScroll = el.scrollLeft;
      lastTime = event.timeStamp;
      velocity = 0;
      dragging = false;
    };

    const onPointerMove = (event: PointerEvent) => {
      if (event.pointerId !== pointerId) return;
      const dx = event.clientX - startX;
      if (!dragging) {
        if (Math.abs(dx) < DRAG_THRESHOLD) return;
        dragging = true;
        restoreSnap();
        snaps = getComputedStyle(el).scrollSnapType !== "none";
        el.setPointerCapture(event.pointerId);
        el.style.scrollSnapType = "none";
        el.style.cursor = "grabbing";
      }
      const elapsed = event.timeStamp - lastTime;
      if (elapsed > 0) {
        velocity = velocity * 0.4 + (-(event.clientX - lastX) / elapsed) * 0.6;
      }
      lastX = event.clientX;
      lastTime = event.timeStamp;
      el.scrollLeft = startScroll - dx;
    };

    const onPointerUp = (event: PointerEvent) => {
      if (event.pointerId !== pointerId) return;
      pointerId = null;
      if (!dragging) return;
      dragging = false;
      suppressClick = true;
      syncCursor();
      if (el.hasPointerCapture(event.pointerId)) el.releasePointerCapture(event.pointerId);

      // 松手前停顿过，就不再带惯性。
      const idle = event.timeStamp - lastTime > 80;
      const projected = el.scrollLeft + (idle ? 0 : velocity * MOMENTUM_MS);
      let target = projected;
      if (snaps) {
        const points = snapPositions(el);
        if (points.length) {
          target = points.reduce((best, p) =>
            Math.abs(p - projected) < Math.abs(best - projected) ? p : best,
          );
        }
      }
      // 吸附保持暂停，滑到吸附点后再恢复，避免恢复时瞬间跳位。
      el.addEventListener("scrollend", restoreSnap);
      restoreTimer = setTimeout(restoreSnap, 900);
      el.scrollTo({ left: target, behavior: "smooth" });
    };

    const onClickCapture = (event: MouseEvent) => {
      if (!suppressClick) return;
      suppressClick = false;
      event.preventDefault();
      event.stopPropagation();
    };
    const onDragStart = (event: DragEvent) => event.preventDefault();

    el.addEventListener("pointerdown", onPointerDown);
    el.addEventListener("pointermove", onPointerMove);
    el.addEventListener("pointerup", onPointerUp);
    el.addEventListener("pointercancel", onPointerUp);
    el.addEventListener("click", onClickCapture, true);
    el.addEventListener("dragstart", onDragStart);
    return () => {
      restoreSnap();
      resize.disconnect();
      el.removeEventListener("pointerdown", onPointerDown);
      el.removeEventListener("pointermove", onPointerMove);
      el.removeEventListener("pointerup", onPointerUp);
      el.removeEventListener("pointercancel", onPointerUp);
      el.removeEventListener("click", onClickCapture, true);
      el.removeEventListener("dragstart", onDragStart);
      el.style.userSelect = "";
      el.style.cursor = "";
    };
  }, []);

  return ref;
}
```

```tsx title="使用"
const rowRef = useDragScroll<HTMLDivElement>();

<div ref={rowRef} className="flex snap-x snap-mandatory scroll-px-6 overflow-x-auto">
  {items.map((item) => (
    <Card key={item.id} className="snap-start" onClick={() => open(item)} />
  ))}
</div>
```

## 常见坑与修复

### 坑 1: 按下就 `setPointerCapture` / `preventDefault`

错误模式：

```ts
el.addEventListener("pointerdown", (e) => {
  e.preventDefault();
  el.setPointerCapture(e.pointerId);
  dragging = true;
});
```

原因：

- 捕获后，pointerup 的目标变成容器，click 会派发到按下与抬起目标的公共祖先，行内卡片 / 链接的点击全部失效。
- `pointerdown` 上 `preventDefault` 会阻止兼容的 mousedown 默认行为，按钮拿不到焦点。

修复：

- 按下时只记录起点；移动超过 3–5px 才捕获指针、进入拖拽。
- 文本选择与图片拖拽用 `user-select: none` 和 `dragstart` 处理，不要在 `pointerdown` 上 `preventDefault`。

### 坑 2: 拖完松手，卡片被打开

原因：

- 指针在同一元素上按下又抬起，浏览器照常派发 click；拖拽距离再长也一样。

修复：

- 拖拽结束时置一个标记，在**捕获阶段**拦截下一次 click（`preventDefault` + `stopPropagation`），让子元素的处理器收不到。
- 下一次 pointerdown 时清掉标记：click 没有派发到容器内时（例如在容器外抬起），标记不会残留到下一次真正的点击。

### 坑 3: 拖拽时 scroll-snap 与 `scrollLeft` 互相拉扯

现象：`scroll-snap-type: x mandatory` 的行里，拖动发涩、回弹，或每帧被拉回吸附点。

修复：

- 进入拖拽时在内联样式写 `scroll-snap-type: none`，结束后再恢复为空字符串（回到 CSS 规则）。
- 进入拖拽前读取并记住原本是否吸附；拖拽中读到的已是内联的 `none`。

### 坑 4: 松手后立刻恢复吸附，画面瞬间跳位

原因：

- 恢复 `scroll-snap-type` 时，浏览器会立刻把当前位置重新吸附到最近的吸附点，通常没有动画。
- 再叠加一个 `scrollTo({ behavior: "smooth" })`，两者目标不同时还会来回抖。

修复：

- 自己计算吸附点：子项的 `getBoundingClientRect().left` 换算到滚动坐标，减去 `scroll-padding-left`，并夹在 `[0, scrollWidth - clientWidth]` 内。
- 按最后的速度外推一小段（约 200ms）作为落点，取最近的吸附点，在吸附仍暂停时平滑滚过去。
- 在 `scrollend` 后恢复吸附；不支持 `scrollend` 的浏览器用超时兜底。此时位置已在吸附点上，恢复不会再移动。

### 坑 5: 一并接管触屏

原因：

- 触屏本来就能横向滑动，且有系统惯性与回弹；用 pointer 事件手写会变差，还会和页面的纵向滚动、下拉关闭等手势冲突。

修复：

- 只处理 `pointerType === "mouse"` 且 `button === 0`；触屏与触控笔直接返回。

### 坑 6: 宽屏不滚动时仍显示 grab 光标或拦截事件

原因：

- 同一个容器在宽屏常是普通网格（`overflow: visible`），此时拖拽没有意义。

修复：

- 每次按下时检查 `scrollWidth > clientWidth`。
- grab 光标只在精细指针、且确实可滚动时显示；用 ResizeObserver 在尺寸变化时更新。

### 坑 7: 速度估计只取最后一帧

原因：

- 松手前最后一次 pointermove 可能间隔很短或抖动，单帧速度忽大忽小，落点不稳定；手停住后再松手也会被甩出去。

修复：

- 对速度做简单的指数平滑。
- 最后一次移动距松手超过约 80ms 时视为停住，不带惯性。

## AI Agent 执行步骤

1. 找出所有横向滚动区域，确认在哪些断点可滚动、是否使用 scroll-snap 与 scroll-padding。
2. 把拖拽逻辑写成通用 hook（如 `hooks/use-drag-scroll.ts`），不要在每个组件里各写一份。
3. 按推荐结构实现：仅鼠标、超过阈值才拖拽、捕获阶段拦截拖后 click、拖拽中暂停吸附、松手自算吸附点并在 `scrollend` 后恢复。
4. 容器设置 `user-select: none` 并拦截 `dragstart`；可滚动时显示 grab / grabbing 光标。
5. 若容器在平滑滚动库或外层手势容器内，确认横向拖拽不会触发它们（纵向滚动库通常不受影响；内部滚动区按库约定加 `data-lenis-prevent` 等标记）。
6. 用真实鼠标拖拽验证，不只用合成事件。

## 验收清单

- 鼠标拖动能滚动，位移跟手；松手后平滑停在吸附点上（`scrollLeft` 等于某个子项位置减去 `scroll-padding`）。
- 快速甩动会多滑一项，停住再松手不会被甩出去。
- 拖拽后没有打开卡片 / 跳转链接；单击仍正常。
- 拖动过程中没有选中文字，也没有出现图片拖放影子。
- 拖完后 `scroll-snap-type` 已恢复为 CSS 中的值，之后用触控板滚动仍会吸附。
- 触屏滑动的行为与改动前一致。
- 宽屏不可滚动时没有 grab 光标，点击不受影响。

## 推荐回答格式

完成后向用户说明：

- 哪些区域支持了鼠标拖拽，触屏是否保持原生行为。
- 如何区分点击与拖拽、如何避免拖后误点。
- 与 scroll-snap 的配合方式，以及真实拖拽的验证结果（如拖拽距离、最终 `scrollLeft` 与吸附点）。
