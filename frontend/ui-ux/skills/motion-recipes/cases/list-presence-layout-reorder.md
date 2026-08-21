# Case 6: 列表增删、Presence 与位置重排

## 目标

实现带元素增加、删除和顺序变化的 Motion 列表，使删除项在旧位置退场、新增项在最终位置入场、幸存项只重排一次，并避免首帧跳过、文字拉伸、分批消失和快速切换残留。

优先使用 `AnimatePresence mode="popLayout"`。只有真实逐帧验收证明内置 presence 无法满足旧坐标、绘制时序或复杂容器约束时，才升级为退出快照方案。

---

## 适用场景

典型需求表述：

- 「筛选后删除的标签原地淡出，其余标签平滑补位」
- 「列表新增项淡入，同时旧项移动到新位置」
- 「Flex / Grid 批量增删时元素分两次消失」
- 「退出项第一帧就不见了，只有其他元素还在移动」
- 「新增项第一帧直接完全显示，没有真正淡入」
- 「layout 动画导致文字换行、边框拉伸或 scale 失效」
- 「快速连续筛选后残留退出副本」

典型 UI：筛选标签、可删除 Chip、任务列表、卡片 Grid、搜索结果、排序列表、可编辑步骤列表。

不适用于虚拟列表中已经卸载的不可见项；先遵循虚拟化引擎的生命周期和测量模型。

---

## 先选择实现等级

### A. 只有顺序变化，没有增删

使用稳定 key 和 `layout="position"`：

```tsx
{
  items.map((item) => (
    <motion.li key={item.id} layout="position">
      <Item item={item} />
    </motion.li>
  ));
}
```

不要为普通同树重排添加 `layoutId`。`layoutId` 用于跨 DOM 位置的共享元素迁移，不是列表重排的必要条件。

### B. 普通列表增删

默认使用 `AnimatePresence mode="popLayout"`：

```tsx
<AnimatePresence mode="popLayout" initial={false}>
  {items.map((item) => (
    <motion.li
      key={item.id}
      layout="position"
      initial={{ opacity: 0, scale: 0.96 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.96 }}
    >
      <Item item={item} />
    </motion.li>
  ))}
</AnimatePresence>
```

若直接子元素是自定义组件，使用 `forwardRef` 把 ref 转发到要被弹出布局流的 DOM 节点。

### C. 复杂 Flex / Grid、严格逐帧或多层尺寸动画

只有满足以下任一条件时才升级到退出快照：

- 退出项必须严格停留在旧 rect，而内置 `popLayout` 结果不稳定
- 批量筛选、换行或祖先裁剪导致部分 exit 丢失
- React 同步更新与 Motion 启动发生在 paint 前，首态没有真实绘制
- 快速连续操作需要显式批次身份与清理
- layout projection、scale、文字自然宽度或外框尺寸动画互相污染

---

## 核心设计原则

### 1. 把元素分为三组

每次比较 `previousItems` 与 `nextItems` 的稳定 id：

- survivors：继续在真实列表中，用 `layout="position"` 移动
- entering：立即进入最终布局，在最终位置执行视觉入场
- exiting：从真实列表移除，用旧 rect 的绝对定位快照退场

不要用数组 index 作为 key。筛选和排序后 index 会改变，Motion 会把不同业务项误判为同一个元素。

### 2. 位置层与视觉层分开

layout projection 和 scale 都写入 `transform`。不要让一个节点同时承担两者：

```tsx
<motion.div key={item.id} layout="position">
  <EnteringVisual active={enteringIds.has(item.id)}>
    <Item item={item} />
  </EnteringVisual>
</motion.div>
```

- 外层：只负责位置
- 内层：只负责 `opacity / scale`
- 快照：绝对定位，只负责退出

这会避免文字缩放变形、投影 transform 覆盖 scale，以及边框和阴影被尺寸投影拉伸。

### 3. 旧坐标必须相对同一个定位容器

