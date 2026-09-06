# v2.0.0 验证报告

交付日期：2026-09-06（Asia/Tokyo）。日志使用 UTC 时间；若日志为 9 月 5 日，属于时区差异，不是补造执行时间。
基线提交：11ce270ed74c86027334f7aae01805912645e99b。

## 实际执行

| 项目 | 结果 | 证据 |
| --- | --- | --- |
| 解析/状态/追踪/证据/路径/CLI/包一致性回归 | 116 项通过，0 失败，0 跳过 | [self-tests](validation/self-tests.txt) |
| 可执行 CSV 函数示例 | 10 项实际测试通过 | [示例日志](examples/m-filter-export/spec/evidence/unittest.txt) |
| M 示例 done + 总览一致性 | 退出码 0 | [结果](validation/m-done.json) |
| L 滚动规划 ready + 总览一致性 | 退出码 0 | [结果](validation/l-ready.json) |
| 未批准的 L 请求进入实施 | 正确拒绝，退出码 1 | [反例结果](validation/l-no-approval.json) |
| Skill 包 | 入口名称/版本/长度、Markdown 链接、脚本语法、示例及 eval 状态已检查 | 包一致性测试 |

环境：Python 3.13.5；Linux-6.18.35-x86_64-with-glibc2.41。
脚本设计要求 Python 3.10+，但本次只在上述解释器实际运行；不声称其他版本或操作系统已实测。

## 覆盖的原审计问题

重复需求/任务不再被后值覆盖；依赖成环/自依赖/不存在被拒绝；废弃任务不计覆盖；AC 必须由当前有效任务承接。
完成记录缺失、空文件、目录冒充、任务不匹配、日期非法、验证版本缺失、未运行/不适用冒充 required 通过、空证据与过期任务指纹均有反例。
已开始任务依赖未完成任务被拒绝；scope 改变使批准过期；生成总览的篡改/缺失可检测。
脚手架覆盖、路径越界、符号链接、短码冲突、M/L 混合布局及不经许可的自动升级均有测试。
完整用例名称可在测试日志和 tests/ 中核对。

## 限制与未执行

没有运行真实 Coding Agent 的跨模型/A-B 评估、长会话或真实多 Agent 并行；evals/ 的 14 个场景标记为 not_run。
没有浏览器/UI/真实后端环境集成，没有运行用户业务仓库，没有向 GitHub 写入、创建 PR、发布版本或提交代码。
M 示例是真实小型纯函数执行；L 示例只是规划结构。不能把其 ready 结果视为 UI/接口实现或可运行性证明。
结构检查无法证明自然语言验收正确、测试命令真的运行、批准者身份真实、CI 内容有效或源码符合 Spec。
字段与 hash 只能减少误用/过期风险，不是密码学签名、代码安全沙箱或分布式锁。

## 重跑

从 Skill 根目录运行 `python3 -m unittest discover -s tests -v`。
从 examples/m-filter-export 运行 `python3 -m unittest discover -s . -p 'test_*.py' -v`。
机器可读摘要在 [results.json](validation/results.json)。修改代码后应重跑相关检查；包内旧日志不代表修改后的结果。
