"""Sanitizer pipeline: detect -> validate ALL spans -> scope gate -> thresholds -> dedupe ->
resolve overlaps -> replace -> dispatch.

Stdlib only. No raw input, matched values, or exception text is ever logged
or placed in a raised error; failures expose only a fixed public code.
"""
import logging
import math
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Tuple

log = logging.getLogger("sanitizer")
# Library convention: without this, Python's last-resort handler would write
# WARNING+ records to stderr and break the "stderr is exactly the code" contract.
log.addHandler(logging.NullHandler())

MAX_INPUT_CHARS = 10_000
MAX_INPUT_BYTES = MAX_INPUT_CHARS * 4  # a UTF-8 character is at most 4 bytes

ERR_DETECTOR = "SANITIZER_DETECTOR_ERROR"
ERR_INVALID_OUTPUT = "SANITIZER_INVALID_DETECTOR_OUTPUT"
ERR_TOO_LARGE = "SANITIZER_INPUT_TOO_LARGE"
ERR_INVALID_ENCODING = "SANITIZER_INVALID_ENCODING"
ERR_INTERNAL = "SANITIZER_INTERNAL_ERROR"
ERR_INVALID_REQUEST_ID = "SANITIZER_INVALID_REQUEST_ID"
ERR_INVALID_ARGUMENTS = "SANITIZER_INVALID_ARGUMENTS"
ERR_DETECTOR_UNAVAILABLE = "SANITIZER_DETECTOR_UNAVAILABLE"  # dependency/model/config init failed
ERR_INVALID_CONFIG = "SANITIZER_INVALID_CONFIG"              # frozen config missing/invalid/mismatched
ERR_CONFIG_REQUIRED = "SANITIZER_FROZEN_CONFIG_REQUIRED"     # held-out evaluation without a freeze
ERR_INVALID_FIXTURE = "SANITIZER_INVALID_FIXTURE"

# MVP privacy boundary: request IDs are synthetic and carry no caller data.
REQUEST_ID_RE = re.compile(r"(?:demo|req)-[0-9]{3,12}")

# Scope: three types. Tuple order is also the overlap tie-break order.
ENTITY_PRIORITY = ("EMAIL_ADDRESS", "PHONE_NUMBER", "CUSTOMER_ID")
_SPAN_KEYS = frozenset(("entity_type", "start", "end", "score"))

# Baseline email pattern (ASCII only). See README for limitations.
EMAIL_RE = re.compile(
    r"(?<![\w.%+-])"                      # not in the middle of a longer token
    r"[A-Za-z0-9._%+-]+"                  # local part
    r"@"
    r"(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}"   # dotted domain, alphabetic TLD
    r"(?![\w-])",                         # not followed by more token chars
    re.ASCII,
)
# Case-sensitive CUST- + exactly six ASCII digits, not inside a longer token.
CUSTOMER_ID_RE = re.compile(r"(?<![A-Za-z0-9_])CUST-[0-9]{6}(?![A-Za-z0-9_])")
# Frozen phone scope: exactly "(AAA) BBB-CCCC", one ASCII space, A and first B in 2-9.
# A syntax rule, not validation that a number is assigned. Used by the baseline AND as the
# scope gate for every detector's phone candidates.
PHONE_SCOPE_RE = re.compile(r"(?<![A-Za-z0-9_])\([2-9][0-9]{2}\) [2-9][0-9]{2}-[0-9]{4}(?![A-Za-z0-9_])")


