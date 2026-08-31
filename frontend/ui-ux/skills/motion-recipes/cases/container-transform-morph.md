# Case 7: 容器变形过渡（Container Transform）：触发器原地扩展与卡片飞向视口中央

## 目标

实现"点击一个小元素，它平滑变形为一个更大的面板 / 浮层"的容器变形过渡（Container Transform，亦称 shared element transition / hero animation / morphing dialog）。

覆盖两种拓扑：

- **策略 A（原地扩展）**：面板锚定在触发器位置，同一个容器节点 animate 宽高（例：筛选按钮 → 筛选面板）
- **策略 B（矩形迁移）**：卡片飞向视口中央成为模态浮层，占位 + 视觉克隆 animate 矩形（例：列表卡片 → 居中详情浮层 + 遮罩阴影）

---

## 适用场景

典型需求表述：

- 「点击筛选按钮，让它原地展开成一个筛选面板」
- 「点击卡片后，卡片放大 / 飞到屏幕中央变成详情浮层，背景加遮罩」
- 「按钮变成搜索框 / 输入区，要有变形的连续感」
- 「FAB 点击后变成对话框」
- 「图片点击后放大到居中灯箱」
- 「卡片和详情共用标题 / 徽章，过渡时要跟着飞」

典型 UI：筛选面板、搜索框展开、内联编辑、卡片详情浮层、图片灯箱、FAB → Dialog、通知项 → 通知中心。

**策略选型判据（一句话）**：展开后的表面还"属于"触发器附近吗？属于 → 策略 A；要成为全局模态 → 策略 B。

---

## 核心设计原则

### 1. 容器几何用数值驱动，不要给整个容器套 `layoutId`

`layoutId` 的 FLIP 投影基于 `transform: scale()`，容器大幅变形时嵌套内容（多行文字、网格、边框）会拉伸失真；居中终点还需要视口计算与 clamp，自动 FLIP 给不了控制权。正确分工：

- 容器本身：显式 `animate={{ width, height }}`（策略 A）或 `animate={{ top, left, width, height }}`（策略 B），spring `bounce: 0`
- 容器内的小元素（标题、徽章、序号）：用 `layoutId` 迁移（见原则 5）

数值驱动每帧触发 reflow，但换来文字自然换行、圆角边框全程稳定，单个浮层的成本可接受。

### 2. 策略 B 必须占位与视觉分离

留在文档流里的元素和被动画的元素不是同一个：

- **占位层**：真实 `button`，`opacity-0` 留在网格里 —— 保住布局（起飞后网格不塌陷）、点击目标、`aria-expanded/aria-controls`、焦点还原锚点
- **视觉层**：`absolute` 定位的克隆，非激活时精确覆盖占位按钮（测量矩形），激活时矩形换成居中浮层矩形

```tsx
const visualRect = active && expandedRect ? expandedRect : itemRects.get(item.id);

<motion.div
  className="absolute"
  style={{ zIndex: active ? 65 : 10 }}
  initial={false}
  animate={visualRect}
  transition={{ type: "spring", duration: 0.48, bounce: 0 }}
>
```

同一个节点、同一条 spring，起飞 / 降落只是目标矩形的切换。

### 3. 所有矩形换算到同一坐标系，且维护要完整

视觉克隆相对列表容器（`relative` 祖先）定位，`getBoundingClientRect()` 结果和视口计算的终点矩形都要减去列表容器的视口位置：

```tsx
const expandedRect = {
  top: viewportRect.top - listRect.top,
  left: viewportRect.left - listRect.left,
  width: viewportRect.width,
  height: viewportRect.height,
};
```

维护清单：

- `ResizeObserver` 观察列表 + `resize` / capture 阶段 `scroll` 监听（滚动不改尺寸，ResizeObserver 不触发）
- 触发按钮 `onPointerDown={(e) => e.preventDefault()}`：阻止点击聚焦引发的浏览器自动微滚动
- 渲染期直接读一次 live rect 兜底：`listRef.current?.getBoundingClientRect() ?? cachedRect`

