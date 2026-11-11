"""CLI behavior: detector selection, summary flag, dependency/config failures, evaluation gating,
determinism, privacy of reports, and the explicit synthetic demo. No held-out data is read here
(the held-out gate is only tested with a path that does not exist)."""
import json
import os
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

from sanitizer.config import FIXTURE_DIR
from sanitizer.evaluation import load_fixture
from sanitizer.fixture import CANARY_CUSTOMER, CANARY_EMAIL, CANARY_PHONE, CANARY_SANITIZED, CANARY_TEXT

from .support import EMAIL, CUST, FROZEN_CONFIG, LogCapture, ROOT, TEXT, cli, require_candidate

PAYLOAD = {"request_id": "demo-001", "text": "Email [EMAIL_ADDRESS]; customer [CUSTOMER_ID]; quantity 24."}


class RunCommand(unittest.TestCase):
    def test_default_detector_and_output_are_unchanged(self):
        rc, out, err, m = cli(["run", "--request-id", "demo-001"], TEXT)
        self.assertEqual((rc, err), (0, ""))
        self.assertEqual(json.loads(out), PAYLOAD)
        self.assertEqual(out, json.dumps(PAYLOAD) + "\n")
        self.assertEqual(m.calls, [PAYLOAD])

    def test_explicit_baseline_detector_handles_all_three_entities(self):
        rc, out, err, m = cli(["run", "--detector", "baseline", "--request-id", "demo-001"], CANARY_TEXT)
        self.assertEqual((rc, err), (0, ""))
        self.assertEqual(json.loads(out), {"request_id": "demo-001", "text": CANARY_SANITIZED})
        self.assertEqual(m.calls, [{"request_id": "demo-001", "text": CANARY_SANITIZED}])

    def test_summary_flag_adds_counts_outside_the_provider_object(self):
        rc, out, err, m = cli(["run", "--summary", "--request-id", "demo-001"], CANARY_TEXT)
        obj = json.loads(out)
        self.assertEqual(set(obj), {"payload", "entity_counts"})
        self.assertEqual(obj["payload"], {"request_id": "demo-001", "text": CANARY_SANITIZED})
        self.assertEqual(obj["entity_counts"], {"EMAIL_ADDRESS": 1, "PHONE_NUMBER": 1, "CUSTOMER_ID": 1})
        self.assertEqual(m.calls, [obj["payload"]])  # the provider still received exactly {request_id, text}
        self.assertEqual(list(m.calls[0]), ["request_id", "text"])
        for v in (CANARY_EMAIL, CANARY_PHONE, CANARY_CUSTOMER):
            self.assertNotIn(v, out)

    def test_unknown_detector_choice_is_an_argument_error(self):
        rc, out, err, m = cli(["run", "--detector", "gpt", "--request-id", "demo-001"], TEXT)
        self.assertEqual((rc, out, err, m.calls), (2, "", "SANITIZER_INVALID_ARGUMENTS\n", []))


