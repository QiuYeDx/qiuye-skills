---
name: project-pitfall-guard
description: Establish and maintain project-level pitfall guard skills for AI coding. Use when Codex starts work in a new or mature codebase, encounters repeated mistakes, debugging surprises, flaky validation, visual QA traps, build/test gotchas, repository-specific process rules, or when the user mentions 踩坑, 避坑, pitfall, gotcha, lessons learned, project memory, best practices, AGENTS.md, or wants durable AI Agent coding guidance across projects.
---

# Project Pitfall Guard

## Overview

Use this skill to make pitfall learning portable across projects. It tells Codex to create or maintain a project-local `.agents/skills/<project>-pitfall-guard` skill, with a concise index and one detail file per reusable lesson.

The system-level skill stores the practice. The project-level skill stores the actual project facts.

## Workflow

1. Check whether the current repository already has a pitfall guard:

   ```bash
   find .agents/skills -maxdepth 2 -name SKILL.md 2>/dev/null | rg 'pitfall|guard|gotcha|avoid'
   ```

2. If one exists, read its `SKILL.md`, then read `references/index.md`, then open only detail files that plausibly match the current task.
3. If none exists and the task is likely to benefit from durable lessons, create one with:

   ```bash
   python3 <this-skill>/scripts/bootstrap_project_pitfall_guard.py --project-root .
   ```

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

Default generated structure:

```text
.agents/skills/<project-slug>-pitfall-guard/
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
