#!/usr/bin/env python3
"""Generate the single read-only overview; never import it as authoritative state."""
from __future__ import annotations
import argparse
import os
import pathlib
import tempfile
from spec_core import GENERATED, SpecError, local_path, render_overall, text, validate


def main() -> int:
    parser = argparse.ArgumentParser(description="从 tasks.md 生成总览；默认输出到 stdout")
    parser.add_argument("root", type=pathlib.Path)
    parser.add_argument("--write", action="store_true", help="写入 task-list-overall.md；拒绝覆盖人工文档")
    args = parser.parse_args()
    report = validate(args.root, "draft")
    if report.errors:
        for error in report.errors:
            print("[ERROR] " + error)
        return 1
    output = render_overall(report)
    if not args.write:
        print(output, end="")
        return 0
    temporary: str | None = None
    try:
        path = local_path(args.root.absolute(), "task-list-overall.md")
        if path.exists() and not text(path).startswith(GENERATED + "\n"):
            raise SpecError("已有人工总览，拒绝覆盖；先按 migration.md 审阅并归档")
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", dir=path.parent, delete=False) as handle:
            temporary = handle.name
            handle.write(output)
        os.replace(temporary, path)
        temporary = None
        print(f"已生成：{path}")
    except (SpecError, OSError) as exc:
        print(f"[ERROR] {exc}")
        return 1
    finally:
        if temporary:
            pathlib.Path(temporary).unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
