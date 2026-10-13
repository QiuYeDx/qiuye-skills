#!/usr/bin/env python3
"""Scaffold a project-level pitfall guard skill."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

META_SKILL_NAME = "project-pitfall-guard"


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")


def detect_skills_dir(project_root: Path) -> tuple[Path, str]:
    """Pick where the host agent discovers project skills.

    Claude Code reads `.claude/skills/`; Codex and other Agent Skills hosts read
    `.agents/skills/`. Prefer a directory that already exists, then host markers.
    """
    claude = Path(".claude") / "skills"
    agents = Path(".agents") / "skills"
    if (project_root / claude).is_dir():
        return claude, "existing .claude/skills"
    if (project_root / agents).is_dir():
        return agents, "existing .agents/skills"
    if (project_root / ".claude").is_dir() or (project_root / "CLAUDE.md").exists():
        return claude, "found .claude/ or CLAUDE.md"
    if (project_root / "AGENTS.md").exists():
        return agents, "found AGENTS.md"
    return agents, "no host marker found; pass --skills-dir to override"


ADD_PITFALL = r'''#!/usr/bin/env python3
"""Create a project pitfall detail file and append it to the index."""

from __future__ import annotations

import argparse
import datetime as _dt
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFERENCES = ROOT / "references"
INDEX = REFERENCES / "index.md"
HEADER = "| ID | Area | Triggers / symptoms | Detail |"


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9一-鿿]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "pitfall"


def cell(text: str) -> str:
    """Keep user text inside one Markdown table cell."""
    return " ".join(text.split()).replace("|", "\\|")


def next_id(index_text: str, prefix: str) -> str:
    numbers = [
        int(match.group(1))
        for match in re.finditer(rf"{re.escape(prefix)}-(\d{{4}})", index_text)
    ]
    # Detail files also carry IDs, so a damaged index cannot cause reuse.
    for detail in REFERENCES.glob("*.md"):
        head = detail.read_text(encoding="utf-8").split("\n", 1)[0]
        match = re.match(rf"# {re.escape(prefix)}-(\d{{4}})", head)
        if match:
            numbers.append(int(match.group(1)))
    return f"{prefix}-{(max(numbers) + 1) if numbers else 1:04d}"


def insert_row(index_text: str, row: str) -> str:
    lines = index_text.rstrip().splitlines()
    start = next((i for i, line in enumerate(lines) if line.strip() == HEADER), None)
    if start is None:
        lines += ["", HEADER, "| --- | --- | --- | --- |"]
        start = len(lines) - 2
    end = start + 1
    while end + 1 < len(lines) and lines[end + 1].startswith("|"):
        end += 1
    lines.insert(end + 1, row)
    return "\n".join(lines) + "\n"


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", required=True)
    parser.add_argument("--area", required=True)
    parser.add_argument("--triggers", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--prefix", default="PROJ-PIT")
    parser.add_argument("--date", default=_dt.date.today().isoformat())
    args = parser.parse_args()

    REFERENCES.mkdir(parents=True, exist_ok=True)
    index_text = INDEX.read_text(encoding="utf-8") if INDEX.exists() else (
        "# Project pitfall index\n\n"
        "Read this index first, then open only the detail files that plausibly match the current task.\n\n"
        f"{HEADER}\n| --- | --- | --- | --- |\n"
    )
    pitfall_id = next_id(index_text, args.prefix)
    filename = f"{slugify(args.title)}.md"
    path = REFERENCES / filename

    if path.exists():
        raise SystemExit(f"Refusing to overwrite existing pitfall: {path}")

    path.write_text(
        f"""# {pitfall_id}: {args.title}

