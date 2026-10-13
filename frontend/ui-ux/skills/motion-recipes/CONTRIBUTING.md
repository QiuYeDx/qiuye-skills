# Motion Recipes 维护指南

## 新增 Case 流程

### 1. 创建 case 文件

在 `cases/` 目录下新建 `<case-slug>.md`，命名使用小写英文 + 连字符，例如：

- `layout-id-nav-switch.md`
- `stagger-list-enter.md`
- `drag-to-dismiss.md`
- `shared-layout-modal.md`

### 2. 按模板编写内容

每个 case 文件应包含以下结构。核心章节为：目标、适用场景、AI Agent 执行步骤、常见坑与修复、验收清单；标注“可选”的章节和「最小代码骨架」按需添加。组合型 case（如 Case 9 连续布局过渡）可按“先选最小方案 → 分层结构 → 失败定位”组织，但仍需保留目标、执行步骤与验收清单：

```markdown
# Case N: [简洁标题]

## 目标
用 1–3 句话说明该 case 解决什么问题。

## 适用场景
- 典型需求表述（用户可能怎么描述这个需求）
- 典型 UI 列表

## 核心设计原则
按优先级列出该 case 的关键设计决策和"为什么这样做"。
每条原则配简短代码片段。

## 推荐实现模板
分步骤给出完整的、可直接复制的代码模板。
每步附简要说明和设计意图。

## AI Agent 执行步骤
Agent 收到匹配需求时应按什么顺序操作。
按 Step 1 / Step 2 ... 编号。

## 常见坑与修复
按「坑 N: 标题」格式列出。
每个坑包含：现象、原因、修复代码。

## 动效参数建议（可选）
给出该场景下推荐的 transition / spring / ease 参数及变体。

## 变体模式（可选）
该 case 的变体写法（如横向 vs 纵向、淡入 vs 位移等）。

## 验收清单
完成后必须逐项检查的 checklist。

## 推荐回答格式
Agent 完成实现后应如何向用户汇报。

## 最小代码骨架
一个可运行的最小完整示例。
```

### 3. 在 SKILL.md 中注册

在 `SKILL.md` 的「案例索引」表格中添加一行：

```markdown
| N | [Case 名称] | [cases/xxx.md](cases/xxx.md) | 关键词 / 适用场景 |
```

在「场景匹配指南」表格中添加一行，写 2–3 句用户的典型说法；完整场景列表留在 case 的「适用场景」里：

```markdown
| 「用户可能的表述 1」「用户可能的表述 2」 | N |
```

若新 case 与已有 case 容易混淆（例如都涉及高度或列表），同时更新「选择 case」决策表，并让 case 开头的引用写明“何时改读另一个 case”，避免互相要求先读对方。

### 4. 检查 SKILL.md frontmatter

`description` 只写“做什么 + 何时用 + 不用于什么”，不要逐条追加触发短语（上限 1024 字符，过长还会让 Skill 在无关任务中误触发）。只有新 case 引入了全新领域时，才在 description 里补一个领域词。

---

## Case 编写原则

### 内容定位

- **面向 AI Agent**：不是面向人类的教程，而是让 Agent 在匹配场景时能直接参考执行
- **可复制性**：模板代码应可直接复制到项目中使用，只需替换业务变量
- **坑位优先**：重点记录实战中踩过的坑和修复方案，而非基础 API 用法

### 代码规范

- 使用 TypeScript + TSX
- 样式使用 Tailwind CSS
- Motion 导入统一使用 `motion/react`（如项目用 framer-motion 则在文中说明）
- 代码片段使用 `tsx` 语法高亮

### 篇幅控制

- 单个 case 文件建议控制在 200–400 行
- 含多策略完整模板的 case 可到约 600 行（如 Case 1、7）；超过 400 行时先删冗余解释，把可直接复用的组件代码移到 `assets/`，仍然过长再拆成独立 case
- 避免冗余解释：Agent 已经很聪明，只写它不知道的

### 验收清单要求

- 每个 case 必须有验收清单
- 清单项应可客观验证（能看到/测到），不要写主观描述
- 清单项覆盖：视觉效果、层级问题、TypeScript 类型、样式冲突

---

## 目录结构

```
motion-recipes/
├── SKILL.md                           # 主索引（Agent 入口）
├── CONTRIBUTING.md                    # 本文件（维护指南）
├── assets/
│   └── flow-transition.tsx            # Case 9 组件模板
└── cases/
    ├── layout-id-nav-switch.md        # Case 1
    ├── ...                            # Case 2, 3, ...
    └── ...
```
