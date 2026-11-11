"""Shared test helpers. REQUIRE_CANDIDATE_TESTS=1 turns "Presidio or model missing" into a failure
instead of a skip (the CI candidate job sets it)."""
import importlib.util
import io
import logging
import os
import re
import unittest

from sanitizer.cli import main
from sanitizer.core import RecordingMock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMAIL = "ava@example.com"
CUST = "CUST-004271"
PHONE = "(415) 555-0132"
TEXT = "Email ava@example.com; customer CUST-004271; quantity 24."
REQUIRE_CANDIDATE = os.environ.get("REQUIRE_CANDIDATE_TESTS") == "1"
HAVE_PRESIDIO = (importlib.util.find_spec("presidio_analyzer") is not None
                 and importlib.util.find_spec("en_core_web_sm") is not None)
FROZEN_CONFIG = os.path.join(ROOT, "config", "frozen_config.json")
LOG_LINE_OK = re.compile(r"(INFO|WARNING|ERROR) sanitizer "
                         r"(dispatched chars=[0-9]+|rejected code=SANITIZER_[A-Z_]+)")


def require_candidate():
    """Call from setUpClass of every test that needs Presidio."""
    if HAVE_PRESIDIO:
        return
    if REQUIRE_CANDIDATE:
        raise AssertionError("Presidio / en_core_web_sm missing but REQUIRE_CANDIDATE_TESTS=1")
    raise unittest.SkipTest("presidio-analyzer / en_core_web_sm not installed")


class _ListHandler(logging.Handler):
    def __init__(self):
        super().__init__(logging.DEBUG)
        self.records = []

    def emit(self, record):
        self.records.append(record)


class LogCapture:
    """Handler on the ROOT logger at DEBUG: sees every record any library emits."""

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
        return [f"{r.levelname} {r.name}: {r.getMessage()}" for r in self.handler.records]

    @property
    def text(self):
        return "\n".join(self.lines)


def cli(argv, data=b"", provider=None):
    """Run the real CLI main() with NO injected detector. Returns (rc, stdout, stderr, provider)."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    out, err = io.StringIO(), io.StringIO()
    provider = provider if provider is not None else RecordingMock()
    rc = main(argv, io.BytesIO(data), out, err, None, provider)
    return rc, out.getvalue(), err.getvalue(), provider
