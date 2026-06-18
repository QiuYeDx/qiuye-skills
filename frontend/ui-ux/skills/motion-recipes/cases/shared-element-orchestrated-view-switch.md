# Case 3: 共享元素迁移与辅助内容编排切换

## 目标

在固定尺寸容器中切换两套互斥视图，让两边共有的核心元素通过 `layoutId` 连续迁移，同时让其余内容自然退场和分批入场。

重点解决：

- Header、Toolbar、Compact / Expanded 面板之间的共享品牌或标题迁移
- `layoutId` 元素被父级 opacity / filter 污染，过渡态颜色异常
- 新视图辅助内容首帧闪现，旧视图辅助内容延迟到最后一帧才消失
- 共享文字带渐变或扫光时，投影层出现透明填充、深灰文字或重复高亮

---

## 适用场景

典型需求表述：

- 「滚动后把品牌 Header 切换成导航操作栏，品牌名要平滑移动过去」
- 「两个视图都有同一个标题，希望用 layoutId 无缝过渡」
- 「共享元素在迁移，但旁边按钮会突然出现或消失」
- 「深色模式下 layoutId 过渡态文字变黑」
- 「带渐变文字 / 扫光效果的 shared element 过渡异常」

典型 UI：品牌 Header、响应式 Toolbar、搜索框展开、播放器 Mini / Full 模式、卡片到详情标题迁移、命令栏模式切换。

---

## 核心设计原则

### 1. 固定外壳，只切换内部视图

如果组件本身不需要改变高度，给外壳一个稳定尺寸，让 Motion 只处理内部元素的位置和透明度。

```tsx
<header className="h-14">
  <div className="relative h-full">
    {/* 两套 absolute 视图 */}
  </div>
</header>
```

不要让 Header 高度和内部视图一起切换，否则页面内容偏移、shared layout 投影和辅助内容动画会同时竞争。

### 2. 共享元素必须是同一个组件、同一个 `layoutId`

把两端共有的标题或品牌抽成一个组件。字体、颜色、扫光结构和投影配置只维护一份，端点只传字号等布局差异。

```tsx
const sharedTransition = {
  duration: 0.42,
  ease: [0.22, 1, 0.36, 1] as const,
};

function SharedTitle({ className }: { className?: string }) {
  return (
    <motion.span
      layoutId="header-shared-title"
      layoutCrossfade={false}
      transition={sharedTransition}
      className={cn(
        "relative inline-block whitespace-nowrap text-foreground",
        className
      )}
    >
      <span className="relative z-10">QiuVision</span>
      <TitleShimmer>QiuVision</TitleShimmer>
    </motion.span>
  );
}
```

使用 `LayoutGroup` 限定共享布局作用域，避免页面上其他同名 `layoutId` 参与投影。

### 3. 不要在共享元素的祖先上动画 opacity 或 filter

Motion 的 shared layout 投影会暂时跨越两个 React 分支。若整个分支容器执行淡出或 blur，共享元素也会被一起变暗、变模糊。

```tsx
// 避免：SharedTitle 会继承整个视图的透明度和滤镜
<motion.div exit={{ opacity: 0, filter: "blur(4px)" }}>
  <SharedTitle />
  <Navigation />
</motion.div>
```

正确做法：父级只负责稳定定位或很轻的几何位移；把 opacity / filter 动画下沉到非共享内容。

```tsx
<motion.div exit={{ y: 3 }}>
  <SharedTitle />
  <motion.nav exit={satelliteExit}>...</motion.nav>
</motion.div>
```

### 4. 把非共享内容当作“卫星内容”独立编排

Logo、导航、操作按钮、slogan 都不是 shared element。它们必须拥有自己的 `initial / animate / exit`，不能依赖父分支卸载时机。

```tsx
const satelliteInitial = {
  opacity: 0,
  y: 3,
  filter: "blur(4px)",
};

const satelliteExit = {
  opacity: 0,
  y: -2,
  filter: "blur(3px)",
  transition: {
    duration: 0.14,
    ease: [0.4, 0, 1, 1] as const,
  },
};

function satelliteEnter(delay: number) {
  return {
    opacity: 1,
    y: 0,
    filter: "blur(0px)",
    transition: {
      duration: 0.22,
      delay,
      ease: [0.22, 1, 0.36, 1] as const,
    },
  };
}
```

退出要立即开始且短于进入。进入按视觉阅读顺序错开 `40–80ms`，让共享主角先建立连续性。

