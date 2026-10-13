# Skills 全量审查：修复 / 优化工作文档

创建日期：2026-10-13
基线提交：`6258e64`
范围：仓库内全部 10 个 Skill + 根 README

状态标记：`[ ]` 待处理 · `[x]` 已完成 · `[-]` 决定不做（附原因）

## 决策记录

| 决策 | 结论 | 原因 |
|---|---|---|
| 目录名与 `name` 不一致 | 目录改名对齐 `name`（`smooth-corners/` → `qiuye-smooth-corners/`，`edge-gradient-mask/` → `qiuye-edge-gradient-mask/`）；不增删其他 Skill 的 `qiuye-` 前缀 | `--skill <name>` 不变，已安装用户零影响；前缀统一会改名破坏安装命令，收益不足 |
| spec-driven 维护资料位置 | 移到仓库 `dev/spec-driven-ai-coding/`（tests、evals、validation、VALIDATION.md）；删除 PACKAGE-MANIFEST.json、integration-notes.md；保留 examples（SKILL.md 引用） | 安装包只保留运行时所需内容 |

---

## 第 1 步：修正错误内容（Agent 照做会直接产出 bug）

- [x] **E1** motion-recipes Case 7 推荐“独立 blur 柔影层 + opacity 淡出”，与 frontend-pitfalls Case 3 坑 4/5 结论冲突。改为共享静止阴影 + `--lift`，并互相链接。
  `motion-recipes/cases/container-transform-morph.md` §6、策略 B 代码
- [x] **E2** edge-gradient-mask 模板 B：absolute 遮罩放在 `overflow-auto` 容器内部，会随内容滚走。改为外层 relative 包裹、遮罩为滚动容器兄弟节点。
- [x] **E3** edge-gradient-mask 模板 E：径向 mask 中心透明、外围不透明，与“边缘柔和消失”相反。
- [x] **E4** edge-gradient-mask 模板 A：`isolate` 限制 blur 范围的说法错误；缺 `WebkitBackdropFilter`；`oklch(from var(--background))` 在 HSL 分量变量下失效需回退；“Safari 必须 -webkit-mask-image”过时；折叠遮罩缺 `aria-hidden`。
- [x] **E5** smooth-corners 原生 JS 示例 `Object.assign(el.style, …)` 写不进 `--sc-*`，改为 `setProperty`。
- [x] **E6** spec-driven 测试在非 UTF-8 系统失败（`read_text/write_text` 未指定 encoding）；脚本 stdout 在 Windows 为 GBK。
- [x] **E7** motion-recipes `assets/flow-transition.tsx`：`getBoundingClientRect` 受祖先 transform 影响；缺 `"use client"`；`following` 标记可能卡住。Case 5 同类测量问题及 `height > 0` 误判“已测量”。
- [x] **E8** frontend-pitfalls 鼠标拖拽：阈值内松手于行外后 `pointerId` 残留，悬停即拖拽；move 中检查 `buttons`。
- [x] **E9** 次要技术细节：
  - smooth-corners 尺寸感知阈值应基于补偿后半径 `r*(1+s)`
  - smooth-scroll MutationObserver 被 Lenis 自身 class 变化触发；全局 `scroll-behavior: smooth` 影响路由重置
  - glass-blur case 中 `transform/contain/isolation` 不会破坏 backdrop 采样，需与“改变层叠”区分
  - geometric：computed mask 为 `none` 的回退检测不可靠；羽化起始帧提前露出

## 第 2 步：触发与路由治理

- [x] **T1** project-pitfall-guard：收紧触发（去掉“starts work”“best practices”）；宿主中立（Claude Code `.claude/skills` + Codex `.agents/skills`），脚本加 `--skills-dir`；检测命令跨平台；中文项目名 slug 冲突；`--force` 不覆盖 index；表格 `|` 与 YAML 转义。
- [x] **T2** frontend-pitfalls description 924 字符 → 精简，触发词移入正文。
- [x] **T3** geometric-mask-transition description 960 字符 → 精简。
- [x] **T4** motion-recipes：description 去掉路由指令；理顺 Case 2/5/6/9 循环引用；压缩“场景匹配指南”与索引重复。
- [x] **T5** qiuye-ui-quality：收窄触发；SKILL.md 改为主流程 + 症状→reference 路由表，细节下沉。
- [x] **T6** edge-gradient-mask：补反向排除与中文触发词；补 `agents/openai.yaml`。
- [x] **T7** spec-driven：SKILL.md 中前端规则约 10 处重复 → 1 条边界规则 + 1 个指针；openai.yaml 中立化。
- [x] **T8** motion-recipes 补 `agents/openai.yaml`。