### 4. 用四相位状态机，不要只用 boolean

```tsx
type OverlayPhase = "closed" | "opening" | "open" | "closing";
```

- `opening`：容器飞行；卡片非共享内容淡出；详情辅助内容延迟淡入；遮罩 delay 0.12s 淡入；定时器（约 520ms）转 `open`
- `open`：详情可交互；背景滚动锁定
- `closing`：**关闭那一刻重测触发器矩形**作为返回目标（resize / 布局可能已变化）；详情内容立即淡出；遮罩 0.18s 快速退场；定时器（约 600ms）转 `closed`
- `closed`：卸载遮罩与详情；`trigger.focus({ preventScroll: true })` 还原焦点

策略 A 用 `isOpen + isInteractive` 两个状态即可，`isInteractive` 在开 / 关时都先置 false，`onAnimationComplete` 后恢复。

### 5. 内容三分法：共享元素迁移、旧内容让位、新内容错峰

1. **共享元素**（两端都有的标题 / 徽章 / 序号）：`layoutId` + `LayoutGroup` 作用域 + `layoutCrossfade={false}`（避免双份文字重影），transition 与容器同参数
2. **旧内容**（卡片描述、图标等非共享部分）：opening 时淡出 0.18–0.2s，closing 时恢复不透明等克隆落地
3. **新内容**（详情数据、按钮等"卫星内容"）：`opacity: 0, y: 5` 起步，容器基本就位后淡入；closing 时立即淡出

关闭回程的共享元素处理：详情侧**注销 `layoutId`**（渲染普通元素 + `invisible` 占位保尺寸），同名 `layoutId` 接力棒交回卡片侧，Motion 自动迁回，无需手写回程。

### 6. 环境层：遮罩 portal + 独立柔影 + z-index 阶梯

- 遮罩 `createPortal` 到 `document.body`，避免被祖先 `overflow` / 层叠上下文裁剪
- `backdrop-filter` 不直接交给 Motion，动画一个 CSS 变量再让 `backdropFilter` 引用它（兼容性更稳）
- 阴影不用容器 `box-shadow`，单独一层 `bg-black/20 blur-xl` 的柔影 div 跟随同一矩形飞行（重绘开销低、可独立控制透明度时间线）
- z-index 阶梯：非激活卡片 10 < 遮罩 60 < 柔影 64 < 激活浮层 65；定位锚加 `isolate`

---

## 推荐实现模板

### 策略 A：原地扩展（单容器变形）

```tsx
const SPRING = { type: "spring" as const, duration: 0.4, bounce: 0 };
const CONTENT_EASE = [0.23, 1, 0.32, 1] as const;

// 测量：两个源
// - triggerMeasureRef: invisible 的触发器内容副本（内容变化时宽度会变）
// - panelContentRef: 面板内容本体（内部展开时高度会变）
// 两者都挂同一个 ResizeObserver，写入 triggerWidth / panelSize

<div className="relative isolate" style={{ height: 28 }}>
  <div ref={triggerMeasureRef} aria-hidden="true"
    className="invisible pointer-events-none flex h-7 w-max items-center px-2.5">
    {triggerContent}
  </div>

  <motion.div
    className="absolute top-0 right-0 isolate overflow-hidden rounded-lg border bg-popover"
    initial={false}
    animate={{
      width: isOpen ? panelSize.width || triggerWidth : triggerWidth,
      height: isOpen ? panelSize.height || 28 : 28,
    }}
    transition={shouldReduceMotion ? { duration: 0 } : SPRING}
    onAnimationComplete={() => { if (isOpen) setIsInteractive(true); }}
  >
    {/* 收起态：真实卸载，保证可聚焦可点击 */}
    <AnimatePresence initial={false}>
      {!isOpen && (
        <motion.button key="trigger" onClick={openPanel}
          className="absolute top-0 right-0 flex h-7 items-center px-2.5"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1, transition: { duration: 0.14, delay: 0.24, ease: CONTENT_EASE } }}
          exit={{ opacity: 0, transition: { duration: 0.1 } }}>
          {triggerContent}
        </motion.button>
      )}
    </AnimatePresence>

    {/* 展开态：常驻挂载，只切 opacity + inert（面板内部状态不丢失） */}
    <motion.div ref={panelContentRef}
      className="absolute top-0 right-0 w-[min(48rem,calc(100vw-2rem))]"
      initial={false}
      animate={{ opacity: isOpen ? 1 : 0 }}
      transition={{
        duration: isOpen ? 0.22 : 0.28,
        delay: isOpen ? 0.08 : 0,
        ease: CONTENT_EASE,
      }}
      inert={!isInteractive}
      aria-hidden={!isInteractive}>
      {panelContent}
    </motion.div>
  </motion.div>
</div>
```

