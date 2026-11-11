"""Provider-boundary and logging tests for BOTH detectors.

These check what reaches the provider (a RecordingMock) and what reaches the logs. They are separate
from accuracy: a detector miss in evaluation is an accuracy/coverage failure, not proof that dispatch was
bypassed, and nothing here asserts universal PII removal.

The KNOWN_CORRECT lists below were derived from DEVELOPMENT results only."""
import unittest

from sanitizer import RecordingMock, SanitizerError
from sanitizer.config import FIXTURE_DIR
from sanitizer.core import run_pipeline
from sanitizer.detectors import load_detector
from sanitizer.evaluation import load_fixture
from sanitizer.fixture import CANARY_CUSTOMER, CANARY_EMAIL, CANARY_PHONE, CANARY_SANITIZED, CANARY_TEXT

from .support import FROZEN_CONFIG, LOG_LINE_OK, LogCapture, require_candidate

DEV = {e["id"]: e for e in load_fixture(FIXTURE_DIR / "development.json")["examples"]}
# Development examples whose actual output equals the fixture oracle, per detector (dev results only).
KNOWN_CORRECT = {
    "baseline": sorted(DEV),
    "presidio": sorted(k for k in DEV if k != "dev-008"),  # dev-008: Presidio rejects the .invalid suffix (documented miss)
}
DOCUMENTED_MISS = {"baseline": [], "presidio": ["dev-008"]}


class _Boundary:
    name = None

    @classmethod
    def setUpClass(cls):
        if cls.name == "presidio":
            require_candidate()
        cls.det = load_detector(cls.name, FROZEN_CONFIG)

    def run_one(self, text, detector=None, request_id="demo-001"):
        mock = RecordingMock()
        payload, res = run_pipeline(request_id, text, mock, detector or self.det.fn, thresholds=self.det.thresholds)
        return mock, payload, res

    def test_all_three_entity_canary_payload_is_exactly_the_sanitized_text(self):
        mock, payload, res = self.run_one(CANARY_TEXT)
        self.assertEqual(mock.calls, [{"request_id": "demo-001", "text": CANARY_SANITIZED}])
        self.assertIs(mock.calls[0], payload)
        self.assertEqual(list(mock.calls[0]), ["request_id", "text"])
        for canary in (CANARY_EMAIL, CANARY_PHONE, CANARY_CUSTOMER):
            self.assertNotIn(canary, repr(mock.calls[0]))
        self.assertEqual(res.entity_counts(), {"EMAIL_ADDRESS": 1, "PHONE_NUMBER": 1, "CUSTOMER_ID": 1})

    def test_known_correct_development_cases_have_exact_payload(self):
        for ex_id in KNOWN_CORRECT[self.name]:
            with self.subTest(ex_id):
                mock, payload, _ = self.run_one(DEV[ex_id]["text"])
                self.assertEqual(mock.calls, [{"request_id": "demo-001", "text": DEV[ex_id]["expected_sanitized"]}])

    def test_every_development_payload_equals_the_actual_sanitized_text_even_on_misses(self):
        for ex_id, ex in DEV.items():
            with self.subTest(ex_id):
                mock, payload, res = self.run_one(ex["text"])
                self.assertEqual(mock.calls, [{"request_id": "demo-001", "text": res.sanitized}])

    def test_documented_misses_are_accuracy_failures_not_boundary_failures(self):
        for ex_id in DOCUMENTED_MISS[self.name]:
            with self.subTest(ex_id):
                mock, payload, res = self.run_one(DEV[ex_id]["text"])
                self.assertNotEqual(payload["text"], DEV[ex_id]["expected_sanitized"])  # accuracy failure
                self.assertEqual(mock.calls, [payload])                               # boundary still holds

    def test_detector_failure_and_malformed_output_give_zero_provider_calls(self):
        real = self.det.fn

        def raises(text):
            real(text)
            raise RuntimeError(f"boom {CANARY_EMAIL} {CANARY_CUSTOMER} {CANARY_PHONE}")

        def malformed(text):
            return real(text) + [{"entity_type": "EMAIL_ADDRESS", "start": True, "end": 3, "score": 1.0}]

        for fn, code in ((raises, "SANITIZER_DETECTOR_ERROR"), (malformed, "SANITIZER_INVALID_DETECTOR_OUTPUT")):
            with self.subTest(code):
                mock = RecordingMock()
                with LogCapture() as logs, self.assertRaises(SanitizerError) as cm:
                    run_pipeline("demo-001", CANARY_TEXT, mock, fn, thresholds=self.det.thresholds)
                self.assertEqual(str(cm.exception), code)
                self.assertEqual(mock.calls, [])
                for canary in (CANARY_EMAIL, CANARY_PHONE, CANARY_CUSTOMER, "boom"):
                    self.assertNotIn(canary, logs.text)

    def test_provider_exception_is_distinct_from_detector_failure(self):
        calls = []

        def provider(payload):
            calls.append(payload)
            raise RuntimeError(f"provider boom {CANARY_EMAIL}")

        with LogCapture() as logs, self.assertRaises(SanitizerError) as cm:
            run_pipeline("demo-001", CANARY_TEXT, provider, self.det.fn, thresholds=self.det.thresholds)
        self.assertEqual(str(cm.exception), "SANITIZER_INTERNAL_ERROR")
        self.assertEqual(len(calls), 1)  # the provider HAD been invoked (with the sanitized payload)
        self.assertEqual(calls[0]["text"], CANARY_SANITIZED)
        self.assertNotIn(CANARY_EMAIL, logs.text)

    def test_logs_at_root_debug_contain_only_approved_metadata(self):
        with LogCapture() as logs:
            for ex in DEV.values():
                self.run_one(ex["text"])
            self.run_one(CANARY_TEXT)
        self.assertTrue(logs.lines)
        for rec in logs.handler.records:
            if rec.name == "sanitizer":
                self.assertRegex(f"{rec.levelname} {rec.name} {rec.getMessage()}", LOG_LINE_OK)
            self.assertIsNone(rec.exc_info)
        blob = logs.text
        for needle in (CANARY_EMAIL, CANARY_PHONE, CANARY_CUSTOMER, "quantity", "Café", "training.invalid",
                       "team@example.com", "maya+lab", "555-0147"):
            self.assertNotIn(needle, blob)


class BaselineBoundary(_Boundary, unittest.TestCase):
    name = "baseline"


class PresidioBoundary(_Boundary, unittest.TestCase):
    name = "presidio"


if __name__ == "__main__":
    unittest.main()