class CandidateUnavailable(unittest.TestCase):
    """A dependency/model/config failure is a fixed code and zero dispatch. No fallback to the baseline."""

    ARGV = ["run", "--detector", "presidio", "--request-id", "demo-001"]

    def assert_unavailable(self, rc, out, err, m, logs=None):
        self.assertEqual((rc, out, err), (2, "", "SANITIZER_DETECTOR_UNAVAILABLE\n"))
        self.assertEqual(m.calls, [])  # zero dispatch, and stdout empty: no baseline or raw-text fallback
        for canary in (EMAIL, CUST, "boom"):
            self.assertNotIn(canary, out + err + (logs.text if logs else ""))

    def test_missing_package_in_process(self):
        with mock.patch.dict(sys.modules, {"sanitizer.presidio_detector": None}), LogCapture() as logs:
            self.assert_unavailable(*cli(self.ARGV, TEXT), logs=logs)

    def test_initialization_failure_message_is_never_exposed(self):
        fake = types.ModuleType("sanitizer.presidio_detector")

        def build_analyzer():
            print(f"noisy stdout {EMAIL}")
            sys.stderr.write(f"noisy stderr {CUST}\n")
            raise RuntimeError(f"boom model path leaked {EMAIL} {CUST}")

        fake.build_analyzer = build_analyzer
        with mock.patch.dict(sys.modules, {"sanitizer.presidio_detector": fake}), LogCapture() as logs:
            self.assert_unavailable(*cli(self.ARGV, TEXT), logs=logs)
        self.assertEqual(logs.lines, ["ERROR sanitizer: rejected code=SANITIZER_DETECTOR_UNAVAILABLE"])

    def test_missing_package_in_a_real_process(self):
        # Blocks the import inside a subprocess instead of relying on the environment lacking Presidio.
        prog = ("import sys\nsys.modules['presidio_analyzer'] = None\nfrom sanitizer.cli import main\n"
                "sys.stdout.reconfigure(newline='\\n'); sys.stderr.reconfigure(newline='\\n')\n"
                "sys.exit(main(['run', '--detector', 'presidio', '--request-id', 'demo-001']))\n")
        p = subprocess.run([sys.executable, "-c", prog], input=TEXT.encode(), capture_output=True, cwd=ROOT)
        self.assertEqual(p.returncode, 2)
        self.assertEqual(p.stdout, b"")
        self.assertEqual(p.stderr, b"SANITIZER_DETECTOR_UNAVAILABLE\n")

    def test_missing_invalid_or_mismatched_config_is_a_fixed_code(self):
        with tempfile.TemporaryDirectory() as d:
            cases = {"missing": os.path.join(d, "nope.json")}
            for name, content in (("not json", "{"), ("wrong version", json.dumps({"config_version": 9})),
                                  ("no thresholds", json.dumps({"config_version": 1, "detector": "presidio",
                                                                "development_sha256": "a", "heldout_sha256": "b"})),
                                  ("bad threshold", json.dumps({"config_version": 1, "detector": "presidio",
                                                                "development_sha256": "a", "heldout_sha256": "b",
                                                                "thresholds": {"EMAIL_ADDRESS": 2, "PHONE_NUMBER": 0,
                                                                               "CUSTOMER_ID": 0}}))):
                p = os.path.join(d, name.replace(" ", "_") + ".json")
                Path(p).write_text(content, encoding="utf-8")
                cases[name] = p
            for name, path in cases.items():
                with self.subTest(name):
                    rc, out, err, m = cli(self.ARGV + ["--config", path], TEXT)
                    self.assertEqual((rc, out, err, m.calls), (2, "", "SANITIZER_INVALID_CONFIG\n", []))


class EvaluationCommands(unittest.TestCase):
    def test_heldout_requires_the_frozen_config(self):
        with tempfile.TemporaryDirectory() as d:
            for det in ("baseline", "presidio"):
                with self.subTest(det):
                    rc, out, err, _ = cli(["evaluate", "--detector", det, "--split", "heldout",
                                           "--config", os.path.join(d, "missing.json"), "--out", os.path.join(d, "r.json")])
                    self.assertEqual((rc, out, err), (2, "", "SANITIZER_FROZEN_CONFIG_REQUIRED\n"))
                    self.assertFalse(os.path.exists(os.path.join(d, "r.json")))

    def test_debug_thresholds_are_development_only(self):
        rc, out, err, _ = cli(["evaluate", "--detector", "presidio", "--split", "heldout", "--debug-thresholds", "0,0,0"])
        self.assertEqual((rc, out, err), (2, "", "SANITIZER_INVALID_ARGUMENTS\n"))

    def test_select_thresholds_refuses_to_overwrite_a_freeze(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "frozen.json")
            Path(p).write_text("{}", encoding="utf-8")
            rc, out, err, _ = cli(["select-thresholds", "--out", p])
            self.assertEqual((rc, out, err), (2, "", "SANITIZER_INVALID_CONFIG\n"))
            self.assertEqual(Path(p).read_text(encoding="utf-8"), "{}")

    def test_baseline_development_report_is_deterministic_and_privacy_safe(self):
        with tempfile.TemporaryDirectory() as d:
            outs = []
            for i in range(2):
                p = os.path.join(d, f"r{i}.json")
                rc, stdout, err, _ = cli(["evaluate", "--detector", "baseline", "--split", "development", "--out", p])
                self.assertEqual((rc, err), (0, ""))
                outs.append((Path(p).read_bytes(), stdout))
        self.assertEqual(outs[0], outs[1])
        report_text = outs[0][0].decode("utf-8")
        rep = json.loads(report_text)
        self.assertEqual(rep["metrics"]["micro"]["tp"], 16)
        # no raw values, texts or sanitized outputs in the report or the console summary
        for ex in load_fixture(FIXTURE_DIR / "development.json")["examples"]:
            for g in ex["entities"]:
                self.assertNotIn(ex["text"][g["start"]:g["end"]], report_text + outs[0][1])
            if len(ex["text"]) > 12:
                self.assertNotIn(ex["text"], report_text)
            if len(ex["expected_sanitized"]) > 12:
                self.assertNotIn(ex["expected_sanitized"], report_text)
        for key in ("text", "sanitized", "value"):
            self.assertNotIn(f'"{key}"', report_text)

    def test_report_separates_accuracy_from_provider_boundary(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "r.json")
            cli(["evaluate", "--detector", "baseline", "--split", "development", "--out", p])
            rep = json.loads(Path(p).read_text(encoding="utf-8"))
        self.assertIn("metrics", rep)
        self.assertIn("provider_boundary", rep)
        self.assertEqual(rep["provider_boundary"]["examples_dispatched"], 10)
        self.assertEqual(rep["provider_boundary"]["payload_equals_actual_sanitized"], 10)
        self.assertEqual(rep["provider_boundary"]["provider_calls_total"], 10)
        self.assertEqual(rep["preservation"]["no_gold_examples_preserved"], rep["preservation"]["examples_with_no_gold"])
        self.assertTrue(all(e["reconstruction_from_applied_spans_equals_output"] for e in rep["examples"]))


