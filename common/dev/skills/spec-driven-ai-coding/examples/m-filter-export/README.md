# 可执行 M 格式演示：筛选导出

本例用于演示完整 Spec→任务→真实测试→record 链路。现实中这种纯函数小改通常用 S 即可，不应为所有小函数生成 M 文档。

从本目录运行：

```bash
python3 -m unittest discover -s . -p 'test_*.py' -v
python3 ../../scripts/check_spec.py spec --stage done --check-overall
```

spec/records/T-EXPORT-01.md 和 spec/evidence/unittest.txt 是构建包时实际运行的结果，不是 mock 日志。
批准范围仅为本地演示代码；没有用户业务仓库批准、远程合并或人工验收声明。批次保持 verifying，acceptance 保持 pending。
任务指纹与源码快照用途不同；重新修改示例代码后必须重新执行测试，checker 不会替你运行或检查源码 hash。
