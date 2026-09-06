#!/usr/bin/env python3
"""Create a NEW v2 spec. Existing directories are never migrated or overwritten."""
from __future__ import annotations
import argparse
import datetime as dt
import json
import pathlib
import re
from spec_core import CODE, SpecError, local_path, safe_relative

SKILL = pathlib.Path(__file__).resolve().parent.parent
SLUG = r"[a-z0-9]+(?:[-_][a-z0-9]+)*"


def module_code(slug: str) -> str:
    result = slug.upper().replace("-", "_")
    if not re.fullmatch(CODE, result):
        raise SpecError("模块短码须以字母开头，1–32 个大写字母/数字/下划线；M 可用 --code 指定")
    return result


def render(name: str, values: dict[str, str]) -> str:
    template = (SKILL / "templates" / name).read_text(encoding="utf-8")
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    if re.search(r"\{\{[^{}]+\}\}", template):
        raise SpecError(f"模板变量未全部替换：{name}")
    return template


def new_config(feature: str, tier: str, modules: list[dict[str, str]], risk: str) -> dict:
    return {"schema_version": 2, "feature": feature, "tier": tier, "risk": risk,
            "current_increment": "I1", "modules": modules,
            "increments": [{"id": "I1", "title": "首个可验收增量", "status": "planning",
                "approval": {"state": "pending", "by": "", "basis": "", "digest": ""},
                "acceptance": {"state": "pending", "by": "", "basis": "", "digest": "", "record": ""}}],
            "decisions": [], "parallel": {"enabled": False, "integrator": "", "shared_files": []}}


def build_files(feature: str, tier: str, modules: list[dict[str, str]], risk: str, date: str, discovery: bool) -> dict[str, str]:
    files = {"spec.json": json.dumps(new_config(feature, tier, modules, risk), ensure_ascii=False, indent=2) + "\n"}
    business_slugs = [m["slug"] for m in modules if m["slug"] != "common"]
    source_ids = {slug: f"BR-{i + 1:02}" for i, slug in enumerate(business_slugs)}
    for mod in modules:
        values = {"TITLE": mod["slug"], "CODE": mod["code"], "DATE": date,
                  "SOURCE": source_ids.get(mod["slug"], "BR-01") if tier == "L" else "用户请求（补充出处或原文）"}
        for name in ("requirements.md", "design.md", "tasks.md"):
            path = name if tier == "M" else mod["path"] + "/" + name
            files[path] = render(name, values)
    if tier == "L":
        business = []
        for slug in business_slugs:
            business.append(f"### {source_ids[slug]} <标题>\n\n| 字段 | 值 |\n| --- | --- |\n| 状态 | active |\n| 批次 | I1 |\n\n#### 说明\n\n<说明>\n\n#### 验收要点\n\n<说明>\n")
        index = "\n".join(f"- {m['slug']}：`{m['path']}/requirements.md`、`{m['path']}/design.md`。" for m in modules)
        files["brd.md"] = render("brd.md", {"TITLE": feature, "BUSINESS_ITEMS": "\n".join(business), "MODULE_INDEX": index})
    if discovery:
        files["discovery.md"] = render("discovery.md", {"TITLE": feature, "DATE": date})
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description="生成全新 v2 Spec 骨架；不覆盖，不迁移，不批准")
    parser.add_argument("--root", type=pathlib.Path, default=pathlib.Path("docs/开发设计文档"))
    parser.add_argument("--feature", required=True)
    parser.add_argument("--tier", required=True, choices=("M", "L"))
    parser.add_argument("--modules", default="", help="L 业务模块 slug，逗号分隔；不自动添加 common")
    parser.add_argument("--with-common", action="store_true", help="L 确需独立共享模块时显式添加")
    parser.add_argument("--code", default="", help="M 自定义短码")
    parser.add_argument("--risk", choices=("low", "medium", "high"), default="medium")
    parser.add_argument("--date", default=dt.date.today().isoformat())
    parser.add_argument("--with-discovery", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        if not re.fullmatch(SLUG, args.feature) or len(args.feature) > 80:
            raise SpecError("feature 须为不超过 80 字符的小写 slug，不允许路径字符")
        if dt.date.fromisoformat(args.date).isoformat() != args.date:
            raise SpecError("date 须为 YYYY-MM-DD")
        if args.tier == "M":
            if args.modules or args.with_common:
                raise SpecError("M 不接受 --modules/--with-common；升级请按 migration.md 操作")
            code = args.code if args.code else module_code(args.feature)
            if not re.fullmatch(CODE, code):
                raise SpecError("--code 格式非法，应为 1–32 位大写字母/数字/下划线且字母开头")
            modules = [{"slug": args.feature, "code": code, "path": "."}]
        else:
            if args.code:
                raise SpecError("--code 只适用于 M")
            slugs = args.modules.split(",") if args.modules else []
            if not slugs or any(not re.fullmatch(SLUG, s) for s in slugs) or not any(s != "common" for s in slugs):
                raise SpecError("L 至少指定一个合法业务模块；slug 不允许空项、路径、首尾空格")
            if args.with_common and "common" not in slugs:
                slugs = ["common", *slugs]
            codes = [module_code(s) for s in slugs]
            if len(slugs) != len(set(slugs)) or len(codes) != len(set(codes)):
                raise SpecError("模块名重复或短码冲突（例如 a-b 与 a_b）")
            modules = [{"slug": s, "code": c, "path": f"modules/module-{s}"} for s, c in zip(slugs, codes)]
        root = args.root.absolute()
        # An explicitly chosen root may be outside the project, but must not traverse symlinks.
        for part in [root, *root.parents]:
            if part.is_symlink():
                raise SpecError("root 不接受符号链接路径")
        target = local_path(root, args.feature)
        if target.exists():
            raise SpecError(f"目标已存在，拒绝覆盖/追加/自动升级：{target}")
        files = build_files(args.feature, args.tier, modules, args.risk, args.date, args.with_discovery)
        for path in files:
            safe_relative(path)
        if args.dry_run:
            print("仅预览，不写文件：")
        else:
            root.mkdir(parents=True, exist_ok=True)
            target.mkdir(exist_ok=False)  # exclusive reservation: no clobber of concurrent creator
        for relative, content in files.items():
            if not args.dry_run:
                path = local_path(target, relative)
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("x", encoding="utf-8", newline="\n") as handle:
                    handle.write(content)
            print(target / relative)
        print("骨架为 draft，不代表 ready 或已批准。填写当前增量后检查 ready；批准前不实施。")
        print("records/changes/acceptance 只在需要时创建，不预生成空台账。")
        return 0
    except (SpecError, ValueError, OSError) as exc:
        print(f"[ERROR] {exc}\n若写入中断，保留现场供检查；脚本不会覆盖重跑。")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
