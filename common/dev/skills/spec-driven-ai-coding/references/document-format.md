# v2 文档与脚本契约

## 文件职责

M：requirements.md（唯一行为/AC）+ design.md（实现方案）+ tasks.md（唯一任务块）+ spec.json（批次、批准、分工）。
L：brd.md（业务范围）+ modules/module-*/{requirements,design,tasks}.md + spec.json。
records、changes、acceptance、discovery、handoff 按需创建；不预填空文件。
task-list-overall.md 完全生成，可选；M 无须它，L 也不靠它维护事实。

不用 Python 时可手工执行规范；旧格式不要求迁移。以下精确格式仅适用于选择使用 v2 检查器的文档。

## Markdown 子集

实体声明必须是 `### BR-01 标题`、`### R-APP-01 标题`、`### T-APP-01 标题`，编号与标题用空格分隔。
实体直到下一个同级或更高标题结束；其元数据表必须在首个 `####` 小节之前。
表格列名精确匹配模板，每行以 | 开始和结束；单元格内字面量管道（含代码中的管道）写成 `\|`。
不支持多行表格单元格；长步骤放文字小节，表格写简短步骤/引用。脚本不是任意 Markdown 或旧版表格的通用解析器。
实体外的 fenced code/HTML 注释内的假 ID 不作声明。围栏/注释必须闭合。
不要在同一文档重复同名权威章节或复制第二份元数据表。

## 编号

模块 code：字母开头，1–32 位大写英文字母/数字/下划线。目录 slug 是小写字母/数字、单个 -/_ 分段。
代码可用 `ORDER_CENTER`；脚手架拒绝 a-b 与 a_b 产生同一个 code。它不会静默截短编号。

- BR-01：业务目标。
- R-APP-01：模块需求；meta 的状态 active/deferred/retired、批次 I1/I2…。L 来源为 BR ID 列表，M 来源为真实请求/原文定位。
- AC-APP-01-1：R-APP-01 的验收标准。精确格式 `- AC-APP-01-1: 条件、操作、结果`，不要用复选框维护执行状态。
- T-APP-01：任务。需求/验收/依赖列表以逗号分隔，空列表用 `-`。
- V-APP-01-1：T-APP-01 的验证项，类型 unit/component/interface/browser/integration/static/manual/other。
- A-01/Q-01：持久化假设/问题，状态只在 spec.json decisions 中维护。

任务不复制 AC 内容；record 通过 AC→V→证据建立追踪。一个 AC 可有多个任务与多个检查，当前 AC 必须被当前批次的非废弃任务覆盖。

## spec.json

脚手架生成完整结构。schema_version 固定 2；tier 为 M/L；risk 为 low/medium/high；current_increment 必须引用 increments。
modules 明确 slug/code/path，M 的 path 为 `.`，L 为 `modules/module-<slug>`；模块数量、名称、code 和目录须一致，不通过文件存在性推断规模。

每个 increment 包含：

| 字段 | 值 |
| --- | --- |
| id / title | I1 等稳定 ID 与名称 |
| status | planning / implementing / verifying / accepted |
| approval.state | pending / approved / delegated |
| approval.by / basis | 实际确认人、可定位的批准/授权依据；不能自填“用户同意”而没有来源 |
| approval.digest | 当前 scope_digest；由 checker 输出，不手算、不把写入 hash 当批准 |
| acceptance.state | pending / accepted |
| acceptance.by / basis / record | 实际验收来源与相对 spec 根的验收记录路径 |
| acceptance.digest | checker 的 increment_digest，不是 scope_digest |

规划文件完成后运行 ready；确认或获得明确授权后，把真实来源和最新 scope_digest 写入 approval。
任务状态变化无需反复批准。范围/AC/相关约束变化使摘要失效；重要设计风险变化也必须显式撤回批准，工具不能推断所有自然语言影响。

决策对象：id、increment、blocking（JSON boolean）、state（open/resolved）、text、resolution。
当前阻断的 open 项让 ready 不通过；未来批次和非阻断项不妨碍当前增量。resolved 必须有结论。
parallel.enabled 默认 false；开启时必须有 integrator；shared_files 为 `{path, owner}` 对象数组。

## 路径与写集

Spec 文件/record/file:证据路径均相对 spec 根。源码写集相对业务仓库根。
使用 `/`，不允许绝对路径、盘符、`..`、URL、反斜线或 glob；目录前缀如 `src/export/` 可用。
脚本拒绝所读 Spec 入口中的符号链接，避免无意跨目录读取/写入；Skill 安装目录本身可由宿主管理，不影响此限制。
路径与文档引用不能自动授予写入代码、读取敏感数据或外部联网权限。

## 状态与 record

tasks.md 字段按模板：状态、批次、需求、验收、依赖、写集、负责人、依赖确认、完成日期、实施记录、集成版本。
已完成需要合法 YYYY-MM-DD 日期、非空 record 普通文件。日期要与 record 一致。
record 的任务、环境、实际验证版本和任务指纹必须存在；版本使用真实 commit 或可复核工作树快照，不能只写“最新版”。

每项 V 记录通过/失败/未运行/不适用；已完成时 required 必须通过，na 必须不适用且计划中有理由。
每个 AC 必须映射到至少一个通过、有证据的 required 检查。记录的多余/重复检查或 AC 也会报错。
证据格式：

| 前缀 | 说明 |
| --- | --- |
| file: | 相对 spec 根的非空 UTF-8 日志/报告，checker 检查路径与非空；二进制截图应放在文本索引中引用 |
| inline: | 实际输出/观察摘要，须非空；不能只重复“测试通过”而没有可核对事实 |
| ci: | 实际 CI 运行地址或 ID；checker 不联网核验 |
| tool: | 实际工具调用/截图轨迹 ID；checker 不核验外部宿主轨迹 |

`实际结果` 与 `风险与未执行项` 不能留空。原始日志不能包含密钥/个人数据；脱敏并保留可定位性。

## 三种指纹

scope_digest：当前 active R、相关 BR 和这些需求文档实体外的范围/约束文本，加批次与风险。
任务状态、普通实现设计不参与范围摘要；需求文件外层路线图等文字修改也可能触发保守的重新确认。
task_digests：该任务的目标、批次、AC、依赖、写集、实现/验证计划和关联需求语义。进度、负责人和记录路径不参与。
increment_digest：scope_digest 与当前有效任务指纹集合。用于发现整体验收后增加/调整任务。

取值：`python3 <skill>/scripts/check_spec.py <root> --stage draft --json`。
这些摘要不校验源码内容。即使摘要未变，代码变了也必须重新运行受影响检查并记录新版本。

## CLI 与退出码

check_spec.py：默认 ready；--stage draft/ready/done；--require-approval；--check-overall；--json。成功 0，发现错误 1，argparse 用法错误 2。
init_spec.py：--root --feature --tier --risk；M 可 --code；L 用 --modules，可 --with-common；可 --with-discovery --date --dry-run。
init 只创建全新目标，绝不覆盖/追加/自动升级。所有输入先检查；磁盘写入中断时保留现场并报错，不静默修复。
render_overall.py：默认 stdout，--write 只覆盖带本工具生成标记的总览，拒绝覆盖旧人工总览；采用同目录临时文件后替换。
脚本无运行时第三方依赖、不联网、不执行 Spec 内命令。不要把验证器当作可信代码沙箱或并发锁。