如果 item 的 `offsetParent` 就是 `relative` 列表根节点，可保存：

```tsx
const rect = {
  left: node.offsetLeft,
  top: node.offsetTop,
  width: node.offsetWidth,
  height: node.offsetHeight,
};
```

如果不能保证 offset parent，使用 item rect 减去容器 rect，并补偿容器滚动：

```tsx
const itemRect = node.getBoundingClientRect();
const rootRect = root.getBoundingClientRect();

const rect = {
  left: itemRect.left - rootRect.left + root.scrollLeft,
  top: itemRect.top - rootRect.top + root.scrollTop,
  width: itemRect.width,
  height: itemRect.height,
};
```

### 4. DOM 初态不等于绘制初态

如果录帧证明 `controls.set(initial)` 与 `controls.start(target)` 被浏览器合并，使用双 rAF 保证中间至少发生一次 paint：

```tsx
function scheduleAfterPaint(callback: () => void) {
  let secondFrame = 0;
  const firstFrame = window.requestAnimationFrame(() => {
    secondFrame = window.requestAnimationFrame(callback);
  });

  return () => {
    window.cancelAnimationFrame(firstFrame);
    if (secondFrame) window.cancelAnimationFrame(secondFrame);
  };
}
```

不要默认给所有入场动画增加双 rAF。它是逐帧验证确认首态被吞掉后的修复，不是通用仪式。

### 5. 用动画完成信号清理，不用固定 timer

`controls.start()` 返回 Promise。退出完成后再删除对应快照：

```tsx
void controls.start(exitTarget).then(() => onExited(snapshotId));
```

固定 `setTimeout` 会在动画参数、后台降频、减少动态效果或快速操作变化后提前清理，产生末帧突消。

---

## 推荐实现模板

### 1. 类型与参数

```tsx
interface Item {
  id: string;
  label: string;
}

interface ExitSnapshot {
  snapshotId: string;
  item: Item;
  left: number;
  top: number;
  width: number;
  height: number;
}

const ENTER_SCALE = 0.6;
const ENTER_DURATION = 0.14;
const EXIT_DURATION = 0.12;
const ENTER_EASE = [0.23, 1, 0.32, 1] as const;
const EXIT_EASE = [0.4, 0, 1, 1] as const;
```

退出通常比进入快 15–25%。`scale: 0.6` 具有明显的聚散感；克制型业务 UI 可改为 `0.94–0.98`。

### 2. 进入视觉层

```tsx
function EnteringVisual({
  active,
  children,
  id,
  onEntered,
}: {
  active: boolean;
  children: ReactNode;
  id: string;
  onEntered: (id: string) => void;
}) {
  const controls = useAnimationControls();
  const reduceMotion = useReducedMotion();

  useLayoutEffect(() => {
    if (!active || reduceMotion) {
      controls.set({ opacity: 1, scale: 1 });
      return;
    }

    controls.set({ opacity: 0, scale: ENTER_SCALE });
    let cancelled = false;
    const cancelFrames = scheduleAfterPaint(() => {
      void controls
        .start({
          opacity: 1,
          scale: 1,
          transition: { duration: ENTER_DURATION, ease: ENTER_EASE },
        })
        .then(() => {
          if (!cancelled) onEntered(id);
        });
    });

    return () => {
      cancelled = true;
      cancelFrames();
    };
  }, [active, controls, id, onEntered, reduceMotion]);

  return (
    <motion.div
      initial={false}
      animate={controls}
      style={{
        opacity: active ? 0 : 1,
        scale: active ? ENTER_SCALE : 1,
      }}
      className="origin-center"
    >
      {children}
    </motion.div>
  );
}
```

### 3. 退出快照层