### 5. 文字颜色与渐变填充必须分层

带 `background-clip: text` 的扫光层通常使用 `-webkit-text-fill-color: transparent`。不要把这些样式放在 shared element 根节点，否则投影快照可能继承透明填充或错误颜色。

```tsx
function TitleShimmer({ children }: { children: React.ReactNode }) {
  return (
    <motion.span
      aria-hidden="true"
      className="pointer-events-none absolute inset-0"
      style={{
        color: "transparent",
        WebkitTextFillColor: "transparent",
        backgroundImage:
          "linear-gradient(105deg, transparent 35%, #D6C8A6 50%, transparent 65%)",
        backgroundSize: "200% 100%",
        backgroundClip: "text",
        WebkitBackgroundClip: "text",
      }}
      animate={{ backgroundPosition: ["-50% center", "-250% center"] }}
      transition={{
        duration: 1.5,
        repeat: Infinity,
        repeatDelay: 2,
        ease: "linear",
      }}
    >
      {children}
    </motion.span>
  );
}
```

基础文字层显式使用语义前景色；必要时在 shared 根节点和基础文字层同时声明：

```tsx
style={{
  color: "var(--foreground)",
  WebkitTextFillColor: "currentColor",
}}
```

slogan 的扫光应使用自己的 overlay 和动画实例，不要与共享标题共用同一个 `layoutId` 或 DOM 层。

---

## 推荐实现模板

```tsx
import { AnimatePresence, LayoutGroup, motion } from "motion/react";

export function SwitchingHeader({ compact }: { compact: boolean }) {
  return (
    <header className="h-14 border-b bg-background/95">
      <div className="relative mx-auto h-full max-w-7xl px-6">
        <LayoutGroup id="switching-header">
          <AnimatePresence initial={false}>
            {!compact ? (
              <motion.div
                key="brand"
                className="absolute inset-0 flex items-center justify-center"
                initial={{ y: -3 }}
                animate={{ y: 0 }}
                exit={{ y: -3 }}
                transition={sharedTransition}
              >
                <div className="flex flex-col items-center gap-0.5">
                  <SharedTitle className="text-xl" />
                  <motion.div
                    initial={satelliteInitial}
                    animate={satelliteEnter(0.18)}
                    exit={satelliteExit}
                  >
                    <SloganWithIndependentShimmer />
                  </motion.div>
                </div>
              </motion.div>
            ) : (
              <motion.div
                key="operations"
                className="absolute inset-0 flex items-center justify-between"
                initial={{ y: 3 }}
                animate={{ y: 0 }}
                exit={{ y: 3 }}
                transition={sharedTransition}
              >
                <div className="flex items-center gap-3">
                  <motion.span
                    initial={satelliteInitial}
                    animate={satelliteEnter(0.1)}
                    exit={satelliteExit}
                  >
                    <Logo />
                  </motion.span>
                  <SharedTitle className="text-base" />
                </div>

                <motion.nav
                  className="absolute left-1/2 flex -translate-x-1/2"
                  initial={satelliteInitial}
                  animate={satelliteEnter(0.14)}
                  exit={satelliteExit}
                >
                  {navItems.map((item) => (
                    <a key={item.href} href={item.href} className="whitespace-nowrap">
                      {item.label}
                    </a>
                  ))}
                </motion.nav>

                <motion.div
                  initial={satelliteInitial}
                  animate={satelliteEnter(0.18)}
                  exit={satelliteExit}
                >
                  <Actions />
                </motion.div>
              </motion.div>
            )}
          </AnimatePresence>
        </LayoutGroup>
      </div>
    </header>
  );
}
```

`AnimatePresence` 保持默认同步模式，让 shared element 的两个端点能在切换窗口中完成匹配。不要使用 `mode="wait"` 把新端点推迟到旧视图完全退出之后。

---

## AI Agent 执行步骤

### Step 1: 列出共享元素和卫星内容

先明确：

- 哪个元素在两个视图中语义相同，需要连续迁移
- 哪些元素只属于其中一个视图，需要独立进入或退出
- 外壳尺寸是否应该稳定

### Step 2: 抽取共享组件

确保两个端点渲染同一个组件，并具有：

- 相同 `layoutId`
- 相同文字、颜色和效果层结构
- 稳定的 `LayoutGroup`
- `layoutCrossfade={false}`，避免两份文字交叉淡化产生重影

