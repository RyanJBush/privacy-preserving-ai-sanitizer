import io
import json
import logging
import os
import re
import subprocess
import sys
import unittest
from unittest import mock

from sanitizer import MAX_INPUT_CHARS, RecordingMock, SanitizerError, baseline_detector, dispatch, sanitize
from sanitizer.cli import main
from sanitizer.core import MAX_INPUT_BYTES, resolve_spans
from sanitizer.fixture import DEV_001

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMAIL = "ava@example.com"
CUST = "CUST-004271"
TEXT = "Email ava@example.com; customer CUST-004271; quantity 24."
SANITIZED = "Email [EMAIL_ADDRESS]; customer [CUSTOMER_ID]; quantity 24."
PAYLOAD = {"request_id": "demo-001", "text": SANITIZED}


def span(t, a, b, score=1.0):
    return {"entity_type": t, "start": a, "end": b, "score": score}


def leaky_detector(text):
    raise RuntimeError(f"boom {EMAIL} {CUST} {text}")


class _ListHandler(logging.Handler):
    def __init__(self):
        super().__init__(logging.DEBUG)
        self.records = []

    def emit(self, record):
        self.records.append(record)


class LogCapture:
    """Handler on the ROOT logger at DEBUG: sees every record the app emits."""

    def __enter__(self):
        self.handler = _ListHandler()
        self.root = logging.getLogger()
        self.old_level = self.root.level
        self.root.addHandler(self.handler)
        self.root.setLevel(logging.DEBUG)
        return self

    def __exit__(self, *exc):
        self.root.removeHandler(self.handler)
        self.root.setLevel(self.old_level)

    @property
    def lines(self):
        return [f"{r.levelname} {r.name} {r.getMessage()}" for r in self.handler.records]

    @property
    def text(self):
        return "\n".join(self.lines)


# Approved log content: output length on success, or a fixed code. Never request_id or text.
LOG_LINE_OK = re.compile(
    r"(INFO|WARNING|ERROR) sanitizer "
    r"(dispatched chars=[0-9]+|rejected code=SANITIZER_[A-Z_]+)"
)


