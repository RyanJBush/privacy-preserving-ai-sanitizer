"""Scoring, coverage, fixture loading and threshold-selection unit tests (stdlib only).

Synthetic scoring cases only. None of these touches held-out data."""
import json
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

from sanitizer.config import FIXTURE_DIR, GRID, file_sha256
from sanitizer.core import ENTITY_PRIORITY, SanitizerError, replace_spans
from sanitizer.evaluation import (aggregate, load_fixture, metrics, pick_best, run_split, score_example,
                                  select_thresholds)

ORACLE = {
    "text": "ABCD----WXYZ--pq",
    "gold": [{"entity_type": "EMAIL_ADDRESS", "start": 0, "end": 4},
             {"entity_type": "CUSTOMER_ID", "start": 8, "end": 12}],
    "applied": [{"entity_type": "EMAIL_ADDRESS", "start": 0, "end": 3},
                {"entity_type": "CUSTOMER_ID", "start": 7, "end": 12},
                {"entity_type": "PHONE_NUMBER", "start": 14, "end": 16}],
    "expected_output": "[EMAIL_ADDRESS]D---[CUSTOMER_ID]--[PHONE_NUMBER]",
}


def E(a, b):
    return {"entity_type": "EMAIL_ADDRESS", "start": a, "end": b}


def C(a, b):
    return {"entity_type": "CUSTOMER_ID", "start": a, "end": b}


def P(a, b):
    return {"entity_type": "PHONE_NUMBER", "start": a, "end": b}


def totals(sc):
    tp = sum(sc["by_type"][t]["tp"] for t in ENTITY_PRIORITY)
    fp = sum(sc["by_type"][t]["fp"] for t in ENTITY_PRIORITY)
    fn = sum(sc["by_type"][t]["fn"] for t in ENTITY_PRIORITY)
    return tp, fp, fn


class HandCalculatedOracle(unittest.TestCase):
    def setUp(self):
        self.sc = score_example(ORACLE["text"], ORACLE["gold"], ORACLE["applied"])

    def test_counts_and_micro_metrics(self):
        self.assertEqual(totals(self.sc), (0, 3, 2))
        m = metrics(*totals(self.sc))
        self.assertEqual((m["precision"], m["recall"], m["f1"]), (0.0, 0.0, 0.0))

    def test_per_type_counts(self):
        self.assertEqual(self.sc["by_type"], {
            "EMAIL_ADDRESS": {"tp": 0, "fp": 1, "fn": 1},
            "PHONE_NUMBER": {"tp": 0, "fp": 1, "fn": 0},
            "CUSTOMER_ID": {"tp": 0, "fp": 1, "fn": 1}})

    def test_coverage(self):
        self.assertEqual(self.sc["coverage"], ["partial", "full"])  # email partial, customer id full
        self.assertEqual(self.sc["coverage"].count("untouched"), 0)
        self.assertEqual(self.sc["coverage"].count("full") / len(self.sc["coverage"]), 0.5)

    def test_benign_statistics(self):
        self.assertEqual(sum(self.sc["touches_benign"]), 2)
        self.assertEqual(sum(self.sc["touches_no_gold"]), 1)
        self.assertEqual(self.sc["benign_characters_removed"], 3)  # original indices 7, 14, 15

    def test_replacement_output(self):
        self.assertEqual(replace_spans(ORACLE["text"], ORACLE["applied"]), ORACLE["expected_output"])


class EdgeCases(unittest.TestCase):
    def test_wrong_type_with_full_coverage(self):
        sc = score_example("abcdef", [E(0, 4)], [C(0, 4)])
        self.assertEqual(totals(sc), (0, 1, 1))
        self.assertEqual(sc["coverage"], ["full"])  # coverage is distinct from exact-span/type accuracy
        self.assertEqual(sc["benign_characters_removed"], 0)

    def test_adjacent_intervals_union_covers_gold_but_is_not_an_exact_match(self):
        sc = score_example("abcdef", [E(0, 6)], [E(0, 3), E(3, 6)])
        self.assertEqual(sc["coverage"], ["full"])
        self.assertEqual(totals(sc), (0, 2, 1))

    def test_partial_interval_is_one_fp_and_one_fn(self):
        self.assertEqual(totals(score_example("abcdef", [E(0, 4)], [E(0, 3)])), (0, 1, 1))

    def test_repeated_values_are_separate_gold_entities(self):
        sc = score_example("x@y.zz x@y.zz", [E(0, 6), E(7, 13)], [E(0, 6), E(7, 13)])
        self.assertEqual(totals(sc), (2, 0, 0))
        sc = score_example("x@y.zz x@y.zz", [E(0, 6), E(7, 13)], [E(0, 6)])
        self.assertEqual(totals(sc), (1, 0, 1))
        self.assertEqual(sc["coverage"], ["full", "untouched"])

    def test_unicode_offsets_are_code_points(self):
        text = "\U0001F512 Café: leo@example.net"
        start = text.index("leo")
        gold = [E(start, len(text))]
        self.assertEqual(start, 8)
        self.assertEqual(totals(score_example(text, gold, gold)), (1, 0, 0))
        # a UTF-8 byte offset would be wrong: 12 bytes before 'leo', not 8
        self.assertNotEqual(len(text[:start].encode("utf-8")), start)

    def test_empty_gold_and_empty_predictions(self):
        sc = score_example("", [], [])
        self.assertEqual(totals(sc), (0, 0, 0))
        self.assertEqual(sc["benign_characters_removed"], 0)
        m = metrics(0, 0, 0)
        self.assertEqual((m["precision"], m["recall"], m["f1"]), (None, None, None))

    def test_metric_null_rules(self):
        m = metrics(0, 0, 3)  # no predictions, positive gold
        self.assertEqual((m["precision"], m["recall"], m["f1"]), (None, 0.0, 0.0))
        m = metrics(0, 2, 0)  # predictions, no gold
        self.assertEqual((m["precision"], m["recall"], m["f1"]), (0.0, None, 0.0))
        m = metrics(3, 1, 1)
        self.assertEqual((m["precision"], m["recall"], m["f1"]), (0.75, 0.75, 6 / 8))

    def test_benign_only_example_with_a_replacement_is_all_benign(self):
        sc = score_example("hello world", [], [C(0, 5)])
        self.assertEqual((sum(sc["touches_benign"]), sum(sc["touches_no_gold"]), sc["benign_characters_removed"]),
                         (1, 1, 5))
        self.assertEqual(totals(sc), (0, 1, 0))


