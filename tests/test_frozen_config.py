"""Frozen-config integrity. Written and run AFTER the development freeze.

Fixture-integrity checks that open heldout.json (summary counts, gold slices) are fixture validation only;
no detector output on held-out data is involved. Held-out detector results exist only in reports/."""
import json
import os
import shutil
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

from sanitizer.config import GRID, check_fixture_integrity, file_sha256, load_frozen_config
from sanitizer.core import ENTITY_PRIORITY, SanitizerError, replace_spans
from sanitizer.evaluation import collect_raw, load_fixture, pick_best, select_thresholds

from .support import FROZEN_CONFIG, ROOT, require_candidate

FIX = Path(ROOT) / "fixtures"
MANIFEST = json.loads((Path(ROOT) / "docs" / "handoff" / "MANIFEST.json").read_text(encoding="utf-8"))


@unittest.skipUnless(os.path.isfile(FROZEN_CONFIG), "no frozen_config.json (freeze not done yet)")
class FrozenConfig(unittest.TestCase):
    def setUp(self):
        self.cfg_raw = json.loads(Path(FROZEN_CONFIG).read_text(encoding="utf-8"))
        self.cfg = load_frozen_config(FROZEN_CONFIG)

    def test_records_the_required_freeze_metadata(self):
        c = self.cfg_raw
        for key in ("thresholds", "recognizer_settings", "packages", "model_wheel_sha256", "resolution_policy",
                    "selection_rule", "development_sha256", "heldout_sha256", "scope", "python", "baseline",
                    "development_metrics_at_selected_thresholds", "selection_grid"):
            self.assertIn(key, c)
        self.assertIn("procedural freeze", c["freeze_kind"])
        self.assertIn("not a blinded external evaluation", c["freeze_kind"])
        self.assertIn("raw bytes only", c["heldout_access"])
        self.assertEqual(c["selection_grid_size"], len(GRID) ** 3)
        self.assertEqual(sorted(c["thresholds"]), sorted(ENTITY_PRIORITY))
        self.assertTrue(all(v in GRID for v in c["thresholds"].values()))
        for pkg in ("presidio-analyzer", "spacy", "en-core-web-sm", "phonenumbers", "tldextract", "regex"):
            self.assertTrue(c["packages"][pkg])

    def test_hashes_match_the_handoff_fixtures_and_files_on_disk(self):
        self.assertEqual(self.cfg["development_sha256"], MANIFEST["development.json"])
        self.assertEqual(self.cfg["heldout_sha256"], MANIFEST["heldout.json"])
        check_fixture_integrity(self.cfg)  # raises on mismatch with fixtures/ on disk

    def test_model_hash_matches_the_requirements_pin(self):
        req = (Path(ROOT) / "requirements-presidio.txt").read_text(encoding="utf-8")
        self.assertIn("sha256=" + self.cfg_raw["model_wheel_sha256"], req)

    def test_selected_thresholds_follow_the_selection_rule_over_the_stored_grid(self):
        grid = []
        for r in self.cfg_raw["selection_grid"]:
            r = dict(r)
            r["_f1"] = Fraction(2 * r["tp"], 2 * r["tp"] + r["fp"] + r["fn"]) if 2 * r["tp"] + r["fp"] + r["fn"] else Fraction(0)
            grid.append(r)
        self.assertEqual(len(grid), 125)
        self.assertEqual(len({tuple(sorted(r["thresholds"].items())) for r in grid}), 125)
        best = pick_best(grid)
        self.assertEqual(best["thresholds"], self.cfg["thresholds"])
        m = self.cfg_raw["development_metrics_at_selected_thresholds"]["micro"]
        self.assertEqual((best["tp"], best["fp"], best["fn"]), (m["tp"], m["fp"], m["fn"]))

    def test_mismatched_or_missing_fixture_bytes_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            for name in ("development.json", "heldout.json"):
                shutil.copy(FIX / name, Path(d) / name)
            check_fixture_integrity(self.cfg, d)
            (Path(d) / "heldout.json").write_bytes((FIX / "heldout.json").read_bytes() + b" ")
            with self.assertRaises(SanitizerError) as cm:
                check_fixture_integrity(self.cfg, d)
            self.assertEqual(str(cm.exception), "SANITIZER_INVALID_CONFIG")
            shutil.copy(FIX / "heldout.json", Path(d) / "heldout.json")
            (Path(d) / "development.json").unlink()
            with self.assertRaises(SanitizerError):
                check_fixture_integrity(self.cfg, d)


@unittest.skipUnless(os.path.isfile(FROZEN_CONFIG), "freeze not done yet")
class FixtureIntegrityAfterFreeze(unittest.TestCase):
    def test_heldout_fixture_matches_summary_and_is_self_consistent(self):
        summary = json.loads((FIX / "fixture_summary.json").read_text(encoding="utf-8"))["heldout"]
        fx = load_fixture(FIX / "heldout.json")
        self.assertEqual(len(fx["examples"]), summary["examples"])
        counts = {t: 0 for t in ENTITY_PRIORITY}
        for ex in fx["examples"]:
            for g in ex["entities"]:
                counts[g["entity_type"]] += 1
            applied = [dict(g, score=1.0) for g in ex["entities"]]
            self.assertEqual(replace_spans(ex["text"], applied), ex["expected_sanitized"], ex["id"])
        self.assertEqual(counts, summary["gold_entities"])
        dev_ids = {e["id"] for e in load_fixture(FIX / "development.json")["examples"]}
        self.assertFalse(dev_ids & {e["id"] for e in fx["examples"]})
        self.assertTrue(any(not e["entities"] for e in fx["examples"]))  # includes benign-only/empty examples


@unittest.skipUnless(os.path.isfile(FROZEN_CONFIG), "freeze not done yet")
class SelectionReproducible(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_candidate()

    def test_rerunning_the_development_selection_reproduces_the_frozen_thresholds(self):
        from sanitizer.detectors import build_presidio
        fn, _mod, _an = build_presidio()
        dev = load_fixture(FIX / "development.json")
        sel = select_thresholds(dev, collect_raw(dev, fn))
        self.assertEqual(sel["best"]["thresholds"], load_frozen_config(FROZEN_CONFIG)["thresholds"])
        self.assertEqual(sel["grid"], json.loads(Path(FROZEN_CONFIG).read_text(encoding="utf-8"))["selection_grid"])


if __name__ == "__main__":
    unittest.main()
