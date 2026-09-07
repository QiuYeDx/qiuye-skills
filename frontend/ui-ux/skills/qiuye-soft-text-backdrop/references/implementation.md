# 实现与调参参考

## 来自 QiuVision 的两处实例

以下是 2026-09-07 提取的效果参数。源路径用于追溯，不要求目标项目存在这些文件或依赖 QiuVision。

| 属性 | 首页城市 Hero | 关于页简介 |
| --- | --- | --- |
| 源文件 | `components/home/lujiazui/city-hero.css` | `components/about/about-hero.css` |
| 文案容器 | `.city-hero-copy`，绝对定位的标题与简介组 | `.about-hero-description`，相对定位的段落 |
| 承载色 | `var(--background)` | `var(--background)` |
| 字影 | `0 2px 20px var(--background)` | 同左 |
| 衬底 inset | `-40px -110px -50px` | `-32px -16px` |
| 渐变 | `radial-gradient(ellipse, var(--background) 25%, transparent 72%)` | 同左 |
| 衬底 opacity | `calc(0.2 + var(--city-intro) * 0.7)` | `0.9` |
| 层级 | 文案 `isolation: isolate`，伪元素 `z-index: -1` | 同左 |

首页 `--city-intro` 从 1 向 0 变化时，衬底由 0.9 降至 0.2，配合现有场景展开。它不是透明度固定为 0.2 的预设。关于页衬底与原 `BlurFade` 一起入场，保持固定强度即可。

自然感来自承载色统一、渐变越过文字后逐渐消失，以及较小偏移的字影。它不依赖特定字体、品牌颜色、Next.js 或动画库。

## 按布局选择范围

短简介直接采用入口模板，然后按真实容器调整。关于页原容器最多 672px 宽，手机页面左右各留 24px，16px 的水平扩展没有超出视口。

大标题组可以扩大垂直与水平覆盖，但首页的 110px 水平扩展是场景参数，不能原样复制到靠近屏幕边缘的段落。该首页有裁剪场景的 viewport，移植时需重新验证衬底边缘与焦点是否被截断。

例如，目标项目的桌面文案两侧至少有 80px 空间时，可以在入口模板上添加以下可选变体。这里的断点与数值是迁移建议，并非原首页已验证参数：

```css
@media (min-width: 1024px) {
  .soft-copy--hero {
    --copy-backdrop-inset: -40px -80px -50px;
  }
}
```

文本过长时优先匹配文案块尺寸。不要给整节、整个宽屏容器或每行文字各放一个高强度渐变；前者覆盖过多场景，后者会产生叠加亮斑或暗斑。

## 主题与图片

承载色与文字前景色是一对。组件处于局部反色区域时，应使用该区域的 surface token，而不是全局背景。固定白字覆盖照片时可局部覆盖变量，例如下面的颜色只是示例，应换成项目现有的媒体文字 token：

```css
.soft-copy--photo {
  --copy-surface: #161616;
  color: #f5f5f5;
}
```

先应用 `.soft-copy`，再让同一元素的 `.soft-copy--photo` 规则覆盖它。图片或视频的亮区可能仍穿过渐变边缘；根据实际素材调范围和强度，必要时调整文字位置。对比度验收应包含文字覆盖的最不利背景，不能仅测试深浅色开关。

## 显式层级方案

当 `::before` 已有业务用途，或框架样式使负层级难以维护时，可以用装饰元素和内容容器明确顺序。该方案替代入口模板，不要同时给 shell 添加 `.soft-copy` 产生两层衬底。

```html
<div class="copy-shell">
  <div class="copy-backdrop" aria-hidden="true"></div>
  <div class="copy-content">
    <p>让文字与画面保有清晰而柔和的距离。</p>
    <a href="#details">了解更多</a>
  </div>
</div>
```

```css
.copy-shell {
  --copy-surface: var(--background);
  position: relative;
  isolation: isolate;
}

.copy-backdrop {
  position: absolute;
  z-index: 0;
  inset: -32px -16px;
  background: radial-gradient(ellipse, var(--copy-surface) 25%, transparent 72%);
  opacity: 0.9;
  pointer-events: none;
}

.copy-content {
  position: relative;
  z-index: 1;
  text-shadow: 0 2px 20px var(--copy-surface);
}
```

shell 的外部层级仍需高于媒体。使用现有布局控制内部段落 margin，避免 margin collapse 让 shell 的高度与文字覆盖范围不符。

## 按现象排查

| 现象 | 检查和处理 |
| --- | --- |
| 衬底完全消失 | 确认 `content`、定位、颜色变量和 `isolation`；再看文案整体是否被更高层级媒体遮住。 |
| 衬底变成矩形或硬边 | 检查祖先 `overflow`、`clip-path`、mask；确认没有额外不透明背景。衬底应在被裁剪前已经淡出。 |
| 中央清楚、两侧仍杂乱 | 调整容器与水平扩展或渐变中心/停止点，不要只提升中央 opacity。 |
| 浅色模式有黑边 | 检查衬底与字影是否都使用正确的承载色，是否继承了旧的黑色 `drop-shadow`。 |
| 文字糊或像描边 | 检查静态 `filter: blur`、多重 `text-shadow` 与原入场滤镜是否恢复，减少短而浓的阴影叠加。 |
| 手机横向滚动 | 用实际 viewport 与 scrollWidth 查溢出源；收窄负 inset 或增加合法布局留白，保留焦点可见性。 |
| 动画时衬底跳出 | 让衬底与整组文字共享动画容器，避免逐字各建伪元素；检查开始、结束及中断状态。 |
| 链接点不到 | 检查装饰层的 `pointer-events` 和兄弟层级；不要禁用整个文案的指针事件。 |

如果需要同屏开关对比，仅在开发者工具中临时禁用字影和衬底；不要往产品页面加入调参开关或实现说明。
