"""Candidate (Presidio) configuration tests. They need presidio-analyzer and en_core_web_sm.

Without them these tests SKIP locally; with REQUIRE_CANDIDATE_TESTS=1 (the CI candidate job) a missing
dependency is a FAILURE. Passing results here are not accuracy claims."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from sanitizer import RecordingMock, dispatch, sanitize
from sanitizer.config import load_frozen_config
from sanitizer.core import ENTITY_PRIORITY
from sanitizer.fixture import CANARY_CUSTOMER, CANARY_EMAIL, DEV_001

from .support import FROZEN_CONFIG, HAVE_PRESIDIO, LogCapture, ROOT, cli, require_candidate

TEXT = DEV_001["text"]
SANITIZED = "Email [EMAIL_ADDRESS]; customer [CUSTOMER_ID]; quantity 24."
PAYLOAD = {"request_id": "demo-001", "text": SANITIZED}

if HAVE_PRESIDIO:
    from sanitizer.presidio_detector import build_analyzer, make_detector, recognizer_settings


class PresidioConfiguration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_candidate()
        cls.analyzer = build_analyzer()
        cls.detector = staticmethod(make_detector(cls.analyzer))
        cls.thresholds = load_frozen_config(FROZEN_CONFIG)["thresholds"]

    def test_only_selected_recognizers_loaded(self):
        loaded = {(r.name, type(r).__name__, tuple(r.supported_entities)) for r in self.analyzer.registry.recognizers}
        self.assertEqual(loaded, {
            ("OfflineEmailRecognizer", "OfflineEmailRecognizer", ("EMAIL_ADDRESS",)),
            ("PhoneRecognizer", "PhoneRecognizer", ("PHONE_NUMBER",)),
            ("CustomerIdRecognizer", "PatternRecognizer", ("CUSTOMER_ID",)),
        })
        self.assertEqual(sorted(self.analyzer.get_supported_entities("en")), sorted(ENTITY_PRIORITY))

    def test_phone_recognizer_is_us_only_and_no_ner_recognizer_registered(self):
        settings = recognizer_settings(self.analyzer)
        phone = [r for r in settings["recognizers"] if r["class"] == "PhoneRecognizer"][0]
        self.assertEqual(phone["supported_regions"], ["US"])
        self.assertFalse(settings["ner_recognizer_registered"])
        self.assertEqual(settings["spacy_model"], "en_core_web_sm")
        self.assertEqual(settings["nlp_engine"], "SpacyNlpEngine")

    def test_frozen_config_records_the_live_recognizer_settings(self):
        cfg = json.loads(Path(FROZEN_CONFIG).read_text(encoding="utf-8"))
        self.assertEqual(cfg["recognizer_settings"], json.loads(json.dumps(recognizer_settings(self.analyzer))))

    def test_engine_candidates_for_dev_001(self):
        got = sorted((s["entity_type"], s["start"], s["end"]) for s in self.detector(TEXT))
        want = sorted((e["entity_type"], e["start"], e["end"]) for e in DEV_001["entities"])
        self.assertEqual(got, want)

    def test_sanitized_text_and_payload_exact(self):
        self.assertEqual(sanitize(TEXT, self.detector, thresholds=self.thresholds), SANITIZED)
        mock = RecordingMock()
        dispatch("demo-001", TEXT, mock, self.detector, thresholds=self.thresholds)
        self.assertEqual(mock.calls, [PAYLOAD])
        self.assertEqual(list(mock.calls[0]), ["request_id", "text"])
        for canary in (CANARY_EMAIL, CANARY_CUSTOMER):
            self.assertNotIn(canary, repr(mock.calls[0]))

    def test_customer_id_rule_is_case_sensitive_with_token_boundaries(self):
        for t in ("cust-004271", "Cust-004271", "CUST-00427", "CUST-0042711", "xCUST-004271", "CUST-004271_x"):
            with self.subTest(t=t):
                self.assertEqual([s for s in self.detector(t) if s["entity_type"] == "CUSTOMER_ID"], [])
        self.assertEqual([(s["start"], s["end"]) for s in self.detector("(CUST-004271),")
                          if s["entity_type"] == "CUSTOMER_ID"], [(1, 12)])

    def test_unsupported_phone_format_is_gated_out_of_the_applied_spans(self):
        text = "Unsupported phone 202-555-0147 here"
        raw = self.detector(text)
        self.assertTrue(any(s["entity_type"] == "PHONE_NUMBER" for s in raw))  # Presidio does see it
        self.assertEqual(sanitize(text, self.detector, thresholds=self.thresholds), text)  # the shared gate drops it

    def test_no_network_and_no_cache_writes_in_a_fresh_process(self):
        # Fresh process: tldextract memoizes after first use, so in-process checks are order-dependent.
        # TLDEXTRACT_CACHE points at a temp dir so even a regression cannot write to the user's home.
        prog = """
import json, socket
attempts = []
def gai(h, *a, **k):
    attempts.append(str(h))
    raise OSError('blocked')
def conn(self, addr):
    attempts.append(str(addr))
    raise OSError('blocked')
socket.getaddrinfo = gai
socket.socket.connect = conn
from sanitizer.presidio_detector import build_analyzer, make_detector
d = make_detector(build_analyzer())
d('Email ava@example.com; customer CUST-004271; quantity 24.')
d('contact bob@example.org')
print(json.dumps(attempts))
"""
        with tempfile.TemporaryDirectory() as cache:
            env = dict(os.environ, TLDEXTRACT_CACHE=cache)
            p = subprocess.run([sys.executable, "-c", prog], capture_output=True, text=True, cwd=ROOT, env=env)
            written = [f for _, _, fs in os.walk(cache) for f in fs]
        self.assertEqual(p.returncode, 0, p.stderr[-800:])
        self.assertEqual(json.loads(p.stdout.strip().splitlines()[-1]), [])
        self.assertEqual(written, [])

    def test_no_input_text_in_logs_at_root_debug(self):
        with LogCapture() as logs:
            det = make_detector(build_analyzer())  # build_analyzer sets presidio-analyzer to INFO
            dispatch("demo-001", TEXT, RecordingMock(), det, thresholds=self.thresholds)
        self.assertTrue(logs.lines)
        for needle in (CANARY_EMAIL, CANARY_CUSTOMER, "quantity", "customer "):
            self.assertNotIn(needle, logs.text)

    def test_stock_email_probe_is_not_a_cli_route(self):
        rc, out, err, _ = cli(["run", "--request-id", "demo-001", "--detector", "presidio", "--stock-email"], TEXT)
        self.assertEqual((rc, out, err), (2, "", "SANITIZER_INVALID_ARGUMENTS\n"))
        src = (Path(ROOT) / "sanitizer" / "cli.py").read_text(encoding="utf-8")
        self.assertNotIn("stock", src.lower())


if __name__ == "__main__":
    unittest.main()
