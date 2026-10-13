# 工作包 SK-6：全应用工具类与嵌套圆角推导

## 基本信息

- 日期：2026-10-13
- 状态：已完成
- 对应执行计划工作包：SK-6
- 来源：PotSubOverlay v1.3.0（Electron 桌面应用）。用户反馈简洁模式外框圆角太小、内外间距不等，并要求全应用改用平滑圆角。实装与验收结果证明有效后，把可复用的方法沉淀到 Skill。

## 本次实现内容

- **qiuye-smooth-corners**
  - 路由表新增“全应用推广”场景；`App-Wide Utility Route` 一节说明它作为 shadcn 组件优先规则的例外，以及成立条件：固定 smoothing 下输出与半径无关。
  - recipe 8：smoothing 0.4–0.8 的补偿倍数与 `superellipse(K)` 常数表；Tailwind v4 `@utility rounded-smooth-*`（`[*]` 而非 `[length]`，否则丢掉 `var()` 任意值）；运行时半径走 CSS 变量；tailwind-merge 冲突配置；推广规则（不改胶囊 / 圆形、小尺寸降档、`rounded-[inherit]` 补 `corner-shape: inherit`、`overflow-hidden` 按超椭圆裁剪、批量替换后检查遗漏）。
  - 嵌套圆角一节：从最内层固定形状向外推半径；在补偿前的基础半径上套用该关系；嵌套各层用同一 smoothing；最外层轮廓可能由平台决定。
  - Common Mistakes 新增 4 条。
- **qiuye-ui-quality**
  - `visual-insets-and-contours.md`：新增“从内向外定半径（首版就做对）”，含转角空隙估算 `p + 0.41 × (r − (R − p))` 与例子；新增“最外层轮廓可能不归页面控制”，覆盖桌面窗口、宿主容器、iframe、屏幕圆角，以及自绘外壳的代价；症状表新增“外框圆角太小、内外圆角不和谐”。
  - `SKILL.md`：第 2 节靠角规则补充“首版就从内向外推半径并确认最外层归属”；症状路由加入“外框圆角太小”。
  - `evals/scenarios.md`：新增 2 个场景（首版推导嵌套半径；系统固定窗口圆角下的迷你窗口）。
- README 同步两项 Skill 的说明。

## 关键决策

- **不新建 Skill**：嵌套轮廓的通用方法已在 `qiuye-ui-quality` 的专题参考中，平滑圆角的实现已在 `qiuye-smooth-corners` 中。新建一个“圆角和谐”Skill 会与两者触发重叠。两处各补自己负责的部分，并互相引用。
- **首版生效靠两处入口**：`qiuye-ui-quality` 在新建 / 重写界面时触发，第 2 节的规则在写样式前就要求推导半径；`qiuye-smooth-corners` 在提到平滑圆角时触发，嵌套一节给出同样的规则。
- 公式只用作定位工具：普通圆弧下转角空隙的线性近似可以直接算；超椭圆仍以渲染截图为准，不宣称公式能证明美观。
- 常数表由包实算，注明来源版本，便于包变化时重算。

## 验证结果

```text
常数表          node 调用 @qiuyedx/smooth-corners@0.1.0 的 smoothCorners(10, s) 与 smoothCorners(37, s)，
                确认同一 s 下 K 相同、补偿倍数为 1 + s
工具类与配置    PotSubOverlay v1.3.0：构建产物包含 rounded-smooth-{token,[px],[var(--x)]}，增强部分位于 @supports 内；
                tailwind-merge 用例（rounded-smooth-2xl + rounded-none → rounded-none 等）通过；Electron 41 截图中
                overflow-hidden 按超椭圆裁剪
嵌套推导        简洁面板 24 = 预览 16 + 8；预览内 8px 处 24px 胶囊（估算转角空隙 9.7px）；底角 28px 圆形按钮；截图验收通过
```

## 未完成事项

- 未做 subagent 前向测试（新增的两个评估场景尚未实际运行）。
- 已安装的副本（`~/.agents/skills/`）需要推送后用 `npx skills add` 重新安装才会更新。
