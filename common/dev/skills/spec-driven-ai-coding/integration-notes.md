# 合入 qiuye-skills 的建议

本包不更改远程仓库。维护者先检查本地未提交改动，再整体替换 `common/dev/skills/spec-driven-ai-coding/`。
旧目录备份移到 Skill 扫描路径之外，不并排保留同名版本。不要只覆盖一部分文件。

## 仓库根 README 简介建议

可把原 `spec-driven-ai-coding` 段落更新为：

> 按规模、风险和不确定性选择流程。S 轻量开发；M 使用小三件套与批次元数据；L 采用滚动规划，仅细化当前可交付增量。保留需求/验收追踪、真实验证和可恢复交接，区分 bugfix 与需求变更。任务状态单源，总览生成；内置分阶段结构检查、批准/证据过期检测、受控技术实验与按实际写集协调的可选并行规范。旧业务文档可继续沿用，机械检查迁移需显式进行。

目录概览补充 scripts/spec_core.py、render_overall.py、tests、examples、evals、spec.json 的运行说明；不要继续声称 common 必建或任何 fix 都要改 BRD。
触发词收窄到明确的 Spec 规划/实施/续接/协作，而非任意 feat/fix。

## 本地检查

从仓库根运行：

```bash
python3 -m unittest discover -s common/dev/skills/spec-driven-ai-coding/tests -v
python3 common/dev/skills/spec-driven-ai-coding/scripts/check_spec.py common/dev/skills/spec-driven-ai-coding/examples/m-filter-export/spec --stage done --check-overall
python3 common/dev/skills/spec-driven-ai-coding/scripts/check_spec.py common/dev/skills/spec-driven-ai-coding/examples/l-rolling/spec --stage ready --check-overall
```

若添加 CI，可把同样命令放到仓库既有 Python 工作流，不需要新建一套发布基础设施。没有替仓库自动创建 CI 或 release。
先在一个真实 M 功能和一个真实 bugfix 上观察文档维护量、打断次数和验证质量，再决定是否作为广泛默认规则。