class AggregateThroughRealPipeline(unittest.TestCase):
    def test_counts_are_summed_before_micro_metrics(self):
        fx = {"examples": [
            {"id": "a", "text": "x@y.zz", "entities": [E(0, 6)], "expected_sanitized": "[EMAIL_ADDRESS]"},
            {"id": "b", "text": "hello CUST-123456", "entities": [C(6, 17)], "expected_sanitized": "hello [CUSTOMER_ID]"},
            {"id": "c", "text": "plain", "entities": [], "expected_sanitized": "plain"},
        ]}
        spans = {"a": [dict(E(0, 6), score=1.0)], "b": [dict(C(6, 17), score=1.0), dict(E(0, 5), score=1.0)], "c": []}
        recs = run_split(fx, lambda ex: (lambda _t, s=spans[ex["id"]]: s), {t: 0.0 for t in ENTITY_PRIORITY})
        agg = aggregate(recs)
        self.assertEqual((agg["micro"]["tp"], agg["micro"]["fp"], agg["micro"]["fn"]), (2, 1, 0))
        self.assertEqual(agg["per_type"]["EMAIL_ADDRESS"]["fp"], 1)
        self.assertEqual(agg["coverage"]["overall"]["coverage_rate"], 1.0)
        self.assertEqual(agg["benign"]["replacements_touching_no_gold"], 1)
        self.assertEqual(agg["preservation"]["no_gold_examples_preserved"], 1)
        self.assertEqual(agg["preservation"]["examples_equal_expected_sanitized"], 2)  # b has an extra redaction
        self.assertEqual(agg["boundary"]["payload_equals_actual_sanitized"], 3)
        self.assertEqual(agg["boundary"]["provider_calls_total"], 3)

    def test_detector_failure_counts_gold_as_missed_with_zero_calls(self):
        fx = {"examples": [{"id": "a", "text": "x@y.zz", "entities": [E(0, 6)], "expected_sanitized": "[EMAIL_ADDRESS]"}]}

        def boom(_t):
            raise RuntimeError("secret x@y.zz")

        recs = run_split(fx, lambda ex: boom, {t: 0.0 for t in ENTITY_PRIORITY})
        self.assertEqual(recs[0]["status"], "SANITIZER_DETECTOR_ERROR")
        self.assertEqual(recs[0]["provider_calls"], 0)
        agg = aggregate(recs)
        self.assertEqual((agg["micro"]["tp"], agg["micro"]["fn"]), (0, 1))
        self.assertEqual(agg["coverage"]["overall"]["untouched"], 1)
        self.assertEqual(agg["boundary"]["zero_calls_on_failure"], 1)


