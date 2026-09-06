#!/usr/bin/env python3
"""Shared, read-only validation logic. Python 3.10+, standard library only.

This is deliberately a parser for the documented v2 Markdown subset, not a
CommonMark parser, test executor, approval authority, or distributed task lock.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import pathlib
import re
from dataclasses import dataclass, field
from typing import Any

VERSION = "2.0.0"
CODE = r"[A-Z][A-Z0-9_]{0,31}"
RID = rf"R-{CODE}-[0-9]+"
TID = rf"T-{CODE}-[0-9]+"
ACID = rf"AC-{CODE}-[0-9]+-[0-9]+"
VID = rf"V-{CODE}-[0-9]+-[0-9]+"
BRID = r"BR-[0-9]+"
INCREMENT = r"I[1-9][0-9]*"
STATUSES = {"未开始", "进行中", "待验证", "已完成", "阻塞", "废弃"}
REQ_STATUSES = {"active", "deferred", "retired"}
TYPES = {"unit", "component", "interface", "browser", "integration", "static", "manual", "other"}
PROGRESSED = {"进行中", "待验证", "已完成"}
PLACEHOLDER = re.compile(r"\{\{[^{}]+\}\}|<(?:标题|条件|操作|可观察结果|待填|文件路径|命令|说明)>")
GENERATED = "<!-- spec-driven-ai-coding:generated:v2; DO NOT EDIT -->"


class SpecError(ValueError):
    """Malformed or unsafe input, with an actionable message."""


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SpecError(f"JSON 键重复：{key}")
        result[key] = value
    return result


def load_json(path: pathlib.Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=unique_object)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SpecError(f"无法读取 JSON {path.name}: {exc}") from exc


def text(path: pathlib.Path) -> str:
    try:
        if path.is_symlink() or not path.is_file():
            raise SpecError(f"不是普通文件或文件缺失：{path}")
        return path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    except (OSError, UnicodeError) as exc:
        raise SpecError(f"无法读取 {path}: {exc}") from exc


def safe_relative(value: str, *, allow_dot: bool = False) -> str:
    """Portable paths: POSIX separators; no escapes, globbing, drive or URI."""
    if not isinstance(value, str) or not value or value != value.strip():
        raise SpecError(f"路径为空或有首尾空格：{value!r}")
    if value == "." and allow_dot:
        return value
    if "\\" in value or ":" in value or any(c in value for c in "*?[]\n\r\0"):
        raise SpecError(f"路径需为相对路径，不允许盘符、URL、反斜线或通配符：{value}")
    path = pathlib.PurePosixPath(value)
    if path.is_absolute() or any(p in {"", ".", ".."} for p in value.rstrip("/").split("/")):
        raise SpecError(f"路径越界或不是规范相对路径：{value}")
    return value


def local_path(root: pathlib.Path, value: str, *, allow_dot: bool = False) -> pathlib.Path:
    safe_relative(value, allow_dot=allow_dot)
    target = root / value
    # Reject symlink traversal, even when a link points inside the root.
    cur = root
    if root.is_symlink():
        raise SpecError(f"不接受符号链接根目录：{root}")
    for part in pathlib.PurePosixPath(value).parts:
        cur = cur / part
        if cur.is_symlink():
            raise SpecError(f"不接受符号链接路径：{value}")
    if not target.resolve().is_relative_to(root.resolve()):
        raise SpecError(f"路径逃出 spec 根：{value}")
    return target


def nonempty(value: str) -> bool:
    return bool(value.strip()) and value.strip() not in {"-", "—", "[]", "[ ]"}


def concrete(value: str) -> bool:
    # An unchecked/empty bullet is not content; words such as the real enum
    # "todo" inside prose must not be treated as template placeholders.
    clean = re.sub(r"(?m)^\s*(?:[-*]\s+(?:\[[ xX]\]\s*)?|[0-9]+\.\s+)", "", value).strip()
    return nonempty(clean) and clean not in {"TODO", "TBD", "FIXME"} and not PLACEHOLDER.search(value)


def normalized(value: str) -> str:
    return "\n".join(line.rstrip() for line in value.strip().splitlines())


def digest(value: Any) -> str:
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def visible_lines(value: str) -> list[str]:
    """Ignore fenced examples and HTML comments while preserving line numbers."""
    result: list[str] = []
    fence: tuple[str, int] | None = None
    comment = False
    for line in value.splitlines():
        # HTML comment stripping is intentionally limited to actual comment spans.
        out = ""
        rest = line
        while rest:
            if comment:
                end = rest.find("-->")
                if end < 0:
                    rest = ""
                else:
                    comment, rest = False, rest[end + 3:]
            else:
                start = rest.find("<!--")
                if start < 0:
                    out += rest
                    rest = ""
                else:
                    out += rest[:start]
                    rest, comment = rest[start + 4:], True
        m = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", out)
        if fence:
            if m and m[1][0] == fence[0] and len(m[1]) >= fence[1] and not m[2].strip():
                fence = None
            result.append("")
        elif m:
            fence = (m[1][0], len(m[1]))
            result.append("")
        else:
            result.append(out)
    if fence:
        raise SpecError("Markdown 代码围栏未闭合")
    if comment:
        raise SpecError("HTML 注释未闭合")
    return result


def split_row(line: str) -> list[str]:
    """A literal pipe in a cell must be escaped as \\|, including in code spans."""
    line = line.strip()
    if not (line.startswith("|") and line.endswith("|")):
        raise SpecError("表格行必须以 | 开始和结束")
    parts: list[str] = []
    buf = ""
    i = 1
    while i < len(line) - 1:
        if line[i] == "\\" and i + 1 < len(line) - 1 and line[i + 1] in "|\\":
            buf += line[i + 1]
            i += 2
        elif line[i] == "|":
            parts.append(buf.strip())
            buf = ""
            i += 1
        else:
            buf += line[i]
            i += 1
    parts.append(buf.strip())
    return parts


def tables(value: str) -> list[tuple[list[str], list[dict[str, str]]]]:
    lines = visible_lines(value)
    result: list[tuple[list[str], list[dict[str, str]]]] = []
    i = 0
    while i + 1 < len(lines):
        if not lines[i].lstrip().startswith("|") or not lines[i + 1].lstrip().startswith("|"):
            i += 1
            continue
        headers = split_row(lines[i])
        separators = split_row(lines[i + 1])
        if not all(re.fullmatch(r":?-{3,}:?", c) for c in separators):
            i += 1
            continue
        if len(headers) != len(separators) or len(headers) != len(set(headers)):
            raise SpecError(f"表格列数不一致或列名重复，局部行 {i + 1}")
        rows = []
        j = i + 2
        while j < len(lines) and lines[j].lstrip().startswith("|"):
            cells = split_row(lines[j])
            if len(cells) != len(headers):
                raise SpecError(f"表格列数错误，局部行 {j + 1}；单元格内 | 应写为 \\|")
            rows.append(dict(zip(headers, cells)))
            j += 1
        result.append((headers, rows))
        i = j
    return result


def table(value: str, headers: list[str], *, required: bool = True) -> list[dict[str, str]]:
    found = [rows for cols, rows in tables(value) if cols == headers]
    if len(found) > 1:
        raise SpecError(f"重复权威表格：{' / '.join(headers)}")
    if not found:
        if required:
            raise SpecError(f"缺少表格，精确列名应为：{' / '.join(headers)}")
        return []
    return found[0]


def metadata(value: str) -> dict[str, str]:
    result = {}
    # Entity metadata must precede the first subheading; nested model tables do not count.
    prefix = re.split(r"^#{1,6}\s", "\n".join(visible_lines(value)), maxsplit=1, flags=re.M)[0]
    for row in table(prefix, ["字段", "值"]):
        if row["字段"] in result:
            raise SpecError(f"元数据字段重复：{row['字段']}")
        result[row["字段"]] = row["值"]
    return result


def section(value: str, title: str) -> str:
    lines = value.splitlines()
    visible = visible_lines(value)
    headings = []
    for i, line in enumerate(visible):
        m = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if m:
            headings.append((i, len(m[1]), m[2]))
    targets = [h for h in headings if h[2] == title]
    if len(targets) > 1:
        raise SpecError(f"章节重复：{title}")
    if not targets:
        return ""
    start, level, _ = targets[0]
    end = next((i for i, lev, _ in headings if i > start and lev <= level), len(lines))
    return "\n".join(lines[start + 1:end]).strip()


def ids(value: str, pattern: str) -> list[str]:
    if not nonempty(value):
        return []
    tokens = [s.strip().strip("`") for s in re.split(r"[,，]", value)]
    if any(not re.fullmatch(pattern, s) for s in tokens):
        raise SpecError(f"编号列表格式不合法：{value}")
    if len(tokens) != len(set(tokens)):
        raise SpecError(f"编号列表重复：{value}")
    return tokens


@dataclass
class Entity:
    id: str
    title: str
    body: str
    path: pathlib.Path
    line: int
    meta: dict[str, str]
    module: str = ""
    acs: dict[str, str] = field(default_factory=dict)
    reqs: list[str] = field(default_factory=list)
    deps: list[str] = field(default_factory=list)
    accepts: list[str] = field(default_factory=list)
    writes: list[str] = field(default_factory=list)
    checks: dict[str, dict[str, str]] = field(default_factory=dict)


def entities(path: pathlib.Path, kind: str) -> list[Entity]:
    raw = text(path)
    lines = raw.splitlines()
    visible = visible_lines(raw)
    pattern = {"BR": BRID, "R": RID, "T": TID}[kind]
    found: list[Entity] = []
    starts = []
    for i, line in enumerate(visible):
        m = re.match(r"^###\s+(\S+)(?:\s+(.*))?$", line)
        if m and m[1].startswith(kind + "-"):
            if not re.fullmatch(pattern, m[1]):
                raise SpecError(f"{path.name}:{i + 1} 编号格式错误：{m[1]}")
            starts.append((i, m[1], (m[2] or "").strip()))
    for i, eid, title in starts:
        end = len(lines)
        for j in range(i + 1, len(lines)):
            if re.match(r"^#{1,3}\s", visible[j]):
                end = j
                break
        body = "\n".join(lines[i + 1:end])
        found.append(Entity(eid, title, body, path, i + 1, metadata(body)))
    return found


@dataclass
class Report:
    root: pathlib.Path
    stage: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)
    requirements: dict[str, Entity] = field(default_factory=dict)
    business: dict[str, Entity] = field(default_factory=dict)
    tasks: dict[str, Entity] = field(default_factory=dict)
    scope_digest: str = ""
    task_digests: dict[str, str] = field(default_factory=dict)
    increment_digest: str = ""

    def error(self, message: str, item: Entity | None = None) -> None:
        loc = f"{item.path.relative_to(self.root)}:{item.line}: " if item else ""
        self.errors.append(loc + message)

    def pending(self, message: str, item: Entity | None = None) -> None:
        if self.stage == "draft":
            self.warnings.append((item.id + ": " if item else "") + message)
        else:
            self.error(message, item)

    def result(self) -> dict[str, Any]:
        return {"version": VERSION, "stage": self.stage, "errors": self.errors,
                "warnings": self.warnings, "scope_digest": self.scope_digest,
                "increment_digest": self.increment_digest, "task_digests": self.task_digests,
                "meaning": "仅结构、引用与声明完整性检查；不证明批准真实、代码正确或测试实际执行。"}


def require_keys(obj: Any, keys: set[str], label: str) -> None:
    if not isinstance(obj, dict):
        raise SpecError(f"{label} 必须是对象")
    missing = keys - obj.keys()
    if missing:
        raise SpecError(f"{label} 缺少字段：{', '.join(sorted(missing))}")


def validate_config(root: pathlib.Path) -> dict[str, Any]:
    cfg = load_json(local_path(root, "spec.json"))
    require_keys(cfg, {"schema_version", "feature", "tier", "risk", "current_increment", "increments", "modules"}, "spec.json")
    if type(cfg["schema_version"]) is not int or cfg["schema_version"] != 2:
        raise SpecError("只接受 schema_version: 2；旧格式请读 references/migration.md，不自动迁移")
    if cfg["tier"] not in {"M", "L"} or cfg["risk"] not in {"low", "medium", "high"}:
        raise SpecError("tier 必须为 M/L；risk 必须为 low/medium/high")
    if not isinstance(cfg["feature"], str) or not re.fullmatch(r"[a-z0-9]+(?:[-_][a-z0-9]+)*", cfg["feature"]):
        raise SpecError("feature 必须是小写英文/数字 slug，可用单个 - 或 _ 分段")
    if not isinstance(cfg["increments"], list) or not cfg["increments"]:
        raise SpecError("increments 必须是非空数组")
    seen = set()
    for inc in cfg["increments"]:
        require_keys(inc, {"id", "title", "status", "approval", "acceptance"}, "increment")
        if not isinstance(inc["id"], str) or not re.fullmatch(INCREMENT, inc["id"]) or inc["id"] in seen:
            raise SpecError("批次 ID 非法或重复")
        seen.add(inc["id"])
        if inc["status"] not in {"planning", "implementing", "verifying", "accepted"}:
            raise SpecError("批次 status 非法")
        if not isinstance(inc["title"], str) or not nonempty(inc["title"]):
            raise SpecError("批次 title 不能为空")
        for key in ("approval", "acceptance"):
            require_keys(inc[key], {"state", "by", "basis", "digest"}, key)
            if not all(isinstance(v, str) for v in inc[key].values()):
                raise SpecError(f"{key} 字段值必须为字符串")
        if inc["approval"]["state"] not in {"pending", "approved", "delegated"}:
            raise SpecError("approval.state 非法")
        if inc["acceptance"]["state"] not in {"pending", "accepted"}:
            raise SpecError("acceptance.state 非法")
    if cfg["current_increment"] not in seen:
        raise SpecError("current_increment 未在 increments 中定义")
    if not isinstance(cfg["modules"], list) or not cfg["modules"]:
        raise SpecError("modules 必须是非空数组")
    codes, paths, slugs = set(), set(), set()
    for mod in cfg["modules"]:
        require_keys(mod, {"slug", "code", "path"}, "module")
        if not all(isinstance(mod[k], str) for k in ("slug", "code", "path")):
            raise SpecError("module 字段必须为字符串")
        if not re.fullmatch(r"[a-z0-9]+(?:[-_][a-z0-9]+)*", mod["slug"]) or not re.fullmatch(CODE, mod["code"]):
            raise SpecError("模块 slug 或短码不合法")
        if mod["code"] in codes or mod["path"] in paths or mod["slug"] in slugs:
            raise SpecError("模块 slug、短码、路径必须分别唯一")
        codes.add(mod["code"]); paths.add(mod["path"]); slugs.add(mod["slug"])
        expected = "." if cfg["tier"] == "M" else f"modules/module-{mod['slug']}"
        if mod["path"] != expected:
            raise SpecError(f"模块路径应为 {expected}，不支持静默混合 M/L 布局")
        local_path(root, mod["path"], allow_dot=True)
    if cfg["tier"] == "M" and len(cfg["modules"]) != 1:
        raise SpecError("M 只能声明一个模块")
    if cfg["tier"] == "L":
        base = local_path(root, "modules")
        actual = {p.relative_to(root).as_posix() for p in base.iterdir() if p.is_dir()} if base.is_dir() else set()
        if actual != paths:
            raise SpecError(f"modules/ 与 spec.json 声明不一致：{sorted(actual.symmetric_difference(paths))}")
        if any((root / name).exists() for name in ("requirements.md", "design.md", "tasks.md")):
            raise SpecError("L 根目录发现 M 三件套；请明确迁移/归档，不能静默忽略")
    elif (root / "modules").exists() or (root / "brd.md").exists():
        raise SpecError("M 中发现 L 文件；请明确迁移，不能根据文件存在性猜规模")
    decisions = cfg.get("decisions", [])
    if not isinstance(decisions, list):
        raise SpecError("decisions 必须是数组")
    decision_ids = set()
    for decision in decisions:
        require_keys(decision, {"id", "increment", "blocking", "state", "text", "resolution"}, "decision")
        if not isinstance(decision["id"], str) or not re.fullmatch(r"[AQ]-[0-9]+", decision["id"]) or decision["id"] in decision_ids:
            raise SpecError("决策编号非法或重复")
        decision_ids.add(decision["id"])
        if decision["increment"] not in seen or type(decision["blocking"]) is not bool or decision["state"] not in {"open", "resolved"}:
            raise SpecError("决策批次、阻断标记或状态非法")
        if not all(isinstance(decision[k], str) for k in ("text", "resolution")):
            raise SpecError("决策 text/resolution 必须是字符串")
    par = cfg.get("parallel", {"enabled": False, "integrator": "", "shared_files": []})
    require_keys(par, {"enabled", "integrator", "shared_files"}, "parallel")
    if type(par["enabled"]) is not bool or not isinstance(par["integrator"], str) or not isinstance(par["shared_files"], list):
        raise SpecError("parallel 字段类型错误")
    shared = set()
    for item in par["shared_files"]:
        require_keys(item, {"path", "owner"}, "shared_files[]")
        safe_relative(item["path"])
        if item["path"] in shared or not isinstance(item["owner"], str) or not concrete(item["owner"]):
            raise SpecError("共享文件重复或未指定唯一负责人")
        shared.add(item["path"])
    cfg["decisions"], cfg["parallel"] = decisions, par
    return cfg


def add_entities(report: Report, target: dict[str, Entity], path: pathlib.Path, kind: str, module: str = "") -> None:
    for entity in entities(path, kind):
        entity.module = module
        if entity.id in target:
            report.error(f"编号重复：{entity.id}；首次出现于 {target[entity.id].path.relative_to(report.root)}:{target[entity.id].line}", entity)
        else:
            target[entity.id] = entity


def active(entity: Entity, increment: str) -> bool:
    return entity.meta.get("批次") == increment and entity.meta.get("状态") == "active"


def validate_requirement(report: Report, entity: Entity, business: bool = False) -> None:
    cfg = report.config
    incs = {i["id"] for i in cfg["increments"]}
    for key in ("状态", "批次"):
        if key not in entity.meta:
            report.error(f"缺少元数据：{key}", entity)
    if entity.meta.get("状态") not in REQ_STATUSES or entity.meta.get("批次") not in incs:
        report.error("需求状态或批次非法", entity)
    if not business and entity.id.split("-")[1] != entity.module:
        report.error("R 短码与声明的模块短码不一致", entity)
    if not business:
        for line in visible_lines(section(entity.body, "验收标准")):
            match = re.match(rf"^\s*-\s+({ACID})\s*[:：]\s*(.*)$", line)
            if match:
                if match[1] in entity.acs:
                    report.error(f"AC 编号重复：{match[1]}", entity)
                expected = "AC-" + entity.id[2:] + "-"
                if not match[1].startswith(expected):
                    report.error(f"AC 编号必须以 {expected} 开头", entity)
                entity.acs[match[1]] = match[2].strip()
            elif re.match(r"^\s*-\s+AC-", line):
                report.error("AC 编号或格式错误，使用 - AC-MOD-01-1: 条件、操作、结果", entity)
    if active(entity, cfg["current_increment"]):
        if not concrete(entity.title):
            report.pending("需求标题为空或仍为模板占位", entity)
        if not concrete(section(entity.body, "说明")):
            report.pending("缺少具体的「说明」", entity)
        if business:
            if not concrete(section(entity.body, "验收要点")):
                report.pending("BR 缺少验收要点", entity)
        else:
            if not entity.acs or any(not concrete(v) for v in entity.acs.values()):
                report.pending("AC 缺失、为空或仍为模板占位", entity)
            if not concrete(section(entity.body, "边界与异常")):
                report.pending("边界与异常为空；不适用也需说明理由", entity)
            if not concrete(entity.meta.get("来源", "")):
                report.pending("需求缺少来源", entity)
    if not business and cfg["tier"] == "L":
        sources = ids(entity.meta.get("来源", ""), BRID)
        for source in sources:
            if source not in report.business:
                report.error(f"来源 {source} 不存在", entity)
            elif entity.meta.get("状态") == "active" and report.business[source].meta.get("状态") == "retired":
                report.error(f"有效需求不能来源于 retired 的 {source}", entity)
        if active(entity, cfg["current_increment"]) and not sources:
            report.pending("L 当前需求必须关联至少一个 BR", entity)


def validate_task(report: Report, entity: Entity) -> None:
    current = report.config["current_increment"]
    if entity.id.split("-")[1] != entity.module:
        report.error("T 短码与声明模块不一致", entity)
    if entity.meta.get("状态") not in STATUSES:
        report.error("任务状态非法", entity)
    if entity.meta.get("批次") not in {i["id"] for i in report.config["increments"]}:
        report.error("任务批次不存在", entity)
    entity.reqs = ids(entity.meta.get("需求", ""), RID)
    entity.accepts = ids(entity.meta.get("验收", ""), ACID)
    entity.deps = ids(entity.meta.get("依赖", ""), TID)
    raw_writes = entity.meta.get("写集", "")
    if nonempty(raw_writes):
        entity.writes = [p.strip().strip("`") for p in re.split(r"[,，]", raw_writes)]
        for path in entity.writes:
            safe_relative(path)
        if len(entity.writes) != len(set(entity.writes)):
            report.error("写集路径重复", entity)
    rows = table(section(entity.body, "验证计划"), ["检查", "类型", "要求", "命令或步骤", "不适用理由"], required=False)
    for row in rows:
        vid = row["检查"]
        if not re.fullmatch(VID, vid) or not vid.startswith("V-" + entity.id[2:] + "-"):
            report.error(f"检查编号与任务不匹配：{vid}", entity)
        if vid in entity.checks:
            report.error(f"重复检查编号：{vid}", entity)
        entity.checks[vid] = row
        if row["类型"] not in TYPES or row["要求"] not in {"required", "na"}:
            report.error(f"检查类型或要求非法：{vid}", entity)
    live_current = entity.meta.get("批次") == current and entity.meta.get("状态") != "废弃"
    if live_current:
        for key, value in (("标题", entity.title), ("实现要点", section(entity.body, "实现要点"))):
            if not concrete(value):
                report.pending(f"任务{key}为空或为占位", entity)
        if not entity.reqs or not entity.accepts or not entity.writes:
            report.pending("任务必须有关联需求、验收 AC、明确写集", entity)
        if not entity.checks or not any(r["要求"] == "required" for r in entity.checks.values()):
            report.pending("任务必须至少有一个 required 验证项", entity)
        for row in entity.checks.values():
            if row["要求"] == "required" and not concrete(row["命令或步骤"]):
                report.pending(f"{row['检查']} 缺少可执行命令或人工步骤", entity)
            if row["要求"] == "na" and not concrete(row["不适用理由"]):
                report.pending(f"{row['检查']} 的 N/A 缺少理由", entity)
    known_acs = {aid for rid in entity.reqs if rid in report.requirements for aid in report.requirements[rid].acs}
    for rid in entity.reqs:
        if rid not in report.requirements:
            report.error(f"关联需求不存在：{rid}", entity)
        elif live_current and report.requirements[rid].meta.get("状态") != "active":
            report.error(f"当前有效任务关联了非 active 需求：{rid}", entity)
    for aid in entity.accepts:
        if aid not in known_acs:
            report.error(f"AC {aid} 不属于任务关联的需求或不存在", entity)
    for dep in entity.deps:
        if dep == entity.id:
            report.error("任务依赖自身", entity)
        elif dep not in report.tasks:
            report.error(f"依赖不存在：{dep}", entity)
        elif entity.meta.get("状态") != "废弃" and report.tasks[dep].meta.get("状态") == "废弃":
            report.error(f"有效任务依赖废弃任务：{dep}", entity)
        elif entity.meta.get("状态") in PROGRESSED and report.tasks[dep].meta.get("状态") != "已完成":
            report.error(f"已开始任务的依赖尚未完成：{dep}", entity)
    if entity.meta.get("状态") in PROGRESSED and entity.deps:
        evidence = entity.meta.get("依赖确认", "")
        if not concrete(evidence) or any(dep not in evidence for dep in entity.deps):
            report.error("必须在「依赖确认」记录每个依赖已在当前基线可用的版本/核验方式", entity)


def find_cycles(tasks: dict[str, Entity]) -> list[str]:
    """Iterative DFS: no recursion-depth failure on long dependency chains."""
    color: dict[str, int] = {}
    cycles: list[str] = []
    for start in tasks:
        if color.get(start):
            continue
        stack: list[tuple[str, Any]] = [(start, iter(tasks[start].deps))]
        path = [start]
        color[start] = 1
        while stack:
            node, deps = stack[-1]
            dep = next(deps, None)
            if dep is None:
                color[node] = 2
                stack.pop(); path.pop()
            elif dep in tasks:
                if color.get(dep) == 1:
                    cycles.append(" → ".join(path[path.index(dep):] + [dep]))
                elif not color.get(dep):
                    color[dep] = 1
                    path.append(dep)
                    stack.append((dep, iter(tasks[dep].deps)))
    return cycles


def document_context(path: pathlib.Path, kind: str) -> str:
    """Common scope text outside entity blocks (goals, non-goals, constraints)."""
    raw = text(path)
    lines = raw.splitlines()
    visible = visible_lines(raw)
    skip = False
    result = []
    for i, line in enumerate(visible):
        if re.match(r"^#{1,3}\s", line):
            skip = bool(re.match(r"^###\s+" + kind + r"-", line))
        if not skip:
            result.append(lines[i])
    return normalized("\n".join(result))


def compute_digests(report: Report) -> None:
    current = report.config["current_increment"]
    reqs = [r for r in report.requirements.values() if active(r, current)]
    brs = [r for r in report.business.values() if active(r, current)]
    sources = {bid for r in reqs for bid in ids(r.meta.get("来源", ""), BRID)} if report.config["tier"] == "L" else set()
    brs += [r for bid, r in report.business.items() if bid in sources and r not in brs]
    # Scope deliberately excludes task progress and routine implementation design.
    report.scope_digest = digest({"increment": current, "risk": report.config["risk"],
                                  "requirements": [(r.id, r.title, normalized(r.body)) for r in sorted(reqs, key=lambda x: x.id)],
                                  "business": [(r.id, r.title, normalized(r.body)) for r in sorted(brs, key=lambda x: x.id)],
                                  "context": {str(p.relative_to(report.root)): document_context(p, kind)
                                      for p, kind in [(r.path, "R") for r in reqs] + [(r.path, "BR") for r in brs]}})
    for tid, t in report.tasks.items():
        report.task_digests[tid] = digest({"id": tid, "title": t.title, "increment": t.meta.get("批次"),
            "requirements": t.reqs, "acs": t.accepts, "deps": t.deps, "writes": t.writes,
            "plan": normalized(section(t.body, "实现要点")), "checks": t.checks,
            "requirement_context": {r.id: {"title": r.title, "description": normalized(section(r.body, "说明")),
                                          "boundaries": normalized(section(r.body, "边界与异常"))}
                                    for r in report.requirements.values() if r.id in t.reqs},
            "acceptance_text": {aid: r.acs[aid] for r in report.requirements.values() for aid in t.accepts if aid in r.acs}})
    report.increment_digest = digest({"scope": report.scope_digest,
        "tasks": {tid: report.task_digests[tid] for tid, t in report.tasks.items()
                  if t.meta.get("批次") == current and t.meta.get("状态") != "废弃"}})


def proof(report: Report, value: str) -> bool:
    if value.startswith("file:"):
        path = local_path(report.root, value[5:])
        return path.is_file() and bool(text(path).strip())
    # Tool/CI reports may be binary screenshots or remote; use trace IDs as declarations.
    return any(value.startswith(prefix) and concrete(value[len(prefix):]) for prefix in ("inline:", "ci:", "tool:"))


def record_check(report: Report, task: Entity) -> None:
    if not task.reqs or not task.accepts or not task.writes or not any(c["要求"] == "required" for c in task.checks.values()):
        report.error("已完成任务必须具有需求、AC、写集和 required 验证计划（包括 draft 检查）", task)
    rec = task.meta.get("实施记录", "")
    if not nonempty(rec):
        report.error("已完成任务缺少实施记录路径", task)
        return
    path = local_path(report.root, rec)
    raw = text(path)
    if not raw.strip():
        report.error("实施记录为空", task)
        return
    # Strip the top-level title before parsing record metadata.
    body = re.sub(r"\A\s*# [^\n]*\n", "", raw, count=1)
    meta = metadata(body)
    if meta.get("任务") != task.id:
        report.error("实施记录关联的任务不匹配", task)
    date = task.meta.get("完成日期", "")
    try:
        parsed = dt.date.fromisoformat(date)
        if date != parsed.isoformat():
            raise ValueError("not canonical")
    except ValueError:
        report.error("已完成任务缺少合法完成日期 YYYY-MM-DD", task)
    if meta.get("日期") != date:
        report.error("任务与实施记录日期不一致", task)
    if not concrete(meta.get("验证版本", "")) or not concrete(meta.get("环境", "")):
        report.error("实施记录缺少实际验证版本或环境", task)
    if meta.get("任务指纹") != report.task_digests.get(task.id):
        report.error("实施记录的任务指纹缺失或过期；验收/写集/验证计划变化后应重新评估", task)
    checks = table(raw, ["检查", "结果", "证据"])
    indexed: dict[str, dict[str, str]] = {}
    for row in checks:
        if row["检查"] in indexed or row["检查"] not in task.checks:
            report.error(f"实施记录检查项重复或未在任务计划中声明：{row['检查']}", task)
        indexed[row["检查"]] = row
    passed = set()
    for vid, plan in task.checks.items():
        row = indexed.get(vid)
        if row is None:
            report.error(f"实施记录遗漏验证项：{vid}", task)
            continue
        expected = "通过" if plan["要求"] == "required" else "不适用"
        if row["结果"] != expected or not proof(report, row["证据"]):
            report.error(f"{vid} 未通过或缺少可定位证据；required 不能用未运行/N/A 替代", task)
        elif expected == "通过":
            passed.add(vid)
    ac_rows = table(raw, ["验收", "结果", "关联检查"])
    acs = {}
    for row in ac_rows:
        if row["验收"] in acs or row["验收"] not in task.accepts:
            report.error("实施记录 AC 重复或超出该任务声明", task)
        acs[row["验收"]] = row
    for aid in task.accepts:
        row = acs.get(aid)
        vids = ids(row["关联检查"], VID) if row else []
        if not row or row["结果"] != "通过" or not vids or any(vid not in passed for vid in vids):
            report.error(f"{aid} 没有关联到已通过且有证据的验证项", task)
    for title in ("实际结果", "风险与未执行项"):
        if not concrete(section(raw, title)):
            report.error(f"实施记录缺少「{title}」", task)


def overlap(a: str, b: str) -> bool:
    a, b = a.rstrip("/"), b.rstrip("/")
    return a == b or a.startswith(b + "/") or b.startswith(a + "/")


def parallel_check(report: Report) -> None:
    cfg = report.config["parallel"]
    if not cfg["enabled"]:
        return
    if not concrete(cfg["integrator"]):
        report.pending("并行开发必须指定单一集成/协调负责人")
    current = [t for t in report.tasks.values() if t.meta.get("批次") == report.config["current_increment"] and t.meta.get("状态") != "废弃"]
    for task in current:
        owner = task.meta.get("负责人", "")
        if not concrete(owner):
            report.pending("并行任务必须指定负责人", task)
        for shared in cfg["shared_files"]:
            if any(overlap(shared["path"], path) for path in task.writes) and owner != shared["owner"]:
                report.error(f"共享写路径 {shared['path']} 只能由 {shared['owner']} 修改", task)
    running = [t for t in current if t.meta.get("状态") in {"进行中", "待验证"}]
    for i, left in enumerate(running):
        for right in running[i + 1:]:
            if left.meta.get("负责人") == right.meta.get("负责人"):
                report.error(f"同一负责人同时领取两个活动任务：{left.id}, {right.id}")
            elif any(overlap(a, b) for a in left.writes for b in right.writes):
                report.error(f"并行任务写集冲突：{left.id}, {right.id}")


def approval_check(report: Report, required: bool) -> None:
    cfg = report.config
    inc = next(i for i in cfg["increments"] if i["id"] == cfg["current_increment"])
    approval = inc["approval"]
    if required or approval["state"] != "pending":
        if approval["state"] == "pending":
            report.error("当前批次尚未批准；文件存在/ready 通过不等于获准实施")
        elif approval["state"] == "delegated" and cfg["risk"] == "high":
            report.error("high 风险不能用笼统授权 delegated 代替具体批准")
        if not concrete(approval["by"]) or not concrete(approval["basis"]):
            report.error("批准缺少确认人/授权来源；不得自行编造用户确认")
        if approval["digest"] != report.scope_digest:
            report.error("批准的需求范围指纹缺失或过期")
    accepted = inc["acceptance"]
    if inc["status"] == "accepted" or accepted["state"] == "accepted":
        if inc["status"] != "accepted" or accepted["state"] != "accepted":
            report.error("批次状态与验收状态不一致")
        if any(not concrete(accepted.get(k, "")) for k in ("by", "basis", "record")):
            report.error("批次验收缺少确认人、依据或记录")
        else:
            if not text(local_path(report.root, accepted["record"])).strip():
                report.error("批次验收记录为空")
        if accepted["digest"] != report.increment_digest:
            report.error("批次验收指纹过期；任务/需求变化后不得沿用原验收")
        if any(t.meta.get("状态") not in {"已完成", "废弃"} for t in report.tasks.values() if t.meta.get("批次") == inc["id"]):
            report.error("批次宣称验收，但仍存在未完成任务")


def validate(root: pathlib.Path, stage: str = "ready", *, require_approval: bool = False, check_overall: bool = False) -> Report:
    root = root.absolute()
    report = Report(root, stage)
    if stage not in {"draft", "ready", "done"}:
        report.error("stage 必须是 draft/ready/done")
        return report
    try:
        report.config = validate_config(root)
        cfg = report.config
        if cfg["tier"] == "L":
            add_entities(report, report.business, local_path(root, "brd.md"), "BR")
            if not report.business:
                report.error("brd.md 未定义 BR")
        for mod in cfg["modules"]:
            module_dir = local_path(root, mod["path"], allow_dot=True)
            add_entities(report, report.requirements, module_dir / "requirements.md", "R", mod["code"])
            add_entities(report, report.tasks, module_dir / "tasks.md", "T", mod["code"])
            # Even deferred modules have a brief design file, not mandatory full details.
            text(module_dir / "design.md")
        for item in report.business.values():
            validate_requirement(report, item, business=True)
        global_acs = set()
        for item in report.requirements.values():
            validate_requirement(report, item)
            for aid in item.acs:
                if aid in global_acs:
                    report.error(f"全局 AC 重复：{aid}", item)
                global_acs.add(aid)
        for item in report.tasks.values():
            validate_task(report, item)
        for cycle in find_cycles(report.tasks):
            report.error("依赖成环：" + cycle)
        current = cfg["current_increment"]
        reqs = [r for r in report.requirements.values() if active(r, current)]
        tasks_now = [t for t in report.tasks.values() if t.meta.get("批次") == current and t.meta.get("状态") != "废弃"]
        if not reqs:
            report.pending("当前批次没有 active 需求")
        for req in reqs:
            covered = {aid for t in tasks_now if req.id in t.reqs for aid in t.accepts}
            if not any(req.id in t.reqs for t in tasks_now):
                report.pending("当前需求未被当前批次的有效任务覆盖", req)
            for aid in req.acs:
                if aid not in covered:
                    report.pending(f"验收标准未被有效任务覆盖：{aid}", req)
        for br in report.business.values():
            if active(br, current) and not any(br.id in ids(r.meta.get("来源", ""), BRID) for r in reqs):
                report.pending("当前 BR 未被当前批次 active 模块需求覆盖", br)
        for mod in cfg["modules"]:
            current_reqs = [r for r in reqs if r.module == mod["code"]]
            if not current_reqs:
                continue
            req_path = local_path(root, mod["path"], allow_dot=True) / "requirements.md"
            if PLACEHOLDER.search(document_context(req_path, "R")):
                report.pending(f"{req_path.relative_to(root)} 的范围/约束仍有模板占位")
            design_path = local_path(root, mod["path"], allow_dot=True) / "design.md"
            design = text(design_path)
            for title in ("现状与约束", "方案与取舍", "代码落点", "验证与风险"):
                if not concrete(section(design, title)):
                    report.pending(f"{design_path.relative_to(root)} 的「{title}」为空或占位")
            mapping = table(section(design, "需求映射"), ["需求", "设计元素"], required=False)
            mapped = {}
            for row in mapping:
                if row["需求"] in mapped:
                    report.error("设计需求映射重复：" + row["需求"])
                if row["需求"] not in report.requirements:
                    report.error("设计引用未知需求：" + row["需求"])
                mapped[row["需求"]] = row["设计元素"]
            for req in current_reqs:
                if not concrete(mapped.get(req.id, "")):
                    report.pending(f"设计缺少 {req.id} 的具体设计元素映射")
        if cfg["tier"] == "L" and PLACEHOLDER.search(document_context(local_path(root, "brd.md"), "BR")):
            report.pending("BRD 范围/约束仍有模板占位")
        for decision in cfg["decisions"]:
            if decision["state"] == "resolved" and not concrete(decision["resolution"]):
                report.error("已解决决策缺少结论：" + decision["id"])
            if decision["increment"] == current and decision["blocking"] and decision["state"] == "open":
                report.pending("当前批次存在阻断问题/假设：" + decision["id"])
        compute_digests(report)
        for task in report.tasks.values():
            if task.meta.get("状态") == "已完成":
                record_check(report, task)
            elif stage == "done" and task.meta.get("批次") == current and task.meta.get("状态") != "废弃":
                report.error("done 要求当前有效任务全部已完成", task)
        parallel_check(report)
        inc = next(i for i in cfg["increments"] if i["id"] == current)
        started = any(t.meta.get("状态") in PROGRESSED for t in tasks_now)
        approval_check(report, require_approval or stage == "done" or started or inc["status"] in {"implementing", "verifying", "accepted"})
        if check_overall:
            view = local_path(root, "task-list-overall.md")
            if not view.is_file() or text(view) != render_overall(report):
                report.error("总览缺失或过期；运行 render_overall.py <root> --write，不手工同步")
    except (SpecError, OSError, UnicodeError) as exc:
        report.error(str(exc))
    except (TypeError, KeyError, AttributeError, IndexError) as exc:
        report.error(f"输入字段类型/结构错误：{exc}")
    return report


def escape_cell(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")


def render_overall(report: Report) -> str:
    cfg = report.config
    lines = [GENERATED, f"# {cfg['feature']} 任务总览", "",
             "由各模块 tasks.md 生成；它不是第二份任务状态来源。", "",
             f"规模：{cfg['tier']}；风险：{cfg['risk']}；当前批次：{cfg['current_increment']}。", "",
             "| 任务 | 模块 | 标题 | 状态 | 批次 | 需求 | 依赖 | 负责人 | 实施记录 | 集成版本 |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for tid, t in sorted(report.tasks.items()):
        values = [tid, t.module, t.title, t.meta.get("状态", ""), t.meta.get("批次", ""),
                  t.meta.get("需求", ""), t.meta.get("依赖", ""), t.meta.get("负责人", ""),
                  t.meta.get("实施记录", ""), t.meta.get("集成版本", "")]
        lines.append("| " + " | ".join(escape_cell(v) for v in values) + " |")
    lines.extend(["", "## 批次与批准", "", "| 批次 | 名称 | 状态 | 范围批准 | 整体验收 |", "| --- | --- | --- | --- | --- |"])
    for inc in cfg["increments"]:
        values = [inc["id"], inc["title"], inc["status"], inc["approval"]["state"], inc["acceptance"]["state"]]
        lines.append("| " + " | ".join(escape_cell(v) for v in values) + " |")
    lines.append("")
    return "\n".join(lines)
