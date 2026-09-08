# 渲染验收方法

## 选择证据，而不是堆数量

先写出本任务要排除的失败性质，再选择状态和测量。已有项目测试能覆盖时直接复用；不能运行时说明具体缺口，不伪造截图或用 mock 冒充原生流程。

| 对象 | 最有区分力的状态 | 观察/测量 |
| --- | --- | --- |
| 风格 | 相同主题和窗口下的目标页及参照页 | 组件变体、字体、色彩、圆角和密度关系 |
| 边距 | 有图标、有按钮和无操作的面板；相关折叠区 | 最终 padding、控件边缘、分隔线边缘；光学差异另外判断 |
| 圆角留白 | 四角附近的按钮/输入框、底栏首尾控件及其焦点态 | 每个靠角元素到相邻两条边的距离、内外曲线间的空白，不能只比较同方向 padding |
| 空间预算 | 正常数据量下的宽/窄窗口，包含上传、元数据和分页 | 各层高度及正文可见行数；横向闲置是否伴随不必要的竖向堆叠 |
| 数据行 | 相邻的一行、多行、长无空格内容 | 行高、各列距行顶偏移、操作目标尺寸 |
| 文件名 | 短、长、尾部相近、中英混合、极窄宽度 | 截断段、尾部可见、完整名称及辅助技术名称 |
| Tooltip | 实际悬停、键盘焦点、窗口边缘、长短文案 | 外框尺寸、最长行利用率、换行、位置、关闭行为 |
| 列表高亮 | 选中项旁边悬停另一项 | 间隔、边界、颜色和焦点轮廓 |
| 共享组件 | 消费页与实际使用的各个 variant | 局部覆盖、嵌套边距、窄窗口和状态组合 |

不必测试所有状态的笛卡尔积。优先选择可能改变布局的组合：最长文案 + 最窄受支持窗口、选中 + 相邻悬停、正文多行 + 操作按钮、Popover + 靠近窗口边缘。

## 截图前后

1. 用隔离配置和可识别 fixture，避免污染用户数据、剪贴板、登录态或真实服务。原生桥接依赖用项目实际运行环境验证；替代服务的证据需说明边界。
2. 等目标路由、数据、字体和已知 loading / 动画结束。不要仅凭固定 sleep 或 DOM 存在认定就绪。
3. 设置并确认实际窗口/视口、主题与语言。注意系统缩放、devicePixelRatio 和应用最小窗口约束。
4. 滚动真正承载内容的容器；查看目标矩形，确认固定标题栏和底栏没有遮挡本次验收对象。需要时补充组件截图，但它不能代替上下文截图。
5. 打开需要检查的 Tooltip / 菜单 / 折叠区。悬停测试应有真实移动轨迹；组件的 hover grace 区域可能需要后续 pointer move 才能完成关闭，不把一次瞬移造成的差异直接判成产品缺陷。
6. 亲自查看生成图。发现遮挡、加载或内容错误时修正取证，不把无效图归档成通过证据。
7. 最后一次代码修改后更新受影响证据，结束后关闭本次启动的进程。

## 几何检查范例

使用当前项目的测试工具。以下 Playwright 示例是测量思路，选择器、阈值及辅助文本结构需适配项目，不是可直接宣称“设计合格”的通用测试。

### 圆角附近的等距关系

例为右上角按钮。底栏右侧按钮应改为比较 bottom/right，左侧相应比较 left；以实际可见的圆角外壳为测量祖先，不能只量一个无边框的内部 flex 容器。下列数值以边框内沿为基准，圆角弧线仍需截图检查。

```ts
const insets = await action.evaluate(button => {
  const panel = button.closest('[data-qa="panel"]')!;
  const outer = panel.getBoundingClientRect();
  const inner = button.getBoundingClientRect();
  const style = getComputedStyle(panel);
  return {
    top: inner.top - outer.top - parseFloat(style.borderTopWidth),
    right: outer.right - inner.right - parseFloat(style.borderRightWidth),
    bottom: outer.bottom - inner.bottom - parseFloat(style.borderBottomWidth),
    left: inner.left - outer.left - parseFloat(style.borderLeftWidth),
  };
});
// 仅当设计约定要求这两个边距相等时比较；容忍约 1 CSS px 的舍入。
expect(Math.abs(insets.top - insets.right)).toBeLessThanOrEqual(1);
```

### Tooltip 内容利用率

选择只承载可见文本的元素，排除箭头和无障碍副本。若混有隐藏元素，先缩小测量对象，不能把整个组件的所有 Range rect 当成可见文本。

```ts
const geometry = await tooltipText.evaluate(element => {
  const range = document.createRange();
  range.selectNodeContents(element);
  const lines = [...range.getClientRects()];
  const box = element.getBoundingClientRect();
  return {
    width: box.width,
    longestLine: Math.max(0, ...lines.map(line => line.width)),
    rightmostText: Math.max(box.left, ...lines.map(line => line.right)),
  };
});
```

将可见文本宽度与 Tooltip 内容框比较，结合词长判断整块空白是否合理。对确实换行的长文件名样本，可用“最长行仍远小于内容框”找嫌疑，再读 `text-wrap`、`min-width`、padding 和布局父级。不要给所有语言硬设同一个利用率门槛，也不要要求最后一行填满。

### 密度和组合状态

对短行和多行分别记录行高，以及编号、时间、文本和操作的 `top - row.top`；用 Range 的首行矩形观察文本基线关系。行内按钮的视觉图形和点击区域需分别检查。

相邻项间隔是 `next.top - previous.bottom`；它仅对设计要求离散高亮的列表有意义，不能据此否定本来连续的表格选区。横向溢出还应检查实际内容容器，避免 `overflow-x: hidden` 掩盖问题。

## 让测试真正检出问题

- 边距缺陷：比较相关边，不只断言它们都有 padding。
- 靠角留白：加入水平 12px、垂直 4px 这类所有值合法却关系不均衡的反例；不同值仅作样本，不是全局禁用这些 token。
- 空间分配：在相同窗口和数据下比较工作区可见行数与上部占用；无溢出但元数据占高、横向闲置的布局仍需检出。
- Tooltip 缺陷：检验真实长文本的排版，不只断言组件出现或宽度小于上限。
- 多行缺陷：包含会换行的 fixture，不只检查第一条短行。
- 组件变体：检查渲染结果及实际 shape，不只查源代码 import。
- 测量逻辑可在临时 fixture 上加入已知坏值，确认断言从通过变为失败；不要把故意的坏值写入生产组件。
- 既有失败说明来源、与本次的关系以及未覆盖之处。不能把任何不方便的失败都标为“无关”。

## 审查记录的最小形式

```text
目标：任务列表首次可用且与现有工具页一致
参照：已认可工具页 + 共享面板/控件
发现：长文件名 Tooltip 两行都提前换行，框仍很宽
原因：通用 Tooltip 的均衡换行与当前标识符内容不匹配
修复：仅此内容场景覆盖换行策略，并限制最大宽度
复验：长短文本、键盘焦点、窄窗口，截图与实际文本矩形已检查
限制：未验证的平台或流程如实列出；无则省略
```
