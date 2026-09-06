# 解析与校验本地记录设计

## 现状与约束

这是独立规划示例，尚无实际业务仓库可调研；命令/代码路径是拟定落点，接入项目时必须先核对。

## 方案与取舍

解析模块拥有 ParseError/ImportRow 与 parse 接口定义；预览模块引用 modules/module-ingest/design.md，不建立强制 common 模块。
parse(text: string, size: number): ImportRow[]；ImportRow 为 id/name 字符串；ParseError.code 为 INVALID_JSON、INVALID_ROW、DUPLICATE_ID、LIMIT_EXCEEDED。
当前串行先实现解析再完成真实预览；不从局部测试推断浏览器已验证。

## 代码落点

src/import/parse.ts, tests/import/parse.test.ts。

## 需求映射

| 需求 | 设计元素 |
| --- | --- |
| R-INGEST-01 | src/import/parse.ts 的当前增量实现 |

## 验证与风险

pnpm test -- tests/import/parse.test.ts。命令在接入业务项目后核对；目前只校验规划结构，不声称运行成功。
