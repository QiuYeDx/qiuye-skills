# 预览结果与错误反馈设计

## 现状与约束

这是独立规划示例，尚无实际业务仓库可调研；命令/代码路径是拟定落点，接入项目时必须先核对。

## 方案与取舍

解析模块拥有 ParseError/ImportRow 与 parse 接口定义；预览模块引用 modules/module-ingest/design.md，不建立强制 common 模块。
签名、数据类型和错误码唯一维护在 ../module-ingest/design.md 的「方案与取舍」；本模块只消费该契约，不复制第二套定义。
当前串行先实现解析再完成真实预览；不从局部测试推断浏览器已验证。

## 代码落点

src/import/Preview.tsx, tests/import/preview.test.tsx。

## 需求映射

| 需求 | 设计元素 |
| --- | --- |
| R-PREVIEW-01 | src/import/Preview.tsx 的当前增量实现 |

## 验证与风险

在隔离浏览器中依次导入合法/非法文件并验证保留结果、重试与键盘焦点。命令在接入业务项目后核对；目前只校验规划结构，不声称运行成功。
