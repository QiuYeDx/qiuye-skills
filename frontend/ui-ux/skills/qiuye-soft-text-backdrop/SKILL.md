---
name: qiuye-soft-text-backdrop
description: >-
  Add natural text separation over images, particles, canvas, or 3D scenes using
  a soft text shadow and a local feathered backdrop (scrim). Use for Hero copy,
  introductory text, 文字背后的自然阴影, 文字与背景分离, 柔和文字衬底,
  or improving text readability over visual effects. Covers theme-aware colors,
  stacking, responsive falloff, and existing entrance animations. Not for card
  elevation shadows, decorative glows, glass blur, or scroll-edge fade masks.
---

# 自然文字衬底

让文字从复杂画面中自然浮现：贴近字形的柔和阴影保护轮廓，文字背后的局部渐隐衬底降低背景干扰。衬底应融入画面，周围的图片、粒子或场景仍然可见。

## 接入判断

- 先读目标文字、背景和现有主题样式；有相似效果时沿用它的色彩与强度。保留文案、排版、场景及原有定位。
- 低干扰背景可只用 `text-shadow`；点阵、线条或明暗变化穿过多行文字时，用下面的双层方案。
- 识别实际承载面颜色。深色面上的浅字配深色衬底，浅色面上的深字配浅色衬底。若图片上固定白字，使用配套的深色衬底，不要随页面浅色主题变白。
- 默认不引入依赖、主题检测 JS、Canvas 后处理或额外循环动画。CSS 变量随现有主题切换即可。

## 最小实现

将类加在整段文字或紧凑文案组上；多行共用一个衬底。以下示例假定 `--background` 是合法 CSS 颜色，并与文字所在承载面一致；旧式 HSL 通道变量需映射为 `hsl(var(--background))`。颜色和布局沿用目标项目。

```html
<p class="soft-copy">前端工程与界面体验，让系统能力与审美表达共同生长。</p>
```

```css
.soft-copy {
  --copy-surface: var(--background);
  --copy-backdrop-inset: -32px -16px;
  --copy-backdrop-opacity: 0.9;
  position: relative;
  isolation: isolate;
  text-shadow: 0 2px 20px var(--copy-surface);
}

.soft-copy::before {
  content: "";
  position: absolute;
  z-index: -1;
  inset: var(--copy-backdrop-inset);
  background: radial-gradient(
    ellipse,
    var(--copy-surface) 25%,
    transparent 72%
  );
  opacity: var(--copy-backdrop-opacity);
  pointer-events: none;
}
```

已有 `position: absolute / sticky` 的文案保留其定位，不被示例的 `relative` 覆盖。类应作用于 block 或 inline-block 的稳定文字容器，避免直接挂在跨行 inline 文本或每个动画字符上。原项目若没有限宽，按实际文案范围设置容器，避免遮罩跟随整屏空白扩散。

## 必须保留的结构

- `isolation: isolate` 将负层级伪元素约束在文案内部，绘制于文字之后、外部背景之前。文案整体仍须处于媒体之上；它不能越过外层兄弟的更高层级。
- `pointer-events: none` 仅用于衬底，保留文字选择、链接与按钮交互。使用真实衬底元素时加 `aria-hidden="true"`，不要复制一份文字做阴影。
- `opacity` 调整衬底本身。不要给整段文字降透明度来弱化阴影，否则会同时削弱可读性。
- 渐变负责柔化边界，无需额外 `filter: blur()`。不要在文字上加静态模糊，也不要用 `mask-image` 把文字一起淡掉。
- 衬底保持透明边缘，不添加矩形底色、边框、圆角面板或彩色光晕。`box-shadow` 描绘盒子轮廓，无法替代这里的字影与局部衬底。

## 调参顺序

1. **颜色与基础对比度**：先确认文字在纯承载面上已清楚可读，再确认衬底色正确。阴影不能补救本身过淡的文字。
2. **覆盖范围**：让衬底中心覆盖主要文字，边缘落到文字外围。先调容器宽度与 `inset`，再调不透明度。
3. **衬底强度**：以 `0.9` 为短简介起点；保留背景纹理，避免抹出明显斑块。降低强度前确认最繁杂背景帧仍然可读。
4. **渐变与字影**：`25% / 72%` 和 `0 2px 20px` 是已用实例的起点，不是通用常量。边缘字仍受干扰时微调覆盖或增加较短字影，避免堆成描边。

渐变百分比沿椭圆半径计算，不代表容器中相同比例的矩形区域。窄屏换行、文案加长或容器宽高比改变后，需要重新观察首末行和两侧文字。

需要大型 Hero 参数、固定浅字的图片场景、显式层级替代方案或问题排查时，读取 [实现与调参参考](references/implementation.md)。

## 动画与验证

- 文字已有入场动画时，让衬底放在同一文案容器内，随文字一起显现；不要另建一个有独立延迟的遮罩。逐字动画使用共同父容器承载衬底。
- 只有原交互确实需要时才让衬底强度随滚动变化。复用现有进度和 reduced-motion 行为，不为静态可读性效果新增滚动监听。
- 检查窄屏和桌面、深浅主题、真实换行及 200% 缩放：无横向溢出、硬边、文字遮挡或布局变化。负 inset 会产生可滚动溢出，即使伪元素不可点击。
- 对动态背景检查繁杂帧和亮度极端帧，等待已有入场完成后再看最终效果；检查动画中途是否闪现整块衬底。保持原 reduced-motion 设置可用。
- 检查文本选择、链接点击、焦点轮廓及祖先裁剪；必要时使用显式层级方案，不要靠全局 `overflow-x: hidden` 掩盖问题。
- 使用浏览器截图比较效果开关，确认背景在文字区域的干扰下降、外围视觉仍保留。计算样式和 lint 只能检查接入，不能证明自然程度或文字对比度达标；按项目可访问性目标核查实际合成背景上的对比度。
- 使用项目现有工具做相关检查。仅修改 CSS 不需要新增 JS 单元测试；完成后停止本次启动的预览服务。
