# spec-driven-ai-coding 维护资料

[`common/dev/skills/spec-driven-ai-coding`](../../common/dev/skills/spec-driven-ai-coding/) 的回归测试、行为评估场景与验证日志。这些文件只服务维护，不随 Skill 安装分发。

```bash
# 在本目录运行；测试按相对路径定位 Skill 目录
python3 -m unittest discover -s tests -v
```

- `tests/`：解析、门禁、路径、CLI 与包一致性回归（Windows 可用 `python` / `py -3`）
- `evals/`：Agent 行为评估场景，状态为 `not_run`，不是测得成绩
- `validation/`、`VALIDATION.md`：历次版本的运行日志、范围与局限
