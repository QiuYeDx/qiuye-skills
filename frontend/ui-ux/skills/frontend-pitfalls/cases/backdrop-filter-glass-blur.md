# Case 1: backdrop-filter 背景模糊与玻璃态浮层

## 目标

稳定实现移动端 Header 下拉菜单、玻璃态浮层、透明导航栏、HUD 工具条等 `backdrop-filter` / `backdrop-blur` UI，避免「class 写对但不模糊」「动画结束后才突然变模糊」「离场最后一帧边框硬消失」「父子嵌套 blur 失效」等问题。

## 适用场景

- 需求中出现 `backdrop-filter`、`backdrop-blur`、玻璃态、毛玻璃、透明导航栏、移动端菜单、HUD 浮层。
- 用户反馈「看起来只是半透明，没有模糊底下内容」。
- 浮层入场过程中没有 blur，动画结束后突然出现强模糊。
- 浮层离场时背景淡出了，但边框、阴影或玻璃层在最后一帧硬消失。
- Chrome、Safari、移动端浏览器表现不一致。

## 核心判断

`backdrop-filter` 模糊的是元素背后的已绘制像素，不是元素自己的背景。它依赖透明背景、背后可取样内容、浏览器合成层、Backdrop Root、层叠上下文和裁切区域。

看到半透明覆盖层不等于 `backdrop-filter` 已经生效。

## 排查顺序

1. 确认元素有透明或半透明背景，且后方真的有可被取样的页面内容。
2. 同时设置 `backdrop-filter` 和 `-webkit-backdrop-filter`。
3. 检查父级是否也有 `backdrop-filter`、`filter`、`transform`、`opacity`、`contain`、`isolation` 等会改变合成上下文的属性。
4. 检查承载 blur 的元素是否正在做 `height`、`clip-path`、`overflow` 相关动画。
5. 检查是否只用 `opacity` 淡入一个已经满强度的 blur 层。
6. 检查静态 `border`、阴影、背景 tint 是否放在了离场动画容器上。
7. 在 DevTools 里确认最终元素是否真的生成了 `backdrop-filter` 样式。
8. 临时把背景透明度调低、blur 调高，观察是否真的模糊底层内容。

## 推荐结构

把玻璃态浮层拆成三层：

1. 外层容器：只负责定位、生命周期、尺寸和 `z-index`。
2. 玻璃背景层：只负责背景 tint、`backdrop-filter` 和相关离场动画。
3. 内容层：只负责真实交互内容，只动画 `opacity` / `transform`。

Header 自身如果也需要玻璃效果，把 Header 背景层和菜单背景层做成 sibling，不要让「带 blur 的父元素」包住「带 blur 的子浮层」。

## 推荐实现模板

```tsx
import { AnimatePresence, motion } from "motion/react";

const GLASS_EASE = [0.22, 1, 0.36, 1] as const;

const glassHidden = {
  backgroundColor: "color-mix(in oklab, var(--background) 0%, transparent)",
  backdropFilter: "blur(0px) saturate(100%)",
  WebkitBackdropFilter: "blur(0px) saturate(100%)",
};

const glassVisible = {
  backgroundColor: "color-mix(in oklab, var(--background) 76%, transparent)",
  backdropFilter: "blur(20px) saturate(180%)",
  WebkitBackdropFilter: "blur(20px) saturate(180%)",
};

export function MobileGlassMenu({
  open,
  children,
}: {
  open: boolean;
  children: React.ReactNode;
}) {
  return (
    <AnimatePresence initial={false}>
      {open && (
        <motion.div
          className="absolute inset-x-0 top-full z-20 overflow-hidden"
          initial="hidden"
          animate="visible"
          exit="hidden"
        >
          <motion.div
            className="absolute inset-0"
            variants={{
              hidden: glassHidden,
              visible: glassVisible,
            }}
            transition={{ duration: 0.28, ease: GLASS_EASE }}
            aria-hidden="true"
          />

          <motion.div
            className="absolute inset-x-0 bottom-0 h-px bg-border"
            variants={{
              hidden: { opacity: 0 },
              visible: { opacity: 1 },
            }}
            transition={{ duration: 0.24, ease: GLASS_EASE }}
            aria-hidden="true"
          />

          <motion.div
            className="relative"
            variants={{
              hidden: { opacity: 0, y: -4 },
              visible: { opacity: 1, y: 0 },
            }}
            transition={{ duration: 0.2, ease: GLASS_EASE }}
          >
            {children}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
```

Header 场景推荐这样组织：

```tsx
<header className="sticky top-0 z-50">
  <div
    className="absolute inset-x-0 top-0 h-14 bg-background/80"
    style={{
      backdropFilter: "blur(16px) saturate(180%)",
      WebkitBackdropFilter: "blur(16px) saturate(180%)",
    }}
    aria-hidden="true"
  />

  <div className="relative z-10 h-14">{/* header content */}</div>

  <MobileGlassMenu open={open}>{/* menu content */}</MobileGlassMenu>
</header>
```

