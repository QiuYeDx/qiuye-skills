from __future__ import annotations
import copy
import json
import pathlib
import tempfile
import unittest
from fixtures import baseline, approve, complete, config, save, replace, put, requirement, task
from spec_core import validate, render_overall, split_row, visible_lines, SpecError


class SpecTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = baseline(pathlib.Path(self.tmp.name) / "spec")

    def tearDown(self):
        self.tmp.cleanup()

    def reject(self, fragment: str = "", stage="ready", **options):
        report = validate(self.root, stage, **options)
        self.assertTrue(report.errors, report.result())
        if fragment:
            self.assertIn(fragment, "\n".join(report.errors), report.result())
        return report

    def test_baseline_ready(self):
        self.assertEqual(validate(self.root).errors, [])

    def test_pending_approval_is_not_execute(self):
        self.reject("尚未批准", require_approval=True)

    def test_approved_ready(self):
        approve(self.root)
        self.assertEqual(validate(self.root, require_approval=True).errors, [])

    def test_requirement_scope_change_invalidates_approval(self):
        approve(self.root)
        replace(self.root, "requirements.md", "输出只包含完成记录", "输出包含全部记录")
        self.reject("指纹", require_approval=True)

    def test_non_goal_change_invalidates_approval(self):
        approve(self.root)
        replace(self.root, "requirements.md", "不做文件上传", "增加文件上传")
        self.reject("指纹", require_approval=True)

    def test_design_detail_change_does_not_invalidate_scope(self):
        approve(self.root)
        replace(self.root, "design.md", "使用 csv 模块", "继续使用标准 csv 模块")
        self.assertEqual(validate(self.root, require_approval=True).errors, [])

    def test_task_progress_does_not_invalidate_scope(self):
        approve(self.root)
        replace(self.root, "tasks.md", "| 状态 | 未开始 |", "| 状态 | 进行中 |")
        self.assertEqual(validate(self.root).errors, [])

    def test_started_task_requires_approval(self):
        replace(self.root, "tasks.md", "| 状态 | 未开始 |", "| 状态 | 进行中 |")
        self.reject("尚未批准")

    def test_high_risk_no_blanket_delegation(self):
        cfg = config(self.root); cfg["risk"] = "high"; save(self.root, cfg)
        approve(self.root, "delegated")
        self.reject("high")

    def test_low_risk_explicit_delegation(self):
        approve(self.root, "delegated")
        self.assertEqual(validate(self.root, require_approval=True).errors, [])

    def test_approval_needs_source(self):
        approve(self.root)
        cfg = config(self.root); cfg["increments"][0]["approval"]["basis"] = ""; save(self.root, cfg)
        self.reject("授权来源")

    def test_completed_task(self):
        approve(self.root); complete(self.root)
        self.assertEqual(validate(self.root, "done").errors, [])

    def test_done_does_not_accept_pending_tasks(self):
        approve(self.root)
        self.reject("全部已完成", "done")

    def test_duplicate_requirement(self):
        with (self.root / "requirements.md").open("a") as f:
            f.write("\n" + requirement())
        self.reject("编号重复")

    def test_duplicate_task_not_overwritten(self):
        with (self.root / "tasks.md").open("a") as f:
            f.write("\n" + task(state="非法状态"))
        self.reject("编号重复")

    def test_duplicate_ac(self):
        replace(self.root, "requirements.md", "#### 边界与异常", "- AC-APP-01-1: 再定义一次。\n\n#### 边界与异常")
        self.reject("AC 编号重复")

    def test_todo_enum_is_not_a_placeholder(self):
        replace(self.root, "requirements.md", "导出满足状态筛选的行", "导出 status 为 todo 的行")
        self.assertEqual(validate(self.root).errors, [])

    def test_literal_todo_title_is_placeholder(self):
        replace(self.root, "requirements.md", "只导出满足筛选条件的记录", "TODO")
        self.reject("标题")

    def test_duplicate_named_section_rejected(self):
        replace(self.root, "design.md", "## 验证与风险", "## 方案与取舍\n\n另一个互相矛盾的权威设计。\n\n## 验证与风险")
        self.reject("章节重复")

    def test_empty_checkbox_is_not_content(self):
        replace(self.root, "requirements.md", "导出满足状态筛选的行，保持输入顺序，不改变源数据。", "- [ ]")
        self.reject("具体的「说明」")

    def test_global_scope_placeholder_rejected(self):
        replace(self.root, "requirements.md", "不做文件上传。", "<说明>")
        self.reject("范围/约束")

    def test_blank_title(self):
        replace(self.root, "requirements.md", "只导出满足筛选条件的记录", "<标题>")
        self.reject("标题")

    def test_blank_ac(self):
        replace(self.root, "requirements.md", "输入一条完成记录和一条未完成记录，选择完成状态，输出只包含完成记录。", "")
        self.reject("AC 缺失")

    def test_draft_allows_placeholder_but_warns(self):
        replace(self.root, "requirements.md", "只导出满足筛选条件的记录", "<标题>")
        report = validate(self.root, "draft")
        self.assertEqual(report.errors, [])
        self.assertTrue(report.warnings)

    def test_invalid_id(self):
        replace(self.root, "requirements.md", "### R-APP-01", "### R-app-01")
        self.reject("编号格式")

    def test_invalid_state(self):
        replace(self.root, "tasks.md", "| 状态 | 未开始 |", "| 状态 | 完成了 |")
        self.reject("状态非法")

    def test_unknown_dependency(self):
        replace(self.root, "tasks.md", "| 依赖 | - |", "| 依赖 | T-APP-99 |")
        self.reject("依赖不存在")

    def test_self_dependency(self):
        replace(self.root, "tasks.md", "| 依赖 | - |", "| 依赖 | T-APP-01 |")
        self.reject("依赖自身")

    def test_two_task_dependency_cycle(self):
        replace(self.root, "tasks.md", "| 依赖 | - |", "| 依赖 | T-APP-02 |")
        with (self.root / "tasks.md").open("a") as f:
            f.write("\n" + task(number="02", deps="T-APP-01"))
        self.reject("依赖成环")

    def test_retired_task_does_not_cover_requirement(self):
        replace(self.root, "tasks.md", "| 状态 | 未开始 |", "| 状态 | 废弃 |")
        self.reject("未被")

    def test_active_task_cannot_depend_on_retired(self):
        with (self.root / "tasks.md").open("a") as f:
            f.write("\n" + task(number="02", state="废弃"))
        replace(self.root, "tasks.md", "| 依赖 | - |", "| 依赖 | T-APP-02 |")
        self.reject("废弃任务")

    def test_task_cannot_claim_other_requirement_ac(self):
        replace(self.root, "tasks.md", "| 验收 | AC-APP-01-1 |", "| 验收 | AC-APP-99-1 |")
        self.reject("不属于")

    def test_ac_must_be_covered(self):
        replace(self.root, "requirements.md", "#### 边界与异常", "- AC-APP-01-2: 空数据只返回表头。\n\n#### 边界与异常")
        self.reject("未被有效任务覆盖")

    def test_completed_without_record(self):
        approve(self.root)
        replace(self.root, "tasks.md", "| 状态 | 未开始 |", "| 状态 | 已完成 |")
        self.reject("缺少实施记录")

    def test_empty_record(self):
        approve(self.root); complete(self.root)
        put(self.root, "records/T-APP-01.md", "")
        self.reject("实施记录为空")

    def test_directory_as_record(self):
        approve(self.root); complete(self.root)
        rec = self.root / "records/T-APP-01.md"; rec.unlink(); rec.mkdir()
        self.reject("不是普通文件")

    def test_record_task_mismatch(self):
        approve(self.root); complete(self.root)
        replace(self.root, "records/T-APP-01.md", "| 任务 | T-APP-01 |", "| 任务 | T-APP-02 |")
        self.reject("不匹配")

    def test_invalid_completion_date(self):
        approve(self.root); complete(self.root)
        replace(self.root, "tasks.md", "2026-09-06", "2026-02-31")
        self.reject("合法完成日期")

    def test_done_missing_revision(self):
        approve(self.root); complete(self.root)
        replace(self.root, "records/T-APP-01.md", "synthetic-fixture-revision-not-a-real-test-run", "-")
        self.reject("验证版本")

    def test_empty_evidence(self):
        approve(self.root); complete(self.root)
        replace(self.root, "records/T-APP-01.md", "inline:synthetic unit-test fixture only", "inline:")
        self.reject("缺少可定位证据")

    def test_required_not_run(self):
        approve(self.root); complete(self.root)
        replace(self.root, "records/T-APP-01.md", "| V-APP-01-1 | 通过 |", "| V-APP-01-1 | 未运行 |")
        self.reject("未通过")

    def test_required_cannot_be_na(self):
        approve(self.root); complete(self.root)
        replace(self.root, "records/T-APP-01.md", "| V-APP-01-1 | 通过 |", "| V-APP-01-1 | 不适用 |")
        self.reject("未通过")

    def test_missing_record_check(self):
        approve(self.root); complete(self.root)
        replace(self.root, "records/T-APP-01.md", "| V-APP-01-1 | 通过 | inline:synthetic unit-test fixture only |", "")
        self.reject("遗漏验证项")

    def test_changed_test_plan_invalidates_evidence(self):
        approve(self.root); complete(self.root)
        replace(self.root, "tasks.md", "python -m unittest discover -s tests", "python -m unittest discover -s tests -v")
        self.reject("任务指纹")

    def test_changed_implementation_target_invalidates_evidence(self):
        approve(self.root); complete(self.root)
        replace(self.root, "tasks.md", "src/app.py", "src/another.py")
        self.reject("任务指纹")

    def test_unfinished_dependency_for_started_task(self):
        with (self.root / "tasks.md").open("a") as f:
            f.write("\n" + task(number="02"))
        replace(self.root, "tasks.md", "### T-APP-01", "### T-APP-01")
        value = (self.root / "tasks.md").read_text()
        value = value.replace("| 依赖 | - |", "| 依赖 | T-APP-02 |", 1).replace("| 状态 | 未开始 |", "| 状态 | 已完成 |", 1)
        put(self.root, "tasks.md", value)
        self.reject("依赖尚未完成")

    def test_na_requires_reason(self):
        replace(self.root, "tasks.md", "| V-APP-01-1 | unit | required |", "| V-APP-01-1 | unit | na |")
        self.reject("N/A 缺少理由")

    def test_unknown_check_type(self):
        replace(self.root, "tasks.md", "| unit | required |", "| unknown | required |")
        self.reject("类型或要求非法")

    def test_missing_write_set(self):
        replace(self.root, "tasks.md", "src/app.py, tests/test_app.py", "-")
        self.reject("明确写集")

    def test_scope_path_escape(self):
        replace(self.root, "tasks.md", "src/app.py", "../outside.py")
        self.reject("路径越界")

    def test_windows_absolute_path_rejected(self):
        replace(self.root, "tasks.md", "src/app.py", "C:\\outside.py")
        self.reject("盘符")

    def test_glob_write_set_rejected(self):
        replace(self.root, "tasks.md", "src/app.py", "src/**")
        self.reject("通配符")

    def test_fenced_fake_requirement_ignored(self):
        put(self.root, "requirements.md", (self.root / "requirements.md").read_text() + "\n```md\n" + requirement() + "\n```\n")
        self.assertEqual(validate(self.root).errors, [])

    def test_unclosed_fence(self):
        put(self.root, "tasks.md", (self.root / "tasks.md").read_text() + "\n```\n")
        self.reject("未闭合")

    def test_html_comment_fake_id_ignored(self):
        put(self.root, "requirements.md", (self.root / "requirements.md").read_text() + "\n<!--\n" + requirement() + "\n-->\n")
        self.assertEqual(validate(self.root).errors, [])

    def test_bad_table_columns(self):
        replace(self.root, "tasks.md", "| 负责人 | agent-app |", "| 负责人 | agent-app | extra |")
        self.reject("列数错误")

    def test_duplicate_metadata_field(self):
        replace(self.root, "tasks.md", "| 负责人 | agent-app |", "| 负责人 | agent-app |\n| 负责人 | other |")
        self.reject("字段重复")

    def test_escaped_pipe(self):
        self.assertEqual(split_row(r"| A | `a\|b` |"), ["A", "`a|b`"])

    def test_design_needs_real_mapping_not_incidental_id(self):
        replace(self.root, "design.md", "| R-APP-01 | src/app.py 的 export_rows 函数 |", "| R-APP-01 | - |")
        self.reject("具体设计元素")

    def test_json_duplicate_key(self):
        raw = (self.root / "spec.json").read_text().replace('"schema_version": 2', '"schema_version": 2, "schema_version": 2')
        put(self.root, "spec.json", raw)
        self.reject("JSON 键重复")

    def test_json_bad_shape_is_error_not_crash(self):
        for value in ([], None, {"schema_version": 2}, {**config(self.root), "tier": []}):
            with self.subTest(value=value):
                put(self.root, "spec.json", json.dumps(value))
                self.assertTrue(validate(self.root).errors)

    def test_legacy_not_silently_guessed(self):
        (self.root / "spec.json").unlink()
        self.reject("JSON")

    def test_mixed_tiers_rejected(self):
        put(self.root, "brd.md", "# 旧文档")
        self.reject("M 中发现 L")

    def test_missing_module_file(self):
        (self.root / "design.md").unlink()
        self.reject("文件缺失")

    def test_symlink_record_rejected(self):
        approve(self.root); complete(self.root)
        record = self.root / "records/T-APP-01.md"
        outside = self.root.parent / "outside.md"
        outside.write_text(record.read_text()); record.unlink()
        try:
            record.symlink_to(outside)
        except OSError:
            self.skipTest("symlink creation unavailable")
        self.reject("符号链接")

    def test_symlink_requirement_rejected(self):
        file = self.root / "requirements.md"
        outside = self.root.parent / "outside.md"
        outside.write_text(file.read_text()); file.unlink()
        try:
            file.symlink_to(outside)
        except OSError:
            self.skipTest("symlink creation unavailable")
        self.reject("不是普通文件")

    def test_record_path_escape_rejected(self):
        approve(self.root); complete(self.root)
        replace(self.root, "tasks.md", "records/T-APP-01.md", "../outside.md")
        self.reject("路径越界")

    def test_file_evidence_must_exist(self):
        approve(self.root); complete(self.root)
        replace(self.root, "records/T-APP-01.md", "inline:synthetic unit-test fixture only", "file:evidence/missing.txt")
        self.reject("缺少可定位证据")

    def test_empty_file_evidence_rejected(self):
        approve(self.root); complete(self.root)
        put(self.root, "evidence/empty.txt", "")
        replace(self.root, "records/T-APP-01.md", "inline:synthetic unit-test fixture only", "file:evidence/empty.txt")
        self.reject("缺少可定位证据")

    def test_blocking_open_decision(self):
        cfg = config(self.root)
        cfg["decisions"] = [{"id":"Q-01","increment":"I1","blocking":True,"state":"open","text":"角色归属待确认","resolution":""}]
        save(self.root,cfg)
        self.reject("阻断问题")

    def test_nonblocking_open_question_allowed(self):
        cfg = config(self.root)
        cfg["decisions"] = [{"id":"Q-01","increment":"I1","blocking":False,"state":"open","text":"后续导出样式","resolution":""}]
        save(self.root,cfg)
        self.assertEqual(validate(self.root).errors, [])

    def test_resolved_decision_needs_resolution(self):
        cfg = config(self.root)
        cfg["decisions"] = [{"id":"Q-01","increment":"I1","blocking":True,"state":"resolved","text":"角色归属待确认","resolution":""}]
        save(self.root,cfg)
        self.reject("已解决决策缺少结论")

    def test_generated_overall_matches(self):
        put(self.root, "task-list-overall.md", render_overall(validate(self.root)))
        self.assertEqual(validate(self.root, check_overall=True).errors, [])

    def test_tampered_overall_detected(self):
        put(self.root, "task-list-overall.md", render_overall(validate(self.root)).replace("| APP |", "| WRONG |"))
        self.reject("总览缺失或过期", check_overall=True)

    def test_missing_overall_only_when_requested(self):
        self.assertEqual(validate(self.root).errors, [])
        self.reject("总览缺失", check_overall=True)

    def test_l_without_common(self):
        other = baseline(self.root.parent / "large", "L")
        self.assertEqual(validate(other).errors, [])

    def test_unknown_br_source(self):
        other = baseline(self.root.parent / "large", "L")
        replace(other, "modules/module-ui/requirements.md", "BR-01", "BR-99")
        self.assertTrue(any("不存在" in e for e in validate(other).errors))

    def test_deferred_future_does_not_require_detailed_tasks(self):
        cfg = config(self.root)
        future = copy.deepcopy(cfg["increments"][0]); future["id"] = "I2"; cfg["increments"].append(future); save(self.root,cfg)
        with (self.root / "requirements.md").open("a") as file:
            file.write("\n" + requirement(number="02", batch="I2", state="deferred").replace("只导出满足筛选条件的记录", "<标题>"))
        self.assertEqual(validate(self.root).errors, [])

    def test_parallel_requires_integrator(self):
        cfg = config(self.root); cfg["parallel"]["enabled"] = True; save(self.root,cfg)
        self.reject("集成/协调负责人")

    def test_parallel_shared_owner(self):
        cfg = config(self.root); cfg["parallel"] = {"enabled":True,"integrator":"coord","shared_files":[{"path":"src/","owner":"shared-agent"}]}; save(self.root,cfg)
        self.reject("只能由")

    def test_parallel_same_owner_cannot_run_two_tasks(self):
        cfg = config(self.root); cfg["parallel"].update({"enabled":True,"integrator":"coord"}); save(self.root,cfg)
        with (self.root / "tasks.md").open("a") as file:
            file.write("\n" + task(number="02"))
        approve(self.root)
        replace(self.root, "tasks.md", "| 状态 | 未开始 |", "| 状态 | 进行中 |")
        self.reject("同时领取两个")

    def test_parallel_overlap(self):
        cfg = config(self.root); cfg["parallel"].update({"enabled":True,"integrator":"coord"}); save(self.root,cfg)
        with (self.root / "tasks.md").open("a") as file:
            file.write("\n" + task(number="02").replace("agent-app", "other-agent"))
        approve(self.root)
        replace(self.root, "tasks.md", "| 状态 | 未开始 |", "| 状态 | 进行中 |")
        self.reject("写集冲突")

    def test_acceptance_cannot_claim_pending_tasks(self):
        approve(self.root)
        report = validate(self.root)
        cfg = config(self.root); inc = cfg["increments"][0]; inc["status"] = "accepted"
        inc["acceptance"] = {"state":"accepted","by":"fixture","basis":"synthetic only","digest":report.increment_digest,"record":"acceptance/result.md"}
        put(self.root,"acceptance/result.md","合成验收夹具"); save(self.root,cfg)
        self.reject("仍存在未完成任务")


if __name__ == "__main__":
    unittest.main()
