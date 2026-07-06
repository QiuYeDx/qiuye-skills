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
│   ├── large-feature-ai-coding/
│   │   └── SKILL.md
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
    │   └── agents/openai.yaml
    └── motion-recipes/
        ├── SKILL.md
        ├── CONTRIBUTING.md
        └── cases/
            ├── layout-id-nav-switch.md
            ├── animate-presence-auto-height-popover.md
            └── shared-element-orchestrated-view-switch.md
```

## Skills 一览

### common/dev — 通用开发工作流

#### `large-feature-ai-coding` — 中大型需求 AI Coding 协作工作流

中大型需求的 AI Agent Coding 协作工作流，涵盖开发设计文档、执行计划、多会话实施记录与进度台账。适用于跨前后端的中大型功能开发。

**触发词：** 中大型需求、跨前后端、开发设计文档、执行计划、多会话开发、工作包、进度台账

```bash
npx skills add https://github.com/qiuyedx/qiuye-skills.git --skill large-feature-ai-coding
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

通用的几何遮罩 / 揭幕过渡实现方法论，指导 AI Agent 用独立遮罩层、少量几何变量和稳定的时序模型实现圆形揭幕、斜向 wipe、clip-path、mask-image、SVG mask、canvas/WebGL matte 等过渡效果。

**触发词：** reveal transition、geometric mask、clip-path reveal、radial wipe、aperture reveal、几何遮罩、揭幕、遮罩过渡、图形过渡

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

经过验证的 Motion (framer-motion) 动效实现方案与最佳实践，每个 case 包含完整模板代码、常见坑位修复与验收清单。当前包含 3 个 case：

| Case | 文件 | 覆盖主题 |
|---|---|---|
| layoutId 导航切换 + 内容过渡 | `cases/layout-id-nav-switch.md` | Nav/Tabs 活跃态滑动、方向感知内容过渡、z-index 遮挡修复 |
| AnimatePresence + Popover auto-height | `cases/animate-presence-auto-height-popover.md` | popLayout、动态内容高度突变修复 |
| 共享元素迁移 + 辅助内容编排 | `cases/shared-element-orchestrated-view-switch.md` | Header 模式切换、卫星内容编排、暗色模式文字伪影 |

**触发词：** motion、framer-motion、layoutId、AnimatePresence、nav 切换动效、spring animation、动效案例

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
