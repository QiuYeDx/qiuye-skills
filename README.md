# qiuye-skills

精心整理的 Agent Skills 仓库，用于沉淀可复用的工程能力、团队规范与领域知识。

## 设计目标

- 分层治理，避免技能散落和命名冲突
- 路径结构统一，保证可检索、可审阅、可演进
- 每个技能目录最小可用单元固定为 `SKILL.md + 辅助文档`
- 所有技能最终目录层级统一为：`.../.../skills/<xxx skill>/<SKILL.md 和其他资产>`
  如 `frontend/ui-ux/skills/.../SKILL.md`

## 目录约定

```text
qiuye-skills/
├── common/dev/skills/
│   ├── spec-driven-ai-coding/
│   │   ├── SKILL.md
│   │   ├── agents/openai.yaml
│   │   ├── references/
│   │   │   ├── quality-gates.md
│   │   │   ├── frontend-quality.md
│   │   │   ├── backend-quality.md
│   │   │   └── planning-guide.md
│   │   ├── templates/
│   │   │   ├── discovery.md
│   │   │   ├── brd.md
│   │   │   ├── requirements.md
│   │   │   ├── design.md
│   │   │   ├── tasks.md
│   │   │   ├── task-list-overall.md
│   │   │   ├── record.md
│   │   │   ├── change.md
│   │   │   └── manual-test-checklist.md
│   │   └── scripts/
│   │       ├── init_spec.py
│   │       └── check_spec.py
│   └── project-pitfall-guard/
│       ├── SKILL.md
│       ├── agents/openai.yaml
│       ├── references/project-pitfall-guard-contract.md
│       └── scripts/bootstrap_project_pitfall_guard.py
└── frontend/ui-ux/skills/
    ├── edge-gradient-mask/
    │   └── SKILL.md
    ├── frontend-pitfalls/
    │   ├── SKILL.md
    │   ├── agents/openai.yaml
    │   └── cases/backdrop-filter-glass-blur.md
    ├── geometric-mask-transition/
    │   ├── SKILL.md
    │   ├── agents/openai.yaml
    │   └── references/
    │       ├── technique-selection.md
    │       ├── implementation-recipes.md
    │       └── validation.md
    └── motion-recipes/
        ├── SKILL.md
        ├── CONTRIBUTING.md
        └── cases/
            ├── layout-id-nav-switch.md
            ├── animate-presence-auto-height-popover.md
            ├── shared-element-orchestrated-view-switch.md
            ├── layout-dependency-isolate-indicator.md
            ├── measured-auto-height-content.md
            ├── list-presence-layout-reorder.md
            └── container-transform-morph.md
```

## Skills 一览

### common/dev — 通用开发工作流

#### `spec-driven-ai-coding` — 分级 Spec 驱动的 AI Coding 工作流

按需求规模 S / M / L 选择流程与文档量：S 直接开发并自检；M 产出单模块 `requirements / design / tasks`；L 走项目级 Spec 模式：需求梳理 → BRD（唯一需求基底）→ 模块拆分（`module-common` + `module-xxx`）→ 各模块三件套 → `task-list-overall` → 一 Agent 一模块并行开发 → 单项 / 结合 / 人工测试 → 变更先改 BRD 再回流。

针对 AI 做大需求时常见的「遗漏需求点、前端粗糙、功能肤浅不可用、逻辑不自洽、后端质量差、放飞自我」，内置：`BR → R → T` 需求编号追踪、前端 / 后端设计阶段产出要求与质量门、浏览器自检与接口验证流程、完成定义（DoD）、检查点（CP1/CP2/CP3）必停、一 Agent 一模块一任务的范围栅栏、状态诚实规则。附 9 套文档模板与两个脚本：`init_spec.py` 生成骨架，`check_spec.py` 检查需求覆盖、状态合法性与 overall/tasks 一致性。

替代原 `large-feature-ai-coding`；存量项目中旧格式（`*_final_design.md` / `*_execution_plan.md`）可继续沿用。

**触发词：** spec 模式、BRD、需求梳理、需求文档、开发设计、任务拆分、模块拆分、module-common、中小型需求、中大型需求、项目级开发、多 Agent 并行、多会话开发、实施记录、变更管理、新需求/修改点、验收测试、AI Agent Coding

```bash
npx skills add https://github.com/qiuyedx/qiuye-skills.git --skill spec-driven-ai-coding
```

---

#### `project-pitfall-guard` — 项目级踩坑防护

元技能（Meta-skill）：在当前项目中建立并维护项目级踩坑防护 Skill，将踩坑经验沉淀为可跨会话复用的项目记忆。自动为项目生成 `.agents/skills/<project>-pitfall-guard/` 结构，含索引、详情文件与添加脚本。

**触发词：** 踩坑、避坑、pitfall、gotcha、lessons learned、project memory、repeated mistakes

```bash
npx skills add https://github.com/qiuyedx/qiuye-skills.git --skill project-pitfall-guard
```

---

### frontend/ui-ux — 前端 UI/UX

#### `qiuye-edge-gradient-mask` — 边缘渐变淡出遮罩

为可滚动区域、视口、卡片等元素添加边缘渐变淡出遮罩（soft fade），提供 5 套开箱即用模板，覆盖页面固定边缘、滚动感知显隐、水平无限滚动、装饰性渐变、CSS mask-image 等场景。

**触发词：** edge fade、gradient mask、scroll fade、soft edge、overflow fade、mask-image gradient

