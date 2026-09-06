# 示例任务

### T-EXPORT-01 实现并验证筛选导出纯函数

| 字段 | 值 |
| --- | --- |
| 状态 | 已完成 |
| 批次 | I1 |
| 需求 | R-EXPORT-01, R-EXPORT-02 |
| 验收 | AC-EXPORT-01-1, AC-EXPORT-01-2, AC-EXPORT-01-3, AC-EXPORT-02-1, AC-EXPORT-02-2 |
| 依赖 | - |
| 写集 | export_rows.py, test_export_rows.py |
| 负责人 | 示例包构建者 |
| 依赖确认 | - |
| 完成日期 | 2026-09-06 |
| 实施记录 | records/T-EXPORT-01.md |
| 集成版本 | - |

#### 实现要点

校验输入与筛选枚举，复制行后导出 CSV，处理规定的公式前缀；用标准库单测覆盖所有 AC。

#### 验证计划

| 检查 | 类型 | 要求 | 命令或步骤 | 不适用理由 |
| --- | --- | --- | --- | --- |
| V-EXPORT-01-1 | unit | required | 在示例目录执行 python -m unittest discover -s . -p 'test_*.py' -v | - |
