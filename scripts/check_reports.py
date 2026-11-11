"""Re-run the evaluations and compare them with the committed reports (deterministic rerun check).

    python scripts/check_reports.py baseline            # stdlib only
    python scripts/check_reports.py baseline presidio   # needs the candidate environment

meta.python is ignored (the interpreter patch version is not part of the result). Everything else must
be byte-identical, including the frozen-config hash recorded in each report.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def normalized(path: Path):
    obj = json.loads(path.read_text(encoding="utf-8"))
    obj["meta"].pop("python", None)
    return json.dumps(obj, sort_keys=True, indent=2)


def main(detectors) -> int:
    bad = 0
    with tempfile.TemporaryDirectory() as d:
        for det in detectors:
            for split in ("development", "heldout"):
                out = Path(d) / f"{split}_{det}.json"
                p = subprocess.run([sys.executable, "-m", "sanitizer", "evaluate", "--detector", det, "--split", split,
                                    "--config", str(ROOT / "config" / "frozen_config.json"), "--out", str(out)],
                                   cwd=ROOT, capture_output=True, text=True)
                same = p.returncode == 0 and normalized(out) == normalized(ROOT / "reports" / f"{split}_{det}.json")
                print(f"{det:<9} {split:<12} rerun matches committed report: {same}")
                bad += 0 if same else 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or ["baseline"]))
