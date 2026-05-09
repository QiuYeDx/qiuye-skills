---
name: large-feature-ai-coding
description: >-
  中大型需求的 AI Agent Coding 协作工作流。Use when Codex needs to plan or
  implement medium/large features, especially cross-frontend/backend work, by
  creating development design docs, execution/implementation plan docs, per-session
  implementation records, progress ledgers, multi-session handoff notes, and
  post-acceptance feat/fix documentation. Triggers include: 中大型需求、跨前后端、
  开发设计文档、执行计划、实施计划、多会话开发、AI Agent Coding、工作包、进度台账、
  实施记录、验收修复、feat/fix 文档。
---

# Large Feature AI Coding

Use this skill to turn a large requirement into a durable, multi-session coding workflow. Keep the code, plan, records, and final behavior aligned so another Agent can continue without losing key context.

## Workflow Decision

Choose the entry point from the user's request and repository state:

| Situation | Action |
|---|---|
| New large requirement, no design yet | Read relevant code/docs, then write a final design doc before implementation. |
| Design exists but no execution plan | Convert the design into a work-package execution plan with a status ledger. |
| Execution plan exists | Read design + plan, claim the smallest coherent work package, implement it, verify it, update plan status, and write an implementation record. |
| Acceptance/self-test found changes | Create a focused `feat/` or `fix/` doc, implement the change, verify it, and update the plan/design if the contract changed. |
| User asks only for review/analysis | Do not code yet; produce findings or a planning/design update that can become the next work package. |

Prefer the project's existing doc root. If none exists, use:

```text
docs/开发设计文档/
```

## Document Set

For each large feature, maintain these core documents:

```text
docs/开发设计文档/
  <feature_slug>_final_design.md
  <feature_slug>_execution_plan.md
  <feature_slug>_implementation_records/
    YYYY-MM-DD_<work-package-id>_<short-title>.md
  feat/
    YYYY-MM-DD_<feature_slug>_<short-title>.md
  fix/
    YYYY-MM-DD_<feature_slug>_<short-title>.md
```

Use concise, stable feature slugs such as `shmoo_full_export`. If the repository already uses another naming style, follow it.

## Final Design Doc

Create or update `<feature_slug>_final_design.md` before substantial implementation.

Include:

- Background, goals, non-goals, and user-facing behavior.
- Current frontend/backend state with concrete files, APIs, services, data flows, and known constraints.
- Final architecture and module responsibilities.
- API contracts, request/response shapes, state/status models, permissions, persistence, async jobs, error handling, and compatibility rules as applicable.
- Frontend interaction design, loading/empty/error states, and integration points.
- Backend data/query/write path design, performance boundaries, batching/sharding rules, and cleanup/rollback behavior.
- Risks, edge cases, validation strategy, rollout notes, and explicit exclusions.

When merging multiple candidate designs, write the review conclusion first: what each source got right, what is risky, and which final constraints must not be violated during coding.

## Execution Plan Doc

Create or update `<feature_slug>_execution_plan.md` after the design is stable enough to build.

The plan must include:

- How future Agents should use the design and plan at the start of each session.
- Status rules with only these values unless the project already has a stricter set: `未开始`, `进行中`, `已完成`, `阻塞`, `废弃`.
- A progress ledger table with work package id, status, completion date, key changed files, validation, implementation record path, and open issues.
- Work packages small enough for one focused session. Use prefixes like `PRE`, `BE`, `FE`, `QA`, `DOC`, `FIX` when helpful.
- Dependency order and priority principles, such as first closing the minimal end-to-end path, then expanding coverage.
- Project-specific "do not violate" engineering constraints from the final design.
- The implementation record template future sessions must use.

Do not make the execution plan a second design document. It is the build ledger and handoff contract.

## Per-Session Implementation

At the start of each coding session:

1. Read the final design doc and execution plan.
2. Inspect the progress ledger.
3. Choose one unfinished or partially finished work package, or a small set of tightly coupled packages.
4. State the claimed package and expected output before editing.
5. Inspect the relevant code paths and existing user changes.

During implementation:

- Keep edits scoped to the claimed package.
- Preserve all design invariants; if implementation proves a design assumption wrong, update the design or create a follow-up doc instead of silently drifting.
- Prefer a working vertical slice over broad unfinished scaffolding.
- Add or update tests according to risk and available project conventions.
- Leave the repo in a runnable state whenever practical.

Before finishing the session:

1. Run relevant validation commands, or record why validation could not run.
2. Update the execution plan progress ledger.
3. Create or update an implementation record in `<feature_slug>_implementation_records/`.
4. Mark only truly verified work as `已完成`; use `进行中` or `阻塞` honestly.
5. End with next-session guidance: the next best work package, unresolved risks, and validation gaps.

## Implementation Record Template

Use this template for each session/work package:

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
````

If a session touches several tightly coupled work packages, one record may cover them, but the execution plan ledger must still update each package separately.

## Acceptance Feat/Fix Docs

After manual self-test, QA, or user acceptance reveals new changes, document them before or alongside implementation.

Use:

- `feat/YYYY-MM-DD_<feature_slug>_<short-title>.md` for requirement additions or interaction enhancements.
- `fix/YYYY-MM-DD_<feature_slug>_<short-title>.md` for bugs, regressions, data mismatches, formatting issues, or behavioral corrections.

Each feat/fix doc should include:

- Background and observed behavior.
- Root cause or design gap.
- Intended behavior after the change.
- Affected frontend/backend files and APIs.
- Implementation summary.
- Validation commands and results.
- Follow-up suggestions.

If a feat/fix changes the original contract, also update the final design doc and the execution plan ledger so the document set matches the actual system.

## Quality Checklist

Before final response, confirm:

- Design, execution plan, implementation records, and feat/fix docs do not contradict the implementation.
- The execution plan status is accurate and not overly optimistic.
- File paths in docs point to real or intentionally planned files.
- Validation results are recorded with exact commands.
- The next Agent can continue from the docs without relying on hidden chat context.
- The final user-facing response names changed docs/code, verification, and the recommended next step.
