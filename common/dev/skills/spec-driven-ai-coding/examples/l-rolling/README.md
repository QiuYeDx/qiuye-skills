# L 滚动规划示例（未实施）

I1 展开 ingest/preview 两个模块；I2 只有 deferred 的 BR-02，无模块细节和任务。没有强制 common。
全部任务未开始，批准 pending；ready 检查可通过，但 --require-approval 必须失败。
“结构可读”不是代码存在、命令有效或业务设计已经批准。本例尚未运行 pnpm/浏览器，也没有多 Agent 实测。

```bash
python3 ../../scripts/check_spec.py spec --stage ready --check-overall
# 预期非零：当前批次没有批准
python3 ../../scripts/check_spec.py spec --stage ready --require-approval
```

接入真实项目时先核对命令/现状与契约，做语义审查，再确认当前批次。不能复制本例的拟定路径后直接宣布完成。
