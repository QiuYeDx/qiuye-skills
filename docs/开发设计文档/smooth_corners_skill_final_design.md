# Smooth Corners Skill 最终设计文档

创建日期：2026-07-06
更新日期：2026-07-06

## 设计结论

新增 Skill 应命名为 `qiuye-smooth-corners`，目录放在：

```text
frontend/ui-ux/skills/smooth-corners/
```

这个 Skill 的定位不是解释 CSS 圆角基础知识，而是帮助 AI Agent 在真实前端项目中识别“平滑圆角”意图，并选择正确实现方式：

1. shadcn/ui + QiuYe UI registry 项目：优先安装 `@qiuye-ui/smooth-corners`。
2. 普通 React/Vue/Vanilla 项目且允许依赖：安装平滑圆角 npm 包。
3. 不能新增依赖或用户要求内联：复制最小 `smoothCorners` helper + CSS `@supports`。
4. 元素尺寸动态、圆角接近短边一半：使用尺寸感知 compute 或 observer。

硬性优先级：只要目标项目能使用 shadcn/ui registry，Skill 就应优先推荐 QiuYe UI 的 `@qiuye-ui/smooth-corners` 组件，而不是让用户手动安装底层算法包。底层 npm 包只作为 QiuYe UI 组件的依赖、非 shadcn 项目的直接方案，或需要更底层 API 时的选择。

Skill 要明确“渐进增强”是核心不变量：永远使用 `@supports (corner-shape: superellipse(2))` 切换，unsupported 浏览器回退到原始 `border-radius`，不要用 UA 判断或硬编码浏览器版本。

## 目标

- 让 Agent 在用户说“平滑圆角”“Figma corner smoothing”“iOS continuous corner”“squircle”“superellipse corner”“圆角更柔和”等意图时自动触发。
- 引导 Agent 先检查项目类型、依赖策略、包管理器、CSS/Tailwind 约束和是否已经使用 shadcn/ui。
- 提供四条实现路线：QiuYe UI 组件、npm 包 API、本地内联 helper、尺寸感知 observer。
- 给出常见坑：inline `borderRadius` 覆盖 `@supports`、忘记注入 CSS、过度使用 ResizeObserver、在 Tailwind `rounded-*` 与动态半径之间冲突。
- 提供可复用代码模板，但通过 `references/` 延迟加载，保持 `SKILL.md` 主体精简。
- 在 README 中注册 Skill，便于 `npx skills add ... --skill qiuye-smooth-corners` 安装。

## 非目标

- 不把 `smooth-corners-web` 的完整文档复制进 Skill。
- 不维护浏览器支持表；Skill 只要求使用 `@supports`。
- 不要求所有项目都安装 QiuYe UI。
- 不实现图片、SVG、Canvas 等复杂路径裁切 polyfill。
- 不作为 Tailwind 主题圆角 token 的全局替代方案。

## 当前仓库状态

`qiuye-skills` 当前目录约定：

```text
common/dev/skills/
frontend/ui-ux/skills/
```

已有 UI/UX Skills：

- `qiuye-edge-gradient-mask`
- `geometric-mask-transition`
- `frontend-pitfalls`
- `motion-recipes`

新增 Skill 属于 `frontend/ui-ux`，与 edge/mask/motion 类视觉实现能力同层。

## Skill 目录结构

推荐结构：

```text
frontend/ui-ux/skills/smooth-corners/
  SKILL.md
  agents/openai.yaml
  references/
    implementation-recipes.md
```

说明：

- `SKILL.md`：触发后的核心流程、决策矩阵、验收清单。
- `agents/openai.yaml`：安装列表和 UI 展示元数据，按 `skill-creator` 规则生成。
- `references/implementation-recipes.md`：放较长代码模板，如内联 helper、React wrapper、Vue/Vanilla 用法、observer 模板。

不新增 README、安装指南或 changelog，避免 Skill 目录膨胀。

