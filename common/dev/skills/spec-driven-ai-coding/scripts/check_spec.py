#!/usr/bin/env python3
"""检查 spec 文档集的需求追踪覆盖与状态一致性。

用法：
  python3 check_spec.py docs/开发设计文档/<feature_slug> [--no-vague]

检查项：
  - L：brd.md 每条 BR 至少被一条模块需求 R 覆盖；R 的来源 BR 必须存在
  - 每条 R 至少被一个任务 T 覆盖；T 的关联需求与依赖必须存在
  - 状态只允许 未开始 / 进行中 / 已完成 / 阻塞 / 废弃
  - L：task-list-overall.md 与各模块 tasks.md 的任务集合与状态一致
  - 已完成 的任务应填写完成日期与实施记录，且记录文件存在
  - design.md 应提及本模块每条 R（需求追踪矩阵）
  - 模糊词与未替换的模板占位符（警告）

退出码：有 error 返回 1，否则返回 0。仅依赖标准库。
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

STATUSES = {"未开始", "进行中", "已完成", "阻塞", "废弃"}
BR_HEAD = re.compile(r"^#{2,4}\s+(BR-\d+)\b", re.M)
R_HEAD = re.compile(r"^#{2,4}\s+(R-[A-Z0-9_]+-\d+)\b", re.M)
BR_ID = re.compile(r"\bBR-\d+\b")
R_ID = re.compile(r"\bR-[A-Z0-9_]+-\d+\b")
T_ID = re.compile(r"\bT-[A-Z0-9_]+-\d+\b")
SOURCE_LINE = re.compile(r"^\s*[-*]\s*来源\s*[:：]\s*(.*)$", re.M)
PLACEHOLDER = re.compile(r"\{\{[A-Z_]+\}\}")
VAGUE_WORDS = ["等等", "类似", "合理", "适当", "若干", "友好提示", "尽量", "后续完善", "大概", "之类", "必要时"]


class Report:
    def __init__(self, root: pathlib.Path) -> None:
        self.root = root
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def _rel(self, path: pathlib.Path) -> str:
        try:
            return str(path.relative_to(self.root))
        except ValueError:
            return str(path)

    def error(self, path: pathlib.Path, msg: str, line: int | None = None) -> None:
        loc = f"{self._rel(path)}:{line}" if line else self._rel(path)
        self.errors.append(f"[ERROR] {loc}: {msg}")

    def warn(self, path: pathlib.Path, msg: str, line: int | None = None) -> None:
        loc = f"{self._rel(path)}:{line}" if line else self._rel(path)
        self.warnings.append(f"[WARN]  {loc}: {msg}")


def read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def split_row(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def is_separator(line: str) -> bool:
    cells = split_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", c) for c in cells)


def parse_tables(text: str) -> list[tuple[list[str], list[dict[str, str]]]]:
    """解析 Markdown 表格。每行记录附带 `_line`（1-based 行号）。"""
    lines = text.splitlines()
    tables: list[tuple[list[str], list[dict[str, str]]]] = []
    i = 0
    while i < len(lines) - 1:
        if lines[i].strip().startswith("|") and lines[i + 1].strip().startswith("|") and is_separator(lines[i + 1]):
            headers = split_row(lines[i])
            rows: list[dict[str, str]] = []
            j = i + 2
            while j < len(lines) and lines[j].strip().startswith("|"):
                cells = split_row(lines[j])
                cells += [""] * (len(headers) - len(cells))
                row = dict(zip(headers, cells))
                row["_line"] = str(j + 1)
                rows.append(row)
                j += 1
            tables.append((headers, rows))
            i = j
        else:
            i += 1
    return tables


def find_table(text: str, required: tuple[str, ...]) -> list[dict[str, str]] | None:
    for headers, rows in parse_tables(text):
        if all(any(h.startswith(r) for h in headers) for r in required):
            return rows
    return None


def col(row: dict[str, str], prefix: str) -> str:
    for key, value in row.items():
        if key.startswith(prefix):
            return value
    return ""


def parse_requirements(text: str) -> dict[str, dict]:
    """返回 {R-ID: {"sources": [BR...], "line": n}}。"""
    result: dict[str, dict] = {}
    matches = list(R_HEAD.finditer(text))
    for idx, m in enumerate(matches):
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        block = text[m.end():end]
        # 只取到下一个同级或更高级标题
        next_heading = re.search(r"^#{1,3}\s", block, re.M)
        if next_heading:
            block = block[: next_heading.start()]
        src = SOURCE_LINE.search(block)
        sources = BR_ID.findall(src.group(1)) if src else []
        result[m.group(1)] = {"sources": sources, "line": text.count("\n", 0, m.start()) + 1}
    return result


def parse_tasks(text: str) -> dict[str, dict]:
    """返回 {T-ID: {...}}，来自含 任务/状态/关联需求 列的表格。"""
    rows = find_table(text, ("任务", "状态", "关联需求"))
    result: dict[str, dict] = {}
    if rows is None:
        return result
    for row in rows:
        m = T_ID.search(col(row, "任务"))
        if not m:
            continue
        result[m.group(0)] = {
            "status": col(row, "状态"),
            "reqs": R_ID.findall(col(row, "关联需求")),
            "deps": T_ID.findall(col(row, "依赖")),
            "date": col(row, "完成日期"),
            "record": col(row, "实施记录"),
            "line": int(row["_line"]),
        }
    return result


def parse_overall(text: str) -> dict[str, dict]:
    rows = find_table(text, ("任务", "模块", "状态"))
    result: dict[str, dict] = {}
    if rows is None:
        return result
    for row in rows:
        m = T_ID.search(col(row, "任务"))
        if not m:
            continue
        result[m.group(0)] = {
            "status": col(row, "状态"),
            "module": col(row, "模块"),
            "deps": T_ID.findall(col(row, "依赖")),
            "line": int(row["_line"]),
        }
    return result


def expected_code(module_dir_name: str) -> str:
    slug = module_dir_name[len("module-"):] if module_dir_name.startswith("module-") else module_dir_name
    return re.sub(r"[^A-Z0-9]+", "_", slug.upper()).strip("_")


def lint_text(report: Report, path: pathlib.Path, check_vague: bool) -> None:
    for idx, line in enumerate(read(path).splitlines(), start=1):
        if PLACEHOLDER.search(line):
            report.warn(path, f"存在未替换的模板占位符：{PLACEHOLDER.search(line).group(0)}", idx)
        if check_vague and not line.lstrip().startswith(("写作要求", "禁用")):
            hits = [w for w in VAGUE_WORDS if w in line]
            if hits:
                report.warn(path, f"模糊词：{'、'.join(hits)}", idx)


def check_module(
    report: Report,
    module_dir: pathlib.Path,
    br_ids: set[str] | None,
    all_reqs: dict[str, pathlib.Path],
    all_tasks: dict[str, tuple[pathlib.Path, dict]],
    check_vague: bool,
) -> tuple[dict[str, dict], dict[str, dict]]:
    """检查单个模块目录（或 M 规模的根目录）。返回 (reqs, tasks)。"""
    req_path = module_dir / "requirements.md"
    design_path = module_dir / "design.md"
    tasks_path = module_dir / "tasks.md"
    for p in (req_path, design_path, tasks_path):
        if not p.exists():
            report.error(p, "文件缺失")
    reqs = parse_requirements(read(req_path)) if req_path.exists() else {}
    tasks = parse_tasks(read(tasks_path)) if tasks_path.exists() else {}

    if req_path.exists():
        lint_text(report, req_path, check_vague)
        if not reqs:
            report.error(req_path, "未定义任何 R-<MOD>-xx 需求（需用 ### R-XXX-01 标题）")
        code = expected_code(module_dir.name) if module_dir.name.startswith("module-") else None
        for rid, info in reqs.items():
            all_reqs[rid] = req_path
            if code and rid.split("-")[1] != code:
                report.warn(req_path, f"{rid} 的短码与模块目录 {module_dir.name} 不一致（期望 {code}）", info["line"])
            if br_ids is not None:
                if not info["sources"]:
                    report.warn(req_path, f"{rid} 未标注来源 BR", info["line"])
                for br in info["sources"]:
                    if br not in br_ids:
                        report.error(req_path, f"{rid} 的来源 {br} 不存在于 brd.md", info["line"])

    if design_path.exists():
        design_text = read(design_path)
        for rid, info in reqs.items():
            if rid not in design_text:
                report.warn(design_path, f"未提及 {rid}（需求追踪矩阵缺失）")
        if PLACEHOLDER.search(design_text):
            report.warn(design_path, "存在未替换的模板占位符")

    if tasks_path.exists():
        if not tasks:
            report.error(tasks_path, "未找到任务台账表（需含 任务 / 状态 / 关联需求 列）")
        for tid, info in tasks.items():
            all_tasks[tid] = (tasks_path, info)
            if info["status"] not in STATUSES:
                report.error(tasks_path, f"{tid} 状态非法：'{info['status']}'", info["line"])
            if not info["reqs"]:
                report.error(tasks_path, f"{tid} 未填写关联需求", info["line"])
            if info["status"] == "已完成":
                if not info["date"]:
                    report.warn(tasks_path, f"{tid} 已完成但未填完成日期", info["line"])
                if not info["record"]:
                    report.warn(tasks_path, f"{tid} 已完成但未填实施记录", info["line"])
                else:
                    rec = info["record"].strip("`")
                    candidates = [module_dir / rec, report.root / rec, module_dir.parent.parent / rec]
                    if not any(c.exists() for c in candidates):
                        report.warn(tasks_path, f"{tid} 的实施记录路径不存在：{rec}", info["line"])
        covered = {r for info in tasks.values() for r in info["reqs"]}
        for rid in reqs:
            if rid not in covered:
                report.error(tasks_path, f"{rid} 未被任何任务覆盖")
    return reqs, tasks


def cross_check_tasks(
    report: Report,
    all_reqs: dict[str, pathlib.Path],
    all_tasks: dict[str, tuple[pathlib.Path, dict]],
) -> None:
    for tid, (path, info) in all_tasks.items():
        own_code = tid.split("-")[1]
        for rid in info["reqs"]:
            if rid not in all_reqs:
                report.error(path, f"{tid} 关联的 {rid} 不存在", info["line"])
            elif rid.split("-")[1] != own_code:
                report.warn(path, f"{tid} 关联了其他模块的需求 {rid}", info["line"])
        for dep in info["deps"]:
            if dep not in all_tasks:
                report.error(path, f"{tid} 依赖的 {dep} 不存在", info["line"])
            elif dep == tid:
                report.error(path, f"{tid} 依赖自身", info["line"])


def check_overall(report: Report, root: pathlib.Path, all_tasks: dict[str, tuple[pathlib.Path, dict]]) -> None:
    overall_path = root / "task-list-overall.md"
    if not overall_path.exists():
        report.error(overall_path, "文件缺失")
        return
    overall = parse_overall(read(overall_path))
    if not overall:
        report.error(overall_path, "未找到总任务表（需含 任务 / 模块 / 状态 列）")
        return
    for tid, (path, info) in all_tasks.items():
        if tid not in overall:
            report.error(overall_path, f"缺少任务 {tid}（存在于 {report._rel(path)}）")
            continue
        if overall[tid]["status"] != info["status"]:
            report.error(
                overall_path,
                f"{tid} 状态不一致：overall='{overall[tid]['status']}'，tasks.md='{info['status']}'",
                overall[tid]["line"],
            )
    for tid, info in overall.items():
        if tid not in all_tasks:
            report.error(overall_path, f"{tid} 不存在于任何模块的 tasks.md", info["line"])
        if info["status"] not in STATUSES:
            report.error(overall_path, f"{tid} 状态非法：'{info['status']}'", info["line"])
    if PLACEHOLDER.search(read(overall_path)):
        report.warn(overall_path, "存在未替换的模板占位符")


def run(root: pathlib.Path, check_vague: bool) -> Report:
    report = Report(root)
    brd_path = root / "brd.md"
    modules_dir = root / "modules"
    all_reqs: dict[str, pathlib.Path] = {}
    all_tasks: dict[str, tuple[pathlib.Path, dict]] = {}

    if brd_path.exists() or modules_dir.exists():
        # L 规模
        if not brd_path.exists():
            report.error(brd_path, "L 结构缺少 brd.md")
            br_ids: set[str] = set()
        else:
            brd_text = read(brd_path)
            br_ids = set(BR_HEAD.findall(brd_text))
            if not br_ids:
                report.error(brd_path, "未定义任何 BR-xx（需用 ### BR-01 标题）")
            lint_text(report, brd_path, check_vague)
        if not modules_dir.exists():
            report.error(modules_dir, "缺少 modules/ 目录")
            module_dirs: list[pathlib.Path] = []
        else:
            module_dirs = sorted(p for p in modules_dir.iterdir() if p.is_dir() and p.name.startswith("module-"))
            if not module_dirs:
                report.error(modules_dir, "modules/ 下没有 module-* 目录")
            if not (modules_dir / "module-common").exists():
                report.warn(modules_dir, "缺少 module-common（共享契约应放在这里）")
        covered_br: set[str] = set()
        for module_dir in module_dirs:
            reqs, _ = check_module(report, module_dir, br_ids, all_reqs, all_tasks, check_vague)
            for info in reqs.values():
                covered_br.update(info["sources"])
        for br in sorted(br_ids, key=lambda s: int(s.split("-")[1])):
            if br not in covered_br:
                report.error(brd_path, f"{br} 未被任何模块需求覆盖")
        cross_check_tasks(report, all_reqs, all_tasks)
        check_overall(report, root, all_tasks)
    elif (root / "requirements.md").exists():
        # M 规模
        check_module(report, root, None, all_reqs, all_tasks, check_vague)
        cross_check_tasks(report, all_reqs, all_tasks)
    else:
        report.error(root, "未找到 brd.md（L）或 requirements.md（M），请确认目录是否为 spec 根")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="检查 spec 文档集的追踪覆盖与状态一致性")
    parser.add_argument("root", help="spec 根目录，例如 docs/开发设计文档/<feature_slug>")
    parser.add_argument("--no-vague", action="store_true", help="不检查模糊词")
    args = parser.parse_args()

    root = pathlib.Path(args.root)
    if not root.exists():
        print(f"[ERROR] 目录不存在：{root}")
        return 1

    report = run(root, check_vague=not args.no_vague)
    for line in report.errors:
        print(line)
    for line in report.warnings:
        print(line)
    print()
    print(f"检查完成：{len(report.errors)} 个 error，{len(report.warnings)} 个 warning")
    if report.errors:
        print("存在 error，不得进入下一阶段。")
        return 1
    print("未发现 error。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