def run_cli(argv, data, detector=baseline_detector, provider=None):
    """data: bytes, or str (UTF-8 encoded). stdin is a binary stream, as in the real CLI."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    out, err = io.StringIO(), io.StringIO()
    provider = provider if provider is not None else RecordingMock()
    rc = main(argv, io.BytesIO(data), out, err, detector, provider)
    return rc, out.getvalue(), err.getvalue(), provider


class FailingProvider:
    """Provider whose exception message contains both canaries; counts invocations."""

    def __init__(self):
        self.calls = 0

    def __call__(self, payload):
        self.calls += 1
        raise RuntimeError(f"provider boom {EMAIL} {CUST}")


class Dev001(unittest.TestCase):
    def test_fixture_matches_contract_and_slices(self):
        self.assertEqual(DEV_001["text"], TEXT)
        self.assertEqual(TEXT[6:21], EMAIL)
        self.assertEqual(TEXT[32:43], CUST)

    def test_detected_spans_match_expected(self):
        got = sorted((s["entity_type"], s["start"], s["end"]) for s in baseline_detector(TEXT))
        want = sorted((e["entity_type"], e["start"], e["end"]) for e in DEV_001["entities"])
        self.assertEqual(got, want)
        self.assertTrue(all(s["score"] == 1.0 for s in baseline_detector(TEXT)))

    def test_sanitized_text_exact(self):
        self.assertEqual(sanitize(TEXT), SANITIZED)

    def test_mock_payload_exact(self):
        mock = RecordingMock()
        dispatch("demo-001", TEXT, mock)
        self.assertEqual(len(mock.calls), 1)
        self.assertIs(type(mock.calls[0]), dict)
        self.assertEqual(mock.calls[0], PAYLOAD)
        self.assertEqual(list(mock.calls[0]), ["request_id", "text"])
        blob = json.dumps(mock.calls[0])
        self.assertNotIn(EMAIL, blob)
        self.assertNotIn(CUST, blob)


class Preservation(unittest.TestCase):
    def test_benign_numbers_and_punctuation_untouched(self):
        for t in ("quantity 24.", "Total: 24, ok; (24) -- 24!", "CUST-12345 and 1234567", "a@b", "24"):
            with self.subTest(t=t):
                self.assertEqual(sanitize(t), t)

    def test_surrounding_punctuation_and_whitespace_preserved(self):
        self.assertEqual(sanitize("(CUST-004271),  x\n\tava@example.com."),
                         "([CUSTOMER_ID]),  x\n\t[EMAIL_ADDRESS].")

    def test_customer_id_boundaries(self):
        for t in ("xCUST-004271", "CUST-0042711", "CUST-00427", "cust-004271",
                  "CUST_004271", "_CUST-004271", "CUST-004271_x", "ACUST-004271", "CUST-00427١"):
            with self.subTest(t=t):
                self.assertEqual(sanitize(t), t)
        self.assertEqual(sanitize("CUST-004271-x"), "[CUSTOMER_ID]-x")

    def test_no_unicode_normalization_and_char_offsets(self):
        t = "\U0001F600 ava@example.com"  # non-BMP char counts as one index
        self.assertEqual(baseline_detector(t)[0]["start"], 2)
        self.assertEqual(sanitize(t), "\U0001F600 [EMAIL_ADDRESS]")
        self.assertEqual(sanitize("é CUST-004271"), "é [CUSTOMER_ID]")


class EmptyInput(unittest.TestCase):
    def test_empty_is_valid(self):
        self.assertEqual(sanitize(""), "")
        mock = RecordingMock()
        dispatch("req-001", "", mock)
        self.assertEqual(mock.calls, [{"request_id": "req-001", "text": ""}])

    def test_empty_via_cli(self):
        rc, out, err, mock = run_cli(["run", "--request-id", "req-001"], "")
        self.assertEqual((rc, err), (0, ""))
        self.assertEqual(json.loads(out), {"request_id": "req-001", "text": ""})
        self.assertEqual(len(mock.calls), 1)


class DetectorFailure(unittest.TestCase):
    def test_exception_stops_dispatch_without_leaking(self):
        mock = RecordingMock()
        with self.assertRaises(SanitizerError) as cm:
            dispatch("demo-001", TEXT, mock, leaky_detector)
        self.assertEqual(str(cm.exception), "SANITIZER_DETECTOR_ERROR")
        self.assertIsNone(cm.exception.__cause__)
        self.assertTrue(cm.exception.__suppress_context__)
        self.assertEqual(mock.calls, [])

    def test_cli_contract(self):
        with LogCapture() as logs:
            rc, out, err, mock = run_cli(["run", "--request-id", "demo-001"], TEXT, leaky_detector)
        self.assertEqual(rc, 2)
        self.assertEqual(out, "")
        self.assertEqual(err, "SANITIZER_DETECTOR_ERROR\n")
        self.assertEqual(mock.calls, [])
        for canary in (EMAIL, CUST):
            for stream in (out, err, logs.text):
                self.assertNotIn(canary, stream)
        self.assertNotIn("Traceback", err + logs.text)
        self.assertNotIn("boom", err + logs.text)


class InvalidDetectorOutput(unittest.TestCase):
    BAD = {
        "bool start": [span("EMAIL_ADDRESS", True, 5)],
        "bool end": [span("EMAIL_ADDRESS", 0, True)],
        "float start": [span("EMAIL_ADDRESS", 0.0, 5)],
        "str start": [span("EMAIL_ADDRESS", "0", 5)],
        "negative start": [span("EMAIL_ADDRESS", -1, 5)],
        "start == end": [span("EMAIL_ADDRESS", 3, 3)],
        "start > end": [span("EMAIL_ADDRESS", 5, 3)],
        "end > len": [span("EMAIL_ADDRESS", 0, len(TEXT) + 1)],
        "unknown entity": [span("PERSON", 0, 5)],
        "non-str entity": [span(["EMAIL_ADDRESS"], 0, 5)],
        "bool score": [span("EMAIL_ADDRESS", 0, 5, True)],
        "NaN score": [span("EMAIL_ADDRESS", 0, 5, float("nan"))],
        "inf score": [span("EMAIL_ADDRESS", 0, 5, float("inf"))],
        "score > 1": [span("EMAIL_ADDRESS", 0, 5, 1.5)],
        "score < 0": [span("EMAIL_ADDRESS", 0, 5, -0.1)],
        "str score": [span("EMAIL_ADDRESS", 0, 5, "1.0")],
        "huge positive int score": [span("EMAIL_ADDRESS", 0, 5, 10**400)],
        "huge negative int score": [span("EMAIL_ADDRESS", 0, 5, -(10**400))],
        "int score 2": [span("EMAIL_ADDRESS", 0, 5, 2)],
        "int score -1": [span("EMAIL_ADDRESS", 0, 5, -1)],
        "huge int offsets": [span("EMAIL_ADDRESS", 0, 10**400)],
        "missing key": [{"entity_type": "EMAIL_ADDRESS", "start": 0, "end": 5}],
        "extra key": [dict(span("EMAIL_ADDRESS", 0, 5), text=EMAIL)],
        "non-mapping item": [("EMAIL_ADDRESS", 0, 5, 1.0)],
        "None result": None,
        "string result": "EMAIL_ADDRESS",
        "dict result": span("EMAIL_ADDRESS", 0, 5),
        "one bad among good": [span("EMAIL_ADDRESS", 6, 21), span("CUSTOMER_ID", 32, 99)],
    }

    def test_each_malformed_output_stops_dispatch(self):
        for name, bad in self.BAD.items():
            with self.subTest(name):
                mock = RecordingMock()
                with self.assertRaises(SanitizerError) as cm:
                    dispatch("demo-001", TEXT, mock, lambda t, b=bad: b)
                self.assertEqual(str(cm.exception), "SANITIZER_INVALID_DETECTOR_OUTPUT")
                self.assertEqual(mock.calls, [])

    def test_cli_contract(self):
        bad = self.BAD["extra key"]  # extra key carries a canary
        with LogCapture() as logs:
            rc, out, err, mock = run_cli(["run", "--request-id", "demo-001"], TEXT, lambda t: bad)
        self.assertEqual((rc, out, err), (2, "", "SANITIZER_INVALID_DETECTOR_OUTPUT\n"))
        self.assertEqual(mock.calls, [])
        for canary in (EMAIL, CUST):
            self.assertNotIn(canary, logs.text)

    def test_huge_integer_scores_via_cli_not_internal_error(self):
        for name in ("huge positive int score", "huge negative int score", "huge int offsets"):
            with self.subTest(name):
                bad = self.BAD[name]
                with LogCapture() as logs:
                    rc, out, err, mock = run_cli(["run", "--request-id", "demo-001"], TEXT, lambda t, b=bad: b)
                self.assertEqual((rc, out, err), (2, "", "SANITIZER_INVALID_DETECTOR_OUTPUT\n"))
                self.assertEqual(mock.calls, [])
                self.assertEqual(logs.lines, ["ERROR sanitizer rejected code=SANITIZER_INVALID_DETECTOR_OUTPUT"])

    def test_validator_itself_rejects_huge_ints_without_overflow(self):
        # sanitize() has a defensive catch-all; this pins the validator's own behavior.
        from sanitizer.core import _is_score, validate_spans
        for score in (10**400, -(10**400), 2, -1, True, False, float("nan"), "1"):
            with self.subTest(score=score):
                self.assertIs(_is_score(score), False)
                with self.assertRaises(SanitizerError):
                    validate_spans([span("EMAIL_ADDRESS", 0, 5, score)], 20)

    def test_boundary_scores_still_accepted(self):
        for score in (0, 1, 0.0, 1.0, 0.5):
            with self.subTest(score=score):
                self.assertEqual(sanitize("abc", lambda t, s=score: [span("EMAIL_ADDRESS", 0, 3, s)]),
                                 "[EMAIL_ADDRESS]")

    def test_hostile_span_object_is_invalid_output_not_crash(self):
        class Hostile(dict):
            def keys(self):
                raise RuntimeError(f"boom {EMAIL}")
            def __iter__(self):
                raise RuntimeError(f"boom {CUST}")
        with self.assertRaises(SanitizerError) as cm:
            sanitize(TEXT, lambda t: [Hostile(span("EMAIL_ADDRESS", 0, 5))])
        self.assertEqual(str(cm.exception), "SANITIZER_INVALID_DETECTOR_OUTPUT")


class RequestIdBoundary(unittest.TestCase):
    GOOD = ("demo-001", "req-001", "demo-123", "req-123456789012", "demo-000000000000")
    BAD = {
        "email canary": EMAIL,
        "customer canary": CUST,
        "trailing newline": "demo-001\n",
        "embedded newline": "demo-001\nERROR sanitizer rejected code=FAKE",
        "leading newline": "\ndemo-001",
        "empty": "",
        "too few digits": "demo-01",
        "too many digits": "demo-1234567890123",
        "wrong prefix": "id-001",
        "uppercase prefix": "DEMO-001",
        "no hyphen": "demo001",
        "space": "demo- 001",
        "non-ASCII digits": "demo-١٢٣",
        "suffix": "demo-001x",
        "prefix text": "xdemo-001",
        "nul byte": "demo-001\x00",
        "None": None,
        "int": 1,
        "bytes": b"demo-001",
        "bool": True,
        "list": ["demo-001"],
    }

    def test_valid_ids_accepted_and_passed_through(self):
        for rid in self.GOOD:
            with self.subTest(rid):
                m = RecordingMock()
                dispatch(rid, TEXT, m)
                self.assertEqual(m.calls, [{"request_id": rid, "text": SANITIZED}])

    def test_str_subclass_rejected(self):
        class S(str):
            pass
        with self.assertRaises(SanitizerError):
            dispatch(S("demo-001"), TEXT, RecordingMock())

    def test_invalid_ids_rejected_before_detector_and_provider(self):
        for name, rid in self.BAD.items():
            with self.subTest(name):
                seen, m = [], RecordingMock()
                with LogCapture() as logs:
                    with self.assertRaises(SanitizerError) as cm:
                        dispatch(rid, TEXT, m, lambda t: seen.append(t) or [])
                self.assertEqual(str(cm.exception), "SANITIZER_INVALID_REQUEST_ID")
                self.assertIsNone(cm.exception.__cause__)
                self.assertEqual(seen, [])
                self.assertEqual(m.calls, [])
                self.assertEqual(logs.lines, ["ERROR sanitizer rejected code=SANITIZER_INVALID_REQUEST_ID"])

    def test_cli_in_process(self):
        for name, rid in self.BAD.items():
            if not isinstance(rid, str) or "\x00" in rid:
                continue  # argv cannot carry non-str or NUL
            with self.subTest(name):
                with LogCapture() as logs:
                    rc, out, err, m = run_cli(["run", "--request-id", rid], TEXT)
                self.assertEqual((rc, out, err), (2, "", "SANITIZER_INVALID_REQUEST_ID\n"))
                self.assertEqual(m.calls, [])
                for canary in (EMAIL, CUST, "FAKE"):
                    self.assertNotIn(canary, logs.text + out + err)

    def test_cli_real_process(self):
        for rid in (EMAIL, CUST, "demo-001\nERROR forged", "demo-001\n"):
            with self.subTest(repr(rid)):
                p = subprocess.run([sys.executable, "-m", "sanitizer", "run", "--request-id", rid],
                                   input=TEXT.encode(), capture_output=True, cwd=ROOT)
                self.assertEqual(p.returncode, 2)
                self.assertEqual(p.stdout, b"")
                self.assertEqual(p.stderr, b"SANITIZER_INVALID_REQUEST_ID\n")

    def test_request_id_checked_before_stdin_is_decoded(self):
        rc, out, err, _ = run_cli(["run", "--request-id", EMAIL], b"\xff")
        self.assertEqual(err, "SANITIZER_INVALID_REQUEST_ID\n")

    def test_canary_ids_never_reach_provider_or_logs(self):
        for rid in (EMAIL, CUST):
            m = RecordingMock()
            with LogCapture() as logs, self.assertRaises(SanitizerError):
                dispatch(rid, TEXT, m)
            self.assertEqual(m.calls, [])
            self.assertNotIn(rid, logs.text)


class ArgumentErrors(unittest.TestCase):
    PREFIX = [sys.executable, "-m", "sanitizer"]

    def proc(self, args, data=b""):
        return subprocess.run(self.PREFIX + args, input=data, capture_output=True, cwd=ROOT)

    def test_parser_failures_are_fixed_code_and_never_echo_values(self):
        cases = {
            "unknown option with email": ["run", "--request-id", "demo-001", "--unknown", EMAIL],
            "unknown option with customer id": ["run", "--request-id", "demo-001", "--unknown=" + CUST],
            "missing --request-id": ["run"],
            "--request-id without value": ["run", "--request-id"],
            "no subcommand": [],
            "unknown subcommand email": [EMAIL],
            "unknown subcommand customer id": [CUST],
            "extra positional": ["run", "--request-id", "demo-001", EMAIL],
            "extra on inspect-fixture": ["inspect-fixture", "--extra", CUST],
            "duplicate-looking flag": ["run", "--request-id", "demo-001", "--request-id"],
            "top-level unknown": ["--nope", EMAIL],
        }
        for name, args in cases.items():
            with self.subTest(name):
                p = self.proc(args)
                self.assertEqual(p.returncode, 2)
                self.assertEqual(p.stdout, b"")
                self.assertEqual(p.stderr, b"SANITIZER_INVALID_ARGUMENTS\n")

    def test_in_process_parser_failure_logs_only_code(self):
        with LogCapture() as logs:
            rc, out, err, m = run_cli(["run", "--request-id", "demo-001", "--unknown", EMAIL], TEXT)
        self.assertEqual((rc, out, err), (2, "", "SANITIZER_INVALID_ARGUMENTS\n"))
        self.assertEqual(m.calls, [])
        self.assertEqual(logs.lines, ["ERROR sanitizer rejected code=SANITIZER_INVALID_ARGUMENTS"])

    def test_explicit_help_still_works(self):
        for args in (["--help"], ["-h"], ["run", "--help"], ["inspect-fixture", "-h"]):
            with self.subTest(args):
                p = self.proc(args)
                self.assertEqual(p.returncode, 0)
                self.assertIn(b"usage:", p.stdout)
                self.assertEqual(p.stderr, b"")
                self.assertNotIn(EMAIL.encode(), p.stdout)

    def test_valid_invocation_unaffected(self):
        p = self.proc(["run", "--request-id", "demo-001"], TEXT.encode())
        self.assertEqual((p.returncode, p.stderr), (0, b""))
        self.assertEqual(json.loads(p.stdout), PAYLOAD)


class OversizedInput(unittest.TestCase):
    def test_rejected_before_detection_and_dispatch(self):
        calls = []
        mock = RecordingMock()
        big = EMAIL + "x" * (MAX_INPUT_CHARS - len(EMAIL) + 1)
        self.assertEqual(len(big), MAX_INPUT_CHARS + 1)
        with self.assertRaises(SanitizerError) as cm:
            dispatch("req-001", big, mock, lambda t: calls.append(t) or [])
        self.assertEqual(str(cm.exception), "SANITIZER_INPUT_TOO_LARGE")
        self.assertEqual(calls, [])
        self.assertEqual(mock.calls, [])

    def test_limit_is_inclusive_and_counts_characters(self):
        self.assertEqual(sanitize("x" * MAX_INPUT_CHARS), "x" * MAX_INPUT_CHARS)
        self.assertEqual(sanitize("\U0001F600" * MAX_INPUT_CHARS), "\U0001F600" * MAX_INPUT_CHARS)

    def test_cli_contract_real_process(self):
        big = (EMAIL + " " + CUST + " ") + "x" * MAX_INPUT_CHARS
        p = subprocess.run([sys.executable, "-m", "sanitizer", "run", "--request-id", "req-001"],
                           input=big.encode(), capture_output=True, cwd=ROOT)  # bytes: no newline translation
        self.assertEqual(p.returncode, 2)
        self.assertEqual(p.stdout, b"")
        self.assertEqual(p.stderr, b"SANITIZER_INPUT_TOO_LARGE\n")


class OverlapResolution(unittest.TestCase):
    def kept(self, *spans):
        return [(s["entity_type"], s["start"], s["end"]) for s in resolve_spans(spans)]

    def test_longest_wins(self):
        self.assertEqual(self.kept(span("EMAIL_ADDRESS", 0, 5, 0.1), span("CUSTOMER_ID", 3, 12, 1.0)),
                         [("CUSTOMER_ID", 3, 12)])

    def test_higher_score_on_equal_length(self):
        self.assertEqual(self.kept(span("EMAIL_ADDRESS", 0, 5, 0.5), span("CUSTOMER_ID", 0, 5, 0.9)),
                         [("CUSTOMER_ID", 0, 5)])

    def test_email_before_customer_id_on_tie(self):
        self.assertEqual(self.kept(span("CUSTOMER_ID", 1, 6), span("EMAIL_ADDRESS", 0, 5)),
                         [("EMAIL_ADDRESS", 0, 5)])

    def test_earlier_start_on_full_tie(self):
        self.assertEqual(self.kept(span("EMAIL_ADDRESS", 2, 7), span("EMAIL_ADDRESS", 0, 5)),
                         [("EMAIL_ADDRESS", 0, 5)])

    def test_dedupe_and_adjacent_spans_kept(self):
        a, b = span("EMAIL_ADDRESS", 0, 3), span("CUSTOMER_ID", 3, 6)
        self.assertEqual(self.kept(a, dict(a), b), [("EMAIL_ADDRESS", 0, 3), ("CUSTOMER_ID", 3, 6)])
        self.assertEqual(sanitize("abcdef", lambda t: [a, dict(a), b]), "[EMAIL_ADDRESS][CUSTOMER_ID]")

    def test_ints_accepted_as_scores(self):
        self.assertEqual(sanitize("abc", lambda t: [span("EMAIL_ADDRESS", 0, 3, 1)]), "[EMAIL_ADDRESS]")


class Logging(unittest.TestCase):
    def test_default_logs_contain_no_canaries_on_success_and_failure(self):
        with LogCapture() as logs:
            dispatch("demo-001", TEXT, RecordingMock())
            for det in (leaky_detector, lambda t: [span("EMAIL_ADDRESS", -1, 2)]):
                with self.assertRaises(SanitizerError):
                    sanitize(TEXT, det)
            with self.assertRaises(SanitizerError):
                sanitize(TEXT + "x" * MAX_INPUT_CHARS)
        self.assertTrue(logs.text)  # logging actually happened
        for canary in (EMAIL, CUST, "Email ", "quantity"):
            self.assertNotIn(canary, logs.text)

    def test_real_process_default_logging(self):
        p = subprocess.run([sys.executable, "-m", "sanitizer", "run", "--request-id", "demo-001"],
                           input=TEXT, capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stderr, "")
        self.assertEqual(json.loads(p.stdout), PAYLOAD)
        self.assertNotIn(EMAIL, p.stdout + p.stderr)
        self.assertNotIn(CUST, p.stdout + p.stderr)


class InvalidEncoding(unittest.TestCase):
    def test_in_process_no_detection_no_dispatch(self):
        seen = []
        data = b"\xff " + EMAIL.encode() + b" " + CUST.encode()
        with LogCapture() as logs:
            rc, out, err, mock_ = run_cli(["run", "--request-id", "req-001"], data,
                                          detector=lambda t: seen.append(t) or [])
        self.assertEqual((rc, out, err), (2, "", "SANITIZER_INVALID_ENCODING\n"))
        self.assertEqual(seen, [])
        self.assertEqual(mock_.calls, [])
        for canary in (EMAIL, CUST):
            self.assertNotIn(canary, logs.text)
        self.assertNotIn("codec", logs.text)  # no UnicodeDecodeError text

    def test_byte_bound_precedes_decoding_and_chars_checked_after(self):
        rc, _, err, _ = run_cli(["run", "--request-id", "req-001"], b"x" * (MAX_INPUT_BYTES + 1))
        self.assertEqual((rc, err), (2, "SANITIZER_INPUT_TOO_LARGE\n"))
        rc, _, err, _ = run_cli(["run", "--request-id", "req-001"], b"\xff" * (MAX_INPUT_BYTES + 1))
        self.assertEqual((rc, err), (2, "SANITIZER_INPUT_TOO_LARGE\n"))  # documented precedence
        rc, _, err, _ = run_cli(["run", "--request-id", "req-001"], "é" * (MAX_INPUT_CHARS + 1))
        self.assertEqual((rc, err), (2, "SANITIZER_INPUT_TOO_LARGE\n"))  # 20,002 bytes, 10,001 chars
        rc, out, err, _ = run_cli(["run", "--request-id", "req-001"], "\U0001F600" * MAX_INPUT_CHARS)
        self.assertEqual((rc, err), (0, ""))  # exactly MAX_INPUT_BYTES bytes, 10,000 chars


class InternalError(unittest.TestCase):
    def assert_clean(self, rc, out, err, logs):
        self.assertEqual((rc, out, err), (2, "", "SANITIZER_INTERNAL_ERROR\n"))
        for canary in (EMAIL, CUST, "boom"):
            for stream in (out, err, logs.text):
                self.assertNotIn(canary, stream)
        self.assertNotIn("Traceback", err + logs.text)

    def test_provider_exception_with_canaries(self):
        provider = FailingProvider()
        with LogCapture() as logs:
            rc, out, err, _ = run_cli(["run", "--request-id", "demo-001"], TEXT, provider=provider)
        self.assert_clean(rc, out, err, logs)
        self.assertEqual(provider.calls, 1)  # the provider WAS invoked (with the sanitized payload)
        self.assertIn("ERROR sanitizer rejected code=SANITIZER_INTERNAL_ERROR", logs.lines)
        self.assertTrue(all(r.exc_info is None and r.exc_text is None for r in logs.handler.records))

    def test_library_wraps_provider_exception(self):
        with self.assertRaises(SanitizerError) as cm:
            dispatch("req-001", TEXT, FailingProvider())
        self.assertEqual(str(cm.exception), "SANITIZER_INTERNAL_ERROR")
        self.assertIsNone(cm.exception.__cause__)
        self.assertTrue(cm.exception.__suppress_context__)

    def test_unexpected_exception_inside_sanitizer(self):
        provider = RecordingMock()
        boom = RuntimeError(f"internal {EMAIL} {CUST}")
        with mock.patch("sanitizer.core.resolve_spans", side_effect=boom), LogCapture() as logs:
            rc, out, err, _ = run_cli(["run", "--request-id", "demo-001"], TEXT, provider=provider)
        self.assertEqual(provider.calls, [])
        self.assertEqual((rc, out, err), (2, "", "SANITIZER_INTERNAL_ERROR\n"))
        for canary in (EMAIL, CUST):
            self.assertNotIn(canary, logs.text)
        self.assertNotIn("Traceback", err + logs.text)


class LoggingAllowlist(unittest.TestCase):
    """Root-logger handler at DEBUG; every emitted line must be approved metadata."""

    SCENARIOS = {
        "success": (TEXT, baseline_detector, RecordingMock, "INFO sanitizer dispatched chars=59"),
        "detector failure": (TEXT, leaky_detector, RecordingMock, "ERROR sanitizer rejected code=SANITIZER_DETECTOR_ERROR"),
        "malformed output": (TEXT, lambda t: [span("EMAIL_ADDRESS", True, 5)], RecordingMock,
                             "ERROR sanitizer rejected code=SANITIZER_INVALID_DETECTOR_OUTPUT"),
        "provider failure": (TEXT, baseline_detector, FailingProvider,
                             "ERROR sanitizer rejected code=SANITIZER_INTERNAL_ERROR"),
        "invalid encoding": (b"\xff" + TEXT.encode(), baseline_detector, RecordingMock,
                             "ERROR sanitizer rejected code=SANITIZER_INVALID_ENCODING"),
        "oversize": (TEXT + "x" * MAX_INPUT_CHARS, baseline_detector, RecordingMock,
                     "WARNING sanitizer rejected code=SANITIZER_INPUT_TOO_LARGE"),
    }

    def test_every_log_line_is_approved(self):
        for name, (data, det, prov, expected) in self.SCENARIOS.items():
            with self.subTest(name):
                with LogCapture() as logs:
                    run_cli(["run", "--request-id", "demo-001"], data, det, prov())
                self.assertEqual(logs.lines, [expected])  # exactly one approved line
                for line in logs.lines:
                    self.assertRegex(line, LOG_LINE_OK)
                for r in logs.handler.records:
                    self.assertIsNone(r.exc_info)
                    self.assertIsNone(r.exc_text)
                    self.assertIsNone(r.stack_info)
                for canary in (EMAIL, CUST, "Email", "quantity", "boom"):
                    self.assertNotIn(canary, logs.text)

    def test_logs_never_contain_request_id(self):
        for rid in ("demo-001", "req-987654"):
            with LogCapture() as logs:
                run_cli(["run", "--request-id", rid], TEXT)
            self.assertEqual(logs.lines, ["INFO sanitizer dispatched chars=59"])
            self.assertNotIn(rid, logs.text)
        with LogCapture() as logs:  # also through the library entry point
            dispatch("req-424242", TEXT, RecordingMock())
        self.assertNotIn("424242", logs.text)

    def test_real_process_with_root_logging_configured(self):
        prog = ("import logging, sys\n"
                "logging.basicConfig(level=logging.DEBUG, stream=sys.stderr,"
                " format='%(levelname)s %(name)s %(message)s')\n"
                "from sanitizer.cli import main\n"
                "sys.exit(main(['run', '--request-id', 'demo-001']))\n")
        cases = ((TEXT.encode(), 0, [b"INFO sanitizer dispatched chars=59"]),
                 (b"\xff" + TEXT.encode(), 2, [b"ERROR sanitizer rejected code=SANITIZER_INVALID_ENCODING",
                                               b"SANITIZER_INVALID_ENCODING"]))
        for data, rc, want in cases:
            with self.subTest(rc=rc):
                p = subprocess.run([sys.executable, "-c", prog], input=data, capture_output=True, cwd=ROOT)
                self.assertEqual(p.returncode, rc)
                self.assertEqual(p.stderr.replace(b"\r\n", b"\n").split(b"\n"), want + [b""])
                for canary in (EMAIL.encode(), CUST.encode()):
                    self.assertNotIn(canary, p.stderr)


class RealProcessBytes(unittest.TestCase):
    def run_proc(self, data):
        return subprocess.run([sys.executable, "-m", "sanitizer", "run", "--request-id", "req-001"],
                              input=data, capture_output=True, cwd=ROOT)

    def test_crlf_input_not_normalized(self):
        p = self.run_proc(b"a\r\nCUST-004271\r\n")
        self.assertEqual(p.returncode, 0)
        self.assertEqual(json.loads(p.stdout), {"request_id": "req-001", "text": "a\r\n[CUSTOMER_ID]\r\n"})
        self.assertEqual(p.stdout, json.dumps({"request_id": "req-001", "text": "a\r\n[CUSTOMER_ID]\r\n"},
                                              ensure_ascii=False).encode() + b"\n")

    def test_invalid_utf8_rejected_real_process(self):
        bad_inputs = {
            "invalid start byte": b"\xff\xfe " + CUST.encode() + b" " + EMAIL.encode(),
            "truncated sequence": CUST.encode() + b" \xe2\x82",
            "overlong encoding": b"\xc0\xaf",
            "encoded surrogate": b"\xed\xa0\x80",
            "lone continuation": b"ok \x80",
        }
        for name, data in bad_inputs.items():
            with self.subTest(name):
                p = self.run_proc(data)
                self.assertEqual(p.returncode, 2)
                self.assertEqual(p.stdout, b"")
                self.assertEqual(p.stderr, b"SANITIZER_INVALID_ENCODING\n")

    def test_valid_utf8_edge_cases_accepted(self):
        for data, want in ((b"", ""), ("\U0001F600".encode(), "\U0001F600"),
                           (b"\xef\xbb\xbf" + CUST.encode(), "﻿[CUSTOMER_ID]")):
            with self.subTest(data=data):
                p = self.run_proc(data)
                self.assertEqual(p.returncode, 0, p.stderr)
                self.assertEqual(json.loads(p.stdout)["text"], want)


class Cli(unittest.TestCase):
    def test_success_prints_only_captured_payload(self):
        rc, out, err, mock = run_cli(["run", "--request-id", "demo-001"], TEXT)
        self.assertEqual((rc, err), (0, ""))
        self.assertEqual(json.loads(out), PAYLOAD)
        self.assertEqual(mock.calls, [PAYLOAD])

    def test_inspect_fixture_is_the_explicit_synthetic_view(self):
        rc, out, err, _ = run_cli(["inspect-fixture"], "")
        self.assertEqual(rc, 0)
        self.assertIn(EMAIL, out)
        self.assertIn(CUST, out)
        self.assertIn("EMAIL_ADDRESS [6:21]", out)
        self.assertIn("CUSTOMER_ID [32:43]", out)


if __name__ == "__main__":
    unittest.main()
