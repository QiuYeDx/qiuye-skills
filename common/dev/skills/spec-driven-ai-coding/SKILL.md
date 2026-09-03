---
name: spec-driven-ai-coding
description: >-
  分级（S/M/L）的 Spec 驱动 AI Coding 工作流。小需求直接开发并自检；中型需求产出单模块
  requirements/design/tasks；中大型或项目级需求走 需求梳理 → BRD → 模块拆分（module-common +
  module-xxx）→ 各模块 requirements/design/tasks → task-list-overall → 一 Agent 一模块并行开发 →
  单项/结合/人工测试 → 变更先改 BRD 的闭环，并用需求编号追踪、前端/后端质量门、检查点与完成定义
  防止遗漏需求、前端粗糙、功能肤浅、逻辑不自洽与 AI 放飞。Use when the user asks to plan or
  implement a feature or project with AI agents, mentions spec mode, BRD, requirements/design/tasks
  docs, module split, task list, parallel or multi-session development, acceptance testing, or
  submits 新需求/修改点. Triggers: spec 模式、BRD、需求梳理、需求文档、开发设计、任务拆分、
  task-list、模块拆分、module-common、中小型需求、中大型需求、项目级开发、多 Agent 并行、
  多会话开发、实施记录、变更管理、新需求/修改点、验收测试、人工测试、feat/fix、AI Agent Coding。
---

# Spec-Driven AI Coding

按需求规模选择恰当的流程与文档量，用「需求基底 → 模块 Spec → 任务 → 验证 → 变更回流」的闭环约束 AI，让另一位 Agent 或人只凭文档就能继续开发。

## 每次会话开始

1. 判定规模（见下表），或沿用文档中已判定的规模。
2. 定位文档根与当前阶段（见「入口路由」）。
3. 明确本会话角色：规划者 / 模块开发者 / 测试验收 / 变更管理。
4. 在回复开头用 3–5 行声明：规模、角色、本会话产出、将在哪个检查点停下。
5. 结束前执行「会话收尾清单」。

## 规模判定

| 规模 | 典型特征 | 流程 |
| --- | --- | --- |
| S | 单点修改或 bugfix；≤3 个文件；无新接口/新页面/新表；一次会话可完成 | 流程 S |
| M | 单一功能，落在 1 个模块；少量页面/接口/表；1–5 个会话；单 Agent 串行 | 流程 M |
| L | 多模块或跨前后端；需多会话或多 Agent 并行；从零起项目；需求模糊需先讨论 | 流程 L |

拿不准时向上取一级；用户明确指定规模时以用户为准。S 中途发现需要新接口/新页面 → 升级 M；M 中途发现需要拆模块 → 升级 L，并补齐对应文档后再继续。

## 入口路由

| 仓库/对话状态 | 角色与动作 |
| --- | --- |
| 无 spec 文档，需求模糊或较大 | 规划者：阶段 0 需求梳理 |
| 有 `discovery.md` 无 `brd.md`（L） | 规划者：写 BRD → CP1 |
| 有 `brd.md` 无模块 spec | 规划者：模块拆分 + 模块三件套 + `task-list-overall.md` → CP2 |
| 有三件套（M）或用户指定模块/任务 | 模块开发者：按「开发会话协议」领取一个任务 |
| 用户给出「新需求/修改点」或验收发现的问题 | 变更管理：影响分析 → 先改需求基底 → 再改其他文档 → 确认 → 实施 |
| 用户要求测试/验收 | 测试验收：单项 → 结合 → 人工测试清单 → CP3 |
| 用户只要分析/评审 | 不写代码，产出结论或文档更新建议 |
| 项目已有旧格式（`*_final_design.md` / `*_execution_plan.md`） | 沿用旧格式与其台账，不迁移；质量门与 DoD 仍然适用 |

检查点（到达即停下等待用户确认，并在 `task-list-overall.md`「检查点记录」登记）：

| 检查点 | L | M |
| --- | --- | --- |
| CP1 需求基底 | `brd.md` 完成 | `requirements.md` 完成（可与 CP2 合并停一次） |
| CP2 设计与任务 | 全部模块三件套 + `task-list-overall.md` 完成，`check_spec.py` 无 error | `design.md` + `tasks.md` 完成，`check_spec.py` 无 error |
| CP3 阶段验收 | 每个阶段端到端可演示；最终人工测试清单 | 全部任务完成后的人工测试清单 |