Recorded: {args.date}

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
        f"| {pitfall_id} | {cell(args.area)} | {cell(args.triggers)}; {cell(args.summary)} | "
        f"[{filename}]({filename}) |"
    )
    INDEX.write_text(insert_row(index_text, row), encoding="utf-8")

    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def write_file(path: Path, content: str, overwrite: bool) -> bool:
    if path.exists() and not overwrite:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--project-name")
    parser.add_argument("--skill-name", help="Required when the project name has no ASCII letters or digits")
    parser.add_argument(
        "--skills-dir",
        help="Project skills directory relative to the root: .claude/skills (Claude Code) "
        "or .agents/skills (Codex and other Agent Skills hosts). Auto-detected by default.",
    )
    parser.add_argument("--pitfall-prefix", default="PROJ-PIT")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Refresh SKILL.md, scripts and the template. Never touches index.md or pitfall records.",
    )
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    project_name = args.project_name or project_root.name

    if args.skill_name:
        skill_name = args.skill_name
    else:
        slug = slugify(project_name)
        if not slug:
            raise SystemExit(
                f"Cannot derive an ASCII skill name from {project_name!r}; pass --skill-name <slug>-pitfall-guard."
            )
        skill_name = f"{slug}-pitfall-guard"
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", skill_name):
        raise SystemExit(f"Invalid skill name {skill_name!r}: use lowercase letters, digits and hyphens.")
    if skill_name == META_SKILL_NAME:
        raise SystemExit(f"{skill_name!r} would shadow the meta skill; choose a project-specific name.")

    if args.skills_dir:
        skills_dir, reason = Path(args.skills_dir), "--skills-dir"
    else:
        skills_dir, reason = detect_skills_dir(project_root)
    skill_root = project_root / skills_dir / skill_name
    skill_path = (skills_dir / skill_name).as_posix()

    if skill_root.exists() and not args.force:
        raise SystemExit(f"Skill already exists: {skill_root} (use --force to refresh its SKILL.md and scripts)")

    description = (
        f"Project-level pitfall records for {project_name}. Use when diagnosing a failure, flaky "
        f"validation or surprising behavior in this repository, before running its build, test, "
        f"release or visual QA workflows, or when the user mentions 踩坑, 避坑, pitfall, gotcha, "
        f"regression or lessons learned for this project."
    )

    write_file(
        skill_root / "SKILL.md",
        f"""---
name: {skill_name}
description: {json.dumps(description, ensure_ascii=False)}
---

# {project_name} Pitfall Guard

## Overview

Use this skill to prevent repeated {project_name} mistakes. It provides a compact pitfall index and one-file-per-case references so the agent can check known traps before acting.

## Required workflow

1. Read `references/index.md` first.
2. Match the current task against the index by area, trigger words, symptoms, commands, and files.
3. Read only the referenced pitfall detail files that plausibly apply.
4. Apply the "Do / Avoid / Validation" guidance from those files.
5. If the current task reveals a new reusable lesson, add a new pitfall detail file and update the index before finishing.
6. Mention in the final response when this skill materially changed the approach.

## Adding a pitfall

Run from the project root (use `python` or `py -3` where `python3` is unavailable):

```bash
python3 {skill_path}/scripts/add_pitfall.py \\
  --prefix {args.pitfall_prefix} \\
  --title "Short pitfall title" \\
  --area "Frontend / Build / Docs / QA" \\
  --triggers "comma-separated trigger words" \\
  --summary "One-line symptom and lesson"
```

Then edit the generated detail file and replace the TODO sections. The required fields are listed in `references/pitfall-template.md`.
""",
        overwrite=True,
    )

    write_file(
        skill_root / "agents" / "openai.yaml",
        f"""interface:
  display_name: {json.dumps(f"{project_name} Pitfall Guard", ensure_ascii=False)}
  short_description: "Project pitfall index and avoidance workflow"
  default_prompt: "Use ${skill_name} to check project pitfall records before diagnosing or changing code."
""",
        overwrite=True,
    )

    created_index = write_file(
        skill_root / "references" / "index.md",
        """# Project pitfall index

Read this index first, then open only the detail files that plausibly match the current task.

| ID | Area | Triggers / symptoms | Detail |
| --- | --- | --- | --- |

## Add new cases

Use `scripts/add_pitfall.py` from the skill root when possible. Each pitfall should live as one Markdown file directly under `references/`, and every new file must have one index row here.
""",
        overwrite=False,
    )

    write_file(
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
        overwrite=True,
    )

    script = skill_root / "scripts" / "add_pitfall.py"
    write_file(script, ADD_PITFALL, overwrite=True)
    script.chmod(0o755)

    print(skill_root)
    print(f"skills dir: {skills_dir.as_posix()} ({reason})")
    if not created_index:
        print("kept existing references/index.md and pitfall records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