class SanitizerError(Exception):
    """Carries only a fixed public code; never input or underlying messages."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def decode_input(data: bytes) -> str:
    """Strict UTF-8 decode of at most MAX_INPUT_BYTES + 1 bytes read from a stream.

    More than MAX_INPUT_BYTES bytes is always too large (checked first, so such
    input is never decoded). Invalid UTF-8 is rejected, never replaced. A leading
    BOM is kept as U+FEFF; nothing is normalized.
    """
    if len(data) > MAX_INPUT_BYTES:
        log.warning("rejected code=%s", ERR_TOO_LARGE)
        raise SanitizerError(ERR_TOO_LARGE)
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        log.error("rejected code=%s", ERR_INVALID_ENCODING)  # message holds input bytes
        raise SanitizerError(ERR_INVALID_ENCODING) from None


def baseline_detector(text: str) -> List[Dict[str, Any]]:
    spans = []
    for etype, rx in (("EMAIL_ADDRESS", EMAIL_RE), ("PHONE_NUMBER", PHONE_SCOPE_RE),
                      ("CUSTOMER_ID", CUSTOMER_ID_RE)):
        for m in rx.finditer(text):
            spans.append({"entity_type": etype, "start": m.start(), "end": m.end(), "score": 1.0})
    return spans


def _is_int(v: Any) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def _is_score(v: Any) -> bool:
    if isinstance(v, bool):
        return False
    if isinstance(v, int):  # compare directly: math.isfinite(10**400) raises OverflowError
        return 0 <= v <= 1
    if isinstance(v, float):
        return math.isfinite(v) and 0 <= v <= 1
    return False


def validate_request_id(request_id: Any) -> None:
    """Fullmatch (?:demo|req)-[0-9]{3,12}; any other value or type is rejected, never echoed."""
    if type(request_id) is not str or REQUEST_ID_RE.fullmatch(request_id) is None:
        log.error("rejected code=%s", ERR_INVALID_REQUEST_ID)
        raise SanitizerError(ERR_INVALID_REQUEST_ID)


def validate_spans(spans: Any, text_len: int,
                   entities: Tuple[str, ...] = ENTITY_PRIORITY) -> List[Dict[str, Any]]:
    """Strict validation of EVERY span; any problem raises ERR_INVALID_OUTPUT with no detail.

    `entities` is the allowlist (default: the three scoped types)."""
    if not isinstance(spans, (list, tuple)):
        raise SanitizerError(ERR_INVALID_OUTPUT)
    for s in spans:
        if not isinstance(s, dict) or set(s) != _SPAN_KEYS:
            raise SanitizerError(ERR_INVALID_OUTPUT)
        t, a, b, sc = s["entity_type"], s["start"], s["end"], s["score"]
        if not isinstance(t, str) or t not in entities:
            raise SanitizerError(ERR_INVALID_OUTPUT)
        if not (_is_int(a) and _is_int(b) and 0 <= a < b <= text_len):
            raise SanitizerError(ERR_INVALID_OUTPUT)
        if not _is_score(sc):
            raise SanitizerError(ERR_INVALID_OUTPUT)
    return list(spans)


def resolve_spans(spans: Iterable[Dict[str, Any]],
                  entities: Tuple[str, ...] = ENTITY_PRIORITY) -> List[Dict[str, Any]]:
    """Dedupe same-type/same-range spans (keep the highest score), then keep non-overlapping ones.

    Priority: longest, higher score, position in `entities` (EMAIL_ADDRESS -> PHONE_NUMBER ->
    CUSTOMER_ID), earlier start. Result is sorted by start.
    """
    best: Dict[Tuple[str, int, int], Dict[str, Any]] = {}
    for s in spans:
        k = (s["entity_type"], s["start"], s["end"])
        if k not in best or s["score"] > best[k]["score"]:
            best[k] = s
    ranked = sorted(
        best.values(),
        key=lambda s: (-(s["end"] - s["start"]), -s["score"],
                       entities.index(s["entity_type"]), s["start"]),
    )
    kept: List[Dict[str, Any]] = []
    for s in ranked:
        if all(s["end"] <= k["start"] or s["start"] >= k["end"] for k in kept):
            kept.append(s)
    return sorted(kept, key=lambda s: s["start"])


def replace_spans(text: str, spans: Iterable[Dict[str, Any]]) -> str:
    for s in sorted(spans, key=lambda s: s["start"], reverse=True):  # right to left
        text = text[:s["start"]] + "[" + s["entity_type"] + "]" + text[s["end"]:]
    return text


@dataclass
class ProcessResult:
    """What the pipeline actually did. Holds offsets/scores only, never matched values."""
    sanitized: str
    applied: List[Dict[str, Any]]                       # spans actually replaced (original coordinates)
    validated: List[Dict[str, Any]] = field(default_factory=list)  # every validated candidate, pre-filter
    dropped_by_scope: int = 0
    dropped_by_threshold: int = 0

    def entity_counts(self) -> Dict[str, int]:
        return {t: sum(1 for s in self.applied if s["entity_type"] == t) for t in ENTITY_PRIORITY}


def process(text: str, detector: Callable[[str], Any] = None,
            entities: Tuple[str, ...] = ENTITY_PRIORITY,
            thresholds: Optional[Mapping[str, float]] = None) -> ProcessResult:
    """The single shared pipeline used by sanitize(), dispatch(), the CLI and the evaluation."""
    detector = baseline_detector if detector is None else detector
    if not isinstance(text, str):
        raise TypeError("text must be str")
    if len(text) > MAX_INPUT_CHARS:  # before any detection
        log.warning("rejected code=%s", ERR_TOO_LARGE)
        raise SanitizerError(ERR_TOO_LARGE)
    try:
        spans = detector(text)
    except Exception:
        log.error("rejected code=%s", ERR_DETECTOR)  # no exc_info: message may hold input
        raise SanitizerError(ERR_DETECTOR) from None
    try:
        valid = validate_spans(spans, len(text), entities)  # validate everything BEFORE filtering
    except Exception:  # SanitizerError, or anything a hostile detector output provokes
        log.error("rejected code=%s", ERR_INVALID_OUTPUT)
        raise SanitizerError(ERR_INVALID_OUTPUT) from None
    scope = {(m.start(), m.end()) for m in PHONE_SCOPE_RE.finditer(text)}
    in_scope = [s for s in valid
                if s["entity_type"] != "PHONE_NUMBER" or (s["start"], s["end"]) in scope]
    limits = thresholds or {}
    passing = [s for s in in_scope if s["score"] >= limits.get(s["entity_type"], 0.0)]
    applied = resolve_spans(passing, entities)
    return ProcessResult(
        sanitized=replace_spans(text, applied), applied=applied, validated=valid,
        dropped_by_scope=len(valid) - len(in_scope), dropped_by_threshold=len(in_scope) - len(passing),
    )


def sanitize(text: str, detector: Callable[[str], Any] = None,
             entities: Tuple[str, ...] = ENTITY_PRIORITY,
             thresholds: Optional[Mapping[str, float]] = None) -> str:
    return process(text, detector, entities, thresholds).sanitized


def run_pipeline(request_id: str, text: str, provider: Callable[[Dict[str, str]], Any],
                 detector: Callable[[str], Any] = None,
                 entities: Tuple[str, ...] = ENTITY_PRIORITY,
                 thresholds: Optional[Mapping[str, float]] = None) -> Tuple[Dict[str, str], ProcessResult]:
    """validate request_id -> process -> send exactly {"request_id", "text"} to the provider.

    request_id is validated first (before any detection). Any SanitizerError from validation
    or process() propagates before the provider is touched. A provider exception is replaced by
    ERR_INTERNAL (the provider HAS been invoked in that case); its message is never logged or
    re-raised.
    """
    validate_request_id(request_id)
    result = process(text, detector, entities, thresholds)
    payload = {"request_id": request_id, "text": result.sanitized}
    try:
        provider(payload)
    except Exception:
        log.error("rejected code=%s", ERR_INTERNAL)
        raise SanitizerError(ERR_INTERNAL) from None
    log.info("dispatched chars=%d", len(result.sanitized))  # no request_id, no text
    return payload, result


def dispatch(request_id: str, text: str, provider: Callable[[Dict[str, str]], Any],
             detector: Callable[[str], Any] = None,
             entities: Tuple[str, ...] = ENTITY_PRIORITY,
             thresholds: Optional[Mapping[str, float]] = None) -> Dict[str, str]:
    return run_pipeline(request_id, text, provider, detector, entities, thresholds)[0]


class RecordingMock:
    """In-memory provider: records the exact object it receives."""

    def __init__(self) -> None:
        self.calls: List[Any] = []

    def __call__(self, payload: Any) -> None:
        self.calls.append(payload)