## 不可违反的规则

1. **需求基底唯一**：L 以 `brd.md`、M 以 `requirements.md` 为唯一需求来源。任何新增/修改需求必须先改需求基底，再改 design/tasks/overall，最后才改代码。
2. **不脑补需求**：文档未写明的行为，先查需求基底；仍无 → 登记为 `Q-xx` 未决问题或 `A-xx` 假设，取最保守实现，并在回复中显式列出。用户说「由 AI 自行补充细节并设计方案」时，可联网参考同类产品并自行设计，但每条补充都要写成 `A-xx` 进入文档等待确认。
3. **把读者当零上下文的新人**：文档写具体值、枚举、示例数据、字段类型/必填/默认值、每个按钮点击后的行为、每个异常下用户看到什么。禁用模糊词：等等、类似、合理、适当、若干、友好提示、尽量、后续完善。
4. **一 Agent、一模块、一任务**：一次会话只领 1 个任务（强耦合 ≤3 个），只改本模块 `design.md`「代码落点」列出的路径及其测试。需要改 `module-common` 或其他模块 → 走变更管理。
5. **检查点必停**：CP1（需求基底）、CP2（设计与任务）未获用户确认前不写业务代码，只做只读调研。用户明确要求「不用确认一直做」时，仍先完成文档、列清假设，再继续。
6. **真实可用才算完成**：生产路径不得残留 TODO、占位、mock 数据、示意实现、`console.log`；前端每个页面必须在浏览器中实际走通全部状态；后端每个接口必须跑过正反例。满足 DoD 才能标 `已完成`。
7. **状态诚实**：状态只用 `未开始 / 进行中 / 已完成 / 阻塞 / 废弃`；未验证的不得标 `已完成`。
8. **源码目录遵循项目规范**：`module-xxx` 只是文档与任务的组织单位，不要在源码里创建 `module-xxx` 目录；每模块 `design.md` 用「代码落点」表映射到真实目录。
9. **语言约定写进文档**：默认文档中文；代码注释与 UI 文案跟随项目现状。用户指定「中文开发」时，注释、提示文案、错误信息、日志全部中文，并写入需求基底的约束章节。

## 文档目录与编号

优先使用项目已有的文档根；默认 `docs/开发设计文档/`。

```text
docs/开发设计文档/<feature_slug>/
  discovery.md                 # 需求梳理（L 可选；M 需求模糊时可选）
  brd.md                       # L：总需求基底
  task-list-overall.md         # L：总任务列表 + 推荐顺序 + 台账
  modules/                     # L
    module-common/{requirements,design,tasks}.md
    module-<name>/{requirements,design,tasks}.md
  requirements.md              # M：单模块三件套直接放在根
  design.md
  tasks.md
  records/YYYY-MM-DD_<T-ID>_<title>.md       # 实施记录
  changes/YYYY-MM-DD_<feat|fix>_<title>.md   # 变更记录
  acceptance/manual-test-checklist.md        # 人工测试清单
```

编号：`BR-01` 业务需求（BRD）；`R-<MOD>-01` 模块需求；`T-<MOD>-01` 任务；`A-01` 假设；`Q-01` 未决问题。`<MOD>` 为模块大写短码（`COMMON`、`AUTH`、`ORDER`），不含连字符。`tasks.md` 每个任务必须填「关联需求」；记录与变更文件名必须带任务或需求编号。

脚本（`<skill>` 为本 Skill 目录）：

```bash
# 脚手架：L 会自动加入 module-common；M 不传 --modules
python3 <skill>/scripts/init_spec.py --root docs/开发设计文档 --feature <slug> --tier L --modules auth,order
python3 <skill>/scripts/init_spec.py --root docs/开发设计文档 --feature <slug> --tier M
# 检查：BR→R→T 覆盖、状态合法、overall 与 tasks 一致、模糊词
python3 <skill>/scripts/check_spec.py docs/开发设计文档/<slug>
```

## 流程 S（小）

