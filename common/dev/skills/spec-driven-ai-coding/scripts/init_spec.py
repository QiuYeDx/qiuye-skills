#!/usr/bin/env python3
"""按 spec-driven-ai-coding 约定生成 spec 文档骨架。

用法：
  # L 规模：BRD + module-common + 各模块三件套 + 总任务列表
  python3 init_spec.py --root docs/开发设计文档 --feature order-center --tier L --modules auth,order

  # M 规模：单模块三件套直接放在需求目录根
  python3 init_spec.py --root docs/开发设计文档 --feature export-button --tier M

  # 向已有 L 结构追加模块（已存在文件一律跳过，不覆盖）
  python3 init_spec.py --root docs/开发设计文档 --feature order-center --tier L --modules report

仅依赖标准库。已存在的文件不会被覆盖。
"""

from __future__ import annotations

import argparse
import datetime as dt
import pathlib
import re
import sys

SKILL_DIR = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE_DIR = SKILL_DIR / "templates"


def module_code(slug: str) -> str:
    """模块短码：大写、无连字符，例如 order-center -> ORDER_CENTER。"""
    code = re.sub(r"[^A-Z0-9]+", "_", slug.upper()).strip("_")
    if not code:
        raise SystemExit(f"无法从 '{slug}' 生成模块短码")
    return code


def render(template_name: str, mapping: dict[str, str]) -> str:
    path = TEMPLATE_DIR / template_name
    if not path.exists():
        raise SystemExit(f"缺少模板：{path}")
    text = path.read_text(encoding="utf-8")
    for key, value in mapping.items():
        text = text.replace("{{" + key + "}}", value)
    return text


class Writer:
    def __init__(self) -> None:
        self.created: list[pathlib.Path] = []
        self.skipped: list[pathlib.Path] = []

    def write(self, path: pathlib.Path, text: str) -> None:
        if path.exists():
            self.skipped.append(path)
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        self.created.append(path)

    def keep_dir(self, path: pathlib.Path) -> None:
        self.write(path / ".gitkeep", "")


def module_mapping(feature: str, slug: str, code: str, date: str, is_common: bool) -> dict[str, str]:
    return {
        "FEATURE": feature,
        "DATE": date,
        "MODULE_TITLE": f"module-{slug}",
        "MOD": code,
        "BRD_REF": "../../brd.md",
        "COMMON_REF": "本模块即公共契约" if is_common else "../module-common/design.md",
        "SOURCE_EXAMPLE": "BR-01",
        "OVERALL_REF": "../../task-list-overall.md",
        "STAGE": "0" if is_common else "1",
    }


def single_mapping(feature: str, code: str, date: str) -> dict[str, str]:
    return {
        "FEATURE": feature,
        "DATE": date,
        "MODULE_TITLE": feature,
        "MOD": code,
        "BRD_REF": "本文件即需求基底（M 规模无 BRD）",
        "COMMON_REF": "无（单模块）",
        "SOURCE_EXAMPLE": "用户需求 / discovery.md",
        "OVERALL_REF": "无（单模块）",
        "STAGE": "1",
    }


def write_common_files(writer: Writer, feature_dir: pathlib.Path, feature: str, date: str, with_discovery: bool) -> None:
    writer.keep_dir(feature_dir / "records")
    writer.keep_dir(feature_dir / "changes")
    writer.write(
        feature_dir / "acceptance" / "manual-test-checklist.md",
        render("manual-test-checklist.md", {"FEATURE": feature, "DATE": date}),
    )
    if with_discovery:
        writer.write(feature_dir / "discovery.md", render("discovery.md", {"FEATURE": feature, "DATE": date}))


def scaffold_m(writer: Writer, feature_dir: pathlib.Path, feature: str, code: str, date: str, with_discovery: bool) -> None:
    mapping = single_mapping(feature, code, date)
    for name in ("requirements.md", "design.md", "tasks.md"):
        writer.write(feature_dir / name, render(name, mapping))
    write_common_files(writer, feature_dir, feature, date, with_discovery)


