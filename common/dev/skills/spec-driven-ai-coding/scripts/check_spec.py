#!/usr/bin/env python3
"""Check v2 specs without running their commands or changing files."""
from __future__ import annotations
import argparse
import json
import pathlib
from spec_core import validate


def main() -> int:
    parser = argparse.ArgumentParser(description="检查 v2 Spec 的结构、追踪、批准与验证声明；不执行测试")
    parser.add_argument("root", type=pathlib.Path, help="含 spec.json 的需求目录")
    parser.add_argument("--stage", choices=("draft", "ready", "done"), default="ready")
    parser.add_argument("--require-approval", action="store_true", help="实施前检查当前范围已批准/获明确授权")
    parser.add_argument("--check-overall", action="store_true", help="要求只读总览存在且与源文档一致")
    parser.add_argument("--json", action="store_true", help="结构化结果，含批准和任务指纹")
    args = parser.parse_args()
    report = validate(args.root, args.stage, require_approval=args.require_approval, check_overall=args.check_overall)
    if args.json:
        print(json.dumps(report.result(), ensure_ascii=False, indent=2))
    else:
        for message in report.errors:
            print("[ERROR] " + message)
        for message in report.warnings:
            print("[WARN]  " + message)
        print(f"阶段 {args.stage}：{len(report.errors)} error，{len(report.warnings)} warning")
        print("范围指纹：" + report.scope_digest)
        print("批次指纹：" + report.increment_digest)
        print("仅检查结构与声明完整性，不证明实际批准、实际执行或业务正确性。")
    return 1 if report.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
