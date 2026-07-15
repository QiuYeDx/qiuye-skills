# Validation Workflow

## 目录

- [验收原则](#验收原则)
- [静态检查](#静态检查)
- [确定性动画检查](#确定性动画检查)
- [视觉矩阵](#视觉矩阵)
- [交互与生命周期](#交互与生命周期)
- [无障碍与 reduced motion](#无障碍与-reduced-motion)
- [性能与浏览器](#性能与浏览器)
- [交付前清理](#交付前清理)

## 验收原则

不要只看动画是否“能动”。几何转场最常见的错误发生在首帧、中间帧、提交帧、取消帧和清理帧，而最终静态页面往往完全正常。

实施代码后必须：

1. 运行项目已有的类型检查、lint 和相关测试。
2. 使用项目指定的包管理器和版本；不要因验证命令意外改写 lockfile。
3. 启动真实页面，在浏览器中检查至少 `0% / 25% / 50% / 75% / 100%` 五个阶段。
4. 覆盖 desktop、mobile、亮暗主题、reduced-motion 和至少一个回退路径。
5. 停止为验收启动的开发服务，并确认没有遗留进程。

## 静态检查

检查实现是否满足：

- source、target、cover 的 DOM 顺序和 z-index 与设计定义一致。
- `clip-path`/mask 实际作用在应该被裁剪的层，不是恰好看起来相似的装饰层。
- mask 同时提供标准属性和项目目标浏览器需要的 `-webkit-` 属性。
- alpha/luminance 语义明确；SVG ids 唯一，units 明确。
- 同一属性只有一个动画 owner。
- 关键 overlay 不挂在会随路由卸载、带 transform/filter 或错误 overflow 的祖先下。
- 临时层不会与 dialog/popover 的 top layer 产生错误预期。
- TypeScript 没有用宽泛断言掩盖错误 property 或 animation 类型。

## 确定性动画检查

优先给组件提供只在开发/测试环境启用的 progress 控制，使几何直接由 `0..1` 推导。这样能固定任意中间帧，而不是依赖 timeout 截图。

没有测试接口时，可在测试页暂停 WAAPI/CSS animations 并设置时间：

```ts
const animations = document.getAnimations();
for (const animation of animations) animation.pause();

for (const progress of [0, 0.25, 0.5, 0.75, 1]) {
  for (const animation of animations) {
    const timing = animation.effect?.getComputedTiming();
    const duration = Number(timing?.duration ?? 0);
    animation.currentTime = duration * progress;
  }
  // Capture screenshot and inspect pixels here.
}
```

注意：

- View Transition pseudo-element animations 和框架 spring 不一定都能用同一方式固定。必要时使用测试模式的线性 duration/progress，而不是 sleep 猜时刻。
- Spring 的 nominal duration 不代表每个浏览器上的视觉进度线性。中间帧验收应关注几何覆盖和层关系，不要把 spring 当线性时间轴。
- 截图前等待两次 RAF，让 style 和 paint 稳定；不要等待一个任意的长 timeout。

## 视觉矩阵

至少检查：

| 维度 | 样本 |
|---|---|
| viewport | 窄手机、常规 desktop、宽且矮的 desktop |
| origin | 中心、四角附近、容器边界、键盘触发的语义中心 |
| frame | 首帧、两个中间帧、完整覆盖/提交帧、清理后 |
| theme | light、dark、高对比度（项目支持时） |
| content | 短页面、长页面、图片未缓存、字体首次加载 |
| direction | forward、back/close（若产品支持） |

逐项观察：

- origin 是否与触发器或设计锚点对齐。
- 圆/多边形的内外内容是否正确，没有 source/target 反转。
- 所有角都覆盖，没有 `1px` 露角、接缝、抗锯齿底色或 overflow 裁切。
- 第一帧没有完整 target 闪现，最后一帧 cleanup 没有闪回 source。
- 主题背景、品牌色、文字和媒体在中间帧保持正确，不受 blend/filter 污染。
- 固定 header、sticky 元素、portal、dialog、popover 和滚动条没有突然跨层。
- viewport resize/orientation change 后不使用旧半径。

用截图做像素检查时，在预期始终由 cover/source 遮挡的角落取样，并在预期揭示区域取样。单纯判断 canvas/screenshot 非空不能发现层反转。

## 交互与生命周期

主动制造以下情况：

- 快速双击或连续触发两个不同 target。
- 动画每个阶段分别触发取消、后退、关闭或新导航。
- 在 covering、covered、revealing 阶段 resize/旋转。
- 动画中卸载组件或让 `commit()` reject。
- target 数据慢、图片慢、字体首次加载。
- 页面切到后台再回来。

每次都确认：

- 当前 token/controller 独占状态，旧事务的 cleanup 不会删除新事务样式。
- 页面最终只停在完整 source 或完整 target，不存在半遮罩永久状态。
- 交互锁、`inert`、disabled、focus 和滚动策略都恢复。
- `[data-transition-cover]` 等临时节点数量符合设计，没有每次触发累积。
- `document.getAnimations()` 中没有本组件遗留的 running animation。
- 没有残留 RAF、timer、observer、matchMedia listener 或 Motion subscription。

检查命中测试时，在被遮和已揭示区域分别使用真实点击，必要时用 `document.elementFromPoint(x, y)` 辅助确认。不要仅根据 `pointer-events: none` 推断交互正确。

## 无障碍与 reduced motion

- 用键盘触发转场，确认没有 pointer coordinate 时仍选择稳定 origin。
- source/target 共存时检查 tab 顺序，只允许当前有效内容获得焦点。
- route 完成后检查焦点位置和页面标题/announcement 是否遵循项目惯例。
- 装饰层不出现在 accessibility tree；真实 progress 才公开数值。
- 模拟 `prefers-reduced-motion: reduce`，确认直接提交或短淡入淡出，并且 cleanup 仍执行。
- reduced-motion 分支不能跳过业务 `commit()`、焦点恢复或错误处理。

Playwright 可使用：

```ts
await page.emulateMedia({ reducedMotion: "reduce", colorScheme: "dark" });
```

同时测试切回 `no-preference`，避免 media listener 或缓存状态污染后续用例。

## 性能与浏览器

至少在项目主要浏览器做一次真实运行；使用 mask、SVG filter、backdrop-filter 或 WebGL 时，补测 Safari/WebKit 和目标移动设备。

记录或检查：

- 动画期间是否出现长任务、连续大面积 paint、掉帧或纹理内存突增。
- 大型 `mask-image` 是否比简单 `clip-path`/transform 明显更贵。
- `will-change` 是否真的改变合成行为；无证据则删除。
- 高 DPR 手机上软边、锯齿和 Canvas 尺寸是否正确。
- feature detection 失败时是否仍提交 target，并落到简短 fallback。
- 外部 SVG/media 的 CORS 或加载失败是否会把内容完全隐藏。

不要仅用开发环境的热更新页面判断性能；开发构建、React Strict Mode 和调试工具会改变时序。必要时使用项目现有 preview/production build 复核。

## 交付前清理

- 移除调试 progress、临时按钮、强制 duration、outline 和 screenshot hook，除非它们是正式测试设施。
- 停止本次启动的所有前端开发/preview 服务，不要结束用户原本已运行且不属于本次任务的进程。
- 确认验证未意外修改 lockfile、构建配置、截图目录或生成产物。
- 汇报实际运行的检查、未覆盖的浏览器/设备和仍存在的风险。
