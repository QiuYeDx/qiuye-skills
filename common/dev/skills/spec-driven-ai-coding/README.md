# Spec-Driven AI Coding · v2.0.0

按规模选择文档量，按风险决定确认与验证强度，按证据判断完成。

这是 `QiuYeDx/qiuye-skills/common/dev/skills/spec-driven-ai-coding` 的完整重写包，基于审计时的提交 `11ce270ed74c86027334f7aae01805912645e99b`。包含 Skill 指令、参考规范、模板、脚本、测试、示例与评估场景；不是只改了 SKILL.md 的补丁。

## 和旧版最关键的区别

| 旧版容易遇到的情况 | v2 |
| --- | --- |
| 文件多/跨前后端/未知问题直接升大流程 | 文档规模、风险、探索需求分开判断 |
| 任何 fix 都先改 BRD | 修复实现偏差保留正确 AC；行为变更才改需求 |
| 一次会话只做一个任务 | 同一时刻一个任务，完成后可连续做已批准任务 |
| 全部模块设计完才开始 | 只细化当前增量，未来需求可 deferred |
| common 必建且全部先完成 | common 可选，业务契约有归属，先实现当前链路所需共享能力 |
| tasks/overall 双份手工状态 | tasks 单源，总览生成，spec.json 只维护批次/批准/分工 |
| UI 全部强制五态/全部接口强制鉴权 | 按实际状态、访问策略和影响面制定验证；不适用要有理由 |
| 文件存在/脚本绿了就继续 | 结构通过、范围批准、实际验证、集成验收明确区分 |
| 完成记录仅检查是否存在 | AC→检查→证据、版本/日期/环境、任务指纹与过期检测 |

v2 的理念不是增加审批：低风险小改仍直接做；可逆内部决策由 Agent 处理。真正的需求、权限、数据风险与验证缺失不能被流程形式掩盖。

## 安装

解压后得到一个名为 `spec-driven-ai-coding/` 的目录。

**替换自己的 Skills 仓库：** 将整个目录放到 `qiuye-skills/common/dev/skills/spec-driven-ai-coding/`。先备份/提交旧目录和未提交改动，再替换；不要把新 SKILL.md 与旧脚本混装。

**Codex 项目内安装：** 放入目标项目 `.agents/skills/spec-driven-ai-coding/`；用户级可放入 `~/.agents/skills/spec-driven-ai-coding/`。避免同名新旧版本同时被扫描。安装目录说明依据见 SOURCES.md；其他宿主按其 Skill 安装规则使用。

没有改动远程 GitHub。远程安装命令在你提交新版之前仍会取得仓库当前版本，不会自动取得本压缩包。
完整替换与旧项目兼容见 [migration](references/migration.md)。仓库根 README 的同步建议见 [integration-notes](integration-notes.md)。

## 怎么开始用

在支持 `$skill` 调用的 Coding Agent 中：

```text
$spec-driven-ai-coding
为现有导出功能增加“导出筛选结果”。先读取现状，采用最小合适流程。
只规划当前增量，保留既有行为，给出可验证的 AC。
```

连续实施的明确授权示例：

```text
$spec-driven-ai-coding
按已经确认的当前范围连续实施，不要每个任务完成后都停下。
内部可逆细节沿用项目惯例。遇到需求改变、权限/数据风险或必要验证无法完成时停止并说明。
```

修复已有功能：

```text
$spec-driven-ai-coding
修复 T-EXPORT-01：原 AC 要求导出筛选结果，实际导出全部记录。
不要为了迁就现状改 AC，先复现并补回归测试；只更新必要文档。
```

默认允许宿主按精确 description 匹配；不因任意 feat/fix/coding 字样启动整套流程。
Codex 中需要完全显式调用时，把 `agents/openai.yaml` 的 `allow_implicit_invocation` 改为 `false`。其他宿主可能不识别此可选元数据；没有声称跨宿主自动触发行为已实测。

## 实际会生成多少文档

