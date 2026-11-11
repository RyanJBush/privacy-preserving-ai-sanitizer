"""Shared scoring, coverage, reporting and development-only threshold selection.

Stdlib only. Everything here scores the spans the real pipeline APPLIED (after validation, scope
gate, frozen thresholds, dedupe and overlap resolution). Reports contain example IDs, entity types,
scores, offsets, counts and metrics, and never raw text, matched values or sanitized text.
"""
import importlib.metadata as md
import itertools
import json
import platform
from collections import Counter
from fractions import Fraction
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .config import GRID
from .core import (ENTITY_PRIORITY, ERR_INVALID_FIXTURE, RecordingMock, SanitizerError, process,
                   replace_spans, run_pipeline)

REPORT_VERSION = 1
NO_PREDICTION_WITH_GOLD = "precision null, recall 0, F1 0 (contract section: primary accuracy metrics)"


# ---------------------------------------------------------------- fixtures
def load_fixture(path) -> Dict[str, Any]:
    """Parse and structurally validate a fixture; any problem -> ERR_INVALID_FIXTURE (no detail)."""
    try:
        fx = json.loads(Path(path).read_text(encoding="utf-8"))
        assert fx["schema_version"] == 1 and fx["offset_unit"] == "python_unicode_codepoint"
        seen = set()
        for ex in fx["examples"]:
            assert isinstance(ex["id"], str) and ex["id"] not in seen
            seen.add(ex["id"])
            assert isinstance(ex["text"], str) and isinstance(ex["expected_sanitized"], str)
            for g in ex["entities"]:
                assert g["entity_type"] in ENTITY_PRIORITY
                assert type(g["start"]) is int and type(g["end"]) is int
                assert 0 <= g["start"] < g["end"] <= len(ex["text"])
        return fx
    except Exception:
        raise SanitizerError(ERR_INVALID_FIXTURE) from None


# ---------------------------------------------------------------- metrics
def metrics(tp: int, fp: int, fn: int) -> Dict[str, Any]:
    """Integer counts and exact-denominator metrics; null when the metric's own denominator is 0."""
    return {
        "tp": tp, "fp": fp, "fn": fn,
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": tp / (tp + fn) if tp + fn else None,
        "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None,
    }


