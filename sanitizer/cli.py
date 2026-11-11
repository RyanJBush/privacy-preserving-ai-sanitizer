"""CLI. Normal use never prints the original text. Every failure prints exactly one fixed code + LF
to stderr, nothing to stdout, exit 2.

  run --request-id ID [--detector baseline|presidio] [--config PATH] [--summary]
        reads UTF-8 bytes from stdin; prints the payload captured by the in-memory mock
        (--summary wraps it as {"payload": {...}, "entity_counts": {...}}; counts only, no values)
  inspect-fixture        explicit synthetic inspection of dev-001 (prints the canaries)
  demo [--detector ...]  explicit synthetic inspection of fixture examples (prints fabricated values)
  select-thresholds      development-only threshold selection + procedural freeze (writes frozen_config.json)
  evaluate --detector D --split development|heldout   writes a privacy-safe JSON report
"""
import json
import logging
import sys
from argparse import ArgumentParser
from pathlib import Path

from .config import (DEFAULT_CONFIG, FIXTURE_DIR, PROJECT_ROOT, check_fixture_integrity, file_sha256,
                     load_frozen_config, validate_thresholds)
from .core import (ENTITY_PRIORITY, ERR_CONFIG_REQUIRED, ERR_INTERNAL, ERR_INVALID_ARGUMENTS, ERR_INVALID_CONFIG,
                   MAX_INPUT_BYTES, RecordingMock, SanitizerError, baseline_detector, decode_input,
                   run_pipeline, validate_request_id)
from .detectors import BASELINE_THRESHOLDS, DETECTOR_NAMES, build_presidio, load_detector
from .fixture import DEV_001

log = logging.getLogger("sanitizer")
EXIT_ERROR = 2


class _Parser(ArgumentParser):
    """argparse's default error() echoes supplied argument values to stderr; never do that."""

    def error(self, message):
        log.error("rejected code=%s", ERR_INVALID_ARGUMENTS)
        raise SanitizerError(ERR_INVALID_ARGUMENTS)


def _run(args, stdin, stdout, detector, provider):
    validate_request_id(args.request_id)  # before reading stdin or detecting
    text = decode_input(stdin.read(MAX_INPUT_BYTES + 1))  # bounded binary read, strict UTF-8
    if detector is not None:  # injected detector (tests); accepts every score
        fn, th = detector, None
    else:  # named detector; a dependency/model/config failure is a fixed code, never a fallback
        loaded = load_detector(args.detector, args.config)
        fn, th = loaded.fn, loaded.thresholds
    payload, res = run_pipeline(args.request_id, text, provider, fn, thresholds=th)
    out = {"payload": payload, "entity_counts": res.entity_counts()} if args.summary else payload
    stdout.write(json.dumps(out, ensure_ascii=False) + "\n")
    return 0


def _inspect(stdout, detector):
    text = DEV_001["text"]
    found = sorted((s["entity_type"], s["start"], s["end"]) for s in (detector or baseline_detector)(text))
    for t, a, b in found:
        stdout.write(f"{t} [{a}:{b}] {text[a:b]!r}\n")
    return 0


def _fmt(v):
    return "null" if v is None else f"{v:.4f}"


def _summary_lines(rep):
    m = rep["metrics"]
    lines = []
    for t in ENTITY_PRIORITY + ("micro",):
        b = m["micro"] if t == "micro" else m["per_type"][t]
        lines.append(f"{t:<14} TP={b['tp']} FP={b['fp']} FN={b['fn']} precision={_fmt(b['precision'])} "
                     f"recall={_fmt(b['recall'])} f1={_fmt(b['f1'])}")
    c = rep["coverage"]["overall"]
    lines.append(f"coverage       full={c['full']} partial={c['partial']} untouched={c['untouched']} rate={_fmt(c['coverage_rate'])}")
    b = rep["benign"]
    lines.append(f"benign         replacements_touching_benign={b['replacements_touching_benign']} "
                 f"replacements_touching_no_gold={b['replacements_touching_no_gold']} "
                 f"benign_characters_removed={b['benign_characters_removed']}")
    p = rep["preservation"]
    lines.append(f"preservation   no_gold_preserved={p['no_gold_examples_preserved']}/{p['examples_with_no_gold']} "
                 f"equal_expected={p['examples_equal_expected_sanitized']}/{p['examples_total']}")
    return lines


def _parse_thresholds(s):
    try:
        e, p, c = (float(x) for x in s.split(","))
    except Exception:
        raise SanitizerError(ERR_INVALID_ARGUMENTS) from None
    return validate_thresholds({"EMAIL_ADDRESS": e, "PHONE_NUMBER": p, "CUSTOMER_ID": c})


