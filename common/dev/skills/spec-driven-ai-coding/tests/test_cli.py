from __future__ import annotations
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from fixtures import baseline

SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / "scripts"


class CliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="spec test 中文 ")
        self.root = pathlib.Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, script, *args):
        return subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)], capture_output=True, text=True, encoding="utf-8", timeout=10)

    def init(self, *args):
        return self.run_cli("init_spec.py", "--root", self.root, *args)

    def test_m_scaffold_is_draft_not_ready(self):
        result = self.init("--feature", "export", "--tier", "M")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        draft = self.run_cli("check_spec.py", self.root / "export", "--stage", "draft", "--json")
        self.assertEqual(draft.returncode, 0, draft.stdout)
        self.assertTrue(json.loads(draft.stdout)["warnings"])
        ready = self.run_cli("check_spec.py", self.root / "export", "--stage", "ready")
        self.assertEqual(ready.returncode, 1)
        self.assertEqual(len(list((self.root / "export").rglob("*"))), 4)

    def test_l_scaffold_without_common(self):
        result = self.init("--feature", "shop", "--tier", "L", "--modules", "auth,order")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertFalse((self.root / "shop/modules/module-common").exists())
        result = self.run_cli("check_spec.py", self.root / "shop", "--stage", "draft")
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_l_optional_common(self):
        result = self.init("--feature", "shop", "--tier", "L", "--modules", "order", "--with-common")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertTrue((self.root / "shop/modules/module-common").is_dir())
        result = self.run_cli("check_spec.py", self.root / "shop", "--stage", "draft")
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_discovery_only_when_requested(self):
        result = self.init("--feature", "export", "--tier", "M", "--with-discovery")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertTrue((self.root / "export/discovery.md").is_file())

    def test_dry_run_no_side_effects(self):
        result = self.init("--feature", "export", "--tier", "M", "--dry-run")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_existing_target_untouched(self):
        target = self.root / "export"; target.mkdir(); (target / "owned.txt").write_text("user work")
        result = self.init("--feature", "export", "--tier", "M")
        self.assertEqual(result.returncode, 1)
        self.assertEqual((target / "owned.txt").read_text(), "user work")
        self.assertEqual(list(target.iterdir()), [target / "owned.txt"])

    def test_m_to_l_not_silently_upgraded(self):
        self.assertEqual(self.init("--feature", "export", "--tier", "M").returncode, 0)
        result = self.init("--feature", "export", "--tier", "L", "--modules", "order")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads((self.root / "export/spec.json").read_text())["tier"], "M")

    def test_feature_traversal_rejected_before_write(self):
        result = self.init("--feature", "../outside", "--tier", "M")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_module_traversal_rejected_before_write(self):
        result = self.init("--feature", "shop", "--tier", "L", "--modules", "../../outside")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_module_code_collision_rejected(self):
        result = self.init("--feature", "shop", "--tier", "L", "--modules", "a-b,a_b")
        self.assertEqual(result.returncode, 1)
        self.assertIn("短码冲突", result.stdout)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_duplicate_module_rejected(self):
        result = self.init("--feature", "shop", "--tier", "L", "--modules", "order,order")
        self.assertEqual(result.returncode, 1)

    def test_trailing_empty_module_rejected(self):
        result = self.init("--feature", "shop", "--tier", "L", "--modules", "order,")
        self.assertEqual(result.returncode, 1)

    def test_custom_code_validated(self):
        result = self.init("--feature", "export", "--tier", "M", "--code", "bad-code")
        self.assertEqual(result.returncode, 1)

    def test_long_feature_can_use_short_custom_code(self):
        result = self.init("--feature", "long-feature-name-which-exceeds-thirty-two-chars", "--tier", "M", "--code", "EXPORT")
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_long_default_code_not_silently_truncated(self):
        result = self.init("--feature", "long-feature-name-which-exceeds-thirty-two-chars", "--tier", "M")
        self.assertEqual(result.returncode, 1)

    def test_m_rejects_module_flags(self):
        result = self.init("--feature", "export", "--tier", "M", "--modules", "x")
        self.assertEqual(result.returncode, 1)

    def test_invalid_date(self):
        result = self.init("--feature", "export", "--tier", "M", "--date", "2026-02-31")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_path_with_spaces_and_unicode(self):
        result = self.init("--feature", "export", "--tier", "M")
        self.assertEqual(result.returncode, 0)
        self.assertTrue((self.root / "export/spec.json").is_file())

    def test_json_cli_clean_output(self):
        root = baseline(self.root / "spec")
        result = self.run_cli("check_spec.py", root, "--json")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(json.loads(result.stdout)["errors"], [])

    def test_unknown_cli_option_not_ignored(self):
        result = self.run_cli("check_spec.py", self.root, "--no-vague")
        self.assertEqual(result.returncode, 2)

    def test_render_stdout_does_not_write(self):
        root = baseline(self.root / "spec")
        result = self.run_cli("render_overall.py", root)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("T-APP-01", result.stdout)
        self.assertFalse((root / "task-list-overall.md").exists())

    def test_render_refuses_manual_overall(self):
        root = baseline(self.root / "spec")
        (root / "task-list-overall.md").write_text("old user-maintained overview")
        result = self.run_cli("render_overall.py", root, "--write")
        self.assertEqual(result.returncode, 1)
        self.assertEqual((root / "task-list-overall.md").read_text(), "old user-maintained overview")

    def test_render_deterministic_and_checkable(self):
        root = baseline(self.root / "spec")
        first = self.run_cli("render_overall.py", root, "--write")
        self.assertEqual(first.returncode, 0, first.stdout)
        contents = (root / "task-list-overall.md").read_bytes()
        second = self.run_cli("render_overall.py", root, "--write")
        self.assertEqual(second.returncode, 0, second.stdout)
        self.assertEqual(contents, (root / "task-list-overall.md").read_bytes())
        check = self.run_cli("check_spec.py", root, "--check-overall")
        self.assertEqual(check.returncode, 0, check.stdout)

    def test_render_rejects_symlink_output(self):
        root = baseline(self.root / "spec")
        outside = self.root / "outside.md"; outside.write_text("unrelated")
        try:
            (root / "task-list-overall.md").symlink_to(outside)
        except OSError:
            self.skipTest("symlinks unavailable")
        result = self.run_cli("render_overall.py", root, "--write")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(outside.read_text(), "unrelated")

    def test_checker_does_not_execute_embedded_commands(self):
        root = baseline(self.root / "spec")
        file = root / "tasks.md"
        file.write_text(file.read_text().replace("python -m unittest discover -s tests", "touch SHOULD_NOT_EXIST"))
        result = self.run_cli("check_spec.py", root)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertFalse((root / "SHOULD_NOT_EXIST").exists())
        self.assertFalse((self.root / "SHOULD_NOT_EXIST").exists())


if __name__ == "__main__":
    unittest.main()
