# Project-level pitfall guard contract

Use this reference when creating or reviewing a project-local pitfall guard skill.

## Purpose

The project pitfall guard is a lightweight memory layer for AI coding agents. It records lessons that are specific enough to this repository that a generic model or generic skill is likely to miss them.

## Required workflow in the project skill

The project-level `SKILL.md` should require agents to:

1. Read `references/index.md` first.
2. Match the task against index rows by area, triggers, symptoms, files, and commands.
3. Open only the relevant detail files.
4. Apply “Do / Avoid / Validation” guidance.
5. Add or update a pitfall when the current session reveals a reusable trap.

## Index row shape

```markdown
| ID | Area | Triggers / symptoms | Detail |
| --- | --- | --- | --- |
| PROJ-PIT-0001 | Frontend visual QA | screenshots show loading overlay, visual matrix | [frontend-visual-loading.md](frontend-visual-loading.md) |
```

## Detail file shape

Each pitfall detail file should include:

- `Area`
- `Triggers`
- `Symptoms`
- `Root cause`
- `Do`
- `Avoid`
- `Validation`
- `Related files`

## What belongs here

- local commands that have non-obvious failure modes;
- visual QA timing traps;
- project-specific lint/test/build gotchas;
- environment or permission quirks;
- dirty-data, dirty-design, or dirty-doc cleanup rules;
- repeated agent mistakes;
- workflow constraints from `AGENTS.md` or similar files.

## What does not belong here

- generic language/framework tips better handled by general skills;
- one-off bug notes with no reusable lesson;
- full feature plans or architecture specs;
- release notes or changelogs;
- secrets, tokens, credentials, or private operational data.

## Naming guidance

Use `<project-slug>-pitfall-guard` for the project-level skill name. Examples:

- `fusionkit-pitfall-guard`
- `my-app-pitfall-guard`
- `data-platform-pitfall-guard`

Use stable pitfall IDs such as `PROJ-PIT-0001` or a project prefix like `FK-PIT-0001`.