def score_example(text: str, gold: List[Dict[str, Any]], applied: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Score one example against the spans that were actually applied (original coordinates)."""
    g_keys = [(g["entity_type"], g["start"], g["end"]) for g in gold]
    p_keys = [(a["entity_type"], a["start"], a["end"]) for a in applied]
    avail = Counter(g_keys)
    pred_result = []
    for k in p_keys:  # one-to-one exact match on (type, start, end)
        if avail[k] > 0:
            avail[k] -= 1
            pred_result.append("TP")
        else:
            pred_result.append("FP")
    remaining = Counter(p_keys[i] for i, r in enumerate(pred_result) if r == "TP")
    gold_result = []
    for k in g_keys:
        if remaining[k] > 0:
            remaining[k] -= 1
            gold_result.append("TP")
        else:
            gold_result.append("FN")

    covered = set()
    for a in applied:
        covered.update(range(a["start"], a["end"]))
    gold_positions = set()
    for g in gold:
        gold_positions.update(range(g["start"], g["end"]))

    coverage = []
    for g in gold:
        pos = set(range(g["start"], g["end"]))
        n_in = len(pos & covered)
        coverage.append("full" if n_in == len(pos) else ("untouched" if n_in == 0 else "partial"))

    touches_benign, touches_no_gold = [], []
    for a in applied:
        pos = set(range(a["start"], a["end"]))
        touches_benign.append(bool(pos - gold_positions))
        touches_no_gold.append(not (pos & gold_positions))

    by_type = {t: {"tp": 0, "fp": 0, "fn": 0} for t in ENTITY_PRIORITY}
    for k, r in zip(p_keys, pred_result):
        by_type[k[0]]["tp" if r == "TP" else "fp"] += 1
    for k, r in zip(g_keys, gold_result):
        if r == "FN":
            by_type[k[0]]["fn"] += 1

    return {
        "by_type": by_type, "pred_result": pred_result, "gold_result": gold_result, "coverage": coverage,
        "touches_benign": touches_benign, "touches_no_gold": touches_no_gold,
        "benign_characters_removed": len(covered - gold_positions),
    }


def aggregate(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Sum counts across examples BEFORE computing micro metrics."""
    tot = {t: {"tp": 0, "fp": 0, "fn": 0} for t in ENTITY_PRIORITY}
    cov = {t: Counter() for t in ENTITY_PRIORITY}
    benign = {"replacements_touching_benign": 0, "replacements_touching_no_gold": 0,
              "benign_characters_removed": 0}
    pres = {"examples_total": 0, "examples_with_no_gold": 0, "no_gold_examples_preserved": 0,
            "examples_equal_expected_sanitized": 0, "examples_failed_with_fixed_code": 0}
    boundary = {"examples_dispatched": 0, "provider_calls_total": 0,
                "payload_exact_request_id_text_only": 0, "payload_equals_actual_sanitized": 0,
                "reconstruction_from_applied_spans_equals_output": 0, "zero_calls_on_failure": 0}
    for r in records:
        s = r["_score"]
        for t in ENTITY_PRIORITY:
            for k in ("tp", "fp", "fn"):
                tot[t][k] += s["by_type"][t][k]
        for g, c in zip(r["gold"], s["coverage"]):
            cov[g["entity_type"]][c] += 1
        benign["replacements_touching_benign"] += sum(s["touches_benign"])
        benign["replacements_touching_no_gold"] += sum(s["touches_no_gold"])
        benign["benign_characters_removed"] += s["benign_characters_removed"]
        pres["examples_total"] += 1
        if not r["gold"]:
            pres["examples_with_no_gold"] += 1
            pres["no_gold_examples_preserved"] += 1 if r["no_gold_preserved"] else 0
        pres["examples_equal_expected_sanitized"] += 1 if r["matches_expected_sanitized"] else 0
        if r["status"] != "ok":
            pres["examples_failed_with_fixed_code"] += 1
            boundary["zero_calls_on_failure"] += 1 if r["provider_calls"] == 0 else 0
        else:
            boundary["examples_dispatched"] += 1
            boundary["payload_exact_request_id_text_only"] += 1 if r["payload_exact_keys"] else 0
            boundary["payload_equals_actual_sanitized"] += 1 if r["payload_equals_sanitized"] else 0
            boundary["reconstruction_from_applied_spans_equals_output"] += 1 if r["reconstruction_ok"] else 0
        boundary["provider_calls_total"] += r["provider_calls"]

    per_type = {t: metrics(**tot[t]) for t in ENTITY_PRIORITY}
    micro = metrics(sum(tot[t]["tp"] for t in ENTITY_PRIORITY), sum(tot[t]["fp"] for t in ENTITY_PRIORITY),
                    sum(tot[t]["fn"] for t in ENTITY_PRIORITY))

    def cov_block(c: Counter) -> Dict[str, Any]:
        total = c["full"] + c["partial"] + c["untouched"]
        return {"gold": total, "full": c["full"], "partial": c["partial"], "untouched": c["untouched"],
                "coverage_rate": c["full"] / total if total else None}

    overall = Counter()
    for t in ENTITY_PRIORITY:
        overall.update(cov[t])
    return {
        "per_type": per_type, "micro": micro,
        "coverage": {"overall": cov_block(overall), "per_type": {t: cov_block(cov[t]) for t in ENTITY_PRIORITY}},
        "benign": benign, "preservation": pres, "boundary": boundary,
    }


# ---------------------------------------------------------------- running a split
def run_split(fixture: Dict[str, Any], detector_for: Callable[[Dict[str, Any]], Callable[[str], Any]],
              thresholds: Dict[str, float]) -> List[Dict[str, Any]]:
    """Run every example through the REAL pipeline/dispatch path with a RecordingMock provider."""
    records = []
    for i, ex in enumerate(fixture["examples"], 1):
        mock = RecordingMock()
        rid = f"req-{i:03d}"
        try:
            payload, res = run_pipeline(rid, ex["text"], mock, detector_for(ex), thresholds=thresholds)
            status = "ok"
        except SanitizerError as e:
            payload, res, status = None, None, e.code
        applied = res.applied if res else []
        sanitized = res.sanitized if res else None
        sc = score_example(ex["text"], ex["entities"], applied)
        rec = {
            "id": ex["id"], "status": status, "gold": [dict(g) for g in ex["entities"]],
            "applied": [{"entity_type": a["entity_type"], "start": a["start"], "end": a["end"], "score": a["score"]}
                        for a in applied],
            "provider_calls": len(mock.calls),
            "matches_expected_sanitized": sanitized == ex["expected_sanitized"],
            "payload_exact_keys": bool(payload) and mock.calls == [payload] and list(payload) == ["request_id", "text"],
            "payload_equals_sanitized": bool(payload) and payload["text"] == sanitized,
            "reconstruction_ok": bool(res) and replace_spans(ex["text"], applied) == sanitized,
            "no_gold_preserved": (sanitized == ex["text"]) if not ex["entities"] else None,
            "dropped_by_scope": res.dropped_by_scope if res else 0,
            "dropped_by_threshold": res.dropped_by_threshold if res else 0,
            # DIAGNOSTIC ONLY (pre-filter, pre-resolution); never used for the primary metrics
            "diagnostic_validated_candidates": [
                {"entity_type": v["entity_type"], "start": v["start"], "end": v["end"], "score": v["score"]}
                for v in (res.validated if res else [])],
            "_score": sc,
        }
        records.append(rec)
    return records


def public_examples(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for r in records:
        s = r["_score"]
        gold = [dict(g, result=res, coverage=c) for g, res, c in zip(r["gold"], s["gold_result"], s["coverage"])]
        applied = [dict(a, result=res, touches_benign=tb, touches_no_gold=tn)
                   for a, res, tb, tn in zip(r["applied"], s["pred_result"], s["touches_benign"], s["touches_no_gold"])]
        out.append({
            "id": r["id"], "status": r["status"], "gold": gold, "applied": applied,
            "benign_characters_removed": s["benign_characters_removed"],
            "matches_expected_sanitized": r["matches_expected_sanitized"],
            "payload_equals_actual_sanitized": r["payload_equals_sanitized"],
            "payload_exact_request_id_text_only": r["payload_exact_keys"],
            "provider_calls": r["provider_calls"],
            "reconstruction_from_applied_spans_equals_output": r["reconstruction_ok"],
            "no_gold_preserved": r["no_gold_preserved"],
            "dropped_by_scope": r["dropped_by_scope"], "dropped_by_threshold": r["dropped_by_threshold"],
            "diagnostic_pre_resolution_validated_candidates": r["diagnostic_validated_candidates"],
        })
    return out


def package_versions(names=("presidio-analyzer", "spacy", "en-core-web-sm", "phonenumbers", "tldextract", "regex")):
    out = {}
    for n in names:
        try:
            out[n] = md.version(n)
        except md.PackageNotFoundError:
            out[n] = None
    return out


def build_report(meta: Dict[str, Any], records: List[Dict[str, Any]]) -> Dict[str, Any]:
    agg = aggregate(records)
    return {
        "report_version": REPORT_VERSION, "meta": meta,
        "metrics": {"per_type": agg["per_type"], "micro": agg["micro"]},
        "coverage": agg["coverage"], "benign": agg["benign"], "preservation": agg["preservation"],
        "provider_boundary": agg["boundary"], "examples": public_examples(records),
        "notes": [
            "Primary metrics score the spans actually applied after validation, scope gate, thresholds, dedupe and overlap resolution.",
            "diagnostic_pre_resolution_validated_candidates is a separate diagnostic and is not used for the metrics.",
            "Provider-boundary counts are separate from accuracy: a detector miss is an accuracy/coverage failure, not a boundary failure.",
            "Small synthetic template split; not evidence of real-world performance.",
        ],
    }


def dump_report(report: Dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def run_meta(detector: str, split: str, fixture_sha: str, thresholds: Dict[str, float],
             config_sha: Optional[str], extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    meta = {
        "detector": detector, "split": split, "fixture_sha256": fixture_sha, "thresholds": thresholds,
        "frozen_config_sha256": config_sha, "python": platform.python_version(),
        "packages": package_versions() if detector == "presidio" else {},
        "resolution_policy": "validate all spans; phone scope gate; type thresholds (score >= t); dedupe same type/range "
                             "keeping highest score; overlap resolution by length, score, type order "
                             "EMAIL_ADDRESS>PHONE_NUMBER>CUSTOMER_ID, earlier start; replace right to left",
        "status": "procedural freeze of the development configuration; not a blinded external evaluation",
    }
    if extra:
        meta.update(extra)
    return meta


# ---------------------------------------------------------------- development-only threshold selection
def collect_raw(fixture: Dict[str, Any], detector_fn: Callable[[str], Any]) -> Dict[str, Any]:
    """Run the NLP detector ONCE per example and cache its raw candidates (development only)."""
    return {ex["id"]: detector_fn(ex["text"]) for ex in fixture["examples"]}


def pick_best(grid: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Highest F1 (exact Fraction in `_f1`), then fewer benign characters removed, then lexicographically
    higher thresholds in EMAIL_ADDRESS, PHONE_NUMBER, CUSTOMER_ID order."""
    return max(grid, key=lambda r: (r["_f1"], -r["benign_characters_removed"], r["thresholds"]["EMAIL_ADDRESS"],
                                    r["thresholds"]["PHONE_NUMBER"], r["thresholds"]["CUSTOMER_ID"]))


def select_thresholds(fixture: Dict[str, Any], raw_by_id: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate GRID^3 on cached development candidates through the full shared pipeline.

    Rule: highest development exact-span micro F1; ties -> fewer benign characters removed;
    then lexicographically higher thresholds in (EMAIL_ADDRESS, PHONE_NUMBER, CUSTOMER_ID) order.
    """
    grid = []
    for e, p, c in itertools.product(GRID, repeat=3):
        th = {"EMAIL_ADDRESS": e, "PHONE_NUMBER": p, "CUSTOMER_ID": c}
        tp = fp = fn = benign = 0
        for ex in fixture["examples"]:
            cands = raw_by_id[ex["id"]]
            res = process(ex["text"], lambda _t, c_=cands: c_, thresholds=th)
            sc = score_example(ex["text"], ex["entities"], res.applied)
            for t in ENTITY_PRIORITY:
                tp += sc["by_type"][t]["tp"]
                fp += sc["by_type"][t]["fp"]
                fn += sc["by_type"][t]["fn"]
            benign += sc["benign_characters_removed"]
        f1 = Fraction(2 * tp, 2 * tp + fp + fn) if 2 * tp + fp + fn else Fraction(0)
        grid.append({"thresholds": th, "tp": tp, "fp": fp, "fn": fn, "benign_characters_removed": benign,
                     "f1": float(f1), "_f1": f1})
    best = pick_best(grid)
    ties = [r["thresholds"] for r in grid
            if r["_f1"] == best["_f1"] and r["benign_characters_removed"] == best["benign_characters_removed"]]
    for r in grid:
        del r["_f1"]
    return {"best": {k: v for k, v in best.items() if k != "_f1"}, "grid": grid, "tied_at_top_after_benign_rule": len(ties)}