时序规律：容器先行（t=0 spring），新内容 delay 0.08s 淡入，旧内容立即淡出；关闭反向（面板内容立即淡出，触发器 delay 0.24s 出现）。

### 策略 B：矩形迁移（占位 + 克隆飞行）

```tsx
const CARD_TRANSITION = { type: "spring" as const, duration: 0.48, bounce: 0 };

// 终点矩形：居中 + 安全边距 + 尺寸 clamp + 内容高度感知
function readCenteredPanelRect(contentHeight = 0) {
  const isMobile = window.innerWidth < 640;
  const inset = isMobile ? 12 : 16;
  const width = isMobile
    ? window.innerWidth - inset * 2
    : Math.min(640, window.innerWidth - inset * 2);
  const maxHeight = window.innerHeight - inset * 2;
  const height = Math.min(maxHeight, Math.max(isMobile ? 320 : 360, contentHeight));
  return {
    top: inset + Math.max(0, (maxHeight - height) / 2),
    left: Math.max(inset, (window.innerWidth - width) / 2),
    width,
    height,
  };
}

<LayoutGroup id={panelId}>
  <ol ref={listRef} className="relative grid gap-4 lg:grid-cols-2">
    {items.map((item, index) => {
      const active = item.id === activeId;
      const visualRect = active && expandedRect ? expandedRect : itemRects.get(item.id);
      return (
        <li key={item.id} className="h-full min-w-0">
          {/* ① 占位层：真实按钮，opacity-0 */}
          <button type="button"
            aria-controls={panelId} aria-expanded={active}
            onPointerDown={(e) => e.preventDefault()}
            onClick={(e) => onSelect(item.id, e.currentTarget)}
            className="w-full opacity-0 focus-visible:outline-none">
            <CardContent item={item} index={index} />
          </button>

          {visualRect ? (
            <>
              {/* ② 柔影层：独立软阴影，同步飞行 */}
              {active && overlayPhase ? (
                <motion.div aria-hidden="true"
                  className="pointer-events-none absolute rounded-2xl bg-black/20 blur-xl"
                  style={{ zIndex: 64 }}
                  initial={{ opacity: 0 }}
                  animate={{ ...visualRect, opacity: overlayPhase === "closing" ? 0 : 1 }}
                  transition={CARD_TRANSITION} />
              ) : null}

              {/* ③ 视觉层：被动画的克隆 */}
              <motion.div
                className={cn("absolute", active ? "pointer-events-auto" : "pointer-events-none")}
                style={{ zIndex: active ? 65 : 10 }}
                initial={false}
                animate={visualRect}
                transition={shouldReduceMotion ? { duration: 0 } : CARD_TRANSITION}>
                <CardVisual item={item} index={index}
                  fadeBody={Boolean(active && overlayPhase && overlayPhase !== "closing")} />
                {active && overlayPhase ? (
                  <DetailVisual item={item} index={index} phase={overlayPhase}
                    onClose={closeDetails} onContentHeightChange={setContentHeight} />
                ) : null}
              </motion.div>
            </>
          ) : null}
        </li>
      );
    })}
  </ol>
</LayoutGroup>

{/* ④ 遮罩层：portal 到 body，CSS 变量动画 backdrop-filter */}
{overlayMounted && createPortal(
  <motion.div aria-hidden="true"
    className="fixed inset-0 bg-black/40"
    style={{
      zIndex: 60,
      ["--scrim-bf" as string]: "blur(0px)",
      backdropFilter: "var(--scrim-bf)",
      WebkitBackdropFilter: "var(--scrim-bf)",
    }}
    onClick={() => closeDetails(false)}
    initial={{ opacity: 0, ["--scrim-bf" as string]: "blur(0px)" }}
    animate={{
      opacity: phase === "closing" ? 0 : 1,
      ["--scrim-bf" as string]: phase === "closing" ? "blur(0px)" : "blur(6px)",
      transition: {
        duration: phase === "closing" ? 0.18 : 0.32,
        delay: phase === "closing" ? 0 : 0.12,
      },
    }} />,
  document.body,
)}
```