class ThresholdSelection(unittest.TestCase):
    def fx(self, text, gold):
        return {"examples": [{"id": "a", "text": text, "entities": gold, "expected_sanitized": text}]}

    def test_grid_is_125_and_ties_prefer_higher_thresholds(self):
        sel = select_thresholds(self.fx("x@y.zz", [E(0, 6)]), {"a": [dict(E(0, 6), score=1.0)]})
        self.assertEqual(len(sel["grid"]), len(GRID) ** 3)
        self.assertEqual(sel["best"]["thresholds"], {"EMAIL_ADDRESS": 1.0, "PHONE_NUMBER": 1.0, "CUSTOMER_ID": 1.0})

    def test_threshold_is_inclusive_and_picks_highest_passing_value(self):
        sel = select_thresholds(self.fx("x@y.zz", [E(0, 6)]), {"a": [dict(E(0, 6), score=0.6)]})
        self.assertEqual(sel["best"]["thresholds"]["EMAIL_ADDRESS"], 0.6)  # score >= threshold
        self.assertEqual((sel["best"]["tp"], sel["best"]["fp"], sel["best"]["fn"]), (1, 0, 0))

    def test_no_predictions_has_f1_zero_and_selection_still_defined(self):
        sel = select_thresholds(self.fx("x@y.zz", [E(0, 6)]), {"a": []})
        self.assertEqual(sel["best"]["f1"], 0.0)
        self.assertEqual(sel["best"]["fn"], 1)

    def test_false_positive_is_cut_by_raising_its_threshold(self):
        raw = {"a": [dict(E(0, 6), score=0.9), dict(C(8, 11), score=0.5)]}
        sel = select_thresholds(self.fx("x@y.zz  abc", [E(0, 6)]), raw)
        self.assertGreater(sel["best"]["thresholds"]["CUSTOMER_ID"], 0.5)
        self.assertEqual((sel["best"]["tp"], sel["best"]["fp"]), (1, 0))

    def test_tie_break_order_is_f1_then_fewer_benign_then_higher_thresholds(self):
        def entry(f1, benign, e, p_, c):
            return {"_f1": Fraction(f1), "benign_characters_removed": benign,
                    "thresholds": {"EMAIL_ADDRESS": e, "PHONE_NUMBER": p_, "CUSTOMER_ID": c}}

        # higher F1 beats everything
        self.assertEqual(pick_best([entry(1, 9, 0.0, 0.0, 0.0), entry(Fraction(1, 2), 0, 1.0, 1.0, 1.0)])["benign_characters_removed"], 9)
        # equal F1: fewer benign characters wins even with lower thresholds
        best = pick_best([entry(1, 5, 1.0, 1.0, 1.0), entry(1, 2, 0.0, 0.0, 0.0)])
        self.assertEqual(best["benign_characters_removed"], 2)
        # equal F1 and benign: lexicographically higher (EMAIL, PHONE, CUSTOMER) wins
        best = pick_best([entry(1, 2, 0.8, 1.0, 1.0), entry(1, 2, 1.0, 0.0, 0.0), entry(1, 2, 1.0, 0.4, 0.0)])
        self.assertEqual(best["thresholds"], {"EMAIL_ADDRESS": 1.0, "PHONE_NUMBER": 0.4, "CUSTOMER_ID": 0.0})


class FixtureLoading(unittest.TestCase):
    def test_development_fixture_loads_and_matches_summary(self):
        fx = load_fixture(FIXTURE_DIR / "development.json")
        summary = json.loads((FIXTURE_DIR / "fixture_summary.json").read_text(encoding="utf-8"))["development"]
        self.assertEqual(len(fx["examples"]), summary["examples"])
        counts = {t: 0 for t in ENTITY_PRIORITY}
        for ex in fx["examples"]:
            for g in ex["entities"]:
                counts[g["entity_type"]] += 1
        self.assertEqual(counts, summary["gold_entities"])

    def test_development_gold_slices_and_oracles_are_self_consistent(self):
        for ex in load_fixture(FIXTURE_DIR / "development.json")["examples"]:
            applied = [dict(g, score=1.0) for g in ex["entities"]]
            self.assertEqual(replace_spans(ex["text"], applied), ex["expected_sanitized"], ex["id"])

    def test_fixtures_are_the_unchanged_handoff_files(self):
        manifest = json.loads((FIXTURE_DIR.parent / "docs" / "handoff" / "MANIFEST.json").read_text(encoding="utf-8"))
        for name in ("development.json", "heldout.json", "fixture_summary.json"):
            self.assertEqual(file_sha256(FIXTURE_DIR / name), manifest[name], name)

    def test_malformed_fixture_is_rejected_with_fixed_code(self):
        bad = [
            {"schema_version": 2, "offset_unit": "python_unicode_codepoint", "examples": []},
            {"schema_version": 1, "offset_unit": "utf8_bytes", "examples": []},
            {"schema_version": 1, "offset_unit": "python_unicode_codepoint", "examples": [
                {"id": "a", "text": "abc", "entities": [E(0, 9)], "expected_sanitized": "abc"}]},
            {"schema_version": 1, "offset_unit": "python_unicode_codepoint", "examples": [
                {"id": "a", "text": "abc", "entities": [], "expected_sanitized": "abc"},
                {"id": "a", "text": "abc", "entities": [], "expected_sanitized": "abc"}]},
        ]
        with tempfile.TemporaryDirectory() as d:
            for i, obj in enumerate(bad):
                p = Path(d) / f"f{i}.json"
                p.write_text(json.dumps(obj), encoding="utf-8")
                with self.assertRaises(SanitizerError) as cm:
                    load_fixture(p)
                self.assertEqual(str(cm.exception), "SANITIZER_INVALID_FIXTURE")
            with self.assertRaises(SanitizerError):
                load_fixture(Path(d) / "missing.json")


if __name__ == "__main__":
    unittest.main()