```tsx
function ExitingVisual({
  snapshot,
  onExited,
}: {
  snapshot: ExitSnapshot;
  onExited: (snapshotId: string) => void;
}) {
  const controls = useAnimationControls();

  useLayoutEffect(() => {
    controls.set({ opacity: 1, scale: 1 });
    let cancelled = false;
    const cancelFrames = scheduleAfterPaint(() => {
      void controls
        .start({
          opacity: 0,
          scale: ENTER_SCALE,
          transition: { duration: EXIT_DURATION, ease: EXIT_EASE },
        })
        .then(() => {
          if (!cancelled) onExited(snapshot.snapshotId);
        });
    });

    return () => {
      cancelled = true;
      cancelFrames();
    };
  }, [controls, onExited, snapshot.snapshotId]);

  return (
    <motion.div
      aria-hidden="true"
      className="pointer-events-none absolute z-20 origin-center"
      style={{
        left: snapshot.left,
        top: snapshot.top,
        width: snapshot.width,
        height: snapshot.height,
        opacity: 1,
        scale: 1,
      }}
      initial={false}
      animate={controls}
    >
      <ItemVisual item={snapshot.item} inert />
    </motion.div>
  );
}
```

快照必须 `aria-hidden`、不可点击、不可聚焦，且不得重复业务副作用。

### 4. 比较列表并创建批次快照

```tsx
useLayoutEffect(() => {
  const nextIds = new Set(items.map((item) => item.id));
  const previousIds = new Set(previousItemsRef.current.map((item) => item.id));
  const added = items.filter((item) => !previousIds.has(item.id));
  const removed = previousItemsRef.current.filter(
    (item) => !nextIds.has(item.id),
  );

  setEnteringIds((current) => {
    const next = new Set([...current].filter((id) => nextIds.has(id)));
    if (!reduceMotion) added.forEach((item) => next.add(item.id));
    return next;
  });

  if (removed.length > 0 && !reduceMotion) {
    batchRef.current += 1;
    const snapshots = removed.flatMap((item) => {
      const rect = previousRectsRef.current.get(item.id);
      return rect
        ? [{ snapshotId: `${batchRef.current}-${item.id}`, item, ...rect }]
        : [];
    });

    setExitingSnapshots((current) => [
      ...current.filter((entry) => !nextIds.has(entry.item.id)),
      ...snapshots,
    ]);
  }

  previousItemsRef.current = items;
  previousRectsRef.current = captureCurrentRects();
}, [items, reduceMotion]);
```

快照 id 加批次号，防止同一业务项快速退出、进入、再退出时，旧 Promise 回调清理新一批快照。

### 5. 渲染结构

真实列表立即使用最终 `items`；退出快照与 item 同处一个 `relative` 根节点，但不参与 Flex / Grid 布局：

```tsx
<div ref={rootRef} className="relative flex flex-wrap gap-2">
  {items.map((item) => (
    <motion.div key={item.id} layout="position">
      <EnteringVisual active={enteringIds.has(item.id)}>
        <ItemVisual item={item} />
      </EnteringVisual>
    </motion.div>
  ))}
  {exitingSnapshots.map((snapshot) => (
    <ExitingVisual key={snapshot.snapshotId} snapshot={snapshot} />
  ))}
</div>
```

---

## AI Agent 执行步骤

### Step 1: 建立逐帧目标并检查结构

明确新增、删除、幸存项的坐标和首态；确认稳定业务 key、Flex/Grid 根节点、滚动/裁剪祖先及所有写入 transform 的节点。

### Step 2: 先尝试内置方案

用 `AnimatePresence mode="popLayout"` + `layout="position"` 完成最小实现。自定义直接子组件转发 ref。视觉通过后停止。

### Step 3: 用录帧证据决定是否升级

只有看到首帧跳过、旧坐标丢失、批量 exit 缺失或 transform 冲突时，才添加进入状态集合、旧 rect 与退出快照。

### Step 4: 分层并处理生命周期

外层 layout，内层 opacity/scale；使用批次 id、Motion Promise 和 rAF cleanup；reduced motion 下跳过明显位移、缩放和快照。