def scaffold_l(
    writer: Writer,
    feature_dir: pathlib.Path,
    feature: str,
    modules: list[str],
    date: str,
    with_discovery: bool,
) -> None:
    if "common" not in modules:
        modules = ["common", *modules]
    codes = {slug: module_code(slug) for slug in modules}

    brd_rows = []
    overview_rows = []
    task_rows = []
    for slug in modules:
        code = codes[slug]
        is_common = slug == "common"
        depends = "-" if is_common else "module-common"
        brd_rows.append(f"| module-{slug} | {code} |  |  |  | {depends} |")
        overview_rows.append(f"| module-{slug} | {code} |  |  |  | 0/2 |")
        stage = "0" if is_common else "1"
        task_rows.append(f"| T-{code}-01 | module-{slug} |  | 未开始 |  | {stage} |  |")
        task_rows.append(f"| T-{code}-02 | module-{slug} |  | 未开始 | T-{code}-01 | {stage} |  |")

    writer.write(
        feature_dir / "brd.md",
        render("brd.md", {"FEATURE": feature, "DATE": date, "MODULE_TABLE_ROWS": "\n".join(brd_rows)}),
    )
    writer.write(
        feature_dir / "task-list-overall.md",
        render(
            "task-list-overall.md",
            {
                "FEATURE": feature,
                "DATE": date,
                "MODULE_TABLE_ROWS": "\n".join(overview_rows),
                "TASK_TABLE_ROWS": "\n".join(task_rows),
            },
        ),
    )
    for slug in modules:
        mapping = module_mapping(feature, slug, codes[slug], date, slug == "common")
        module_dir = feature_dir / "modules" / f"module-{slug}"
        for name in ("requirements.md", "design.md", "tasks.md"):
            writer.write(module_dir / name, render(name, mapping))
    write_common_files(writer, feature_dir, feature, date, with_discovery)


def main() -> int:
    parser = argparse.ArgumentParser(description="生成 spec-driven-ai-coding 文档骨架")
    parser.add_argument("--root", default="docs/开发设计文档", help="文档根目录，默认 docs/开发设计文档")
    parser.add_argument("--feature", required=True, help="需求 slug，例如 order-center")
    parser.add_argument("--tier", required=True, choices=["M", "L"], help="规模：M 单模块；L 多模块")
    parser.add_argument("--modules", default="", help="L 规模的模块 slug 列表，逗号分隔；common 会自动加入")
    parser.add_argument("--code", default="", help="M 规模的模块短码，默认由 feature 生成")
    parser.add_argument("--with-discovery", action="store_true", help="同时生成 discovery.md")
    parser.add_argument("--date", default=dt.date.today().isoformat(), help="文档日期，默认今天")
    args = parser.parse_args()

    feature = args.feature.strip()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", feature):
        parser.error("--feature 只能包含字母、数字、连字符、下划线")

    feature_dir = pathlib.Path(args.root) / feature
    writer = Writer()

    if args.tier == "M":
        if args.modules:
            parser.error("M 规模不接受 --modules；需要拆模块请用 --tier L")
        code = args.code.strip().upper() if args.code else module_code(feature)
        scaffold_m(writer, feature_dir, feature, code, args.date, args.with_discovery)
    else:
        modules = [m.strip() for m in args.modules.split(",") if m.strip()]
        if not modules:
            parser.error("L 规模至少提供一个业务模块，例如 --modules auth,order")
        scaffold_l(writer, feature_dir, feature, modules, args.date, args.with_discovery)

    print(f"文档根目录：{feature_dir}")
    if writer.created:
        print("已创建：")
        for path in writer.created:
            if path.name != ".gitkeep":
                print(f"  {path}")
    if writer.skipped:
        print("已存在，跳过：")
        for path in writer.skipped:
            if path.name != ".gitkeep":
                print(f"  {path}")
        if args.tier == "L":
            print("提示：brd.md 与 task-list-overall.md 已存在时不会自动追加新模块的表格行，请手动补齐。")

    print()
    print("下一步：")
    if args.tier == "L":
        print("  1. 填写 brd.md（BR-xx、用户流程、约束与假设、模块划分）→ CP1 请用户确认")
        print("  2. 填写各模块 requirements.md / design.md / tasks.md 与 task-list-overall.md → CP2")
    else:
        print("  1. 填写 requirements.md（R-xx + 验收标准）→ CP1")
        print("  2. 填写 design.md 与 tasks.md → CP2")
    print(f"  3. 运行检查：python3 {SKILL_DIR / 'scripts' / 'check_spec.py'} {feature_dir}")
    print("  模板中的占位需求/任务（*-01、*-02）需要替换为真实内容，check_spec 会提示未填项。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