## Frontmatter 设计

建议：

```yaml
---
name: qiuye-smooth-corners
description: >-
  Implement Figma/iOS-style smooth corners for frontend UI using progressive
  enhancement with CSS corner-shape: superellipse(...), border-radius fallback,
  and optional size-aware computation. Use when users ask for smooth corners,
  corner smoothing, continuous corners, superellipse/squircle corners, iOS-like
  rounded corners, Figma corner smoothing, or want shadcn/ui components to reuse
  smooth corner effects. Covers QiuYe UI registry installation, npm package
  usage, no-dependency inline helpers, ResizeObserver/observer patterns,
  Tailwind/shadcn integration, and validation.
---
```

该 description 需要同时覆盖英文和中文意图：

- smooth corners
- corner smoothing
- continuous corners
- superellipse / squircle
- Figma corner smoothing
- iOS continuous corner
- 平滑圆角
- 圆角平滑
- 超椭圆圆角
- 连续圆角
- 柔和圆角

## SKILL.md 主体设计

### 核心流程

Skill 使用时按以下步骤执行：

1. **识别项目环境**
   - 是否 React / Next.js / Vue / Vanilla。
   - 是否已经有 shadcn/ui 和 `components.json`。
   - 是否已配置 QiuYe UI registry。
   - 是否允许安装 npm 依赖。
   - 包管理器和 lockfile 版本。

2. **选择实现路线**
   - shadcn/ui 且能使用 QiuYe UI registry：安装 `@qiuye-ui/smooth-corners`，不要先手动安装底层算法包。
   - 非 shadcn 项目，或明确只需要工具 API：安装 `@qiuyedx/smooth-corners@0.1.0` 或更新版本。
   - 不允许依赖：读取 `references/implementation-recipes.md` 中的 inline helper。
   - 元素尺寸动态或半径接近短边一半：选择 observer / ResizeObserver / `computeSmoothCorners`。

3. **实现渐进增强**
   - 写入 CSS 变量：`--sc-r`、`--sc-i`、`--sc-s`。
   - 基础规则使用原始半径。
   - `@supports (corner-shape: superellipse(2))` 中使用补偿半径和 `corner-shape`。

4. **避免常见错误**
   - 不要同时用 inline `borderRadius` 和 `@supports` class 控制同一元素。
   - 不要用 UA 判断支持情况。
   - 不要默认给大量列表项启用 ResizeObserver。
   - 不要让 Tailwind `rounded-*` 覆盖动态圆角 class。
   - 不要在 unsupported 浏览器里承诺真实超椭圆效果。

5. **验证**
   - 检查支持与不支持 `corner-shape` 的回退逻辑。
   - 检查深浅色主题、hover/focus 状态、布局是否因参数变化跳动。
   - 如启动 dev server，结束前关闭。

### 决策矩阵

`SKILL.md` 中建议放一个短表：

| 场景 | 首选方案 |
| --- | --- |
| QiuYe UI / shadcn 项目，需要可复用组件 | `shadcn add @qiuye-ui/smooth-corners` |
| React/Vue/Vanilla，可安装依赖，且不使用 shadcn registry | npm 包 CSS variable API |
| 元素尺寸不固定或大圆角容易溢出 | compute/observer 尺寸感知方案 |
| 不允许新增依赖 | inline helper + CSS `@supports` |
| 只是全局主题圆角调整 | 不用本 Skill，优先改 design token |

## references/implementation-recipes.md 设计

参考文件应包含以下模板：

1. npm 包 CSS variable API：

```tsx
import { smoothCorners } from "@qiuyedx/smooth-corners";

<div className="smooth-corners" style={smoothCorners(30, 0.6)} />
```

2. 全局 CSS：

```css
.smooth-corners {
  border-radius: var(--sc-r);
}
@supports (corner-shape: superellipse(2)) {
  .smooth-corners {
    border-radius: var(--sc-i);
    corner-shape: var(--sc-s);
  }
}
```