S：一般只有对话里的目标/验收/结果，不自动创建文件。
M：requirements.md、design.md、tasks.md、spec.json，三份 Markdown 可以很短。record 在实际执行后创建，其他文件按需。
L：粗粒度 brd.md、当前需要的模块三件套、spec.json；后续增量不必预写所有设计/任务。overall 是可选的只读视图。
Skill 包里的 templates/references/evals 不是每个业务项目都要复制的文件，Agent 按当前任务选用。

## 辅助工具

要求 Python 3.10+，仅用标准库，不需要 pip 安装、不联网、不执行 Spec 内命令。
以下从本 Skill 根目录运行；`/path/to/project` 替换为实际业务项目位置。

```bash
# 只预览生成路径
python3 scripts/init_spec.py --root /path/to/project/docs/开发设计文档 --feature export --tier M --risk low --dry-run
# 创建新 M（去掉 --dry-run 才写入）
python3 scripts/init_spec.py --root /path/to/project/docs/开发设计文档 --feature export --tier M --risk low
# 创建新 L；不默认添加 common
python3 scripts/init_spec.py --root /path/to/project/docs/开发设计文档 --feature order-center --tier L --modules order,report

python3 scripts/check_spec.py /path/to/spec --stage draft
python3 scripts/check_spec.py /path/to/spec --stage ready
python3 scripts/check_spec.py /path/to/spec --stage ready --require-approval
python3 scripts/check_spec.py /path/to/spec --stage draft --json
python3 scripts/check_spec.py /path/to/spec --stage done
python3 scripts/render_overall.py /path/to/spec --write
python3 scripts/check_spec.py /path/to/spec --stage ready --check-overall
```

脚手架保留待填的内容，因此全新骨架预期能过 draft、不能过 ready。**ready 通过不是批准动作。** 批准信息须来自真实用户/项目授权；脚本没有“自动批准”命令。
Windows 可用已安装的 `python` 或 `py -3` 调用同一脚本；本包的实际运行环境和未测平台见 VALIDATION.md。

## 包内容

```text
spec-driven-ai-coding/
  SKILL.md                 # Agent 入口；按需加载下面资源
  agents/openai.yaml
  references/              # 流程、规划、质量、协作、格式、迁移
  templates/               # 按需使用的 Markdown 模板
  scripts/                 # init / check / render + 共享实现
  tests/                   # 解析、门禁、路径、CLI、包一致性回归
  examples/                # 真正运行过的函数示例 + 未实施的 L 规划示例
  evals/                   # Agent 行为评估场景，未假装已经执行
  validation/              # 本次运行日志与机器可读结果
  VALIDATION.md            # 验证范围、结果与局限
  CHANGELOG.md
  integration-notes.md
  SOURCES.md
```

## 自检与示例

```bash
python3 -m unittest discover -s tests -v
python3 scripts/check_spec.py examples/m-filter-export/spec --stage done --check-overall
python3 scripts/check_spec.py examples/l-rolling/spec --stage ready --check-overall
# 以下预期失败：L 示例没有用户批准
python3 scripts/check_spec.py examples/l-rolling/spec --stage ready --require-approval
```

实际导出函数测试在 `examples/m-filter-export/` 中运行：

```bash
python3 -m unittest discover -s . -p 'test_*.py' -v
```

## 兼容性与诚实边界

Skill 目录可以整体替换，但 v2 辅助检查器不是 v1 文档格式的无缝替代品。已有 v1/其他格式可以继续人工遵循工作流；需要机械检查时再按迁移指南转换。
检查器防止许多确定性的漏检与状态过期，不证明自然语言需求正确、不验证用户身份、不执行测试、不审查源码、不提供分布式锁。
无浏览器/真实后端时必须保留必要验证缺项。当前自动化与示例测试不能替代真实多 Agent、长会话或各宿主的行为评估。
更详细的字段和限制见 [document-format](references/document-format.md)，未来行为评估见 [evals](evals/README.md)。
