from __future__ import annotations
import ast
import json
import pathlib
import re
import sys
import unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from spec_core import VERSION, validate

ROOT = pathlib.Path(__file__).resolve().parents[1]


class PackageTests(unittest.TestCase):
    def test_entry_name_and_version(self):
        raw = (ROOT / "SKILL.md").read_text()
        self.assertTrue(raw.startswith("---\n"))
        self.assertIn("name: spec-driven-ai-coding\n", raw)
        self.assertIn(f'version: "{VERSION}"', raw)
        self.assertEqual((ROOT / "VERSION").read_text().strip(), VERSION)
        self.assertEqual(ROOT.name, "spec-driven-ai-coding")

    def test_frontmatter_description_limits(self):
        raw = (ROOT / "SKILL.md").read_text().split("---", 2)[1]
        description = re.search(r"description: >-\n(.*?)(?=^\S)", raw, re.S | re.M)[1]
        self.assertGreater(len(description.strip()), 1)
        self.assertLessEqual(len(description.strip()), 1024)
        compat = re.search(r"compatibility: >-\n(.*?)(?=^\S)", raw, re.S | re.M)[1]
        self.assertLessEqual(len(compat.strip()), 500)

    def test_main_under_500_lines(self):
        self.assertLess(len((ROOT / "SKILL.md").read_text().splitlines()), 500)

    def test_all_local_markdown_links_resolve(self):
        for path in ROOT.rglob("*.md"):
            if "validation" in path.parts:
                continue
            raw = path.read_text()
            for link in re.findall(r"\]\(([^)\s]+)\)", raw):
                if "://" in link or link.startswith("#"):
                    continue
                target = (path.parent / link.split("#", 1)[0]).resolve()
                with self.subTest(file=path.relative_to(ROOT), link=link):
                    self.assertTrue(target.exists(), target)

    def test_scripts_syntax(self):
        for path in (ROOT / "scripts").glob("*.py"):
            ast.parse(path.read_text(), filename=str(path))

    def test_m_example_done(self):
        report = validate(ROOT / "examples/m-filter-export/spec", "done", check_overall=True)
        self.assertEqual(report.errors, [], report.result())

    def test_l_example_ready_not_approved(self):
        root = ROOT / "examples/l-rolling/spec"
        self.assertEqual(validate(root, "ready", check_overall=True).errors, [])
        self.assertTrue(validate(root, "ready", require_approval=True).errors)

    def test_evals_are_not_claimed_as_run(self):
        cases = json.loads((ROOT / "evals/cases.json").read_text())
        self.assertEqual(cases["status"], "not_run")
        self.assertEqual(len({c["id"] for c in cases["cases"]}), len(cases["cases"]))
        self.assertGreaterEqual(len(cases["cases"]), 10)
        template = json.loads((ROOT / "evals/run-template.json").read_text())
        self.assertEqual(template["status"], "not_run")


if __name__ == "__main__":
    unittest.main()
