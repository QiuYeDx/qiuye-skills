"""Synthetic spec fixtures. Their approvals and evidence are NOT real attestations."""
from __future__ import annotations
import json
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from init_spec import new_config
from spec_core import validate


def put(root: pathlib.Path, path: str, value: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(value, encoding="utf-8")


def save(root: pathlib.Path, cfg: dict) -> None:
    put(root, "spec.json", json.dumps(cfg, ensure_ascii=False, indent=2) + "\n")


def config(root: pathlib.Path) -> dict:
    return json.loads((root / "spec.json").read_text())


def replace(root: pathlib.Path, path: str, old: str, new: str) -> None:
    target = root / path
    value = target.read_text()
    assert old in value, (path, old)
    target.write_text(value.replace(old, new), encoding="utf-8")


def requirement(code: str = "APP", number: str = "01", source: str = "用户请求中的导出行为", batch: str = "I1", state: str = "active") -> str:
    return f'''### R-{code}-{number} 只导出满足筛选条件的记录

| 字段 | 值 |
| --- | --- |
| 来源 | {source} |
| 状态 | {state} |
| 批次 | {batch} |

#### 说明

导出满足状态筛选的行，保持输入顺序，不改变源数据。

#### 验收标准

- AC-{code}-{number}-1: 输入一条完成记录和一条未完成记录，选择完成状态，输出只包含完成记录。

#### 边界与异常

没有匹配记录时返回仅含表头的 CSV；缺少 status 字段时拒绝该输入。
'''


def task(code: str = "APP", number: str = "01", reqnumber: str = "01", batch: str = "I1", state: str = "未开始", deps: str = "-") -> str:
    return f'''### T-{code}-{number} 实现按状态筛选的导出函数

| 字段 | 值 |
| --- | --- |
| 状态 | {state} |
| 批次 | {batch} |
| 需求 | R-{code}-{reqnumber} |
| 验收 | AC-{code}-{reqnumber}-1 |
| 依赖 | {deps} |
| 写集 | src/{code.lower()}.py, tests/test_{code.lower()}.py |
| 负责人 | agent-{code.lower()} |
| 依赖确认 | - |
| 完成日期 | - |
| 实施记录 | - |
| 集成版本 | - |

#### 实现要点

对输入先校验再筛选，使用 CSV writer 输出，覆盖空集和非法字段。

#### 验证计划

| 检查 | 类型 | 要求 | 命令或步骤 | 不适用理由 |
| --- | --- | --- | --- | --- |
| V-{code}-{number}-1 | unit | required | python -m unittest discover -s tests | - |
'''


def design(code: str = "APP") -> str:
    return f'''# 设计

## 现状与约束

src/{code.lower()}.py 导出函数尚未实现；沿用 Python 标准库，无外部服务。

## 方案与取舍

使用 csv 模块处理字段转义，而非字符串拼接。

## 代码落点

src/{code.lower()}.py 与 tests/test_{code.lower()}.py。

## 需求映射

| 需求 | 设计元素 |
| --- | --- |
| R-{code}-01 | src/{code.lower()}.py 的 export_rows 函数 |

## 验证与风险

单测覆盖筛选、空集和非法字段；此夹具没有 UI，不运行浏览器。
'''


def baseline(root: pathlib.Path, tier: str = "M") -> pathlib.Path:
    root.mkdir(parents=True, exist_ok=True)
    modules = [{"slug": "demo", "code": "APP", "path": "."}] if tier == "M" else [
        {"slug": "api", "code": "API", "path": "modules/module-api"},
        {"slug": "ui", "code": "UI", "path": "modules/module-ui"}]
    save(root, new_config("demo", tier, modules, "low"))
    for mod in modules:
        prefix = "" if tier == "M" else mod["path"] + "/"
        put(root, prefix + "requirements.md", "# 范围\n\n## 范围外\n\n不做文件上传。\n\n" + requirement(mod["code"], source="BR-01" if tier == "L" else "用户原始请求"))
        put(root, prefix + "design.md", design(mod["code"]))
        put(root, prefix + "tasks.md", "# 任务\n\n" + task(mod["code"]))
    if tier == "L":
        put(root, "brd.md", '''# 业务范围

### BR-01 导出筛选后的记录

| 字段 | 值 |
| --- | --- |
| 状态 | active |
| 批次 | I1 |

#### 说明

给操作人员提供与当前筛选一致的导出结果。

#### 验收要点

完整链路从选择筛选到读取 CSV 的内容一致。
''')
    return root


def approve(root: pathlib.Path, state: str = "approved") -> None:
    report = validate(root, "ready")
    cfg = config(root)
    cfg["increments"][0]["approval"] = {"state": state, "by": "unit-test-fixture",
        "basis": "合成测试夹具，仅用于脚本测试，不代表真实用户批准", "digest": report.scope_digest}
    save(root, cfg)


def complete(root: pathlib.Path, code: str = "APP", number: str = "01", prefix: str = "", deps_confirm: str | None = None) -> None:
    path = prefix + "tasks.md"
    replace(root, path, "| 状态 | 未开始 |", "| 状态 | 已完成 |")
    replace(root, path, "| 完成日期 | - |", "| 完成日期 | 2026-09-06 |")
    rec = f"records/T-{code}-{number}.md"
    replace(root, path, "| 实施记录 | - |", f"| 实施记录 | {rec} |")
    if deps_confirm:
        replace(root, path, "| 依赖确认 | - |", f"| 依赖确认 | {deps_confirm} |")
    report = validate(root, "draft")
    fingerprint = report.task_digests[f"T-{code}-{number}"]
    put(root, rec, f'''# 实施记录：T-{code}-{number}

| 字段 | 值 |
| --- | --- |
| 任务 | T-{code}-{number} |
| 日期 | 2026-09-06 |
| 验证版本 | synthetic-fixture-revision-not-a-real-test-run |
| 环境 | 合成单元测试夹具，无真实业务执行 |
| 任务指纹 | {fingerprint} |

## 实际结果

本记录只用于验证解析与结构门禁，不是实际代码执行证据。

## 验证结果

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| V-{code}-{number}-1 | 通过 | inline:synthetic unit-test fixture only |

## AC 结果

| 验收 | 结果 | 关联检查 |
| --- | --- | --- |
| AC-{code}-01-1 | 通过 | V-{code}-{number}-1 |

## 风险与未执行项

这是门禁测试夹具，不对真实软件行为作保证。
''')