共享元素（卡片视觉与详情视觉里各渲染一份）：

```tsx
<motion.h3
  layoutId={`${prefix}-title`}
  layoutCrossfade={false}
  transition={CARD_TRANSITION}
  className="mt-2 text-lg font-semibold"
>
  {item.title}
</motion.h3>
```

---

## AI Agent 执行步骤

### Step 1: 判定拓扑，选择策略

- 面板锚定触发器（Popover 型）→ 策略 A
- 终点在视口中央 / 需要遮罩的模态 → 策略 B

### Step 2: 搭建几何骨架

- 策略 A：定位锚 + 单容器 + 隐形测量节点 + 面板内容 ResizeObserver
- 策略 B：列表 `relative` 坐标系 + 占位按钮 + 视觉克隆 + 矩形测量（ResizeObserver + scroll/resize + live rect 兜底）+ `readCenteredPanelRect`

### Step 3: 建立状态机

- 策略 A：`isOpen` + `isInteractive`（开关都先置 false，`onAnimationComplete` 恢复）
- 策略 B：`closed / opening / open / closing` + 开关定时器（约 520ms / 600ms，reduced motion 时为 0）；closing 时重测 trigger rect

### Step 4: 编排内容

- 列出共享元素（两端都有的），套 `layoutId` + `layoutCrossfade={false}`，放进 `LayoutGroup`
- 旧内容 opening 淡出、closing 恢复；新内容延迟淡入、closing 立即淡出
- 关闭回程：详情侧注销 layoutId（普通元素 + `invisible`）

### Step 5: 补环境层与可访问性

- 遮罩 portal + CSS 变量 backdrop-filter + 点击关闭
- 柔影层同步矩形
- Escape 关闭、focus trap、焦点还原 `preventScroll`、滚动锁定（拦截 wheel/touchmove，放行浮层内部）
- `useReducedMotion` 全链路归零时长

### Step 6: 逐帧验证

双向过渡各采样首帧（约 16ms）、中间态（80–300ms）、结束帧，检查容器几何、共享元素、旧 / 新内容、遮罩与阴影。

---

## 常见坑与修复

### 坑 1: 用 `layoutId` 包整个卡片，过渡中文字拉伸、圆角变形

**原因**：容器级 FLIP 投影用 `transform: scale()`，深层内容的尺寸矫正不完美。

**修复**：容器几何改为数值驱动（animate 矩形），`layoutId` 只留给内部小元素。

### 坑 2: 面板打开瞬间尺寸为 0 或跳变

**原因**：首次打开时测量还没就绪。

**修复**：animate 目标写 fallback：`panelSize.width || triggerWidth`；策略 B 在 `selectItem` 里同步先算一次 `readCenteredPanelRect()`。

### 坑 3: 过渡中半透明面板可以点击 / 聚焦

**修复**：`inert={!isInteractive}` + `pointer-events-none`；`isInteractive` 在开与关时都先置 false，动画完成回调中恢复。

### 坑 4: 点击卡片瞬间克隆错位几像素

**原因**：浏览器在按钮聚焦时执行了自动微滚动，缓存的矩形过期。