1. 读相关代码；在回复中列出：改动点、涉及文件、可测的验收标准、风险。
2. 实现；运行相关测试/构建。涉及 UI 时，按 `references/frontend-quality.md` 的「浏览器自检流程」走一遍。
3. 若项目已有 `changes/`（或旧格式的 `feat/`、`fix/`）目录，补一条变更记录；否则不产出文档。
4. 回复：改了什么、怎么验证的、遗留风险。

## 流程 M（中）

0. 需求模糊 → 先做需求梳理（用 `references/planning-guide.md` 的问题清单），结论写入 `discovery.md`。
1. 现状调研：读相关代码、接口、已有文档与项目级 pitfall guard；结论写入 `design.md`「现状与约束」。
2. 写 `requirements.md`（`templates/requirements.md`）：R-xx + 用户场景 + 验收标准 + 边界异常 + 范围外。→ CP1（可与 CP2 合并停一次）。
3. 写 `design.md`（`templates/design.md`）：代码落点、数据模型、接口契约、后端设计、前端设计（涉及 UI 必写全）、需求追踪矩阵。
4. 写 `tasks.md`（`templates/tasks.md`）：任务 ≤1 会话，每任务有关联需求/涉及文件/验收标准/测试要求/依赖，先打通最小端到端链路。
5. 运行 `check_spec.py`，无 error 后到 **CP2** 停下，请用户确认。
6. 按「开发会话协议」逐任务开发。
7. 全部任务完成后：按 R-xx 验收标准逐条走查，产出 `acceptance/manual-test-checklist.md` → CP3 等待人工测试；反馈进入变更管理。

## 流程 L（项目级 Spec 模式）

需求大纲 → 需求梳理 → BRD → 模块拆分 + 模块 spec → task-list-overall → 确认 → 并行开发 → 单项测试 → 结合测试 → 人工测试 → 变更回流 BRD。存量项目只针对本次需求做此流程，不重写整个项目文档，但必须做现状调研并写入 BRD「现状与集成点」。

### 阶段 0 需求梳理（需求模糊或描述不足时必做）

- 用 `references/planning-guide.md` 的问题清单分批提问（有 AskQuestion 类工具时优先使用）；每轮 ≤6 个问题，先问阻断性问题。
- 结论写入 `discovery.md`（`templates/discovery.md`）：目标与成功标准、用户与场景、范围 in/out、问答记录、决策、未决问题。
- 退出条件：能写出带验收要点的 BRD，且无阻断性未决问题。

### 阶段 1 BRD → CP1

- 用 `templates/brd.md`。核心：BR-xx 列表（每条含优先级与验收要点）、主/异常用户流程、非功能需求、约束与假设、语言约定、模块划分草案（含 `module-common`）、未决问题。
- 存量项目增加「现状与集成点」：具体文件、接口、表、可复用组件。
- 到 CP1 停下，请用户确认 BRD。

### 阶段 2 模块拆分与模块 Spec → CP2

- 拆分原则见 `references/planning-guide.md`：按业务领域/页面群/服务边界拆；模块间只通过 `module-common` 中声明的契约交互；共享的领域模型、接口约定、错误码、权限、公共组件与工具放 `module-common`。
- 每个模块写三件套（`templates/requirements.md`、`templates/design.md`、`templates/tasks.md`）。每条 R 标注来源 BR；`design.md` 的前端设计与后端设计分别按 `references/frontend-quality.md`、`references/backend-quality.md` 的「设计阶段产出要求」写全。
- 写 `task-list-overall.md`（`templates/task-list-overall.md`）：阶段 0 common → 阶段 1 最小端到端链路 → 阶段 2+ 扩展；每任务标依赖与阶段。
- 运行 `check_spec.py` 修到无 error；到 CP2 停下，请用户确认。

### 阶段 3 开发（开发会话协议）

每个开发会话按顺序执行：

