---
name: project-pitfall-guard
description: Create and maintain a project-local pitfall guard skill that records repository-specific traps (non-obvious build/test/release failures, flaky validation, visual QA timing, environment quirks, repeated agent mistakes) as one file per lesson behind a compact index. Use when the user asks for 踩坑/避坑 records, pitfalls, gotchas or lessons learned for a project; when the same mistake or surprising failure recurs across sessions; or to read and update an existing <project>-pitfall-guard. Not for one-off bugs, generic framework tips, or routine coding tasks.
---

# Project Pitfall Guard

## Overview

Use this skill to make pitfall learning portable across projects. It creates or maintains a project-local `<project>-pitfall-guard` skill, with a concise index and one detail file per reusable lesson, in the directory the current agent host discovers project skills from:

| Host | Project skills directory | Project instructions file |
|---|---|---|
| Claude Code | `.claude/skills/` | `CLAUDE.md` |
| Codex and other Agent Skills hosts | `.agents/skills/` | `AGENTS.md` |

The system-level skill stores the practice. The project-level skill stores the actual project facts.

## Workflow

1. Check whether the current repository already has a pitfall guard: glob `.claude/skills/*/SKILL.md` and `.agents/skills/*/SKILL.md` with the agent's file search tool (works on every OS) and look for names containing `pitfall`, `guard`, `gotcha` or `avoid`.
2. If one exists, read its `SKILL.md`, then read `references/index.md`, then open only detail files that plausibly match the current task.
3. If none exists and the task is likely to benefit from durable lessons, create one with:

   ```bash
   python3 <this-skill>/scripts/bootstrap_project_pitfall_guard.py --project-root . --skills-dir .claude/skills
   ```

   - Pass the `--skills-dir` of the current host (see the table above). Without it the script auto-detects: an existing skills directory first, then `CLAUDE.md` / `.claude/`, then `AGENTS.md`, falling back to `.agents/skills`.
   - On Windows use `python` or `py -3` if `python3` is unavailable.
   - Pass `--skill-name <slug>-pitfall-guard` when the project name has no ASCII letters or digits.
   - `--force` refreshes the generated `SKILL.md`, scripts and template only; it never rewrites `references/index.md` or existing pitfall records.

4. When a new reusable trap appears, add one focused detail file to the project-level skill and update its index.
5. Before final response, mention any new or updated pitfall records if they materially affect future work.

## When to create a project-level pitfall guard

Create or propose one when at least one is true:

- The user asks for project-level 踩坑/避坑 documentation or AI coding best practices.
- A mistake is likely to repeat across sessions or agents.
- The workaround depends on project-specific files, commands, services, permissions, UI timing, release process, or local environment.
- Existing docs are too broad, buried, or not triggerable as a skill.
- The lesson is more procedural than architectural.

Do not create one for a one-off typo, a generic language rule, or a lesson already covered by a more specific project skill.

## Project-level structure

Default generated structure (under `.claude/skills/` or `.agents/skills/`):

```text
<skills-dir>/<project-slug>-pitfall-guard/
  SKILL.md
  agents/openai.yaml
  references/
    index.md
    pitfall-template.md
  scripts/
    add_pitfall.py
```

Use one Markdown file per pitfall under `references/`. Keep the index compact so future agents can scan it first.

## Pitfall quality bar

A good pitfall record has:

- a clear trigger or symptom;
- the project-specific root cause;
- specific “Do” and “Avoid” guidance;
- validation commands or observable proof;
- related files or docs;
- enough context for another agent to act without reading the original chat.

Split unrelated lessons. Do not turn the pitfall guard into a second architecture document, changelog, or task journal.

## Resources

- Use `scripts/bootstrap_project_pitfall_guard.py` to scaffold a project-level pitfall guard.
- See `references/project-pitfall-guard-contract.md` for the generated project skill contract and maintenance rules.