```bash
npx skills add https://github.com/qiuyedx/qiuye-skills.git --skill qiuye-edge-gradient-mask
```

---

#### `geometric-mask-transition` — 几何遮罩与揭幕过渡

面向生产实现的几何遮罩 / 揭幕转场工作流。先明确 source、target、形状内外关系和 DOM 提交点，再在 transform cover、clip-path、CSS alpha mask、View Transition API、SVG 与 Canvas/WebGL 中正确选型；同时覆盖任意原点半径计算、首尾帧、并发取消、resize、reduced motion、浏览器回退和逐帧视觉验收。

**触发词：** reveal transition、geometric mask、clip-path reveal、radial wipe、aperture reveal、view transition reveal、几何遮罩、揭幕、遮罩过渡、图形过渡、页面转场遮罩

```bash
npx skills add https://github.com/qiuyedx/qiuye-skills.git --skill geometric-mask-transition
```

---

#### `frontend-pitfalls` — 前端避坑 Case 集合

沉淀真实项目中容易被 AI Agent 或开发者误用的 UI/CSS/交互实现坑位，给出稳定结构、排查顺序、推荐模板与验收清单。当前包含 1 个 case：

| Case | 文件 | 覆盖主题 |
|---|---|---|
| backdrop-filter 背景模糊与玻璃态浮层 | `cases/backdrop-filter-glass-blur.md` | backdrop-blur、glassmorphism、移动端菜单模糊、Safari 兼容、退出动画故障 |

**触发词：** 前端避坑、backdrop-filter、玻璃态、毛玻璃、Safari 模糊、移动端菜单模糊、透明导航栏

```bash
npx skills add https://github.com/qiuyedx/qiuye-skills.git --skill frontend-pitfalls
```

---

#### `qiuye-smooth-corners` — 平滑圆角实现指南

面向前端项目实现 Figma / iOS 风格平滑圆角，优先使用 QiuYe UI 的 shadcn registry 组件，并提供 `@qiuyedx/smooth-corners` npm 包、无依赖内联 helper 与尺寸感知 observer 方案。

**触发词：** smooth corners、corner smoothing、continuous corners、squircle、superellipse、平滑圆角、圆角平滑、超椭圆圆角、连续圆角

```bash
npx skills add https://github.com/qiuyedx/qiuye-skills.git --skill qiuye-smooth-corners
```

---

#### `motion-recipes` — Motion 动效案例集

经过验证的 Motion (framer-motion) 动效实现方案与最佳实践，每个 case 包含完整模板代码、常见坑位修复与验收清单。当前包含 7 个 case：

| Case | 文件 | 覆盖主题 |
|---|---|---|
| layoutId 导航切换 + 内容过渡 | `cases/layout-id-nav-switch.md` | Nav/Tabs 活跃态滑动、方向感知内容过渡、z-index 遮挡修复 |
| AnimatePresence + Popover auto-height | `cases/animate-presence-auto-height-popover.md` | popLayout、动态内容高度突变修复 |
| 共享元素迁移 + 辅助内容编排 | `cases/shared-element-orchestrated-view-switch.md` | Header 模式切换、卫星内容编排、暗色模式文字伪影 |
| layoutDependency 隔离无关布局变化 | `cases/layout-dependency-isolate-indicator.md` | 祖先重排时避免未交互 indicator 上下漂移 |
| 测量式 auto-height | `cases/measured-auto-height-content.md` | useMeasure / ResizeObserver、同一内容树 auto → auto 平滑过渡 |
| 列表增删、Presence 与位置重排 | `cases/list-presence-layout-reorder.md` | AnimatePresence、popLayout、Flex/Grid 批量增删、退出快照与平滑重排 |
| 容器变形过渡（Container Transform） | `cases/container-transform-morph.md` | 触发器原地扩展成面板、卡片飞向视口中央变浮层、占位 + 视觉克隆、遮罩与焦点管理 |

**触发词：** motion、framer-motion、layoutId、AnimatePresence、nav 切换动效、dynamic height、useMeasure、ResizeObserver、spring animation、列表增删、列表重排、popLayout、退出快照、container transform、容器变形、卡片展开、居中浮层、动效案例

```bash
npx skills add https://github.com/qiuyedx/qiuye-skills.git --skill motion-recipes
```

---

## Skills 安装指引

### 安装全部 Skills

```bash
npx skills add https://github.com/qiuyedx/qiuye-skills.git
```

### 安装特定子路径下的 Skills

```bash
# 安装 frontend/ui-ux 下的所有 skills
npx skills add https://github.com/qiuyedx/qiuye-skills/-/tree/master/frontend/ui-ux/skills

# 安装 common/dev 下的所有 skills
npx skills add https://github.com/qiuyedx/qiuye-skills/-/tree/master/common/dev/skills
```

### 查看可用 Skills 列表

```bash
npx skills add https://github.com/qiuyedx/qiuye-skills.git --list
```

### 安装指定某个 Skill

`skill-name` 为 `SKILL.md` 头部 `name` 字段，在仓库中全局唯一：

```bash
npx skills add https://github.com/qiuyedx/qiuye-skills.git --skill <skill-name>
```

## 维护建议

- 新增技能时优先保证命名清晰、场景明确
- `SKILL.md` 应提供最小可运行示例与边界说明
- 辅助文档建议按 `references`、`cases`、`scripts` 拆分，便于检索与维护
- 含多个 case 的技能（如 `motion-recipes`、`frontend-pitfalls`）遵循索引 + `cases/` 详情文件模式