1. 读：需求基底的范围/约束/语言约定章节、`module-common/design.md` 的契约部分、本模块三件套、`task-list-overall.md` 中本模块任务及其依赖状态。
2. 检查依赖任务是否 `已完成`；否则换任务，或将本任务标 `阻塞` 并说明。
3. 领取 1 个任务，在回复中声明：任务 ID、关联需求、输出、涉及文件、验收标准、测试要求。把 `tasks.md` 与 overall 中该任务置 `进行中`。
4. 实现，遵守规则 4 的范围栅栏。实现中发现设计错误 → 先更新 `design.md` 并在 record 中标注，不静默偏离。
5. 验证：运行任务的测试要求；UI 任务执行「浏览器自检流程」；后端任务执行「接口验证流程」；对照 `references/quality-gates.md` 的 DoD 自检。
6. 收尾：更新 `tasks.md` 与 `task-list-overall.md` 中该任务行；写 `records/`（`templates/record.md`）；回复中列出变更文件、验证命令与结果、未完成项、假设、下一任务建议。

并行规则：一个 Agent 只在一个模块内开发；`module-common` 的任务先于依赖它的模块完成，或由专门的 Agent 负责；overall 只改自己任务所在的行；建议一模块一分支，合并前跑一次 `check_spec.py`。

### 阶段 4 测试与验收 → CP3

- 单项测试：每任务按其「测试要求」执行（单测/接口测试/组件测试）。
- 结合测试：模块全部任务完成 → 按该模块 R-xx 验收标准逐条走查；跨模块 → 按 BRD 主流程端到端走通，使用真实形态数据。
- 人工测试：产出/更新 `acceptance/manual-test-checklist.md`（`templates/manual-test-checklist.md`），按用户场景写步骤、预期、结果栏；到 CP3 请用户测试。
- 反馈的问题一律进入变更管理。

### 变更管理（新需求 / 修改点 / 验收问题）

用户通常这样给：「新需求/修改点：1. … 2. …」。处理顺序：

1. 影响分析：列出受影响的 BR/R/design 章节/T 与模块，判定 feat 或 fix。
2. 补充细节与方案，写 `changes/YYYY-MM-DD_<feat|fix>_<title>.md`（`templates/change.md`）。
3. 先改需求基底（BRD 升版本号并在变更记录表加行；M 则改 `requirements.md`），再改相关模块 requirements/design/tasks，再改 `task-list-overall.md`（新增或调整任务）。
4. 影响范围大或有争议 → 停下确认；否则实施并按开发会话协议收尾。
5. fix 若暴露设计缺口，同步修正 `design.md`，让文档集与真实系统一致。

## 质量门（摘要）

进入下一阶段前必须过门，细则见 `references/quality-gates.md`：

- **需求门**：每条 R 有 ID、来源 BR、可测验收标准、主/异常场景；范围外明确；无模糊词；未决问题已登记。
- **设计门**：数据模型/状态机/接口契约完整且与 common 一致；前端设计含页面清单、布局、组件树、五态、交互细节、响应式、文案；后端设计含表结构、校验、错误码、事务、幂等、权限、分页、性能边界；需求追踪矩阵覆盖全部 R。
- **任务门**：任务 ≤1 会话，有关联需求/涉及文件/验收标准/测试要求/依赖；全部 R 被覆盖；先最小端到端。
- **完成门（DoD）**：功能真实可用；测试通过；前端/后端自检通过；tasks、overall、record 三处已更新；无范围外改动或已登记。

## 会话收尾清单

- [ ] 文档与代码不矛盾；状态不乐观
- [ ] 记录/变更文件路径真实存在
- [ ] 验证命令与结果如实记录（不能运行则说明原因）
- [ ] 假设 A-xx 与未决问题 Q-xx 在回复中显式列出
- [ ] 给出下一任务或下一检查点

## 资源

- `references/quality-gates.md`：需求门 / 设计门 / 任务门 / DoD / 放飞自我反模式 / 文档写作规范
- `references/frontend-quality.md`：前端设计阶段产出要求、实现基准、浏览器自检流程
- `references/backend-quality.md`：后端设计阶段产出要求、实现基准、接口验证流程
- `references/planning-guide.md`：需求梳理问题清单、BRD 写作指南、模块拆分与任务拆分原则、存量项目调研清单
- `templates/`：discovery、brd、requirements、design、tasks、task-list-overall、record、change、manual-test-checklist
- `scripts/init_spec.py`（脚手架）、`scripts/check_spec.py`（追踪与一致性检查）
