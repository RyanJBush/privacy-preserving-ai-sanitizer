"""Explicit SYNTHETIC inspection command. It prints fabricated fixture values by design.

It accepts no user-supplied text and has no real-provider route: every payload shown was captured
by the in-memory RecordingMock after running the real pipeline.
"""
import json
from pathlib import Path

from .config import FIXTURE_DIR, PROJECT_ROOT, file_sha256
from .core import RecordingMock, SanitizerError, run_pipeline
from .detectors import load_detector
from .evaluation import load_fixture
from .fixture import CANARY_GOLD, CANARY_SANITIZED, CANARY_TEXT

REPORTS_DIR = PROJECT_ROOT / "reports"


def _slice(text, s):
    return text[s["start"]:s["end"]]


def _fmt_spans(text, spans):
    if not spans:
        return ["    (none)"]
    return [f"    {s['entity_type']:<13} [{s['start']}:{s['end']}] {_slice(text, s)!r}"
            + (f" score={s['score']!r}" if "score" in s else "") for s in sorted(spans, key=lambda s: (s["start"], s["end"]))]


def _show(w, title, text, gold, det, expected=None):
    mock = RecordingMock()
    w(f"--- {title}")
    w(f"  original : {text!r}")
    w("  gold:")
    for line in _fmt_spans(text, gold):
        w(line)
    try:
        payload, res = run_pipeline("demo-001", text, mock, det.fn, thresholds=det.thresholds)
    except SanitizerError as e:
        w(f"  FAILED with fixed code {e.code}; provider calls = {len(mock.calls)}")
        return
    w("  detected (validated candidates, before scope/threshold/resolution):")
    for line in _fmt_spans(text, res.validated):
        w(line)
    w("  resolved (applied) spans:")
    for line in _fmt_spans(text, res.applied):
        w(line)
    w(f"  sanitized: {res.sanitized!r}")
    w(f"  payload captured by RecordingMock: {mock.calls[0]!r} (calls={len(mock.calls)})")
    if expected is not None:
        w(f"  equals fixture oracle: {res.sanitized == expected}  (oracle is a check only, never a shortcut)")


def _heldout_section(w, det_name, reports_dir):
    w("")
    w(f"=== Held-out misses and unnecessary redactions ({det_name}) ===")
    rp = Path(reports_dir) / f"heldout_{det_name}.json"
    if not rp.is_file():
        w("  no held-out report found; run the held-out evaluation first (see README)")
        return
    rep = json.loads(rp.read_text(encoding="utf-8"))
    hp = FIXTURE_DIR / "heldout.json"
    if file_sha256(hp) != rep["meta"]["fixture_sha256"]:
        w("  held-out fixture hash differs from the report; not showing values")
        return
    fx = {e["id"]: e for e in load_fixture(hp)["examples"]}
    misses, unnecessary = [], []
    for ex in rep["examples"]:
        for g in ex["gold"]:
            if g["result"] == "FN":
                misses.append((ex, g))
        for a in ex["applied"]:
            if a["touches_benign"] or a["result"] == "FP":
                unnecessary.append((ex, a))
    w(f"  actual missed gold spans (exact-span FN): {len(misses)}; unnecessary or imprecise redactions "
      f"(touch benign characters or are FP): {len(unnecessary)}")

    def one(label, item, kind):
        if not item:
            w(f"  {label}: zero observed on these fixtures")
            return
        ex, s = item
        text = fx[ex["id"]]["text"]
        w(f"  {label}: example {ex['id']}")
        w(f"    text: {text!r}")
        if kind == "miss":
            w(f"    missed gold: {s['entity_type']} [{s['start']}:{s['end']}] {text[s['start']:s['end']]!r} "
              f"(coverage {s['coverage']})")
        else:
            w(f"    applied: {s['entity_type']} [{s['start']}:{s['end']}] {text[s['start']:s['end']]!r} "
              f"(result {s['result']}, touches_benign={s['touches_benign']})")
        w("    all gold: " + "; ".join(f"{g['entity_type']}[{g['start']}:{g['end']}]={text[g['start']:g['end']]!r}" for g in ex["gold"]))
        w("    all applied: " + "; ".join(f"{a['entity_type']}[{a['start']}:{a['end']}]={text[a['start']:a['end']]!r}" for a in ex["applied"]))

    one("first missed gold field", misses[0] if misses else None, "miss")
    one("first unnecessary redaction", unnecessary[0] if unnecessary else None, "redaction")


def run_demo(w, detector_name, config_path=None, reports_dir=REPORTS_DIR):
    det = load_detector(detector_name, config_path)
    dev = {e["id"]: e for e in load_fixture(FIXTURE_DIR / "development.json")["examples"]}
    w("=" * 78)
    w("SYNTHETIC INSPECTION. Every value below is fabricated fixture data printed on purpose.")
    w(f"detector: {det.name} | thresholds: {det.thresholds}")
    w("No user text is accepted here; payloads come from the in-memory RecordingMock only.")
    w("=" * 78)
    _show(w, "all-three-entity canary", CANARY_TEXT, CANARY_GOLD, det, CANARY_SANITIZED)
    for key, title in (("dev-006", "benign preservation (no gold; output must equal input)"),
                       ("dev-004", "Unicode offsets (emoji and accent before the fields)"),
                       ("dev-003", "repeated value at two positions"),
                       ("dev-009", "CRLF and tab preserved")):
        ex = dev[key]
        _show(w, f"{title} [{key}]", ex["text"], ex["entities"], det, ex["expected_sanitized"])
    w("--- detector failure (demo-local failing detector; zero provider calls)")
    mock = RecordingMock()

    def boom(_text):
        raise RuntimeError("synthetic failure that mentions ava@example.com")

    try:
        run_pipeline("demo-001", CANARY_TEXT, mock, boom)
    except SanitizerError as e:
        w(f"  fixed code: {e.code}; provider calls = {len(mock.calls)}; the exception text is not exposed")
    _heldout_section(w, det.name, reports_dir)
    return 0