### Step 5: 逐帧与响应式验收

验证增加、减少、纯重排、最后一项、快速往返、窄屏换行、滚动位置和动画结束后的 DOM 清理。

---

## 常见坑与修复

### 坑 1: 删除项第一帧就消失

真实 DOM 已删除，快照尚未挂载或初态未被 paint。在 `useLayoutEffect` 中基于旧 rect 创建快照；录帧确认首态仍被吞掉时再使用双 rAF。

### 坑 2: 新增项第一帧完全可见

父级 `initial={false}`、同步重渲染或 controls 启动让 initial 未被绘制。内层视觉节点显式设置初态，必要时跨过一次真实 paint 后启动。

### 坑 3: 该消失的元素分两批消失

所有 removed items 应在同一次比较中生成快照；快照 id 包含批次，并由 Motion Promise 统一清理，不使用 timeout。

### 坑 4: 文字换行或边框拉伸

外层只做 position layout，内层做 scale；Chip 使用 `w-max shrink-0 whitespace-nowrap`，不要让尺寸投影污染内容。

### 坑 5: 删除最后一项时退出仍然瞬间消失

列表根节点始终挂载；只在 `items.length === 0 && exitingSnapshots.length === 0` 时显示空状态。

### 坑 6: 外层容器高度与列表动效互相追赶

列表保持自然排版；外框高度需要动画时，单独使用测量内层 + 动画外层，参考 Case 5。

### 坑 7: 退出快照层级或裁剪错误

建立明确的 `relative + isolate` 快照坐标系；只在确实需要的尺寸动画层裁剪，避免祖先 `overflow-hidden` 截断旧位置。

---

## 动效参数建议

```tsx
const transitions = {
  layout: { type: "spring" as const, duration: 0.24, bounce: 0 },
  enter: { duration: 0.14, ease: [0.23, 1, 0.32, 1] as const },
  exit: { duration: 0.12, ease: [0.4, 0, 1, 1] as const },
};
```

- 筛选 Chip：`scale 0.6 ↔ 1` 可形成明确聚散感
- 克制型数据表：使用 `scale 0.96 ↔ 1` 或只做 opacity
- 退出略快于进入，避免旧内容拖住新布局
- layout 时长通常比 opacity/scale 稍长，让位置稳定落下

不要给同一属性同时配置 CSS transition 和 Motion transition。

---

## 验收清单

- [ ] key 使用稳定业务 id，没有使用数组 index
- [ ] 删除项第一个可见中间帧仍在旧坐标，且从 `opacity: 1` 开始
- [ ] 新增项第一个可见中间帧位于最终坐标，且从声明的进入首态开始
- [ ] 幸存项只移动到最终位置一次，没有二次重排
- [ ] 纯排序只触发位置动画，没有 entering / exiting 状态
- [ ] layout 与 scale 位于不同 DOM 节点
- [ ] 批量删除的所有退出项在同一批次开始退场
- [ ] 快速往返筛选后没有残留快照或旧 Promise 误清理
- [ ] 删除最后一项时，快照结束后空状态才出现
- [ ] 窄屏换行后旧 rect 与最终位置正确，文字没有动画中换行
- [ ] 滚动容器内的坐标换算正确
- [ ] 退出结束后快照 DOM 数量为 0
- [ ] reduced motion 下没有明显缩放或位置动画
- [ ] TypeScript、lint 和格式检查通过

---

## 推荐回答格式

```text
已修复列表增删与重排动画。

默认列表使用 popLayout 将退出项弹出布局流；复杂 Flex/Grid 场景则把幸存项位置、进入视觉和退出快照分成三层。删除项在旧坐标完成退场，新增项在最终坐标入场，幸存项只执行一次 layout="position" 投影。清理由 Motion 完成信号驱动，并验证了批量增删、快速切换、最后一项与窄屏状态。
```
