#!/usr/bin/env python3
"""Scaffold a project-level pitfall guard skill."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "project"


ADD_PITFALL = r'''#!/usr/bin/env python3
"""Create a project pitfall detail file and append it to the index."""

from __future__ import annotations

import argparse
import datetime as _dt
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFERENCES = ROOT / "references"
INDEX = REFERENCES / "index.md"


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "pitfall"


def next_id(index_text: str, prefix: str) -> str:
    numbers = [
        int(match.group(1))
        for match in re.finditer(rf"{re.escape(prefix)}-(\d{{4}})", index_text)
    ]
    return f"{prefix}-{(max(numbers) + 1) if numbers else 1:04d}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", required=True)
    parser.add_argument("--area", required=True)
    parser.add_argument("--triggers", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--prefix", default="PROJ-PIT")
    parser.add_argument("--date", default=_dt.date.today().isoformat())
    args = parser.parse_args()

    REFERENCES.mkdir(parents=True, exist_ok=True)
    index_text = INDEX.read_text(encoding="utf-8") if INDEX.exists() else ""
    pitfall_id = next_id(index_text, args.prefix)
    filename = f"{slugify(args.title)}.md"
    path = REFERENCES / filename

    if path.exists():
        raise SystemExit(f"Refusing to overwrite existing pitfall: {path}")

    path.write_text(
        f"""# {pitfall_id}: {args.title}

## Area

{args.area}

## Triggers

{args.triggers}

## Symptoms

{args.summary}

## Root cause

TODO

## Do

TODO

## Avoid

TODO

## Validation

TODO

## Related files

TODO
""",
        encoding="utf-8",
    )

    row = (
        f"| {pitfall_id} | {args.area} | {args.triggers}; {args.summary} | "
        f"[{filename}]({filename}) |"
    )

    if not index_text:
        index_text = (
            "# Project pitfall index\n\n"
            "Read this index first, then open only the detail files that plausibly match the current task.\n\n"
            "| ID | Area | Triggers / symptoms | Detail |\n"
            "| --- | --- | --- | --- |\n"
        )

    if row not in index_text:
        lines = index_text.rstrip().splitlines()
        insert_at = len(lines)
        for idx, line in enumerate(lines):
            if line.startswith("| ") and "-PIT-" in line:
                insert_at = idx + 1
        if insert_at == len(lines):
            for idx, line in enumerate(lines):
                if line.strip() == "| --- | --- | --- | --- |":
                    insert_at = idx + 1
                    break
        lines.insert(insert_at, row)
        INDEX.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def write_new(path: Path, content: str, force: bool) -> None:
    if path.exists() and not force:
        raise SystemExit(f"Refusing to overwrite existing file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--project-name")
    parser.add_argument("--skill-name")
    parser.add_argument("--pitfall-prefix", default="PROJ-PIT")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    project_name = args.project_name or project_root.name
    skill_name = args.skill_name or f"{slugify(project_name)}-pitfall-guard"
    skill_root = project_root / ".agents" / "skills" / skill_name

    if skill_root.exists() and not args.force:
        raise SystemExit(f"Skill already exists: {skill_root}")

    write_new(
        skill_root / "SKILL.md",
        f"""---
name: {skill_name}
description: Project-level pitfall and avoidance workflow for {project_name}. Use when Codex is diagnosing failures, implementing changes, encountering surprising behavior, before repeating risky workflows, or when the user mentions 踩坑, 避坑, pitfall, gotcha, regression, flaky validation, repository-specific process rules, or lessons learned.
---

# {project_name} Pitfall Guard

## Overview

Use this skill to prevent repeated {project_name} mistakes. It provides a compact pitfall index and one-file-per-case references so Codex can quickly check known traps before acting.

## Required workflow

1. Read `references/index.md` first.
2. Match the current task against the index by area, trigger words, symptoms, commands, and files.
3. Read only the referenced pitfall detail files that plausibly apply.
4. Apply the “Do / Avoid / Validation” guidance from those files.
5. If the current task reveals a new reusable lesson, add a new pitfall detail file and update the index before finishing.
6. Mention in the final response when this skill materially changed the approach.

## Adding a pitfall

Prefer:

```bash
python3 .agents/skills/{skill_name}/scripts/add_pitfall.py \\
  --prefix {args.pitfall_prefix} \\
  --title "Short pitfall title" \\
  --area "Frontend / Build / Docs / QA" \\
  --triggers "comma-separated trigger words" \\
  --summary "One-line symptom and lesson"
```

Then edit the generated detail file and replace TODO sections.

## Detail file contract

Each pitfall detail file should include:

- `Area`
- `Triggers`
- `Symptoms`
- `Root cause`
- `Do`
- `Avoid`
- `Validation`
- `Related files`
""",
        args.force,
    )

    write_new(
        skill_root / "agents" / "openai.yaml",
        f"""interface:
  display_name: "{project_name} Pitfall Guard"
  short_description: "Project pitfall index and avoidance workflow"
  default_prompt: "Use ${skill_name} to check project pitfall records before diagnosing or changing code."
""",
        args.force,
    )

    write_new(
        skill_root / "references" / "index.md",
        """# Project pitfall index

Read this index first, then open only the detail files that plausibly match the current task.

| ID | Area | Triggers / symptoms | Detail |
| --- | --- | --- | --- |

## Add new cases

Use `scripts/add_pitfall.py` from the skill root when possible. Each pitfall should live as one Markdown file directly under `references/`, and every new file must have one index row here.
""",
        args.force,
    )

    write_new(
        skill_root / "references" / "pitfall-template.md",
        f"""# {args.pitfall_prefix}-XXXX: Short title

## Area

## Triggers

## Symptoms

## Root cause

## Do

## Avoid

## Validation

## Related files
""",
        args.force,
    )

    write_new(skill_root / "scripts" / "add_pitfall.py", ADD_PITFALL, args.force)
    (skill_root / "scripts" / "add_pitfall.py").chmod(0o755)

    print(skill_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