**修复**：按钮 `onPointerDown={(e) => e.preventDefault()}`；渲染期读 live rect（`listRef.current?.getBoundingClientRect() ?? cachedRect`）。

### 坑 5: 关闭时飞回错误位置

**原因**：使用打开时缓存的 origin rect，期间窗口 resize 或布局变化。

**修复**：`closeDetails` 第一行重测 `triggerRef.current` 的矩形作为 return rect。

### 坑 6: 遮罩 backdrop-filter 不动画或闪烁

**修复**：动画 CSS 自定义属性（如 `--scrim-bf`），`backdropFilter: "var(--scrim-bf)"` 引用；同时写 `WebkitBackdropFilter`。

### 坑 7: 共享元素过渡中出现两份文字重影

**修复**：`layoutCrossfade={false}`；确保两端是同结构组件、同一个 `LayoutGroup`。

### 坑 8: 关闭时共享元素直接闪回，没有回程动画

**原因**：详情侧整体淡出时 layoutId 元素被父级 opacity 污染，或两端同时保留 layoutId 导致投影混乱。

**修复**：closing 时详情侧注销 layoutId（渲染普通元素 + `invisible` 占位），让卡片侧同名 layoutId 接管回程；共享元素祖先不做 opacity/filter 动画（参考 Case 3）。

### 坑 9: 浮层内容滚动带动背景页面滚动

**修复**：overlay 挂载期间拦截 `wheel` / `touchmove`（`passive: false`），事件目标在浮层内部时放行。

---

## 动效参数建议

| 部分 | 推荐参数 |
|---|---|
| 容器几何 | `spring`，`duration: 0.4–0.48`，`bounce: 0`（必须无过冲，避免边框圆角终点抖动） |
| 共享元素迁移 | 与容器同参数（视觉上属于同一次运动） |
| 新内容淡入 | `0.18–0.24s`，delay `0.04–0.12s`，ease-out（如 `[0.23, 1, 0.32, 1]`） |
| 旧内容淡出 | `0.1–0.2s`，无 delay |
| 遮罩 | 进 `0.32s` + delay `0.12s` / 退 `0.18s` |
| 相位定时器 | opening → open 约 `520ms`；closing → closed 约 `600ms` |

---

## 验收清单

- [ ] 过渡全程容器边框、圆角、文字无拉伸变形（逐帧检查）
- [ ] 策略 B：卡片起飞后网格布局不塌陷、其他卡片不动
- [ ] 首次打开无 0 尺寸闪烁或跳变
- [ ] 过渡中面板 / 浮层内容不可点击、不可 Tab 聚焦
- [ ] 页面滚动后再打开，克隆起点仍精确覆盖卡片
- [ ] 窗口 resize 后关闭，克隆飞回正确位置
- [ ] 共享元素双向迁移连续，无重影、无闪回
- [ ] 遮罩淡入淡出平滑，backdrop-filter 正常过渡，点击遮罩可关闭
- [ ] Escape 可关闭；关闭后焦点回到触发器且页面不跳动
- [ ] 浮层打开时背景不可滚动，浮层内部可滚动
- [ ] `useReducedMotion` 下直接切换状态，功能流程完整
- [ ] z-index 阶梯正确：遮罩在飞行元素之下、页面内容之上
- [ ] TypeScript、lint 通过

---

## 推荐回答格式

```text
已完成容器变形过渡（Container Transform）：

- 采用[策略 A 原地扩展 / 策略 B 矩形迁移]：容器几何由数值驱动的 spring 完成，无缩放失真。
- [策略 B] 占位按钮保持布局与无障碍语义，视觉克隆负责飞行；关闭时重测触发器矩形作为返回目标。
- 共享元素（标题 / 徽章）通过 layoutId + layoutCrossfade={false} 在两端连续迁移；其余内容错峰淡入淡出。
- 遮罩经 portal 渲染并以 CSS 变量动画 backdrop-filter；柔影层与容器同步飞行。
- 已覆盖焦点管理、Escape / 遮罩关闭、滚动锁定与 reduced motion。
```
