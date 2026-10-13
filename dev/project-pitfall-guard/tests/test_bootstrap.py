"""Smoke tests for project-pitfall-guard's scaffold and the generated add_pitfall.py."""
from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile
import unittest

SKILL = pathlib.Path(__file__).resolve().parents[3] / "common" / "dev" / "skills" / "project-pitfall-guard"
BOOTSTRAP = SKILL / "scripts" / "bootstrap_project_pitfall_guard.py"


def run(script: pathlib.Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True, text=True, encoding="utf-8", timeout=30,
    )


def frontmatter(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8").split("---", 2)[1]


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def project(self, name: str, *markers: str) -> pathlib.Path:
        path = self.root / name
        path.mkdir()
        for marker in markers:
            (path / marker).write_text("", encoding="utf-8")
        return path

    def test_claude_project_goes_to_claude_skills(self):
        project = self.project("My App", "CLAUDE.md")
        result = run(BOOTSTRAP, "--project-root", str(project))
        self.assertEqual(result.returncode, 0, result.stderr)
        skill = project / ".claude" / "skills" / "my-app-pitfall-guard"
        self.assertTrue((skill / "SKILL.md").exists())
        self.assertIn("name: my-app-pitfall-guard", frontmatter(skill / "SKILL.md"))

    def test_agents_project_and_explicit_dir(self):
        project = self.project("svc", "AGENTS.md")
        self.assertEqual(run(BOOTSTRAP, "--project-root", str(project)).returncode, 0)
        self.assertTrue((project / ".agents" / "skills" / "svc-pitfall-guard" / "SKILL.md").exists())
        result = run(BOOTSTRAP, "--project-root", str(project), "--skill-name", "other-pitfall-guard",
                     "--skills-dir", ".claude/skills")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((project / ".claude" / "skills" / "other-pitfall-guard").is_dir())

    def test_non_ascii_name_requires_skill_name_and_meta_name_is_rejected(self):
        project = self.project("中文项目")
        result = run(BOOTSTRAP, "--project-root", str(project))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--skill-name", result.stderr)
        result = run(BOOTSTRAP, "--project-root", str(project), "--skill-name", "project-pitfall-guard")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(any(project.rglob("SKILL.md")))

    def test_add_pitfall_escapes_cells_and_force_keeps_records(self):
        project = self.project("app", "CLAUDE.md")
        run(BOOTSTRAP, "--project-root", str(project))
        skill = project / ".claude" / "skills" / "app-pitfall-guard"
        add = skill / "scripts" / "add_pitfall.py"
        first = run(add, "--title", "构建 缓存", "--area", "Build | CI", "--triggers", "vite", "--summary", "stale | cache")
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(run(add, "--title", "构建 缓存", "--area", "x", "--triggers", "y", "--summary", "z").returncode, 1)

        forced = run(BOOTSTRAP, "--project-root", str(project), "--force")
        self.assertEqual(forced.returncode, 0, forced.stderr)
        second = run(add, "--title", "Second", "--area", "QA", "--triggers", "x", "--summary", "y")
        self.assertEqual(second.returncode, 0, second.stderr)

        index = (skill / "references" / "index.md").read_text(encoding="utf-8")
        rows = [line for line in index.splitlines() if line.startswith("| PROJ-PIT-")]
        self.assertEqual([row.split(" | ")[0] for row in rows], ["| PROJ-PIT-0001", "| PROJ-PIT-0002"])
        self.assertIn("Build \\| CI", rows[0])
        self.assertTrue(all(row.replace("\\|", "").count("|") == 5 for row in rows))

    def test_yaml_values_survive_special_characters(self):
        try:
            import yaml  # type: ignore[import-untyped]
        except ImportError:
            self.skipTest("PyYAML not installed")
        project = self.project("app", "CLAUDE.md")
        result = run(BOOTSTRAP, "--project-root", str(project), "--project-name", 'App: "x"',
                     "--skill-name", "x-pitfall-guard")
        self.assertEqual(result.returncode, 0, result.stderr)
        skill = project / ".claude" / "skills" / "x-pitfall-guard"
        self.assertEqual(yaml.safe_load(frontmatter(skill / "SKILL.md"))["name"], "x-pitfall-guard")
        interface = yaml.safe_load((skill / "agents" / "openai.yaml").read_text(encoding="utf-8"))["interface"]
        self.assertEqual(interface["display_name"], 'App: "x" Pitfall Guard')


if __name__ == "__main__":
    unittest.main()
