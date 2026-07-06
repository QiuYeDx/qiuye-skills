# Smooth Corners Skill 执行计划

创建日期：2026-07-06
更新日期：2026-07-06

## 使用方式

每次继续开发 Smooth Corners Skill 前，先阅读：

- `docs/开发设计文档/smooth_corners_skill_final_design.md`
- `docs/开发设计文档/smooth_corners_skill_execution_plan.md`
- `qiuye-shadcn_ui/docs/设计并开发SmoothCorners组件/SmoothCorners组件开发设计文档.md`

本计划只覆盖 `qiuye-skills` 仓库。QiuYe UI 组件实现以 `qiuye-shadcn_ui` 的执行计划为准。

## 状态规则

- `未开始`：尚未动工。
- `进行中`：已有改动但未完成验证。
- `已完成`：实现与验证均已完成。
- `阻塞`：缺少外部信息或环境不可用。
- `废弃`：不再实施。

## 进度台账

| 工作包 | 状态 | 完成日期 | 关键文件 | 验证 | 实施记录 | 未决事项 |
| --- | --- | --- | --- | --- | --- | --- |
| SK-1 Skill 骨架创建 | 已完成 | 2026-07-06 | `frontend/ui-ux/skills/smooth-corners/SKILL.md`, `agents/openai.yaml` | `init_skill.py`，`quick_validate.py` | `docs/开发设计文档/smooth_corners_skill_implementation_records/2026-07-06_SK-1-SK-5_qiuye-smooth-corners-skill.md` | 无 |
| SK-2 实现模板参考文档 | 已完成 | 2026-07-06 | `frontend/ui-ux/skills/smooth-corners/references/implementation-recipes.md` | 模板静态检查，源码公式对照 `smooth-corners-web/src/core.js` | `docs/开发设计文档/smooth_corners_skill_implementation_records/2026-07-06_SK-1-SK-5_qiuye-smooth-corners-skill.md` | 无 |
| SK-3 README 注册 | 已完成 | 2026-07-06 | `README.md` | `rg -n "qiuye-smooth-corners|@qiuye-ui/smooth-corners|@qiuyedx/smooth-corners" ...` | `docs/开发设计文档/smooth_corners_skill_implementation_records/2026-07-06_SK-1-SK-5_qiuye-smooth-corners-skill.md` | 无 |
| SK-4 验证与前向测试 | 已完成 | 2026-07-06 | Skill 目录 | 临时 venv 执行 `quick_validate.py` 通过；静态引用检查通过 | `docs/开发设计文档/smooth_corners_skill_implementation_records/2026-07-06_SK-1-SK-5_qiuye-smooth-corners-skill.md` | 未执行 subagent 前向测试 |
| SK-5 与 QiuYe UI 组件发布同步 | 已完成 | 2026-07-06 | `SKILL.md`, `references/implementation-recipes.md` | Skill 明确 shadcn 项目优先 `@qiuye-ui/smooth-corners`，底层包为 `@qiuyedx/smooth-corners@0.1.0` | `docs/开发设计文档/smooth_corners_skill_implementation_records/2026-07-06_SK-1-SK-5_qiuye-smooth-corners-skill.md` | 需等站点部署后做真实 registry 安装抽检 |

## 依赖顺序

1. 先做 `SK-1`：按 `skill-creator` 规则创建最小 Skill 目录。
2. 再做 `SK-2`：补充代码模板和无依赖兜底。
3. 再做 `SK-3`：README 注册，保证可发现。
4. 做 `SK-4`：验证 frontmatter、触发描述和 references 路径。
5. `SK-5` 等 QiuYe UI 组件和 npm 包路径稳定后再更新推荐命令。

## 不可违反的工程约束

- `SKILL.md` frontmatter 只写 `name` 和 `description`。
- Skill 名称使用小写连字符，推荐 `qiuye-smooth-corners`。
- 不创建 README、CHANGELOG、安装指南等额外说明文件。
- 长代码模板放入 `references/implementation-recipes.md`，不要塞满 `SKILL.md`。
- 触发描述必须覆盖中文和英文意图。
- `@qiuyedx/smooth-corners@0.1.0` 已发布；但 shadcn/ui 项目仍必须优先推荐 `@qiuye-ui/smooth-corners`。
- references 文件必须由 `SKILL.md` 明确说明何时读取。

## 实施记录模板

后续实现会话需要在：

```text
docs/开发设计文档/smooth_corners_skill_implementation_records/
```

新增记录：

````markdown
# 工作包 <ID>：<标题>

## 基本信息

- 日期：
- 状态：已完成 / 部分完成 / 阻塞
- 对应执行计划工作包：

## 本次实现内容

-

## 修改文件

-

## 接口或数据结构变化

-

## 验证结果

执行命令：

```text

```

结果：

-

## 未完成事项

-

## 下一步建议

-
```
````

## 验证建议

优先运行 skill validator。如果只能静态检查，至少确认：

```text
rg -n "^name:|^description:" frontend/ui-ux/skills/smooth-corners/SKILL.md
rg -n "qiuye-smooth-corners|smooth-corners" README.md frontend/ui-ux/skills/smooth-corners/SKILL.md
```

可选前向测试提示词：

```text
Use $qiuye-smooth-corners to add Figma-style smooth corners to a React card component. Prefer package usage if appropriate, but provide a no-dependency fallback if dependencies are not allowed.
```

## 下一步建议

当前计划内工作包均已完成。下一步建议在 QiuYe UI 站点部署后，用一个临时 shadcn/ui 项目真实执行 `shadcn add @qiuye-ui/smooth-corners` 做安装抽检。