class DemoCommand(unittest.TestCase):
    def test_baseline_demo_shows_labelled_synthetic_inspection(self):
        rc, out, err, m = cli(["demo", "--detector", "baseline"])
        self.assertEqual((rc, err), (0, ""))
        self.assertIn("SYNTHETIC INSPECTION", out)
        self.assertIn("no user text is accepted", out.lower())
        self.assertIn(f"payload captured by RecordingMock: {{'request_id': 'demo-001', 'text': {CANARY_SANITIZED!r}}}", out)
        for needle in ("benign preservation", "Unicode offsets", "repeated value", "CRLF and tab",
                       "detector failure", "fixed code: SANITIZER_DETECTOR_ERROR; provider calls = 0",
                       "equals fixture oracle: True"):
            self.assertIn(needle, out)
        self.assertEqual(m.calls, [])  # the demo's own mocks are internal; the injected provider is untouched

    def test_demo_has_no_way_to_supply_text_or_pick_a_real_provider(self):
        rc, out, err, _ = cli(["demo", "--text", "hello"])
        self.assertEqual((rc, out, err), (2, "", "SANITIZER_INVALID_ARGUMENTS\n"))
        rc, out, err, _ = cli(["demo", "--provider", "real"])
        self.assertEqual((rc, out, err), (2, "", "SANITIZER_INVALID_ARGUMENTS\n"))

    def test_presidio_demo_without_dependency_is_a_fixed_code(self):
        with mock.patch.dict(sys.modules, {"sanitizer.presidio_detector": None}):
            rc, out, err, _ = cli(["demo", "--detector", "presidio"])
        self.assertEqual((rc, out, err), (2, "", "SANITIZER_DETECTOR_UNAVAILABLE\n"))


class CandidateCli(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_candidate()

    def test_presidio_run_with_the_frozen_config(self):
        rc, out, err, m = cli(["run", "--detector", "presidio", "--summary", "--request-id", "demo-001"], CANARY_TEXT)
        self.assertEqual((rc, err), (0, ""))
        obj = json.loads(out)
        self.assertEqual(obj["payload"], {"request_id": "demo-001", "text": CANARY_SANITIZED})
        self.assertEqual(obj["entity_counts"], {"EMAIL_ADDRESS": 1, "PHONE_NUMBER": 1, "CUSTOMER_ID": 1})
        self.assertEqual(m.calls, [obj["payload"]])

    def test_presidio_run_prints_nothing_extra_to_the_terminal(self):
        p = subprocess.run([sys.executable, "-m", "sanitizer", "run", "--detector", "presidio", "--request-id", "demo-001"],
                           input=TEXT.encode(), capture_output=True, cwd=ROOT,
                           env=dict(os.environ, TLDEXTRACT_CACHE=tempfile.gettempdir()))
        self.assertEqual((p.returncode, p.stderr), (0, b""))
        self.assertEqual(json.loads(p.stdout), PAYLOAD)

    def test_candidate_demo_runs_and_is_labelled(self):
        rc, out, err, _ = cli(["demo", "--detector", "presidio"])
        self.assertEqual((rc, err), (0, ""))
        self.assertIn("SYNTHETIC INSPECTION", out)
        self.assertIn("detector: presidio", out)

    def test_candidate_development_evaluation_is_deterministic(self):
        with tempfile.TemporaryDirectory() as d:
            blobs = []
            for i in range(2):
                p = os.path.join(d, f"r{i}.json")
                rc, _, err, _ = cli(["evaluate", "--detector", "presidio", "--split", "development", "--out", p])
                self.assertEqual((rc, err), (0, ""))
                blobs.append(Path(p).read_bytes())
        self.assertEqual(blobs[0], blobs[1])


if __name__ == "__main__":
    unittest.main()