## 常见坑与修复

### 坑 1: 父元素和子元素嵌套 backdrop-filter

错误模式：

```tsx
<header className="backdrop-blur-md bg-background/60">
  <div className="absolute top-full backdrop-blur-md bg-background/60">
    menu
  </div>
</header>
```

原因：

- 带 `backdrop-filter` 的父元素可能形成独立合成层或 Backdrop Root。
- 子元素再次做 `backdrop-filter` 时，可能无法继续取样真实页面内容。

修复：

- 父容器只负责定位和层级。
- Header 背景层、菜单背景层拆成独立 sibling 层。
- 交互内容放在 `relative` 内容层里。

### 坑 2: 对承载 blur 的元素做 height 动画

错误模式：

```tsx
<motion.div
  initial={{ height: 0, opacity: 0 }}
  animate={{ height: "auto", opacity: 1 }}
  exit={{ height: 0, opacity: 0 }}
  className="overflow-hidden backdrop-blur-md bg-background/60"
>
  menu
</motion.div>
```

原因：

- `height: 0 -> auto` 会触发布局重算。
- `overflow-hidden` 会裁切背景取样区域。
- 浏览器可能等布局稳定后才重新合成 backdrop。

修复：

- 不动画玻璃层高度。
- 外层容器固定定位或由内容撑开。
- 内容层只做 `opacity` / `transform` 动画。
- 如果需要 blur 自然过渡，动画 `backdropFilter: blur(0px) -> blur(20px)`。

### 坑 3: 只用 opacity 淡入整个玻璃层

错误模式：

```tsx
<motion.div
  initial={{ opacity: 0 }}
  animate={{ opacity: 1 }}
  exit={{ opacity: 0 }}
  className="backdrop-blur-md bg-background/60"
>
  menu
</motion.div>
```

原因：

- `opacity` 作用在整个合成层。
- 某些浏览器会延后 backdrop 合成。
- 视觉上可能出现「透明层先出现，模糊随后跳出」。

修复：

- 玻璃层动画 `backdropFilter` 和 `WebkitBackdropFilter`。
- 背景 tint 的透明度同步过渡。
- 内容层单独做 `opacity` / `transform`。

### 坑 4: 静态 border 在离场结束时硬消失

错误模式：

```tsx
<motion.div exit={{ opacity: 0 }} className="border-b">
  menu
</motion.div>
```

原因：

- `border-b` 是静态样式。
- 组件卸载时边框会在最后一帧突然消失。

修复：

- 把边框线拆成独立的 1px `motion.div`。
- 让边框、背景 tint、阴影与玻璃层一起淡入淡出。

### 坑 5: 缺少 Safari / 移动端前缀

错误模式：

```tsx
style={{ backdropFilter: "blur(20px)" }}
```

修复：

```tsx
style={{
  backdropFilter: "blur(20px) saturate(180%)",
  WebkitBackdropFilter: "blur(20px) saturate(180%)",
}}
```

## AI Agent 执行步骤

1. 在项目里定位所有相关 `backdrop-filter`、`backdrop-blur`、`filter`、`opacity`、`overflow-hidden`、`height` 动画代码。
2. 判断 blur 是否挂在业务容器、父容器或同时包含内容和子浮层的容器上。
3. 如果存在父子嵌套 blur，重构为「定位容器 + 独立玻璃背景层 + 内容层」。
4. 如果 blur 层正在做高度或裁切动画，取消 blur 层高度动画，改为内容层位移/透明度动画。
5. 如果只用 opacity 淡入玻璃层，改为动画 `backdropFilter` / `WebkitBackdropFilter` 和背景 tint。
6. 把离场时可见的 border、阴影、分割线拆成独立可动画层。
7. 保持项目现有导入方式：项目已用 `framer-motion` 就沿用；新写 Motion v11+ 优先 `motion/react`。
8. 运行项目校验，至少检查 Chrome；涉及移动端或 Safari 反馈时，额外检查 Safari / 移动端视口。

## 验收清单

- 玻璃层有半透明背景，且同时设置 `backdropFilter` 和 `WebkitBackdropFilter`。
- 没有在父级 blur 容器内再嵌套子级 blur 浮层。
- 承载 blur 的层没有做 `height: 0 -> auto`、`clip-path` 或裁切驱动的入离场动画。
- 入场过程中 blur 是逐步增强，不是在动画结束后突然出现。
- 离场过程中背景 tint、分割线、边框、阴影同步淡出，没有最后一帧硬消失。
- 真实交互内容位于独立内容层，只动画 `opacity` / `transform`。
- DevTools 中最终目标元素能看到实际生成的 `backdrop-filter` 样式。
- Chrome、Safari 或目标移动端浏览器的表现没有明显不一致。

## 推荐回答格式

完成修复后向用户说明：

- 改了哪些层级结构。
- 移除了哪些会破坏 blur 合成的动画或嵌套。
- 如何验证了入场、离场和浏览器表现。
