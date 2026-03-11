# qiuye-skills

精心整理的 Agent Skills 仓库，用于沉淀可复用的工程能力、团队规范与领域知识。

## 设计目标

- 分层治理，避免技能散落和命名冲突
- 路径结构统一，保证可检索、可审阅、可演进
- 每个技能目录最小可用单元固定为 `SKILL.md + 辅助文档`
- 所有技能最终目录层级统一为：`.../.../skills/<xxx skill>/<SKILL.md 和其他资产>`
  如 `frontend/ui-ux/skills/.../SKILL.md`

## 目录约定

推荐目录结构示例：

```text
frontend/ui-ux/skills/
  ├── skill-A/
  │   ├── SKILL.md
  │   └── ...
  └── skill-B/
      ├── SKILL.md
      └── ...
```

## Skills 安装指引

以下命令可用于从本仓库安装 skills：

### 1) 普通使用示例

```bash
npx skills add https://github.com/qiuyedx/qiuye-skills.git
```

### 2) 安装特定子路径下的 skill

直接复制 GitLab 子路径页面链接即可安装对应目录下的 skills：

```bash
npx skills add https://github.com/qiuyedx/qiuye-skills/-/tree/master/frontend/ui-ux/skills
```

### 3) 查看 skills 列表

```bash
npx skills add https://github.com/qiuyedx/qiuye-skills.git --list
```

### 4) 安装指定某个 Skill

`skill-name` 为 `SKILL.md` 头部 `name` 字段，且在仓库中全局唯一：

```bash
npx skills add https://github.com/qiuyedx/qiuye-skills.git --skill <skill-name>
```

## 维护建议

- 新增技能时优先保证命名清晰、场景明确
- `SKILL.md` 应提供最小可运行示例与边界说明
- 辅助文档建议按 `reference`、`recipes`、`examples` 拆分，便于检索与维护
