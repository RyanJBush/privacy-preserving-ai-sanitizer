"""Run the whole suite and FAIL if anything is skipped. Used by the CI candidate job (and locally).

    REQUIRE_CANDIDATE_TESTS=1 python scripts/run_tests_no_skips.py

A skipped candidate test is not candidate verification, so skips are treated as failures here.
"""
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.environ.setdefault("REQUIRE_CANDIDATE_TESTS", "1")
sys.path.insert(0, str(ROOT))


def main() -> int:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), top_level_dir=str(ROOT))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(f"\nran={result.testsRun} failures={len(result.failures)} errors={len(result.errors)} "
          f"skipped={len(result.skipped)}")
    if result.skipped:
        print("FAIL: skipped tests are not allowed in the candidate job:")
        for test, reason in result.skipped:
            print("  -", test.id(), "|", reason)
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