## 第 3 步：仓库一致性

- [x] **R1** 目录名对齐 `name`（见决策记录），同步 README、docs 内路径。
- [x] **R2** README 子路径安装命令改为 GitHub 写法（`/tree/main/...`）。
- [x] **R3** README motion-recipes case 数（8 → 9）。
- [x] **R4** README 目录树补 smooth-corners、`staggered-grid-transitions.md`；geometric 触发词与 frontmatter 对齐。
- [x] **R5** 新增 `.gitattributes`（`* text=auto eol=lf`）。
- [x] **R7** README 说明 `docs/` 用途。

## 第 4 步：瘦身与去重

- [x] **S1** spec-driven 维护资料移出安装目录；README/CHANGELOG 去掉“压缩包交付”口吻；删除已完成的 `integration-notes.md`。
- [x] **S2** PACKAGE-MANIFEST.json：随 S1 移走或删除。
- [x] **S3** 嵌套圆角 / hover 内缩规则只保留一处权威来源，其余链接。
  ui-quality 内部以 `visual-insets-and-contours.md` 为唯一来源，SKILL.md 收为一句并链接；smooth-corners 保留平滑圆角特有的补偿半径与分角内容，通用方法改为指向 ui-quality（两个 Skill 独立安装，不做跨 Skill 相对链接）。
- [-] **S4** 项目专属信息（QiuVision、`--city-intro`、Mermaid 注释、设备轶事等）从通用正文移到来源说明。
  仅移除未标注来源的泄漏（smooth-scroll 模板中的“fullscreen Mermaid”注释）。其余均已明确标注为来源与验证范围（如“模板基于 QiuVision 中 Lenis 1.3.23 的实际实现”“已验证的取舍”），对 Agent 判断适用边界有用，保留。
- [x] **S5** motion-recipes：Motion 版本表述（11.11+）、Case 7 `inert` 需 React 19 提示、CONTRIBUTING 不再要求往 description 堆触发词、目录树补 `assets/`。

## 第 5 步：长期

- [x] **L1** 拆分超长 case（Case 1/2/6/7 超出 CONTRIBUTING 400 行上限）或调整上限。
  调整规则：含多策略完整模板的 case 允许约 600 行，超过 400 行先删冗余、把组件代码移到 `assets/`。未拆分现有 case。
- [x] **L2** 统一 case 模板结构。
  核查后 Case 1–8 已基本符合模板；CONTRIBUTING 明确核心章节与可选章节，并允许组合型 case（Case 9）使用自有结构。
- [x] **L3** pitfall-guard 脚手架补冒烟测试。

---

## 进度日志

- 2026-10-13：完成审查，建立本文档。
- 2026-10-13：第 1 步完成。验证：spec-driven 116 个测试在默认 GBK 环境通过；`flow-transition.tsx` 与 `smooth-page-scroll.ts` 通过 `tsc --strict`；headless Edge 实测 `scale(0.95)` 容器中 FlowRegion 展开高度由 190px（旧，被裁切）变为 200px（新），FlowSwap 切换 / 清空 / 重新出现行为与旧版一致。附带修复：Case 7 `inert` 的 React 18 提示（原 S5 部分）、pitfalls Case 3 与 motion Case 7 互链。
- 2026-10-13：第 2–5 步完成。
  - 验证：`dev/spec-driven-ai-coding` 116 项测试通过（默认 GBK）；新增 `dev/project-pitfall-guard` 5 项冒烟测试通过（覆盖 Claude/Codex 目录探测、中文项目名、`--force` 保留记录、`|` 转义、YAML 特殊字符）；全仓库相对链接检查无断链；10 个 Skill 的目录名与 `name` 一致，description 均在 414–622 字符，全部带 `agents/openai.yaml`。
  - 未做：未在真实宿主中实测各 Skill 的触发率变化；`npx skills add .../tree/main/<path>` 子路径安装写法按 GitHub URL 规范修正，未联网实测。
