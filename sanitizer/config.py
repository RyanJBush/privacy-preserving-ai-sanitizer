"""Frozen configuration: schema, loading, and integrity checks. Stdlib only."""
import hashlib
import json
import logging
import math
from pathlib import Path
from typing import Any, Dict

from .core import ENTITY_PRIORITY, ERR_INVALID_CONFIG, SanitizerError

log = logging.getLogger("sanitizer")

CONFIG_VERSION = 1
GRID = (0.0, 0.4, 0.6, 0.8, 1.0)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "frozen_config.json"
FIXTURE_DIR = PROJECT_ROOT / "fixtures"


def file_sha256(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _bad() -> SanitizerError:
    log.error("rejected code=%s", ERR_INVALID_CONFIG)
    return SanitizerError(ERR_INVALID_CONFIG)


def validate_thresholds(th: Any) -> Dict[str, float]:
    if not isinstance(th, dict) or set(th) != set(ENTITY_PRIORITY):
        raise _bad()
    out = {}
    for t in ENTITY_PRIORITY:
        v = th[t]
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not 0 <= v <= 1:
            raise _bad()
        out[t] = float(v)
    return out


def load_frozen_config(path=None) -> Dict[str, Any]:
    """Load and structurally validate a frozen config. Any problem -> fixed ERR_INVALID_CONFIG."""
    p = Path(path) if path is not None else DEFAULT_CONFIG
    try:
        cfg = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        raise _bad() from None
    try:
        ok = (isinstance(cfg, dict) and cfg.get("config_version") == CONFIG_VERSION
              and cfg.get("detector") == "presidio"
              and isinstance(cfg.get("development_sha256"), str)
              and isinstance(cfg.get("heldout_sha256"), str))
        if not ok:
            raise _bad()
        cfg["thresholds"] = validate_thresholds(cfg.get("thresholds"))
    except SanitizerError:
        raise
    except Exception:
        raise _bad() from None
    return cfg


def check_fixture_integrity(cfg: Dict[str, Any], fixture_dir=None) -> None:
    """The freeze must describe the fixtures on disk (byte hashes), else ERR_INVALID_CONFIG."""
    d = Path(fixture_dir) if fixture_dir is not None else FIXTURE_DIR
    try:
        if file_sha256(d / "development.json") != cfg["development_sha256"]:
            raise _bad()
        if file_sha256(d / "heldout.json") != cfg["heldout_sha256"]:
            raise _bad()
    except SanitizerError:
        raise
    except Exception:
        raise _bad() from None