### Step 3: 清理祖先动画污染

沿 shared element 向上检查所有祖先。移除会影响共享元素的：

- `opacity`
- `filter`
- `color`
- `WebkitTextFillColor`
- 大范围 CSS `transition-all`

### Step 4: 给卫星内容添加独立时序

逐组添加 `initial / animate / exit`。确认：

- 新视图首帧 opacity 为 0
- 旧视图切换后立刻开始 exit
- shared element 不在这些 motion wrapper 内

### Step 5: 验证双向过渡

两个方向都至少采样：

- 第一帧或约 `16ms`
- 中间态约 `80–200ms`
- 动画结束

分别检查共享元素、旧卫星内容、新卫星内容和独立效果层。

---

## 常见坑与修复

### 坑 1: 操作区第一帧瞬间出现

**原因**：操作区只依靠条件渲染，没有自己的 `initial`；或者 `AnimatePresence initial={false}` 被误解为所有后续入场也跳过 initial。

**修复**：给操作区各组显式设置 `initial={satelliteInitial}`。

### 坑 2: 操作区一直存在，最后突然消失

**原因**：父分支为了保护 shared element 没有 opacity exit，但子内容也没有独立 exit。

**修复**：把 `exit={satelliteExit}` 放到 Logo、nav、actions 等非共享节点上。

### 坑 3: 共享标题过渡态变灰或变黑

**原因**：祖先 opacity / filter、主题颜色解析，或渐变文字的透明 fill 污染了投影层。

**修复**：

- shared element 脱离卫星内容的淡出 wrapper
- 根节点与基础文字层显式设置 `color: var(--foreground)`
- 基础文字使用 `WebkitTextFillColor: currentColor`
- 透明 fill 仅留在 absolute shimmer overlay

### 坑 4: 共享标题有两份金色高亮

**原因**：两端各自实现一套标题或交叉淡化，投影时同时可见。

**修复**：复用同一个标题组件，使用 `layoutCrossfade={false}`；效果层作为组件内部结构，不参与其他 `layoutId`。

### 坑 5: slogan 扫光被误删

**原因**：为消除标题的重复高亮，把所有扫光都当成共享效果处理。

**修复**：共享标题和 slogan 各自拥有独立 overlay。只有标题参与 shared layout，slogan 作为卫星内容独立退出和延迟进入。

### 坑 6: 菜单文字在紧凑 Header 中换行

**修复**：给导航容器稳定布局，菜单项和文字使用 `whitespace-nowrap`；必要时减少水平 padding，而不是压缩字体到不可读。

---

## 动效参数建议

| 部分 | 推荐参数 |
|---|---|
| 共享元素迁移 | `0.36–0.48s`，`[0.22, 1, 0.36, 1]` |
| 卫星内容退出 | `0.12–0.16s`，无 delay |
| 卫星内容进入 | `0.18–0.26s`，delay `0.08–0.2s` |
| 位移 | `2–4px` |
| blur | `3–4px`，只用于卫星内容 |

共享元素负责空间连续性，辅助内容只做轻微淡入、位移和模糊，不要让所有元素同时大幅运动。

---

## 验收清单

- [ ] 外壳高度在两种视图之间保持稳定
- [ ] shared element 双向切换都连续移动，没有跳变或交叉重影
- [ ] shared element 的祖先没有 opacity / filter 动画
- [ ] 新视图卫星内容第一帧不可见，随后按顺序进入
- [ ] 旧视图卫星内容切换后立即开始退出，不会拖到最后一帧消失
- [ ] 深色和浅色模式的过渡态文字颜色都正确
- [ ] 基础文字与 shimmer overlay 的 fill / color 互不污染
- [ ] slogan 等独立效果仍正常播放
- [ ] 导航文字不换行，固定容器内没有重叠
- [ ] 正向与反向都检查了开始、中间、结束三个阶段
- [ ] TypeScript、lint 和 build 通过

---

## 推荐回答格式

```text
已完成共享元素编排式切换：

- 两个视图复用同一个 shared title 组件，通过 layoutId 连续迁移。
- Header 外壳保持固定高度；shared title 的祖先不再参与 opacity / filter 动画。
- Logo、导航、操作按钮和 slogan 作为卫星内容独立退场并延迟入场，修复首帧闪现与末帧突消。
- 文字基础层和扫光 overlay 已隔离，并验证深色 / 浅色模式及双向过渡。
```
