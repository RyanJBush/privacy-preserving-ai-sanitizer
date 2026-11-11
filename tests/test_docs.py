"""Documentation and CI-config consistency: the README numbers are generated from the reports, the
workflow keeps its guarantees, and importing the CLI does not import Presidio."""
import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

from .support import ROOT

R = Path(ROOT)
sys.path.insert(0, str(R / "scripts"))


@unittest.skipUnless((R / "reports" / "heldout_presidio.json").is_file(), "reports not generated yet")
class ReadmeMatchesReports(unittest.TestCase):
    def test_readme_summary_block_equals_the_rendered_reports(self):
        import render_summary
        readme = (R / "README.md").read_text(encoding="utf-8")
        a, b = readme.index(render_summary.BEGIN) + len(render_summary.BEGIN), readme.index(render_summary.END)
        self.assertEqual(readme[a:b].strip(), render_summary.render().strip())

    def test_summary_file_is_current(self):
        import render_summary
        self.assertEqual((R / "reports" / "SUMMARY.md").read_text(encoding="utf-8").split("\n\n", 1)[1].strip(),
                         render_summary.render().strip())

    def test_required_documents_exist(self):
        for name in ("README.md", "WALKTHROUGH.md", "requirements-presidio.txt", "config/frozen_config.json",
                     ".github/workflows/ci.yml", "docs/handoff/EVALUATION_CONTRACT.md"):
            self.assertTrue((R / name).is_file(), name)


class WorkflowKeepsItsGuarantees(unittest.TestCase):
    def setUp(self):
        self.text = (R / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    def test_structure_by_text(self):
        for needle in ("baseline:", "candidate:", 'REQUIRE_CANDIDATE_TESTS: "1"', "pip check",
                       "scripts/run_tests_no_skips.py", "requirements-presidio.txt", r"C:\pv",
                       "scripts/check_reports.py baseline presidio", "PENDING"):
            self.assertIn(needle, self.text)

    @unittest.skipUnless(importlib.util.find_spec("yaml"), "PyYAML not installed (candidate environment has it)")
    def test_structure_by_yaml(self):
        import yaml
        doc = yaml.safe_load(self.text)
        jobs = doc["jobs"]
        self.assertEqual(set(jobs), {"baseline", "candidate"})
        self.assertEqual(jobs["candidate"]["env"]["REQUIRE_CANDIDATE_TESTS"], "1")
        runs = [s.get("run", "") for s in jobs["candidate"]["steps"]]
        self.assertTrue(any("pip check" in r for r in runs))
        self.assertTrue(any("run_tests_no_skips" in r for r in runs))
        self.assertFalse(any("-m unittest" in r for r in runs))  # the candidate job must use the no-skip runner


class StdlibBaselineStaysStdlib(unittest.TestCase):
    def test_cli_and_core_do_not_import_presidio_or_spacy(self):
        prog = ("import sys\nimport sanitizer.cli, sanitizer.core, sanitizer.evaluation, sanitizer.detectors, sanitizer.demo\n"
                "bad = [m for m in sys.modules if m.split('.')[0] in ('presidio_analyzer', 'spacy', 'tldextract')]\n"
                "print(bad)\n")
        p = subprocess.run([sys.executable, "-c", prog], capture_output=True, text=True, cwd=ROOT)
        self.assertEqual((p.returncode, p.stdout.strip()), (0, "[]"), p.stderr[-400:])


if __name__ == "__main__":
    unittest.main()
