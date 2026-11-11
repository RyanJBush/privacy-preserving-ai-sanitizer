"""Shared-pipeline tests: phone baseline and scope gate, validate-before-filter, thresholds,
dedupe, and every type-priority tie. Stdlib only; no held-out data."""
import unittest

from sanitizer import RecordingMock, SanitizerError, baseline_detector, dispatch, sanitize
from sanitizer.core import ENTITY_PRIORITY, PHONE_SCOPE_RE, process, resolve_spans, run_pipeline

PHONE = "(415) 555-0132"


def sp(t, a, b, score=1.0):
    return {"entity_type": t, "start": a, "end": b, "score": score}


def fixed(*spans):
    return lambda _t: list(spans)


class PhoneBaseline(unittest.TestCase):
    def test_exact_format_detected(self):
        t = f"Call {PHONE}, ok"
        self.assertEqual([(s["entity_type"], s["start"], s["end"]) for s in baseline_detector(t)],
                         [("PHONE_NUMBER", 5, 19)])
        self.assertEqual(sanitize(t), "Call [PHONE_NUMBER], ok")

    def test_out_of_scope_formats_are_not_detected(self):
        for t in ("(115) 555-0132",      # area code starts with 1
                  "(415) 155-0132",      # exchange starts with 1
                  "415-555-0132", "(415)555-0132", "(415)  555-0132", "(415) 555-0132",
                  "x(415) 555-0132", "(415) 555-01323", "(415) 555-0132_", "A(415) 555-0132",
                  "(415) 555-013", "( 415) 555-0132", "(٤١٥) 555-0132"):
            with self.subTest(t=t):
                self.assertEqual([s for s in baseline_detector(t) if s["entity_type"] == "PHONE_NUMBER"], [])
                self.assertEqual(sanitize(t), t)

    def test_digit_ranges(self):
        self.assertIsNotNone(PHONE_SCOPE_RE.search("(200) 200-0000"))
        self.assertIsNotNone(PHONE_SCOPE_RE.search("(999) 999-9999"))
        self.assertIsNone(PHONE_SCOPE_RE.search("(100) 200-0000"))
        self.assertIsNone(PHONE_SCOPE_RE.search("(200) 100-0000"))

    def test_boundaries_allow_punctuation_and_whitespace(self):
        self.assertEqual(sanitize(f"({PHONE}),\n{PHONE}!"), "([PHONE_NUMBER]),\n[PHONE_NUMBER]!")


class ScopeGate(unittest.TestCase):
    TEXT = f"Call {PHONE} now"  # PHONE occupies [5,19)

    def test_exact_match_is_kept(self):
        self.assertEqual(sanitize(self.TEXT, fixed(sp("PHONE_NUMBER", 5, 19))), "Call [PHONE_NUMBER] now")

    def test_trimmed_expanded_and_shifted_candidates_are_dropped_not_repaired(self):
        for a, b in ((5, 18), (6, 19), (4, 19), (5, 20), (0, 19), (7, 12)):
            with self.subTest(span=(a, b)):
                res = process(self.TEXT, fixed(sp("PHONE_NUMBER", a, b)))
                self.assertEqual(res.sanitized, self.TEXT)
                self.assertEqual(res.applied, [])
                self.assertEqual(res.dropped_by_scope, 1)

    def test_gate_does_not_insert_missing_detections(self):
        res = process(self.TEXT, fixed())  # a detector that finds nothing: the gate must not "repair" that
        self.assertEqual((res.sanitized, res.applied), (self.TEXT, []))

    def test_unsupported_format_phone_candidate_is_dropped(self):
        text = "Unsupported phone 202-555-0147 here"
        self.assertEqual(sanitize(text, fixed(sp("PHONE_NUMBER", 18, 30))), text)

    def test_gate_applies_only_to_phone_candidates(self):
        res = process("hello", fixed(sp("EMAIL_ADDRESS", 0, 5)))
        self.assertEqual(res.sanitized, "[EMAIL_ADDRESS]")

    def test_all_spans_are_validated_before_the_gate_or_thresholds(self):
        # The out-of-scope phone span would be silently dropped, but it is malformed (bool offset):
        # the whole output must abort, and the provider must not be called.
        for bad in (sp("PHONE_NUMBER", True, 19), sp("PHONE_NUMBER", 5, 19, 1.5), sp("PHONE_NUMBER", 5, 19, float("nan")),
                    sp("PHONE_NUMBER", 5, 999), sp("PHONE_NUMBER", 5, 19, 10 ** 400)):
            with self.subTest(bad=bad):
                mock = RecordingMock()
                with self.assertRaises(SanitizerError) as cm:
                    dispatch("demo-001", self.TEXT, mock, fixed(sp("EMAIL_ADDRESS", 0, 4), bad),
                             thresholds={t: 1.0 for t in ENTITY_PRIORITY})
                self.assertEqual(str(cm.exception), "SANITIZER_INVALID_DETECTOR_OUTPUT")
                self.assertEqual(mock.calls, [])