3. 无依赖 helper：

- `superellipseK(radius, compensated)`
- `smoothCorners(radius, smoothing = 0.6)`
- `computeSmoothCorners(width, height, radius, smoothing)`

4. React wrapper 简化版：

- 支持 `radius`、`smoothing`、`className`、`style`。
- 不写 inline `borderRadius`。
- 自动合并 CSS 变量。

5. Observer 模板：

- `ResizeObserver` 读取尺寸。
- 调用 `computeSmoothCorners`。
- 清理 observer。

6. Tailwind/shadcn 注意事项：

- `rounded-*` 与 `.smooth-corners` 的优先级问题。
- `asChild` 场景优先用 QiuYe UI 组件。
- 图片、按钮、卡片、弹窗的推荐挂载层。

## 与 QiuYe UI 组件的关系

当 `qiuye-shadcn_ui` 完成 `smooth-corners` registry item 后，Skill 需要把它作为 shadcn 项目的首选路径。对于已经使用或可以使用 shadcn/ui 的项目，Agent 应先安装 QiuYe UI 组件；只有在项目不是 shadcn/ui 体系、无法接入 registry、或用户明确要底层 helper/API 时，才直接安装 `@qiuyedx/smooth-corners` 或使用内联实现。

示例：

```bash
pnpm dlx shadcn@latest add @qiuye-ui/smooth-corners
```

或直接 URL：

```bash
pnpm dlx shadcn@latest add https://ui.qiuyedx.com/registry/smooth-corners.json
```

如果目标项目还没配置 registry，Skill 要提醒 Agent 检查 `components.json`：

```json
{
  "registries": {
    "@qiuye-ui": "https://ui.qiuyedx.com/registry/{name}.json"
  }
}
```

## README 注册设计

`qiuye-skills/README.md` 的 `frontend/ui-ux` 章节新增：

````markdown
#### `qiuye-smooth-corners` - 平滑圆角 / Figma Corner Smoothing

为前端界面实现 Figma/iOS 风格的平滑圆角，支持 QiuYe UI registry、npm 包、无依赖内联实现和尺寸感知 observer 方案。

**触发词：** smooth corners、corner smoothing、squircle、superellipse、Figma 圆角平滑、iOS 连续圆角、平滑圆角

```bash
npx skills add https://github.com/qiuyedx/qiuye-skills.git --skill qiuye-smooth-corners
```
````

## 验证策略

实现 Skill 后执行：

```text
quick_validate.py <path/to/frontend/ui-ux/skills/smooth-corners>
```

如果本机没有直接可用的 validator，可至少检查：

- `SKILL.md` frontmatter 只有 `name` 和 `description`。
- Skill name 全局唯一，且为小写连字符。
- README 中的安装命令与 frontmatter name 一致。
- references 文件确实被 `SKILL.md` 提及，且触发后知道何时读取。
- 代码模板使用已发布的 `@qiuyedx/smooth-corners` 包；如后续版本升级，应保持 QiuYe UI 组件优先级不变。

## 风险

- 如果目标项目可使用 shadcn/ui registry，Skill 直接推荐底层 npm 包会绕过 QiuYe UI 组件，导致复用体验变差。必须优先推荐 `@qiuye-ui/smooth-corners`。
- 如果 Skill 主体过长，Agent 每次触发都会加载大量模板。较长代码必须放入 `references/implementation-recipes.md`。
- 如果触发词只写英文，会漏掉“平滑圆角”“圆角平滑”等中文需求。
- 如果没有强调 `@supports`，Agent 容易写出只在新浏览器可用的样式。

## 明确排除

- 不在 Skill 中维护 QiuYe UI registry 的完整组件清单。
- 不把 Skill 变成 shadcn 组件开发教程。
- 不在 Skill 中要求 Agent 无条件启动 dev server。
