"""Development-only threshold selection and the procedural freeze (frozen_config.json).

Held-out data is only HASHED here (bytes, never parsed). Everything else is derived from
development.json.
"""
import json
import platform
import re
from pathlib import Path
from typing import Any, Dict

from .config import CONFIG_VERSION, GRID, PROJECT_ROOT, file_sha256
from .core import CUSTOMER_ID_RE, ENTITY_PRIORITY, ERR_INVALID_CONFIG, PHONE_SCOPE_RE, SanitizerError
from .detectors import build_presidio
from .evaluation import aggregate, collect_raw, load_fixture, package_versions, run_split, select_thresholds

SELECTION_RULE = (
    "Candidate thresholds from {0.0,0.4,0.6,0.8,1.0}^3 evaluated on development.json only, using cached raw "
    "candidates through the full shared pipeline (validate all, phone scope gate, score >= threshold, dedupe, "
    "overlap resolution). Choose the highest development exact-span micro F1; ties -> fewer benign characters "
    "removed; then lexicographically higher thresholds in EMAIL_ADDRESS, PHONE_NUMBER, CUSTOMER_ID order."
)


def model_wheel_sha256(requirements_path: Path) -> str:
    for line in requirements_path.read_text(encoding="utf-8").splitlines():
        if line.lower().startswith("en_core_web_sm"):
            m = re.search(r"sha256=([0-9a-f]{64})", line)
            if m:
                return m.group(1)
    raise SanitizerError(ERR_INVALID_CONFIG)


def build_frozen_config(dev_path: Path, heldout_path: Path, requirements_path: Path) -> Dict[str, Any]:
    fixture = load_fixture(dev_path)  # development ONLY
    fn, _mod, analyzer = build_presidio()
    raw = collect_raw(fixture, fn)  # NLP runs once per development example
    sel = select_thresholds(fixture, raw)
    th = sel["best"]["thresholds"]
    records = run_split(fixture, lambda ex: (lambda _t, c=raw[ex["id"]]: c), th)
    agg = aggregate(records)
    return {
        "config_version": CONFIG_VERSION,
        "detector": "presidio",
        "freeze_kind": "procedural freeze of the development configuration; not a blinded external evaluation",
        "heldout_access": "heldout.json was hashed as raw bytes only; its contents were not parsed or read "
                          "before this file was written",
        "thresholds": th,
        "threshold_grid": list(GRID),
        "selection_rule": SELECTION_RULE,
        "selection_grid_size": len(sel["grid"]),
        "selection_tied_at_top_after_benign_rule": sel["tied_at_top_after_benign_rule"],
        "selection_grid": sel["grid"],
        "development_metrics_at_selected_thresholds": {
            "micro": agg["micro"], "per_type": agg["per_type"], "coverage": agg["coverage"], "benign": agg["benign"]},
        "development_sha256": file_sha256(dev_path),
        "heldout_sha256": file_sha256(heldout_path),
        "scope": {
            "entities": list(ENTITY_PRIORITY),
            "PHONE_NUMBER_scope_regex": PHONE_SCOPE_RE.pattern,
            "CUSTOMER_ID_regex": CUSTOMER_ID_RE.pattern,
            "phone_gate": "after validation, a PHONE_NUMBER candidate is kept only if its exact (start,end) is a "
                          "match of the scope regex on the original text; never repaired, trimmed or synthesized",
        },
        "resolution_policy": "decreasing length, decreasing score, type order EMAIL_ADDRESS>PHONE_NUMBER>CUSTOMER_ID, "
                             "earlier start; keep non-overlapping; replace right to left with [TYPE]",
        "baseline": {"score": 1.0, "thresholds": {t: 1.0 for t in ENTITY_PRIORITY}},
        "recognizer_settings": _mod.recognizer_settings(analyzer),
        "packages": package_versions(),
        "model_wheel_sha256": model_wheel_sha256(requirements_path),
        "python": platform.python_version(),
    }


def write_frozen_config(out: Path, cfg: Dict[str, Any]) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(cfg, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8", newline="\n")
