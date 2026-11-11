# Privacy-preserving AI sanitizer (local MVP)

[![CI](https://github.com/RyanJBush/privacy-preserving-ai-sanitizer/actions/workflows/ci.yml/badge.svg)](https://github.com/RyanJBush/privacy-preserving-ai-sanitizer/actions)

A small Python layer that rewrites sensitive fields in text **before** it is handed to an LLM-provider
object. It redacts three synthetic-scope entity types and replaces each match with a placeholder such as
`[EMAIL_ADDRESS]`:

| Type | Scope (frozen, see [EVALUATION_CONTRACT](docs/handoff/EVALUATION_CONTRACT.md)) |
|---|---|
| `EMAIL_ADDRESS` | ASCII-shaped email fields (local part of letters, digits, `. _ % + -`; dotted ASCII domain; alphabetic final label of 2+ letters) |
| `PHONE_NUMBER` | exactly `(AAA) BBB-CCCC`, one ASCII space, `A` and the first `B` in 2-9. A syntax rule, not proof a number is assigned. Other phone formats are negatives for this narrow task |
| `CUSTOMER_ID` | case-sensitive `CUST-` + exactly six ASCII digits, not inside a longer letter/digit/underscore token |

Two detectors feed one shared pipeline:

- **`baseline`**: regular expressions, Python standard library only.
- **`presidio`** (candidate): Presidio's rule-based `EmailRecognizer` and `PhoneRecognizer` (US only) plus a custom
  `CUSTOMER_ID` regex, running on a spaCy small English model (`en_core_web_sm`). The NLP engine supplies tokens
  and lemmas for Presidio's context scoring. **No NER recognizer is registered. This is not a trained PII
  model**; it is rules plus context scoring.

> **What this is not.** Sanitized output can still contain sensitive fields the detector missed (see
> [Known errors](#known-errors)). This is a small synthetic template benchmark, not evidence of real-world
> performance. There is no gateway integration, no retry/fallback behavior, no real-provider call, no UI.
> The only provider is an in-memory `RecordingMock`.

## Pipeline (shared by `sanitize`, `dispatch`, the CLI and the evaluation)

validate request ID → size/UTF-8 checks → detector → **validate every span** → phone scope gate (a phone
candidate must have the exact `(start, end)` of a match of the scope regex; never repaired, trimmed or
synthesized) → frozen type thresholds (`score >= t`) → dedupe same type/range (highest score) → overlap
resolution (longest, then higher score, then `EMAIL_ADDRESS` → `PHONE_NUMBER` → `CUSTOMER_ID`, then earlier
start) → replace right to left → provider receives exactly `{"request_id", "text"}`.

Offsets are Python Unicode code-point indices, zero-based and end-exclusive. Nothing is normalized (Unicode,
CRLF, tabs, whitespace). Limits: 10,000 characters and 40,000 bytes, strict UTF-8.

## Setup, demo, evaluation (exact commands)

Tested locally on **Windows 11, Python 3.13.7, one machine**, and on one hosted Windows runner (`windows-latest`, Python 3.13.17; see [CI](#ci)). Other platforms are untested. Installation uses the
network (PyPI and one GitHub release asset); the tested inference path does not (see
[Dependency notes](#dependency-notes)).

All commands below are **PowerShell** (Windows PowerShell 5.1 and PowerShell 7 both work) and are run from the
project root. `evaluate` writes `reports/<split>_<detector>.json`; re-running it overwrites the committed report
with identical bytes.

Get the project:

```powershell
git clone https://github.com/RyanJBush/privacy-preserving-ai-sanitizer.git
Set-Location privacy-preserving-ai-sanitizer
```

Baseline only (no installs):

```powershell
python -m unittest discover -v
'Email ava@example.com; phone (415) 555-0132; customer CUST-004271.' | python -m sanitizer run --request-id demo-001
python -m sanitizer demo                                              # explicit SYNTHETIC inspection
python -m sanitizer evaluate --detector baseline --split development
python -m sanitizer evaluate --detector baseline --split heldout      # requires config/frozen_config.json
```

PowerShell appends a line break (`\r\n`) to a string it pipes into a program. The sanitizer does not normalize
whitespace, so the piped example above returns text ending in `\r\n`. To send exact bytes with no trailing line
break, write the input to a file and redirect it through `cmd` (PowerShell has no `<` operator):

```powershell
[System.IO.File]::WriteAllText((Join-Path $PWD "input.txt"), "Email ava@example.com; phone (415) 555-0132; customer CUST-004271.", (New-Object System.Text.UTF8Encoding $false))
cmd /c "python -m sanitizer run --request-id demo-001 < input.txt"
Remove-Item input.txt
```

Use ASCII text when piping from Windows PowerShell 5.1: its default pipe encoding is ASCII, which turns other
characters into `?` before the sanitizer sees them. The file form above sends UTF-8 in both versions.

Candidate (use a **short** venv path on Windows; a deep path made spaCy fail to load a DLL):

```powershell
$PV = "C:\pv"          # any SHORT path
python -m venv $PV
& "$PV\Scripts\python" -m pip install -r requirements-presidio.txt
& "$PV\Scripts\python" -m pip check
& "$PV\Scripts\python" scripts/run_tests_no_skips.py                  # fails if any test is skipped
'Email ava@example.com; phone (415) 555-0132; customer CUST-004271.' | & "$PV\Scripts\python" -m sanitizer run --detector presidio --summary --request-id demo-001
& "$PV\Scripts\python" -m sanitizer demo --detector presidio
& "$PV\Scripts\python" -m sanitizer evaluate --detector presidio --split development
& "$PV\Scripts\python" -m sanitizer evaluate --detector presidio --split heldout
& "$PV\Scripts\python" scripts/check_reports.py baseline presidio     # deterministic rerun check
```

CLI output: `run` prints the provider payload `{"request_id", "text"}` as one JSON line. `--summary` prints
`{"payload": {...}, "entity_counts": {...}}`; counts only, never matched values. Every failure prints one fixed
code and a newline on stderr, nothing on stdout, exit status 2 (`SANITIZER_INVALID_ARGUMENTS`,
`_INVALID_REQUEST_ID`, `_INPUT_TOO_LARGE`, `_INVALID_ENCODING`, `_DETECTOR_ERROR`, `_INVALID_DETECTOR_OUTPUT`,
`_DETECTOR_UNAVAILABLE`, `_INVALID_CONFIG`, `_FROZEN_CONFIG_REQUIRED`, `_INVALID_FIXTURE`, `_INTERNAL_ERROR`).
A missing dependency, missing model or bad config returns `SANITIZER_DETECTOR_UNAVAILABLE` or
`SANITIZER_INVALID_CONFIG` with zero dispatch: **there is no silent fallback to the baseline or to raw text.**
A provider that raises *after* being invoked yields `SANITIZER_INTERNAL_ERROR`; detector or validation failures
yield zero provider calls.

## Protocol: what was frozen, and when

1. Fixtures from the reviewer, placed unchanged and hash-checked: [development.json](fixtures/development.json)
   (10 examples; 7 email, 4 phone, 5 customer-ID gold spans) and [heldout.json](fixtures/heldout.json)
   (18 different example templates; 12 email, 8 phone, 8 customer-ID).
2. All debugging used development data only. Candidate thresholds were chosen from `{0,0.4,0.6,0.8,1}^3`
   (125 configurations, raw candidates cached once) on **development only**, by the contract's rule, and
   saved with recognizer settings, package/model versions and file hashes in
   [config/frozen_config.json](config/frozen_config.json). `heldout.json` was only hashed (bytes) before that file
   was written. **This is a procedural freeze, not a blinded external evaluation.**
3. Both detectors then ran on the held-out file with the frozen configuration; those runs produced the committed
   reports. **No held-out retuning occurred:** thresholds, recognizer settings, pipeline code and fixtures did not
   change afterwards. Later runs were **deterministic verification reruns** (a fresh-environment evaluation,
   `scripts/check_reports.py`, and a reviewer's reproduction of the baseline reports). They used the same frozen
   configuration and code and reproduced the committed reports byte for byte (the interpreter patch version is the
   only field the check ignores). The results are still a tiny synthetic split. The held-out command refuses to run
   without the frozen config.

## Results

Generated by `python scripts/render_summary.py --update-readme` from [reports/](reports/) (the JSON reports contain
IDs, types, scores, offsets and counts, never text). A test checks this block equals the reports.

<!-- SUMMARY:BEGIN -->

#### development (exact-span, after validation, scope gate, thresholds and overlap resolution)

| Detector | Type | TP | FP | FN | Precision | Recall | F1 |
|---|---|---:|---:|---:|---:|---:|---:|
| baseline | EMAIL_ADDRESS | 7 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| baseline | PHONE_NUMBER | 4 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| baseline | CUSTOMER_ID | 5 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| baseline | **micro** | 16 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| presidio | EMAIL_ADDRESS | 6 | 0 | 1 | 1.0000 | 0.8571 | 0.9231 |
| presidio | PHONE_NUMBER | 4 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| presidio | CUSTOMER_ID | 5 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| presidio | **micro** | 15 | 0 | 1 | 1.0000 | 0.9375 | 0.9677 |

| Detector | Gold fully covered | Partial | Untouched | Coverage rate | Replacements touching benign | Touching no gold | Benign chars removed | Benign-only examples preserved | Outputs equal oracle |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 16/16 | 0 | 0 | 1.0000 | 0 | 0 | 0 | 2/2 | 10/10 |
| presidio | 15/16 | 0 | 1 | 0.9375 | 0 | 0 | 0 | 2/2 | 9/10 |

| Detector | Examples dispatched | Provider calls | Payload is exactly {request_id, text} | Payload text equals actual sanitized text | Output rebuilt from applied spans |
|---|---:|---:|---:|---:|---:|
| baseline | 10 | 10 | 10 | 10 | 10 |
| presidio | 10 | 10 | 10 | 10 | 10 |

#### heldout (exact-span, after validation, scope gate, thresholds and overlap resolution)

| Detector | Type | TP | FP | FN | Precision | Recall | F1 |
|---|---|---:|---:|---:|---:|---:|---:|
| baseline | EMAIL_ADDRESS | 12 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| baseline | PHONE_NUMBER | 8 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| baseline | CUSTOMER_ID | 8 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| baseline | **micro** | 28 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| presidio | EMAIL_ADDRESS | 10 | 1 | 2 | 0.9091 | 0.8333 | 0.8696 |
| presidio | PHONE_NUMBER | 8 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| presidio | CUSTOMER_ID | 8 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| presidio | **micro** | 26 | 1 | 2 | 0.9630 | 0.9286 | 0.9455 |

| Detector | Gold fully covered | Partial | Untouched | Coverage rate | Replacements touching benign | Touching no gold | Benign chars removed | Benign-only examples preserved | Outputs equal oracle |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 28/28 | 0 | 0 | 1.0000 | 0 | 0 | 0 | 5/5 | 18/18 |
| presidio | 27/28 | 0 | 1 | 0.9643 | 1 | 0 | 5 | 5/5 | 16/18 |

| Detector | Examples dispatched | Provider calls | Payload is exactly {request_id, text} | Payload text equals actual sanitized text | Output rebuilt from applied spans |
|---|---:|---:|---:|---:|---:|
| baseline | 18 | 18 | 18 | 18 | 18 |
| presidio | 18 | 18 | 18 | 18 | 18 |

Frozen candidate thresholds (selected on development only): EMAIL_ADDRESS 1.0, PHONE_NUMBER 0.4, CUSTOMER_ID 1.0. Baseline: score 1.0, threshold 1.0 for all three types.

<!-- SUMMARY:END -->

Reading the numbers:

- **Primary metrics** score the spans actually applied (exact `(example, type, start, end)`; a wrong type or
  partial interval is one FP and one FN). **Coverage** is separate: a gold interval is fully covered if every
  character is inside some applied replacement, whatever its type.
- **The baseline's perfect score is expected and says little.** Its regexes implement the same syntax rules that
  define the gold labels, on a small template set. The comparison is a sanity check of the harness and a contrast
  with a differently-built detector, not a quality ranking.
- Provider-boundary columns are reported **separately from accuracy**. A miss is a detector/coverage failure; the
  payload still equals the actual sanitized text. The fixtures' `expected_sanitized` strings are an oracle for
  comparison only; they are never detector output or a provider input.

### Known errors

Observed on the held-out split (candidate; the baseline had none). Values are visible only via the explicit
`demo` command, which reads the held-out report and fixture.

- `test-010`: an email-shaped field with a `.invalid` suffix was not detected (gold FN, untouched). The offline
  public-suffix validator rejects suffixes absent from its snapshot. The contract defines such fields as
  sensitive, so this is a candidate miss, not a label problem. The same cause appeared on development (`dev-008`).
- `test-012`: Presidio's email pattern allows `=` in the local part, so the matched span began at a `key=` prefix
  (5 benign characters removed): one FP plus one FN at the exact-span level, although the real email is fully
  covered (partial-interval rule).
- 3 phone candidates in the held-out run were dropped by the scope gate (other phone formats), correctly by the
  contract; 0 were dropped by the threshold.

## Dependency notes

- Pinned in [requirements-presidio.txt](requirements-presidio.txt): `presidio-analyzer==2.2.366`, `spacy==3.8.18`,
  `en_core_web_sm` 3.8.0 (12,806,118 bytes, SHA-256 `1932429d…fb85`, hash-pinned), 52 packages in total.
- Stock Presidio `EmailRecognizer` validates through `tldextract`, which tries to download the Public Suffix List
  and writes a cache. The default here is an offline subclass that uses the suffix snapshot bundled in the wheel
  (no network, no cache; the snapshot can be stale). The stock recognizer is reachable only through the diagnostic
  `python -m sanitizer.presidio_check --stock-email`; it is not a CLI route.
- Presidio's DEBUG log records contain input text. `build_analyzer()` sets the `presidio-analyzer` logger to INFO,
  a **process-wide** setting, and tests assert nothing sensitive appears with a root logger at DEBUG. That protects
  only this tested configuration: it is not robust against an application that re-enables that logger's DEBUG level.
- Installation uses the network. The tested offline inference path makes no network attempts (socket-blocked test).

## Limitations

Tiny synthetic fixtures, three entity types, one narrow phone syntax, ASCII-shaped emails, English only, no
statistical claims, thresholds chosen on 10 examples (the frozen phone threshold equals the recognizer's base
score, so it has no margin), PHONE_NUMBER's position in the tie-break order is an agreed assumption. Only one
hosted platform (Windows, Python 3.13.17) and one local machine have been exercised. Gateway integration,
retries/fallbacks and real-provider behavior are out of scope and were not tested.

## CI

[.github/workflows/ci.yml](.github/workflows/ci.yml) defines a baseline job and a candidate job (the candidate
job sets `REQUIRE_CANDIDATE_TESTS=1`, fails if dependencies are absent and fails on any skipped test).

**Hosted CI status: passed.** [Run 42962482672](https://github.com/RyanJBush/privacy-preserving-ai-sanitizer/actions/runs/42962482672) on `windows-latest` (Python 3.13.17) tested commit
`02169e0cda9d454a1985947fcd124d1ed540a14c`, and both jobs succeeded. The repository and its CI logs are public.

Both jobs also passed on documentation commit `0c71e3acd2d37aa242126cde5e27c1f7d0d18e91`:
[Run 42964476226](https://github.com/RyanJBush/privacy-preserving-ai-sanitizer/actions/runs/42964476226).

| | Hosted run (commit `02169e0`) | Local (Windows 11, Python 3.13.7) |
|---|---|---|
| Baseline job / base interpreter | 132 tests run, 127 passed, **5 skipped**, 0 failed | 132 run, 128 passed, **4 skipped**, 0 failed |
| Candidate job / candidate venv | 154 run, **0 skipped**, 0 failed | 154 run, **0 skipped**, 0 failed |
| Deterministic rerun vs committed reports | baseline: matched (development, held-out); candidate: matched for both detectors | matched for both detectors |

The baseline job skips candidate tests because Presidio is not installed there. Each of 4 skipped entries is a whole
candidate test class; the hosted run has one more skip than the local run because its base Python has no PyYAML,
which skips the workflow-YAML structure test (the local base interpreter has PyYAML). The skips are not candidate
verification; the candidate job is the one that exercises them, with zero skips.

An earlier run on the first commit `add4bdb` ([run 42962280122](https://github.com/RyanJBush/privacy-preserving-ai-sanitizer/actions/runs/42962280122)) **failed**: the runner checked files
out with CRLF line endings, which changed the SHA-256 of the byte-verified fixtures (observed for `fixtures/development.json`: the CRLF
form hashes to the value the runner reported), so the byte-hash integrity checks failed (baseline: 1 failure, 2 errors; candidate: 2 failures, 2 errors). The fix commit
`02169e0` adds only `.gitattributes` (`* -text`, no line-ending conversion). No detector code, thresholds,
fixtures, reports or tests changed, and nothing was retuned against held-out data. Later documentation-only
commits trigger further runs; see the repository's Actions tab.

## Repository layout

- `sanitizer/`: `core.py` (pipeline), `detectors.py`, `presidio_detector.py`, `evaluation.py`, `freeze.py`,
  `config.py`, `demo.py`, `cli.py`
- `fixtures/`, `docs/handoff/` (unchanged reviewer files), `config/frozen_config.json`, `reports/`
- `tests/`, `scripts/`, `.github/workflows/ci.yml`, [WALKTHROUGH.md](WALKTHROUGH.md)

## Email pattern (baseline) and its limits

    (?<![\w.%+-])[A-Za-z0-9._%+-]+@(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}(?![\w-])    (ASCII flag)

ASCII only; not RFC 5322; requires a dotted domain with an alphabetic final label of 2+ letters; labels may start or
end with `-` and local parts may have consecutive dots (over-matches); obfuscated forms are not detected;
`xava@example.com` is matched whole while `a@b.com-x` and `a@b.com1` are not matched at all.

## Detector contract

`detector(text)` returns a list/tuple of dicts with exactly `entity_type`, `start`, `end`, `score`. Anything else
(generator, extra keys, bool offsets, non-finite or out-of-range score, unknown type) aborts dispatch as
`SANITIZER_INVALID_DETECTOR_OUTPUT`. Every span is validated **before** scope or threshold filtering. Request IDs
must fullmatch `(?:demo|req)-[0-9]{3,12}` and are never logged. Logs contain only `dispatched chars=<n>` or
`rejected code=<CODE>`.