def _evaluate(args, stdout):
    from .evaluation import build_report, dump_report, load_fixture, run_meta, run_split

    split = args.split
    fx_path = FIXTURE_DIR / f"{split}.json"
    cfg_path = Path(args.config) if args.config else DEFAULT_CONFIG
    th, cfg_sha, extra = None, None, {}
    if args.debug_thresholds is not None:  # development-only debugging of the candidate
        if split != "development" or args.detector != "presidio":
            raise SanitizerError(ERR_INVALID_ARGUMENTS)
        th, extra = _parse_thresholds(args.debug_thresholds), {"debug_thresholds": True}
    elif split == "heldout" or args.detector == "presidio":
        # the held-out command REQUIRES the frozen config (for both detectors); the candidate always needs it
        if not cfg_path.is_file():
            raise SanitizerError(ERR_CONFIG_REQUIRED if split == "heldout" else ERR_INVALID_CONFIG)
        cfg = load_frozen_config(cfg_path)
        check_fixture_integrity(cfg)
        cfg_sha = file_sha256(cfg_path)
        th = cfg["thresholds"] if args.detector == "presidio" else dict(BASELINE_THRESHOLDS)
    else:  # baseline on development: fixed thresholds, no freeze needed
        th = dict(BASELINE_THRESHOLDS)
    fixture = load_fixture(fx_path)
    if args.detector == "baseline":
        fn = baseline_detector
    else:
        fn, _mod, _analyzer = build_presidio()
    records = run_split(fixture, lambda _ex: fn, th)
    report = build_report(run_meta(args.detector, split, file_sha256(fx_path), th, cfg_sha, extra), records)
    out = Path(args.out) if args.out else PROJECT_ROOT / "reports" / f"{split}_{args.detector}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(dump_report(report), encoding="utf-8", newline="\n")
    stdout.write(f"{args.detector} on {split} (thresholds {th}); report written\n")
    for line in _summary_lines(report):
        stdout.write(line + "\n")
    return 0


def _select_thresholds(args, stdout):
    from .freeze import build_frozen_config, write_frozen_config

    out = Path(args.out) if args.out else DEFAULT_CONFIG
    if out.exists() and not args.allow_refreeze:  # never silently re-freeze after the fact
        raise SanitizerError(ERR_INVALID_CONFIG)
    cfg = build_frozen_config(FIXTURE_DIR / "development.json", FIXTURE_DIR / "heldout.json",
                              PROJECT_ROOT / "requirements-presidio.txt")
    write_frozen_config(out, cfg)
    m = cfg["development_metrics_at_selected_thresholds"]["micro"]
    stdout.write(f"selected thresholds (development only): {cfg['thresholds']}\n")
    stdout.write(f"development micro: TP={m['tp']} FP={m['fp']} FN={m['fn']} precision={_fmt(m['precision'])} "
                 f"recall={_fmt(m['recall'])} f1={_fmt(m['f1'])}\n")
    stdout.write(f"configurations tied at top after the benign rule: {cfg['selection_tied_at_top_after_benign_rule']}\n")
    stdout.write("frozen config written (procedural freeze, not a blinded external evaluation)\n")
    return 0


def _demo(args, stdout):
    from .demo import run_demo

    return run_demo(lambda s="": stdout.write(s + "\n"), args.detector, args.config)


def main(argv=None, stdin=None, stdout=None, stderr=None, detector=None, provider=None):
    """stdin must be a binary stream (default: sys.stdin.buffer). `detector`/`provider` are injection
    points for tests of the `run` command only; the shipped CLI never passes them."""
    stdin = stdin or sys.stdin.buffer
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr
    provider = provider if provider is not None else RecordingMock()
    p = _Parser(prog="sanitizer")
    sub = p.add_subparsers(dest="cmd", required=True)  # subparsers reuse _Parser
    r = sub.add_parser("run")
    r.add_argument("--request-id", required=True)
    r.add_argument("--detector", choices=DETECTOR_NAMES, default="baseline")
    r.add_argument("--config", default=None)
    r.add_argument("--summary", action="store_true")
    sub.add_parser("inspect-fixture")
    d = sub.add_parser("demo")
    d.add_argument("--detector", choices=DETECTOR_NAMES, default="baseline")
    d.add_argument("--config", default=None)
    s = sub.add_parser("select-thresholds")
    s.add_argument("--out", default=None)
    s.add_argument("--allow-refreeze", action="store_true")
    e = sub.add_parser("evaluate")
    e.add_argument("--detector", choices=DETECTOR_NAMES, required=True)
    e.add_argument("--split", choices=("development", "heldout"), required=True)
    e.add_argument("--config", default=None)
    e.add_argument("--out", default=None)
    e.add_argument("--debug-thresholds", default=None)
    try:
        args = p.parse_args(argv)  # --help/-h still prints help and exits 0
    except SanitizerError as ex:
        stderr.write(ex.code + "\n")
        return EXIT_ERROR
    try:
        if args.cmd == "run":
            return _run(args, stdin, stdout, detector, provider)
        if args.cmd == "inspect-fixture":
            return _inspect(stdout, detector)
        if args.cmd == "demo":
            return _demo(args, stdout)
        if args.cmd == "select-thresholds":
            return _select_thresholds(args, stdout)
        return _evaluate(args, stdout)
    except SanitizerError as ex:
        code = ex.code
    except Exception:  # unexpected: never expose message or traceback
        log.error("rejected code=%s", ERR_INTERNAL)
        code = ERR_INTERNAL
    stderr.write(code + "\n")
    return EXIT_ERROR
