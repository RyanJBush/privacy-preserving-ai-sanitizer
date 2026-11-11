"""Exploratory dev-001 compatibility check. Run: python -m sanitizer.presidio_check [--stock-email]

--stock-email uses Presidio's unmodified EmailRecognizer (to reproduce its tldextract network attempt).

Explicit synthetic inspection: prints dev-001 text, spans and slices (the canaries) by design.
Uses only the in-memory RecordingMock. Makes no provider or gateway request. A socket guard
records (and blocks) any network attempt made while analyzing.
"""
import importlib.metadata as md
import logging
import os
import socket
import sys

import tldextract

from . import RecordingMock, dispatch
from .core import resolve_spans, validate_spans
from .fixture import CANARY_CUSTOMER, CANARY_EMAIL, DEV_001
from .core import ENTITY_PRIORITY as PRESIDIO_ENTITIES
from .presidio_detector import (LANGUAGE, SPACY_MODEL, build_analyzer,
                                make_detector)

EXPECTED_SANITIZED = "Email [EMAIL_ADDRESS]; customer [CUSTOMER_ID]; quantity 24."
EXPECTED_PAYLOAD = {"request_id": "demo-001", "text": EXPECTED_SANITIZED}


class _Records(logging.Handler):
    def __init__(self):
        super().__init__(logging.DEBUG)
        self.records = []

    def emit(self, record):
        self.records.append(record)


def _fmt(spans, text):
    return [f"{s['entity_type']} [{s['start']}:{s['end']}] score={s['score']!r} text={text[s['start']:s['end']]!r}"
            for s in sorted(spans, key=lambda s: (s["start"], s["end"], s["entity_type"]))]


def _cache_files():
    d = os.path.join(os.path.dirname(tldextract.__file__), ".suffix_cache")
    return sorted(os.path.relpath(os.path.join(r, f), d) for r, _, fs in os.walk(d) for f in fs) if os.path.isdir(d) else []


def main() -> int:
    stock = "--stock-email" in sys.argv[1:]
    text = DEV_001["text"]
    cache_before = _cache_files()
    print("== versions ==")
    print("python", sys.version.split()[0])
    print("email recognizer mode:", "STOCK (unmodified Presidio EmailRecognizer)" if stock else "offline-validated subclass")
    for pkg in ("presidio-analyzer", "spacy", "en-core-web-sm", "phonenumbers", "tldextract", "regex", "numpy", "thinc"):
        print(f"{pkg}=={md.version(pkg)}")

    handler = _Records()
    root = logging.getLogger()
    old_level = root.level
    root.addHandler(handler)
    root.setLevel(logging.DEBUG)

    attempts = []
    real_getaddrinfo, real_connect = socket.getaddrinfo, socket.socket.connect

    def blocked_getaddrinfo(host, *a, **k):
        attempts.append(f"getaddrinfo:{host}")
        raise OSError("network blocked by presidio_check")

    def blocked_connect(self, address):
        attempts.append(f"connect:{address[0] if isinstance(address, tuple) else address}")
        raise OSError("network blocked by presidio_check")

    socket.getaddrinfo, socket.socket.connect = blocked_getaddrinfo, blocked_connect  # covers model load too
    try:
        analyzer = build_analyzer(stock_email=stock)
        print("\n== loaded recognizers (registry.recognizers) ==")
        for r in analyzer.registry.recognizers:
            print(f"{r.name} | class={type(r).__name__} | entities={r.supported_entities} | lang={r.supported_language}")
        print("analyzer.get_supported_entities:", sorted(analyzer.get_supported_entities(LANGUAGE)))
        nlp = analyzer.nlp_engine
        print("nlp engine:", type(nlp).__name__, "| languages:", nlp.get_supported_languages(),
              "| spaCy pipeline:", nlp.nlp[LANGUAGE].pipe_names, "| model:", SPACY_MODEL)
        print("context enhancer:", type(analyzer.context_aware_enhancer).__name__,
              "| default_score_threshold:", analyzer.default_score_threshold)

        print("\n== dev-001 text ==")
        print(repr(text))

        print("\n== raw per-recognizer candidates (recognizer.analyze, before the engine's merge/context steps) ==")
        artifacts = nlp.process_text(text, LANGUAGE)
        for r in analyzer.registry.recognizers:
            raw = r.analyze(text, list(r.supported_entities), artifacts)
            spans = [{"entity_type": x.entity_type, "start": x.start, "end": x.end, "score": x.score} for x in raw]
            print(f"[{r.name}] {len(spans)} candidate(s)")
            for line in _fmt(spans, text):
                print("   ", line)

        print("\n== analyzer.analyze output (engine-level candidates passed to the sanitizer) ==")
        detector = make_detector(analyzer)
        engine_spans = detector(text)
        for line in _fmt(engine_spans, text):
            print("   ", line)

        print("\n== resolved spans (sanitizer validate + resolve, entities=%s) ==" % (PRESIDIO_ENTITIES,))
        resolved = resolve_spans(validate_spans(engine_spans, len(text), PRESIDIO_ENTITIES), PRESIDIO_ENTITIES)
        for line in _fmt(resolved, text):
            print("   ", line)

        print("\n== dispatch to RecordingMock ==")
        mock = RecordingMock()
        payload = dispatch("demo-001", text, mock, detector, PRESIDIO_ENTITIES)
    finally:
        socket.getaddrinfo, socket.socket.connect = real_getaddrinfo, real_connect
        root.removeHandler(handler)
        root.setLevel(old_level)

    print("sanitized text:", repr(payload["text"]))
    print("mock calls:", len(mock.calls))
    print("captured payload:", repr(mock.calls[0]))
    print("payload type:", type(mock.calls[0]).__name__, "| keys:", list(mock.calls[0]))
    ok_text = payload["text"] == EXPECTED_SANITIZED
    ok_payload = mock.calls[0] == EXPECTED_PAYLOAD
    clean = CANARY_EMAIL not in repr(mock.calls[0]) and CANARY_CUSTOMER not in repr(mock.calls[0])
    print(f"sanitized text equals dev-001 expectation: {ok_text}")
    print(f"payload equals dev-001 expected payload:   {ok_payload}")
    print(f"canaries absent from payload:              {clean}")

    print("\n== network attempts while building + analyzing (all blocked) ==")
    print(attempts or "none")
    print("tldextract site-packages cache files before/after:", len(cache_before), "/", len(_cache_files()))

    print("\n== log records emitted during analysis (root handler at DEBUG) ==")
    lines = [f"{r.levelname} {r.name}: {r.getMessage()}" for r in handler.records]
    print(f"{len(lines)} record(s)")
    for line in lines:
        print("   ", line)
    leaked = [l for l in lines if CANARY_EMAIL in l or CANARY_CUSTOMER in l or "quantity" in l]
    print("log records containing canaries or input text:", len(leaked))
    return 0 if (ok_text and ok_payload and clean) else 1


if __name__ == "__main__":
    sys.exit(main())
