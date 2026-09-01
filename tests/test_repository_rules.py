from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = REPOSITORY_ROOT / "scripts" / "check-repository.py"
SPEC = importlib.util.spec_from_file_location("quantbrief_repository_checker", CHECKER_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load repository checker from {CHECKER_PATH}")
CHECKER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CHECKER
SPEC.loader.exec_module(CHECKER)


class RepositoryRuleTests(unittest.TestCase):
    def test_current_repository_satisfies_architecture_contract(self) -> None:
        self.assertEqual([], CHECKER.collect_violations(REPOSITORY_ROOT))

    def test_reverse_dependency_reports_a_repair_direction(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / "quantbrief"
            package.mkdir()
            (package / "models.py").write_text("from .pipeline import Pipeline\n", encoding="utf-8")

            violations = CHECKER.python_architecture_violations(root)

        self.assertEqual(1, len(violations))
        self.assertIn("imports disallowed module(s) pipeline", violations[0])
        self.assertIn("Move orchestration upward", violations[0])

    def test_new_product_module_must_join_the_documented_graph(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / "quantbrief"
            package.mkdir()
            (package / "misc.py").write_text("VALUE = 1\n", encoding="utf-8")

            violations = CHECKER.python_architecture_violations(root)

        self.assertEqual(1, len(violations))
        self.assertIn("undeclared product module", violations[0])
        self.assertIn("ARCHITECTURE.md", violations[0])

    def test_daily_workflow_requires_deepseek_bilingual_summaries(self) -> None:
        workflow = (REPOSITORY_ROOT / ".github" / "workflows" / "daily-brief.yml").read_text(encoding="utf-8")

        self.assertIn("SUMMARY_PROVIDER: deepseek", workflow)
        self.assertIn("DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}", workflow)
        self.assertIn("--require-ai", workflow)
        self.assertNotIn("OPENAI_API_KEY:", workflow)
        self.assertIn("cron: '10 2 * * *'", workflow)
        self.assertIn("timezone: 'Asia/Singapore'", workflow)


if __name__ == "__main__":
    unittest.main()