class Thresholds(unittest.TestCase):
    def test_score_equal_to_threshold_passes_and_below_fails(self):
        for score, expect in ((0.6, True), (0.5999, False), (1.0, True)):
            with self.subTest(score=score):
                res = process("abcdef", fixed(sp("EMAIL_ADDRESS", 0, 6, score)), thresholds={"EMAIL_ADDRESS": 0.6})
                self.assertEqual(bool(res.applied), expect)
                self.assertEqual(res.dropped_by_threshold, 0 if expect else 1)

    def test_thresholds_are_per_type(self):
        res = process("abc def", fixed(sp("EMAIL_ADDRESS", 0, 3, 0.5), sp("CUSTOMER_ID", 4, 7, 0.5)),
                      thresholds={"EMAIL_ADDRESS": 0.4, "CUSTOMER_ID": 0.6})
        self.assertEqual([s["entity_type"] for s in res.applied], ["EMAIL_ADDRESS"])

    def test_no_thresholds_accepts_every_valid_score(self):
        self.assertEqual(sanitize("abc", fixed(sp("EMAIL_ADDRESS", 0, 3, 0.0))), "[EMAIL_ADDRESS]")

    def test_dedupe_keeps_highest_score_for_same_type_and_range(self):
        res = process("abcdef", fixed(sp("EMAIL_ADDRESS", 0, 6, 0.7), sp("EMAIL_ADDRESS", 0, 6, 0.95),
                                      sp("EMAIL_ADDRESS", 0, 6, 0.8)))
        self.assertEqual([(s["start"], s["end"], s["score"]) for s in res.applied], [(0, 6, 0.95)])


class TypePriorityTies(unittest.TestCase):
    """Same length and same score: EMAIL_ADDRESS > PHONE_NUMBER > CUSTOMER_ID, then earlier start."""

    def winner(self, *spans):
        return [(s["entity_type"], s["start"], s["end"]) for s in resolve_spans(spans)]

    def test_all_pairwise_ties_same_range(self):
        E, P, C = "EMAIL_ADDRESS", "PHONE_NUMBER", "CUSTOMER_ID"
        self.assertEqual(self.winner(sp(P, 0, 5), sp(E, 0, 5)), [(E, 0, 5)])
        self.assertEqual(self.winner(sp(C, 0, 5), sp(E, 0, 5)), [(E, 0, 5)])
        self.assertEqual(self.winner(sp(C, 0, 5), sp(P, 0, 5)), [(P, 0, 5)])
        self.assertEqual(self.winner(sp(C, 0, 5), sp(P, 0, 5), sp(E, 0, 5)), [(E, 0, 5)])

    def test_ties_with_offset_overlap_use_type_before_start(self):
        E, P, C = "EMAIL_ADDRESS", "PHONE_NUMBER", "CUSTOMER_ID"
        self.assertEqual(self.winner(sp(P, 0, 5), sp(E, 2, 7)), [(E, 2, 7)])   # type beats earlier start
        self.assertEqual(self.winner(sp(C, 0, 5), sp(P, 2, 7)), [(P, 2, 7)])
        self.assertEqual(self.winner(sp(E, 3, 8), sp(E, 1, 6)), [(E, 1, 6)])   # same type: earlier start

    def test_length_then_score_precede_type(self):
        E, P, C = "EMAIL_ADDRESS", "PHONE_NUMBER", "CUSTOMER_ID"
        self.assertEqual(self.winner(sp(E, 0, 5, 1.0), sp(C, 0, 7, 0.1)), [(C, 0, 7)])
        self.assertEqual(self.winner(sp(E, 0, 5, 0.5), sp(P, 0, 5, 0.9)), [(P, 0, 5)])

    def test_adjacent_nonoverlapping_spans_are_both_kept(self):
        E, C = "EMAIL_ADDRESS", "CUSTOMER_ID"
        self.assertEqual(self.winner(sp(E, 0, 3), sp(C, 3, 6)), [(E, 0, 3), (C, 3, 6)])

    def test_customer_id_inside_an_email_loses_to_the_whole_email(self):
        text = "Owner CUST-100005@example.com;"
        self.assertEqual(sanitize(text), "Owner [EMAIL_ADDRESS];")


class SharedPipeline(unittest.TestCase):
    def test_sanitize_dispatch_and_run_pipeline_agree(self):
        text = f"Email ava@example.com; phone {PHONE}; customer CUST-004271."
        mock = RecordingMock()
        payload, res = run_pipeline("demo-001", text, mock, baseline_detector)
        self.assertEqual(payload["text"], res.sanitized)
        self.assertEqual(res.sanitized, sanitize(text))
        self.assertEqual(dispatch("demo-001", text, RecordingMock()), payload)
        self.assertEqual(replace_applied(text, res), res.sanitized)
        self.assertEqual(res.entity_counts(), {"EMAIL_ADDRESS": 1, "PHONE_NUMBER": 1, "CUSTOMER_ID": 1})
        self.assertEqual(mock.calls, [{"request_id": "demo-001", "text": res.sanitized}])


def replace_applied(text, res):
    from sanitizer.core import replace_spans
    return replace_spans(text, res.applied)


if __name__ == "__main__":
    unittest.main()
