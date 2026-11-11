"""Detector selection. A dependency/model/config failure is a fixed code and never falls back."""
import contextlib
import importlib
import io
import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict

from .config import load_frozen_config
from .core import ENTITY_PRIORITY, ERR_DETECTOR_UNAVAILABLE, SanitizerError, baseline_detector

log = logging.getLogger("sanitizer")

DETECTOR_NAMES = ("baseline", "presidio")
BASELINE_THRESHOLDS = {t: 1.0 for t in ENTITY_PRIORITY}  # baseline scores are 1.0; threshold 1.0


@dataclass
class LoadedDetector:
    name: str
    fn: Callable[[str], Any]
    thresholds: Dict[str, float]


def build_presidio():
    """Import Presidio and load the model with no output leaking to the terminal.

    Returns (detector_fn, presidio_detector_module, analyzer). Any failure (missing package,
    missing model, bad config, ...) becomes ERR_DETECTOR_UNAVAILABLE with zero detail. There is
    no fallback to the baseline and no fallback to raw text.
    """
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            mod = importlib.import_module("sanitizer.presidio_detector")
            analyzer = mod.build_analyzer()
            return mod.make_detector(analyzer), mod, analyzer
    except Exception:
        log.error("rejected code=%s", ERR_DETECTOR_UNAVAILABLE)
        raise SanitizerError(ERR_DETECTOR_UNAVAILABLE) from None


def load_detector(name: str, config_path=None) -> LoadedDetector:
    if name == "baseline":
        return LoadedDetector("baseline", baseline_detector, dict(BASELINE_THRESHOLDS))
    if name == "presidio":
        cfg = load_frozen_config(config_path)  # missing/invalid config -> ERR_INVALID_CONFIG
        fn, _mod, _analyzer = build_presidio()
        return LoadedDetector("presidio", fn, cfg["thresholds"])
    raise SanitizerError(ERR_DETECTOR_UNAVAILABLE)
