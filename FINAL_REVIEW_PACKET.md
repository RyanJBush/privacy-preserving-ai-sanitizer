# FINAL REVIEW PACKET: privacy-preserving AI sanitizer (local MVP)

## 1. Objective, status, and the one request

Objective: finish the agreed local MVP per `START_HERE.md` and `EVALUATION_CONTRACT.md` (supplied in
`sanitizer-final-handoff.zip`): three-entity baseline and candidate detectors behind one shared pipeline, shared
scoring, a development-only frozen threshold selection, one held-out comparison, a usable CLI and explicit synthetic
demo, boundary/logging tests for both detectors, basic CI configuration, README + walkthrough, and this packet with
the final ZIP, both from the same source revision.

**Request for ChatGPT:** independently review this packet (source, frozen config, reports, evidence, assumptions)
and reproduce the tests and evaluation with the commands in section 6. Please mark independently executed versus
Claude-reported evidence separately.

Not done and not claimed: hosted CI (**PENDING**, no run was executed), any platform other than Windows 11,
gateway integration / retries / fallbacks (**OUT OF SCOPE**), real-provider calls (none), blinded external
evaluation (this is a procedural freeze). Elapsed effort was not measured by me and is not reported.

## 2. Summary of results


- Tests: **baseline interpreter** (stdlib only): OK (skipped=4); discovered Ran 132 tests in 3.833s. The skipped entries are 4 whole candidate test classes that need Presidio. **Candidate environment, fresh venv, no skips allowed**: ran=154 failures=0 errors=0 skipped=0.

- Fresh-environment checks (same OS only): `pip check` rc=0; `pip freeze` equals the lock file: **True**; candidate development evaluation byte-identical on rerun: **True**; project files in the extracted ZIP byte-identical to the source tree: **True**.

- Held-out and development results (generated from `reports/*.json`; also in the README):

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


- Honest reading: the baseline's perfect scores are expected (its regexes encode the same syntax rules that define the
  labels, on a small template set). The candidate's held-out misses are one `.invalid`-suffix email (offline suffix
  validator) and one email whose span started at a `key=` prefix (exact-span FP + FN, though fully covered).

## 2a. Revision 2: documentation-only correction

Requested change: replace the README's mixed Bash/Windows input examples with commands that work in PowerShell,
label each block with its actual shell, run the exact replacement examples, and clarify the evaluation history.
Detector code, thresholds, fixtures and measured results are fixed.

- Files that differ from the previous final ZIP (excluding this packet): **README.md**; added: none; removed: none.
- README changes: (a) every command block is labelled `powershell` and is PowerShell syntax (`$PV`, the call operator `&`, a quoted string piped into `python`); (b) the Bash `printf ... |` examples are gone; (c) a documented exact-bytes form (write a file, then `cmd /c ... < input.txt`) for input without PowerShell's trailing line break; (d) a Windows PowerShell 5.1 vs PowerShell 7 input-encoding note; (e) the evaluation-history paragraph now says: no held-out retuning occurred, and later runs were deterministic verification reruns that reproduced the committed reports byte for byte.
- The README blocks were extracted programmatically and run UNMODIFIED except for the single `$PV = "C:\pv"` line, which was pointed at the existing fresh venv built from `requirements-presidio.txt` (the drive root was not written to). Both shells ran from the project root.
- Encoding behavior observed separately: PowerShell 7 pipes `Café ava@example.com` as UTF-8 plus a CRLF; Windows PowerShell 5.1 pipes `Caf? ava@example.com` plus CRLF (non-ASCII becomes `?`); the file + `cmd /c <` form sends UTF-8 with no trailing break in both, and the sanitizer returned `Café [EMAIL_ADDRESS]` in both.
- Measured results are unchanged: all four reports were byte-identical before and after running the README blocks in each shell.

README diff against the previous final ZIP:

````diff
--- a/README.md
+++ b/README.md
@@ -40,28 +40,46 @@
 network (PyPI and one GitHub release asset); the tested inference path does not (see
 [Dependency notes](#dependency-notes)).
 
+All commands below are **PowerShell** (Windows PowerShell 5.1 and PowerShell 7 both work) and are run from the
+project root. `evaluate` writes `reports/<split>_<detector>.json`; re-running it overwrites the committed report
+with identical bytes.
+
 Baseline only (no installs):
 
-```bash
+```powershell
 python -m unittest discover -v
-printf 'Email ava@example.com; phone (415) 555-0132; customer CUST-004271.' | python -m sanitizer run --request-id demo-001
-python -m sanitizer demo                      # explicit SYNTHETIC inspection
+'Email ava@example.com; phone (415) 555-0132; customer CUST-004271.' | python -m sanitizer run --request-id demo-001
+python -m sanitizer demo                                              # explicit SYNTHETIC inspection
 python -m sanitizer evaluate --detector baseline --split development
 python -m sanitizer evaluate --detector baseline --split heldout      # requires config/frozen_config.json
 ```
 
+PowerShell appends a line break (`\r\n`) to a string it pipes into a program. The sanitizer does not normalize
+whitespace, so the piped example above returns text ending in `\r\n`. To send exact bytes with no trailing line
+break, write the input to a file and redirect it through `cmd` (PowerShell has no `<` operator):
+
+```powershell
+[System.IO.File]::WriteAllText((Join-Path $PWD "input.txt"), "Email ava@example.com; phone (415) 555-0132; customer CUST-004271.", (New-Object System.Text.UTF8Encoding $false))
+cmd /c "python -m sanitizer run --request-id demo-001 < input.txt"
+Remove-Item input.txt
+```
+
+Use ASCII text when piping from Windows PowerShell 5.1: its default pipe encoding is ASCII, which turns other
+characters into `?` before the sanitizer sees them. The file form above sends UTF-8 in both versions.
+
 Candidate (use a **short** venv path on Windows; a deep path made spaCy fail to load a DLL):
 
-```bash
-python -m venv C:\pv
-C:\pv\Scripts\python -m pip install -r requirements-presidio.txt
-C:\pv\Scripts\python -m pip check
-C:\pv\Scripts\python scripts/run_tests_no_skips.py                    # fails if any test is skipped
-printf 'Email ava@example.com; phone (415) 555-0132; customer CUST-004271.' | C:\pv\Scripts\python -m sanitizer run --detector presidio --summary --request-id demo-001
-C:\pv\Scripts\python -m sanitizer demo --detector presidio
-C:\pv\Scripts\python -m sanitizer evaluate --detector presidio --split development
-C:\pv\Scripts\python -m sanitizer evaluate --detector presidio --split heldout
-C:\pv\Scripts\python scripts/check_reports.py baseline presidio       # deterministic rerun check
+```powershell
+$PV = "C:\pv"          # any SHORT path
+python -m venv $PV
+& "$PV\Scripts\python" -m pip install -r requirements-presidio.txt
+& "$PV\Scripts\python" -m pip check
+& "$PV\Scripts\python" scripts/run_tests_no_skips.py                  # fails if any test is skipped
+'Email ava@example.com; phone (415) 555-0132; customer CUST-004271.' | & "$PV\Scripts\python" -m sanitizer run --detector presidio --summary --request-id demo-001
+& "$PV\Scripts\python" -m sanitizer demo --detector presidio
+& "$PV\Scripts\python" -m sanitizer evaluate --detector presidio --split development
+& "$PV\Scripts\python" -m sanitizer evaluate --detector presidio --split heldout
+& "$PV\Scripts\python" scripts/check_reports.py baseline presidio     # deterministic rerun check
 ```
 
 CLI output: `run` prints the provider payload `{"request_id", "text"}` as one JSON line. `--summary` prints
@@ -84,9 +102,13 @@
    saved with recognizer settings, package/model versions and file hashes in
    [config/frozen_config.json](config/frozen_config.json). `heldout.json` was only hashed (bytes) before that file
    was written. **This is a procedural freeze, not a blinded external evaluation.**
-3. Both detectors then ran once on the held-out file with the frozen configuration. Nothing was retuned or
-   rerun after seeing the output, and no implementation change followed it, so these are the first-run held-out
-   results (still a tiny synthetic split). The held-out command refuses to run without the frozen config.
+3. Both detectors then ran on the held-out file with the frozen configuration; those runs produced the committed
+   reports. **No held-out retuning occurred:** thresholds, recognizer settings, pipeline code and fixtures did not
+   change afterwards. Later runs were **deterministic verification reruns** (a fresh-environment evaluation,
+   `scripts/check_reports.py`, and a reviewer's reproduction of the baseline reports). They used the same frozen
+   configuration and code and reproduced the committed reports byte for byte (the interpreter patch version is the
+   only field the check ignores). The results are still a tiny synthetic split. The held-out command refuses to run
+   without the frozen config.
 
 ## Results
 
````

Observed output of the README blocks, PowerShell 7.6.9:

````
shell: pwsh | blocks run: 3 | reports unchanged afterwards: True | input.txt left behind: False
--- README block 1 (first line: python -m unittest discover -v) exit status 0
{"request_id": "demo-001", "text": "Email [EMAIL_ADDRESS]; phone [PHONE_NUMBER]; customer [CUSTOMER_ID].\r\n"}
SYNTHETIC INSPECTION. Every value below is fabricated fixture data printed on purpose.
detector: baseline | thresholds: {'EMAIL_ADDRESS': 1.0, 'PHONE_NUMBER': 1.0, 'CUSTOMER_ID': 1.0}
baseline on development (thresholds {'EMAIL_ADDRESS': 1.0, 'PHONE_NUMBER': 1.0, 'CUSTOMER_ID': 1.0}); report written
EMAIL_ADDRESS  TP=7 FP=0 FN=0 precision=1.0000 recall=1.0000 f1=1.0000
PHONE_NUMBER   TP=4 FP=0 FN=0 precision=1.0000 recall=1.0000 f1=1.0000
CUSTOMER_ID    TP=5 FP=0 FN=0 precision=1.0000 recall=1.0000 f1=1.0000
micro          TP=16 FP=0 FN=0 precision=1.0000 recall=1.0000 f1=1.0000
coverage       full=16 partial=0 untouched=0 rate=1.0000
benign         replacements_touching_benign=0 replacements_touching_no_gold=0 benign_characters_removed=0
preservation   no_gold_preserved=2/2 equal_expected=10/10
baseline on heldout (thresholds {'EMAIL_ADDRESS': 1.0, 'PHONE_NUMBER': 1.0, 'CUSTOMER_ID': 1.0}); report written
EMAIL_ADDRESS  TP=12 FP=0 FN=0 precision=1.0000 recall=1.0000 f1=1.0000
PHONE_NUMBER   TP=8 FP=0 FN=0 precision=1.0000 recall=1.0000 f1=1.0000
CUSTOMER_ID    TP=8 FP=0 FN=0 precision=1.0000 recall=1.0000 f1=1.0000
micro          TP=28 FP=0 FN=0 precision=1.0000 recall=1.0000 f1=1.0000
coverage       full=28 partial=0 untouched=0 rate=1.0000
benign         replacements_touching_benign=0 replacements_touching_no_gold=0 benign_characters_removed=0
preservation   no_gold_preserved=5/5 equal_expected=18/18
Ran 132 tests in 4.053s
OK (skipped=4)
--- README block 2 (first line: [System.IO.File]::WriteAllText((Join-Path $PWD "input.txt"),) exit status 0
stdout (exact-bytes form, no trailing line break): '{"request_id": "demo-001", "text": "Email [EMAIL_ADDRESS]; phone [PHONE_NUMBER]; customer [CUSTOMER_ID]."}\n'
--- README block 3 (first line: $PV = "C:\pv"          # any SHORT path) exit status 0
No broken requirements found.
ran=154 failures=0 errors=0 skipped=0
{"payload": {"request_id": "demo-001", "text": "Email [EMAIL_ADDRESS]; phone [PHONE_NUMBER]; customer [CUSTOMER_ID].\r\n"}, "entity_counts": {"EMAIL_ADDRESS": 1, "PHONE_NUMBER": 1, "CUSTOMER_ID": 1}}
SYNTHETIC INSPECTION. Every value below is fabricated fixture data printed on purpose.
detector: presidio | thresholds: {'EMAIL_ADDRESS': 1.0, 'PHONE_NUMBER': 0.4, 'CUSTOMER_ID': 1.0}
presidio on development (thresholds {'EMAIL_ADDRESS': 1.0, 'PHONE_NUMBER': 0.4, 'CUSTOMER_ID': 1.0}); report written
EMAIL_ADDRESS  TP=6 FP=0 FN=1 precision=1.0000 recall=0.8571 f1=0.9231
PHONE_NUMBER   TP=4 FP=0 FN=0 precision=1.0000 recall=1.0000 f1=1.0000
CUSTOMER_ID    TP=5 FP=0 FN=0 precision=1.0000 recall=1.0000 f1=1.0000
micro          TP=15 FP=0 FN=1 precision=1.0000 recall=0.9375 f1=0.9677
coverage       full=15 partial=0 untouched=1 rate=0.9375
benign         replacements_touching_benign=0 replacements_touching_no_gold=0 benign_characters_removed=0
preservation   no_gold_preserved=2/2 equal_expected=9/10
presidio on heldout (thresholds {'EMAIL_ADDRESS': 1.0, 'PHONE_NUMBER': 0.4, 'CUSTOMER_ID': 1.0}); report written
EMAIL_ADDRESS  TP=10 FP=1 FN=2 precision=0.9091 recall=0.8333 f1=0.8696
PHONE_NUMBER   TP=8 FP=0 FN=0 precision=1.0000 recall=1.0000 f1=1.0000
CUSTOMER_ID    TP=8 FP=0 FN=0 precision=1.0000 recall=1.0000 f1=1.0000
micro          TP=26 FP=1 FN=2 precision=0.9630 recall=0.9286 f1=0.9455
coverage       full=27 partial=0 untouched=1 rate=0.9643
benign         replacements_touching_benign=1 replacements_touching_no_gold=0 benign_characters_removed=5
preservation   no_gold_preserved=5/5 equal_expected=16/18
baseline  development  rerun matches committed report: True
baseline  heldout      rerun matches committed report: True
presidio  development  rerun matches committed report: True
presidio  heldout      rerun matches committed report: True
Ran 154 tests in 10.474s
OK
````

Observed output of the README blocks, Windows PowerShell 5.1.26100:

````
shell: powershell | blocks run: 3 | reports unchanged afterwards: True | input.txt left behind: False
--- README block 1 (first line: python -m unittest discover -v) exit status 0
{"request_id": "demo-001", "text": "Email [EMAIL_ADDRESS]; phone [PHONE_NUMBER]; customer [CUSTOMER_ID].\r\n"}
SYNTHETIC INSPECTION. Every value below is fabricated fixture data printed on purpose.
detector: baseline | thresholds: {'EMAIL_ADDRESS': 1.0, 'PHONE_NUMBER': 1.0, 'CUSTOMER_ID': 1.0}
baseline on development (thresholds {'EMAIL_ADDRESS': 1.0, 'PHONE_NUMBER': 1.0, 'CUSTOMER_ID': 1.0}); report written
EMAIL_ADDRESS  TP=7 FP=0 FN=0 precision=1.0000 recall=1.0000 f1=1.0000
PHONE_NUMBER   TP=4 FP=0 FN=0 precision=1.0000 recall=1.0000 f1=1.0000
CUSTOMER_ID    TP=5 FP=0 FN=0 precision=1.0000 recall=1.0000 f1=1.0000
micro          TP=16 FP=0 FN=0 precision=1.0000 recall=1.0000 f1=1.0000
coverage       full=16 partial=0 untouched=0 rate=1.0000
benign         replacements_touching_benign=0 replacements_touching_no_gold=0 benign_characters_removed=0
preservation   no_gold_preserved=2/2 equal_expected=10/10
baseline on heldout (thresholds {'EMAIL_ADDRESS': 1.0, 'PHONE_NUMBER': 1.0, 'CUSTOMER_ID': 1.0}); report written
EMAIL_ADDRESS  TP=12 FP=0 FN=0 precision=1.0000 recall=1.0000 f1=1.0000
PHONE_NUMBER   TP=8 FP=0 FN=0 precision=1.0000 recall=1.0000 f1=1.0000
CUSTOMER_ID    TP=8 FP=0 FN=0 precision=1.0000 recall=1.0000 f1=1.0000
micro          TP=28 FP=0 FN=0 precision=1.0000 recall=1.0000 f1=1.0000
coverage       full=28 partial=0 untouched=0 rate=1.0000
benign         replacements_touching_benign=0 replacements_touching_no_gold=0 benign_characters_removed=0
preservation   no_gold_preserved=5/5 equal_expected=18/18
Ran 132 tests in 3.682s
OK (skipped=4)
--- README block 2 (first line: [System.IO.File]::WriteAllText((Join-Path $PWD "input.txt"),) exit status 0
stdout (exact-bytes form, no trailing line break): '{"request_id": "demo-001", "text": "Email [EMAIL_ADDRESS]; phone [PHONE_NUMBER]; customer [CUSTOMER_ID]."}\n'
--- README block 3 (first line: $PV = "C:\pv"          # any SHORT path) exit status 0
No broken requirements found.
ran=154 failures=0 errors=0 skipped=0
{"payload": {"request_id": "demo-001", "text": "Email [EMAIL_ADDRESS]; phone [PHONE_NUMBER]; customer [CUSTOMER_ID].\r\n"}, "entity_counts": {"EMAIL_ADDRESS": 1, "PHONE_NUMBER": 1, "CUSTOMER_ID": 1}}
SYNTHETIC INSPECTION. Every value below is fabricated fixture data printed on purpose.
detector: presidio | thresholds: {'EMAIL_ADDRESS': 1.0, 'PHONE_NUMBER': 0.4, 'CUSTOMER_ID': 1.0}
presidio on development (thresholds {'EMAIL_ADDRESS': 1.0, 'PHONE_NUMBER': 0.4, 'CUSTOMER_ID': 1.0}); report written
EMAIL_ADDRESS  TP=6 FP=0 FN=1 precision=1.0000 recall=0.8571 f1=0.9231
PHONE_NUMBER   TP=4 FP=0 FN=0 precision=1.0000 recall=1.0000 f1=1.0000
CUSTOMER_ID    TP=5 FP=0 FN=0 precision=1.0000 recall=1.0000 f1=1.0000
micro          TP=15 FP=0 FN=1 precision=1.0000 recall=0.9375 f1=0.9677
coverage       full=15 partial=0 untouched=1 rate=0.9375
benign         replacements_touching_benign=0 replacements_touching_no_gold=0 benign_characters_removed=0
preservation   no_gold_preserved=2/2 equal_expected=9/10
presidio on heldout (thresholds {'EMAIL_ADDRESS': 1.0, 'PHONE_NUMBER': 0.4, 'CUSTOMER_ID': 1.0}); report written
EMAIL_ADDRESS  TP=10 FP=1 FN=2 precision=0.9091 recall=0.8333 f1=0.8696
PHONE_NUMBER   TP=8 FP=0 FN=0 precision=1.0000 recall=1.0000 f1=1.0000
CUSTOMER_ID    TP=8 FP=0 FN=0 precision=1.0000 recall=1.0000 f1=1.0000
micro          TP=26 FP=1 FN=2 precision=0.9630 recall=0.9286 f1=0.9455
coverage       full=27 partial=0 untouched=1 rate=0.9643
benign         replacements_touching_benign=1 replacements_touching_no_gold=0 benign_characters_removed=5
preservation   no_gold_preserved=5/5 equal_expected=16/18
baseline  development  rerun matches committed report: True
baseline  heldout      rerun matches committed report: True
presidio  development  rerun matches committed report: True
presidio  heldout      rerun matches committed report: True
Ran 154 tests in 9.358s
OK
````


## 3. Handoff checklist (START_HERE steps 1-10)

| # | Requirement | Status / evidence |
|---|---|---|
| 1 | Preserve behavior/tests; add fixtures unchanged; baseline phone; US-only candidate phone + shared scope gate; validate before filtering; keep offline email and request-ID/error contracts | Done. Fixtures byte-identical to the handoff manifest (`tests/test_scoring.py::test_fixtures_are_the_unchanged_handoff_files`). One baseline test was edited because the scope changed: the "unknown entity" case used `PHONE_NUMBER` as its invalid example; it now uses `PERSON`. Everything else in `tests/test_sanitizer.py` is unchanged (see the diff in section 4). |
| 2 | Shared scoring/reporting; hand-calculated oracle; empty, wrong-type, adjacent, repeated, Unicode cases | Done: `sanitizer/evaluation.py`, `tests/test_scoring.py` (oracle: TP=0 FP=3 FN=2, coverage 0.5, benign 2/1/3 reproduced). |
| 3 | Thresholds on development only; save `frozen_config.json`; hash held-out without inspecting; procedural-freeze note; held-out command requires the config | Done: `config/frozen_config.json` (section 7). `heldout.json` was only hashed before the freeze. `evaluate --split heldout` fails with `SANITIZER_FROZEN_CONFIG_REQUIRED` without it (test + F8). |
| 4 | Run both detectors on the same held-out examples; aggregate + privacy-safe diagnostics; no retuning | Done once, after the freeze: `reports/heldout_*.json`. No rerun or code change followed. |
| 5 | CLI for both detectors; counts without raw values; provider object exactly `{request_id, text}`; fixed error-only stderr; init failure = fixed code, zero dispatch, no fallback | Done (`run --detector baseline|presidio [--summary] [--config]`). Default behavior unchanged. Missing dependency / init failure / bad config tests (in-process, real process, with canaries in the exception). |
| 6 | Explicit synthetic `demo` | Done (F4, F14): canary, benign, Unicode, repeated, CRLF/tab, detector failure with zero calls, actual held-out miss and unnecessary redaction. No user-text path, no real-provider route. |
| 7 | Provider-boundary and logging tests for both detectors; phone canary; type-priority ties; missing-dependency CLI; no production failure-injection switch | Done: `tests/test_detectors_boundary.py`, `tests/test_pipeline.py`, `tests/test_cli.py`. Accuracy and boundary results are reported separately. No injection switch exists in `sanitizer/`. |
| 8 | GitHub Actions for baseline and candidate; candidate fails on missing deps or skips; run equivalent commands locally; fresh env following README | Workflow written. Equivalent commands run locally in a fresh venv (F9-F17). **Hosted CI: PENDING.** The README uses `C:\pv`; the fresh run used an equivalent short path inside the session folder (it did not write to the drive root). |
| 9 | README rewrite, WALKTHROUGH.md, modest resume bullets from measured results | Done. README results block is generated from the reports and checked by a test. |
| 10 | Final ZIP and ONE packet from the same revision; regenerated hashes; diff or "all files new" | Done. No git repository exists here, so section 4 is a diff against the previous exported ZIP. Manifest in section 11. |

## 4. Files changed

**Modified since the previous export:** `README.md`, `sanitizer/cli.py`, `sanitizer/core.py`, `sanitizer/fixture.py`, `sanitizer/presidio_check.py`, `sanitizer/presidio_detector.py`, `tests/test_presidio_optional.py`, `tests/test_sanitizer.py`.

**New files:** `.github/workflows/ci.yml`, `.gitignore`, `WALKTHROUGH.md`, `config/frozen_config.json`, `docs/handoff/EVALUATION_CONTRACT.md`, `docs/handoff/MANIFEST.json`, `docs/handoff/START_HERE.md`, `docs/handoff/fixture_summary.json`, `fixtures/development.json`, `fixtures/fixture_summary.json`, `fixtures/heldout.json`, `reports/SUMMARY.md`, `reports/development_baseline.json`, `reports/development_presidio.json`, `reports/heldout_baseline.json`, `reports/heldout_presidio.json`, `sanitizer/config.py`, `sanitizer/demo.py`, `sanitizer/detectors.py`, `sanitizer/evaluation.py`, `sanitizer/freeze.py`, `scripts/check_reports.py`, `scripts/render_summary.py`, `scripts/run_tests_no_skips.py`, `tests/support.py`, `tests/test_cli.py`, `tests/test_detectors_boundary.py`, `tests/test_docs.py`, `tests/test_frozen_config.py`, `tests/test_pipeline.py`, `tests/test_scoring.py`.

**Removed from the project root:** previous exports and diff files (none).

Unified diff of the modified files against the previous exported ZIP (`a/` previous, `b/` now). New files appear in full in section 9.

````diff
--- a/README.md
+++ b/README.md
@@ -1,79 +1,244 @@
-# Baseline sanitizer (milestone 1)
-
-Stdlib-only. Python 3.13.7 was used; older versions are untested.
-
-    python -m unittest discover -v
-    printf '<text>' | python -m sanitizer run --request-id demo-001
-    python -m sanitizer inspect-fixture      # explicit synthetic view; prints dev-001 text
-
-Flow: stdin bytes (max 40,001 read) -> strict UTF-8 decode -> 10,000-character
-check -> detector -> strict span validation -> dedupe/overlap resolution ->
-right-to-left replacement -> provider gets exactly `{"request_id", "text"}`.
-
-Errors expose only fixed codes; CLI exit status 2, stdout empty, stderr is
-exactly `<CODE>\n`:
-
-| Code | Cause |
+# Privacy-preserving AI sanitizer (local MVP)
+
+A small Python layer that rewrites sensitive fields in text **before** it is handed to an LLM-provider
+object. It redacts three synthetic-scope entity types and replaces each match with a placeholder such as
+`[EMAIL_ADDRESS]`:
+
+| Type | Scope (frozen, see [EVALUATION_CONTRACT](docs/handoff/EVALUATION_CONTRACT.md)) |
 |---|---|
-| `SANITIZER_INPUT_TOO_LARGE` | more than 40,000 bytes (checked before decoding), or more than 10,000 characters |
-| `SANITIZER_INVALID_ENCODING` | stdin is not valid UTF-8 (rejected, never replaced) |
-| `SANITIZER_DETECTOR_ERROR` | detector raised |
-| `SANITIZER_INVALID_DETECTOR_OUTPUT` | detector returned malformed spans |
-| `SANITIZER_INTERNAL_ERROR` | provider or any other unexpected exception (the provider may already have been called) |
-| `SANITIZER_INVALID_REQUEST_ID` | `request_id` is not a `str` fullmatching `(?:demo\|req)-[0-9]{3,12}` (checked first, before stdin is read) |
-| `SANITIZER_INVALID_ARGUMENTS` | command-line parse failure; argument values are never echoed |
-
-`--help` / `-h` keep argparse's normal behavior (usage on stdout, exit 0).
-
-Request IDs are synthetic by design (MVP privacy boundary): the library
-(`dispatch`) and the CLI both reject anything else before detection or dispatch,
-and the value is never logged.
-
-Logs (logger `sanitizer`, NullHandler by default) contain only
-`dispatched chars=<n>` or `rejected code=<CODE>`: no request_id, text, or exception text.
-
-Detector scores must be `int` or `float` (not `bool`) in `[0, 1]`; huge ints,
-NaN and infinities are invalid detector output.
-
-## Baseline patterns
-
-Customer ID: `(?<![A-Za-z0-9_])CUST-[0-9]{6}(?![A-Za-z0-9_])`, case-sensitive.
-
-Email (ASCII flag):
-
-    (?<![\w.%+-])[A-Za-z0-9._%+-]+@(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}(?![\w-])
-
-Email limitations:
-- ASCII only: internationalized local parts and IDN domains are missed.
-- Not RFC 5322: quoted local parts, comments, and IP-literal domains are missed.
-- Requires a dotted domain with an alphabetic TLD of 2+ letters (`a@localhost` is not matched).
-- Labels may start/end with `-` and local parts may have consecutive dots (over-matches).
-- A trailing sentence period is excluded; an address glued to adjacent non-ASCII letters may match.
-- Obfuscated forms (`ava [at] example.com`) are not detected.
-- Boundary lookarounds: `xava@example.com` is matched whole (the token starts at `x`); `a@b.com-x` and `a@b.com1` are not matched at all.
+| `EMAIL_ADDRESS` | ASCII-shaped email fields (local part of letters, digits, `. _ % + -`; dotted ASCII domain; alphabetic final label of 2+ letters) |
+| `PHONE_NUMBER` | exactly `(AAA) BBB-CCCC`, one ASCII space, `A` and the first `B` in 2-9. A syntax rule, not proof a number is assigned. Other phone formats are negatives for this narrow task |
+| `CUSTOMER_ID` | case-sensitive `CUST-` + exactly six ASCII digits, not inside a longer letter/digit/underscore token |
+
+Two detectors feed one shared pipeline:
+
+- **`baseline`**: regular expressions, Python standard library only.
+- **`presidio`** (candidate): Presidio's rule-based `EmailRecognizer` and `PhoneRecognizer` (US only) plus a custom
+  `CUSTOMER_ID` regex, running on a spaCy small English model (`en_core_web_sm`). The NLP engine supplies tokens
+  and lemmas for Presidio's context scoring. **No NER recognizer is registered. This is not a trained PII
+  model**; it is rules plus context scoring.
+
+> **What this is not.** Sanitized output can still contain sensitive fields the detector missed (see
+> [Known errors](#known-errors)). This is a small synthetic template benchmark, not evidence of real-world
+> performance. There is no gateway integration, no retry/fallback behavior, no real-provider call, no UI.
+> The only provider is an in-memory `RecordingMock`.
+
+## Pipeline (shared by `sanitize`, `dispatch`, the CLI and the evaluation)
+
+validate request ID → size/UTF-8 checks → detector → **validate every span** → phone scope gate (a phone
+candidate must have the exact `(start, end)` of a match of the scope regex; never repaired, trimmed or
+synthesized) → frozen type thresholds (`score >= t`) → dedupe same type/range (highest score) → overlap
+resolution (longest, then higher score, then `EMAIL_ADDRESS` → `PHONE_NUMBER` → `CUSTOMER_ID`, then earlier
+start) → replace right to left → provider receives exactly `{"request_id", "text"}`.
+
+Offsets are Python Unicode code-point indices, zero-based and end-exclusive. Nothing is normalized (Unicode,
+CRLF, tabs, whitespace). Limits: 10,000 characters and 40,000 bytes, strict UTF-8.
+
+## Setup, demo, evaluation (exact commands)
+
+Tested on **Windows 11, Python 3.13.7, one machine**. Other platforms are untested. Installation uses the
+network (PyPI and one GitHub release asset); the tested inference path does not (see
+[Dependency notes](#dependency-notes)).
+
+All commands below are **PowerShell** (Windows PowerShell 5.1 and PowerShell 7 both work) and are run from the
+project root. `evaluate` writes `reports/<split>_<detector>.json`; re-running it overwrites the committed report
+with identical bytes.
+
+Baseline only (no installs):
+
+```powershell
+python -m unittest discover -v
+'Email ava@example.com; phone (415) 555-0132; customer CUST-004271.' | python -m sanitizer run --request-id demo-001
+python -m sanitizer demo                                              # explicit SYNTHETIC inspection
+python -m sanitizer evaluate --detector baseline --split development
+python -m sanitizer evaluate --detector baseline --split heldout      # requires config/frozen_config.json
+```
+
+PowerShell appends a line break (`\r\n`) to a string it pipes into a program. The sanitizer does not normalize
+whitespace, so the piped example above returns text ending in `\r\n`. To send exact bytes with no trailing line
+break, write the input to a file and redirect it through `cmd` (PowerShell has no `<` operator):
+
+```powershell
+[System.IO.File]::WriteAllText((Join-Path $PWD "input.txt"), "Email ava@example.com; phone (415) 555-0132; customer CUST-004271.", (New-Object System.Text.UTF8Encoding $false))
+cmd /c "python -m sanitizer run --request-id demo-001 < input.txt"
+Remove-Item input.txt
+```
+
+Use ASCII text when piping from Windows PowerShell 5.1: its default pipe encoding is ASCII, which turns other
+characters into `?` before the sanitizer sees them. The file form above sends UTF-8 in both versions.
+
+Candidate (use a **short** venv path on Windows; a deep path made spaCy fail to load a DLL):
+
+```powershell
+$PV = "C:\pv"          # any SHORT path
+python -m venv $PV
+& "$PV\Scripts\python" -m pip install -r requirements-presidio.txt
+& "$PV\Scripts\python" -m pip check
+& "$PV\Scripts\python" scripts/run_tests_no_skips.py                  # fails if any test is skipped
+'Email ava@example.com; phone (415) 555-0132; customer CUST-004271.' | & "$PV\Scripts\python" -m sanitizer run --detector presidio --summary --request-id demo-001
+& "$PV\Scripts\python" -m sanitizer demo --detector presidio
+& "$PV\Scripts\python" -m sanitizer evaluate --detector presidio --split development
+& "$PV\Scripts\python" -m sanitizer evaluate --detector presidio --split heldout
+& "$PV\Scripts\python" scripts/check_reports.py baseline presidio     # deterministic rerun check
+```
+
+CLI output: `run` prints the provider payload `{"request_id", "text"}` as one JSON line. `--summary` prints
+`{"payload": {...}, "entity_counts": {...}}`; counts only, never matched values. Every failure prints one fixed
+code and a newline on stderr, nothing on stdout, exit status 2 (`SANITIZER_INVALID_ARGUMENTS`,
+`_INVALID_REQUEST_ID`, `_INPUT_TOO_LARGE`, `_INVALID_ENCODING`, `_DETECTOR_ERROR`, `_INVALID_DETECTOR_OUTPUT`,
+`_DETECTOR_UNAVAILABLE`, `_INVALID_CONFIG`, `_FROZEN_CONFIG_REQUIRED`, `_INVALID_FIXTURE`, `_INTERNAL_ERROR`).
+A missing dependency, missing model or bad config returns `SANITIZER_DETECTOR_UNAVAILABLE` or
+`SANITIZER_INVALID_CONFIG` with zero dispatch: **there is no silent fallback to the baseline or to raw text.**
+A provider that raises *after* being invoked yields `SANITIZER_INTERNAL_ERROR`; detector or validation failures
+yield zero provider calls.
+
+## Protocol: what was frozen, and when
+
+1. Fixtures from the reviewer, placed unchanged and hash-checked: [development.json](fixtures/development.json)
+   (10 examples; 7 email, 4 phone, 5 customer-ID gold spans) and [heldout.json](fixtures/heldout.json)
+   (18 different example templates; 12 email, 8 phone, 8 customer-ID).
+2. All debugging used development data only. Candidate thresholds were chosen from `{0,0.4,0.6,0.8,1}^3`
+   (125 configurations, raw candidates cached once) on **development only**, by the contract's rule, and
+   saved with recognizer settings, package/model versions and file hashes in
+   [config/frozen_config.json](config/frozen_config.json). `heldout.json` was only hashed (bytes) before that file
+   was written. **This is a procedural freeze, not a blinded external evaluation.**
+3. Both detectors then ran on the held-out file with the frozen configuration; those runs produced the committed
+   reports. **No held-out retuning occurred:** thresholds, recognizer settings, pipeline code and fixtures did not
+   change afterwards. Later runs were **deterministic verification reruns** (a fresh-environment evaluation,
+   `scripts/check_reports.py`, and a reviewer's reproduction of the baseline reports). They used the same frozen
+   configuration and code and reproduced the committed reports byte for byte (the interpreter patch version is the
+   only field the check ignores). The results are still a tiny synthetic split. The held-out command refuses to run
+   without the frozen config.
+
+## Results
+
+Generated by `python scripts/render_summary.py --update-readme` from [reports/](reports/) (the JSON reports contain
+IDs, types, scores, offsets and counts, never text). A test checks this block equals the reports.
+
+<!-- SUMMARY:BEGIN -->
+
+#### development (exact-span, after validation, scope gate, thresholds and overlap resolution)
+
+| Detector | Type | TP | FP | FN | Precision | Recall | F1 |
+|---|---|---:|---:|---:|---:|---:|---:|
+| baseline | EMAIL_ADDRESS | 7 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
+| baseline | PHONE_NUMBER | 4 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
+| baseline | CUSTOMER_ID | 5 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
+| baseline | **micro** | 16 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
+| presidio | EMAIL_ADDRESS | 6 | 0 | 1 | 1.0000 | 0.8571 | 0.9231 |
+| presidio | PHONE_NUMBER | 4 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
+| presidio | CUSTOMER_ID | 5 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
+| presidio | **micro** | 15 | 0 | 1 | 1.0000 | 0.9375 | 0.9677 |
+
+| Detector | Gold fully covered | Partial | Untouched | Coverage rate | Replacements touching benign | Touching no gold | Benign chars removed | Benign-only examples preserved | Outputs equal oracle |
+|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
+| baseline | 16/16 | 0 | 0 | 1.0000 | 0 | 0 | 0 | 2/2 | 10/10 |
+| presidio | 15/16 | 0 | 1 | 0.9375 | 0 | 0 | 0 | 2/2 | 9/10 |
+
+| Detector | Examples dispatched | Provider calls | Payload is exactly {request_id, text} | Payload text equals actual sanitized text | Output rebuilt from applied spans |
+|---|---:|---:|---:|---:|---:|
+| baseline | 10 | 10 | 10 | 10 | 10 |
+| presidio | 10 | 10 | 10 | 10 | 10 |
+
+#### heldout (exact-span, after validation, scope gate, thresholds and overlap resolution)
+
+| Detector | Type | TP | FP | FN | Precision | Recall | F1 |
+|---|---|---:|---:|---:|---:|---:|---:|
+| baseline | EMAIL_ADDRESS | 12 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
+| baseline | PHONE_NUMBER | 8 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
+| baseline | CUSTOMER_ID | 8 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
+| baseline | **micro** | 28 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
+| presidio | EMAIL_ADDRESS | 10 | 1 | 2 | 0.9091 | 0.8333 | 0.8696 |
+| presidio | PHONE_NUMBER | 8 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
+| presidio | CUSTOMER_ID | 8 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
+| presidio | **micro** | 26 | 1 | 2 | 0.9630 | 0.9286 | 0.9455 |
+
+| Detector | Gold fully covered | Partial | Untouched | Coverage rate | Replacements touching benign | Touching no gold | Benign chars removed | Benign-only examples preserved | Outputs equal oracle |
+|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
+| baseline | 28/28 | 0 | 0 | 1.0000 | 0 | 0 | 0 | 5/5 | 18/18 |
+| presidio | 27/28 | 0 | 1 | 0.9643 | 1 | 0 | 5 | 5/5 | 16/18 |
+
+| Detector | Examples dispatched | Provider calls | Payload is exactly {request_id, text} | Payload text equals actual sanitized text | Output rebuilt from applied spans |
+|---|---:|---:|---:|---:|---:|
+| baseline | 18 | 18 | 18 | 18 | 18 |
+| presidio | 18 | 18 | 18 | 18 | 18 |
+
+Frozen candidate thresholds (selected on development only): EMAIL_ADDRESS 1.0, PHONE_NUMBER 0.4, CUSTOMER_ID 1.0. Baseline: score 1.0, threshold 1.0 for all three types.
+
+<!-- SUMMARY:END -->
+
+Reading the numbers:
+
+- **Primary metrics** score the spans actually applied (exact `(example, type, start, end)`; a wrong type or
+  partial interval is one FP and one FN). **Coverage** is separate: a gold interval is fully covered if every
+  character is inside some applied replacement, whatever its type.
+- **The baseline's perfect score is expected and says little.** Its regexes implement the same syntax rules that
+  define the gold labels, on a small template set. The comparison is a sanity check of the harness and a contrast
+  with a differently-built detector, not a quality ranking.
+- Provider-boundary columns are reported **separately from accuracy**. A miss is a detector/coverage failure; the
+  payload still equals the actual sanitized text. The fixtures' `expected_sanitized` strings are an oracle for
+  comparison only; they are never detector output or a provider input.
+
+### Known errors
+
+Observed on the held-out split (candidate; the baseline had none). Values are visible only via the explicit
+`demo` command, which reads the held-out report and fixture.
+
+- `test-010`: an email-shaped field with a `.invalid` suffix was not detected (gold FN, untouched). The offline
+  public-suffix validator rejects suffixes absent from its snapshot. The contract defines such fields as
+  sensitive, so this is a candidate miss, not a label problem. The same cause appeared on development (`dev-008`).
+- `test-012`: Presidio's email pattern allows `=` in the local part, so the matched span began at a `key=` prefix
+  (5 benign characters removed): one FP plus one FN at the exact-span level, although the real email is fully
+  covered (partial-interval rule).
+- 3 phone candidates in the held-out run were dropped by the scope gate (other phone formats), correctly by the
+  contract; 0 were dropped by the threshold.
+
+## Dependency notes
+
+- Pinned in [requirements-presidio.txt](requirements-presidio.txt): `presidio-analyzer==2.2.366`, `spacy==3.8.18`,
+  `en_core_web_sm` 3.8.0 (12,806,118 bytes, SHA-256 `1932429d…fb85`, hash-pinned), 52 packages in total.
+- Stock Presidio `EmailRecognizer` validates through `tldextract`, which tries to download the Public Suffix List
+  and writes a cache. The default here is an offline subclass that uses the suffix snapshot bundled in the wheel
+  (no network, no cache; the snapshot can be stale). The stock recognizer is reachable only through the diagnostic
+  `python -m sanitizer.presidio_check --stock-email`; it is not a CLI route.
+- Presidio's DEBUG log records contain input text. `build_analyzer()` sets the `presidio-analyzer` logger to INFO,
+  a **process-wide** setting, and tests assert nothing sensitive appears with a root logger at DEBUG. That protects
+  only this tested configuration: it is not robust against an application that re-enables that logger's DEBUG level.
+- Installation uses the network. The tested offline inference path makes no network attempts (socket-blocked test).
+
+## Limitations
+
+Tiny synthetic fixtures, three entity types, one narrow phone syntax, ASCII-shaped emails, English only, no
+statistical claims, thresholds chosen on 10 examples (the frozen phone threshold equals the recognizer's base
+score, so it has no margin), PHONE_NUMBER's position in the tie-break order is an agreed assumption. Hosted CI has
+not run (see below). Gateway integration, retries/fallbacks and real-provider behavior are out of scope and were
+not tested.
+
+## CI
+
+[.github/workflows/ci.yml](.github/workflows/ci.yml) defines a baseline job and a candidate job (the candidate
+job sets `REQUIRE_CANDIDATE_TESTS=1`, fails if dependencies are absent and fails on any skipped test). **Hosted
+CI status: PENDING** (no hosted run was executed). The same commands were run locally; see the review packet.
+
+## Repository layout
+
+- `sanitizer/`: `core.py` (pipeline), `detectors.py`, `presidio_detector.py`, `evaluation.py`, `freeze.py`,
+  `config.py`, `demo.py`, `cli.py`
+- `fixtures/`, `docs/handoff/` (unchanged reviewer files), `config/frozen_config.json`, `reports/`
+- `tests/`, `scripts/`, `.github/workflows/ci.yml`, [WALKTHROUGH.md](WALKTHROUGH.md)
+
+## Email pattern (baseline) and its limits
+
+    (?<![\w.%+-])[A-Za-z0-9._%+-]+@(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}(?![\w-])    (ASCII flag)
+
+ASCII only; not RFC 5322; requires a dotted domain with an alphabetic final label of 2+ letters; labels may start or
+end with `-` and local parts may have consecutive dots (over-matches); obfuscated forms are not detected;
+`xava@example.com` is matched whole while `a@b.com-x` and `a@b.com1` are not matched at all.
 
 ## Detector contract
 
-`detector(text)` returns a list/tuple of dicts with exactly the keys
-`entity_type`, `start`, `end`, `score`. Anything else (generator, extra keys,
-bool offsets, non-finite score, unknown type) is rejected as invalid output.
-
-## Exploratory Presidio path (optional; not part of the stdlib baseline)
-
-`sanitizer/presidio_detector.py` builds an `AnalyzerEngine` with exactly three recognizers:
-Presidio's `EmailRecognizer` (subclassed to validate offline), `PhoneRecognizer`, and a custom
-`CUSTOMER_ID` pattern (same regex as the baseline, case-sensitive). No NER recognizer, no
-bulk `load_predefined_recognizers()`. `sanitizer.core` never imports it.
-
-Setup (pins and the model wheel hash are in `requirements-presidio.txt`; use a SHORT venv path on
-Windows, a deep path made spaCy fail to load a DLL):
-
-    python -m venv C:\pv
-    C:\pv\Scripts\python -m pip install -r requirements-presidio.txt
-    C:\pv\Scripts\python -m sanitizer.presidio_check          # dev-001 exploratory check
-    C:\pv\Scripts\python -m unittest discover -v              # Presidio tests run only here
-
-The entity allowlist for this path is `EMAIL_ADDRESS, PHONE_NUMBER, CUSTOMER_ID` (also the
-overlap tie-break order; the PHONE_NUMBER position is an assumption). The baseline allowlist is
-unchanged. Presidio's `presidio-analyzer` logger is set to INFO because its DEBUG records include
-the text around a match. Nothing here is an accuracy claim.
+`detector(text)` returns a list/tuple of dicts with exactly `entity_type`, `start`, `end`, `score`. Anything else
+(generator, extra keys, bool offsets, non-finite or out-of-range score, unknown type) aborts dispatch as
+`SANITIZER_INVALID_DETECTOR_OUTPUT`. Every span is validated **before** scope or threshold filtering. Request IDs
+must fullmatch `(?:demo|req)-[0-9]{3,12}` and are never logged. Logs contain only `dispatched chars=<n>` or
+`rejected code=<CODE>`.

--- a/sanitizer/cli.py
+++ b/sanitizer/cli.py
@@ -1,19 +1,26 @@
-"""CLI. Normal use never prints the original text.
-
-  python -m sanitizer run --request-id ID     reads UTF-8 bytes from stdin; prints the
-                                              payload captured by the in-memory mock
-  python -m sanitizer inspect-fixture         explicit synthetic inspection (prints dev-001 text)
-
-Every failure prints exactly one fixed code + LF to stderr, nothing to stdout, exit 2.
+"""CLI. Normal use never prints the original text. Every failure prints exactly one fixed code + LF
+to stderr, nothing to stdout, exit 2.
+
+  run --request-id ID [--detector baseline|presidio] [--config PATH] [--summary]
+        reads UTF-8 bytes from stdin; prints the payload captured by the in-memory mock
+        (--summary wraps it as {"payload": {...}, "entity_counts": {...}}; counts only, no values)
+  inspect-fixture        explicit synthetic inspection of dev-001 (prints the canaries)
+  demo [--detector ...]  explicit synthetic inspection of fixture examples (prints fabricated values)
+  select-thresholds      development-only threshold selection + procedural freeze (writes frozen_config.json)
+  evaluate --detector D --split development|heldout   writes a privacy-safe JSON report
 """
 import json
 import logging
 import sys
 from argparse import ArgumentParser
-
-from .core import (ERR_INTERNAL, ERR_INVALID_ARGUMENTS, MAX_INPUT_BYTES, RecordingMock,
-                   SanitizerError, baseline_detector, decode_input, dispatch,
-                   validate_request_id)
+from pathlib import Path
+
+from .config import (DEFAULT_CONFIG, FIXTURE_DIR, PROJECT_ROOT, check_fixture_integrity, file_sha256,
+                     load_frozen_config, validate_thresholds)
+from .core import (ENTITY_PRIORITY, ERR_CONFIG_REQUIRED, ERR_INTERNAL, ERR_INVALID_ARGUMENTS, ERR_INVALID_CONFIG,
+                   MAX_INPUT_BYTES, RecordingMock, SanitizerError, baseline_detector, decode_input,
+                   run_pipeline, validate_request_id)
+from .detectors import BASELINE_THRESHOLDS, DETECTOR_NAMES, build_presidio, load_detector
 from .fixture import DEV_001
 
 log = logging.getLogger("sanitizer")
@@ -28,34 +35,123 @@
         raise SanitizerError(ERR_INVALID_ARGUMENTS)
 
 
-def _run(args, stdin, stdout, stderr, detector, provider):
-    try:
-        validate_request_id(args.request_id)  # before reading stdin or detecting
-        data = stdin.read(MAX_INPUT_BYTES + 1)  # bounded binary read
-        text = decode_input(data)
-        payload = dispatch(args.request_id, text, provider, detector)
-        stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
-        return 0
-    except SanitizerError as e:
-        code = e.code
-    except Exception:  # unexpected: never expose message or traceback
-        log.error("rejected code=%s", ERR_INTERNAL)
-        code = ERR_INTERNAL
-    stderr.write(code + "\n")
-    return EXIT_ERROR
+def _run(args, stdin, stdout, detector, provider):
+    validate_request_id(args.request_id)  # before reading stdin or detecting
+    text = decode_input(stdin.read(MAX_INPUT_BYTES + 1))  # bounded binary read, strict UTF-8
+    if detector is not None:  # injected detector (tests); accepts every score
+        fn, th = detector, None
+    else:  # named detector; a dependency/model/config failure is a fixed code, never a fallback
+        loaded = load_detector(args.detector, args.config)
+        fn, th = loaded.fn, loaded.thresholds
+    payload, res = run_pipeline(args.request_id, text, provider, fn, thresholds=th)
+    out = {"payload": payload, "entity_counts": res.entity_counts()} if args.summary else payload
+    stdout.write(json.dumps(out, ensure_ascii=False) + "\n")
+    return 0
 
 
 def _inspect(stdout, detector):
     text = DEV_001["text"]
-    found = sorted((s["entity_type"], s["start"], s["end"]) for s in detector(text))
+    found = sorted((s["entity_type"], s["start"], s["end"]) for s in (detector or baseline_detector)(text))
     for t, a, b in found:
         stdout.write(f"{t} [{a}:{b}] {text[a:b]!r}\n")
     return 0
 
 
-def main(argv=None, stdin=None, stdout=None, stderr=None,
-         detector=baseline_detector, provider=None):
-    """stdin must be a binary stream (default: sys.stdin.buffer)."""
+def _fmt(v):
+    return "null" if v is None else f"{v:.4f}"
+
+
+def _summary_lines(rep):
+    m = rep["metrics"]
+    lines = []
+    for t in ENTITY_PRIORITY + ("micro",):
+        b = m["micro"] if t == "micro" else m["per_type"][t]
+        lines.append(f"{t:<14} TP={b['tp']} FP={b['fp']} FN={b['fn']} precision={_fmt(b['precision'])} "
+                     f"recall={_fmt(b['recall'])} f1={_fmt(b['f1'])}")
+    c = rep["coverage"]["overall"]
+    lines.append(f"coverage       full={c['full']} partial={c['partial']} untouched={c['untouched']} rate={_fmt(c['coverage_rate'])}")
+    b = rep["benign"]
+    lines.append(f"benign         replacements_touching_benign={b['replacements_touching_benign']} "
+                 f"replacements_touching_no_gold={b['replacements_touching_no_gold']} "
+                 f"benign_characters_removed={b['benign_characters_removed']}")
+    p = rep["preservation"]
+    lines.append(f"preservation   no_gold_preserved={p['no_gold_examples_preserved']}/{p['examples_with_no_gold']} "
+                 f"equal_expected={p['examples_equal_expected_sanitized']}/{p['examples_total']}")
+    return lines
+
+
+def _parse_thresholds(s):
+    try:
+        e, p, c = (float(x) for x in s.split(","))
+    except Exception:
+        raise SanitizerError(ERR_INVALID_ARGUMENTS) from None
+    return validate_thresholds({"EMAIL_ADDRESS": e, "PHONE_NUMBER": p, "CUSTOMER_ID": c})
+
+
+def _evaluate(args, stdout):
+    from .evaluation import build_report, dump_report, load_fixture, run_meta, run_split
+
+    split = args.split
+    fx_path = FIXTURE_DIR / f"{split}.json"
+    cfg_path = Path(args.config) if args.config else DEFAULT_CONFIG
+    th, cfg_sha, extra = None, None, {}
+    if args.debug_thresholds is not None:  # development-only debugging of the candidate
+        if split != "development" or args.detector != "presidio":
+            raise SanitizerError(ERR_INVALID_ARGUMENTS)
+        th, extra = _parse_thresholds(args.debug_thresholds), {"debug_thresholds": True}
+    elif split == "heldout" or args.detector == "presidio":
+        # the held-out command REQUIRES the frozen config (for both detectors); the candidate always needs it
+        if not cfg_path.is_file():
+            raise SanitizerError(ERR_CONFIG_REQUIRED if split == "heldout" else ERR_INVALID_CONFIG)
+        cfg = load_frozen_config(cfg_path)
+        check_fixture_integrity(cfg)
+        cfg_sha = file_sha256(cfg_path)
+        th = cfg["thresholds"] if args.detector == "presidio" else dict(BASELINE_THRESHOLDS)
+    else:  # baseline on development: fixed thresholds, no freeze needed
+        th = dict(BASELINE_THRESHOLDS)
+    fixture = load_fixture(fx_path)
+    if args.detector == "baseline":
+        fn = baseline_detector
+    else:
+        fn, _mod, _analyzer = build_presidio()
+    records = run_split(fixture, lambda _ex: fn, th)
+    report = build_report(run_meta(args.detector, split, file_sha256(fx_path), th, cfg_sha, extra), records)
+    out = Path(args.out) if args.out else PROJECT_ROOT / "reports" / f"{split}_{args.detector}.json"
+    out.parent.mkdir(parents=True, exist_ok=True)
+    out.write_text(dump_report(report), encoding="utf-8", newline="\n")
+    stdout.write(f"{args.detector} on {split} (thresholds {th}); report written\n")
+    for line in _summary_lines(report):
+        stdout.write(line + "\n")
+    return 0
+
+
+def _select_thresholds(args, stdout):
+    from .freeze import build_frozen_config, write_frozen_config
+
+    out = Path(args.out) if args.out else DEFAULT_CONFIG
+    if out.exists() and not args.allow_refreeze:  # never silently re-freeze after the fact
+        raise SanitizerError(ERR_INVALID_CONFIG)
+    cfg = build_frozen_config(FIXTURE_DIR / "development.json", FIXTURE_DIR / "heldout.json",
+                              PROJECT_ROOT / "requirements-presidio.txt")
+    write_frozen_config(out, cfg)
+    m = cfg["development_metrics_at_selected_thresholds"]["micro"]
+    stdout.write(f"selected thresholds (development only): {cfg['thresholds']}\n")
+    stdout.write(f"development micro: TP={m['tp']} FP={m['fp']} FN={m['fn']} precision={_fmt(m['precision'])} "
+                 f"recall={_fmt(m['recall'])} f1={_fmt(m['f1'])}\n")
+    stdout.write(f"configurations tied at top after the benign rule: {cfg['selection_tied_at_top_after_benign_rule']}\n")
+    stdout.write("frozen config written (procedural freeze, not a blinded external evaluation)\n")
+    return 0
+
+
+def _demo(args, stdout):
+    from .demo import run_demo
+
+    return run_demo(lambda s="": stdout.write(s + "\n"), args.detector, args.config)
+
+
+def main(argv=None, stdin=None, stdout=None, stderr=None, detector=None, provider=None):
+    """stdin must be a binary stream (default: sys.stdin.buffer). `detector`/`provider` are injection
+    points for tests of the `run` command only; the shipped CLI never passes them."""
     stdin = stdin or sys.stdin.buffer
     stdout = stdout or sys.stdout
     stderr = stderr or sys.stderr
@@ -64,12 +160,41 @@
     sub = p.add_subparsers(dest="cmd", required=True)  # subparsers reuse _Parser
     r = sub.add_parser("run")
     r.add_argument("--request-id", required=True)
+    r.add_argument("--detector", choices=DETECTOR_NAMES, default="baseline")
+    r.add_argument("--config", default=None)
+    r.add_argument("--summary", action="store_true")
     sub.add_parser("inspect-fixture")
+    d = sub.add_parser("demo")
+    d.add_argument("--detector", choices=DETECTOR_NAMES, default="baseline")
+    d.add_argument("--config", default=None)
+    s = sub.add_parser("select-thresholds")
+    s.add_argument("--out", default=None)
+    s.add_argument("--allow-refreeze", action="store_true")
+    e = sub.add_parser("evaluate")
+    e.add_argument("--detector", choices=DETECTOR_NAMES, required=True)
+    e.add_argument("--split", choices=("development", "heldout"), required=True)
+    e.add_argument("--config", default=None)
+    e.add_argument("--out", default=None)
+    e.add_argument("--debug-thresholds", default=None)
     try:
         args = p.parse_args(argv)  # --help/-h still prints help and exits 0
-    except SanitizerError as e:
-        stderr.write(e.code + "\n")
+    except SanitizerError as ex:
+        stderr.write(ex.code + "\n")
         return EXIT_ERROR
-    if args.cmd == "run":
-        return _run(args, stdin, stdout, stderr, detector, provider)
-    return _inspect(stdout, detector)
+    try:
+        if args.cmd == "run":
+            return _run(args, stdin, stdout, detector, provider)
+        if args.cmd == "inspect-fixture":
+            return _inspect(stdout, detector)
+        if args.cmd == "demo":
+            return _demo(args, stdout)
+        if args.cmd == "select-thresholds":
+            return _select_thresholds(args, stdout)
+        return _evaluate(args, stdout)
+    except SanitizerError as ex:
+        code = ex.code
+    except Exception:  # unexpected: never expose message or traceback
+        log.error("rejected code=%s", ERR_INTERNAL)
+        code = ERR_INTERNAL
+    stderr.write(code + "\n")
+    return EXIT_ERROR

--- a/sanitizer/core.py
+++ b/sanitizer/core.py
@@ -1,4 +1,5 @@
-"""Baseline sanitizer: detect -> validate spans -> resolve overlaps -> replace -> dispatch.
+"""Sanitizer pipeline: detect -> validate ALL spans -> scope gate -> thresholds -> dedupe ->
+resolve overlaps -> replace -> dispatch.
 
 Stdlib only. No raw input, matched values, or exception text is ever logged
 or placed in a raised error; failures expose only a fixed public code.
@@ -6,7 +7,8 @@
 import logging
 import math
 import re
-from typing import Any, Callable, Dict, Iterable, List, Tuple
+from dataclasses import dataclass, field
+from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Tuple
 
 log = logging.getLogger("sanitizer")
 # Library convention: without this, Python's last-resort handler would write
@@ -23,12 +25,16 @@
 ERR_INTERNAL = "SANITIZER_INTERNAL_ERROR"
 ERR_INVALID_REQUEST_ID = "SANITIZER_INVALID_REQUEST_ID"
 ERR_INVALID_ARGUMENTS = "SANITIZER_INVALID_ARGUMENTS"
+ERR_DETECTOR_UNAVAILABLE = "SANITIZER_DETECTOR_UNAVAILABLE"  # dependency/model/config init failed
+ERR_INVALID_CONFIG = "SANITIZER_INVALID_CONFIG"              # frozen config missing/invalid/mismatched
+ERR_CONFIG_REQUIRED = "SANITIZER_FROZEN_CONFIG_REQUIRED"     # held-out evaluation without a freeze
+ERR_INVALID_FIXTURE = "SANITIZER_INVALID_FIXTURE"
 
 # MVP privacy boundary: request IDs are synthetic and carry no caller data.
 REQUEST_ID_RE = re.compile(r"(?:demo|req)-[0-9]{3,12}")
 
-# Allowlist; list order is also the overlap tie-break priority (EMAIL first).
-ENTITY_PRIORITY = ("EMAIL_ADDRESS", "CUSTOMER_ID")
+# Scope: three types. Tuple order is also the overlap tie-break order.
+ENTITY_PRIORITY = ("EMAIL_ADDRESS", "PHONE_NUMBER", "CUSTOMER_ID")
 _SPAN_KEYS = frozenset(("entity_type", "start", "end", "score"))
 
 # Baseline email pattern (ASCII only). See README for limitations.
@@ -42,6 +48,10 @@
 )
 # Case-sensitive CUST- + exactly six ASCII digits, not inside a longer token.
 CUSTOMER_ID_RE = re.compile(r"(?<![A-Za-z0-9_])CUST-[0-9]{6}(?![A-Za-z0-9_])")
+# Frozen phone scope: exactly "(AAA) BBB-CCCC", one ASCII space, A and first B in 2-9.
+# A syntax rule, not validation that a number is assigned. Used by the baseline AND as the
+# scope gate for every detector's phone candidates.
+PHONE_SCOPE_RE = re.compile(r"(?<![A-Za-z0-9_])\([2-9][0-9]{2}\) [2-9][0-9]{2}-[0-9]{4}(?![A-Za-z0-9_])")
 
 
 class SanitizerError(Exception):
@@ -71,7 +81,8 @@
 
 def baseline_detector(text: str) -> List[Dict[str, Any]]:
     spans = []
-    for etype, rx in (("EMAIL_ADDRESS", EMAIL_RE), ("CUSTOMER_ID", CUSTOMER_ID_RE)):
+    for etype, rx in (("EMAIL_ADDRESS", EMAIL_RE), ("PHONE_NUMBER", PHONE_SCOPE_RE),
+                      ("CUSTOMER_ID", CUSTOMER_ID_RE)):
         for m in rx.finditer(text):
             spans.append({"entity_type": etype, "start": m.start(), "end": m.end(), "score": 1.0})
     return spans
@@ -100,9 +111,9 @@
 
 def validate_spans(spans: Any, text_len: int,
                    entities: Tuple[str, ...] = ENTITY_PRIORITY) -> List[Dict[str, Any]]:
-    """Strict validation; any problem raises ERR_INVALID_OUTPUT with no detail.
-
-    `entities` is the allowlist (default: the baseline's two types)."""
+    """Strict validation of EVERY span; any problem raises ERR_INVALID_OUTPUT with no detail.
+
+    `entities` is the allowlist (default: the three scoped types)."""
     if not isinstance(spans, (list, tuple)):
         raise SanitizerError(ERR_INVALID_OUTPUT)
     for s in spans:
@@ -120,14 +131,18 @@
 
 def resolve_spans(spans: Iterable[Dict[str, Any]],
                   entities: Tuple[str, ...] = ENTITY_PRIORITY) -> List[Dict[str, Any]]:
-    """Dedupe identical spans, then keep non-overlapping ones.
-
-    Priority: longest, higher score, position in `entities` (default: EMAIL_ADDRESS
-    before CUSTOMER_ID), earlier start. Result is sorted by start.
+    """Dedupe same-type/same-range spans (keep the highest score), then keep non-overlapping ones.
+
+    Priority: longest, higher score, position in `entities` (EMAIL_ADDRESS -> PHONE_NUMBER ->
+    CUSTOMER_ID), earlier start. Result is sorted by start.
     """
-    unique = {(s["entity_type"], s["start"], s["end"], s["score"]): s for s in spans}
+    best: Dict[Tuple[str, int, int], Dict[str, Any]] = {}
+    for s in spans:
+        k = (s["entity_type"], s["start"], s["end"])
+        if k not in best or s["score"] > best[k]["score"]:
+            best[k] = s
     ranked = sorted(
-        unique.values(),
+        best.values(),
         key=lambda s: (-(s["end"] - s["start"]), -s["score"],
                        entities.index(s["entity_type"]), s["start"]),
     )
@@ -144,8 +159,24 @@
     return text
 
 
-def sanitize(text: str, detector: Callable[[str], Any] = baseline_detector,
-             entities: Tuple[str, ...] = ENTITY_PRIORITY) -> str:
+@dataclass
+class ProcessResult:
+    """What the pipeline actually did. Holds offsets/scores only, never matched values."""
+    sanitized: str
+    applied: List[Dict[str, Any]]                       # spans actually replaced (original coordinates)
+    validated: List[Dict[str, Any]] = field(default_factory=list)  # every validated candidate, pre-filter
+    dropped_by_scope: int = 0
+    dropped_by_threshold: int = 0
+
+    def entity_counts(self) -> Dict[str, int]:
+        return {t: sum(1 for s in self.applied if s["entity_type"] == t) for t in ENTITY_PRIORITY}
+
+
+def process(text: str, detector: Callable[[str], Any] = None,
+            entities: Tuple[str, ...] = ENTITY_PRIORITY,
+            thresholds: Optional[Mapping[str, float]] = None) -> ProcessResult:
+    """The single shared pipeline used by sanitize(), dispatch(), the CLI and the evaluation."""
+    detector = baseline_detector if detector is None else detector
     if not isinstance(text, str):
         raise TypeError("text must be str")
     if len(text) > MAX_INPUT_CHARS:  # before any detection
@@ -157,34 +188,56 @@
         log.error("rejected code=%s", ERR_DETECTOR)  # no exc_info: message may hold input
         raise SanitizerError(ERR_DETECTOR) from None
     try:
-        valid = validate_spans(spans, len(text), entities)
+        valid = validate_spans(spans, len(text), entities)  # validate everything BEFORE filtering
     except Exception:  # SanitizerError, or anything a hostile detector output provokes
         log.error("rejected code=%s", ERR_INVALID_OUTPUT)
         raise SanitizerError(ERR_INVALID_OUTPUT) from None
-    kept = resolve_spans(valid, entities)
-    return replace_spans(text, kept)
-
-
-def dispatch(request_id: str, text: str, provider: Callable[[Dict[str, str]], Any],
-             detector: Callable[[str], Any] = baseline_detector,
-             entities: Tuple[str, ...] = ENTITY_PRIORITY) -> Dict[str, str]:
-    """Sanitize, then send exactly {"request_id", "text"} to the provider.
-
-    request_id is validated first (before any detection). Any SanitizerError from
-    validation or sanitize() propagates before the provider is touched.
-    A provider exception is replaced by ERR_INTERNAL (the provider HAS been invoked
-    in that case); its message is never logged or re-raised.
+    scope = {(m.start(), m.end()) for m in PHONE_SCOPE_RE.finditer(text)}
+    in_scope = [s for s in valid
+                if s["entity_type"] != "PHONE_NUMBER" or (s["start"], s["end"]) in scope]
+    limits = thresholds or {}
+    passing = [s for s in in_scope if s["score"] >= limits.get(s["entity_type"], 0.0)]
+    applied = resolve_spans(passing, entities)
+    return ProcessResult(
+        sanitized=replace_spans(text, applied), applied=applied, validated=valid,
+        dropped_by_scope=len(valid) - len(in_scope), dropped_by_threshold=len(in_scope) - len(passing),
+    )
+
+
+def sanitize(text: str, detector: Callable[[str], Any] = None,
+             entities: Tuple[str, ...] = ENTITY_PRIORITY,
+             thresholds: Optional[Mapping[str, float]] = None) -> str:
+    return process(text, detector, entities, thresholds).sanitized
+
+
+def run_pipeline(request_id: str, text: str, provider: Callable[[Dict[str, str]], Any],
+                 detector: Callable[[str], Any] = None,
+                 entities: Tuple[str, ...] = ENTITY_PRIORITY,
+                 thresholds: Optional[Mapping[str, float]] = None) -> Tuple[Dict[str, str], ProcessResult]:
+    """validate request_id -> process -> send exactly {"request_id", "text"} to the provider.
+
+    request_id is validated first (before any detection). Any SanitizerError from validation
+    or process() propagates before the provider is touched. A provider exception is replaced by
+    ERR_INTERNAL (the provider HAS been invoked in that case); its message is never logged or
+    re-raised.
     """
     validate_request_id(request_id)
-    sanitized = sanitize(text, detector, entities)
-    payload = {"request_id": request_id, "text": sanitized}
+    result = process(text, detector, entities, thresholds)
+    payload = {"request_id": request_id, "text": result.sanitized}
     try:
         provider(payload)
     except Exception:
         log.error("rejected code=%s", ERR_INTERNAL)
         raise SanitizerError(ERR_INTERNAL) from None
-    log.info("dispatched chars=%d", len(sanitized))  # no request_id, no text
-    return payload
+    log.info("dispatched chars=%d", len(result.sanitized))  # no request_id, no text
+    return payload, result
+
+
+def dispatch(request_id: str, text: str, provider: Callable[[Dict[str, str]], Any],
+             detector: Callable[[str], Any] = None,
+             entities: Tuple[str, ...] = ENTITY_PRIORITY,
+             thresholds: Optional[Mapping[str, float]] = None) -> Dict[str, str]:
+    return run_pipeline(request_id, text, provider, detector, entities, thresholds)[0]
 
 
 class RecordingMock:

--- a/sanitizer/fixture.py
+++ b/sanitizer/fixture.py
@@ -1,7 +1,8 @@
-"""Synthetic development fixture dev-001 (contains the canary values by design)."""
+"""Synthetic development fixture dev-001 and canaries (they appear in source by design)."""
 
 CANARY_EMAIL = "ava@example.com"
 CANARY_CUSTOMER = "CUST-004271"
+CANARY_PHONE = "(415) 555-0132"  # inside the frozen phone scope: (AAA) BBB-CCCC, A and first B in 2-9
 
 DEV_001 = {
     "id": "dev-001",
@@ -11,3 +12,11 @@
         {"entity_type": "CUSTOMER_ID", "start": 32, "end": 43},
     ],
 }
+
+# All-three-entity synthetic canary text (gold offsets are located by substring, not by a detector).
+CANARY_TEXT = f"Email {CANARY_EMAIL}; phone {CANARY_PHONE}; customer {CANARY_CUSTOMER}; quantity 24."
+CANARY_SANITIZED = "Email [EMAIL_ADDRESS]; phone [PHONE_NUMBER]; customer [CUSTOMER_ID]; quantity 24."
+CANARY_GOLD = [
+    {"entity_type": t, "start": CANARY_TEXT.index(v), "end": CANARY_TEXT.index(v) + len(v)}
+    for t, v in (("EMAIL_ADDRESS", CANARY_EMAIL), ("PHONE_NUMBER", CANARY_PHONE), ("CUSTOMER_ID", CANARY_CUSTOMER))
+]

--- a/sanitizer/presidio_check.py
+++ b/sanitizer/presidio_check.py
@@ -17,7 +17,8 @@
 from . import RecordingMock, dispatch
 from .core import resolve_spans, validate_spans
 from .fixture import CANARY_CUSTOMER, CANARY_EMAIL, DEV_001
-from .presidio_detector import (LANGUAGE, PRESIDIO_ENTITIES, SPACY_MODEL, build_analyzer,
+from .core import ENTITY_PRIORITY as PRESIDIO_ENTITIES
+from .presidio_detector import (LANGUAGE, SPACY_MODEL, build_analyzer,
                                 make_detector)
 
 EXPECTED_SANITIZED = "Email [EMAIL_ADDRESS]; customer [CUSTOMER_ID]; quantity 24."

--- a/sanitizer/presidio_detector.py
+++ b/sanitizer/presidio_detector.py
@@ -1,8 +1,10 @@
-"""EXPLORATORY Presidio-backed detector. Requires presidio-analyzer and a spaCy model.
+"""Candidate detector: Presidio rule-based recognizers on a spaCy NLP engine.
 
-sanitizer.core never imports this module, so the stdlib-only baseline is unaffected.
-Only three recognizers are registered: email, phone, and a custom CUSTOMER_ID rule.
-No predefined-recognizer bulk load, no NER recognizer, no remote/LLM recognizers.
+NOT a trained PII model. Three rule-based recognizers are registered (email, US phone, a
+custom CUSTOMER_ID regex); the small spaCy model only provides tokens/lemmas for Presidio's
+context enhancer and no NER recognizer is registered. Requires presidio-analyzer and the
+en_core_web_sm model. sanitizer.core never imports this module, so the stdlib-only baseline
+is unaffected.
 """
 import logging
 from typing import Any, Callable, Dict, List
@@ -13,22 +15,21 @@
 from presidio_analyzer.nlp_engine import NlpEngineProvider
 from presidio_analyzer.predefined_recognizers import EmailRecognizer, PhoneRecognizer
 
+from .core import ENTITY_PRIORITY
+
 LANGUAGE = "en"
 SPACY_MODEL = "en_core_web_sm"
-
-# Allowlist + overlap tie-break order for this path. The position of PHONE_NUMBER is an
-# exploratory assumption: the scoring contract does not define it yet.
-PRESIDIO_ENTITIES = ("EMAIL_ADDRESS", "PHONE_NUMBER", "CUSTOMER_ID")
+PHONE_REGIONS = ("US",)  # frozen scope: US only; the shared exact-format gate narrows it further
 
 # Same rule as the baseline: case-sensitive CUST- + exactly six ASCII digits, not inside a token.
 CUSTOMER_ID_REGEX = r"(?<![A-Za-z0-9_])CUST-[0-9]{6}(?![A-Za-z0-9_])"
 
-
 # Stock EmailRecognizer.validate_result calls tldextract.extract(), whose default extractor
 # tries to download the Public Suffix List (publicsuffix.org, then raw.githubusercontent.com)
-# and writes a cache inside site-packages. Observed with presidio-analyzer 2.2.366 /
-# tldextract 5.4.0. This subclass validates with the suffix snapshot bundled in the
-# tldextract wheel: no network, no cache directory.
+# and writes a cache inside site-packages or the user profile. This subclass validates with
+# the suffix snapshot bundled in the tldextract wheel: no network, no cache directory. The
+# snapshot can be stale versus the live list. (The stock recognizer is reachable only through
+# the diagnostic `python -m sanitizer.presidio_check --stock-email`, never through the CLI.)
 _OFFLINE_TLD = tldextract.TLDExtract(suffix_list_urls=(), cache_dir=None)
 
 
@@ -41,7 +42,7 @@
     registry = RecognizerRegistry(supported_languages=[LANGUAGE])
     email_cls = EmailRecognizer if stock_email else OfflineEmailRecognizer
     registry.add_recognizer(email_cls(supported_language=LANGUAGE))
-    registry.add_recognizer(PhoneRecognizer(supported_language=LANGUAGE))
+    registry.add_recognizer(PhoneRecognizer(supported_language=LANGUAGE, supported_regions=PHONE_REGIONS))
     registry.add_recognizer(PatternRecognizer(
         supported_entity="CUSTOMER_ID",
         name="CustomerIdRecognizer",
@@ -55,7 +56,8 @@
 
 def build_analyzer(stock_email: bool = False) -> AnalyzerEngine:
     # Presidio's DEBUG records include input text (LemmaContextAwareEnhancer logs
-    # "Context list is: ... <text around the match>"). Keep that logger at INFO or above.
+    # "Context list is: ... <text around the match>"). This process-wide setting keeps that
+    # logger at INFO or above. It does NOT protect against an application re-lowering the level.
     logging.getLogger("presidio-analyzer").setLevel(logging.INFO)
     nlp_engine = NlpEngineProvider(nlp_configuration={
         "nlp_engine_name": "spacy",
@@ -66,12 +68,39 @@
 
 
 def make_detector(analyzer: AnalyzerEngine = None) -> Callable[[str], List[Dict[str, Any]]]:
-    """Return detector(text) -> spans in the sanitizer's detector contract."""
+    """Return detector(text) -> raw candidates in the sanitizer's detector contract (all scores)."""
     analyzer = analyzer or build_analyzer()
 
     def detect(text: str) -> List[Dict[str, Any]]:
-        results = analyzer.analyze(text=text, language=LANGUAGE, entities=list(PRESIDIO_ENTITIES))
+        results = analyzer.analyze(text=text, language=LANGUAGE, entities=list(ENTITY_PRIORITY))
         return [{"entity_type": r.entity_type, "start": r.start, "end": r.end, "score": r.score}
                 for r in results]
 
     return detect
+
+
+def recognizer_settings(analyzer: AnalyzerEngine) -> Dict[str, Any]:
+    """Settings recorded in frozen_config.json (read from the live objects, not retyped)."""
+    recognizers = []
+    for r in analyzer.registry.recognizers:
+        item = {"name": r.name, "class": type(r).__name__, "entities": list(r.supported_entities)}
+        if hasattr(r, "supported_regions"):
+            item["supported_regions"] = list(r.supported_regions)
+            item["leniency"] = r.leniency
+            item["base_score"] = r.SCORE
+        if hasattr(r, "patterns"):
+            item["patterns"] = [{"name": p.name, "regex": p.regex, "score": p.score} for p in r.patterns]
+            item["regex_flags"] = repr(r.global_regex_flags)
+        recognizers.append(item)
+    return {
+        "recognizers": recognizers,
+        "nlp_engine": type(analyzer.nlp_engine).__name__,
+        "spacy_model": SPACY_MODEL,
+        "spacy_pipeline": list(analyzer.nlp_engine.nlp[LANGUAGE].pipe_names),
+        "ner_recognizer_registered": any(type(r).__name__ == "SpacyRecognizer" for r in analyzer.registry.recognizers),
+        "context_enhancer": type(analyzer.context_aware_enhancer).__name__,
+        "analyze_entities": list(ENTITY_PRIORITY),
+        "engine_default_score_threshold": analyzer.default_score_threshold,
+        "email_validator": "offline tldextract snapshot (suffix_list_urls=(), cache_dir=None)",
+        "presidio_logger_level": "INFO (process-wide setting made in build_analyzer)",
+    }

--- a/tests/test_presidio_optional.py
+++ b/tests/test_presidio_optional.py
@@ -1,46 +1,58 @@
-"""Exploratory Presidio compatibility tests (dev-001 only). Skipped when presidio is absent,
-so the stdlib-only baseline suite is unaffected. No accuracy claims are made here."""
-import importlib.util
+"""Candidate (Presidio) configuration tests. They need presidio-analyzer and en_core_web_sm.
+
+Without them these tests SKIP locally; with REQUIRE_CANDIDATE_TESTS=1 (the CI candidate job) a missing
+dependency is a FAILURE. Passing results here are not accuracy claims."""
 import json
-import logging
 import os
 import subprocess
 import sys
 import tempfile
 import unittest
+from pathlib import Path
 
-from sanitizer import RecordingMock, SanitizerError, dispatch, sanitize
+from sanitizer import RecordingMock, dispatch, sanitize
+from sanitizer.config import load_frozen_config
+from sanitizer.core import ENTITY_PRIORITY
 from sanitizer.fixture import CANARY_CUSTOMER, CANARY_EMAIL, DEV_001
 
-ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
-HAVE_PRESIDIO = (importlib.util.find_spec("presidio_analyzer") is not None
-                 and importlib.util.find_spec("en_core_web_sm") is not None)
+from .support import FROZEN_CONFIG, HAVE_PRESIDIO, LogCapture, ROOT, cli, require_candidate
 
 TEXT = DEV_001["text"]
 SANITIZED = "Email [EMAIL_ADDRESS]; customer [CUSTOMER_ID]; quantity 24."
 PAYLOAD = {"request_id": "demo-001", "text": SANITIZED}
 
 if HAVE_PRESIDIO:
-    from sanitizer.presidio_detector import (PRESIDIO_ENTITIES, build_analyzer, make_detector)
+    from sanitizer.presidio_detector import build_analyzer, make_detector, recognizer_settings
 
 
-@unittest.skipUnless(HAVE_PRESIDIO, "presidio-analyzer / en_core_web_sm not installed")
-class PresidioDev001(unittest.TestCase):
+class PresidioConfiguration(unittest.TestCase):
     @classmethod
     def setUpClass(cls):
+        require_candidate()
         cls.analyzer = build_analyzer()
         cls.detector = staticmethod(make_detector(cls.analyzer))
+        cls.thresholds = load_frozen_config(FROZEN_CONFIG)["thresholds"]
 
     def test_only_selected_recognizers_loaded(self):
-        loaded = {(r.name, type(r).__name__, tuple(r.supported_entities))
-                  for r in self.analyzer.registry.recognizers}
+        loaded = {(r.name, type(r).__name__, tuple(r.supported_entities)) for r in self.analyzer.registry.recognizers}
         self.assertEqual(loaded, {
             ("OfflineEmailRecognizer", "OfflineEmailRecognizer", ("EMAIL_ADDRESS",)),
             ("PhoneRecognizer", "PhoneRecognizer", ("PHONE_NUMBER",)),
             ("CustomerIdRecognizer", "PatternRecognizer", ("CUSTOMER_ID",)),
         })
-        self.assertEqual(sorted(self.analyzer.get_supported_entities("en")),
-                         ["CUSTOMER_ID", "EMAIL_ADDRESS", "PHONE_NUMBER"])
+        self.assertEqual(sorted(self.analyzer.get_supported_entities("en")), sorted(ENTITY_PRIORITY))
+
+    def test_phone_recognizer_is_us_only_and_no_ner_recognizer_registered(self):
+        settings = recognizer_settings(self.analyzer)
+        phone = [r for r in settings["recognizers"] if r["class"] == "PhoneRecognizer"][0]
+        self.assertEqual(phone["supported_regions"], ["US"])
+        self.assertFalse(settings["ner_recognizer_registered"])
+        self.assertEqual(settings["spacy_model"], "en_core_web_sm")
+        self.assertEqual(settings["nlp_engine"], "SpacyNlpEngine")
+
+    def test_frozen_config_records_the_live_recognizer_settings(self):
+        cfg = json.loads(Path(FROZEN_CONFIG).read_text(encoding="utf-8"))
+        self.assertEqual(cfg["recognizer_settings"], json.loads(json.dumps(recognizer_settings(self.analyzer))))
 
     def test_engine_candidates_for_dev_001(self):
         got = sorted((s["entity_type"], s["start"], s["end"]) for s in self.detector(TEXT))
@@ -48,9 +60,9 @@
         self.assertEqual(got, want)
 
     def test_sanitized_text_and_payload_exact(self):
-        self.assertEqual(sanitize(TEXT, self.detector, PRESIDIO_ENTITIES), SANITIZED)
+        self.assertEqual(sanitize(TEXT, self.detector, thresholds=self.thresholds), SANITIZED)
         mock = RecordingMock()
-        dispatch("demo-001", TEXT, mock, self.detector, PRESIDIO_ENTITIES)
+        dispatch("demo-001", TEXT, mock, self.detector, thresholds=self.thresholds)
         self.assertEqual(mock.calls, [PAYLOAD])
         self.assertEqual(list(mock.calls[0]), ["request_id", "text"])
         for canary in (CANARY_EMAIL, CANARY_CUSTOMER):
@@ -63,11 +75,11 @@
         self.assertEqual([(s["start"], s["end"]) for s in self.detector("(CUST-004271),")
                           if s["entity_type"] == "CUSTOMER_ID"], [(1, 12)])
 
-    def test_phone_type_allowed_only_on_presidio_path(self):
-        phone = lambda t: [{"entity_type": "PHONE_NUMBER", "start": 0, "end": 3, "score": 0.4}]
-        with self.assertRaises(SanitizerError):
-            sanitize("abc", phone)  # baseline allowlist unchanged
-        self.assertEqual(sanitize("abc", phone, PRESIDIO_ENTITIES), "[PHONE_NUMBER]")
+    def test_unsupported_phone_format_is_gated_out_of_the_applied_spans(self):
+        text = "Unsupported phone 202-555-0147 here"
+        raw = self.detector(text)
+        self.assertTrue(any(s["entity_type"] == "PHONE_NUMBER" for s in raw))  # Presidio does see it
+        self.assertEqual(sanitize(text, self.detector, thresholds=self.thresholds), text)  # the shared gate drops it
 
     def test_no_network_and_no_cache_writes_in_a_fresh_process(self):
         # Fresh process: tldextract memoizes after first use, so in-process checks are order-dependent.
@@ -98,26 +110,18 @@
         self.assertEqual(written, [])
 
     def test_no_input_text_in_logs_at_root_debug(self):
-        records = []
+        with LogCapture() as logs:
+            det = make_detector(build_analyzer())  # build_analyzer sets presidio-analyzer to INFO
+            dispatch("demo-001", TEXT, RecordingMock(), det, thresholds=self.thresholds)
+        self.assertTrue(logs.lines)
+        for needle in (CANARY_EMAIL, CANARY_CUSTOMER, "quantity", "customer "):
+            self.assertNotIn(needle, logs.text)
 
-        class H(logging.Handler):
-            def emit(self, record):
-                records.append(record.getMessage())
-
-        h, root = H(logging.DEBUG), logging.getLogger()
-        old = root.level
-        root.addHandler(h)
-        root.setLevel(logging.DEBUG)
-        try:
-            det = make_detector(build_analyzer())  # build_analyzer sets presidio-analyzer to INFO
-            dispatch("demo-001", TEXT, RecordingMock(), det, PRESIDIO_ENTITIES)
-        finally:
-            root.removeHandler(h)
-            root.setLevel(old)
-        self.assertTrue(records)
-        blob = "\n".join(records)
-        for needle in (CANARY_EMAIL, CANARY_CUSTOMER, "quantity", "customer "):
-            self.assertNotIn(needle, blob)
+    def test_stock_email_probe_is_not_a_cli_route(self):
+        rc, out, err, _ = cli(["run", "--request-id", "demo-001", "--detector", "presidio", "--stock-email"], TEXT)
+        self.assertEqual((rc, out, err), (2, "", "SANITIZER_INVALID_ARGUMENTS\n"))
+        src = (Path(ROOT) / "sanitizer" / "cli.py").read_text(encoding="utf-8")
+        self.assertNotIn("stock", src.lower())
 
 
 if __name__ == "__main__":

--- a/tests/test_sanitizer.py
+++ b/tests/test_sanitizer.py
@@ -189,7 +189,7 @@
         "start == end": [span("EMAIL_ADDRESS", 3, 3)],
         "start > end": [span("EMAIL_ADDRESS", 5, 3)],
         "end > len": [span("EMAIL_ADDRESS", 0, len(TEXT) + 1)],
-        "unknown entity": [span("PHONE_NUMBER", 0, 5)],
+        "unknown entity": [span("PERSON", 0, 5)],
         "non-str entity": [span(["EMAIL_ADDRESS"], 0, 5)],
         "bool score": [span("EMAIL_ADDRESS", 0, 5, True)],
         "NaN score": [span("EMAIL_ADDRESS", 0, 5, float("nan"))],
````

## 5. Procedural integrity of the freeze

1. `sanitizer-final-handoff.zip` was extracted; `fixtures/*.json` were copied with `cp` and checked against the manifest
   hashes. `heldout.json` was **not** displayed, parsed, run or tuned against before the freeze; it was only hashed.
2. Detector debugging used development data only (`evaluate --debug-thresholds` is rejected for any other split).
3. `select-thresholds` hashed `heldout.json` as raw bytes, selected thresholds on development only, and wrote
   `config/frozen_config.json` (it records that statement).
4. Only then were the held-out evaluations run; those runs produced the committed reports (section 8). **No held-out
   retuning occurred**: no threshold, recognizer setting, pipeline code or fixture changed afterwards. Later runs (F5,
   F15, F16, the README-block runs in section 2a, and the reviewer's reproduction) were deterministic verification
   reruns with the same frozen configuration; they wrote to temporary files or rewrote byte-identical reports.
5. After the freeze I added tests that read `heldout.json` for fixture-integrity checks only (summary counts, gold slices
   vs oracle). No detector output on held-out data is used by any test.
6. The final rerun (F16) reproduces the committed reports byte-for-byte (ignoring the interpreter patch version),
   which also shows the final code behaves as it did at the held-out run.
7. This is a procedural freeze by the same author, not a blinded external evaluation, on a tiny synthetic template split.

## 6. Environment and exact commands with observed results

- Base interpreter: Python 3.13.7 on Windows-11-10.0.26100-SP0 (AMD64)
- Candidate venv: Python 3.13.7; pip 25.2
- Git: installed but this folder is not a repository, so no commit hash is available.
- Every command below was run in a fresh folder extracted from the project ZIP (`sanitizer-final-project.zip` minus this packet). Output is verbatim except that local paths are scrubbed.

### F1 baseline: full suite (stdlib only, base interpreter)

Command: `python -m unittest discover -v` | exit status: 0

````
--- stderr ---
setUpClass (tests.test_cli.CandidateCli) ... skipped 'presidio-analyzer / en_core_web_sm not installed'
test_initialization_failure_message_is_never_exposed (tests.test_cli.CandidateUnavailable.test_initialization_failure_message_is_never_exposed) ... ok
test_missing_invalid_or_mismatched_config_is_a_fixed_code (tests.test_cli.CandidateUnavailable.test_missing_invalid_or_mismatched_config_is_a_fixed_code) ... ok
test_missing_package_in_a_real_process (tests.test_cli.CandidateUnavailable.test_missing_package_in_a_real_process) ... ok
test_missing_package_in_process (tests.test_cli.CandidateUnavailable.test_missing_package_in_process) ... ok
test_baseline_demo_shows_labelled_synthetic_inspection (tests.test_cli.DemoCommand.test_baseline_demo_shows_labelled_synthetic_inspection) ... ok
test_demo_has_no_way_to_supply_text_or_pick_a_real_provider (tests.test_cli.DemoCommand.test_demo_has_no_way_to_supply_text_or_pick_a_real_provider) ... ok
test_presidio_demo_without_dependency_is_a_fixed_code (tests.test_cli.DemoCommand.test_presidio_demo_without_dependency_is_a_fixed_code) ... ok
test_baseline_development_report_is_deterministic_and_privacy_safe (tests.test_cli.EvaluationCommands.test_baseline_development_report_is_deterministic_and_privacy_safe) ... ok
test_debug_thresholds_are_development_only (tests.test_cli.EvaluationCommands.test_debug_thresholds_are_development_only) ... ok
test_heldout_requires_the_frozen_config (tests.test_cli.EvaluationCommands.test_heldout_requires_the_frozen_config) ... ok
test_report_separates_accuracy_from_provider_boundary (tests.test_cli.EvaluationCommands.test_report_separates_accuracy_from_provider_boundary) ... ok
test_select_thresholds_refuses_to_overwrite_a_freeze (tests.test_cli.EvaluationCommands.test_select_thresholds_refuses_to_overwrite_a_freeze) ... ok
test_default_detector_and_output_are_unchanged (tests.test_cli.RunCommand.test_default_detector_and_output_are_unchanged) ... ok
test_explicit_baseline_detector_handles_all_three_entities (tests.test_cli.RunCommand.test_explicit_baseline_detector_handles_all_three_entities) ... ok
test_summary_flag_adds_counts_outside_the_provider_object (tests.test_cli.RunCommand.test_summary_flag_adds_counts_outside_the_provider_object) ... ok
test_unknown_detector_choice_is_an_argument_error (tests.test_cli.RunCommand.test_unknown_detector_choice_is_an_argument_error) ... ok
test_all_three_entity_canary_payload_is_exactly_the_sanitized_text (tests.test_detectors_boundary.BaselineBoundary.test_all_three_entity_canary_payload_is_exactly_the_sanitized_text) ... ok
test_detector_failure_and_malformed_output_give_zero_provider_calls (tests.test_detectors_boundary.BaselineBoundary.test_detector_failure_and_malformed_output_give_zero_provider_calls) ... ok
test_documented_misses_are_accuracy_failures_not_boundary_failures (tests.test_detectors_boundary.BaselineBoundary.test_documented_misses_are_accuracy_failures_not_boundary_failures) ... ok
test_every_development_payload_equals_the_actual_sanitized_text_even_on_misses (tests.test_detectors_boundary.BaselineBoundary.test_every_development_payload_equals_the_actual_sanitized_text_even_on_misses) ... ok
test_known_correct_development_cases_have_exact_payload (tests.test_detectors_boundary.BaselineBoundary.test_known_correct_development_cases_have_exact_payload) ... ok
test_logs_at_root_debug_contain_only_approved_metadata (tests.test_detectors_boundary.BaselineBoundary.test_logs_at_root_debug_contain_only_approved_metadata) ... ok
test_provider_exception_is_distinct_from_detector_failure (tests.test_detectors_boundary.BaselineBoundary.test_provider_exception_is_distinct_from_detector_failure) ... ok
setUpClass (tests.test_detectors_boundary.PresidioBoundary) ... skipped 'presidio-analyzer / en_core_web_sm not installed'
test_readme_summary_block_equals_the_rendered_reports (tests.test_docs.ReadmeMatchesReports.test_readme_summary_block_equals_the_rendered_reports) ... ok
test_required_documents_exist (tests.test_docs.ReadmeMatchesReports.test_required_documents_exist) ... ok
test_summary_file_is_current (tests.test_docs.ReadmeMatchesReports.test_summary_file_is_current) ... ok
test_cli_and_core_do_not_import_presidio_or_spacy (tests.test_docs.StdlibBaselineStaysStdlib.test_cli_and_core_do_not_import_presidio_or_spacy) ... ok
test_structure_by_text (tests.test_docs.WorkflowKeepsItsGuarantees.test_structure_by_text) ... ok
test_structure_by_yaml (tests.test_docs.WorkflowKeepsItsGuarantees.test_structure_by_yaml) ... ok
test_heldout_fixture_matches_summary_and_is_self_consistent (tests.test_frozen_config.FixtureIntegrityAfterFreeze.test_heldout_fixture_matches_summary_and_is_self_consistent) ... ok
test_hashes_match_the_handoff_fixtures_and_files_on_disk (tests.test_frozen_config.FrozenConfig.test_hashes_match_the_handoff_fixtures_and_files_on_disk) ... ok
test_mismatched_or_missing_fixture_bytes_are_rejected (tests.test_frozen_config.FrozenConfig.test_mismatched_or_missing_fixture_bytes_are_rejected) ... ok
test_model_hash_matches_the_requirements_pin (tests.test_frozen_config.FrozenConfig.test_model_hash_matches_the_requirements_pin) ... ok
test_records_the_required_freeze_metadata (tests.test_frozen_config.FrozenConfig.test_records_the_required_freeze_metadata) ... ok
test_selected_thresholds_follow_the_selection_rule_over_the_stored_grid (tests.test_frozen_config.FrozenConfig.test_selected_thresholds_follow_the_selection_rule_over_the_stored_grid) ... ok
setUpClass (tests.test_frozen_config.SelectionReproducible) ... skipped 'presidio-analyzer / en_core_web_sm not installed'
test_boundaries_allow_punctuation_and_whitespace (tests.test_pipeline.PhoneBaseline.test_boundaries_allow_punctuation_and_whitespace) ... ok
test_digit_ranges (tests.test_pipeline.PhoneBaseline.test_digit_ranges) ... ok
test_exact_format_detected (tests.test_pipeline.PhoneBaseline.test_exact_format_detected) ... ok
test_out_of_scope_formats_are_not_detected (tests.test_pipeline.PhoneBaseline.test_out_of_scope_formats_are_not_detected) ... ok
test_all_spans_are_validated_before_the_gate_or_thresholds (tests.test_pipeline.ScopeGate.test_all_spans_are_validated_before_the_gate_or_thresholds) ... ok
test_exact_match_is_kept (tests.test_pipeline.ScopeGate.test_exact_match_is_kept) ... ok
test_gate_applies_only_to_phone_candidates (tests.test_pipeline.ScopeGate.test_gate_applies_only_to_phone_candidates) ... ok
test_gate_does_not_insert_missing_detections (tests.test_pipeline.ScopeGate.test_gate_does_not_insert_missing_detections) ... ok
test_trimmed_expanded_and_shifted_candidates_are_dropped_not_repaired (tests.test_pipeline.ScopeGate.test_trimmed_expanded_and_shifted_candidates_are_dropped_not_repaired) ... ok
test_unsupported_format_phone_candidate_is_dropped (tests.test_pipeline.ScopeGate.test_unsupported_format_phone_candidate_is_dropped) ... ok
test_sanitize_dispatch_and_run_pipeline_agree (tests.test_pipeline.SharedPipeline.test_sanitize_dispatch_and_run_pipeline_agree) ... ok
test_dedupe_keeps_highest_score_for_same_type_and_range (tests.test_pipeline.Thresholds.test_dedupe_keeps_highest_score_for_same_type_and_range) ... ok
test_no_thresholds_accepts_every_valid_score (tests.test_pipeline.Thresholds.test_no_thresholds_accepts_every_valid_score) ... ok
test_score_equal_to_threshold_passes_and_below_fails (tests.test_pipeline.Thresholds.test_score_equal_to_threshold_passes_and_below_fails) ... ok
test_thresholds_are_per_type (tests.test_pipeline.Thresholds.test_thresholds_are_per_type) ... ok
test_adjacent_nonoverlapping_spans_are_both_kept (tests.test_pipeline.TypePriorityTies.test_adjacent_nonoverlapping_spans_are_both_kept) ... ok
test_all_pairwise_ties_same_range (tests.test_pipeline.TypePriorityTies.test_all_pairwise_ties_same_range) ... ok
test_customer_id_inside_an_email_loses_to_the_whole_email (tests.test_pipeline.TypePriorityTies.test_customer_id_inside_an_email_loses_to_the_whole_email) ... ok
test_length_then_score_precede_type (tests.test_pipeline.TypePriorityTies.test_length_then_score_precede_type) ... ok
test_ties_with_offset_overlap_use_type_before_start (tests.test_pipeline.TypePriorityTies.test_ties_with_offset_overlap_use_type_before_start) ... ok
setUpClass (tests.test_presidio_optional.PresidioConfiguration) ... skipped 'presidio-analyzer / en_core_web_sm not installed'
test_explicit_help_still_works (tests.test_sanitizer.ArgumentErrors.test_explicit_help_still_works) ... ok
test_in_process_parser_failure_logs_only_code (tests.test_sanitizer.ArgumentErrors.test_in_process_parser_failure_logs_only_code) ... ok
test_parser_failures_are_fixed_code_and_never_echo_values (tests.test_sanitizer.ArgumentErrors.test_parser_failures_are_fixed_code_and_never_echo_values) ... ok
test_valid_invocation_unaffected (tests.test_sanitizer.ArgumentErrors.test_valid_invocation_unaffected) ... ok
test_inspect_fixture_is_the_explicit_synthetic_view (tests.test_sanitizer.Cli.test_inspect_fixture_is_the_explicit_synthetic_view) ... ok
test_success_prints_only_captured_payload (tests.test_sanitizer.Cli.test_success_prints_only_captured_payload) ... ok
test_cli_contract (tests.test_sanitizer.DetectorFailure.test_cli_contract) ... ok
test_exception_stops_dispatch_without_leaking (tests.test_sanitizer.DetectorFailure.test_exception_stops_dispatch_without_leaking) ... ok
test_detected_spans_match_expected (tests.test_sanitizer.Dev001.test_detected_spans_match_expected) ... ok
test_fixture_matches_contract_and_slices (tests.test_sanitizer.Dev001.test_fixture_matches_contract_and_slices) ... ok
test_mock_payload_exact (tests.test_sanitizer.Dev001.test_mock_payload_exact) ... ok
test_sanitized_text_exact (tests.test_sanitizer.Dev001.test_sanitized_text_exact) ... ok
test_empty_is_valid (tests.test_sanitizer.EmptyInput.test_empty_is_valid) ... ok
test_empty_via_cli (tests.test_sanitizer.EmptyInput.test_empty_via_cli) ... ok
test_library_wraps_provider_exception (tests.test_sanitizer.InternalError.test_library_wraps_provider_exception) ... ok
test_provider_exception_with_canaries (tests.test_sanitizer.InternalError.test_provider_exception_with_canaries) ... ok
test_unexpected_exception_inside_sanitizer (tests.test_sanitizer.InternalError.test_unexpected_exception_inside_sanitizer) ... ok
test_boundary_scores_still_accepted (tests.test_sanitizer.InvalidDetectorOutput.test_boundary_scores_still_accepted) ... ok
test_cli_contract (tests.test_sanitizer.InvalidDetectorOutput.test_cli_contract) ... ok
test_each_malformed_output_stops_dispatch (tests.test_sanitizer.InvalidDetectorOutput.test_each_malformed_output_stops_dispatch) ... ok
test_hostile_span_object_is_invalid_output_not_crash (tests.test_sanitizer.InvalidDetectorOutput.test_hostile_span_object_is_invalid_output_not_crash) ... ok
test_huge_integer_scores_via_cli_not_internal_error (tests.test_sanitizer.InvalidDetectorOutput.test_huge_integer_scores_via_cli_not_internal_error) ... ok
test_validator_itself_rejects_huge_ints_without_overflow (tests.test_sanitizer.InvalidDetectorOutput.test_validator_itself_rejects_huge_ints_without_overflow) ... ok
test_byte_bound_precedes_decoding_and_chars_checked_after (tests.test_sanitizer.InvalidEncoding.test_byte_bound_precedes_decoding_and_chars_checked_after) ... ok
test_in_process_no_detection_no_dispatch (tests.test_sanitizer.InvalidEncoding.test_in_process_no_detection_no_dispatch) ... ok
test_default_logs_contain_no_canaries_on_success_and_failure (tests.test_sanitizer.Logging.test_default_logs_contain_no_canaries_on_success_and_failure) ... ok
test_real_process_default_logging (tests.test_sanitizer.Logging.test_real_process_default_logging) ... ok
test_every_log_line_is_approved (tests.test_sanitizer.LoggingAllowlist.test_every_log_line_is_approved) ... ok
test_logs_never_contain_request_id (tests.test_sanitizer.LoggingAllowlist.test_logs_never_contain_request_id) ... ok
test_real_process_with_root_logging_configured (tests.test_sanitizer.LoggingAllowlist.test_real_process_with_root_logging_configured) ... ok
test_dedupe_and_adjacent_spans_kept (tests.test_sanitizer.OverlapResolution.test_dedupe_and_adjacent_spans_kept) ... ok
test_earlier_start_on_full_tie (tests.test_sanitizer.OverlapResolution.test_earlier_start_on_full_tie) ... ok
test_email_before_customer_id_on_tie (tests.test_sanitizer.OverlapResolution.test_email_before_customer_id_on_tie) ... ok
test_higher_score_on_equal_length (tests.test_sanitizer.OverlapResolution.test_higher_score_on_equal_length) ... ok
test_ints_accepted_as_scores (tests.test_sanitizer.OverlapResolution.test_ints_accepted_as_scores) ... ok
test_longest_wins (tests.test_sanitizer.OverlapResolution.test_longest_wins) ... ok
test_cli_contract_real_process (tests.test_sanitizer.OversizedInput.test_cli_contract_real_process) ... ok
test_limit_is_inclusive_and_counts_characters (tests.test_sanitizer.OversizedInput.test_limit_is_inclusive_and_counts_characters) ... ok
test_rejected_before_detection_and_dispatch (tests.test_sanitizer.OversizedInput.test_rejected_before_detection_and_dispatch) ... ok
test_benign_numbers_and_punctuation_untouched (tests.test_sanitizer.Preservation.test_benign_numbers_and_punctuation_untouched) ... ok
test_customer_id_boundaries (tests.test_sanitizer.Preservation.test_customer_id_boundaries) ... ok
test_no_unicode_normalization_and_char_offsets (tests.test_sanitizer.Preservation.test_no_unicode_normalization_and_char_offsets) ... ok
test_surrounding_punctuation_and_whitespace_preserved (tests.test_sanitizer.Preservation.test_surrounding_punctuation_and_whitespace_preserved) ... ok
test_crlf_input_not_normalized (tests.test_sanitizer.RealProcessBytes.test_crlf_input_not_normalized) ... ok
test_invalid_utf8_rejected_real_process (tests.test_sanitizer.RealProcessBytes.test_invalid_utf8_rejected_real_process) ... ok
test_valid_utf8_edge_cases_accepted (tests.test_sanitizer.RealProcessBytes.test_valid_utf8_edge_cases_accepted) ... ok
test_canary_ids_never_reach_provider_or_logs (tests.test_sanitizer.RequestIdBoundary.test_canary_ids_never_reach_provider_or_logs) ... ok
test_cli_in_process (tests.test_sanitizer.RequestIdBoundary.test_cli_in_process) ... ok
test_cli_real_process (tests.test_sanitizer.RequestIdBoundary.test_cli_real_process) ... ok
test_invalid_ids_rejected_before_detector_and_provider (tests.test_sanitizer.RequestIdBoundary.test_invalid_ids_rejected_before_detector_and_provider) ... ok
test_request_id_checked_before_stdin_is_decoded (tests.test_sanitizer.RequestIdBoundary.test_request_id_checked_before_stdin_is_decoded) ... ok
test_str_subclass_rejected (tests.test_sanitizer.RequestIdBoundary.test_str_subclass_rejected) ... ok
test_valid_ids_accepted_and_passed_through (tests.test_sanitizer.RequestIdBoundary.test_valid_ids_accepted_and_passed_through) ... ok
test_counts_are_summed_before_micro_metrics (tests.test_scoring.AggregateThroughRealPipeline.test_counts_are_summed_before_micro_metrics) ... ok
test_detector_failure_counts_gold_as_missed_with_zero_calls (tests.test_scoring.AggregateThroughRealPipeline.test_detector_failure_counts_gold_as_missed_with_zero_calls) ... ok
test_adjacent_intervals_union_covers_gold_but_is_not_an_exact_match (tests.test_scoring.EdgeCases.test_adjacent_intervals_union_covers_gold_but_is_not_an_exact_match) ... ok
test_benign_only_example_with_a_replacement_is_all_benign (tests.test_scoring.EdgeCases.test_benign_only_example_with_a_replacement_is_all_benign) ... ok
test_empty_gold_and_empty_predictions (tests.test_scoring.EdgeCases.test_empty_gold_and_empty_predictions) ... ok
test_metric_null_rules (tests.test_scoring.EdgeCases.test_metric_null_rules) ... ok
test_partial_interval_is_one_fp_and_one_fn (tests.test_scoring.EdgeCases.test_partial_interval_is_one_fp_and_one_fn) ... ok
test_repeated_values_are_separate_gold_entities (tests.test_scoring.EdgeCases.test_repeated_values_are_separate_gold_entities) ... ok
test_unicode_offsets_are_code_points (tests.test_scoring.EdgeCases.test_unicode_offsets_are_code_points) ... ok
test_wrong_type_with_full_coverage (tests.test_scoring.EdgeCases.test_wrong_type_with_full_coverage) ... ok
test_development_fixture_loads_and_matches_summary (tests.test_scoring.FixtureLoading.test_development_fixture_loads_and_matches_summary) ... ok
test_development_gold_slices_and_oracles_are_self_consistent (tests.test_scoring.FixtureLoading.test_development_gold_slices_and_oracles_are_self_consistent) ... ok
test_fixtures_are_the_unchanged_handoff_files (tests.test_scoring.FixtureLoading.test_fixtures_are_the_unchanged_handoff_files) ... ok
test_malformed_fixture_is_rejected_with_fixed_code (tests.test_scoring.FixtureLoading.test_malformed_fixture_is_rejected_with_fixed_code) ... ok
test_benign_statistics (tests.test_scoring.HandCalculatedOracle.test_benign_statistics) ... ok
test_counts_and_micro_metrics (tests.test_scoring.HandCalculatedOracle.test_counts_and_micro_metrics) ... ok
test_coverage (tests.test_scoring.HandCalculatedOracle.test_coverage) ... ok
test_per_type_counts (tests.test_scoring.HandCalculatedOracle.test_per_type_counts) ... ok
test_replacement_output (tests.test_scoring.HandCalculatedOracle.test_replacement_output) ... ok
test_false_positive_is_cut_by_raising_its_threshold (tests.test_scoring.ThresholdSelection.test_false_positive_is_cut_by_raising_its_threshold) ... ok
test_grid_is_125_and_ties_prefer_higher_thresholds (tests.test_scoring.ThresholdSelection.test_grid_is_125_and_ties_prefer_higher_thresholds) ... ok
test_no_predictions_has_f1_zero_and_selection_still_defined (tests.test_scoring.ThresholdSelection.test_no_predictions_has_f1_zero_and_selection_still_defined) ... ok
test_threshold_is_inclusive_and_picks_highest_passing_value (tests.test_scoring.ThresholdSelection.test_threshold_is_inclusive_and_picks_highest_passing_value) ... ok
test_tie_break_order_is_f1_then_fewer_benign_then_higher_thresholds (tests.test_scoring.ThresholdSelection.test_tie_break_order_is_f1_then_fewer_benign_then_higher_thresholds) ... ok

----------------------------------------------------------------------
Ran 132 tests in 3.833s

OK (skipped=4)
````

### F2 baseline: dev-001 through the CLI

Command: `python -m sanitizer run --request-id demo-001   [stdin: the dev-001 text as exact bytes; see the README exact-bytes example for PowerShell]` | exit status: 0

````
{"request_id": "demo-001", "text": "Email [EMAIL_ADDRESS]; customer [CUSTOMER_ID]; quantity 24."}
````

### F3 baseline: all three entities with --summary

Command: `python -m sanitizer run --summary --request-id demo-001   [stdin: the all-three-entity canary text as exact bytes]` | exit status: 0

````
{"payload": {"request_id": "demo-001", "text": "Email [EMAIL_ADDRESS]; phone [PHONE_NUMBER]; customer [CUSTOMER_ID]; quantity 24."}, "entity_counts": {"EMAIL_ADDRESS": 1, "PHONE_NUMBER": 1, "CUSTOMER_ID": 1}}
````

### F4 baseline: explicit synthetic demo

Command: `python -m sanitizer demo` | exit status: 0

````
==============================================================================
SYNTHETIC INSPECTION. Every value below is fabricated fixture data printed on purpose.
detector: baseline | thresholds: {'EMAIL_ADDRESS': 1.0, 'PHONE_NUMBER': 1.0, 'CUSTOMER_ID': 1.0}
No user text is accepted here; payloads come from the in-memory RecordingMock only.
==============================================================================
--- all-three-entity canary
  original : 'Email ava@example.com; phone (415) 555-0132; customer CUST-004271; quantity 24.'
  gold:
    EMAIL_ADDRESS [6:21] 'ava@example.com'
    PHONE_NUMBER  [29:43] '(415) 555-0132'
    CUSTOMER_ID   [54:65] 'CUST-004271'
  detected (validated candidates, before scope/threshold/resolution):
    EMAIL_ADDRESS [6:21] 'ava@example.com' score=1.0
    PHONE_NUMBER  [29:43] '(415) 555-0132' score=1.0
    CUSTOMER_ID   [54:65] 'CUST-004271' score=1.0
  resolved (applied) spans:
    EMAIL_ADDRESS [6:21] 'ava@example.com' score=1.0
    PHONE_NUMBER  [29:43] '(415) 555-0132' score=1.0
    CUSTOMER_ID   [54:65] 'CUST-004271' score=1.0
  sanitized: 'Email [EMAIL_ADDRESS]; phone [PHONE_NUMBER]; customer [CUSTOMER_ID]; quantity 24.'
  payload captured by RecordingMock: {'request_id': 'demo-001', 'text': 'Email [EMAIL_ADDRESS]; phone [PHONE_NUMBER]; customer [CUSTOMER_ID]; quantity 24.'} (calls=1)
  equals fixture oracle: True  (oracle is a check only, never a shortcut)
--- benign preservation (no gold; output must equal input) [dev-006]
  original : 'Units 24; year 2026; code cust-100006; token XCUST-100006; short CUST-10006.'
  gold:
    (none)
  detected (validated candidates, before scope/threshold/resolution):
    (none)
  resolved (applied) spans:
    (none)
  sanitized: 'Units 24; year 2026; code cust-100006; token XCUST-100006; short CUST-10006.'
  payload captured by RecordingMock: {'request_id': 'demo-001', 'text': 'Units 24; year 2026; code cust-100006; token XCUST-100006; short CUST-10006.'} (calls=1)
  equals fixture oracle: True  (oracle is a check only, never a shortcut)
--- Unicode offsets (emoji and accent before the fields) [dev-004]
  original : '🔒 Café: leo@example.net / CUST-100004.'
  gold:
    EMAIL_ADDRESS [8:23] 'leo@example.net'
    CUSTOMER_ID   [26:37] 'CUST-100004'
  detected (validated candidates, before scope/threshold/resolution):
    EMAIL_ADDRESS [8:23] 'leo@example.net' score=1.0
    CUSTOMER_ID   [26:37] 'CUST-100004' score=1.0
  resolved (applied) spans:
    EMAIL_ADDRESS [8:23] 'leo@example.net' score=1.0
    CUSTOMER_ID   [26:37] 'CUST-100004' score=1.0
  sanitized: '🔒 Café: [EMAIL_ADDRESS] / [CUSTOMER_ID].'
  payload captured by RecordingMock: {'request_id': 'demo-001', 'text': '🔒 Café: [EMAIL_ADDRESS] / [CUSTOMER_ID].'} (calls=1)
  equals fixture oracle: True  (oracle is a check only, never a shortcut)
--- repeated value at two positions [dev-003]
  original : 'Copy maya+lab@example.org and maya+lab@example.org; 2 copies.'
  gold:
    EMAIL_ADDRESS [5:25] 'maya+lab@example.org'
    EMAIL_ADDRESS [30:50] 'maya+lab@example.org'
  detected (validated candidates, before scope/threshold/resolution):
    EMAIL_ADDRESS [5:25] 'maya+lab@example.org' score=1.0
    EMAIL_ADDRESS [30:50] 'maya+lab@example.org' score=1.0
  resolved (applied) spans:
    EMAIL_ADDRESS [5:25] 'maya+lab@example.org' score=1.0
    EMAIL_ADDRESS [30:50] 'maya+lab@example.org' score=1.0
  sanitized: 'Copy [EMAIL_ADDRESS] and [EMAIL_ADDRESS]; 2 copies.'
  payload captured by RecordingMock: {'request_id': 'demo-001', 'text': 'Copy [EMAIL_ADDRESS] and [EMAIL_ADDRESS]; 2 copies.'} (calls=1)
  equals fixture oracle: True  (oracle is a check only, never a shortcut)
--- CRLF and tab preserved [dev-009]
  original : 'Line A\r\nPhone (240) 555-0111\r\nReference CUST-100009\tend.'
  gold:
    PHONE_NUMBER  [14:28] '(240) 555-0111'
    CUSTOMER_ID   [40:51] 'CUST-100009'
  detected (validated candidates, before scope/threshold/resolution):
    PHONE_NUMBER  [14:28] '(240) 555-0111' score=1.0
    CUSTOMER_ID   [40:51] 'CUST-100009' score=1.0
  resolved (applied) spans:
    PHONE_NUMBER  [14:28] '(240) 555-0111' score=1.0
    CUSTOMER_ID   [40:51] 'CUST-100009' score=1.0
  sanitized: 'Line A\r\nPhone [PHONE_NUMBER]\r\nReference [CUSTOMER_ID]\tend.'
  payload captured by RecordingMock: {'request_id': 'demo-001', 'text': 'Line A\r\nPhone [PHONE_NUMBER]\r\nReference [CUSTOMER_ID]\tend.'} (calls=1)
  equals fixture oracle: True  (oracle is a check only, never a shortcut)
--- detector failure (demo-local failing detector; zero provider calls)
  fixed code: SANITIZER_DETECTOR_ERROR; provider calls = 0; the exception text is not exposed

=== Held-out misses and unnecessary redactions (baseline) ===
  actual missed gold spans (exact-span FN): 0; unnecessary or imprecise redactions (touch benign characters or are FP): 0
  first missed gold field: zero observed on these fixtures
  first unnecessary redaction: zero observed on these fixtures
````

### F5 baseline: evaluate development

Command: `python -m sanitizer evaluate --detector baseline --split development` | exit status: 0

````
baseline on development (thresholds {'EMAIL_ADDRESS': 1.0, 'PHONE_NUMBER': 1.0, 'CUSTOMER_ID': 1.0}); report written
EMAIL_ADDRESS  TP=7 FP=0 FN=0 precision=1.0000 recall=1.0000 f1=1.0000
PHONE_NUMBER   TP=4 FP=0 FN=0 precision=1.0000 recall=1.0000 f1=1.0000
CUSTOMER_ID    TP=5 FP=0 FN=0 precision=1.0000 recall=1.0000 f1=1.0000
micro          TP=16 FP=0 FN=0 precision=1.0000 recall=1.0000 f1=1.0000
coverage       full=16 partial=0 untouched=0 rate=1.0000
benign         replacements_touching_benign=0 replacements_touching_no_gold=0 benign_characters_removed=0
preservation   no_gold_preserved=2/2 equal_expected=10/10
````

### F5 baseline: evaluate heldout

Command: `python -m sanitizer evaluate --detector baseline --split heldout` | exit status: 0

````
baseline on heldout (thresholds {'EMAIL_ADDRESS': 1.0, 'PHONE_NUMBER': 1.0, 'CUSTOMER_ID': 1.0}); report written
EMAIL_ADDRESS  TP=12 FP=0 FN=0 precision=1.0000 recall=1.0000 f1=1.0000
PHONE_NUMBER   TP=8 FP=0 FN=0 precision=1.0000 recall=1.0000 f1=1.0000
CUSTOMER_ID    TP=8 FP=0 FN=0 precision=1.0000 recall=1.0000 f1=1.0000
micro          TP=28 FP=0 FN=0 precision=1.0000 recall=1.0000 f1=1.0000
coverage       full=28 partial=0 untouched=0 rate=1.0000
benign         replacements_touching_benign=0 replacements_touching_no_gold=0 benign_characters_removed=0
preservation   no_gold_preserved=5/5 equal_expected=18/18
````

### F6 baseline: deterministic rerun matches committed reports

Command: `python scripts/check_reports.py baseline` | exit status: 0

````
baseline  development  rerun matches committed report: True
baseline  heldout      rerun matches committed report: True
````

### F7 no Presidio in the base interpreter: fixed code, zero dispatch

Command: `python -m sanitizer run --detector presidio --request-id demo-001   [stdin: the dev-001 text as exact bytes]` | exit status: 2

````
--- stderr ---
SANITIZER_DETECTOR_UNAVAILABLE
````

### F8 README claim: held-out needs the frozen config

Command: `python -m sanitizer evaluate --detector baseline --split heldout --config does-not-exist.json` | exit status: 2

````
--- stderr ---
SANITIZER_FROZEN_CONFIG_REQUIRED
````

### F9 candidate: create a fresh venv (README uses C:\pv; a short path inside the session folder was used instead)

Command: `python -m venv <SHORT_PATH>\fv` | exit status: 0

````
(no output)
````

### F10 candidate: install pinned requirements (network)

Command: `<SHORT_PATH>\fv\Scripts\python -m pip install -r requirements-presidio.txt` | exit status: 0

````
Successfully installed Jinja2-3.1.6 MarkupSafe-3.0.4 PyYAML-6.0.3 Pygments-2.21.0 annotated-doc-0.0.6 annotated-types-0.8.0 anyio-4.16.0 blis-1.3.4 catalogue-2.0.10 certifi-2026.10.23 charset-normalizer-3.5.2 click-8.5.1 cloudpathlib-0.26.0 colorama-0.4.6 confection-1.3.4 cymem-2.0.16 en_core_web_sm-3.8.0 filelock-4.2.10 h11-0.16.0 httpcore-1.0.9 httpx-0.28.1 idna-3.20 markdown-it-py-4.3.0 mdurl-0.1.2 murmurhash-1.0.16 numpy-2.4.6 packaging-26.3 phonenumbers-9.0.43 preshed-3.0.13 presidio_analyzer-2.2.366 pydantic-2.14.3 pydantic_core-2.50.4 regex-2026.11.9 requests-2.34.2 requests-file-3.0.1 rich-15.0.0 setuptools-84.2.1 shellingham-1.5.4 smart_open-9.0.3 spacy-3.8.18 spacy-legacy-3.0.12 spacy-loggers-1.0.5 srsly-2.5.6 thinc-8.3.14 tldextract-5.4.0 tqdm-4.70.1 typer-0.29.0 typing-inspection-0.4.5 typing_extensions-4.16.0 urllib3-2.8.0 wasabi-1.1.3 weasel-1.0.1 wrapt-2.5.2
````

### F11 candidate: pip check

Command: `<SHORT_PATH>\fv\Scripts\python -m pip check` | exit status: 0

````
No broken requirements found.
````

### F12 candidate: full suite, no skips allowed

Command: `& $PV\Scripts\python scripts/run_tests_no_skips.py   [the script sets REQUIRE_CANDIDATE_TESTS=1 itself]` | exit status: 0

````

ran=154 failures=0 errors=0 skipped=0
--- stderr ---
test_candidate_demo_runs_and_is_labelled (tests.test_cli.CandidateCli.test_candidate_demo_runs_and_is_labelled) ... ok
test_candidate_development_evaluation_is_deterministic (tests.test_cli.CandidateCli.test_candidate_development_evaluation_is_deterministic) ... ok
test_presidio_run_prints_nothing_extra_to_the_terminal (tests.test_cli.CandidateCli.test_presidio_run_prints_nothing_extra_to_the_terminal) ... ok
test_presidio_run_with_the_frozen_config (tests.test_cli.CandidateCli.test_presidio_run_with_the_frozen_config) ... ok
test_initialization_failure_message_is_never_exposed (tests.test_cli.CandidateUnavailable.test_initialization_failure_message_is_never_exposed) ... ok
test_missing_invalid_or_mismatched_config_is_a_fixed_code (tests.test_cli.CandidateUnavailable.test_missing_invalid_or_mismatched_config_is_a_fixed_code) ... ok
test_missing_package_in_a_real_process (tests.test_cli.CandidateUnavailable.test_missing_package_in_a_real_process) ... ok
test_missing_package_in_process (tests.test_cli.CandidateUnavailable.test_missing_package_in_process) ... ok
test_baseline_demo_shows_labelled_synthetic_inspection (tests.test_cli.DemoCommand.test_baseline_demo_shows_labelled_synthetic_inspection) ... ok
test_demo_has_no_way_to_supply_text_or_pick_a_real_provider (tests.test_cli.DemoCommand.test_demo_has_no_way_to_supply_text_or_pick_a_real_provider) ... ok
test_presidio_demo_without_dependency_is_a_fixed_code (tests.test_cli.DemoCommand.test_presidio_demo_without_dependency_is_a_fixed_code) ... ok
test_baseline_development_report_is_deterministic_and_privacy_safe (tests.test_cli.EvaluationCommands.test_baseline_development_report_is_deterministic_and_privacy_safe) ... ok
test_debug_thresholds_are_development_only (tests.test_cli.EvaluationCommands.test_debug_thresholds_are_development_only) ... ok
test_heldout_requires_the_frozen_config (tests.test_cli.EvaluationCommands.test_heldout_requires_the_frozen_config) ... ok
test_report_separates_accuracy_from_provider_boundary (tests.test_cli.EvaluationCommands.test_report_separates_accuracy_from_provider_boundary) ... ok
test_select_thresholds_refuses_to_overwrite_a_freeze (tests.test_cli.EvaluationCommands.test_select_thresholds_refuses_to_overwrite_a_freeze) ... ok
test_default_detector_and_output_are_unchanged (tests.test_cli.RunCommand.test_default_detector_and_output_are_unchanged) ... ok
test_explicit_baseline_detector_handles_all_three_entities (tests.test_cli.RunCommand.test_explicit_baseline_detector_handles_all_three_entities) ... ok
test_summary_flag_adds_counts_outside_the_provider_object (tests.test_cli.RunCommand.test_summary_flag_adds_counts_outside_the_provider_object) ... ok
test_unknown_detector_choice_is_an_argument_error (tests.test_cli.RunCommand.test_unknown_detector_choice_is_an_argument_error) ... ok
test_all_three_entity_canary_payload_is_exactly_the_sanitized_text (tests.test_detectors_boundary.BaselineBoundary.test_all_three_entity_canary_payload_is_exactly_the_sanitized_text) ... ok
test_detector_failure_and_malformed_output_give_zero_provider_calls (tests.test_detectors_boundary.BaselineBoundary.test_detector_failure_and_malformed_output_give_zero_provider_calls) ... ok
test_documented_misses_are_accuracy_failures_not_boundary_failures (tests.test_detectors_boundary.BaselineBoundary.test_documented_misses_are_accuracy_failures_not_boundary_failures) ... ok
test_every_development_payload_equals_the_actual_sanitized_text_even_on_misses (tests.test_detectors_boundary.BaselineBoundary.test_every_development_payload_equals_the_actual_sanitized_text_even_on_misses) ... ok
test_known_correct_development_cases_have_exact_payload (tests.test_detectors_boundary.BaselineBoundary.test_known_correct_development_cases_have_exact_payload) ... ok
test_logs_at_root_debug_contain_only_approved_metadata (tests.test_detectors_boundary.BaselineBoundary.test_logs_at_root_debug_contain_only_approved_metadata) ... ok
test_provider_exception_is_distinct_from_detector_failure (tests.test_detectors_boundary.BaselineBoundary.test_provider_exception_is_distinct_from_detector_failure) ... ok
test_all_three_entity_canary_payload_is_exactly_the_sanitized_text (tests.test_detectors_boundary.PresidioBoundary.test_all_three_entity_canary_payload_is_exactly_the_sanitized_text) ... ok
test_detector_failure_and_malformed_output_give_zero_provider_calls (tests.test_detectors_boundary.PresidioBoundary.test_detector_failure_and_malformed_output_give_zero_provider_calls) ... ok
test_documented_misses_are_accuracy_failures_not_boundary_failures (tests.test_detectors_boundary.PresidioBoundary.test_documented_misses_are_accuracy_failures_not_boundary_failures) ... ok
test_every_development_payload_equals_the_actual_sanitized_text_even_on_misses (tests.test_detectors_boundary.PresidioBoundary.test_every_development_payload_equals_the_actual_sanitized_text_even_on_misses) ... ok
test_known_correct_development_cases_have_exact_payload (tests.test_detectors_boundary.PresidioBoundary.test_known_correct_development_cases_have_exact_payload) ... ok
test_logs_at_root_debug_contain_only_approved_metadata (tests.test_detectors_boundary.PresidioBoundary.test_logs_at_root_debug_contain_only_approved_metadata) ... ok
test_provider_exception_is_distinct_from_detector_failure (tests.test_detectors_boundary.PresidioBoundary.test_provider_exception_is_distinct_from_detector_failure) ... ok
test_readme_summary_block_equals_the_rendered_reports (tests.test_docs.ReadmeMatchesReports.test_readme_summary_block_equals_the_rendered_reports) ... ok
test_required_documents_exist (tests.test_docs.ReadmeMatchesReports.test_required_documents_exist) ... ok
test_summary_file_is_current (tests.test_docs.ReadmeMatchesReports.test_summary_file_is_current) ... ok
test_cli_and_core_do_not_import_presidio_or_spacy (tests.test_docs.StdlibBaselineStaysStdlib.test_cli_and_core_do_not_import_presidio_or_spacy) ... ok
test_structure_by_text (tests.test_docs.WorkflowKeepsItsGuarantees.test_structure_by_text) ... ok
test_structure_by_yaml (tests.test_docs.WorkflowKeepsItsGuarantees.test_structure_by_yaml) ... ok
test_heldout_fixture_matches_summary_and_is_self_consistent (tests.test_frozen_config.FixtureIntegrityAfterFreeze.test_heldout_fixture_matches_summary_and_is_self_consistent) ... ok
test_hashes_match_the_handoff_fixtures_and_files_on_disk (tests.test_frozen_config.FrozenConfig.test_hashes_match_the_handoff_fixtures_and_files_on_disk) ... ok
test_mismatched_or_missing_fixture_bytes_are_rejected (tests.test_frozen_config.FrozenConfig.test_mismatched_or_missing_fixture_bytes_are_rejected) ... ok
test_model_hash_matches_the_requirements_pin (tests.test_frozen_config.FrozenConfig.test_model_hash_matches_the_requirements_pin) ... ok
test_records_the_required_freeze_metadata (tests.test_frozen_config.FrozenConfig.test_records_the_required_freeze_metadata) ... ok
test_selected_thresholds_follow_the_selection_rule_over_the_stored_grid (tests.test_frozen_config.FrozenConfig.test_selected_thresholds_follow_the_selection_rule_over_the_stored_grid) ... ok
test_rerunning_the_development_selection_reproduces_the_frozen_thresholds (tests.test_frozen_config.SelectionReproducible.test_rerunning_the_development_selection_reproduces_the_frozen_thresholds) ... ok
test_boundaries_allow_punctuation_and_whitespace (tests.test_pipeline.PhoneBaseline.test_boundaries_allow_punctuation_and_whitespace) ... ok
test_digit_ranges (tests.test_pipeline.PhoneBaseline.test_digit_ranges) ... ok
test_exact_format_detected (tests.test_pipeline.PhoneBaseline.test_exact_format_detected) ... ok
test_out_of_scope_formats_are_not_detected (tests.test_pipeline.PhoneBaseline.test_out_of_scope_formats_are_not_detected) ... ok
test_all_spans_are_validated_before_the_gate_or_thresholds (tests.test_pipeline.ScopeGate.test_all_spans_are_validated_before_the_gate_or_thresholds) ... ok
test_exact_match_is_kept (tests.test_pipeline.ScopeGate.test_exact_match_is_kept) ... ok
test_gate_applies_only_to_phone_candidates (tests.test_pipeline.ScopeGate.test_gate_applies_only_to_phone_candidates) ... ok
test_gate_does_not_insert_missing_detections (tests.test_pipeline.ScopeGate.test_gate_does_not_insert_missing_detections) ... ok
test_trimmed_expanded_and_shifted_candidates_are_dropped_not_repaired (tests.test_pipeline.ScopeGate.test_trimmed_expanded_and_shifted_candidates_are_dropped_not_repaired) ... ok
test_unsupported_format_phone_candidate_is_dropped (tests.test_pipeline.ScopeGate.test_unsupported_format_phone_candidate_is_dropped) ... ok
test_sanitize_dispatch_and_run_pipeline_agree (tests.test_pipeline.SharedPipeline.test_sanitize_dispatch_and_run_pipeline_agree) ... ok
test_dedupe_keeps_highest_score_for_same_type_and_range (tests.test_pipeline.Thresholds.test_dedupe_keeps_highest_score_for_same_type_and_range) ... ok
test_no_thresholds_accepts_every_valid_score (tests.test_pipeline.Thresholds.test_no_thresholds_accepts_every_valid_score) ... ok
test_score_equal_to_threshold_passes_and_below_fails (tests.test_pipeline.Thresholds.test_score_equal_to_threshold_passes_and_below_fails) ... ok
test_thresholds_are_per_type (tests.test_pipeline.Thresholds.test_thresholds_are_per_type) ... ok
test_adjacent_nonoverlapping_spans_are_both_kept (tests.test_pipeline.TypePriorityTies.test_adjacent_nonoverlapping_spans_are_both_kept) ... ok
test_all_pairwise_ties_same_range (tests.test_pipeline.TypePriorityTies.test_all_pairwise_ties_same_range) ... ok
test_customer_id_inside_an_email_loses_to_the_whole_email (tests.test_pipeline.TypePriorityTies.test_customer_id_inside_an_email_loses_to_the_whole_email) ... ok
test_length_then_score_precede_type (tests.test_pipeline.TypePriorityTies.test_length_then_score_precede_type) ... ok
test_ties_with_offset_overlap_use_type_before_start (tests.test_pipeline.TypePriorityTies.test_ties_with_offset_overlap_use_type_before_start) ... ok
test_customer_id_rule_is_case_sensitive_with_token_boundaries (tests.test_presidio_optional.PresidioConfiguration.test_customer_id_rule_is_case_sensitive_with_token_boundaries) ... ok
test_engine_candidates_for_dev_001 (tests.test_presidio_optional.PresidioConfiguration.test_engine_candidates_for_dev_001) ... ok
test_frozen_config_records_the_live_recognizer_settings (tests.test_presidio_optional.PresidioConfiguration.test_frozen_config_records_the_live_recognizer_settings) ... ok
test_no_input_text_in_logs_at_root_debug (tests.test_presidio_optional.PresidioConfiguration.test_no_input_text_in_logs_at_root_debug) ... ok
test_no_network_and_no_cache_writes_in_a_fresh_process (tests.test_presidio_optional.PresidioConfiguration.test_no_network_and_no_cache_writes_in_a_fresh_process) ... ok
test_only_selected_recognizers_loaded (tests.test_presidio_optional.PresidioConfiguration.test_only_selected_recognizers_loaded) ... ok
test_phone_recognizer_is_us_only_and_no_ner_recognizer_registered (tests.test_presidio_optional.PresidioConfiguration.test_phone_recognizer_is_us_only_and_no_ner_recognizer_registered) ... ok
test_sanitized_text_and_payload_exact (tests.test_presidio_optional.PresidioConfiguration.test_sanitized_text_and_payload_exact) ... ok
test_stock_email_probe_is_not_a_cli_route (tests.test_presidio_optional.PresidioConfiguration.test_stock_email_probe_is_not_a_cli_route) ... ok
test_unsupported_phone_format_is_gated_out_of_the_applied_spans (tests.test_presidio_optional.PresidioConfiguration.test_unsupported_phone_format_is_gated_out_of_the_applied_spans) ... ok
test_explicit_help_still_works (tests.test_sanitizer.ArgumentErrors.test_explicit_help_still_works) ... ok
test_in_process_parser_failure_logs_only_code (tests.test_sanitizer.ArgumentErrors.test_in_process_parser_failure_logs_only_code) ... ok
test_parser_failures_are_fixed_code_and_never_echo_values (tests.test_sanitizer.ArgumentErrors.test_parser_failures_are_fixed_code_and_never_echo_values) ... ok
test_valid_invocation_unaffected (tests.test_sanitizer.ArgumentErrors.test_valid_invocation_unaffected) ... ok
test_inspect_fixture_is_the_explicit_synthetic_view (tests.test_sanitizer.Cli.test_inspect_fixture_is_the_explicit_synthetic_view) ... ok
test_success_prints_only_captured_payload (tests.test_sanitizer.Cli.test_success_prints_only_captured_payload) ... ok
test_cli_contract (tests.test_sanitizer.DetectorFailure.test_cli_contract) ... ok
test_exception_stops_dispatch_without_leaking (tests.test_sanitizer.DetectorFailure.test_exception_stops_dispatch_without_leaking) ... ok
test_detected_spans_match_expected (tests.test_sanitizer.Dev001.test_detected_spans_match_expected) ... ok
test_fixture_matches_contract_and_slices (tests.test_sanitizer.Dev001.test_fixture_matches_contract_and_slices) ... ok
test_mock_payload_exact (tests.test_sanitizer.Dev001.test_mock_payload_exact) ... ok
test_sanitized_text_exact (tests.test_sanitizer.Dev001.test_sanitized_text_exact) ... ok
test_empty_is_valid (tests.test_sanitizer.EmptyInput.test_empty_is_valid) ... ok
test_empty_via_cli (tests.test_sanitizer.EmptyInput.test_empty_via_cli) ... ok
test_library_wraps_provider_exception (tests.test_sanitizer.InternalError.test_library_wraps_provider_exception) ... ok
test_provider_exception_with_canaries (tests.test_sanitizer.InternalError.test_provider_exception_with_canaries) ... ok
test_unexpected_exception_inside_sanitizer (tests.test_sanitizer.InternalError.test_unexpected_exception_inside_sanitizer) ... ok
test_boundary_scores_still_accepted (tests.test_sanitizer.InvalidDetectorOutput.test_boundary_scores_still_accepted) ... ok
test_cli_contract (tests.test_sanitizer.InvalidDetectorOutput.test_cli_contract) ... ok
test_each_malformed_output_stops_dispatch (tests.test_sanitizer.InvalidDetectorOutput.test_each_malformed_output_stops_dispatch) ... ok
test_hostile_span_object_is_invalid_output_not_crash (tests.test_sanitizer.InvalidDetectorOutput.test_hostile_span_object_is_invalid_output_not_crash) ... ok
test_huge_integer_scores_via_cli_not_internal_error (tests.test_sanitizer.InvalidDetectorOutput.test_huge_integer_scores_via_cli_not_internal_error) ... ok
test_validator_itself_rejects_huge_ints_without_overflow (tests.test_sanitizer.InvalidDetectorOutput.test_validator_itself_rejects_huge_ints_without_overflow) ... ok
test_byte_bound_precedes_decoding_and_chars_checked_after (tests.test_sanitizer.InvalidEncoding.test_byte_bound_precedes_decoding_and_chars_checked_after) ... ok
test_in_process_no_detection_no_dispatch (tests.test_sanitizer.InvalidEncoding.test_in_process_no_detection_no_dispatch) ... ok
test_default_logs_contain_no_canaries_on_success_and_failure (tests.test_sanitizer.Logging.test_default_logs_contain_no_canaries_on_success_and_failure) ... ok
test_real_process_default_logging (tests.test_sanitizer.Logging.test_real_process_default_logging) ... ok
test_every_log_line_is_approved (tests.test_sanitizer.LoggingAllowlist.test_every_log_line_is_approved) ... ok
test_logs_never_contain_request_id (tests.test_sanitizer.LoggingAllowlist.test_logs_never_contain_request_id) ... ok
test_real_process_with_root_logging_configured (tests.test_sanitizer.LoggingAllowlist.test_real_process_with_root_logging_configured) ... ok
test_dedupe_and_adjacent_spans_kept (tests.test_sanitizer.OverlapResolution.test_dedupe_and_adjacent_spans_kept) ... ok
test_earlier_start_on_full_tie (tests.test_sanitizer.OverlapResolution.test_earlier_start_on_full_tie) ... ok
test_email_before_customer_id_on_tie (tests.test_sanitizer.OverlapResolution.test_email_before_customer_id_on_tie) ... ok
test_higher_score_on_equal_length (tests.test_sanitizer.OverlapResolution.test_higher_score_on_equal_length) ... ok
test_ints_accepted_as_scores (tests.test_sanitizer.OverlapResolution.test_ints_accepted_as_scores) ... ok
test_longest_wins (tests.test_sanitizer.OverlapResolution.test_longest_wins) ... ok
test_cli_contract_real_process (tests.test_sanitizer.OversizedInput.test_cli_contract_real_process) ... ok
test_limit_is_inclusive_and_counts_characters (tests.test_sanitizer.OversizedInput.test_limit_is_inclusive_and_counts_characters) ... ok
test_rejected_before_detection_and_dispatch (tests.test_sanitizer.OversizedInput.test_rejected_before_detection_and_dispatch) ... ok
test_benign_numbers_and_punctuation_untouched (tests.test_sanitizer.Preservation.test_benign_numbers_and_punctuation_untouched) ... ok
test_customer_id_boundaries (tests.test_sanitizer.Preservation.test_customer_id_boundaries) ... ok
test_no_unicode_normalization_and_char_offsets (tests.test_sanitizer.Preservation.test_no_unicode_normalization_and_char_offsets) ... ok
test_surrounding_punctuation_and_whitespace_preserved (tests.test_sanitizer.Preservation.test_surrounding_punctuation_and_whitespace_preserved) ... ok
test_crlf_input_not_normalized (tests.test_sanitizer.RealProcessBytes.test_crlf_input_not_normalized) ... ok
test_invalid_utf8_rejected_real_process (tests.test_sanitizer.RealProcessBytes.test_invalid_utf8_rejected_real_process) ... ok
test_valid_utf8_edge_cases_accepted (tests.test_sanitizer.RealProcessBytes.test_valid_utf8_edge_cases_accepted) ... ok
test_canary_ids_never_reach_provider_or_logs (tests.test_sanitizer.RequestIdBoundary.test_canary_ids_never_reach_provider_or_logs) ... ok
test_cli_in_process (tests.test_sanitizer.RequestIdBoundary.test_cli_in_process) ... ok
test_cli_real_process (tests.test_sanitizer.RequestIdBoundary.test_cli_real_process) ... ok
test_invalid_ids_rejected_before_detector_and_provider (tests.test_sanitizer.RequestIdBoundary.test_invalid_ids_rejected_before_detector_and_provider) ... ok
test_request_id_checked_before_stdin_is_decoded (tests.test_sanitizer.RequestIdBoundary.test_request_id_checked_before_stdin_is_decoded) ... ok
test_str_subclass_rejected (tests.test_sanitizer.RequestIdBoundary.test_str_subclass_rejected) ... ok
test_valid_ids_accepted_and_passed_through (tests.test_sanitizer.RequestIdBoundary.test_valid_ids_accepted_and_passed_through) ... ok
test_counts_are_summed_before_micro_metrics (tests.test_scoring.AggregateThroughRealPipeline.test_counts_are_summed_before_micro_metrics) ... ok
test_detector_failure_counts_gold_as_missed_with_zero_calls (tests.test_scoring.AggregateThroughRealPipeline.test_detector_failure_counts_gold_as_missed_with_zero_calls) ... ok
test_adjacent_intervals_union_covers_gold_but_is_not_an_exact_match (tests.test_scoring.EdgeCases.test_adjacent_intervals_union_covers_gold_but_is_not_an_exact_match) ... ok
test_benign_only_example_with_a_replacement_is_all_benign (tests.test_scoring.EdgeCases.test_benign_only_example_with_a_replacement_is_all_benign) ... ok
test_empty_gold_and_empty_predictions (tests.test_scoring.EdgeCases.test_empty_gold_and_empty_predictions) ... ok
test_metric_null_rules (tests.test_scoring.EdgeCases.test_metric_null_rules) ... ok
test_partial_interval_is_one_fp_and_one_fn (tests.test_scoring.EdgeCases.test_partial_interval_is_one_fp_and_one_fn) ... ok
test_repeated_values_are_separate_gold_entities (tests.test_scoring.EdgeCases.test_repeated_values_are_separate_gold_entities) ... ok
test_unicode_offsets_are_code_points (tests.test_scoring.EdgeCases.test_unicode_offsets_are_code_points) ... ok
test_wrong_type_with_full_coverage (tests.test_scoring.EdgeCases.test_wrong_type_with_full_coverage) ... ok
test_development_fixture_loads_and_matches_summary (tests.test_scoring.FixtureLoading.test_development_fixture_loads_and_matches_summary) ... ok
test_development_gold_slices_and_oracles_are_self_consistent (tests.test_scoring.FixtureLoading.test_development_gold_slices_and_oracles_are_self_consistent) ... ok
test_fixtures_are_the_unchanged_handoff_files (tests.test_scoring.FixtureLoading.test_fixtures_are_the_unchanged_handoff_files) ... ok
test_malformed_fixture_is_rejected_with_fixed_code (tests.test_scoring.FixtureLoading.test_malformed_fixture_is_rejected_with_fixed_code) ... ok
test_benign_statistics (tests.test_scoring.HandCalculatedOracle.test_benign_statistics) ... ok
test_counts_and_micro_metrics (tests.test_scoring.HandCalculatedOracle.test_counts_and_micro_metrics) ... ok
test_coverage (tests.test_scoring.HandCalculatedOracle.test_coverage) ... ok
test_per_type_counts (tests.test_scoring.HandCalculatedOracle.test_per_type_counts) ... ok
test_replacement_output (tests.test_scoring.HandCalculatedOracle.test_replacement_output) ... ok
test_false_positive_is_cut_by_raising_its_threshold (tests.test_scoring.ThresholdSelection.test_false_positive_is_cut_by_raising_its_threshold) ... ok
test_grid_is_125_and_ties_prefer_higher_thresholds (tests.test_scoring.ThresholdSelection.test_grid_is_125_and_ties_prefer_higher_thresholds) ... ok
test_no_predictions_has_f1_zero_and_selection_still_defined (tests.test_scoring.ThresholdSelection.test_no_predictions_has_f1_zero_and_selection_still_defined) ... ok
test_threshold_is_inclusive_and_picks_highest_passing_value (tests.test_scoring.ThresholdSelection.test_threshold_is_inclusive_and_picks_highest_passing_value) ... ok
test_tie_break_order_is_f1_then_fewer_benign_then_higher_thresholds (tests.test_scoring.ThresholdSelection.test_tie_break_order_is_f1_then_fewer_benign_then_higher_thresholds) ... ok

----------------------------------------------------------------------
Ran 154 tests in 10.403s

OK
````

### F13 candidate: dev-001 + summary through the CLI

Command: `& $PV\Scripts\python -m sanitizer run --detector presidio --summary --request-id demo-001   [stdin: the canary text as exact bytes]` | exit status: 0

````
{"payload": {"request_id": "demo-001", "text": "Email [EMAIL_ADDRESS]; phone [PHONE_NUMBER]; customer [CUSTOMER_ID]; quantity 24."}, "entity_counts": {"EMAIL_ADDRESS": 1, "PHONE_NUMBER": 1, "CUSTOMER_ID": 1}}
````

### F14 candidate: explicit synthetic demo

Command: `<venv>python -m sanitizer demo --detector presidio` | exit status: 0

````
==============================================================================
SYNTHETIC INSPECTION. Every value below is fabricated fixture data printed on purpose.
detector: presidio | thresholds: {'EMAIL_ADDRESS': 1.0, 'PHONE_NUMBER': 0.4, 'CUSTOMER_ID': 1.0}
No user text is accepted here; payloads come from the in-memory RecordingMock only.
==============================================================================
--- all-three-entity canary
  original : 'Email ava@example.com; phone (415) 555-0132; customer CUST-004271; quantity 24.'
  gold:
    EMAIL_ADDRESS [6:21] 'ava@example.com'
    PHONE_NUMBER  [29:43] '(415) 555-0132'
    CUSTOMER_ID   [54:65] 'CUST-004271'
  detected (validated candidates, before scope/threshold/resolution):
    EMAIL_ADDRESS [6:21] 'ava@example.com' score=1.0
    PHONE_NUMBER  [29:43] '(415) 555-0132' score=0.75
    CUSTOMER_ID   [54:65] 'CUST-004271' score=1.0
  resolved (applied) spans:
    EMAIL_ADDRESS [6:21] 'ava@example.com' score=1.0
    PHONE_NUMBER  [29:43] '(415) 555-0132' score=0.75
    CUSTOMER_ID   [54:65] 'CUST-004271' score=1.0
  sanitized: 'Email [EMAIL_ADDRESS]; phone [PHONE_NUMBER]; customer [CUSTOMER_ID]; quantity 24.'
  payload captured by RecordingMock: {'request_id': 'demo-001', 'text': 'Email [EMAIL_ADDRESS]; phone [PHONE_NUMBER]; customer [CUSTOMER_ID]; quantity 24.'} (calls=1)
  equals fixture oracle: True  (oracle is a check only, never a shortcut)
--- benign preservation (no gold; output must equal input) [dev-006]
  original : 'Units 24; year 2026; code cust-100006; token XCUST-100006; short CUST-10006.'
  gold:
    (none)
  detected (validated candidates, before scope/threshold/resolution):
    (none)
  resolved (applied) spans:
    (none)
  sanitized: 'Units 24; year 2026; code cust-100006; token XCUST-100006; short CUST-10006.'
  payload captured by RecordingMock: {'request_id': 'demo-001', 'text': 'Units 24; year 2026; code cust-100006; token XCUST-100006; short CUST-10006.'} (calls=1)
  equals fixture oracle: True  (oracle is a check only, never a shortcut)
--- Unicode offsets (emoji and accent before the fields) [dev-004]
  original : '🔒 Café: leo@example.net / CUST-100004.'
  gold:
    EMAIL_ADDRESS [8:23] 'leo@example.net'
    CUSTOMER_ID   [26:37] 'CUST-100004'
  detected (validated candidates, before scope/threshold/resolution):
    EMAIL_ADDRESS [8:23] 'leo@example.net' score=1.0
    CUSTOMER_ID   [26:37] 'CUST-100004' score=1.0
  resolved (applied) spans:
    EMAIL_ADDRESS [8:23] 'leo@example.net' score=1.0
    CUSTOMER_ID   [26:37] 'CUST-100004' score=1.0
  sanitized: '🔒 Café: [EMAIL_ADDRESS] / [CUSTOMER_ID].'
  payload captured by RecordingMock: {'request_id': 'demo-001', 'text': '🔒 Café: [EMAIL_ADDRESS] / [CUSTOMER_ID].'} (calls=1)
  equals fixture oracle: True  (oracle is a check only, never a shortcut)
--- repeated value at two positions [dev-003]
  original : 'Copy maya+lab@example.org and maya+lab@example.org; 2 copies.'
  gold:
    EMAIL_ADDRESS [5:25] 'maya+lab@example.org'
    EMAIL_ADDRESS [30:50] 'maya+lab@example.org'
  detected (validated candidates, before scope/threshold/resolution):
    EMAIL_ADDRESS [5:25] 'maya+lab@example.org' score=1.0
    EMAIL_ADDRESS [30:50] 'maya+lab@example.org' score=1.0
  resolved (applied) spans:
    EMAIL_ADDRESS [5:25] 'maya+lab@example.org' score=1.0
    EMAIL_ADDRESS [30:50] 'maya+lab@example.org' score=1.0
  sanitized: 'Copy [EMAIL_ADDRESS] and [EMAIL_ADDRESS]; 2 copies.'
  payload captured by RecordingMock: {'request_id': 'demo-001', 'text': 'Copy [EMAIL_ADDRESS] and [EMAIL_ADDRESS]; 2 copies.'} (calls=1)
  equals fixture oracle: True  (oracle is a check only, never a shortcut)
--- CRLF and tab preserved [dev-009]
  original : 'Line A\r\nPhone (240) 555-0111\r\nReference CUST-100009\tend.'
  gold:
    PHONE_NUMBER  [14:28] '(240) 555-0111'
    CUSTOMER_ID   [40:51] 'CUST-100009'
  detected (validated candidates, before scope/threshold/resolution):
    PHONE_NUMBER  [14:28] '(240) 555-0111' score=0.75
    CUSTOMER_ID   [40:51] 'CUST-100009' score=1.0
  resolved (applied) spans:
    PHONE_NUMBER  [14:28] '(240) 555-0111' score=0.75
    CUSTOMER_ID   [40:51] 'CUST-100009' score=1.0
  sanitized: 'Line A\r\nPhone [PHONE_NUMBER]\r\nReference [CUSTOMER_ID]\tend.'
  payload captured by RecordingMock: {'request_id': 'demo-001', 'text': 'Line A\r\nPhone [PHONE_NUMBER]\r\nReference [CUSTOMER_ID]\tend.'} (calls=1)
  equals fixture oracle: True  (oracle is a check only, never a shortcut)
--- detector failure (demo-local failing detector; zero provider calls)
  fixed code: SANITIZER_DETECTOR_ERROR; provider calls = 0; the exception text is not exposed

=== Held-out misses and unnecessary redactions (presidio) ===
  actual missed gold spans (exact-span FN): 2; unnecessary or imprecise redactions (touch benign characters or are FP): 1
  first missed gold field: example test-010
    text: 'Audit destination audit@records.invalid; batch 64 closed.'
    missed gold: EMAIL_ADDRESS [18:39] 'audit@records.invalid' (coverage untouched)
    all gold: EMAIL_ADDRESS[18:39]='audit@records.invalid'
    all applied: 
  first unnecessary redaction: example test-012
    text: '\tArchive\r\nkey=CUST-200012\r\nmail=qa_team@example.org\r\n'
    applied: EMAIL_ADDRESS [27:51] 'mail=qa_team@example.org' (result FP, touches_benign=True)
    all gold: CUSTOMER_ID[14:25]='CUST-200012'; EMAIL_ADDRESS[32:51]='qa_team@example.org'
    all applied: CUSTOMER_ID[14:25]='CUST-200012'; EMAIL_ADDRESS[27:51]='mail=qa_team@example.org'
````

### F15 candidate: evaluate development

Command: `<venv>python -m sanitizer evaluate --detector presidio --split development` | exit status: 0

````
presidio on development (thresholds {'EMAIL_ADDRESS': 1.0, 'PHONE_NUMBER': 0.4, 'CUSTOMER_ID': 1.0}); report written
EMAIL_ADDRESS  TP=6 FP=0 FN=1 precision=1.0000 recall=0.8571 f1=0.9231
PHONE_NUMBER   TP=4 FP=0 FN=0 precision=1.0000 recall=1.0000 f1=1.0000
CUSTOMER_ID    TP=5 FP=0 FN=0 precision=1.0000 recall=1.0000 f1=1.0000
micro          TP=15 FP=0 FN=1 precision=1.0000 recall=0.9375 f1=0.9677
coverage       full=15 partial=0 untouched=1 rate=0.9375
benign         replacements_touching_benign=0 replacements_touching_no_gold=0 benign_characters_removed=0
preservation   no_gold_preserved=2/2 equal_expected=9/10
````

### F15 candidate: evaluate heldout

Command: `<venv>python -m sanitizer evaluate --detector presidio --split heldout` | exit status: 0

````
presidio on heldout (thresholds {'EMAIL_ADDRESS': 1.0, 'PHONE_NUMBER': 0.4, 'CUSTOMER_ID': 1.0}); report written
EMAIL_ADDRESS  TP=10 FP=1 FN=2 precision=0.9091 recall=0.8333 f1=0.8696
PHONE_NUMBER   TP=8 FP=0 FN=0 precision=1.0000 recall=1.0000 f1=1.0000
CUSTOMER_ID    TP=8 FP=0 FN=0 precision=1.0000 recall=1.0000 f1=1.0000
micro          TP=26 FP=1 FN=2 precision=0.9630 recall=0.9286 f1=0.9455
coverage       full=27 partial=0 untouched=1 rate=0.9643
benign         replacements_touching_benign=1 replacements_touching_no_gold=0 benign_characters_removed=5
preservation   no_gold_preserved=5/5 equal_expected=16/18
````

### F16 deterministic rerun matches committed reports, both detectors

Command: `<venv>python scripts/check_reports.py baseline presidio` | exit status: 0

````
baseline  development  rerun matches committed report: True
baseline  heldout      rerun matches committed report: True
presidio  development  rerun matches committed report: True
presidio  heldout      rerun matches committed report: True
````

### F17 re-freezing is refused without --allow-refreeze

Command: `<venv>python -m sanitizer select-thresholds` | exit status: 2

````
--- stderr ---
SANITIZER_INVALID_CONFIG
````

### F18 README claim: a fresh render of the README results block equals the committed one

Command: `python -c <compare the README results block with scripts/render_summary.render()>` | exit status: 0

````
True
````

### Exact package set (`pip freeze` in the fresh venv)

````
annotated-doc==0.0.6
annotated-types==0.8.0
anyio==4.16.0
blis==1.3.4
catalogue==2.0.10
certifi==2026.10.23
charset-normalizer==3.5.2
click==8.5.1
cloudpathlib==0.26.0
colorama==0.4.6
confection==1.3.4
cymem==2.0.16
en_core_web_sm @ https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl#sha256=1932429db727d4bff3deed6b34cfc05df17794f4a52eeb26cf8928f7c1a0fb85
filelock==4.2.10
h11==0.16.0
httpcore==1.0.9
httpx==0.28.1
idna==3.20
Jinja2==3.1.6
markdown-it-py==4.3.0
MarkupSafe==3.0.4
mdurl==0.1.2
murmurhash==1.0.16
numpy==2.4.6
packaging==26.3
phonenumbers==9.0.43
preshed==3.0.13
presidio_analyzer==2.2.366
pydantic==2.14.3
pydantic_core==2.50.4
Pygments==2.21.0
PyYAML==6.0.3
regex==2026.11.9
requests==2.34.2
requests-file==3.0.1
rich==15.0.0
setuptools==84.2.1
shellingham==1.5.4
smart_open==9.0.3
spacy==3.8.18
spacy-legacy==3.0.12
spacy-loggers==1.0.5
srsly==2.5.6
thinc==8.3.14
tldextract==5.4.0
tqdm==4.70.1
typer==0.29.0
typing-inspection==0.4.5
typing_extensions==4.16.0
urllib3==2.8.0
wasabi==1.1.3
weasel==1.0.1
wrapt==2.5.2
````

Model asset: `en_core_web_sm` 3.8.0, 12,806,118 bytes, SHA-256 `1932429db727d4bff3deed6b34cfc05df17794f4a52eeb26cf8928f7c1a0fb85` (hash-pinned in `requirements-presidio.txt`). Installation uses the network; the tested inference path made no network attempts (socket-blocked test in `tests/test_presidio_optional.py`).

## 7. Frozen configuration (complete `config/frozen_config.json`)

````json
{
  "baseline": {
    "score": 1.0,
    "thresholds": {
      "CUSTOMER_ID": 1.0,
      "EMAIL_ADDRESS": 1.0,
      "PHONE_NUMBER": 1.0
    }
  },
  "config_version": 1,
  "detector": "presidio",
  "development_metrics_at_selected_thresholds": {
    "benign": {
      "benign_characters_removed": 0,
      "replacements_touching_benign": 0,
      "replacements_touching_no_gold": 0
    },
    "coverage": {
      "overall": {
        "coverage_rate": 0.9375,
        "full": 15,
        "gold": 16,
        "partial": 0,
        "untouched": 1
      },
      "per_type": {
        "CUSTOMER_ID": {
          "coverage_rate": 1.0,
          "full": 5,
          "gold": 5,
          "partial": 0,
          "untouched": 0
        },
        "EMAIL_ADDRESS": {
          "coverage_rate": 0.8571428571428571,
          "full": 6,
          "gold": 7,
          "partial": 0,
          "untouched": 1
        },
        "PHONE_NUMBER": {
          "coverage_rate": 1.0,
          "full": 4,
          "gold": 4,
          "partial": 0,
          "untouched": 0
        }
      }
    },
    "micro": {
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "precision": 1.0,
      "recall": 0.9375,
      "tp": 15
    },
    "per_type": {
      "CUSTOMER_ID": {
        "f1": 1.0,
        "fn": 0,
        "fp": 0,
        "precision": 1.0,
        "recall": 1.0,
        "tp": 5
      },
      "EMAIL_ADDRESS": {
        "f1": 0.9230769230769231,
        "fn": 1,
        "fp": 0,
        "precision": 1.0,
        "recall": 0.8571428571428571,
        "tp": 6
      },
      "PHONE_NUMBER": {
        "f1": 1.0,
        "fn": 0,
        "fp": 0,
        "precision": 1.0,
        "recall": 1.0,
        "tp": 4
      }
    }
  },
  "development_sha256": "050aab48f30e09d9736f4e3b637d5b67175cb1a8a5e5af59607092b62b7cc172",
  "freeze_kind": "procedural freeze of the development configuration; not a blinded external evaluation",
  "heldout_access": "heldout.json was hashed as raw bytes only; its contents were not parsed or read before this file was written",
  "heldout_sha256": "ce66e9a9dd74935a50f58c7252e50177702470676ebe7c98a060e8f0f3b38dc2",
  "model_wheel_sha256": "1932429db727d4bff3deed6b34cfc05df17794f4a52eeb26cf8928f7c1a0fb85",
  "packages": {
    "en-core-web-sm": "3.8.0",
    "phonenumbers": "9.0.43",
    "presidio-analyzer": "2.2.366",
    "regex": "2026.11.9",
    "spacy": "3.8.18",
    "tldextract": "5.4.0"
  },
  "python": "3.13.7",
  "recognizer_settings": {
    "analyze_entities": [
      "EMAIL_ADDRESS",
      "PHONE_NUMBER",
      "CUSTOMER_ID"
    ],
    "context_enhancer": "LemmaContextAwareEnhancer",
    "email_validator": "offline tldextract snapshot (suffix_list_urls=(), cache_dir=None)",
    "engine_default_score_threshold": 0,
    "ner_recognizer_registered": false,
    "nlp_engine": "SpacyNlpEngine",
    "presidio_logger_level": "INFO (process-wide setting made in build_analyzer)",
    "recognizers": [
      {
        "class": "OfflineEmailRecognizer",
        "entities": [
          "EMAIL_ADDRESS"
        ],
        "name": "OfflineEmailRecognizer",
        "patterns": [
          {
            "name": "Email (Medium)",
            "regex": "\\b((([!#$%&'*+\\-/=?^_`{|}~\\w])|([!#$%&'*+\\-/=?^_`{|}~\\w][!#$%&'*+\\-/=?^_`{|}~\\.\\w]{0,}[!#$%&'*+\\-/=?^_`{|}~\\w]))[@]\\w+(?:-+\\w+)*(?:\\.\\w+(?:-+\\w+)*)+)\\b",
            "score": 0.5
          }
        ],
        "regex_flags": "regex.I|M|S"
      },
      {
        "base_score": 0.4,
        "class": "PhoneRecognizer",
        "entities": [
          "PHONE_NUMBER"
        ],
        "leniency": 1,
        "name": "PhoneRecognizer",
        "supported_regions": [
          "US"
        ]
      },
      {
        "class": "PatternRecognizer",
        "entities": [
          "CUSTOMER_ID"
        ],
        "name": "CustomerIdRecognizer",
        "patterns": [
          {
            "name": "customer-id",
            "regex": "(?<![A-Za-z0-9_])CUST-[0-9]{6}(?![A-Za-z0-9_])",
            "score": 1.0
          }
        ],
        "regex_flags": "regex.M|S"
      }
    ],
    "spacy_model": "en_core_web_sm",
    "spacy_pipeline": [
      "tok2vec",
      "tagger",
      "parser",
      "attribute_ruler",
      "lemmatizer",
      "ner"
    ]
  },
  "resolution_policy": "decreasing length, decreasing score, type order EMAIL_ADDRESS>PHONE_NUMBER>CUSTOMER_ID, earlier start; keep non-overlapping; replace right to left with [TYPE]",
  "scope": {
    "CUSTOMER_ID_regex": "(?<![A-Za-z0-9_])CUST-[0-9]{6}(?![A-Za-z0-9_])",
    "PHONE_NUMBER_scope_regex": "(?<![A-Za-z0-9_])\\([2-9][0-9]{2}\\) [2-9][0-9]{2}-[0-9]{4}(?![A-Za-z0-9_])",
    "entities": [
      "EMAIL_ADDRESS",
      "PHONE_NUMBER",
      "CUSTOMER_ID"
    ],
    "phone_gate": "after validation, a PHONE_NUMBER candidate is kept only if its exact (start,end) is a match of the scope regex on the original text; never repaired, trimmed or synthesized"
  },
  "selection_grid": [
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.0,
        "EMAIL_ADDRESS": 0.0,
        "PHONE_NUMBER": 0.0
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.4,
        "EMAIL_ADDRESS": 0.0,
        "PHONE_NUMBER": 0.0
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.6,
        "EMAIL_ADDRESS": 0.0,
        "PHONE_NUMBER": 0.0
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.8,
        "EMAIL_ADDRESS": 0.0,
        "PHONE_NUMBER": 0.0
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 1.0,
        "EMAIL_ADDRESS": 0.0,
        "PHONE_NUMBER": 0.0
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.0,
        "EMAIL_ADDRESS": 0.0,
        "PHONE_NUMBER": 0.4
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.4,
        "EMAIL_ADDRESS": 0.0,
        "PHONE_NUMBER": 0.4
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.6,
        "EMAIL_ADDRESS": 0.0,
        "PHONE_NUMBER": 0.4
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.8,
        "EMAIL_ADDRESS": 0.0,
        "PHONE_NUMBER": 0.4
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 1.0,
        "EMAIL_ADDRESS": 0.0,
        "PHONE_NUMBER": 0.4
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.896551724137931,
      "fn": 3,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.0,
        "EMAIL_ADDRESS": 0.0,
        "PHONE_NUMBER": 0.6
      },
      "tp": 13
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.896551724137931,
      "fn": 3,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.4,
        "EMAIL_ADDRESS": 0.0,
        "PHONE_NUMBER": 0.6
      },
      "tp": 13
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.896551724137931,
      "fn": 3,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.6,
        "EMAIL_ADDRESS": 0.0,
        "PHONE_NUMBER": 0.6
      },
      "tp": 13
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.896551724137931,
      "fn": 3,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.8,
        "EMAIL_ADDRESS": 0.0,
        "PHONE_NUMBER": 0.6
      },
      "tp": 13
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.896551724137931,
      "fn": 3,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 1.0,
        "EMAIL_ADDRESS": 0.0,
        "PHONE_NUMBER": 0.6
      },
      "tp": 13
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.0,
        "EMAIL_ADDRESS": 0.0,
        "PHONE_NUMBER": 0.8
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.4,
        "EMAIL_ADDRESS": 0.0,
        "PHONE_NUMBER": 0.8
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.6,
        "EMAIL_ADDRESS": 0.0,
        "PHONE_NUMBER": 0.8
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.8,
        "EMAIL_ADDRESS": 0.0,
        "PHONE_NUMBER": 0.8
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 1.0,
        "EMAIL_ADDRESS": 0.0,
        "PHONE_NUMBER": 0.8
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.0,
        "EMAIL_ADDRESS": 0.0,
        "PHONE_NUMBER": 1.0
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.4,
        "EMAIL_ADDRESS": 0.0,
        "PHONE_NUMBER": 1.0
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.6,
        "EMAIL_ADDRESS": 0.0,
        "PHONE_NUMBER": 1.0
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.8,
        "EMAIL_ADDRESS": 0.0,
        "PHONE_NUMBER": 1.0
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 1.0,
        "EMAIL_ADDRESS": 0.0,
        "PHONE_NUMBER": 1.0
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.0,
        "EMAIL_ADDRESS": 0.4,
        "PHONE_NUMBER": 0.0
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.4,
        "EMAIL_ADDRESS": 0.4,
        "PHONE_NUMBER": 0.0
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.6,
        "EMAIL_ADDRESS": 0.4,
        "PHONE_NUMBER": 0.0
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.8,
        "EMAIL_ADDRESS": 0.4,
        "PHONE_NUMBER": 0.0
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 1.0,
        "EMAIL_ADDRESS": 0.4,
        "PHONE_NUMBER": 0.0
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.0,
        "EMAIL_ADDRESS": 0.4,
        "PHONE_NUMBER": 0.4
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.4,
        "EMAIL_ADDRESS": 0.4,
        "PHONE_NUMBER": 0.4
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.6,
        "EMAIL_ADDRESS": 0.4,
        "PHONE_NUMBER": 0.4
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.8,
        "EMAIL_ADDRESS": 0.4,
        "PHONE_NUMBER": 0.4
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 1.0,
        "EMAIL_ADDRESS": 0.4,
        "PHONE_NUMBER": 0.4
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.896551724137931,
      "fn": 3,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.0,
        "EMAIL_ADDRESS": 0.4,
        "PHONE_NUMBER": 0.6
      },
      "tp": 13
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.896551724137931,
      "fn": 3,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.4,
        "EMAIL_ADDRESS": 0.4,
        "PHONE_NUMBER": 0.6
      },
      "tp": 13
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.896551724137931,
      "fn": 3,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.6,
        "EMAIL_ADDRESS": 0.4,
        "PHONE_NUMBER": 0.6
      },
      "tp": 13
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.896551724137931,
      "fn": 3,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.8,
        "EMAIL_ADDRESS": 0.4,
        "PHONE_NUMBER": 0.6
      },
      "tp": 13
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.896551724137931,
      "fn": 3,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 1.0,
        "EMAIL_ADDRESS": 0.4,
        "PHONE_NUMBER": 0.6
      },
      "tp": 13
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.0,
        "EMAIL_ADDRESS": 0.4,
        "PHONE_NUMBER": 0.8
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.4,
        "EMAIL_ADDRESS": 0.4,
        "PHONE_NUMBER": 0.8
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.6,
        "EMAIL_ADDRESS": 0.4,
        "PHONE_NUMBER": 0.8
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.8,
        "EMAIL_ADDRESS": 0.4,
        "PHONE_NUMBER": 0.8
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 1.0,
        "EMAIL_ADDRESS": 0.4,
        "PHONE_NUMBER": 0.8
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.0,
        "EMAIL_ADDRESS": 0.4,
        "PHONE_NUMBER": 1.0
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.4,
        "EMAIL_ADDRESS": 0.4,
        "PHONE_NUMBER": 1.0
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.6,
        "EMAIL_ADDRESS": 0.4,
        "PHONE_NUMBER": 1.0
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.8,
        "EMAIL_ADDRESS": 0.4,
        "PHONE_NUMBER": 1.0
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 1.0,
        "EMAIL_ADDRESS": 0.4,
        "PHONE_NUMBER": 1.0
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.0,
        "EMAIL_ADDRESS": 0.6,
        "PHONE_NUMBER": 0.0
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.4,
        "EMAIL_ADDRESS": 0.6,
        "PHONE_NUMBER": 0.0
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.6,
        "EMAIL_ADDRESS": 0.6,
        "PHONE_NUMBER": 0.0
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.8,
        "EMAIL_ADDRESS": 0.6,
        "PHONE_NUMBER": 0.0
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 1.0,
        "EMAIL_ADDRESS": 0.6,
        "PHONE_NUMBER": 0.0
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.0,
        "EMAIL_ADDRESS": 0.6,
        "PHONE_NUMBER": 0.4
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.4,
        "EMAIL_ADDRESS": 0.6,
        "PHONE_NUMBER": 0.4
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.6,
        "EMAIL_ADDRESS": 0.6,
        "PHONE_NUMBER": 0.4
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.8,
        "EMAIL_ADDRESS": 0.6,
        "PHONE_NUMBER": 0.4
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 1.0,
        "EMAIL_ADDRESS": 0.6,
        "PHONE_NUMBER": 0.4
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.896551724137931,
      "fn": 3,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.0,
        "EMAIL_ADDRESS": 0.6,
        "PHONE_NUMBER": 0.6
      },
      "tp": 13
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.896551724137931,
      "fn": 3,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.4,
        "EMAIL_ADDRESS": 0.6,
        "PHONE_NUMBER": 0.6
      },
      "tp": 13
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.896551724137931,
      "fn": 3,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.6,
        "EMAIL_ADDRESS": 0.6,
        "PHONE_NUMBER": 0.6
      },
      "tp": 13
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.896551724137931,
      "fn": 3,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.8,
        "EMAIL_ADDRESS": 0.6,
        "PHONE_NUMBER": 0.6
      },
      "tp": 13
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.896551724137931,
      "fn": 3,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 1.0,
        "EMAIL_ADDRESS": 0.6,
        "PHONE_NUMBER": 0.6
      },
      "tp": 13
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.0,
        "EMAIL_ADDRESS": 0.6,
        "PHONE_NUMBER": 0.8
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.4,
        "EMAIL_ADDRESS": 0.6,
        "PHONE_NUMBER": 0.8
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.6,
        "EMAIL_ADDRESS": 0.6,
        "PHONE_NUMBER": 0.8
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.8,
        "EMAIL_ADDRESS": 0.6,
        "PHONE_NUMBER": 0.8
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 1.0,
        "EMAIL_ADDRESS": 0.6,
        "PHONE_NUMBER": 0.8
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.0,
        "EMAIL_ADDRESS": 0.6,
        "PHONE_NUMBER": 1.0
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.4,
        "EMAIL_ADDRESS": 0.6,
        "PHONE_NUMBER": 1.0
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.6,
        "EMAIL_ADDRESS": 0.6,
        "PHONE_NUMBER": 1.0
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.8,
        "EMAIL_ADDRESS": 0.6,
        "PHONE_NUMBER": 1.0
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 1.0,
        "EMAIL_ADDRESS": 0.6,
        "PHONE_NUMBER": 1.0
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.0,
        "EMAIL_ADDRESS": 0.8,
        "PHONE_NUMBER": 0.0
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.4,
        "EMAIL_ADDRESS": 0.8,
        "PHONE_NUMBER": 0.0
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.6,
        "EMAIL_ADDRESS": 0.8,
        "PHONE_NUMBER": 0.0
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.8,
        "EMAIL_ADDRESS": 0.8,
        "PHONE_NUMBER": 0.0
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 1.0,
        "EMAIL_ADDRESS": 0.8,
        "PHONE_NUMBER": 0.0
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.0,
        "EMAIL_ADDRESS": 0.8,
        "PHONE_NUMBER": 0.4
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.4,
        "EMAIL_ADDRESS": 0.8,
        "PHONE_NUMBER": 0.4
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.6,
        "EMAIL_ADDRESS": 0.8,
        "PHONE_NUMBER": 0.4
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.8,
        "EMAIL_ADDRESS": 0.8,
        "PHONE_NUMBER": 0.4
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 1.0,
        "EMAIL_ADDRESS": 0.8,
        "PHONE_NUMBER": 0.4
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.896551724137931,
      "fn": 3,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.0,
        "EMAIL_ADDRESS": 0.8,
        "PHONE_NUMBER": 0.6
      },
      "tp": 13
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.896551724137931,
      "fn": 3,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.4,
        "EMAIL_ADDRESS": 0.8,
        "PHONE_NUMBER": 0.6
      },
      "tp": 13
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.896551724137931,
      "fn": 3,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.6,
        "EMAIL_ADDRESS": 0.8,
        "PHONE_NUMBER": 0.6
      },
      "tp": 13
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.896551724137931,
      "fn": 3,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.8,
        "EMAIL_ADDRESS": 0.8,
        "PHONE_NUMBER": 0.6
      },
      "tp": 13
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.896551724137931,
      "fn": 3,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 1.0,
        "EMAIL_ADDRESS": 0.8,
        "PHONE_NUMBER": 0.6
      },
      "tp": 13
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.0,
        "EMAIL_ADDRESS": 0.8,
        "PHONE_NUMBER": 0.8
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.4,
        "EMAIL_ADDRESS": 0.8,
        "PHONE_NUMBER": 0.8
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.6,
        "EMAIL_ADDRESS": 0.8,
        "PHONE_NUMBER": 0.8
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.8,
        "EMAIL_ADDRESS": 0.8,
        "PHONE_NUMBER": 0.8
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 1.0,
        "EMAIL_ADDRESS": 0.8,
        "PHONE_NUMBER": 0.8
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.0,
        "EMAIL_ADDRESS": 0.8,
        "PHONE_NUMBER": 1.0
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.4,
        "EMAIL_ADDRESS": 0.8,
        "PHONE_NUMBER": 1.0
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.6,
        "EMAIL_ADDRESS": 0.8,
        "PHONE_NUMBER": 1.0
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.8,
        "EMAIL_ADDRESS": 0.8,
        "PHONE_NUMBER": 1.0
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 1.0,
        "EMAIL_ADDRESS": 0.8,
        "PHONE_NUMBER": 1.0
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.0,
        "EMAIL_ADDRESS": 1.0,
        "PHONE_NUMBER": 0.0
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.4,
        "EMAIL_ADDRESS": 1.0,
        "PHONE_NUMBER": 0.0
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.6,
        "EMAIL_ADDRESS": 1.0,
        "PHONE_NUMBER": 0.0
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.8,
        "EMAIL_ADDRESS": 1.0,
        "PHONE_NUMBER": 0.0
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 1.0,
        "EMAIL_ADDRESS": 1.0,
        "PHONE_NUMBER": 0.0
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.0,
        "EMAIL_ADDRESS": 1.0,
        "PHONE_NUMBER": 0.4
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.4,
        "EMAIL_ADDRESS": 1.0,
        "PHONE_NUMBER": 0.4
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.6,
        "EMAIL_ADDRESS": 1.0,
        "PHONE_NUMBER": 0.4
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.8,
        "EMAIL_ADDRESS": 1.0,
        "PHONE_NUMBER": 0.4
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 1.0,
        "EMAIL_ADDRESS": 1.0,
        "PHONE_NUMBER": 0.4
      },
      "tp": 15
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.896551724137931,
      "fn": 3,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.0,
        "EMAIL_ADDRESS": 1.0,
        "PHONE_NUMBER": 0.6
      },
      "tp": 13
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.896551724137931,
      "fn": 3,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.4,
        "EMAIL_ADDRESS": 1.0,
        "PHONE_NUMBER": 0.6
      },
      "tp": 13
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.896551724137931,
      "fn": 3,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.6,
        "EMAIL_ADDRESS": 1.0,
        "PHONE_NUMBER": 0.6
      },
      "tp": 13
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.896551724137931,
      "fn": 3,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.8,
        "EMAIL_ADDRESS": 1.0,
        "PHONE_NUMBER": 0.6
      },
      "tp": 13
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.896551724137931,
      "fn": 3,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 1.0,
        "EMAIL_ADDRESS": 1.0,
        "PHONE_NUMBER": 0.6
      },
      "tp": 13
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.0,
        "EMAIL_ADDRESS": 1.0,
        "PHONE_NUMBER": 0.8
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.4,
        "EMAIL_ADDRESS": 1.0,
        "PHONE_NUMBER": 0.8
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.6,
        "EMAIL_ADDRESS": 1.0,
        "PHONE_NUMBER": 0.8
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.8,
        "EMAIL_ADDRESS": 1.0,
        "PHONE_NUMBER": 0.8
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 1.0,
        "EMAIL_ADDRESS": 1.0,
        "PHONE_NUMBER": 0.8
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.0,
        "EMAIL_ADDRESS": 1.0,
        "PHONE_NUMBER": 1.0
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.4,
        "EMAIL_ADDRESS": 1.0,
        "PHONE_NUMBER": 1.0
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.6,
        "EMAIL_ADDRESS": 1.0,
        "PHONE_NUMBER": 1.0
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 0.8,
        "EMAIL_ADDRESS": 1.0,
        "PHONE_NUMBER": 1.0
      },
      "tp": 11
    },
    {
      "benign_characters_removed": 0,
      "f1": 0.8148148148148148,
      "fn": 5,
      "fp": 0,
      "thresholds": {
        "CUSTOMER_ID": 1.0,
        "EMAIL_ADDRESS": 1.0,
        "PHONE_NUMBER": 1.0
      },
      "tp": 11
    }
  ],
  "selection_grid_size": 125,
  "selection_rule": "Candidate thresholds from {0.0,0.4,0.6,0.8,1.0}^3 evaluated on development.json only, using cached raw candidates through the full shared pipeline (validate all, phone scope gate, score >= threshold, dedupe, overlap resolution). Choose the highest development exact-span micro F1; ties -> fewer benign characters removed; then lexicographically higher thresholds in EMAIL_ADDRESS, PHONE_NUMBER, CUSTOMER_ID order.",
  "selection_tied_at_top_after_benign_rule": 50,
  "threshold_grid": [
    0.0,
    0.4,
    0.6,
    0.8,
    1.0
  ],
  "thresholds": {
    "CUSTOMER_ID": 1.0,
    "EMAIL_ADDRESS": 1.0,
    "PHONE_NUMBER": 0.4
  }
}
````

## 8. Fixtures and reports (complete)

### `fixtures/fixture_summary.json`

````json
{
  "development": {
    "examples": 10,
    "gold_entities": {
      "EMAIL_ADDRESS": 7,
      "PHONE_NUMBER": 4,
      "CUSTOMER_ID": 5
    }
  },
  "heldout": {
    "examples": 18,
    "gold_entities": {
      "EMAIL_ADDRESS": 12,
      "PHONE_NUMBER": 8,
      "CUSTOMER_ID": 8
    }
  }
}
````

### `fixtures/development.json`

````json
{
  "schema_version": 1,
  "split": "development",
  "offset_unit": "python_unicode_codepoint",
  "examples": [
    {
      "id": "dev-001",
      "text": "Email ava@example.com; customer CUST-004271; quantity 24.",
      "entities": [
        {
          "entity_type": "EMAIL_ADDRESS",
          "start": 6,
          "end": 21
        },
        {
          "entity_type": "CUSTOMER_ID",
          "start": 32,
          "end": 43
        }
      ],
      "expected_sanitized": "Email [EMAIL_ADDRESS]; customer [CUSTOMER_ID]; quantity 24."
    },
    {
      "id": "dev-002",
      "text": "Call (202) 555-0147 about CUST-100002.",
      "entities": [
        {
          "entity_type": "PHONE_NUMBER",
          "start": 5,
          "end": 19
        },
        {
          "entity_type": "CUSTOMER_ID",
          "start": 26,
          "end": 37
        }
      ],
      "expected_sanitized": "Call [PHONE_NUMBER] about [CUSTOMER_ID]."
    },
    {
      "id": "dev-003",
      "text": "Copy maya+lab@example.org and maya+lab@example.org; 2 copies.",
      "entities": [
        {
          "entity_type": "EMAIL_ADDRESS",
          "start": 5,
          "end": 25
        },
        {
          "entity_type": "EMAIL_ADDRESS",
          "start": 30,
          "end": 50
        }
      ],
      "expected_sanitized": "Copy [EMAIL_ADDRESS] and [EMAIL_ADDRESS]; 2 copies."
    },
    {
      "id": "dev-004",
      "text": "🔒 Café: leo@example.net / CUST-100004.",
      "entities": [
        {
          "entity_type": "EMAIL_ADDRESS",
          "start": 8,
          "end": 23
        },
        {
          "entity_type": "CUSTOMER_ID",
          "start": 26,
          "end": 37
        }
      ],
      "expected_sanitized": "🔒 Café: [EMAIL_ADDRESS] / [CUSTOMER_ID]."
    },
    {
      "id": "dev-005",
      "text": "Owner CUST-100005@example.com; telephone (415) 555-0123.",
      "entities": [
        {
          "entity_type": "EMAIL_ADDRESS",
          "start": 6,
          "end": 29
        },
        {
          "entity_type": "PHONE_NUMBER",
          "start": 41,
          "end": 55
        }
      ],
      "expected_sanitized": "Owner [EMAIL_ADDRESS]; telephone [PHONE_NUMBER]."
    },
    {
      "id": "dev-006",
      "text": "Units 24; year 2026; code cust-100006; token XCUST-100006; short CUST-10006.",
      "entities": [],
      "expected_sanitized": "Units 24; year 2026; code cust-100006; token XCUST-100006; short CUST-10006."
    },
    {
      "id": "dev-007",
      "text": "Use CUST-100007,team@example.com; fax (301) 555-0108!",
      "entities": [
        {
          "entity_type": "CUSTOMER_ID",
          "start": 4,
          "end": 15
        },
        {
          "entity_type": "EMAIL_ADDRESS",
          "start": 16,
          "end": 32
        },
        {
          "entity_type": "PHONE_NUMBER",
          "start": 38,
          "end": 52
        }
      ],
      "expected_sanitized": "Use [CUSTOMER_ID],[EMAIL_ADDRESS]; fax [PHONE_NUMBER]!"
    },
    {
      "id": "dev-008",
      "text": "Email dev@training.invalid. Unsupported phone 202-555-0147 is outside the selected format.",
      "entities": [
        {
          "entity_type": "EMAIL_ADDRESS",
          "start": 6,
          "end": 26
        }
      ],
      "expected_sanitized": "Email [EMAIL_ADDRESS]. Unsupported phone 202-555-0147 is outside the selected format."
    },
    {
      "id": "dev-009",
      "text": "Line A\r\nPhone (240) 555-0111\r\nReference CUST-100009\tend.",
      "entities": [
        {
          "entity_type": "PHONE_NUMBER",
          "start": 14,
          "end": 28
        },
        {
          "entity_type": "CUSTOMER_ID",
          "start": 40,
          "end": 51
        }
      ],
      "expected_sanitized": "Line A\r\nPhone [PHONE_NUMBER]\r\nReference [CUSTOMER_ID]\tend."
    },
    {
      "id": "dev-010",
      "text": "",
      "entities": [],
      "expected_sanitized": ""
    }
  ]
}
````

### `fixtures/heldout.json`

````json
{
  "schema_version": 1,
  "split": "heldout",
  "offset_unit": "python_unicode_codepoint",
  "examples": [
    {
      "id": "test-001",
      "text": "Receipt 81 | recipient=<nora@example.org> | amount=42.50",
      "entities": [
        {
          "entity_type": "EMAIL_ADDRESS",
          "start": 24,
          "end": 40
        }
      ],
      "expected_sanitized": "Receipt 81 | recipient=<[EMAIL_ADDRESS]> | amount=42.50"
    },
    {
      "id": "test-002",
      "text": "Escalation queue: [(703) 555-0188] after ticket CUST-200002; priority 3.",
      "entities": [
        {
          "entity_type": "PHONE_NUMBER",
          "start": 19,
          "end": 33
        },
        {
          "entity_type": "CUSTOMER_ID",
          "start": 48,
          "end": 59
        }
      ],
      "expected_sanitized": "Escalation queue: [[PHONE_NUMBER]] after ticket [CUSTOMER_ID]; priority 3."
    },
    {
      "id": "test-003",
      "text": "To: support+west@example.net\nSubject: account CUST-200003",
      "entities": [
        {
          "entity_type": "EMAIL_ADDRESS",
          "start": 4,
          "end": 28
        },
        {
          "entity_type": "CUSTOMER_ID",
          "start": 46,
          "end": 57
        }
      ],
      "expected_sanitized": "To: [EMAIL_ADDRESS]\nSubject: account [CUSTOMER_ID]"
    },
    {
      "id": "test-004",
      "text": "配送 😀 — CUST-200004 → mei@example.com; café total 19.",
      "entities": [
        {
          "entity_type": "CUSTOMER_ID",
          "start": 7,
          "end": 18
        },
        {
          "entity_type": "EMAIL_ADDRESS",
          "start": 21,
          "end": 36
        }
      ],
      "expected_sanitized": "配送 😀 — [CUSTOMER_ID] → [EMAIL_ADDRESS]; café total 19."
    },
    {
      "id": "test-005",
      "text": "Routing key \"CUST-200005@example.org\" belongs in slot 7.",
      "entities": [
        {
          "entity_type": "EMAIL_ADDRESS",
          "start": 13,
          "end": 36
        }
      ],
      "expected_sanitized": "Routing key \"[EMAIL_ADDRESS]\" belongs in slot 7."
    },
    {
      "id": "test-006",
      "text": "Retry contacts: iris@example.com | iris@example.com | (212) 555-0191 | (212) 555-0191.",
      "entities": [
        {
          "entity_type": "EMAIL_ADDRESS",
          "start": 16,
          "end": 32
        },
        {
          "entity_type": "EMAIL_ADDRESS",
          "start": 35,
          "end": 51
        },
        {
          "entity_type": "PHONE_NUMBER",
          "start": 54,
          "end": 68
        },
        {
          "entity_type": "PHONE_NUMBER",
          "start": 71,
          "end": 85
        }
      ],
      "expected_sanitized": "Retry contacts: [EMAIL_ADDRESS] | [EMAIL_ADDRESS] | [PHONE_NUMBER] | [PHONE_NUMBER]."
    },
    {
      "id": "test-007",
      "text": "Snapshot=v2.3.4; units=108; ratio=0.75; date=2026-11-10; no contacts.",
      "entities": [],
      "expected_sanitized": "Snapshot=v2.3.4; units=108; ratio=0.75; date=2026-11-10; no contacts."
    },
    {
      "id": "test-008",
      "text": "Bad keys: cust-200008, CUST-20008, CUST-2000089, XCUST-200008, CUST-200008_x.",
      "entities": [],
      "expected_sanitized": "Bad keys: cust-200008, CUST-20008, CUST-2000089, XCUST-200008, CUST-200008_x."
    },
    {
      "id": "test-009",
      "text": "Format examples only: 202-555-0199 / (202)555-0199 / (202)  555-0199 / (102) 555-0199 / (202) 155-0199.",
      "entities": [],
      "expected_sanitized": "Format examples only: 202-555-0199 / (202)555-0199 / (202)  555-0199 / (102) 555-0199 / (202) 155-0199."
    },
    {
      "id": "test-010",
      "text": "Audit destination audit@records.invalid; batch 64 closed.",
      "entities": [
        {
          "entity_type": "EMAIL_ADDRESS",
          "start": 18,
          "end": 39
        }
      ],
      "expected_sanitized": "Audit destination [EMAIL_ADDRESS]; batch 64 closed."
    },
    {
      "id": "test-011",
      "text": "Window{(202) 555-0176}; ref(CUST-200011); mailbox<jules@dept.example.com>.",
      "entities": [
        {
          "entity_type": "PHONE_NUMBER",
          "start": 7,
          "end": 21
        },
        {
          "entity_type": "CUSTOMER_ID",
          "start": 28,
          "end": 39
        },
        {
          "entity_type": "EMAIL_ADDRESS",
          "start": 50,
          "end": 72
        }
      ],
      "expected_sanitized": "Window{[PHONE_NUMBER]}; ref([CUSTOMER_ID]); mailbox<[EMAIL_ADDRESS]>."
    },
    {
      "id": "test-012",
      "text": "\tArchive\r\nkey=CUST-200012\r\nmail=qa_team@example.org\r\n",
      "entities": [
        {
          "entity_type": "CUSTOMER_ID",
          "start": 14,
          "end": 25
        },
        {
          "entity_type": "EMAIL_ADDRESS",
          "start": 32,
          "end": 51
        }
      ],
      "expected_sanitized": "\tArchive\r\nkey=[CUSTOMER_ID]\r\nmail=[EMAIL_ADDRESS]\r\n"
    },
    {
      "id": "test-013",
      "text": "first.last@example.net,CUST-200013;(301) 555-0102",
      "entities": [
        {
          "entity_type": "EMAIL_ADDRESS",
          "start": 0,
          "end": 22
        },
        {
          "entity_type": "CUSTOMER_ID",
          "start": 23,
          "end": 34
        },
        {
          "entity_type": "PHONE_NUMBER",
          "start": 35,
          "end": 49
        }
      ],
      "expected_sanitized": "[EMAIL_ADDRESS],[CUSTOMER_ID];[PHONE_NUMBER]"
    },
    {
      "id": "test-014",
      "text": "Reference pair: CUST-200014 / CUST-200014; retained counter 14.",
      "entities": [
        {
          "entity_type": "CUSTOMER_ID",
          "start": 16,
          "end": 27
        },
        {
          "entity_type": "CUSTOMER_ID",
          "start": 30,
          "end": 41
        }
      ],
      "expected_sanitized": "Reference pair: [CUSTOMER_ID] / [CUSTOMER_ID]; retained counter 14."
    },
    {
      "id": "test-015",
      "text": "Decomposed café precedes renee@example.com; dial (415) 555-0160.",
      "entities": [
        {
          "entity_type": "EMAIL_ADDRESS",
          "start": 26,
          "end": 43
        },
        {
          "entity_type": "PHONE_NUMBER",
          "start": 50,
          "end": 64
        }
      ],
      "expected_sanitized": "Decomposed café precedes [EMAIL_ADDRESS]; dial [PHONE_NUMBER]."
    },
    {
      "id": "test-016",
      "text": "",
      "entities": [],
      "expected_sanitized": ""
    },
    {
      "id": "test-017",
      "text": "Footer v8: operations 24×7; temperatures −5, 0, 19; symbol Ω; tabs\tstay.",
      "entities": [],
      "expected_sanitized": "Footer v8: operations 24×7; temperatures −5, 0, 19; symbol Ω; tabs\tstay."
    },
    {
      "id": "test-018",
      "text": "Callback card:\n  primary (240) 555-0139\n  secondary (703) 555-0125\n  alias ops@unit.example.net",
      "entities": [
        {
          "entity_type": "PHONE_NUMBER",
          "start": 25,
          "end": 39
        },
        {
          "entity_type": "PHONE_NUMBER",
          "start": 52,
          "end": 66
        },
        {
          "entity_type": "EMAIL_ADDRESS",
          "start": 75,
          "end": 95
        }
      ],
      "expected_sanitized": "Callback card:\n  primary [PHONE_NUMBER]\n  secondary [PHONE_NUMBER]\n  alias [EMAIL_ADDRESS]"
    }
  ]
}
````

### `reports/development_baseline.json`

````json
{
  "benign": {
    "benign_characters_removed": 0,
    "replacements_touching_benign": 0,
    "replacements_touching_no_gold": 0
  },
  "coverage": {
    "overall": {
      "coverage_rate": 1.0,
      "full": 16,
      "gold": 16,
      "partial": 0,
      "untouched": 0
    },
    "per_type": {
      "CUSTOMER_ID": {
        "coverage_rate": 1.0,
        "full": 5,
        "gold": 5,
        "partial": 0,
        "untouched": 0
      },
      "EMAIL_ADDRESS": {
        "coverage_rate": 1.0,
        "full": 7,
        "gold": 7,
        "partial": 0,
        "untouched": 0
      },
      "PHONE_NUMBER": {
        "coverage_rate": 1.0,
        "full": 4,
        "gold": 4,
        "partial": 0,
        "untouched": 0
      }
    }
  },
  "examples": [
    {
      "applied": [
        {
          "end": 21,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "score": 1.0,
          "start": 6,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 43,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "score": 1.0,
          "start": 32,
          "touches_benign": false,
          "touches_no_gold": false
        }
      ],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [
        {
          "end": 21,
          "entity_type": "EMAIL_ADDRESS",
          "score": 1.0,
          "start": 6
        },
        {
          "end": 43,
          "entity_type": "CUSTOMER_ID",
          "score": 1.0,
          "start": 32
        }
      ],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [
        {
          "coverage": "full",
          "end": 21,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "start": 6
        },
        {
          "coverage": "full",
          "end": 43,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "start": 32
        }
      ],
      "id": "dev-001",
      "matches_expected_sanitized": true,
      "no_gold_preserved": null,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [
        {
          "end": 19,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "score": 1.0,
          "start": 5,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 37,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "score": 1.0,
          "start": 26,
          "touches_benign": false,
          "touches_no_gold": false
        }
      ],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [
        {
          "end": 19,
          "entity_type": "PHONE_NUMBER",
          "score": 1.0,
          "start": 5
        },
        {
          "end": 37,
          "entity_type": "CUSTOMER_ID",
          "score": 1.0,
          "start": 26
        }
      ],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [
        {
          "coverage": "full",
          "end": 19,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "start": 5
        },
        {
          "coverage": "full",
          "end": 37,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "start": 26
        }
      ],
      "id": "dev-002",
      "matches_expected_sanitized": true,
      "no_gold_preserved": null,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [
        {
          "end": 25,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "score": 1.0,
          "start": 5,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 50,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "score": 1.0,
          "start": 30,
          "touches_benign": false,
          "touches_no_gold": false
        }
      ],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [
        {
          "end": 25,
          "entity_type": "EMAIL_ADDRESS",
          "score": 1.0,
          "start": 5
        },
        {
          "end": 50,
          "entity_type": "EMAIL_ADDRESS",
          "score": 1.0,
          "start": 30
        }
      ],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [
        {
          "coverage": "full",
          "end": 25,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "start": 5
        },
        {
          "coverage": "full",
          "end": 50,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "start": 30
        }
      ],
      "id": "dev-003",
      "matches_expected_sanitized": true,
      "no_gold_preserved": null,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [
        {
          "end": 23,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "score": 1.0,
          "start": 8,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 37,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "score": 1.0,
          "start": 26,
          "touches_benign": false,
          "touches_no_gold": false
        }
      ],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [
        {
          "end": 23,
          "entity_type": "EMAIL_ADDRESS",
          "score": 1.0,
          "start": 8
        },
        {
          "end": 37,
          "entity_type": "CUSTOMER_ID",
          "score": 1.0,
          "start": 26
        }
      ],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [
        {
          "coverage": "full",
          "end": 23,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "start": 8
        },
        {
          "coverage": "full",
          "end": 37,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "start": 26
        }
      ],
      "id": "dev-004",
      "matches_expected_sanitized": true,
      "no_gold_preserved": null,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [
        {
          "end": 29,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "score": 1.0,
          "start": 6,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 55,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "score": 1.0,
          "start": 41,
          "touches_benign": false,
          "touches_no_gold": false
        }
      ],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [
        {
          "end": 29,
          "entity_type": "EMAIL_ADDRESS",
          "score": 1.0,
          "start": 6
        },
        {
          "end": 55,
          "entity_type": "PHONE_NUMBER",
          "score": 1.0,
          "start": 41
        },
        {
          "end": 17,
          "entity_type": "CUSTOMER_ID",
          "score": 1.0,
          "start": 6
        }
      ],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [
        {
          "coverage": "full",
          "end": 29,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "start": 6
        },
        {
          "coverage": "full",
          "end": 55,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "start": 41
        }
      ],
      "id": "dev-005",
      "matches_expected_sanitized": true,
      "no_gold_preserved": null,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [],
      "id": "dev-006",
      "matches_expected_sanitized": true,
      "no_gold_preserved": true,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [
        {
          "end": 15,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "score": 1.0,
          "start": 4,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 32,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "score": 1.0,
          "start": 16,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 52,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "score": 1.0,
          "start": 38,
          "touches_benign": false,
          "touches_no_gold": false
        }
      ],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [
        {
          "end": 32,
          "entity_type": "EMAIL_ADDRESS",
          "score": 1.0,
          "start": 16
        },
        {
          "end": 52,
          "entity_type": "PHONE_NUMBER",
          "score": 1.0,
          "start": 38
        },
        {
          "end": 15,
          "entity_type": "CUSTOMER_ID",
          "score": 1.0,
          "start": 4
        }
      ],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [
        {
          "coverage": "full",
          "end": 15,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "start": 4
        },
        {
          "coverage": "full",
          "end": 32,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "start": 16
        },
        {
          "coverage": "full",
          "end": 52,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "start": 38
        }
      ],
      "id": "dev-007",
      "matches_expected_sanitized": true,
      "no_gold_preserved": null,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [
        {
          "end": 26,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "score": 1.0,
          "start": 6,
          "touches_benign": false,
          "touches_no_gold": false
        }
      ],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [
        {
          "end": 26,
          "entity_type": "EMAIL_ADDRESS",
          "score": 1.0,
          "start": 6
        }
      ],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [
        {
          "coverage": "full",
          "end": 26,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "start": 6
        }
      ],
      "id": "dev-008",
      "matches_expected_sanitized": true,
      "no_gold_preserved": null,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [
        {
          "end": 28,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "score": 1.0,
          "start": 14,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 51,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "score": 1.0,
          "start": 40,
          "touches_benign": false,
          "touches_no_gold": false
        }
      ],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [
        {
          "end": 28,
          "entity_type": "PHONE_NUMBER",
          "score": 1.0,
          "start": 14
        },
        {
          "end": 51,
          "entity_type": "CUSTOMER_ID",
          "score": 1.0,
          "start": 40
        }
      ],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [
        {
          "coverage": "full",
          "end": 28,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "start": 14
        },
        {
          "coverage": "full",
          "end": 51,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "start": 40
        }
      ],
      "id": "dev-009",
      "matches_expected_sanitized": true,
      "no_gold_preserved": null,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [],
      "id": "dev-010",
      "matches_expected_sanitized": true,
      "no_gold_preserved": true,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    }
  ],
  "meta": {
    "detector": "baseline",
    "fixture_sha256": "050aab48f30e09d9736f4e3b637d5b67175cb1a8a5e5af59607092b62b7cc172",
    "frozen_config_sha256": null,
    "packages": {},
    "python": "3.13.7",
    "resolution_policy": "validate all spans; phone scope gate; type thresholds (score >= t); dedupe same type/range keeping highest score; overlap resolution by length, score, type order EMAIL_ADDRESS>PHONE_NUMBER>CUSTOMER_ID, earlier start; replace right to left",
    "split": "development",
    "status": "procedural freeze of the development configuration; not a blinded external evaluation",
    "thresholds": {
      "CUSTOMER_ID": 1.0,
      "EMAIL_ADDRESS": 1.0,
      "PHONE_NUMBER": 1.0
    }
  },
  "metrics": {
    "micro": {
      "f1": 1.0,
      "fn": 0,
      "fp": 0,
      "precision": 1.0,
      "recall": 1.0,
      "tp": 16
    },
    "per_type": {
      "CUSTOMER_ID": {
        "f1": 1.0,
        "fn": 0,
        "fp": 0,
        "precision": 1.0,
        "recall": 1.0,
        "tp": 5
      },
      "EMAIL_ADDRESS": {
        "f1": 1.0,
        "fn": 0,
        "fp": 0,
        "precision": 1.0,
        "recall": 1.0,
        "tp": 7
      },
      "PHONE_NUMBER": {
        "f1": 1.0,
        "fn": 0,
        "fp": 0,
        "precision": 1.0,
        "recall": 1.0,
        "tp": 4
      }
    }
  },
  "notes": [
    "Primary metrics score the spans actually applied after validation, scope gate, thresholds, dedupe and overlap resolution.",
    "diagnostic_pre_resolution_validated_candidates is a separate diagnostic and is not used for the metrics.",
    "Provider-boundary counts are separate from accuracy: a detector miss is an accuracy/coverage failure, not a boundary failure.",
    "Small synthetic template split; not evidence of real-world performance."
  ],
  "preservation": {
    "examples_equal_expected_sanitized": 10,
    "examples_failed_with_fixed_code": 0,
    "examples_total": 10,
    "examples_with_no_gold": 2,
    "no_gold_examples_preserved": 2
  },
  "provider_boundary": {
    "examples_dispatched": 10,
    "payload_equals_actual_sanitized": 10,
    "payload_exact_request_id_text_only": 10,
    "provider_calls_total": 10,
    "reconstruction_from_applied_spans_equals_output": 10,
    "zero_calls_on_failure": 0
  },
  "report_version": 1
}
````

### `reports/development_presidio.json`

````json
{
  "benign": {
    "benign_characters_removed": 0,
    "replacements_touching_benign": 0,
    "replacements_touching_no_gold": 0
  },
  "coverage": {
    "overall": {
      "coverage_rate": 0.9375,
      "full": 15,
      "gold": 16,
      "partial": 0,
      "untouched": 1
    },
    "per_type": {
      "CUSTOMER_ID": {
        "coverage_rate": 1.0,
        "full": 5,
        "gold": 5,
        "partial": 0,
        "untouched": 0
      },
      "EMAIL_ADDRESS": {
        "coverage_rate": 0.8571428571428571,
        "full": 6,
        "gold": 7,
        "partial": 0,
        "untouched": 1
      },
      "PHONE_NUMBER": {
        "coverage_rate": 1.0,
        "full": 4,
        "gold": 4,
        "partial": 0,
        "untouched": 0
      }
    }
  },
  "examples": [
    {
      "applied": [
        {
          "end": 21,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "score": 1.0,
          "start": 6,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 43,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "score": 1.0,
          "start": 32,
          "touches_benign": false,
          "touches_no_gold": false
        }
      ],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [
        {
          "end": 21,
          "entity_type": "EMAIL_ADDRESS",
          "score": 1.0,
          "start": 6
        },
        {
          "end": 43,
          "entity_type": "CUSTOMER_ID",
          "score": 1.0,
          "start": 32
        }
      ],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [
        {
          "coverage": "full",
          "end": 21,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "start": 6
        },
        {
          "coverage": "full",
          "end": 43,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "start": 32
        }
      ],
      "id": "dev-001",
      "matches_expected_sanitized": true,
      "no_gold_preserved": null,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [
        {
          "end": 19,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "score": 0.4,
          "start": 5,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 37,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "score": 1.0,
          "start": 26,
          "touches_benign": false,
          "touches_no_gold": false
        }
      ],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [
        {
          "end": 37,
          "entity_type": "CUSTOMER_ID",
          "score": 1.0,
          "start": 26
        },
        {
          "end": 19,
          "entity_type": "PHONE_NUMBER",
          "score": 0.4,
          "start": 5
        }
      ],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [
        {
          "coverage": "full",
          "end": 19,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "start": 5
        },
        {
          "coverage": "full",
          "end": 37,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "start": 26
        }
      ],
      "id": "dev-002",
      "matches_expected_sanitized": true,
      "no_gold_preserved": null,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [
        {
          "end": 25,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "score": 1.0,
          "start": 5,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 50,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "score": 1.0,
          "start": 30,
          "touches_benign": false,
          "touches_no_gold": false
        }
      ],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [
        {
          "end": 25,
          "entity_type": "EMAIL_ADDRESS",
          "score": 1.0,
          "start": 5
        },
        {
          "end": 50,
          "entity_type": "EMAIL_ADDRESS",
          "score": 1.0,
          "start": 30
        }
      ],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [
        {
          "coverage": "full",
          "end": 25,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "start": 5
        },
        {
          "coverage": "full",
          "end": 50,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "start": 30
        }
      ],
      "id": "dev-003",
      "matches_expected_sanitized": true,
      "no_gold_preserved": null,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [
        {
          "end": 23,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "score": 1.0,
          "start": 8,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 37,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "score": 1.0,
          "start": 26,
          "touches_benign": false,
          "touches_no_gold": false
        }
      ],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [
        {
          "end": 23,
          "entity_type": "EMAIL_ADDRESS",
          "score": 1.0,
          "start": 8
        },
        {
          "end": 37,
          "entity_type": "CUSTOMER_ID",
          "score": 1.0,
          "start": 26
        }
      ],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [
        {
          "coverage": "full",
          "end": 23,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "start": 8
        },
        {
          "coverage": "full",
          "end": 37,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "start": 26
        }
      ],
      "id": "dev-004",
      "matches_expected_sanitized": true,
      "no_gold_preserved": null,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [
        {
          "end": 29,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "score": 1.0,
          "start": 6,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 55,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "score": 0.75,
          "start": 41,
          "touches_benign": false,
          "touches_no_gold": false
        }
      ],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [
        {
          "end": 29,
          "entity_type": "EMAIL_ADDRESS",
          "score": 1.0,
          "start": 6
        },
        {
          "end": 17,
          "entity_type": "CUSTOMER_ID",
          "score": 1.0,
          "start": 6
        },
        {
          "end": 55,
          "entity_type": "PHONE_NUMBER",
          "score": 0.75,
          "start": 41
        }
      ],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [
        {
          "coverage": "full",
          "end": 29,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "start": 6
        },
        {
          "coverage": "full",
          "end": 55,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "start": 41
        }
      ],
      "id": "dev-005",
      "matches_expected_sanitized": true,
      "no_gold_preserved": null,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [],
      "id": "dev-006",
      "matches_expected_sanitized": true,
      "no_gold_preserved": true,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [
        {
          "end": 15,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "score": 1.0,
          "start": 4,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 32,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "score": 1.0,
          "start": 16,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 52,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "score": 0.4,
          "start": 38,
          "touches_benign": false,
          "touches_no_gold": false
        }
      ],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [
        {
          "end": 15,
          "entity_type": "CUSTOMER_ID",
          "score": 1.0,
          "start": 4
        },
        {
          "end": 32,
          "entity_type": "EMAIL_ADDRESS",
          "score": 1.0,
          "start": 16
        },
        {
          "end": 52,
          "entity_type": "PHONE_NUMBER",
          "score": 0.4,
          "start": 38
        }
      ],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [
        {
          "coverage": "full",
          "end": 15,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "start": 4
        },
        {
          "coverage": "full",
          "end": 32,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "start": 16
        },
        {
          "coverage": "full",
          "end": 52,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "start": 38
        }
      ],
      "id": "dev-007",
      "matches_expected_sanitized": true,
      "no_gold_preserved": null,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [
        {
          "end": 58,
          "entity_type": "PHONE_NUMBER",
          "score": 0.75,
          "start": 46
        }
      ],
      "dropped_by_scope": 1,
      "dropped_by_threshold": 0,
      "gold": [
        {
          "coverage": "untouched",
          "end": 26,
          "entity_type": "EMAIL_ADDRESS",
          "result": "FN",
          "start": 6
        }
      ],
      "id": "dev-008",
      "matches_expected_sanitized": false,
      "no_gold_preserved": null,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [
        {
          "end": 28,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "score": 0.75,
          "start": 14,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 51,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "score": 1.0,
          "start": 40,
          "touches_benign": false,
          "touches_no_gold": false
        }
      ],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [
        {
          "end": 51,
          "entity_type": "CUSTOMER_ID",
          "score": 1.0,
          "start": 40
        },
        {
          "end": 28,
          "entity_type": "PHONE_NUMBER",
          "score": 0.75,
          "start": 14
        }
      ],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [
        {
          "coverage": "full",
          "end": 28,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "start": 14
        },
        {
          "coverage": "full",
          "end": 51,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "start": 40
        }
      ],
      "id": "dev-009",
      "matches_expected_sanitized": true,
      "no_gold_preserved": null,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [],
      "id": "dev-010",
      "matches_expected_sanitized": true,
      "no_gold_preserved": true,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    }
  ],
  "meta": {
    "detector": "presidio",
    "fixture_sha256": "050aab48f30e09d9736f4e3b637d5b67175cb1a8a5e5af59607092b62b7cc172",
    "frozen_config_sha256": "1531d8b695db5f65414ee7778f4623547a7b67bd5363b9301d9cf2b20cd5eb3c",
    "packages": {
      "en-core-web-sm": "3.8.0",
      "phonenumbers": "9.0.43",
      "presidio-analyzer": "2.2.366",
      "regex": "2026.11.9",
      "spacy": "3.8.18",
      "tldextract": "5.4.0"
    },
    "python": "3.13.7",
    "resolution_policy": "validate all spans; phone scope gate; type thresholds (score >= t); dedupe same type/range keeping highest score; overlap resolution by length, score, type order EMAIL_ADDRESS>PHONE_NUMBER>CUSTOMER_ID, earlier start; replace right to left",
    "split": "development",
    "status": "procedural freeze of the development configuration; not a blinded external evaluation",
    "thresholds": {
      "CUSTOMER_ID": 1.0,
      "EMAIL_ADDRESS": 1.0,
      "PHONE_NUMBER": 0.4
    }
  },
  "metrics": {
    "micro": {
      "f1": 0.967741935483871,
      "fn": 1,
      "fp": 0,
      "precision": 1.0,
      "recall": 0.9375,
      "tp": 15
    },
    "per_type": {
      "CUSTOMER_ID": {
        "f1": 1.0,
        "fn": 0,
        "fp": 0,
        "precision": 1.0,
        "recall": 1.0,
        "tp": 5
      },
      "EMAIL_ADDRESS": {
        "f1": 0.9230769230769231,
        "fn": 1,
        "fp": 0,
        "precision": 1.0,
        "recall": 0.8571428571428571,
        "tp": 6
      },
      "PHONE_NUMBER": {
        "f1": 1.0,
        "fn": 0,
        "fp": 0,
        "precision": 1.0,
        "recall": 1.0,
        "tp": 4
      }
    }
  },
  "notes": [
    "Primary metrics score the spans actually applied after validation, scope gate, thresholds, dedupe and overlap resolution.",
    "diagnostic_pre_resolution_validated_candidates is a separate diagnostic and is not used for the metrics.",
    "Provider-boundary counts are separate from accuracy: a detector miss is an accuracy/coverage failure, not a boundary failure.",
    "Small synthetic template split; not evidence of real-world performance."
  ],
  "preservation": {
    "examples_equal_expected_sanitized": 9,
    "examples_failed_with_fixed_code": 0,
    "examples_total": 10,
    "examples_with_no_gold": 2,
    "no_gold_examples_preserved": 2
  },
  "provider_boundary": {
    "examples_dispatched": 10,
    "payload_equals_actual_sanitized": 10,
    "payload_exact_request_id_text_only": 10,
    "provider_calls_total": 10,
    "reconstruction_from_applied_spans_equals_output": 10,
    "zero_calls_on_failure": 0
  },
  "report_version": 1
}
````

### `reports/heldout_baseline.json`

````json
{
  "benign": {
    "benign_characters_removed": 0,
    "replacements_touching_benign": 0,
    "replacements_touching_no_gold": 0
  },
  "coverage": {
    "overall": {
      "coverage_rate": 1.0,
      "full": 28,
      "gold": 28,
      "partial": 0,
      "untouched": 0
    },
    "per_type": {
      "CUSTOMER_ID": {
        "coverage_rate": 1.0,
        "full": 8,
        "gold": 8,
        "partial": 0,
        "untouched": 0
      },
      "EMAIL_ADDRESS": {
        "coverage_rate": 1.0,
        "full": 12,
        "gold": 12,
        "partial": 0,
        "untouched": 0
      },
      "PHONE_NUMBER": {
        "coverage_rate": 1.0,
        "full": 8,
        "gold": 8,
        "partial": 0,
        "untouched": 0
      }
    }
  },
  "examples": [
    {
      "applied": [
        {
          "end": 40,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "score": 1.0,
          "start": 24,
          "touches_benign": false,
          "touches_no_gold": false
        }
      ],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [
        {
          "end": 40,
          "entity_type": "EMAIL_ADDRESS",
          "score": 1.0,
          "start": 24
        }
      ],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [
        {
          "coverage": "full",
          "end": 40,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "start": 24
        }
      ],
      "id": "test-001",
      "matches_expected_sanitized": true,
      "no_gold_preserved": null,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [
        {
          "end": 33,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "score": 1.0,
          "start": 19,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 59,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "score": 1.0,
          "start": 48,
          "touches_benign": false,
          "touches_no_gold": false
        }
      ],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [
        {
          "end": 33,
          "entity_type": "PHONE_NUMBER",
          "score": 1.0,
          "start": 19
        },
        {
          "end": 59,
          "entity_type": "CUSTOMER_ID",
          "score": 1.0,
          "start": 48
        }
      ],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [
        {
          "coverage": "full",
          "end": 33,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "start": 19
        },
        {
          "coverage": "full",
          "end": 59,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "start": 48
        }
      ],
      "id": "test-002",
      "matches_expected_sanitized": true,
      "no_gold_preserved": null,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [
        {
          "end": 28,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "score": 1.0,
          "start": 4,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 57,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "score": 1.0,
          "start": 46,
          "touches_benign": false,
          "touches_no_gold": false
        }
      ],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [
        {
          "end": 28,
          "entity_type": "EMAIL_ADDRESS",
          "score": 1.0,
          "start": 4
        },
        {
          "end": 57,
          "entity_type": "CUSTOMER_ID",
          "score": 1.0,
          "start": 46
        }
      ],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [
        {
          "coverage": "full",
          "end": 28,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "start": 4
        },
        {
          "coverage": "full",
          "end": 57,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "start": 46
        }
      ],
      "id": "test-003",
      "matches_expected_sanitized": true,
      "no_gold_preserved": null,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [
        {
          "end": 18,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "score": 1.0,
          "start": 7,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 36,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "score": 1.0,
          "start": 21,
          "touches_benign": false,
          "touches_no_gold": false
        }
      ],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [
        {
          "end": 36,
          "entity_type": "EMAIL_ADDRESS",
          "score": 1.0,
          "start": 21
        },
        {
          "end": 18,
          "entity_type": "CUSTOMER_ID",
          "score": 1.0,
          "start": 7
        }
      ],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [
        {
          "coverage": "full",
          "end": 18,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "start": 7
        },
        {
          "coverage": "full",
          "end": 36,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "start": 21
        }
      ],
      "id": "test-004",
      "matches_expected_sanitized": true,
      "no_gold_preserved": null,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [
        {
          "end": 36,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "score": 1.0,
          "start": 13,
          "touches_benign": false,
          "touches_no_gold": false
        }
      ],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [
        {
          "end": 36,
          "entity_type": "EMAIL_ADDRESS",
          "score": 1.0,
          "start": 13
        },
        {
          "end": 24,
          "entity_type": "CUSTOMER_ID",
          "score": 1.0,
          "start": 13
        }
      ],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [
        {
          "coverage": "full",
          "end": 36,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "start": 13
        }
      ],
      "id": "test-005",
      "matches_expected_sanitized": true,
      "no_gold_preserved": null,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [
        {
          "end": 32,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "score": 1.0,
          "start": 16,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 51,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "score": 1.0,
          "start": 35,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 68,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "score": 1.0,
          "start": 54,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 85,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "score": 1.0,
          "start": 71,
          "touches_benign": false,
          "touches_no_gold": false
        }
      ],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [
        {
          "end": 32,
          "entity_type": "EMAIL_ADDRESS",
          "score": 1.0,
          "start": 16
        },
        {
          "end": 51,
          "entity_type": "EMAIL_ADDRESS",
          "score": 1.0,
          "start": 35
        },
        {
          "end": 68,
          "entity_type": "PHONE_NUMBER",
          "score": 1.0,
          "start": 54
        },
        {
          "end": 85,
          "entity_type": "PHONE_NUMBER",
          "score": 1.0,
          "start": 71
        }
      ],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [
        {
          "coverage": "full",
          "end": 32,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "start": 16
        },
        {
          "coverage": "full",
          "end": 51,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "start": 35
        },
        {
          "coverage": "full",
          "end": 68,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "start": 54
        },
        {
          "coverage": "full",
          "end": 85,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "start": 71
        }
      ],
      "id": "test-006",
      "matches_expected_sanitized": true,
      "no_gold_preserved": null,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [],
      "id": "test-007",
      "matches_expected_sanitized": true,
      "no_gold_preserved": true,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [],
      "id": "test-008",
      "matches_expected_sanitized": true,
      "no_gold_preserved": true,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [],
      "id": "test-009",
      "matches_expected_sanitized": true,
      "no_gold_preserved": true,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [
        {
          "end": 39,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "score": 1.0,
          "start": 18,
          "touches_benign": false,
          "touches_no_gold": false
        }
      ],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [
        {
          "end": 39,
          "entity_type": "EMAIL_ADDRESS",
          "score": 1.0,
          "start": 18
        }
      ],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [
        {
          "coverage": "full",
          "end": 39,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "start": 18
        }
      ],
      "id": "test-010",
      "matches_expected_sanitized": true,
      "no_gold_preserved": null,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [
        {
          "end": 21,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "score": 1.0,
          "start": 7,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 39,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "score": 1.0,
          "start": 28,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 72,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "score": 1.0,
          "start": 50,
          "touches_benign": false,
          "touches_no_gold": false
        }
      ],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [
        {
          "end": 72,
          "entity_type": "EMAIL_ADDRESS",
          "score": 1.0,
          "start": 50
        },
        {
          "end": 21,
          "entity_type": "PHONE_NUMBER",
          "score": 1.0,
          "start": 7
        },
        {
          "end": 39,
          "entity_type": "CUSTOMER_ID",
          "score": 1.0,
          "start": 28
        }
      ],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [
        {
          "coverage": "full",
          "end": 21,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "start": 7
        },
        {
          "coverage": "full",
          "end": 39,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "start": 28
        },
        {
          "coverage": "full",
          "end": 72,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "start": 50
        }
      ],
      "id": "test-011",
      "matches_expected_sanitized": true,
      "no_gold_preserved": null,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [
        {
          "end": 25,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "score": 1.0,
          "start": 14,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 51,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "score": 1.0,
          "start": 32,
          "touches_benign": false,
          "touches_no_gold": false
        }
      ],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [
        {
          "end": 51,
          "entity_type": "EMAIL_ADDRESS",
          "score": 1.0,
          "start": 32
        },
        {
          "end": 25,
          "entity_type": "CUSTOMER_ID",
          "score": 1.0,
          "start": 14
        }
      ],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [
        {
          "coverage": "full",
          "end": 25,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "start": 14
        },
        {
          "coverage": "full",
          "end": 51,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "start": 32
        }
      ],
      "id": "test-012",
      "matches_expected_sanitized": true,
      "no_gold_preserved": null,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [
        {
          "end": 22,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "score": 1.0,
          "start": 0,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 34,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "score": 1.0,
          "start": 23,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 49,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "score": 1.0,
          "start": 35,
          "touches_benign": false,
          "touches_no_gold": false
        }
      ],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [
        {
          "end": 22,
          "entity_type": "EMAIL_ADDRESS",
          "score": 1.0,
          "start": 0
        },
        {
          "end": 49,
          "entity_type": "PHONE_NUMBER",
          "score": 1.0,
          "start": 35
        },
        {
          "end": 34,
          "entity_type": "CUSTOMER_ID",
          "score": 1.0,
          "start": 23
        }
      ],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [
        {
          "coverage": "full",
          "end": 22,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "start": 0
        },
        {
          "coverage": "full",
          "end": 34,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "start": 23
        },
        {
          "coverage": "full",
          "end": 49,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "start": 35
        }
      ],
      "id": "test-013",
      "matches_expected_sanitized": true,
      "no_gold_preserved": null,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [
        {
          "end": 27,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "score": 1.0,
          "start": 16,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 41,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "score": 1.0,
          "start": 30,
          "touches_benign": false,
          "touches_no_gold": false
        }
      ],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [
        {
          "end": 27,
          "entity_type": "CUSTOMER_ID",
          "score": 1.0,
          "start": 16
        },
        {
          "end": 41,
          "entity_type": "CUSTOMER_ID",
          "score": 1.0,
          "start": 30
        }
      ],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [
        {
          "coverage": "full",
          "end": 27,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "start": 16
        },
        {
          "coverage": "full",
          "end": 41,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "start": 30
        }
      ],
      "id": "test-014",
      "matches_expected_sanitized": true,
      "no_gold_preserved": null,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [
        {
          "end": 43,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "score": 1.0,
          "start": 26,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 64,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "score": 1.0,
          "start": 50,
          "touches_benign": false,
          "touches_no_gold": false
        }
      ],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [
        {
          "end": 43,
          "entity_type": "EMAIL_ADDRESS",
          "score": 1.0,
          "start": 26
        },
        {
          "end": 64,
          "entity_type": "PHONE_NUMBER",
          "score": 1.0,
          "start": 50
        }
      ],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [
        {
          "coverage": "full",
          "end": 43,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "start": 26
        },
        {
          "coverage": "full",
          "end": 64,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "start": 50
        }
      ],
      "id": "test-015",
      "matches_expected_sanitized": true,
      "no_gold_preserved": null,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [],
      "id": "test-016",
      "matches_expected_sanitized": true,
      "no_gold_preserved": true,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [],
      "id": "test-017",
      "matches_expected_sanitized": true,
      "no_gold_preserved": true,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [
        {
          "end": 39,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "score": 1.0,
          "start": 25,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 66,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "score": 1.0,
          "start": 52,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 95,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "score": 1.0,
          "start": 75,
          "touches_benign": false,
          "touches_no_gold": false
        }
      ],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [
        {
          "end": 95,
          "entity_type": "EMAIL_ADDRESS",
          "score": 1.0,
          "start": 75
        },
        {
          "end": 39,
          "entity_type": "PHONE_NUMBER",
          "score": 1.0,
          "start": 25
        },
        {
          "end": 66,
          "entity_type": "PHONE_NUMBER",
          "score": 1.0,
          "start": 52
        }
      ],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [
        {
          "coverage": "full",
          "end": 39,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "start": 25
        },
        {
          "coverage": "full",
          "end": 66,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "start": 52
        },
        {
          "coverage": "full",
          "end": 95,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "start": 75
        }
      ],
      "id": "test-018",
      "matches_expected_sanitized": true,
      "no_gold_preserved": null,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    }
  ],
  "meta": {
    "detector": "baseline",
    "fixture_sha256": "ce66e9a9dd74935a50f58c7252e50177702470676ebe7c98a060e8f0f3b38dc2",
    "frozen_config_sha256": "1531d8b695db5f65414ee7778f4623547a7b67bd5363b9301d9cf2b20cd5eb3c",
    "packages": {},
    "python": "3.13.7",
    "resolution_policy": "validate all spans; phone scope gate; type thresholds (score >= t); dedupe same type/range keeping highest score; overlap resolution by length, score, type order EMAIL_ADDRESS>PHONE_NUMBER>CUSTOMER_ID, earlier start; replace right to left",
    "split": "heldout",
    "status": "procedural freeze of the development configuration; not a blinded external evaluation",
    "thresholds": {
      "CUSTOMER_ID": 1.0,
      "EMAIL_ADDRESS": 1.0,
      "PHONE_NUMBER": 1.0
    }
  },
  "metrics": {
    "micro": {
      "f1": 1.0,
      "fn": 0,
      "fp": 0,
      "precision": 1.0,
      "recall": 1.0,
      "tp": 28
    },
    "per_type": {
      "CUSTOMER_ID": {
        "f1": 1.0,
        "fn": 0,
        "fp": 0,
        "precision": 1.0,
        "recall": 1.0,
        "tp": 8
      },
      "EMAIL_ADDRESS": {
        "f1": 1.0,
        "fn": 0,
        "fp": 0,
        "precision": 1.0,
        "recall": 1.0,
        "tp": 12
      },
      "PHONE_NUMBER": {
        "f1": 1.0,
        "fn": 0,
        "fp": 0,
        "precision": 1.0,
        "recall": 1.0,
        "tp": 8
      }
    }
  },
  "notes": [
    "Primary metrics score the spans actually applied after validation, scope gate, thresholds, dedupe and overlap resolution.",
    "diagnostic_pre_resolution_validated_candidates is a separate diagnostic and is not used for the metrics.",
    "Provider-boundary counts are separate from accuracy: a detector miss is an accuracy/coverage failure, not a boundary failure.",
    "Small synthetic template split; not evidence of real-world performance."
  ],
  "preservation": {
    "examples_equal_expected_sanitized": 18,
    "examples_failed_with_fixed_code": 0,
    "examples_total": 18,
    "examples_with_no_gold": 5,
    "no_gold_examples_preserved": 5
  },
  "provider_boundary": {
    "examples_dispatched": 18,
    "payload_equals_actual_sanitized": 18,
    "payload_exact_request_id_text_only": 18,
    "provider_calls_total": 18,
    "reconstruction_from_applied_spans_equals_output": 18,
    "zero_calls_on_failure": 0
  },
  "report_version": 1
}
````

### `reports/heldout_presidio.json`

````json
{
  "benign": {
    "benign_characters_removed": 5,
    "replacements_touching_benign": 1,
    "replacements_touching_no_gold": 0
  },
  "coverage": {
    "overall": {
      "coverage_rate": 0.9642857142857143,
      "full": 27,
      "gold": 28,
      "partial": 0,
      "untouched": 1
    },
    "per_type": {
      "CUSTOMER_ID": {
        "coverage_rate": 1.0,
        "full": 8,
        "gold": 8,
        "partial": 0,
        "untouched": 0
      },
      "EMAIL_ADDRESS": {
        "coverage_rate": 0.9166666666666666,
        "full": 11,
        "gold": 12,
        "partial": 0,
        "untouched": 1
      },
      "PHONE_NUMBER": {
        "coverage_rate": 1.0,
        "full": 8,
        "gold": 8,
        "partial": 0,
        "untouched": 0
      }
    }
  },
  "examples": [
    {
      "applied": [
        {
          "end": 40,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "score": 1.0,
          "start": 24,
          "touches_benign": false,
          "touches_no_gold": false
        }
      ],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [
        {
          "end": 40,
          "entity_type": "EMAIL_ADDRESS",
          "score": 1.0,
          "start": 24
        }
      ],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [
        {
          "coverage": "full",
          "end": 40,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "start": 24
        }
      ],
      "id": "test-001",
      "matches_expected_sanitized": true,
      "no_gold_preserved": null,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [
        {
          "end": 33,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "score": 0.4,
          "start": 19,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 59,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "score": 1.0,
          "start": 48,
          "touches_benign": false,
          "touches_no_gold": false
        }
      ],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [
        {
          "end": 59,
          "entity_type": "CUSTOMER_ID",
          "score": 1.0,
          "start": 48
        },
        {
          "end": 33,
          "entity_type": "PHONE_NUMBER",
          "score": 0.4,
          "start": 19
        }
      ],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [
        {
          "coverage": "full",
          "end": 33,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "start": 19
        },
        {
          "coverage": "full",
          "end": 59,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "start": 48
        }
      ],
      "id": "test-002",
      "matches_expected_sanitized": true,
      "no_gold_preserved": null,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [
        {
          "end": 28,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "score": 1.0,
          "start": 4,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 57,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "score": 1.0,
          "start": 46,
          "touches_benign": false,
          "touches_no_gold": false
        }
      ],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [
        {
          "end": 28,
          "entity_type": "EMAIL_ADDRESS",
          "score": 1.0,
          "start": 4
        },
        {
          "end": 57,
          "entity_type": "CUSTOMER_ID",
          "score": 1.0,
          "start": 46
        }
      ],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [
        {
          "coverage": "full",
          "end": 28,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "start": 4
        },
        {
          "coverage": "full",
          "end": 57,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "start": 46
        }
      ],
      "id": "test-003",
      "matches_expected_sanitized": true,
      "no_gold_preserved": null,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [
        {
          "end": 18,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "score": 1.0,
          "start": 7,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 36,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "score": 1.0,
          "start": 21,
          "touches_benign": false,
          "touches_no_gold": false
        }
      ],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [
        {
          "end": 18,
          "entity_type": "CUSTOMER_ID",
          "score": 1.0,
          "start": 7
        },
        {
          "end": 36,
          "entity_type": "EMAIL_ADDRESS",
          "score": 1.0,
          "start": 21
        }
      ],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [
        {
          "coverage": "full",
          "end": 18,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "start": 7
        },
        {
          "coverage": "full",
          "end": 36,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "start": 21
        }
      ],
      "id": "test-004",
      "matches_expected_sanitized": true,
      "no_gold_preserved": null,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [
        {
          "end": 36,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "score": 1.0,
          "start": 13,
          "touches_benign": false,
          "touches_no_gold": false
        }
      ],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [
        {
          "end": 36,
          "entity_type": "EMAIL_ADDRESS",
          "score": 1.0,
          "start": 13
        },
        {
          "end": 24,
          "entity_type": "CUSTOMER_ID",
          "score": 1.0,
          "start": 13
        }
      ],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [
        {
          "coverage": "full",
          "end": 36,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "start": 13
        }
      ],
      "id": "test-005",
      "matches_expected_sanitized": true,
      "no_gold_preserved": null,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [
        {
          "end": 32,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "score": 1.0,
          "start": 16,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 51,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "score": 1.0,
          "start": 35,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 68,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "score": 0.4,
          "start": 54,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 85,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "score": 0.4,
          "start": 71,
          "touches_benign": false,
          "touches_no_gold": false
        }
      ],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [
        {
          "end": 32,
          "entity_type": "EMAIL_ADDRESS",
          "score": 1.0,
          "start": 16
        },
        {
          "end": 51,
          "entity_type": "EMAIL_ADDRESS",
          "score": 1.0,
          "start": 35
        },
        {
          "end": 68,
          "entity_type": "PHONE_NUMBER",
          "score": 0.4,
          "start": 54
        },
        {
          "end": 85,
          "entity_type": "PHONE_NUMBER",
          "score": 0.4,
          "start": 71
        }
      ],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [
        {
          "coverage": "full",
          "end": 32,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "start": 16
        },
        {
          "coverage": "full",
          "end": 51,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "start": 35
        },
        {
          "coverage": "full",
          "end": 68,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "start": 54
        },
        {
          "coverage": "full",
          "end": 85,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "start": 71
        }
      ],
      "id": "test-006",
      "matches_expected_sanitized": true,
      "no_gold_preserved": null,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [],
      "id": "test-007",
      "matches_expected_sanitized": true,
      "no_gold_preserved": true,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [],
      "id": "test-008",
      "matches_expected_sanitized": true,
      "no_gold_preserved": true,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [
        {
          "end": 34,
          "entity_type": "PHONE_NUMBER",
          "score": 0.4,
          "start": 22
        },
        {
          "end": 50,
          "entity_type": "PHONE_NUMBER",
          "score": 0.4,
          "start": 37
        },
        {
          "end": 68,
          "entity_type": "PHONE_NUMBER",
          "score": 0.4,
          "start": 53
        }
      ],
      "dropped_by_scope": 3,
      "dropped_by_threshold": 0,
      "gold": [],
      "id": "test-009",
      "matches_expected_sanitized": true,
      "no_gold_preserved": true,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [
        {
          "coverage": "untouched",
          "end": 39,
          "entity_type": "EMAIL_ADDRESS",
          "result": "FN",
          "start": 18
        }
      ],
      "id": "test-010",
      "matches_expected_sanitized": false,
      "no_gold_preserved": null,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [
        {
          "end": 21,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "score": 0.4,
          "start": 7,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 39,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "score": 1.0,
          "start": 28,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 72,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "score": 1.0,
          "start": 50,
          "touches_benign": false,
          "touches_no_gold": false
        }
      ],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [
        {
          "end": 39,
          "entity_type": "CUSTOMER_ID",
          "score": 1.0,
          "start": 28
        },
        {
          "end": 72,
          "entity_type": "EMAIL_ADDRESS",
          "score": 1.0,
          "start": 50
        },
        {
          "end": 21,
          "entity_type": "PHONE_NUMBER",
          "score": 0.4,
          "start": 7
        }
      ],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [
        {
          "coverage": "full",
          "end": 21,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "start": 7
        },
        {
          "coverage": "full",
          "end": 39,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "start": 28
        },
        {
          "coverage": "full",
          "end": 72,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "start": 50
        }
      ],
      "id": "test-011",
      "matches_expected_sanitized": true,
      "no_gold_preserved": null,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [
        {
          "end": 25,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "score": 1.0,
          "start": 14,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 51,
          "entity_type": "EMAIL_ADDRESS",
          "result": "FP",
          "score": 1.0,
          "start": 27,
          "touches_benign": true,
          "touches_no_gold": false
        }
      ],
      "benign_characters_removed": 5,
      "diagnostic_pre_resolution_validated_candidates": [
        {
          "end": 25,
          "entity_type": "CUSTOMER_ID",
          "score": 1.0,
          "start": 14
        },
        {
          "end": 51,
          "entity_type": "EMAIL_ADDRESS",
          "score": 1.0,
          "start": 27
        }
      ],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [
        {
          "coverage": "full",
          "end": 25,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "start": 14
        },
        {
          "coverage": "full",
          "end": 51,
          "entity_type": "EMAIL_ADDRESS",
          "result": "FN",
          "start": 32
        }
      ],
      "id": "test-012",
      "matches_expected_sanitized": false,
      "no_gold_preserved": null,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [
        {
          "end": 22,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "score": 1.0,
          "start": 0,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 34,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "score": 1.0,
          "start": 23,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 49,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "score": 0.4,
          "start": 35,
          "touches_benign": false,
          "touches_no_gold": false
        }
      ],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [
        {
          "end": 22,
          "entity_type": "EMAIL_ADDRESS",
          "score": 1.0,
          "start": 0
        },
        {
          "end": 34,
          "entity_type": "CUSTOMER_ID",
          "score": 1.0,
          "start": 23
        },
        {
          "end": 49,
          "entity_type": "PHONE_NUMBER",
          "score": 0.4,
          "start": 35
        }
      ],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [
        {
          "coverage": "full",
          "end": 22,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "start": 0
        },
        {
          "coverage": "full",
          "end": 34,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "start": 23
        },
        {
          "coverage": "full",
          "end": 49,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "start": 35
        }
      ],
      "id": "test-013",
      "matches_expected_sanitized": true,
      "no_gold_preserved": null,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [
        {
          "end": 27,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "score": 1.0,
          "start": 16,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 41,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "score": 1.0,
          "start": 30,
          "touches_benign": false,
          "touches_no_gold": false
        }
      ],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [
        {
          "end": 27,
          "entity_type": "CUSTOMER_ID",
          "score": 1.0,
          "start": 16
        },
        {
          "end": 41,
          "entity_type": "CUSTOMER_ID",
          "score": 1.0,
          "start": 30
        }
      ],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [
        {
          "coverage": "full",
          "end": 27,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "start": 16
        },
        {
          "coverage": "full",
          "end": 41,
          "entity_type": "CUSTOMER_ID",
          "result": "TP",
          "start": 30
        }
      ],
      "id": "test-014",
      "matches_expected_sanitized": true,
      "no_gold_preserved": null,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [
        {
          "end": 43,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "score": 1.0,
          "start": 26,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 64,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "score": 0.4,
          "start": 50,
          "touches_benign": false,
          "touches_no_gold": false
        }
      ],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [
        {
          "end": 43,
          "entity_type": "EMAIL_ADDRESS",
          "score": 1.0,
          "start": 26
        },
        {
          "end": 64,
          "entity_type": "PHONE_NUMBER",
          "score": 0.4,
          "start": 50
        }
      ],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [
        {
          "coverage": "full",
          "end": 43,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "start": 26
        },
        {
          "coverage": "full",
          "end": 64,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "start": 50
        }
      ],
      "id": "test-015",
      "matches_expected_sanitized": true,
      "no_gold_preserved": null,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [],
      "id": "test-016",
      "matches_expected_sanitized": true,
      "no_gold_preserved": true,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [],
      "id": "test-017",
      "matches_expected_sanitized": true,
      "no_gold_preserved": true,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    },
    {
      "applied": [
        {
          "end": 39,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "score": 0.75,
          "start": 25,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 66,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "score": 0.4,
          "start": 52,
          "touches_benign": false,
          "touches_no_gold": false
        },
        {
          "end": 95,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "score": 1.0,
          "start": 75,
          "touches_benign": false,
          "touches_no_gold": false
        }
      ],
      "benign_characters_removed": 0,
      "diagnostic_pre_resolution_validated_candidates": [
        {
          "end": 95,
          "entity_type": "EMAIL_ADDRESS",
          "score": 1.0,
          "start": 75
        },
        {
          "end": 39,
          "entity_type": "PHONE_NUMBER",
          "score": 0.75,
          "start": 25
        },
        {
          "end": 66,
          "entity_type": "PHONE_NUMBER",
          "score": 0.4,
          "start": 52
        }
      ],
      "dropped_by_scope": 0,
      "dropped_by_threshold": 0,
      "gold": [
        {
          "coverage": "full",
          "end": 39,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "start": 25
        },
        {
          "coverage": "full",
          "end": 66,
          "entity_type": "PHONE_NUMBER",
          "result": "TP",
          "start": 52
        },
        {
          "coverage": "full",
          "end": 95,
          "entity_type": "EMAIL_ADDRESS",
          "result": "TP",
          "start": 75
        }
      ],
      "id": "test-018",
      "matches_expected_sanitized": true,
      "no_gold_preserved": null,
      "payload_equals_actual_sanitized": true,
      "payload_exact_request_id_text_only": true,
      "provider_calls": 1,
      "reconstruction_from_applied_spans_equals_output": true,
      "status": "ok"
    }
  ],
  "meta": {
    "detector": "presidio",
    "fixture_sha256": "ce66e9a9dd74935a50f58c7252e50177702470676ebe7c98a060e8f0f3b38dc2",
    "frozen_config_sha256": "1531d8b695db5f65414ee7778f4623547a7b67bd5363b9301d9cf2b20cd5eb3c",
    "packages": {
      "en-core-web-sm": "3.8.0",
      "phonenumbers": "9.0.43",
      "presidio-analyzer": "2.2.366",
      "regex": "2026.11.9",
      "spacy": "3.8.18",
      "tldextract": "5.4.0"
    },
    "python": "3.13.7",
    "resolution_policy": "validate all spans; phone scope gate; type thresholds (score >= t); dedupe same type/range keeping highest score; overlap resolution by length, score, type order EMAIL_ADDRESS>PHONE_NUMBER>CUSTOMER_ID, earlier start; replace right to left",
    "split": "heldout",
    "status": "procedural freeze of the development configuration; not a blinded external evaluation",
    "thresholds": {
      "CUSTOMER_ID": 1.0,
      "EMAIL_ADDRESS": 1.0,
      "PHONE_NUMBER": 0.4
    }
  },
  "metrics": {
    "micro": {
      "f1": 0.9454545454545454,
      "fn": 2,
      "fp": 1,
      "precision": 0.9629629629629629,
      "recall": 0.9285714285714286,
      "tp": 26
    },
    "per_type": {
      "CUSTOMER_ID": {
        "f1": 1.0,
        "fn": 0,
        "fp": 0,
        "precision": 1.0,
        "recall": 1.0,
        "tp": 8
      },
      "EMAIL_ADDRESS": {
        "f1": 0.8695652173913043,
        "fn": 2,
        "fp": 1,
        "precision": 0.9090909090909091,
        "recall": 0.8333333333333334,
        "tp": 10
      },
      "PHONE_NUMBER": {
        "f1": 1.0,
        "fn": 0,
        "fp": 0,
        "precision": 1.0,
        "recall": 1.0,
        "tp": 8
      }
    }
  },
  "notes": [
    "Primary metrics score the spans actually applied after validation, scope gate, thresholds, dedupe and overlap resolution.",
    "diagnostic_pre_resolution_validated_candidates is a separate diagnostic and is not used for the metrics.",
    "Provider-boundary counts are separate from accuracy: a detector miss is an accuracy/coverage failure, not a boundary failure.",
    "Small synthetic template split; not evidence of real-world performance."
  ],
  "preservation": {
    "examples_equal_expected_sanitized": 16,
    "examples_failed_with_fixed_code": 0,
    "examples_total": 18,
    "examples_with_no_gold": 5,
    "no_gold_examples_preserved": 5
  },
  "provider_boundary": {
    "examples_dispatched": 18,
    "payload_equals_actual_sanitized": 18,
    "payload_exact_request_id_text_only": 18,
    "provider_calls_total": 18,
    "reconstruction_from_applied_spans_equals_output": 18,
    "zero_calls_on_failure": 0
  },
  "report_version": 1
}
````

(`docs/handoff/START_HERE.md`, `docs/handoff/EVALUATION_CONTRACT.md`, `docs/handoff/MANIFEST.json` are the reviewer's unchanged files; their hashes are in the manifest below and in `MANIFEST.json`.)

## 9. Complete source, tests, workflow and documents

### `sanitizer/__init__.py`

````python
from .core import (MAX_INPUT_CHARS, RecordingMock, SanitizerError, baseline_detector,
                   dispatch, sanitize)

__all__ = ["MAX_INPUT_CHARS", "RecordingMock", "SanitizerError", "baseline_detector",
           "dispatch", "sanitize"]
````

### `sanitizer/__main__.py`

````python
import sys

from .cli import main

# stdin is read as bytes (sys.stdin.buffer) and decoded strictly, so no stdin
# reconfiguration is needed. stdout/stderr: UTF-8 and no CRLF translation, so
# stderr is exactly "<CODE>\n" on every platform.
sys.stdout.reconfigure(encoding="utf-8", newline="\n")
sys.stderr.reconfigure(encoding="utf-8", newline="\n")
sys.exit(main())
````

### `sanitizer/cli.py`

````python
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
````

### `sanitizer/config.py`

````python
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
````

### `sanitizer/core.py`

````python
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
````

### `sanitizer/demo.py`

````python
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
````

### `sanitizer/detectors.py`

````python
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
````

### `sanitizer/evaluation.py`

````python
"""Shared scoring, coverage, reporting and development-only threshold selection.

Stdlib only. Everything here scores the spans the real pipeline APPLIED (after validation, scope
gate, frozen thresholds, dedupe and overlap resolution). Reports contain example IDs, entity types,
scores, offsets, counts and metrics, and never raw text, matched values or sanitized text.
"""
import importlib.metadata as md
import itertools
import json
import platform
from collections import Counter
from fractions import Fraction
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .config import GRID
from .core import (ENTITY_PRIORITY, ERR_INVALID_FIXTURE, RecordingMock, SanitizerError, process,
                   replace_spans, run_pipeline)

REPORT_VERSION = 1
NO_PREDICTION_WITH_GOLD = "precision null, recall 0, F1 0 (contract section: primary accuracy metrics)"


# ---------------------------------------------------------------- fixtures
def load_fixture(path) -> Dict[str, Any]:
    """Parse and structurally validate a fixture; any problem -> ERR_INVALID_FIXTURE (no detail)."""
    try:
        fx = json.loads(Path(path).read_text(encoding="utf-8"))
        assert fx["schema_version"] == 1 and fx["offset_unit"] == "python_unicode_codepoint"
        seen = set()
        for ex in fx["examples"]:
            assert isinstance(ex["id"], str) and ex["id"] not in seen
            seen.add(ex["id"])
            assert isinstance(ex["text"], str) and isinstance(ex["expected_sanitized"], str)
            for g in ex["entities"]:
                assert g["entity_type"] in ENTITY_PRIORITY
                assert type(g["start"]) is int and type(g["end"]) is int
                assert 0 <= g["start"] < g["end"] <= len(ex["text"])
        return fx
    except Exception:
        raise SanitizerError(ERR_INVALID_FIXTURE) from None


# ---------------------------------------------------------------- metrics
def metrics(tp: int, fp: int, fn: int) -> Dict[str, Any]:
    """Integer counts and exact-denominator metrics; null when the metric's own denominator is 0."""
    return {
        "tp": tp, "fp": fp, "fn": fn,
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": tp / (tp + fn) if tp + fn else None,
        "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None,
    }


def score_example(text: str, gold: List[Dict[str, Any]], applied: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Score one example against the spans that were actually applied (original coordinates)."""
    g_keys = [(g["entity_type"], g["start"], g["end"]) for g in gold]
    p_keys = [(a["entity_type"], a["start"], a["end"]) for a in applied]
    avail = Counter(g_keys)
    pred_result = []
    for k in p_keys:  # one-to-one exact match on (type, start, end)
        if avail[k] > 0:
            avail[k] -= 1
            pred_result.append("TP")
        else:
            pred_result.append("FP")
    remaining = Counter(p_keys[i] for i, r in enumerate(pred_result) if r == "TP")
    gold_result = []
    for k in g_keys:
        if remaining[k] > 0:
            remaining[k] -= 1
            gold_result.append("TP")
        else:
            gold_result.append("FN")

    covered = set()
    for a in applied:
        covered.update(range(a["start"], a["end"]))
    gold_positions = set()
    for g in gold:
        gold_positions.update(range(g["start"], g["end"]))

    coverage = []
    for g in gold:
        pos = set(range(g["start"], g["end"]))
        n_in = len(pos & covered)
        coverage.append("full" if n_in == len(pos) else ("untouched" if n_in == 0 else "partial"))

    touches_benign, touches_no_gold = [], []
    for a in applied:
        pos = set(range(a["start"], a["end"]))
        touches_benign.append(bool(pos - gold_positions))
        touches_no_gold.append(not (pos & gold_positions))

    by_type = {t: {"tp": 0, "fp": 0, "fn": 0} for t in ENTITY_PRIORITY}
    for k, r in zip(p_keys, pred_result):
        by_type[k[0]]["tp" if r == "TP" else "fp"] += 1
    for k, r in zip(g_keys, gold_result):
        if r == "FN":
            by_type[k[0]]["fn"] += 1

    return {
        "by_type": by_type, "pred_result": pred_result, "gold_result": gold_result, "coverage": coverage,
        "touches_benign": touches_benign, "touches_no_gold": touches_no_gold,
        "benign_characters_removed": len(covered - gold_positions),
    }


def aggregate(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Sum counts across examples BEFORE computing micro metrics."""
    tot = {t: {"tp": 0, "fp": 0, "fn": 0} for t in ENTITY_PRIORITY}
    cov = {t: Counter() for t in ENTITY_PRIORITY}
    benign = {"replacements_touching_benign": 0, "replacements_touching_no_gold": 0,
              "benign_characters_removed": 0}
    pres = {"examples_total": 0, "examples_with_no_gold": 0, "no_gold_examples_preserved": 0,
            "examples_equal_expected_sanitized": 0, "examples_failed_with_fixed_code": 0}
    boundary = {"examples_dispatched": 0, "provider_calls_total": 0,
                "payload_exact_request_id_text_only": 0, "payload_equals_actual_sanitized": 0,
                "reconstruction_from_applied_spans_equals_output": 0, "zero_calls_on_failure": 0}
    for r in records:
        s = r["_score"]
        for t in ENTITY_PRIORITY:
            for k in ("tp", "fp", "fn"):
                tot[t][k] += s["by_type"][t][k]
        for g, c in zip(r["gold"], s["coverage"]):
            cov[g["entity_type"]][c] += 1
        benign["replacements_touching_benign"] += sum(s["touches_benign"])
        benign["replacements_touching_no_gold"] += sum(s["touches_no_gold"])
        benign["benign_characters_removed"] += s["benign_characters_removed"]
        pres["examples_total"] += 1
        if not r["gold"]:
            pres["examples_with_no_gold"] += 1
            pres["no_gold_examples_preserved"] += 1 if r["no_gold_preserved"] else 0
        pres["examples_equal_expected_sanitized"] += 1 if r["matches_expected_sanitized"] else 0
        if r["status"] != "ok":
            pres["examples_failed_with_fixed_code"] += 1
            boundary["zero_calls_on_failure"] += 1 if r["provider_calls"] == 0 else 0
        else:
            boundary["examples_dispatched"] += 1
            boundary["payload_exact_request_id_text_only"] += 1 if r["payload_exact_keys"] else 0
            boundary["payload_equals_actual_sanitized"] += 1 if r["payload_equals_sanitized"] else 0
            boundary["reconstruction_from_applied_spans_equals_output"] += 1 if r["reconstruction_ok"] else 0
        boundary["provider_calls_total"] += r["provider_calls"]

    per_type = {t: metrics(**tot[t]) for t in ENTITY_PRIORITY}
    micro = metrics(sum(tot[t]["tp"] for t in ENTITY_PRIORITY), sum(tot[t]["fp"] for t in ENTITY_PRIORITY),
                    sum(tot[t]["fn"] for t in ENTITY_PRIORITY))

    def cov_block(c: Counter) -> Dict[str, Any]:
        total = c["full"] + c["partial"] + c["untouched"]
        return {"gold": total, "full": c["full"], "partial": c["partial"], "untouched": c["untouched"],
                "coverage_rate": c["full"] / total if total else None}

    overall = Counter()
    for t in ENTITY_PRIORITY:
        overall.update(cov[t])
    return {
        "per_type": per_type, "micro": micro,
        "coverage": {"overall": cov_block(overall), "per_type": {t: cov_block(cov[t]) for t in ENTITY_PRIORITY}},
        "benign": benign, "preservation": pres, "boundary": boundary,
    }


# ---------------------------------------------------------------- running a split
def run_split(fixture: Dict[str, Any], detector_for: Callable[[Dict[str, Any]], Callable[[str], Any]],
              thresholds: Dict[str, float]) -> List[Dict[str, Any]]:
    """Run every example through the REAL pipeline/dispatch path with a RecordingMock provider."""
    records = []
    for i, ex in enumerate(fixture["examples"], 1):
        mock = RecordingMock()
        rid = f"req-{i:03d}"
        try:
            payload, res = run_pipeline(rid, ex["text"], mock, detector_for(ex), thresholds=thresholds)
            status = "ok"
        except SanitizerError as e:
            payload, res, status = None, None, e.code
        applied = res.applied if res else []
        sanitized = res.sanitized if res else None
        sc = score_example(ex["text"], ex["entities"], applied)
        rec = {
            "id": ex["id"], "status": status, "gold": [dict(g) for g in ex["entities"]],
            "applied": [{"entity_type": a["entity_type"], "start": a["start"], "end": a["end"], "score": a["score"]}
                        for a in applied],
            "provider_calls": len(mock.calls),
            "matches_expected_sanitized": sanitized == ex["expected_sanitized"],
            "payload_exact_keys": bool(payload) and mock.calls == [payload] and list(payload) == ["request_id", "text"],
            "payload_equals_sanitized": bool(payload) and payload["text"] == sanitized,
            "reconstruction_ok": bool(res) and replace_spans(ex["text"], applied) == sanitized,
            "no_gold_preserved": (sanitized == ex["text"]) if not ex["entities"] else None,
            "dropped_by_scope": res.dropped_by_scope if res else 0,
            "dropped_by_threshold": res.dropped_by_threshold if res else 0,
            # DIAGNOSTIC ONLY (pre-filter, pre-resolution); never used for the primary metrics
            "diagnostic_validated_candidates": [
                {"entity_type": v["entity_type"], "start": v["start"], "end": v["end"], "score": v["score"]}
                for v in (res.validated if res else [])],
            "_score": sc,
        }
        records.append(rec)
    return records


def public_examples(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for r in records:
        s = r["_score"]
        gold = [dict(g, result=res, coverage=c) for g, res, c in zip(r["gold"], s["gold_result"], s["coverage"])]
        applied = [dict(a, result=res, touches_benign=tb, touches_no_gold=tn)
                   for a, res, tb, tn in zip(r["applied"], s["pred_result"], s["touches_benign"], s["touches_no_gold"])]
        out.append({
            "id": r["id"], "status": r["status"], "gold": gold, "applied": applied,
            "benign_characters_removed": s["benign_characters_removed"],
            "matches_expected_sanitized": r["matches_expected_sanitized"],
            "payload_equals_actual_sanitized": r["payload_equals_sanitized"],
            "payload_exact_request_id_text_only": r["payload_exact_keys"],
            "provider_calls": r["provider_calls"],
            "reconstruction_from_applied_spans_equals_output": r["reconstruction_ok"],
            "no_gold_preserved": r["no_gold_preserved"],
            "dropped_by_scope": r["dropped_by_scope"], "dropped_by_threshold": r["dropped_by_threshold"],
            "diagnostic_pre_resolution_validated_candidates": r["diagnostic_validated_candidates"],
        })
    return out


def package_versions(names=("presidio-analyzer", "spacy", "en-core-web-sm", "phonenumbers", "tldextract", "regex")):
    out = {}
    for n in names:
        try:
            out[n] = md.version(n)
        except md.PackageNotFoundError:
            out[n] = None
    return out


def build_report(meta: Dict[str, Any], records: List[Dict[str, Any]]) -> Dict[str, Any]:
    agg = aggregate(records)
    return {
        "report_version": REPORT_VERSION, "meta": meta,
        "metrics": {"per_type": agg["per_type"], "micro": agg["micro"]},
        "coverage": agg["coverage"], "benign": agg["benign"], "preservation": agg["preservation"],
        "provider_boundary": agg["boundary"], "examples": public_examples(records),
        "notes": [
            "Primary metrics score the spans actually applied after validation, scope gate, thresholds, dedupe and overlap resolution.",
            "diagnostic_pre_resolution_validated_candidates is a separate diagnostic and is not used for the metrics.",
            "Provider-boundary counts are separate from accuracy: a detector miss is an accuracy/coverage failure, not a boundary failure.",
            "Small synthetic template split; not evidence of real-world performance.",
        ],
    }


def dump_report(report: Dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def run_meta(detector: str, split: str, fixture_sha: str, thresholds: Dict[str, float],
             config_sha: Optional[str], extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    meta = {
        "detector": detector, "split": split, "fixture_sha256": fixture_sha, "thresholds": thresholds,
        "frozen_config_sha256": config_sha, "python": platform.python_version(),
        "packages": package_versions() if detector == "presidio" else {},
        "resolution_policy": "validate all spans; phone scope gate; type thresholds (score >= t); dedupe same type/range "
                             "keeping highest score; overlap resolution by length, score, type order "
                             "EMAIL_ADDRESS>PHONE_NUMBER>CUSTOMER_ID, earlier start; replace right to left",
        "status": "procedural freeze of the development configuration; not a blinded external evaluation",
    }
    if extra:
        meta.update(extra)
    return meta


# ---------------------------------------------------------------- development-only threshold selection
def collect_raw(fixture: Dict[str, Any], detector_fn: Callable[[str], Any]) -> Dict[str, Any]:
    """Run the NLP detector ONCE per example and cache its raw candidates (development only)."""
    return {ex["id"]: detector_fn(ex["text"]) for ex in fixture["examples"]}


def pick_best(grid: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Highest F1 (exact Fraction in `_f1`), then fewer benign characters removed, then lexicographically
    higher thresholds in EMAIL_ADDRESS, PHONE_NUMBER, CUSTOMER_ID order."""
    return max(grid, key=lambda r: (r["_f1"], -r["benign_characters_removed"], r["thresholds"]["EMAIL_ADDRESS"],
                                    r["thresholds"]["PHONE_NUMBER"], r["thresholds"]["CUSTOMER_ID"]))


def select_thresholds(fixture: Dict[str, Any], raw_by_id: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate GRID^3 on cached development candidates through the full shared pipeline.

    Rule: highest development exact-span micro F1; ties -> fewer benign characters removed;
    then lexicographically higher thresholds in (EMAIL_ADDRESS, PHONE_NUMBER, CUSTOMER_ID) order.
    """
    grid = []
    for e, p, c in itertools.product(GRID, repeat=3):
        th = {"EMAIL_ADDRESS": e, "PHONE_NUMBER": p, "CUSTOMER_ID": c}
        tp = fp = fn = benign = 0
        for ex in fixture["examples"]:
            cands = raw_by_id[ex["id"]]
            res = process(ex["text"], lambda _t, c_=cands: c_, thresholds=th)
            sc = score_example(ex["text"], ex["entities"], res.applied)
            for t in ENTITY_PRIORITY:
                tp += sc["by_type"][t]["tp"]
                fp += sc["by_type"][t]["fp"]
                fn += sc["by_type"][t]["fn"]
            benign += sc["benign_characters_removed"]
        f1 = Fraction(2 * tp, 2 * tp + fp + fn) if 2 * tp + fp + fn else Fraction(0)
        grid.append({"thresholds": th, "tp": tp, "fp": fp, "fn": fn, "benign_characters_removed": benign,
                     "f1": float(f1), "_f1": f1})
    best = pick_best(grid)
    ties = [r["thresholds"] for r in grid
            if r["_f1"] == best["_f1"] and r["benign_characters_removed"] == best["benign_characters_removed"]]
    for r in grid:
        del r["_f1"]
    return {"best": {k: v for k, v in best.items() if k != "_f1"}, "grid": grid, "tied_at_top_after_benign_rule": len(ties)}
````

### `sanitizer/fixture.py`

````python
"""Synthetic development fixture dev-001 and canaries (they appear in source by design)."""

CANARY_EMAIL = "ava@example.com"
CANARY_CUSTOMER = "CUST-004271"
CANARY_PHONE = "(415) 555-0132"  # inside the frozen phone scope: (AAA) BBB-CCCC, A and first B in 2-9

DEV_001 = {
    "id": "dev-001",
    "text": "Email ava@example.com; customer CUST-004271; quantity 24.",
    "entities": [
        {"entity_type": "EMAIL_ADDRESS", "start": 6, "end": 21},
        {"entity_type": "CUSTOMER_ID", "start": 32, "end": 43},
    ],
}

# All-three-entity synthetic canary text (gold offsets are located by substring, not by a detector).
CANARY_TEXT = f"Email {CANARY_EMAIL}; phone {CANARY_PHONE}; customer {CANARY_CUSTOMER}; quantity 24."
CANARY_SANITIZED = "Email [EMAIL_ADDRESS]; phone [PHONE_NUMBER]; customer [CUSTOMER_ID]; quantity 24."
CANARY_GOLD = [
    {"entity_type": t, "start": CANARY_TEXT.index(v), "end": CANARY_TEXT.index(v) + len(v)}
    for t, v in (("EMAIL_ADDRESS", CANARY_EMAIL), ("PHONE_NUMBER", CANARY_PHONE), ("CUSTOMER_ID", CANARY_CUSTOMER))
]
````

### `sanitizer/freeze.py`

````python
"""Development-only threshold selection and the procedural freeze (frozen_config.json).

Held-out data is only HASHED here (bytes, never parsed). Everything else is derived from
development.json.
"""
import json
import platform
import re
from pathlib import Path
from typing import Any, Dict

from .config import CONFIG_VERSION, GRID, PROJECT_ROOT, file_sha256
from .core import CUSTOMER_ID_RE, ENTITY_PRIORITY, ERR_INVALID_CONFIG, PHONE_SCOPE_RE, SanitizerError
from .detectors import build_presidio
from .evaluation import aggregate, collect_raw, load_fixture, package_versions, run_split, select_thresholds

SELECTION_RULE = (
    "Candidate thresholds from {0.0,0.4,0.6,0.8,1.0}^3 evaluated on development.json only, using cached raw "
    "candidates through the full shared pipeline (validate all, phone scope gate, score >= threshold, dedupe, "
    "overlap resolution). Choose the highest development exact-span micro F1; ties -> fewer benign characters "
    "removed; then lexicographically higher thresholds in EMAIL_ADDRESS, PHONE_NUMBER, CUSTOMER_ID order."
)


def model_wheel_sha256(requirements_path: Path) -> str:
    for line in requirements_path.read_text(encoding="utf-8").splitlines():
        if line.lower().startswith("en_core_web_sm"):
            m = re.search(r"sha256=([0-9a-f]{64})", line)
            if m:
                return m.group(1)
    raise SanitizerError(ERR_INVALID_CONFIG)


def build_frozen_config(dev_path: Path, heldout_path: Path, requirements_path: Path) -> Dict[str, Any]:
    fixture = load_fixture(dev_path)  # development ONLY
    fn, _mod, analyzer = build_presidio()
    raw = collect_raw(fixture, fn)  # NLP runs once per development example
    sel = select_thresholds(fixture, raw)
    th = sel["best"]["thresholds"]
    records = run_split(fixture, lambda ex: (lambda _t, c=raw[ex["id"]]: c), th)
    agg = aggregate(records)
    return {
        "config_version": CONFIG_VERSION,
        "detector": "presidio",
        "freeze_kind": "procedural freeze of the development configuration; not a blinded external evaluation",
        "heldout_access": "heldout.json was hashed as raw bytes only; its contents were not parsed or read "
                          "before this file was written",
        "thresholds": th,
        "threshold_grid": list(GRID),
        "selection_rule": SELECTION_RULE,
        "selection_grid_size": len(sel["grid"]),
        "selection_tied_at_top_after_benign_rule": sel["tied_at_top_after_benign_rule"],
        "selection_grid": sel["grid"],
        "development_metrics_at_selected_thresholds": {
            "micro": agg["micro"], "per_type": agg["per_type"], "coverage": agg["coverage"], "benign": agg["benign"]},
        "development_sha256": file_sha256(dev_path),
        "heldout_sha256": file_sha256(heldout_path),
        "scope": {
            "entities": list(ENTITY_PRIORITY),
            "PHONE_NUMBER_scope_regex": PHONE_SCOPE_RE.pattern,
            "CUSTOMER_ID_regex": CUSTOMER_ID_RE.pattern,
            "phone_gate": "after validation, a PHONE_NUMBER candidate is kept only if its exact (start,end) is a "
                          "match of the scope regex on the original text; never repaired, trimmed or synthesized",
        },
        "resolution_policy": "decreasing length, decreasing score, type order EMAIL_ADDRESS>PHONE_NUMBER>CUSTOMER_ID, "
                             "earlier start; keep non-overlapping; replace right to left with [TYPE]",
        "baseline": {"score": 1.0, "thresholds": {t: 1.0 for t in ENTITY_PRIORITY}},
        "recognizer_settings": _mod.recognizer_settings(analyzer),
        "packages": package_versions(),
        "model_wheel_sha256": model_wheel_sha256(requirements_path),
        "python": platform.python_version(),
    }


def write_frozen_config(out: Path, cfg: Dict[str, Any]) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(cfg, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8", newline="\n")
````

### `sanitizer/presidio_check.py`

````python
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
````

### `sanitizer/presidio_detector.py`

````python
"""Candidate detector: Presidio rule-based recognizers on a spaCy NLP engine.

NOT a trained PII model. Three rule-based recognizers are registered (email, US phone, a
custom CUSTOMER_ID regex); the small spaCy model only provides tokens/lemmas for Presidio's
context enhancer and no NER recognizer is registered. Requires presidio-analyzer and the
en_core_web_sm model. sanitizer.core never imports this module, so the stdlib-only baseline
is unaffected.
"""
import logging
from typing import Any, Callable, Dict, List

import regex
import tldextract
from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_analyzer.predefined_recognizers import EmailRecognizer, PhoneRecognizer

from .core import ENTITY_PRIORITY

LANGUAGE = "en"
SPACY_MODEL = "en_core_web_sm"
PHONE_REGIONS = ("US",)  # frozen scope: US only; the shared exact-format gate narrows it further

# Same rule as the baseline: case-sensitive CUST- + exactly six ASCII digits, not inside a token.
CUSTOMER_ID_REGEX = r"(?<![A-Za-z0-9_])CUST-[0-9]{6}(?![A-Za-z0-9_])"

# Stock EmailRecognizer.validate_result calls tldextract.extract(), whose default extractor
# tries to download the Public Suffix List (publicsuffix.org, then raw.githubusercontent.com)
# and writes a cache inside site-packages or the user profile. This subclass validates with
# the suffix snapshot bundled in the tldextract wheel: no network, no cache directory. The
# snapshot can be stale versus the live list. (The stock recognizer is reachable only through
# the diagnostic `python -m sanitizer.presidio_check --stock-email`, never through the CLI.)
_OFFLINE_TLD = tldextract.TLDExtract(suffix_list_urls=(), cache_dir=None)


class OfflineEmailRecognizer(EmailRecognizer):
    def validate_result(self, pattern_text: str):
        return _OFFLINE_TLD(pattern_text).fqdn != ""


def build_registry(stock_email: bool = False) -> RecognizerRegistry:
    registry = RecognizerRegistry(supported_languages=[LANGUAGE])
    email_cls = EmailRecognizer if stock_email else OfflineEmailRecognizer
    registry.add_recognizer(email_cls(supported_language=LANGUAGE))
    registry.add_recognizer(PhoneRecognizer(supported_language=LANGUAGE, supported_regions=PHONE_REGIONS))
    registry.add_recognizer(PatternRecognizer(
        supported_entity="CUSTOMER_ID",
        name="CustomerIdRecognizer",
        supported_language=LANGUAGE,
        patterns=[Pattern("customer-id", CUSTOMER_ID_REGEX, 1.0)],
        # Presidio's default flags include IGNORECASE; the rule is case-sensitive.
        global_regex_flags=regex.MULTILINE | regex.DOTALL,
    ))
    return registry


def build_analyzer(stock_email: bool = False) -> AnalyzerEngine:
    # Presidio's DEBUG records include input text (LemmaContextAwareEnhancer logs
    # "Context list is: ... <text around the match>"). This process-wide setting keeps that
    # logger at INFO or above. It does NOT protect against an application re-lowering the level.
    logging.getLogger("presidio-analyzer").setLevel(logging.INFO)
    nlp_engine = NlpEngineProvider(nlp_configuration={
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": LANGUAGE, "model_name": SPACY_MODEL}],
    }).create_engine()
    return AnalyzerEngine(registry=build_registry(stock_email), nlp_engine=nlp_engine,
                          supported_languages=[LANGUAGE])


def make_detector(analyzer: AnalyzerEngine = None) -> Callable[[str], List[Dict[str, Any]]]:
    """Return detector(text) -> raw candidates in the sanitizer's detector contract (all scores)."""
    analyzer = analyzer or build_analyzer()

    def detect(text: str) -> List[Dict[str, Any]]:
        results = analyzer.analyze(text=text, language=LANGUAGE, entities=list(ENTITY_PRIORITY))
        return [{"entity_type": r.entity_type, "start": r.start, "end": r.end, "score": r.score}
                for r in results]

    return detect


def recognizer_settings(analyzer: AnalyzerEngine) -> Dict[str, Any]:
    """Settings recorded in frozen_config.json (read from the live objects, not retyped)."""
    recognizers = []
    for r in analyzer.registry.recognizers:
        item = {"name": r.name, "class": type(r).__name__, "entities": list(r.supported_entities)}
        if hasattr(r, "supported_regions"):
            item["supported_regions"] = list(r.supported_regions)
            item["leniency"] = r.leniency
            item["base_score"] = r.SCORE
        if hasattr(r, "patterns"):
            item["patterns"] = [{"name": p.name, "regex": p.regex, "score": p.score} for p in r.patterns]
            item["regex_flags"] = repr(r.global_regex_flags)
        recognizers.append(item)
    return {
        "recognizers": recognizers,
        "nlp_engine": type(analyzer.nlp_engine).__name__,
        "spacy_model": SPACY_MODEL,
        "spacy_pipeline": list(analyzer.nlp_engine.nlp[LANGUAGE].pipe_names),
        "ner_recognizer_registered": any(type(r).__name__ == "SpacyRecognizer" for r in analyzer.registry.recognizers),
        "context_enhancer": type(analyzer.context_aware_enhancer).__name__,
        "analyze_entities": list(ENTITY_PRIORITY),
        "engine_default_score_threshold": analyzer.default_score_threshold,
        "email_validator": "offline tldextract snapshot (suffix_list_urls=(), cache_dir=None)",
        "presidio_logger_level": "INFO (process-wide setting made in build_analyzer)",
    }
````

### `.github/workflows/ci.yml`

````yaml
# Basic CI. Status: configuration only; no hosted run has been executed (hosted CI is PENDING).
# The same commands were run locally on Windows 11 / Python 3.13.7 (see FINAL_REVIEW_PACKET.md).
name: ci

on:
  push:
  pull_request:

jobs:
  baseline:
    name: baseline (stdlib only)
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      - name: Unit tests (candidate tests skip here because Presidio is not installed)
        run: python -m unittest discover -v
      - name: Deterministic baseline evaluation rerun matches committed reports
        run: python scripts/check_reports.py baseline
      - name: Synthetic demo (baseline)
        run: python -m sanitizer demo --detector baseline

  candidate:
    name: candidate (Presidio + en_core_web_sm)
    runs-on: windows-latest
    env:
      REQUIRE_CANDIDATE_TESTS: "1"   # missing dependencies FAIL instead of skipping
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      # Short venv path: a deep path made spaCy fail to load a DLL on Windows.
      - name: Create venv at a short path
        run: python -m venv C:\pv
      - name: Install pinned dependencies and the model wheel (uses the network)
        run: C:\pv\Scripts\python -m pip install -r requirements-presidio.txt
      - name: pip check
        run: C:\pv\Scripts\python -m pip check
      - name: Full suite; any skipped test fails the job
        run: C:\pv\Scripts\python scripts/run_tests_no_skips.py
      - name: Deterministic evaluation rerun matches committed reports (both detectors)
        run: C:\pv\Scripts\python scripts/check_reports.py baseline presidio
      - name: Synthetic demo (candidate)
        run: C:\pv\Scripts\python -m sanitizer demo --detector presidio
````

### `scripts/check_reports.py`

````python
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
````

### `scripts/render_summary.py`

````python
"""Render reports/SUMMARY.md from the JSON reports, and optionally refresh the block in README.md.

    python scripts/render_summary.py [--update-readme]

Stdlib only. Every number comes from reports/*.json; nothing is typed by hand. A test checks that the
README block equals this output, so documented numbers cannot drift from the reports.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORTS = ROOT / "reports"
BEGIN, END = "<!-- SUMMARY:BEGIN -->", "<!-- SUMMARY:END -->"
TYPES = ("EMAIL_ADDRESS", "PHONE_NUMBER", "CUSTOMER_ID")
RUNS = (("baseline", "development"), ("presidio", "development"), ("baseline", "heldout"), ("presidio", "heldout"))


def f(v):
    return "n/a" if v is None else f"{v:.4f}"


def render() -> str:
    reps = {(d, s): json.loads((REPORTS / f"{s}_{d}.json").read_text(encoding="utf-8")) for d, s in RUNS}
    out = []
    for split in ("development", "heldout"):
        out.append(f"#### {split} (exact-span, after validation, scope gate, thresholds and overlap resolution)\n")
        out.append("| Detector | Type | TP | FP | FN | Precision | Recall | F1 |")
        out.append("|---|---|---:|---:|---:|---:|---:|---:|")
        for det in ("baseline", "presidio"):
            m = reps[(det, split)]["metrics"]
            for t in TYPES + ("micro",):
                b = m["micro"] if t == "micro" else m["per_type"][t]
                name = "**micro**" if t == "micro" else t
                out.append(f"| {det} | {name} | {b['tp']} | {b['fp']} | {b['fn']} | {f(b['precision'])} | {f(b['recall'])} | {f(b['f1'])} |")
        out.append("")
        out.append("| Detector | Gold fully covered | Partial | Untouched | Coverage rate | Replacements touching benign | "
                   "Touching no gold | Benign chars removed | Benign-only examples preserved | Outputs equal oracle |")
        out.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
        for det in ("baseline", "presidio"):
            r = reps[(det, split)]
            c, b, p = r["coverage"]["overall"], r["benign"], r["preservation"]
            out.append(f"| {det} | {c['full']}/{c['gold']} | {c['partial']} | {c['untouched']} | {f(c['coverage_rate'])} | "
                       f"{b['replacements_touching_benign']} | {b['replacements_touching_no_gold']} | {b['benign_characters_removed']} | "
                       f"{p['no_gold_examples_preserved']}/{p['examples_with_no_gold']} | "
                       f"{p['examples_equal_expected_sanitized']}/{p['examples_total']} |")
        out.append("")
        out.append("| Detector | Examples dispatched | Provider calls | Payload is exactly {request_id, text} | "
                   "Payload text equals actual sanitized text | Output rebuilt from applied spans |")
        out.append("|---|---:|---:|---:|---:|---:|")
        for det in ("baseline", "presidio"):
            q = reps[(det, split)]["provider_boundary"]
            out.append(f"| {det} | {q['examples_dispatched']} | {q['provider_calls_total']} | "
                       f"{q['payload_exact_request_id_text_only']} | {q['payload_equals_actual_sanitized']} | "
                       f"{q['reconstruction_from_applied_spans_equals_output']} |")
        out.append("")
    th = reps[("presidio", "heldout")]["meta"]["thresholds"]
    out.append(f"Frozen candidate thresholds (selected on development only): "
               f"EMAIL_ADDRESS {th['EMAIL_ADDRESS']}, PHONE_NUMBER {th['PHONE_NUMBER']}, CUSTOMER_ID {th['CUSTOMER_ID']}. "
               f"Baseline: score 1.0, threshold 1.0 for all three types.")
    return "\n".join(out) + "\n"


def main() -> int:
    text = render()
    (REPORTS / "SUMMARY.md").write_text("# Evaluation summary (generated by scripts/render_summary.py)\n\n" + text,
                                        encoding="utf-8", newline="\n")
    if "--update-readme" in sys.argv[1:]:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        a, b = readme.index(BEGIN) + len(BEGIN), readme.index(END)
        (ROOT / "README.md").write_text(readme[:a] + "\n\n" + text + "\n" + readme[b:], encoding="utf-8", newline="\n")
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
````

### `scripts/run_tests_no_skips.py`

````python
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
````

### `tests/support.py`

````python
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
````

### `tests/test_cli.py`

````python
"""CLI behavior: detector selection, summary flag, dependency/config failures, evaluation gating,
determinism, privacy of reports, and the explicit synthetic demo. No held-out data is read here
(the held-out gate is only tested with a path that does not exist)."""
import json
import os
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

from sanitizer.config import FIXTURE_DIR
from sanitizer.evaluation import load_fixture
from sanitizer.fixture import CANARY_CUSTOMER, CANARY_EMAIL, CANARY_PHONE, CANARY_SANITIZED, CANARY_TEXT

from .support import EMAIL, CUST, FROZEN_CONFIG, LogCapture, ROOT, TEXT, cli, require_candidate

PAYLOAD = {"request_id": "demo-001", "text": "Email [EMAIL_ADDRESS]; customer [CUSTOMER_ID]; quantity 24."}


class RunCommand(unittest.TestCase):
    def test_default_detector_and_output_are_unchanged(self):
        rc, out, err, m = cli(["run", "--request-id", "demo-001"], TEXT)
        self.assertEqual((rc, err), (0, ""))
        self.assertEqual(json.loads(out), PAYLOAD)
        self.assertEqual(out, json.dumps(PAYLOAD) + "\n")
        self.assertEqual(m.calls, [PAYLOAD])

    def test_explicit_baseline_detector_handles_all_three_entities(self):
        rc, out, err, m = cli(["run", "--detector", "baseline", "--request-id", "demo-001"], CANARY_TEXT)
        self.assertEqual((rc, err), (0, ""))
        self.assertEqual(json.loads(out), {"request_id": "demo-001", "text": CANARY_SANITIZED})
        self.assertEqual(m.calls, [{"request_id": "demo-001", "text": CANARY_SANITIZED}])

    def test_summary_flag_adds_counts_outside_the_provider_object(self):
        rc, out, err, m = cli(["run", "--summary", "--request-id", "demo-001"], CANARY_TEXT)
        obj = json.loads(out)
        self.assertEqual(set(obj), {"payload", "entity_counts"})
        self.assertEqual(obj["payload"], {"request_id": "demo-001", "text": CANARY_SANITIZED})
        self.assertEqual(obj["entity_counts"], {"EMAIL_ADDRESS": 1, "PHONE_NUMBER": 1, "CUSTOMER_ID": 1})
        self.assertEqual(m.calls, [obj["payload"]])  # the provider still received exactly {request_id, text}
        self.assertEqual(list(m.calls[0]), ["request_id", "text"])
        for v in (CANARY_EMAIL, CANARY_PHONE, CANARY_CUSTOMER):
            self.assertNotIn(v, out)

    def test_unknown_detector_choice_is_an_argument_error(self):
        rc, out, err, m = cli(["run", "--detector", "gpt", "--request-id", "demo-001"], TEXT)
        self.assertEqual((rc, out, err, m.calls), (2, "", "SANITIZER_INVALID_ARGUMENTS\n", []))


class CandidateUnavailable(unittest.TestCase):
    """A dependency/model/config failure is a fixed code and zero dispatch. No fallback to the baseline."""

    ARGV = ["run", "--detector", "presidio", "--request-id", "demo-001"]

    def assert_unavailable(self, rc, out, err, m, logs=None):
        self.assertEqual((rc, out, err), (2, "", "SANITIZER_DETECTOR_UNAVAILABLE\n"))
        self.assertEqual(m.calls, [])  # zero dispatch, and stdout empty: no baseline or raw-text fallback
        for canary in (EMAIL, CUST, "boom"):
            self.assertNotIn(canary, out + err + (logs.text if logs else ""))

    def test_missing_package_in_process(self):
        with mock.patch.dict(sys.modules, {"sanitizer.presidio_detector": None}), LogCapture() as logs:
            self.assert_unavailable(*cli(self.ARGV, TEXT), logs=logs)

    def test_initialization_failure_message_is_never_exposed(self):
        fake = types.ModuleType("sanitizer.presidio_detector")

        def build_analyzer():
            print(f"noisy stdout {EMAIL}")
            sys.stderr.write(f"noisy stderr {CUST}\n")
            raise RuntimeError(f"boom model path leaked {EMAIL} {CUST}")

        fake.build_analyzer = build_analyzer
        with mock.patch.dict(sys.modules, {"sanitizer.presidio_detector": fake}), LogCapture() as logs:
            self.assert_unavailable(*cli(self.ARGV, TEXT), logs=logs)
        self.assertEqual(logs.lines, ["ERROR sanitizer: rejected code=SANITIZER_DETECTOR_UNAVAILABLE"])

    def test_missing_package_in_a_real_process(self):
        # Blocks the import inside a subprocess instead of relying on the environment lacking Presidio.
        prog = ("import sys\nsys.modules['presidio_analyzer'] = None\nfrom sanitizer.cli import main\n"
                "sys.stdout.reconfigure(newline='\\n'); sys.stderr.reconfigure(newline='\\n')\n"
                "sys.exit(main(['run', '--detector', 'presidio', '--request-id', 'demo-001']))\n")
        p = subprocess.run([sys.executable, "-c", prog], input=TEXT.encode(), capture_output=True, cwd=ROOT)
        self.assertEqual(p.returncode, 2)
        self.assertEqual(p.stdout, b"")
        self.assertEqual(p.stderr, b"SANITIZER_DETECTOR_UNAVAILABLE\n")

    def test_missing_invalid_or_mismatched_config_is_a_fixed_code(self):
        with tempfile.TemporaryDirectory() as d:
            cases = {"missing": os.path.join(d, "nope.json")}
            for name, content in (("not json", "{"), ("wrong version", json.dumps({"config_version": 9})),
                                  ("no thresholds", json.dumps({"config_version": 1, "detector": "presidio",
                                                                "development_sha256": "a", "heldout_sha256": "b"})),
                                  ("bad threshold", json.dumps({"config_version": 1, "detector": "presidio",
                                                                "development_sha256": "a", "heldout_sha256": "b",
                                                                "thresholds": {"EMAIL_ADDRESS": 2, "PHONE_NUMBER": 0,
                                                                               "CUSTOMER_ID": 0}}))):
                p = os.path.join(d, name.replace(" ", "_") + ".json")
                Path(p).write_text(content, encoding="utf-8")
                cases[name] = p
            for name, path in cases.items():
                with self.subTest(name):
                    rc, out, err, m = cli(self.ARGV + ["--config", path], TEXT)
                    self.assertEqual((rc, out, err, m.calls), (2, "", "SANITIZER_INVALID_CONFIG\n", []))


class EvaluationCommands(unittest.TestCase):
    def test_heldout_requires_the_frozen_config(self):
        with tempfile.TemporaryDirectory() as d:
            for det in ("baseline", "presidio"):
                with self.subTest(det):
                    rc, out, err, _ = cli(["evaluate", "--detector", det, "--split", "heldout",
                                           "--config", os.path.join(d, "missing.json"), "--out", os.path.join(d, "r.json")])
                    self.assertEqual((rc, out, err), (2, "", "SANITIZER_FROZEN_CONFIG_REQUIRED\n"))
                    self.assertFalse(os.path.exists(os.path.join(d, "r.json")))

    def test_debug_thresholds_are_development_only(self):
        rc, out, err, _ = cli(["evaluate", "--detector", "presidio", "--split", "heldout", "--debug-thresholds", "0,0,0"])
        self.assertEqual((rc, out, err), (2, "", "SANITIZER_INVALID_ARGUMENTS\n"))

    def test_select_thresholds_refuses_to_overwrite_a_freeze(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "frozen.json")
            Path(p).write_text("{}", encoding="utf-8")
            rc, out, err, _ = cli(["select-thresholds", "--out", p])
            self.assertEqual((rc, out, err), (2, "", "SANITIZER_INVALID_CONFIG\n"))
            self.assertEqual(Path(p).read_text(encoding="utf-8"), "{}")

    def test_baseline_development_report_is_deterministic_and_privacy_safe(self):
        with tempfile.TemporaryDirectory() as d:
            outs = []
            for i in range(2):
                p = os.path.join(d, f"r{i}.json")
                rc, stdout, err, _ = cli(["evaluate", "--detector", "baseline", "--split", "development", "--out", p])
                self.assertEqual((rc, err), (0, ""))
                outs.append((Path(p).read_bytes(), stdout))
        self.assertEqual(outs[0], outs[1])
        report_text = outs[0][0].decode("utf-8")
        rep = json.loads(report_text)
        self.assertEqual(rep["metrics"]["micro"]["tp"], 16)
        # no raw values, texts or sanitized outputs in the report or the console summary
        for ex in load_fixture(FIXTURE_DIR / "development.json")["examples"]:
            for g in ex["entities"]:
                self.assertNotIn(ex["text"][g["start"]:g["end"]], report_text + outs[0][1])
            if len(ex["text"]) > 12:
                self.assertNotIn(ex["text"], report_text)
            if len(ex["expected_sanitized"]) > 12:
                self.assertNotIn(ex["expected_sanitized"], report_text)
        for key in ("text", "sanitized", "value"):
            self.assertNotIn(f'"{key}"', report_text)

    def test_report_separates_accuracy_from_provider_boundary(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "r.json")
            cli(["evaluate", "--detector", "baseline", "--split", "development", "--out", p])
            rep = json.loads(Path(p).read_text(encoding="utf-8"))
        self.assertIn("metrics", rep)
        self.assertIn("provider_boundary", rep)
        self.assertEqual(rep["provider_boundary"]["examples_dispatched"], 10)
        self.assertEqual(rep["provider_boundary"]["payload_equals_actual_sanitized"], 10)
        self.assertEqual(rep["provider_boundary"]["provider_calls_total"], 10)
        self.assertEqual(rep["preservation"]["no_gold_examples_preserved"], rep["preservation"]["examples_with_no_gold"])
        self.assertTrue(all(e["reconstruction_from_applied_spans_equals_output"] for e in rep["examples"]))


class DemoCommand(unittest.TestCase):
    def test_baseline_demo_shows_labelled_synthetic_inspection(self):
        rc, out, err, m = cli(["demo", "--detector", "baseline"])
        self.assertEqual((rc, err), (0, ""))
        self.assertIn("SYNTHETIC INSPECTION", out)
        self.assertIn("no user text is accepted", out.lower())
        self.assertIn(f"payload captured by RecordingMock: {{'request_id': 'demo-001', 'text': {CANARY_SANITIZED!r}}}", out)
        for needle in ("benign preservation", "Unicode offsets", "repeated value", "CRLF and tab",
                       "detector failure", "fixed code: SANITIZER_DETECTOR_ERROR; provider calls = 0",
                       "equals fixture oracle: True"):
            self.assertIn(needle, out)
        self.assertEqual(m.calls, [])  # the demo's own mocks are internal; the injected provider is untouched

    def test_demo_has_no_way_to_supply_text_or_pick_a_real_provider(self):
        rc, out, err, _ = cli(["demo", "--text", "hello"])
        self.assertEqual((rc, out, err), (2, "", "SANITIZER_INVALID_ARGUMENTS\n"))
        rc, out, err, _ = cli(["demo", "--provider", "real"])
        self.assertEqual((rc, out, err), (2, "", "SANITIZER_INVALID_ARGUMENTS\n"))

    def test_presidio_demo_without_dependency_is_a_fixed_code(self):
        with mock.patch.dict(sys.modules, {"sanitizer.presidio_detector": None}):
            rc, out, err, _ = cli(["demo", "--detector", "presidio"])
        self.assertEqual((rc, out, err), (2, "", "SANITIZER_DETECTOR_UNAVAILABLE\n"))


class CandidateCli(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_candidate()

    def test_presidio_run_with_the_frozen_config(self):
        rc, out, err, m = cli(["run", "--detector", "presidio", "--summary", "--request-id", "demo-001"], CANARY_TEXT)
        self.assertEqual((rc, err), (0, ""))
        obj = json.loads(out)
        self.assertEqual(obj["payload"], {"request_id": "demo-001", "text": CANARY_SANITIZED})
        self.assertEqual(obj["entity_counts"], {"EMAIL_ADDRESS": 1, "PHONE_NUMBER": 1, "CUSTOMER_ID": 1})
        self.assertEqual(m.calls, [obj["payload"]])

    def test_presidio_run_prints_nothing_extra_to_the_terminal(self):
        p = subprocess.run([sys.executable, "-m", "sanitizer", "run", "--detector", "presidio", "--request-id", "demo-001"],
                           input=TEXT.encode(), capture_output=True, cwd=ROOT,
                           env=dict(os.environ, TLDEXTRACT_CACHE=tempfile.gettempdir()))
        self.assertEqual((p.returncode, p.stderr), (0, b""))
        self.assertEqual(json.loads(p.stdout), PAYLOAD)

    def test_candidate_demo_runs_and_is_labelled(self):
        rc, out, err, _ = cli(["demo", "--detector", "presidio"])
        self.assertEqual((rc, err), (0, ""))
        self.assertIn("SYNTHETIC INSPECTION", out)
        self.assertIn("detector: presidio", out)

    def test_candidate_development_evaluation_is_deterministic(self):
        with tempfile.TemporaryDirectory() as d:
            blobs = []
            for i in range(2):
                p = os.path.join(d, f"r{i}.json")
                rc, _, err, _ = cli(["evaluate", "--detector", "presidio", "--split", "development", "--out", p])
                self.assertEqual((rc, err), (0, ""))
                blobs.append(Path(p).read_bytes())
        self.assertEqual(blobs[0], blobs[1])


if __name__ == "__main__":
    unittest.main()
````

### `tests/test_detectors_boundary.py`

````python
"""Provider-boundary and logging tests for BOTH detectors.

These check what reaches the provider (a RecordingMock) and what reaches the logs. They are separate
from accuracy: a detector miss in evaluation is an accuracy/coverage failure, not proof that dispatch was
bypassed, and nothing here asserts universal PII removal.

The KNOWN_CORRECT lists below were derived from DEVELOPMENT results only."""
import unittest

from sanitizer import RecordingMock, SanitizerError
from sanitizer.config import FIXTURE_DIR
from sanitizer.core import run_pipeline
from sanitizer.detectors import load_detector
from sanitizer.evaluation import load_fixture
from sanitizer.fixture import CANARY_CUSTOMER, CANARY_EMAIL, CANARY_PHONE, CANARY_SANITIZED, CANARY_TEXT

from .support import FROZEN_CONFIG, LOG_LINE_OK, LogCapture, require_candidate

DEV = {e["id"]: e for e in load_fixture(FIXTURE_DIR / "development.json")["examples"]}
# Development examples whose actual output equals the fixture oracle, per detector (dev results only).
KNOWN_CORRECT = {
    "baseline": sorted(DEV),
    "presidio": sorted(k for k in DEV if k != "dev-008"),  # dev-008: Presidio rejects the .invalid suffix (documented miss)
}
DOCUMENTED_MISS = {"baseline": [], "presidio": ["dev-008"]}


class _Boundary:
    name = None

    @classmethod
    def setUpClass(cls):
        if cls.name == "presidio":
            require_candidate()
        cls.det = load_detector(cls.name, FROZEN_CONFIG)

    def run_one(self, text, detector=None, request_id="demo-001"):
        mock = RecordingMock()
        payload, res = run_pipeline(request_id, text, mock, detector or self.det.fn, thresholds=self.det.thresholds)
        return mock, payload, res

    def test_all_three_entity_canary_payload_is_exactly_the_sanitized_text(self):
        mock, payload, res = self.run_one(CANARY_TEXT)
        self.assertEqual(mock.calls, [{"request_id": "demo-001", "text": CANARY_SANITIZED}])
        self.assertIs(mock.calls[0], payload)
        self.assertEqual(list(mock.calls[0]), ["request_id", "text"])
        for canary in (CANARY_EMAIL, CANARY_PHONE, CANARY_CUSTOMER):
            self.assertNotIn(canary, repr(mock.calls[0]))
        self.assertEqual(res.entity_counts(), {"EMAIL_ADDRESS": 1, "PHONE_NUMBER": 1, "CUSTOMER_ID": 1})

    def test_known_correct_development_cases_have_exact_payload(self):
        for ex_id in KNOWN_CORRECT[self.name]:
            with self.subTest(ex_id):
                mock, payload, _ = self.run_one(DEV[ex_id]["text"])
                self.assertEqual(mock.calls, [{"request_id": "demo-001", "text": DEV[ex_id]["expected_sanitized"]}])

    def test_every_development_payload_equals_the_actual_sanitized_text_even_on_misses(self):
        for ex_id, ex in DEV.items():
            with self.subTest(ex_id):
                mock, payload, res = self.run_one(ex["text"])
                self.assertEqual(mock.calls, [{"request_id": "demo-001", "text": res.sanitized}])

    def test_documented_misses_are_accuracy_failures_not_boundary_failures(self):
        for ex_id in DOCUMENTED_MISS[self.name]:
            with self.subTest(ex_id):
                mock, payload, res = self.run_one(DEV[ex_id]["text"])
                self.assertNotEqual(payload["text"], DEV[ex_id]["expected_sanitized"])  # accuracy failure
                self.assertEqual(mock.calls, [payload])                               # boundary still holds

    def test_detector_failure_and_malformed_output_give_zero_provider_calls(self):
        real = self.det.fn

        def raises(text):
            real(text)
            raise RuntimeError(f"boom {CANARY_EMAIL} {CANARY_CUSTOMER} {CANARY_PHONE}")

        def malformed(text):
            return real(text) + [{"entity_type": "EMAIL_ADDRESS", "start": True, "end": 3, "score": 1.0}]

        for fn, code in ((raises, "SANITIZER_DETECTOR_ERROR"), (malformed, "SANITIZER_INVALID_DETECTOR_OUTPUT")):
            with self.subTest(code):
                mock = RecordingMock()
                with LogCapture() as logs, self.assertRaises(SanitizerError) as cm:
                    run_pipeline("demo-001", CANARY_TEXT, mock, fn, thresholds=self.det.thresholds)
                self.assertEqual(str(cm.exception), code)
                self.assertEqual(mock.calls, [])
                for canary in (CANARY_EMAIL, CANARY_PHONE, CANARY_CUSTOMER, "boom"):
                    self.assertNotIn(canary, logs.text)

    def test_provider_exception_is_distinct_from_detector_failure(self):
        calls = []

        def provider(payload):
            calls.append(payload)
            raise RuntimeError(f"provider boom {CANARY_EMAIL}")

        with LogCapture() as logs, self.assertRaises(SanitizerError) as cm:
            run_pipeline("demo-001", CANARY_TEXT, provider, self.det.fn, thresholds=self.det.thresholds)
        self.assertEqual(str(cm.exception), "SANITIZER_INTERNAL_ERROR")
        self.assertEqual(len(calls), 1)  # the provider HAD been invoked (with the sanitized payload)
        self.assertEqual(calls[0]["text"], CANARY_SANITIZED)
        self.assertNotIn(CANARY_EMAIL, logs.text)

    def test_logs_at_root_debug_contain_only_approved_metadata(self):
        with LogCapture() as logs:
            for ex in DEV.values():
                self.run_one(ex["text"])
            self.run_one(CANARY_TEXT)
        self.assertTrue(logs.lines)
        for rec in logs.handler.records:
            if rec.name == "sanitizer":
                self.assertRegex(f"{rec.levelname} {rec.name} {rec.getMessage()}", LOG_LINE_OK)
            self.assertIsNone(rec.exc_info)
        blob = logs.text
        for needle in (CANARY_EMAIL, CANARY_PHONE, CANARY_CUSTOMER, "quantity", "Café", "training.invalid",
                       "team@example.com", "maya+lab", "555-0147"):
            self.assertNotIn(needle, blob)


class BaselineBoundary(_Boundary, unittest.TestCase):
    name = "baseline"


class PresidioBoundary(_Boundary, unittest.TestCase):
    name = "presidio"


if __name__ == "__main__":
    unittest.main()
````

### `tests/test_docs.py`

````python
"""Documentation and CI-config consistency: the README numbers are generated from the reports, the
workflow keeps its guarantees, and importing the CLI does not import Presidio."""
import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

from .support import ROOT

R = Path(ROOT)
sys.path.insert(0, str(R / "scripts"))


@unittest.skipUnless((R / "reports" / "heldout_presidio.json").is_file(), "reports not generated yet")
class ReadmeMatchesReports(unittest.TestCase):
    def test_readme_summary_block_equals_the_rendered_reports(self):
        import render_summary
        readme = (R / "README.md").read_text(encoding="utf-8")
        a, b = readme.index(render_summary.BEGIN) + len(render_summary.BEGIN), readme.index(render_summary.END)
        self.assertEqual(readme[a:b].strip(), render_summary.render().strip())

    def test_summary_file_is_current(self):
        import render_summary
        self.assertEqual((R / "reports" / "SUMMARY.md").read_text(encoding="utf-8").split("\n\n", 1)[1].strip(),
                         render_summary.render().strip())

    def test_required_documents_exist(self):
        for name in ("README.md", "WALKTHROUGH.md", "requirements-presidio.txt", "config/frozen_config.json",
                     ".github/workflows/ci.yml", "docs/handoff/EVALUATION_CONTRACT.md"):
            self.assertTrue((R / name).is_file(), name)


class WorkflowKeepsItsGuarantees(unittest.TestCase):
    def setUp(self):
        self.text = (R / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    def test_structure_by_text(self):
        for needle in ("baseline:", "candidate:", 'REQUIRE_CANDIDATE_TESTS: "1"', "pip check",
                       "scripts/run_tests_no_skips.py", "requirements-presidio.txt", r"C:\pv",
                       "scripts/check_reports.py baseline presidio", "PENDING"):
            self.assertIn(needle, self.text)

    @unittest.skipUnless(importlib.util.find_spec("yaml"), "PyYAML not installed (candidate environment has it)")
    def test_structure_by_yaml(self):
        import yaml
        doc = yaml.safe_load(self.text)
        jobs = doc["jobs"]
        self.assertEqual(set(jobs), {"baseline", "candidate"})
        self.assertEqual(jobs["candidate"]["env"]["REQUIRE_CANDIDATE_TESTS"], "1")
        runs = [s.get("run", "") for s in jobs["candidate"]["steps"]]
        self.assertTrue(any("pip check" in r for r in runs))
        self.assertTrue(any("run_tests_no_skips" in r for r in runs))
        self.assertFalse(any("-m unittest" in r for r in runs))  # the candidate job must use the no-skip runner


class StdlibBaselineStaysStdlib(unittest.TestCase):
    def test_cli_and_core_do_not_import_presidio_or_spacy(self):
        prog = ("import sys\nimport sanitizer.cli, sanitizer.core, sanitizer.evaluation, sanitizer.detectors, sanitizer.demo\n"
                "bad = [m for m in sys.modules if m.split('.')[0] in ('presidio_analyzer', 'spacy', 'tldextract')]\n"
                "print(bad)\n")
        p = subprocess.run([sys.executable, "-c", prog], capture_output=True, text=True, cwd=ROOT)
        self.assertEqual((p.returncode, p.stdout.strip()), (0, "[]"), p.stderr[-400:])


if __name__ == "__main__":
    unittest.main()
````

### `tests/test_frozen_config.py`

````python
"""Frozen-config integrity. Written and run AFTER the development freeze.

Fixture-integrity checks that open heldout.json (summary counts, gold slices) are fixture validation only;
no detector output on held-out data is involved. Held-out detector results exist only in reports/."""
import json
import os
import shutil
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

from sanitizer.config import GRID, check_fixture_integrity, file_sha256, load_frozen_config
from sanitizer.core import ENTITY_PRIORITY, SanitizerError, replace_spans
from sanitizer.evaluation import collect_raw, load_fixture, pick_best, select_thresholds

from .support import FROZEN_CONFIG, ROOT, require_candidate

FIX = Path(ROOT) / "fixtures"
MANIFEST = json.loads((Path(ROOT) / "docs" / "handoff" / "MANIFEST.json").read_text(encoding="utf-8"))


@unittest.skipUnless(os.path.isfile(FROZEN_CONFIG), "no frozen_config.json (freeze not done yet)")
class FrozenConfig(unittest.TestCase):
    def setUp(self):
        self.cfg_raw = json.loads(Path(FROZEN_CONFIG).read_text(encoding="utf-8"))
        self.cfg = load_frozen_config(FROZEN_CONFIG)

    def test_records_the_required_freeze_metadata(self):
        c = self.cfg_raw
        for key in ("thresholds", "recognizer_settings", "packages", "model_wheel_sha256", "resolution_policy",
                    "selection_rule", "development_sha256", "heldout_sha256", "scope", "python", "baseline",
                    "development_metrics_at_selected_thresholds", "selection_grid"):
            self.assertIn(key, c)
        self.assertIn("procedural freeze", c["freeze_kind"])
        self.assertIn("not a blinded external evaluation", c["freeze_kind"])
        self.assertIn("raw bytes only", c["heldout_access"])
        self.assertEqual(c["selection_grid_size"], len(GRID) ** 3)
        self.assertEqual(sorted(c["thresholds"]), sorted(ENTITY_PRIORITY))
        self.assertTrue(all(v in GRID for v in c["thresholds"].values()))
        for pkg in ("presidio-analyzer", "spacy", "en-core-web-sm", "phonenumbers", "tldextract", "regex"):
            self.assertTrue(c["packages"][pkg])

    def test_hashes_match_the_handoff_fixtures_and_files_on_disk(self):
        self.assertEqual(self.cfg["development_sha256"], MANIFEST["development.json"])
        self.assertEqual(self.cfg["heldout_sha256"], MANIFEST["heldout.json"])
        check_fixture_integrity(self.cfg)  # raises on mismatch with fixtures/ on disk

    def test_model_hash_matches_the_requirements_pin(self):
        req = (Path(ROOT) / "requirements-presidio.txt").read_text(encoding="utf-8")
        self.assertIn("sha256=" + self.cfg_raw["model_wheel_sha256"], req)

    def test_selected_thresholds_follow_the_selection_rule_over_the_stored_grid(self):
        grid = []
        for r in self.cfg_raw["selection_grid"]:
            r = dict(r)
            r["_f1"] = Fraction(2 * r["tp"], 2 * r["tp"] + r["fp"] + r["fn"]) if 2 * r["tp"] + r["fp"] + r["fn"] else Fraction(0)
            grid.append(r)
        self.assertEqual(len(grid), 125)
        self.assertEqual(len({tuple(sorted(r["thresholds"].items())) for r in grid}), 125)
        best = pick_best(grid)
        self.assertEqual(best["thresholds"], self.cfg["thresholds"])
        m = self.cfg_raw["development_metrics_at_selected_thresholds"]["micro"]
        self.assertEqual((best["tp"], best["fp"], best["fn"]), (m["tp"], m["fp"], m["fn"]))

    def test_mismatched_or_missing_fixture_bytes_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            for name in ("development.json", "heldout.json"):
                shutil.copy(FIX / name, Path(d) / name)
            check_fixture_integrity(self.cfg, d)
            (Path(d) / "heldout.json").write_bytes((FIX / "heldout.json").read_bytes() + b" ")
            with self.assertRaises(SanitizerError) as cm:
                check_fixture_integrity(self.cfg, d)
            self.assertEqual(str(cm.exception), "SANITIZER_INVALID_CONFIG")
            shutil.copy(FIX / "heldout.json", Path(d) / "heldout.json")
            (Path(d) / "development.json").unlink()
            with self.assertRaises(SanitizerError):
                check_fixture_integrity(self.cfg, d)


@unittest.skipUnless(os.path.isfile(FROZEN_CONFIG), "freeze not done yet")
class FixtureIntegrityAfterFreeze(unittest.TestCase):
    def test_heldout_fixture_matches_summary_and_is_self_consistent(self):
        summary = json.loads((FIX / "fixture_summary.json").read_text(encoding="utf-8"))["heldout"]
        fx = load_fixture(FIX / "heldout.json")
        self.assertEqual(len(fx["examples"]), summary["examples"])
        counts = {t: 0 for t in ENTITY_PRIORITY}
        for ex in fx["examples"]:
            for g in ex["entities"]:
                counts[g["entity_type"]] += 1
            applied = [dict(g, score=1.0) for g in ex["entities"]]
            self.assertEqual(replace_spans(ex["text"], applied), ex["expected_sanitized"], ex["id"])
        self.assertEqual(counts, summary["gold_entities"])
        dev_ids = {e["id"] for e in load_fixture(FIX / "development.json")["examples"]}
        self.assertFalse(dev_ids & {e["id"] for e in fx["examples"]})
        self.assertTrue(any(not e["entities"] for e in fx["examples"]))  # includes benign-only/empty examples


@unittest.skipUnless(os.path.isfile(FROZEN_CONFIG), "freeze not done yet")
class SelectionReproducible(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_candidate()

    def test_rerunning_the_development_selection_reproduces_the_frozen_thresholds(self):
        from sanitizer.detectors import build_presidio
        fn, _mod, _an = build_presidio()
        dev = load_fixture(FIX / "development.json")
        sel = select_thresholds(dev, collect_raw(dev, fn))
        self.assertEqual(sel["best"]["thresholds"], load_frozen_config(FROZEN_CONFIG)["thresholds"])
        self.assertEqual(sel["grid"], json.loads(Path(FROZEN_CONFIG).read_text(encoding="utf-8"))["selection_grid"])


if __name__ == "__main__":
    unittest.main()
````

### `tests/test_pipeline.py`

````python
"""Shared-pipeline tests: phone baseline and scope gate, validate-before-filter, thresholds,
dedupe, and every type-priority tie. Stdlib only; no held-out data."""
import unittest

from sanitizer import RecordingMock, SanitizerError, baseline_detector, dispatch, sanitize
from sanitizer.core import ENTITY_PRIORITY, PHONE_SCOPE_RE, process, resolve_spans, run_pipeline

PHONE = "(415) 555-0132"


def sp(t, a, b, score=1.0):
    return {"entity_type": t, "start": a, "end": b, "score": score}


def fixed(*spans):
    return lambda _t: list(spans)


class PhoneBaseline(unittest.TestCase):
    def test_exact_format_detected(self):
        t = f"Call {PHONE}, ok"
        self.assertEqual([(s["entity_type"], s["start"], s["end"]) for s in baseline_detector(t)],
                         [("PHONE_NUMBER", 5, 19)])
        self.assertEqual(sanitize(t), "Call [PHONE_NUMBER], ok")

    def test_out_of_scope_formats_are_not_detected(self):
        for t in ("(115) 555-0132",      # area code starts with 1
                  "(415) 155-0132",      # exchange starts with 1
                  "415-555-0132", "(415)555-0132", "(415)  555-0132", "(415) 555-0132",
                  "x(415) 555-0132", "(415) 555-01323", "(415) 555-0132_", "A(415) 555-0132",
                  "(415) 555-013", "( 415) 555-0132", "(٤١٥) 555-0132"):
            with self.subTest(t=t):
                self.assertEqual([s for s in baseline_detector(t) if s["entity_type"] == "PHONE_NUMBER"], [])
                self.assertEqual(sanitize(t), t)

    def test_digit_ranges(self):
        self.assertIsNotNone(PHONE_SCOPE_RE.search("(200) 200-0000"))
        self.assertIsNotNone(PHONE_SCOPE_RE.search("(999) 999-9999"))
        self.assertIsNone(PHONE_SCOPE_RE.search("(100) 200-0000"))
        self.assertIsNone(PHONE_SCOPE_RE.search("(200) 100-0000"))

    def test_boundaries_allow_punctuation_and_whitespace(self):
        self.assertEqual(sanitize(f"({PHONE}),\n{PHONE}!"), "([PHONE_NUMBER]),\n[PHONE_NUMBER]!")


class ScopeGate(unittest.TestCase):
    TEXT = f"Call {PHONE} now"  # PHONE occupies [5,19)

    def test_exact_match_is_kept(self):
        self.assertEqual(sanitize(self.TEXT, fixed(sp("PHONE_NUMBER", 5, 19))), "Call [PHONE_NUMBER] now")

    def test_trimmed_expanded_and_shifted_candidates_are_dropped_not_repaired(self):
        for a, b in ((5, 18), (6, 19), (4, 19), (5, 20), (0, 19), (7, 12)):
            with self.subTest(span=(a, b)):
                res = process(self.TEXT, fixed(sp("PHONE_NUMBER", a, b)))
                self.assertEqual(res.sanitized, self.TEXT)
                self.assertEqual(res.applied, [])
                self.assertEqual(res.dropped_by_scope, 1)

    def test_gate_does_not_insert_missing_detections(self):
        res = process(self.TEXT, fixed())  # a detector that finds nothing: the gate must not "repair" that
        self.assertEqual((res.sanitized, res.applied), (self.TEXT, []))

    def test_unsupported_format_phone_candidate_is_dropped(self):
        text = "Unsupported phone 202-555-0147 here"
        self.assertEqual(sanitize(text, fixed(sp("PHONE_NUMBER", 18, 30))), text)

    def test_gate_applies_only_to_phone_candidates(self):
        res = process("hello", fixed(sp("EMAIL_ADDRESS", 0, 5)))
        self.assertEqual(res.sanitized, "[EMAIL_ADDRESS]")

    def test_all_spans_are_validated_before_the_gate_or_thresholds(self):
        # The out-of-scope phone span would be silently dropped, but it is malformed (bool offset):
        # the whole output must abort, and the provider must not be called.
        for bad in (sp("PHONE_NUMBER", True, 19), sp("PHONE_NUMBER", 5, 19, 1.5), sp("PHONE_NUMBER", 5, 19, float("nan")),
                    sp("PHONE_NUMBER", 5, 999), sp("PHONE_NUMBER", 5, 19, 10 ** 400)):
            with self.subTest(bad=bad):
                mock = RecordingMock()
                with self.assertRaises(SanitizerError) as cm:
                    dispatch("demo-001", self.TEXT, mock, fixed(sp("EMAIL_ADDRESS", 0, 4), bad),
                             thresholds={t: 1.0 for t in ENTITY_PRIORITY})
                self.assertEqual(str(cm.exception), "SANITIZER_INVALID_DETECTOR_OUTPUT")
                self.assertEqual(mock.calls, [])


class Thresholds(unittest.TestCase):
    def test_score_equal_to_threshold_passes_and_below_fails(self):
        for score, expect in ((0.6, True), (0.5999, False), (1.0, True)):
            with self.subTest(score=score):
                res = process("abcdef", fixed(sp("EMAIL_ADDRESS", 0, 6, score)), thresholds={"EMAIL_ADDRESS": 0.6})
                self.assertEqual(bool(res.applied), expect)
                self.assertEqual(res.dropped_by_threshold, 0 if expect else 1)

    def test_thresholds_are_per_type(self):
        res = process("abc def", fixed(sp("EMAIL_ADDRESS", 0, 3, 0.5), sp("CUSTOMER_ID", 4, 7, 0.5)),
                      thresholds={"EMAIL_ADDRESS": 0.4, "CUSTOMER_ID": 0.6})
        self.assertEqual([s["entity_type"] for s in res.applied], ["EMAIL_ADDRESS"])

    def test_no_thresholds_accepts_every_valid_score(self):
        self.assertEqual(sanitize("abc", fixed(sp("EMAIL_ADDRESS", 0, 3, 0.0))), "[EMAIL_ADDRESS]")

    def test_dedupe_keeps_highest_score_for_same_type_and_range(self):
        res = process("abcdef", fixed(sp("EMAIL_ADDRESS", 0, 6, 0.7), sp("EMAIL_ADDRESS", 0, 6, 0.95),
                                      sp("EMAIL_ADDRESS", 0, 6, 0.8)))
        self.assertEqual([(s["start"], s["end"], s["score"]) for s in res.applied], [(0, 6, 0.95)])


class TypePriorityTies(unittest.TestCase):
    """Same length and same score: EMAIL_ADDRESS > PHONE_NUMBER > CUSTOMER_ID, then earlier start."""

    def winner(self, *spans):
        return [(s["entity_type"], s["start"], s["end"]) for s in resolve_spans(spans)]

    def test_all_pairwise_ties_same_range(self):
        E, P, C = "EMAIL_ADDRESS", "PHONE_NUMBER", "CUSTOMER_ID"
        self.assertEqual(self.winner(sp(P, 0, 5), sp(E, 0, 5)), [(E, 0, 5)])
        self.assertEqual(self.winner(sp(C, 0, 5), sp(E, 0, 5)), [(E, 0, 5)])
        self.assertEqual(self.winner(sp(C, 0, 5), sp(P, 0, 5)), [(P, 0, 5)])
        self.assertEqual(self.winner(sp(C, 0, 5), sp(P, 0, 5), sp(E, 0, 5)), [(E, 0, 5)])

    def test_ties_with_offset_overlap_use_type_before_start(self):
        E, P, C = "EMAIL_ADDRESS", "PHONE_NUMBER", "CUSTOMER_ID"
        self.assertEqual(self.winner(sp(P, 0, 5), sp(E, 2, 7)), [(E, 2, 7)])   # type beats earlier start
        self.assertEqual(self.winner(sp(C, 0, 5), sp(P, 2, 7)), [(P, 2, 7)])
        self.assertEqual(self.winner(sp(E, 3, 8), sp(E, 1, 6)), [(E, 1, 6)])   # same type: earlier start

    def test_length_then_score_precede_type(self):
        E, P, C = "EMAIL_ADDRESS", "PHONE_NUMBER", "CUSTOMER_ID"
        self.assertEqual(self.winner(sp(E, 0, 5, 1.0), sp(C, 0, 7, 0.1)), [(C, 0, 7)])
        self.assertEqual(self.winner(sp(E, 0, 5, 0.5), sp(P, 0, 5, 0.9)), [(P, 0, 5)])

    def test_adjacent_nonoverlapping_spans_are_both_kept(self):
        E, C = "EMAIL_ADDRESS", "CUSTOMER_ID"
        self.assertEqual(self.winner(sp(E, 0, 3), sp(C, 3, 6)), [(E, 0, 3), (C, 3, 6)])

    def test_customer_id_inside_an_email_loses_to_the_whole_email(self):
        text = "Owner CUST-100005@example.com;"
        self.assertEqual(sanitize(text), "Owner [EMAIL_ADDRESS];")


class SharedPipeline(unittest.TestCase):
    def test_sanitize_dispatch_and_run_pipeline_agree(self):
        text = f"Email ava@example.com; phone {PHONE}; customer CUST-004271."
        mock = RecordingMock()
        payload, res = run_pipeline("demo-001", text, mock, baseline_detector)
        self.assertEqual(payload["text"], res.sanitized)
        self.assertEqual(res.sanitized, sanitize(text))
        self.assertEqual(dispatch("demo-001", text, RecordingMock()), payload)
        self.assertEqual(replace_applied(text, res), res.sanitized)
        self.assertEqual(res.entity_counts(), {"EMAIL_ADDRESS": 1, "PHONE_NUMBER": 1, "CUSTOMER_ID": 1})
        self.assertEqual(mock.calls, [{"request_id": "demo-001", "text": res.sanitized}])


def replace_applied(text, res):
    from sanitizer.core import replace_spans
    return replace_spans(text, res.applied)


if __name__ == "__main__":
    unittest.main()
````

### `tests/test_presidio_optional.py`

````python
"""Candidate (Presidio) configuration tests. They need presidio-analyzer and en_core_web_sm.

Without them these tests SKIP locally; with REQUIRE_CANDIDATE_TESTS=1 (the CI candidate job) a missing
dependency is a FAILURE. Passing results here are not accuracy claims."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from sanitizer import RecordingMock, dispatch, sanitize
from sanitizer.config import load_frozen_config
from sanitizer.core import ENTITY_PRIORITY
from sanitizer.fixture import CANARY_CUSTOMER, CANARY_EMAIL, DEV_001

from .support import FROZEN_CONFIG, HAVE_PRESIDIO, LogCapture, ROOT, cli, require_candidate

TEXT = DEV_001["text"]
SANITIZED = "Email [EMAIL_ADDRESS]; customer [CUSTOMER_ID]; quantity 24."
PAYLOAD = {"request_id": "demo-001", "text": SANITIZED}

if HAVE_PRESIDIO:
    from sanitizer.presidio_detector import build_analyzer, make_detector, recognizer_settings


class PresidioConfiguration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_candidate()
        cls.analyzer = build_analyzer()
        cls.detector = staticmethod(make_detector(cls.analyzer))
        cls.thresholds = load_frozen_config(FROZEN_CONFIG)["thresholds"]

    def test_only_selected_recognizers_loaded(self):
        loaded = {(r.name, type(r).__name__, tuple(r.supported_entities)) for r in self.analyzer.registry.recognizers}
        self.assertEqual(loaded, {
            ("OfflineEmailRecognizer", "OfflineEmailRecognizer", ("EMAIL_ADDRESS",)),
            ("PhoneRecognizer", "PhoneRecognizer", ("PHONE_NUMBER",)),
            ("CustomerIdRecognizer", "PatternRecognizer", ("CUSTOMER_ID",)),
        })
        self.assertEqual(sorted(self.analyzer.get_supported_entities("en")), sorted(ENTITY_PRIORITY))

    def test_phone_recognizer_is_us_only_and_no_ner_recognizer_registered(self):
        settings = recognizer_settings(self.analyzer)
        phone = [r for r in settings["recognizers"] if r["class"] == "PhoneRecognizer"][0]
        self.assertEqual(phone["supported_regions"], ["US"])
        self.assertFalse(settings["ner_recognizer_registered"])
        self.assertEqual(settings["spacy_model"], "en_core_web_sm")
        self.assertEqual(settings["nlp_engine"], "SpacyNlpEngine")

    def test_frozen_config_records_the_live_recognizer_settings(self):
        cfg = json.loads(Path(FROZEN_CONFIG).read_text(encoding="utf-8"))
        self.assertEqual(cfg["recognizer_settings"], json.loads(json.dumps(recognizer_settings(self.analyzer))))

    def test_engine_candidates_for_dev_001(self):
        got = sorted((s["entity_type"], s["start"], s["end"]) for s in self.detector(TEXT))
        want = sorted((e["entity_type"], e["start"], e["end"]) for e in DEV_001["entities"])
        self.assertEqual(got, want)

    def test_sanitized_text_and_payload_exact(self):
        self.assertEqual(sanitize(TEXT, self.detector, thresholds=self.thresholds), SANITIZED)
        mock = RecordingMock()
        dispatch("demo-001", TEXT, mock, self.detector, thresholds=self.thresholds)
        self.assertEqual(mock.calls, [PAYLOAD])
        self.assertEqual(list(mock.calls[0]), ["request_id", "text"])
        for canary in (CANARY_EMAIL, CANARY_CUSTOMER):
            self.assertNotIn(canary, repr(mock.calls[0]))

    def test_customer_id_rule_is_case_sensitive_with_token_boundaries(self):
        for t in ("cust-004271", "Cust-004271", "CUST-00427", "CUST-0042711", "xCUST-004271", "CUST-004271_x"):
            with self.subTest(t=t):
                self.assertEqual([s for s in self.detector(t) if s["entity_type"] == "CUSTOMER_ID"], [])
        self.assertEqual([(s["start"], s["end"]) for s in self.detector("(CUST-004271),")
                          if s["entity_type"] == "CUSTOMER_ID"], [(1, 12)])

    def test_unsupported_phone_format_is_gated_out_of_the_applied_spans(self):
        text = "Unsupported phone 202-555-0147 here"
        raw = self.detector(text)
        self.assertTrue(any(s["entity_type"] == "PHONE_NUMBER" for s in raw))  # Presidio does see it
        self.assertEqual(sanitize(text, self.detector, thresholds=self.thresholds), text)  # the shared gate drops it

    def test_no_network_and_no_cache_writes_in_a_fresh_process(self):
        # Fresh process: tldextract memoizes after first use, so in-process checks are order-dependent.
        # TLDEXTRACT_CACHE points at a temp dir so even a regression cannot write to the user's home.
        prog = """
import json, socket
attempts = []
def gai(h, *a, **k):
    attempts.append(str(h))
    raise OSError('blocked')
def conn(self, addr):
    attempts.append(str(addr))
    raise OSError('blocked')
socket.getaddrinfo = gai
socket.socket.connect = conn
from sanitizer.presidio_detector import build_analyzer, make_detector
d = make_detector(build_analyzer())
d('Email ava@example.com; customer CUST-004271; quantity 24.')
d('contact bob@example.org')
print(json.dumps(attempts))
"""
        with tempfile.TemporaryDirectory() as cache:
            env = dict(os.environ, TLDEXTRACT_CACHE=cache)
            p = subprocess.run([sys.executable, "-c", prog], capture_output=True, text=True, cwd=ROOT, env=env)
            written = [f for _, _, fs in os.walk(cache) for f in fs]
        self.assertEqual(p.returncode, 0, p.stderr[-800:])
        self.assertEqual(json.loads(p.stdout.strip().splitlines()[-1]), [])
        self.assertEqual(written, [])

    def test_no_input_text_in_logs_at_root_debug(self):
        with LogCapture() as logs:
            det = make_detector(build_analyzer())  # build_analyzer sets presidio-analyzer to INFO
            dispatch("demo-001", TEXT, RecordingMock(), det, thresholds=self.thresholds)
        self.assertTrue(logs.lines)
        for needle in (CANARY_EMAIL, CANARY_CUSTOMER, "quantity", "customer "):
            self.assertNotIn(needle, logs.text)

    def test_stock_email_probe_is_not_a_cli_route(self):
        rc, out, err, _ = cli(["run", "--request-id", "demo-001", "--detector", "presidio", "--stock-email"], TEXT)
        self.assertEqual((rc, out, err), (2, "", "SANITIZER_INVALID_ARGUMENTS\n"))
        src = (Path(ROOT) / "sanitizer" / "cli.py").read_text(encoding="utf-8")
        self.assertNotIn("stock", src.lower())


if __name__ == "__main__":
    unittest.main()
````

### `tests/test_sanitizer.py`

````python
import io
import json
import logging
import os
import re
import subprocess
import sys
import unittest
from unittest import mock

from sanitizer import MAX_INPUT_CHARS, RecordingMock, SanitizerError, baseline_detector, dispatch, sanitize
from sanitizer.cli import main
from sanitizer.core import MAX_INPUT_BYTES, resolve_spans
from sanitizer.fixture import DEV_001

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMAIL = "ava@example.com"
CUST = "CUST-004271"
TEXT = "Email ava@example.com; customer CUST-004271; quantity 24."
SANITIZED = "Email [EMAIL_ADDRESS]; customer [CUSTOMER_ID]; quantity 24."
PAYLOAD = {"request_id": "demo-001", "text": SANITIZED}


def span(t, a, b, score=1.0):
    return {"entity_type": t, "start": a, "end": b, "score": score}


def leaky_detector(text):
    raise RuntimeError(f"boom {EMAIL} {CUST} {text}")


class _ListHandler(logging.Handler):
    def __init__(self):
        super().__init__(logging.DEBUG)
        self.records = []

    def emit(self, record):
        self.records.append(record)


class LogCapture:
    """Handler on the ROOT logger at DEBUG: sees every record the app emits."""

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
        return [f"{r.levelname} {r.name} {r.getMessage()}" for r in self.handler.records]

    @property
    def text(self):
        return "\n".join(self.lines)


# Approved log content: output length on success, or a fixed code. Never request_id or text.
LOG_LINE_OK = re.compile(
    r"(INFO|WARNING|ERROR) sanitizer "
    r"(dispatched chars=[0-9]+|rejected code=SANITIZER_[A-Z_]+)"
)


def run_cli(argv, data, detector=baseline_detector, provider=None):
    """data: bytes, or str (UTF-8 encoded). stdin is a binary stream, as in the real CLI."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    out, err = io.StringIO(), io.StringIO()
    provider = provider if provider is not None else RecordingMock()
    rc = main(argv, io.BytesIO(data), out, err, detector, provider)
    return rc, out.getvalue(), err.getvalue(), provider


class FailingProvider:
    """Provider whose exception message contains both canaries; counts invocations."""

    def __init__(self):
        self.calls = 0

    def __call__(self, payload):
        self.calls += 1
        raise RuntimeError(f"provider boom {EMAIL} {CUST}")


class Dev001(unittest.TestCase):
    def test_fixture_matches_contract_and_slices(self):
        self.assertEqual(DEV_001["text"], TEXT)
        self.assertEqual(TEXT[6:21], EMAIL)
        self.assertEqual(TEXT[32:43], CUST)

    def test_detected_spans_match_expected(self):
        got = sorted((s["entity_type"], s["start"], s["end"]) for s in baseline_detector(TEXT))
        want = sorted((e["entity_type"], e["start"], e["end"]) for e in DEV_001["entities"])
        self.assertEqual(got, want)
        self.assertTrue(all(s["score"] == 1.0 for s in baseline_detector(TEXT)))

    def test_sanitized_text_exact(self):
        self.assertEqual(sanitize(TEXT), SANITIZED)

    def test_mock_payload_exact(self):
        mock = RecordingMock()
        dispatch("demo-001", TEXT, mock)
        self.assertEqual(len(mock.calls), 1)
        self.assertIs(type(mock.calls[0]), dict)
        self.assertEqual(mock.calls[0], PAYLOAD)
        self.assertEqual(list(mock.calls[0]), ["request_id", "text"])
        blob = json.dumps(mock.calls[0])
        self.assertNotIn(EMAIL, blob)
        self.assertNotIn(CUST, blob)


class Preservation(unittest.TestCase):
    def test_benign_numbers_and_punctuation_untouched(self):
        for t in ("quantity 24.", "Total: 24, ok; (24) -- 24!", "CUST-12345 and 1234567", "a@b", "24"):
            with self.subTest(t=t):
                self.assertEqual(sanitize(t), t)

    def test_surrounding_punctuation_and_whitespace_preserved(self):
        self.assertEqual(sanitize("(CUST-004271),  x\n\tava@example.com."),
                         "([CUSTOMER_ID]),  x\n\t[EMAIL_ADDRESS].")

    def test_customer_id_boundaries(self):
        for t in ("xCUST-004271", "CUST-0042711", "CUST-00427", "cust-004271",
                  "CUST_004271", "_CUST-004271", "CUST-004271_x", "ACUST-004271", "CUST-00427١"):
            with self.subTest(t=t):
                self.assertEqual(sanitize(t), t)
        self.assertEqual(sanitize("CUST-004271-x"), "[CUSTOMER_ID]-x")

    def test_no_unicode_normalization_and_char_offsets(self):
        t = "\U0001F600 ava@example.com"  # non-BMP char counts as one index
        self.assertEqual(baseline_detector(t)[0]["start"], 2)
        self.assertEqual(sanitize(t), "\U0001F600 [EMAIL_ADDRESS]")
        self.assertEqual(sanitize("é CUST-004271"), "é [CUSTOMER_ID]")


class EmptyInput(unittest.TestCase):
    def test_empty_is_valid(self):
        self.assertEqual(sanitize(""), "")
        mock = RecordingMock()
        dispatch("req-001", "", mock)
        self.assertEqual(mock.calls, [{"request_id": "req-001", "text": ""}])

    def test_empty_via_cli(self):
        rc, out, err, mock = run_cli(["run", "--request-id", "req-001"], "")
        self.assertEqual((rc, err), (0, ""))
        self.assertEqual(json.loads(out), {"request_id": "req-001", "text": ""})
        self.assertEqual(len(mock.calls), 1)


class DetectorFailure(unittest.TestCase):
    def test_exception_stops_dispatch_without_leaking(self):
        mock = RecordingMock()
        with self.assertRaises(SanitizerError) as cm:
            dispatch("demo-001", TEXT, mock, leaky_detector)
        self.assertEqual(str(cm.exception), "SANITIZER_DETECTOR_ERROR")
        self.assertIsNone(cm.exception.__cause__)
        self.assertTrue(cm.exception.__suppress_context__)
        self.assertEqual(mock.calls, [])

    def test_cli_contract(self):
        with LogCapture() as logs:
            rc, out, err, mock = run_cli(["run", "--request-id", "demo-001"], TEXT, leaky_detector)
        self.assertEqual(rc, 2)
        self.assertEqual(out, "")
        self.assertEqual(err, "SANITIZER_DETECTOR_ERROR\n")
        self.assertEqual(mock.calls, [])
        for canary in (EMAIL, CUST):
            for stream in (out, err, logs.text):
                self.assertNotIn(canary, stream)
        self.assertNotIn("Traceback", err + logs.text)
        self.assertNotIn("boom", err + logs.text)


class InvalidDetectorOutput(unittest.TestCase):
    BAD = {
        "bool start": [span("EMAIL_ADDRESS", True, 5)],
        "bool end": [span("EMAIL_ADDRESS", 0, True)],
        "float start": [span("EMAIL_ADDRESS", 0.0, 5)],
        "str start": [span("EMAIL_ADDRESS", "0", 5)],
        "negative start": [span("EMAIL_ADDRESS", -1, 5)],
        "start == end": [span("EMAIL_ADDRESS", 3, 3)],
        "start > end": [span("EMAIL_ADDRESS", 5, 3)],
        "end > len": [span("EMAIL_ADDRESS", 0, len(TEXT) + 1)],
        "unknown entity": [span("PERSON", 0, 5)],
        "non-str entity": [span(["EMAIL_ADDRESS"], 0, 5)],
        "bool score": [span("EMAIL_ADDRESS", 0, 5, True)],
        "NaN score": [span("EMAIL_ADDRESS", 0, 5, float("nan"))],
        "inf score": [span("EMAIL_ADDRESS", 0, 5, float("inf"))],
        "score > 1": [span("EMAIL_ADDRESS", 0, 5, 1.5)],
        "score < 0": [span("EMAIL_ADDRESS", 0, 5, -0.1)],
        "str score": [span("EMAIL_ADDRESS", 0, 5, "1.0")],
        "huge positive int score": [span("EMAIL_ADDRESS", 0, 5, 10**400)],
        "huge negative int score": [span("EMAIL_ADDRESS", 0, 5, -(10**400))],
        "int score 2": [span("EMAIL_ADDRESS", 0, 5, 2)],
        "int score -1": [span("EMAIL_ADDRESS", 0, 5, -1)],
        "huge int offsets": [span("EMAIL_ADDRESS", 0, 10**400)],
        "missing key": [{"entity_type": "EMAIL_ADDRESS", "start": 0, "end": 5}],
        "extra key": [dict(span("EMAIL_ADDRESS", 0, 5), text=EMAIL)],
        "non-mapping item": [("EMAIL_ADDRESS", 0, 5, 1.0)],
        "None result": None,
        "string result": "EMAIL_ADDRESS",
        "dict result": span("EMAIL_ADDRESS", 0, 5),
        "one bad among good": [span("EMAIL_ADDRESS", 6, 21), span("CUSTOMER_ID", 32, 99)],
    }

    def test_each_malformed_output_stops_dispatch(self):
        for name, bad in self.BAD.items():
            with self.subTest(name):
                mock = RecordingMock()
                with self.assertRaises(SanitizerError) as cm:
                    dispatch("demo-001", TEXT, mock, lambda t, b=bad: b)
                self.assertEqual(str(cm.exception), "SANITIZER_INVALID_DETECTOR_OUTPUT")
                self.assertEqual(mock.calls, [])

    def test_cli_contract(self):
        bad = self.BAD["extra key"]  # extra key carries a canary
        with LogCapture() as logs:
            rc, out, err, mock = run_cli(["run", "--request-id", "demo-001"], TEXT, lambda t: bad)
        self.assertEqual((rc, out, err), (2, "", "SANITIZER_INVALID_DETECTOR_OUTPUT\n"))
        self.assertEqual(mock.calls, [])
        for canary in (EMAIL, CUST):
            self.assertNotIn(canary, logs.text)

    def test_huge_integer_scores_via_cli_not_internal_error(self):
        for name in ("huge positive int score", "huge negative int score", "huge int offsets"):
            with self.subTest(name):
                bad = self.BAD[name]
                with LogCapture() as logs:
                    rc, out, err, mock = run_cli(["run", "--request-id", "demo-001"], TEXT, lambda t, b=bad: b)
                self.assertEqual((rc, out, err), (2, "", "SANITIZER_INVALID_DETECTOR_OUTPUT\n"))
                self.assertEqual(mock.calls, [])
                self.assertEqual(logs.lines, ["ERROR sanitizer rejected code=SANITIZER_INVALID_DETECTOR_OUTPUT"])

    def test_validator_itself_rejects_huge_ints_without_overflow(self):
        # sanitize() has a defensive catch-all; this pins the validator's own behavior.
        from sanitizer.core import _is_score, validate_spans
        for score in (10**400, -(10**400), 2, -1, True, False, float("nan"), "1"):
            with self.subTest(score=score):
                self.assertIs(_is_score(score), False)
                with self.assertRaises(SanitizerError):
                    validate_spans([span("EMAIL_ADDRESS", 0, 5, score)], 20)

    def test_boundary_scores_still_accepted(self):
        for score in (0, 1, 0.0, 1.0, 0.5):
            with self.subTest(score=score):
                self.assertEqual(sanitize("abc", lambda t, s=score: [span("EMAIL_ADDRESS", 0, 3, s)]),
                                 "[EMAIL_ADDRESS]")

    def test_hostile_span_object_is_invalid_output_not_crash(self):
        class Hostile(dict):
            def keys(self):
                raise RuntimeError(f"boom {EMAIL}")
            def __iter__(self):
                raise RuntimeError(f"boom {CUST}")
        with self.assertRaises(SanitizerError) as cm:
            sanitize(TEXT, lambda t: [Hostile(span("EMAIL_ADDRESS", 0, 5))])
        self.assertEqual(str(cm.exception), "SANITIZER_INVALID_DETECTOR_OUTPUT")


class RequestIdBoundary(unittest.TestCase):
    GOOD = ("demo-001", "req-001", "demo-123", "req-123456789012", "demo-000000000000")
    BAD = {
        "email canary": EMAIL,
        "customer canary": CUST,
        "trailing newline": "demo-001\n",
        "embedded newline": "demo-001\nERROR sanitizer rejected code=FAKE",
        "leading newline": "\ndemo-001",
        "empty": "",
        "too few digits": "demo-01",
        "too many digits": "demo-1234567890123",
        "wrong prefix": "id-001",
        "uppercase prefix": "DEMO-001",
        "no hyphen": "demo001",
        "space": "demo- 001",
        "non-ASCII digits": "demo-١٢٣",
        "suffix": "demo-001x",
        "prefix text": "xdemo-001",
        "nul byte": "demo-001\x00",
        "None": None,
        "int": 1,
        "bytes": b"demo-001",
        "bool": True,
        "list": ["demo-001"],
    }

    def test_valid_ids_accepted_and_passed_through(self):
        for rid in self.GOOD:
            with self.subTest(rid):
                m = RecordingMock()
                dispatch(rid, TEXT, m)
                self.assertEqual(m.calls, [{"request_id": rid, "text": SANITIZED}])

    def test_str_subclass_rejected(self):
        class S(str):
            pass
        with self.assertRaises(SanitizerError):
            dispatch(S("demo-001"), TEXT, RecordingMock())

    def test_invalid_ids_rejected_before_detector_and_provider(self):
        for name, rid in self.BAD.items():
            with self.subTest(name):
                seen, m = [], RecordingMock()
                with LogCapture() as logs:
                    with self.assertRaises(SanitizerError) as cm:
                        dispatch(rid, TEXT, m, lambda t: seen.append(t) or [])
                self.assertEqual(str(cm.exception), "SANITIZER_INVALID_REQUEST_ID")
                self.assertIsNone(cm.exception.__cause__)
                self.assertEqual(seen, [])
                self.assertEqual(m.calls, [])
                self.assertEqual(logs.lines, ["ERROR sanitizer rejected code=SANITIZER_INVALID_REQUEST_ID"])

    def test_cli_in_process(self):
        for name, rid in self.BAD.items():
            if not isinstance(rid, str) or "\x00" in rid:
                continue  # argv cannot carry non-str or NUL
            with self.subTest(name):
                with LogCapture() as logs:
                    rc, out, err, m = run_cli(["run", "--request-id", rid], TEXT)
                self.assertEqual((rc, out, err), (2, "", "SANITIZER_INVALID_REQUEST_ID\n"))
                self.assertEqual(m.calls, [])
                for canary in (EMAIL, CUST, "FAKE"):
                    self.assertNotIn(canary, logs.text + out + err)

    def test_cli_real_process(self):
        for rid in (EMAIL, CUST, "demo-001\nERROR forged", "demo-001\n"):
            with self.subTest(repr(rid)):
                p = subprocess.run([sys.executable, "-m", "sanitizer", "run", "--request-id", rid],
                                   input=TEXT.encode(), capture_output=True, cwd=ROOT)
                self.assertEqual(p.returncode, 2)
                self.assertEqual(p.stdout, b"")
                self.assertEqual(p.stderr, b"SANITIZER_INVALID_REQUEST_ID\n")

    def test_request_id_checked_before_stdin_is_decoded(self):
        rc, out, err, _ = run_cli(["run", "--request-id", EMAIL], b"\xff")
        self.assertEqual(err, "SANITIZER_INVALID_REQUEST_ID\n")

    def test_canary_ids_never_reach_provider_or_logs(self):
        for rid in (EMAIL, CUST):
            m = RecordingMock()
            with LogCapture() as logs, self.assertRaises(SanitizerError):
                dispatch(rid, TEXT, m)
            self.assertEqual(m.calls, [])
            self.assertNotIn(rid, logs.text)


class ArgumentErrors(unittest.TestCase):
    PREFIX = [sys.executable, "-m", "sanitizer"]

    def proc(self, args, data=b""):
        return subprocess.run(self.PREFIX + args, input=data, capture_output=True, cwd=ROOT)

    def test_parser_failures_are_fixed_code_and_never_echo_values(self):
        cases = {
            "unknown option with email": ["run", "--request-id", "demo-001", "--unknown", EMAIL],
            "unknown option with customer id": ["run", "--request-id", "demo-001", "--unknown=" + CUST],
            "missing --request-id": ["run"],
            "--request-id without value": ["run", "--request-id"],
            "no subcommand": [],
            "unknown subcommand email": [EMAIL],
            "unknown subcommand customer id": [CUST],
            "extra positional": ["run", "--request-id", "demo-001", EMAIL],
            "extra on inspect-fixture": ["inspect-fixture", "--extra", CUST],
            "duplicate-looking flag": ["run", "--request-id", "demo-001", "--request-id"],
            "top-level unknown": ["--nope", EMAIL],
        }
        for name, args in cases.items():
            with self.subTest(name):
                p = self.proc(args)
                self.assertEqual(p.returncode, 2)
                self.assertEqual(p.stdout, b"")
                self.assertEqual(p.stderr, b"SANITIZER_INVALID_ARGUMENTS\n")

    def test_in_process_parser_failure_logs_only_code(self):
        with LogCapture() as logs:
            rc, out, err, m = run_cli(["run", "--request-id", "demo-001", "--unknown", EMAIL], TEXT)
        self.assertEqual((rc, out, err), (2, "", "SANITIZER_INVALID_ARGUMENTS\n"))
        self.assertEqual(m.calls, [])
        self.assertEqual(logs.lines, ["ERROR sanitizer rejected code=SANITIZER_INVALID_ARGUMENTS"])

    def test_explicit_help_still_works(self):
        for args in (["--help"], ["-h"], ["run", "--help"], ["inspect-fixture", "-h"]):
            with self.subTest(args):
                p = self.proc(args)
                self.assertEqual(p.returncode, 0)
                self.assertIn(b"usage:", p.stdout)
                self.assertEqual(p.stderr, b"")
                self.assertNotIn(EMAIL.encode(), p.stdout)

    def test_valid_invocation_unaffected(self):
        p = self.proc(["run", "--request-id", "demo-001"], TEXT.encode())
        self.assertEqual((p.returncode, p.stderr), (0, b""))
        self.assertEqual(json.loads(p.stdout), PAYLOAD)


class OversizedInput(unittest.TestCase):
    def test_rejected_before_detection_and_dispatch(self):
        calls = []
        mock = RecordingMock()
        big = EMAIL + "x" * (MAX_INPUT_CHARS - len(EMAIL) + 1)
        self.assertEqual(len(big), MAX_INPUT_CHARS + 1)
        with self.assertRaises(SanitizerError) as cm:
            dispatch("req-001", big, mock, lambda t: calls.append(t) or [])
        self.assertEqual(str(cm.exception), "SANITIZER_INPUT_TOO_LARGE")
        self.assertEqual(calls, [])
        self.assertEqual(mock.calls, [])

    def test_limit_is_inclusive_and_counts_characters(self):
        self.assertEqual(sanitize("x" * MAX_INPUT_CHARS), "x" * MAX_INPUT_CHARS)
        self.assertEqual(sanitize("\U0001F600" * MAX_INPUT_CHARS), "\U0001F600" * MAX_INPUT_CHARS)

    def test_cli_contract_real_process(self):
        big = (EMAIL + " " + CUST + " ") + "x" * MAX_INPUT_CHARS
        p = subprocess.run([sys.executable, "-m", "sanitizer", "run", "--request-id", "req-001"],
                           input=big.encode(), capture_output=True, cwd=ROOT)  # bytes: no newline translation
        self.assertEqual(p.returncode, 2)
        self.assertEqual(p.stdout, b"")
        self.assertEqual(p.stderr, b"SANITIZER_INPUT_TOO_LARGE\n")


class OverlapResolution(unittest.TestCase):
    def kept(self, *spans):
        return [(s["entity_type"], s["start"], s["end"]) for s in resolve_spans(spans)]

    def test_longest_wins(self):
        self.assertEqual(self.kept(span("EMAIL_ADDRESS", 0, 5, 0.1), span("CUSTOMER_ID", 3, 12, 1.0)),
                         [("CUSTOMER_ID", 3, 12)])

    def test_higher_score_on_equal_length(self):
        self.assertEqual(self.kept(span("EMAIL_ADDRESS", 0, 5, 0.5), span("CUSTOMER_ID", 0, 5, 0.9)),
                         [("CUSTOMER_ID", 0, 5)])

    def test_email_before_customer_id_on_tie(self):
        self.assertEqual(self.kept(span("CUSTOMER_ID", 1, 6), span("EMAIL_ADDRESS", 0, 5)),
                         [("EMAIL_ADDRESS", 0, 5)])

    def test_earlier_start_on_full_tie(self):
        self.assertEqual(self.kept(span("EMAIL_ADDRESS", 2, 7), span("EMAIL_ADDRESS", 0, 5)),
                         [("EMAIL_ADDRESS", 0, 5)])

    def test_dedupe_and_adjacent_spans_kept(self):
        a, b = span("EMAIL_ADDRESS", 0, 3), span("CUSTOMER_ID", 3, 6)
        self.assertEqual(self.kept(a, dict(a), b), [("EMAIL_ADDRESS", 0, 3), ("CUSTOMER_ID", 3, 6)])
        self.assertEqual(sanitize("abcdef", lambda t: [a, dict(a), b]), "[EMAIL_ADDRESS][CUSTOMER_ID]")

    def test_ints_accepted_as_scores(self):
        self.assertEqual(sanitize("abc", lambda t: [span("EMAIL_ADDRESS", 0, 3, 1)]), "[EMAIL_ADDRESS]")


class Logging(unittest.TestCase):
    def test_default_logs_contain_no_canaries_on_success_and_failure(self):
        with LogCapture() as logs:
            dispatch("demo-001", TEXT, RecordingMock())
            for det in (leaky_detector, lambda t: [span("EMAIL_ADDRESS", -1, 2)]):
                with self.assertRaises(SanitizerError):
                    sanitize(TEXT, det)
            with self.assertRaises(SanitizerError):
                sanitize(TEXT + "x" * MAX_INPUT_CHARS)
        self.assertTrue(logs.text)  # logging actually happened
        for canary in (EMAIL, CUST, "Email ", "quantity"):
            self.assertNotIn(canary, logs.text)

    def test_real_process_default_logging(self):
        p = subprocess.run([sys.executable, "-m", "sanitizer", "run", "--request-id", "demo-001"],
                           input=TEXT, capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stderr, "")
        self.assertEqual(json.loads(p.stdout), PAYLOAD)
        self.assertNotIn(EMAIL, p.stdout + p.stderr)
        self.assertNotIn(CUST, p.stdout + p.stderr)


class InvalidEncoding(unittest.TestCase):
    def test_in_process_no_detection_no_dispatch(self):
        seen = []
        data = b"\xff " + EMAIL.encode() + b" " + CUST.encode()
        with LogCapture() as logs:
            rc, out, err, mock_ = run_cli(["run", "--request-id", "req-001"], data,
                                          detector=lambda t: seen.append(t) or [])
        self.assertEqual((rc, out, err), (2, "", "SANITIZER_INVALID_ENCODING\n"))
        self.assertEqual(seen, [])
        self.assertEqual(mock_.calls, [])
        for canary in (EMAIL, CUST):
            self.assertNotIn(canary, logs.text)
        self.assertNotIn("codec", logs.text)  # no UnicodeDecodeError text

    def test_byte_bound_precedes_decoding_and_chars_checked_after(self):
        rc, _, err, _ = run_cli(["run", "--request-id", "req-001"], b"x" * (MAX_INPUT_BYTES + 1))
        self.assertEqual((rc, err), (2, "SANITIZER_INPUT_TOO_LARGE\n"))
        rc, _, err, _ = run_cli(["run", "--request-id", "req-001"], b"\xff" * (MAX_INPUT_BYTES + 1))
        self.assertEqual((rc, err), (2, "SANITIZER_INPUT_TOO_LARGE\n"))  # documented precedence
        rc, _, err, _ = run_cli(["run", "--request-id", "req-001"], "é" * (MAX_INPUT_CHARS + 1))
        self.assertEqual((rc, err), (2, "SANITIZER_INPUT_TOO_LARGE\n"))  # 20,002 bytes, 10,001 chars
        rc, out, err, _ = run_cli(["run", "--request-id", "req-001"], "\U0001F600" * MAX_INPUT_CHARS)
        self.assertEqual((rc, err), (0, ""))  # exactly MAX_INPUT_BYTES bytes, 10,000 chars


class InternalError(unittest.TestCase):
    def assert_clean(self, rc, out, err, logs):
        self.assertEqual((rc, out, err), (2, "", "SANITIZER_INTERNAL_ERROR\n"))
        for canary in (EMAIL, CUST, "boom"):
            for stream in (out, err, logs.text):
                self.assertNotIn(canary, stream)
        self.assertNotIn("Traceback", err + logs.text)

    def test_provider_exception_with_canaries(self):
        provider = FailingProvider()
        with LogCapture() as logs:
            rc, out, err, _ = run_cli(["run", "--request-id", "demo-001"], TEXT, provider=provider)
        self.assert_clean(rc, out, err, logs)
        self.assertEqual(provider.calls, 1)  # the provider WAS invoked (with the sanitized payload)
        self.assertIn("ERROR sanitizer rejected code=SANITIZER_INTERNAL_ERROR", logs.lines)
        self.assertTrue(all(r.exc_info is None and r.exc_text is None for r in logs.handler.records))

    def test_library_wraps_provider_exception(self):
        with self.assertRaises(SanitizerError) as cm:
            dispatch("req-001", TEXT, FailingProvider())
        self.assertEqual(str(cm.exception), "SANITIZER_INTERNAL_ERROR")
        self.assertIsNone(cm.exception.__cause__)
        self.assertTrue(cm.exception.__suppress_context__)

    def test_unexpected_exception_inside_sanitizer(self):
        provider = RecordingMock()
        boom = RuntimeError(f"internal {EMAIL} {CUST}")
        with mock.patch("sanitizer.core.resolve_spans", side_effect=boom), LogCapture() as logs:
            rc, out, err, _ = run_cli(["run", "--request-id", "demo-001"], TEXT, provider=provider)
        self.assertEqual(provider.calls, [])
        self.assertEqual((rc, out, err), (2, "", "SANITIZER_INTERNAL_ERROR\n"))
        for canary in (EMAIL, CUST):
            self.assertNotIn(canary, logs.text)
        self.assertNotIn("Traceback", err + logs.text)


class LoggingAllowlist(unittest.TestCase):
    """Root-logger handler at DEBUG; every emitted line must be approved metadata."""

    SCENARIOS = {
        "success": (TEXT, baseline_detector, RecordingMock, "INFO sanitizer dispatched chars=59"),
        "detector failure": (TEXT, leaky_detector, RecordingMock, "ERROR sanitizer rejected code=SANITIZER_DETECTOR_ERROR"),
        "malformed output": (TEXT, lambda t: [span("EMAIL_ADDRESS", True, 5)], RecordingMock,
                             "ERROR sanitizer rejected code=SANITIZER_INVALID_DETECTOR_OUTPUT"),
        "provider failure": (TEXT, baseline_detector, FailingProvider,
                             "ERROR sanitizer rejected code=SANITIZER_INTERNAL_ERROR"),
        "invalid encoding": (b"\xff" + TEXT.encode(), baseline_detector, RecordingMock,
                             "ERROR sanitizer rejected code=SANITIZER_INVALID_ENCODING"),
        "oversize": (TEXT + "x" * MAX_INPUT_CHARS, baseline_detector, RecordingMock,
                     "WARNING sanitizer rejected code=SANITIZER_INPUT_TOO_LARGE"),
    }

    def test_every_log_line_is_approved(self):
        for name, (data, det, prov, expected) in self.SCENARIOS.items():
            with self.subTest(name):
                with LogCapture() as logs:
                    run_cli(["run", "--request-id", "demo-001"], data, det, prov())
                self.assertEqual(logs.lines, [expected])  # exactly one approved line
                for line in logs.lines:
                    self.assertRegex(line, LOG_LINE_OK)
                for r in logs.handler.records:
                    self.assertIsNone(r.exc_info)
                    self.assertIsNone(r.exc_text)
                    self.assertIsNone(r.stack_info)
                for canary in (EMAIL, CUST, "Email", "quantity", "boom"):
                    self.assertNotIn(canary, logs.text)

    def test_logs_never_contain_request_id(self):
        for rid in ("demo-001", "req-987654"):
            with LogCapture() as logs:
                run_cli(["run", "--request-id", rid], TEXT)
            self.assertEqual(logs.lines, ["INFO sanitizer dispatched chars=59"])
            self.assertNotIn(rid, logs.text)
        with LogCapture() as logs:  # also through the library entry point
            dispatch("req-424242", TEXT, RecordingMock())
        self.assertNotIn("424242", logs.text)

    def test_real_process_with_root_logging_configured(self):
        prog = ("import logging, sys\n"
                "logging.basicConfig(level=logging.DEBUG, stream=sys.stderr,"
                " format='%(levelname)s %(name)s %(message)s')\n"
                "from sanitizer.cli import main\n"
                "sys.exit(main(['run', '--request-id', 'demo-001']))\n")
        cases = ((TEXT.encode(), 0, [b"INFO sanitizer dispatched chars=59"]),
                 (b"\xff" + TEXT.encode(), 2, [b"ERROR sanitizer rejected code=SANITIZER_INVALID_ENCODING",
                                               b"SANITIZER_INVALID_ENCODING"]))
        for data, rc, want in cases:
            with self.subTest(rc=rc):
                p = subprocess.run([sys.executable, "-c", prog], input=data, capture_output=True, cwd=ROOT)
                self.assertEqual(p.returncode, rc)
                self.assertEqual(p.stderr.replace(b"\r\n", b"\n").split(b"\n"), want + [b""])
                for canary in (EMAIL.encode(), CUST.encode()):
                    self.assertNotIn(canary, p.stderr)


class RealProcessBytes(unittest.TestCase):
    def run_proc(self, data):
        return subprocess.run([sys.executable, "-m", "sanitizer", "run", "--request-id", "req-001"],
                              input=data, capture_output=True, cwd=ROOT)

    def test_crlf_input_not_normalized(self):
        p = self.run_proc(b"a\r\nCUST-004271\r\n")
        self.assertEqual(p.returncode, 0)
        self.assertEqual(json.loads(p.stdout), {"request_id": "req-001", "text": "a\r\n[CUSTOMER_ID]\r\n"})
        self.assertEqual(p.stdout, json.dumps({"request_id": "req-001", "text": "a\r\n[CUSTOMER_ID]\r\n"},
                                              ensure_ascii=False).encode() + b"\n")

    def test_invalid_utf8_rejected_real_process(self):
        bad_inputs = {
            "invalid start byte": b"\xff\xfe " + CUST.encode() + b" " + EMAIL.encode(),
            "truncated sequence": CUST.encode() + b" \xe2\x82",
            "overlong encoding": b"\xc0\xaf",
            "encoded surrogate": b"\xed\xa0\x80",
            "lone continuation": b"ok \x80",
        }
        for name, data in bad_inputs.items():
            with self.subTest(name):
                p = self.run_proc(data)
                self.assertEqual(p.returncode, 2)
                self.assertEqual(p.stdout, b"")
                self.assertEqual(p.stderr, b"SANITIZER_INVALID_ENCODING\n")

    def test_valid_utf8_edge_cases_accepted(self):
        for data, want in ((b"", ""), ("\U0001F600".encode(), "\U0001F600"),
                           (b"\xef\xbb\xbf" + CUST.encode(), "﻿[CUSTOMER_ID]")):
            with self.subTest(data=data):
                p = self.run_proc(data)
                self.assertEqual(p.returncode, 0, p.stderr)
                self.assertEqual(json.loads(p.stdout)["text"], want)


class Cli(unittest.TestCase):
    def test_success_prints_only_captured_payload(self):
        rc, out, err, mock = run_cli(["run", "--request-id", "demo-001"], TEXT)
        self.assertEqual((rc, err), (0, ""))
        self.assertEqual(json.loads(out), PAYLOAD)
        self.assertEqual(mock.calls, [PAYLOAD])

    def test_inspect_fixture_is_the_explicit_synthetic_view(self):
        rc, out, err, _ = run_cli(["inspect-fixture"], "")
        self.assertEqual(rc, 0)
        self.assertIn(EMAIL, out)
        self.assertIn(CUST, out)
        self.assertIn("EMAIL_ADDRESS [6:21]", out)
        self.assertIn("CUSTOMER_ID [32:43]", out)


if __name__ == "__main__":
    unittest.main()
````

### `tests/test_scoring.py`

````python
"""Scoring, coverage, fixture loading and threshold-selection unit tests (stdlib only).

Synthetic scoring cases only. None of these touches held-out data."""
import json
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

from sanitizer.config import FIXTURE_DIR, GRID, file_sha256
from sanitizer.core import ENTITY_PRIORITY, SanitizerError, replace_spans
from sanitizer.evaluation import (aggregate, load_fixture, metrics, pick_best, run_split, score_example,
                                  select_thresholds)

ORACLE = {
    "text": "ABCD----WXYZ--pq",
    "gold": [{"entity_type": "EMAIL_ADDRESS", "start": 0, "end": 4},
             {"entity_type": "CUSTOMER_ID", "start": 8, "end": 12}],
    "applied": [{"entity_type": "EMAIL_ADDRESS", "start": 0, "end": 3},
                {"entity_type": "CUSTOMER_ID", "start": 7, "end": 12},
                {"entity_type": "PHONE_NUMBER", "start": 14, "end": 16}],
    "expected_output": "[EMAIL_ADDRESS]D---[CUSTOMER_ID]--[PHONE_NUMBER]",
}


def E(a, b):
    return {"entity_type": "EMAIL_ADDRESS", "start": a, "end": b}


def C(a, b):
    return {"entity_type": "CUSTOMER_ID", "start": a, "end": b}


def P(a, b):
    return {"entity_type": "PHONE_NUMBER", "start": a, "end": b}


def totals(sc):
    tp = sum(sc["by_type"][t]["tp"] for t in ENTITY_PRIORITY)
    fp = sum(sc["by_type"][t]["fp"] for t in ENTITY_PRIORITY)
    fn = sum(sc["by_type"][t]["fn"] for t in ENTITY_PRIORITY)
    return tp, fp, fn


class HandCalculatedOracle(unittest.TestCase):
    def setUp(self):
        self.sc = score_example(ORACLE["text"], ORACLE["gold"], ORACLE["applied"])

    def test_counts_and_micro_metrics(self):
        self.assertEqual(totals(self.sc), (0, 3, 2))
        m = metrics(*totals(self.sc))
        self.assertEqual((m["precision"], m["recall"], m["f1"]), (0.0, 0.0, 0.0))

    def test_per_type_counts(self):
        self.assertEqual(self.sc["by_type"], {
            "EMAIL_ADDRESS": {"tp": 0, "fp": 1, "fn": 1},
            "PHONE_NUMBER": {"tp": 0, "fp": 1, "fn": 0},
            "CUSTOMER_ID": {"tp": 0, "fp": 1, "fn": 1}})

    def test_coverage(self):
        self.assertEqual(self.sc["coverage"], ["partial", "full"])  # email partial, customer id full
        self.assertEqual(self.sc["coverage"].count("untouched"), 0)
        self.assertEqual(self.sc["coverage"].count("full") / len(self.sc["coverage"]), 0.5)

    def test_benign_statistics(self):
        self.assertEqual(sum(self.sc["touches_benign"]), 2)
        self.assertEqual(sum(self.sc["touches_no_gold"]), 1)
        self.assertEqual(self.sc["benign_characters_removed"], 3)  # original indices 7, 14, 15

    def test_replacement_output(self):
        self.assertEqual(replace_spans(ORACLE["text"], ORACLE["applied"]), ORACLE["expected_output"])


class EdgeCases(unittest.TestCase):
    def test_wrong_type_with_full_coverage(self):
        sc = score_example("abcdef", [E(0, 4)], [C(0, 4)])
        self.assertEqual(totals(sc), (0, 1, 1))
        self.assertEqual(sc["coverage"], ["full"])  # coverage is distinct from exact-span/type accuracy
        self.assertEqual(sc["benign_characters_removed"], 0)

    def test_adjacent_intervals_union_covers_gold_but_is_not_an_exact_match(self):
        sc = score_example("abcdef", [E(0, 6)], [E(0, 3), E(3, 6)])
        self.assertEqual(sc["coverage"], ["full"])
        self.assertEqual(totals(sc), (0, 2, 1))

    def test_partial_interval_is_one_fp_and_one_fn(self):
        self.assertEqual(totals(score_example("abcdef", [E(0, 4)], [E(0, 3)])), (0, 1, 1))

    def test_repeated_values_are_separate_gold_entities(self):
        sc = score_example("x@y.zz x@y.zz", [E(0, 6), E(7, 13)], [E(0, 6), E(7, 13)])
        self.assertEqual(totals(sc), (2, 0, 0))
        sc = score_example("x@y.zz x@y.zz", [E(0, 6), E(7, 13)], [E(0, 6)])
        self.assertEqual(totals(sc), (1, 0, 1))
        self.assertEqual(sc["coverage"], ["full", "untouched"])

    def test_unicode_offsets_are_code_points(self):
        text = "\U0001F512 Café: leo@example.net"
        start = text.index("leo")
        gold = [E(start, len(text))]
        self.assertEqual(start, 8)
        self.assertEqual(totals(score_example(text, gold, gold)), (1, 0, 0))
        # a UTF-8 byte offset would be wrong: 12 bytes before 'leo', not 8
        self.assertNotEqual(len(text[:start].encode("utf-8")), start)

    def test_empty_gold_and_empty_predictions(self):
        sc = score_example("", [], [])
        self.assertEqual(totals(sc), (0, 0, 0))
        self.assertEqual(sc["benign_characters_removed"], 0)
        m = metrics(0, 0, 0)
        self.assertEqual((m["precision"], m["recall"], m["f1"]), (None, None, None))

    def test_metric_null_rules(self):
        m = metrics(0, 0, 3)  # no predictions, positive gold
        self.assertEqual((m["precision"], m["recall"], m["f1"]), (None, 0.0, 0.0))
        m = metrics(0, 2, 0)  # predictions, no gold
        self.assertEqual((m["precision"], m["recall"], m["f1"]), (0.0, None, 0.0))
        m = metrics(3, 1, 1)
        self.assertEqual((m["precision"], m["recall"], m["f1"]), (0.75, 0.75, 6 / 8))

    def test_benign_only_example_with_a_replacement_is_all_benign(self):
        sc = score_example("hello world", [], [C(0, 5)])
        self.assertEqual((sum(sc["touches_benign"]), sum(sc["touches_no_gold"]), sc["benign_characters_removed"]),
                         (1, 1, 5))
        self.assertEqual(totals(sc), (0, 1, 0))


class AggregateThroughRealPipeline(unittest.TestCase):
    def test_counts_are_summed_before_micro_metrics(self):
        fx = {"examples": [
            {"id": "a", "text": "x@y.zz", "entities": [E(0, 6)], "expected_sanitized": "[EMAIL_ADDRESS]"},
            {"id": "b", "text": "hello CUST-123456", "entities": [C(6, 17)], "expected_sanitized": "hello [CUSTOMER_ID]"},
            {"id": "c", "text": "plain", "entities": [], "expected_sanitized": "plain"},
        ]}
        spans = {"a": [dict(E(0, 6), score=1.0)], "b": [dict(C(6, 17), score=1.0), dict(E(0, 5), score=1.0)], "c": []}
        recs = run_split(fx, lambda ex: (lambda _t, s=spans[ex["id"]]: s), {t: 0.0 for t in ENTITY_PRIORITY})
        agg = aggregate(recs)
        self.assertEqual((agg["micro"]["tp"], agg["micro"]["fp"], agg["micro"]["fn"]), (2, 1, 0))
        self.assertEqual(agg["per_type"]["EMAIL_ADDRESS"]["fp"], 1)
        self.assertEqual(agg["coverage"]["overall"]["coverage_rate"], 1.0)
        self.assertEqual(agg["benign"]["replacements_touching_no_gold"], 1)
        self.assertEqual(agg["preservation"]["no_gold_examples_preserved"], 1)
        self.assertEqual(agg["preservation"]["examples_equal_expected_sanitized"], 2)  # b has an extra redaction
        self.assertEqual(agg["boundary"]["payload_equals_actual_sanitized"], 3)
        self.assertEqual(agg["boundary"]["provider_calls_total"], 3)

    def test_detector_failure_counts_gold_as_missed_with_zero_calls(self):
        fx = {"examples": [{"id": "a", "text": "x@y.zz", "entities": [E(0, 6)], "expected_sanitized": "[EMAIL_ADDRESS]"}]}

        def boom(_t):
            raise RuntimeError("secret x@y.zz")

        recs = run_split(fx, lambda ex: boom, {t: 0.0 for t in ENTITY_PRIORITY})
        self.assertEqual(recs[0]["status"], "SANITIZER_DETECTOR_ERROR")
        self.assertEqual(recs[0]["provider_calls"], 0)
        agg = aggregate(recs)
        self.assertEqual((agg["micro"]["tp"], agg["micro"]["fn"]), (0, 1))
        self.assertEqual(agg["coverage"]["overall"]["untouched"], 1)
        self.assertEqual(agg["boundary"]["zero_calls_on_failure"], 1)


class ThresholdSelection(unittest.TestCase):
    def fx(self, text, gold):
        return {"examples": [{"id": "a", "text": text, "entities": gold, "expected_sanitized": text}]}

    def test_grid_is_125_and_ties_prefer_higher_thresholds(self):
        sel = select_thresholds(self.fx("x@y.zz", [E(0, 6)]), {"a": [dict(E(0, 6), score=1.0)]})
        self.assertEqual(len(sel["grid"]), len(GRID) ** 3)
        self.assertEqual(sel["best"]["thresholds"], {"EMAIL_ADDRESS": 1.0, "PHONE_NUMBER": 1.0, "CUSTOMER_ID": 1.0})

    def test_threshold_is_inclusive_and_picks_highest_passing_value(self):
        sel = select_thresholds(self.fx("x@y.zz", [E(0, 6)]), {"a": [dict(E(0, 6), score=0.6)]})
        self.assertEqual(sel["best"]["thresholds"]["EMAIL_ADDRESS"], 0.6)  # score >= threshold
        self.assertEqual((sel["best"]["tp"], sel["best"]["fp"], sel["best"]["fn"]), (1, 0, 0))

    def test_no_predictions_has_f1_zero_and_selection_still_defined(self):
        sel = select_thresholds(self.fx("x@y.zz", [E(0, 6)]), {"a": []})
        self.assertEqual(sel["best"]["f1"], 0.0)
        self.assertEqual(sel["best"]["fn"], 1)

    def test_false_positive_is_cut_by_raising_its_threshold(self):
        raw = {"a": [dict(E(0, 6), score=0.9), dict(C(8, 11), score=0.5)]}
        sel = select_thresholds(self.fx("x@y.zz  abc", [E(0, 6)]), raw)
        self.assertGreater(sel["best"]["thresholds"]["CUSTOMER_ID"], 0.5)
        self.assertEqual((sel["best"]["tp"], sel["best"]["fp"]), (1, 0))

    def test_tie_break_order_is_f1_then_fewer_benign_then_higher_thresholds(self):
        def entry(f1, benign, e, p_, c):
            return {"_f1": Fraction(f1), "benign_characters_removed": benign,
                    "thresholds": {"EMAIL_ADDRESS": e, "PHONE_NUMBER": p_, "CUSTOMER_ID": c}}

        # higher F1 beats everything
        self.assertEqual(pick_best([entry(1, 9, 0.0, 0.0, 0.0), entry(Fraction(1, 2), 0, 1.0, 1.0, 1.0)])["benign_characters_removed"], 9)
        # equal F1: fewer benign characters wins even with lower thresholds
        best = pick_best([entry(1, 5, 1.0, 1.0, 1.0), entry(1, 2, 0.0, 0.0, 0.0)])
        self.assertEqual(best["benign_characters_removed"], 2)
        # equal F1 and benign: lexicographically higher (EMAIL, PHONE, CUSTOMER) wins
        best = pick_best([entry(1, 2, 0.8, 1.0, 1.0), entry(1, 2, 1.0, 0.0, 0.0), entry(1, 2, 1.0, 0.4, 0.0)])
        self.assertEqual(best["thresholds"], {"EMAIL_ADDRESS": 1.0, "PHONE_NUMBER": 0.4, "CUSTOMER_ID": 0.0})


class FixtureLoading(unittest.TestCase):
    def test_development_fixture_loads_and_matches_summary(self):
        fx = load_fixture(FIXTURE_DIR / "development.json")
        summary = json.loads((FIXTURE_DIR / "fixture_summary.json").read_text(encoding="utf-8"))["development"]
        self.assertEqual(len(fx["examples"]), summary["examples"])
        counts = {t: 0 for t in ENTITY_PRIORITY}
        for ex in fx["examples"]:
            for g in ex["entities"]:
                counts[g["entity_type"]] += 1
        self.assertEqual(counts, summary["gold_entities"])

    def test_development_gold_slices_and_oracles_are_self_consistent(self):
        for ex in load_fixture(FIXTURE_DIR / "development.json")["examples"]:
            applied = [dict(g, score=1.0) for g in ex["entities"]]
            self.assertEqual(replace_spans(ex["text"], applied), ex["expected_sanitized"], ex["id"])

    def test_fixtures_are_the_unchanged_handoff_files(self):
        manifest = json.loads((FIXTURE_DIR.parent / "docs" / "handoff" / "MANIFEST.json").read_text(encoding="utf-8"))
        for name in ("development.json", "heldout.json", "fixture_summary.json"):
            self.assertEqual(file_sha256(FIXTURE_DIR / name), manifest[name], name)

    def test_malformed_fixture_is_rejected_with_fixed_code(self):
        bad = [
            {"schema_version": 2, "offset_unit": "python_unicode_codepoint", "examples": []},
            {"schema_version": 1, "offset_unit": "utf8_bytes", "examples": []},
            {"schema_version": 1, "offset_unit": "python_unicode_codepoint", "examples": [
                {"id": "a", "text": "abc", "entities": [E(0, 9)], "expected_sanitized": "abc"}]},
            {"schema_version": 1, "offset_unit": "python_unicode_codepoint", "examples": [
                {"id": "a", "text": "abc", "entities": [], "expected_sanitized": "abc"},
                {"id": "a", "text": "abc", "entities": [], "expected_sanitized": "abc"}]},
        ]
        with tempfile.TemporaryDirectory() as d:
            for i, obj in enumerate(bad):
                p = Path(d) / f"f{i}.json"
                p.write_text(json.dumps(obj), encoding="utf-8")
                with self.assertRaises(SanitizerError) as cm:
                    load_fixture(p)
                self.assertEqual(str(cm.exception), "SANITIZER_INVALID_FIXTURE")
            with self.assertRaises(SanitizerError):
                load_fixture(Path(d) / "missing.json")


if __name__ == "__main__":
    unittest.main()
````

### `README.md`

````markdown
# Privacy-preserving AI sanitizer (local MVP)

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

Tested on **Windows 11, Python 3.13.7, one machine**. Other platforms are untested. Installation uses the
network (PyPI and one GitHub release asset); the tested inference path does not (see
[Dependency notes](#dependency-notes)).

All commands below are **PowerShell** (Windows PowerShell 5.1 and PowerShell 7 both work) and are run from the
project root. `evaluate` writes `reports/<split>_<detector>.json`; re-running it overwrites the committed report
with identical bytes.

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
score, so it has no margin), PHONE_NUMBER's position in the tie-break order is an agreed assumption. Hosted CI has
not run (see below). Gateway integration, retries/fallbacks and real-provider behavior are out of scope and were
not tested.

## CI

[.github/workflows/ci.yml](.github/workflows/ci.yml) defines a baseline job and a candidate job (the candidate
job sets `REQUIRE_CANDIDATE_TESTS=1`, fails if dependencies are absent and fails on any skipped test). **Hosted
CI status: PENDING** (no hosted run was executed). The same commands were run locally; see the review packet.

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
````

### `WALKTHROUGH.md`

````markdown
# Walkthrough (about three minutes)

**1. The idea.** Text on its way to an LLM provider passes through one pipeline that finds email addresses,
US-format phone numbers (`(AAA) BBB-CCCC`) and customer IDs (`CUST-` + 6 digits) and replaces them with
placeholders. The provider object only ever receives `{"request_id", "text"}`.

**2. See it.** `python -m sanitizer demo` prints a clearly labelled *synthetic* inspection: original fixture text,
gold spans, detected spans, resolved spans, sanitized text and the payload actually captured by an in-memory
mock, for a benign example, Unicode offsets, a repeated value, CRLF/tab, and a detector failure with zero
provider calls. With `--detector presidio` it also shows the real held-out misses and the one unnecessary
redaction. There is no way to feed it your own text, and no real provider.

**3. Two detectors, one pipeline.** A regex baseline (standard library only) and a Presidio candidate
(rule-based recognizers on a small spaCy model; not a trained PII model). Both go through the same validation,
phone scope gate, thresholds, tie-break and replacement code, so the evaluation scores exactly what is sent.

**4. How it was evaluated.** The reviewer supplied 10 development and 18 held-out synthetic examples.
Thresholds for the candidate were chosen on development only (125 configurations) and saved in
`config/frozen_config.json` before the held-out file was opened (it was only hashed). The held-out command refuses
to run without that file. Reports (`reports/*.json`) hold counts, types, scores and offsets, never text. This is a
procedural freeze, not a blinded external evaluation.

**5. Results.** Held-out, exact-span: baseline 28/28 (expected: its regexes encode the same rules that define the
labels). Candidate 26 TP, 1 FP, 2 FN (micro F1 0.9455), all on email: one `.invalid`-suffix address its offline
suffix validator rejects, and one span that started at a `key=` prefix. Phone and customer-ID were 8/8 for both.
Details and the full tables are in the README.

**6. Safety behavior worth noticing.** Invalid spans abort dispatch before any filtering; a missing dependency,
model or config returns a fixed code and sends nothing (no silent fallback); errors print only fixed codes; logs
hold only `dispatched chars=<n>` or `rejected code=<CODE>`; request IDs are synthetic and never logged.

**7. What to be careful about.** Sanitized output can still contain missed fields. The data is tiny and
synthetic. Hosted CI has not run. Gateway integration and retries/fallbacks were out of scope.

## Resume bullets (measured results only)

- Built a Python privacy sanitizer that redacts email, US-format phone and customer-ID fields before a mock
  LLM-provider call, with a regex baseline and a Presidio/spaCy candidate behind one shared validation and
  replacement pipeline; the provider boundary is covered by 128 passing stdlib-only tests (plus 4 candidate test classes that skip without Presidio) and 154 tests with zero skips
  in the candidate environment.
- Designed a frozen evaluation protocol on synthetic data: hashed fixtures, development-only selection over 125
  threshold configurations, a config-gated held-out command, and deterministic privacy-safe reports. On a
  18-example held-out split the baseline matched 28/28 gold spans and the candidate 26 of 28 (1 FP, 2 FN).
- Found and mitigated two risks in a third-party recognizer dependency (runtime network access for suffix
  validation and input text in DEBUG logs), with tests for both.
````

### `requirements-presidio.txt`

````
# Exploratory Presidio environment (Python 3.13.7, Windows 11 AMD64). The baseline needs none of this.
# Create the venv at a SHORT path: a deep path made spaCy fail to load a DLL
# ("filename or extension is too long") on Windows.
#   python -m venv C:\pv
#   C:\pv\Scripts\python -m pip install -r requirements-presidio.txt
# Top-level pins: presidio-analyzer==2.2.366 and the spaCy model wheel (hash-pinned below).
annotated-doc==0.0.6
annotated-types==0.8.0
anyio==4.16.0
blis==1.3.4
catalogue==2.0.10
certifi==2026.10.23
charset-normalizer==3.5.2
click==8.5.1
cloudpathlib==0.26.0
colorama==0.4.6
confection==1.3.4
cymem==2.0.16
filelock==4.2.10
h11==0.16.0
httpcore==1.0.9
httpx==0.28.1
idna==3.20
Jinja2==3.1.6
markdown-it-py==4.3.0
MarkupSafe==3.0.4
mdurl==0.1.2
murmurhash==1.0.16
numpy==2.4.6
packaging==26.3
phonenumbers==9.0.43
preshed==3.0.13
presidio_analyzer==2.2.366
pydantic==2.14.3
pydantic_core==2.50.4
Pygments==2.21.0
PyYAML==6.0.3
regex==2026.11.9
requests==2.34.2
requests-file==3.0.1
rich==15.0.0
setuptools==84.2.1
shellingham==1.5.4
smart_open==9.0.3
spacy==3.8.18
spacy-legacy==3.0.12
spacy-loggers==1.0.5
srsly==2.5.6
thinc==8.3.14
tldextract==5.4.0
tqdm==4.70.1
typer==0.29.0
typing-inspection==0.4.5
typing_extensions==4.16.0
urllib3==2.8.0
wasabi==1.1.3
weasel==1.0.1
wrapt==2.5.2
# spaCy model asset (12,806,118 bytes), downloaded from the explosion/spacy-models GitHub release:
en_core_web_sm @ https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl#sha256=1932429db727d4bff3deed6b34cfc05df17794f4a52eeb26cf8928f7c1a0fb85
````

### `.gitignore`

````
__pycache__/
*.pyc
.venv*/
venv/
.tldextract_cache/
````

### `tests/__init__.py`

(empty file)

## 10. Mutation checks (executed against a throwaway copy, not part of the project)

Each mutation applied to the final source made the suite fail:

| Mutation | Result |
|---|---|
| Phone scope gate removed | 7 failures |
| Threshold comparison `>` instead of `>=` | 26 failures |
| PHONE_NUMBER / CUSTOMER_ID tie order swapped | 2 failures |
| Silent fallback to the baseline when Presidio init fails | 4 failures (the first attempt did not apply; the retry did) |
| Held-out no longer requires the frozen config | 2 failures |
| Dedupe keeps the first span instead of the highest score | 1 failure |
| Phone spans bypass validation | 26 failures |
| (earlier rounds) lenient UTF-8, no request-ID validation, default argparse error, request ID in logs, stock email recognizer, IGNORECASE on CUSTOMER_ID, Presidio logger left at DEBUG | each failed at least one test |

## 11. Manifest (SHA-256 of every file in the ZIP except this packet)


````
ccde76017b643ddaadb9e4f0f7fa59af8d80289c8373efc4a6cd9d0901d960ca  .github/workflows/ci.yml
32d96b5ecd4fe2626a107d4f228d3b88f4a42dcf90590dee4f3301c93f548d0b  .gitignore
507e98f6766828af3e85425d0eb3e05001ca82c49f9e77353fa410930eebb4b9  README.md
a254bbe5f41a0c9e9054833410d8b95b5275a1714a7e7251da6d511f7738247c  WALKTHROUGH.md
1531d8b695db5f65414ee7778f4623547a7b67bd5363b9301d9cf2b20cd5eb3c  config/frozen_config.json
329a93590ff86b544b4966f584855f973cf7aeab9e78fed83d921f0059b85b71  docs/handoff/EVALUATION_CONTRACT.md
f2a9cd0e71b9e60fc3fb0a58f0a73e2e8fd89269f53a7f6e8b5747a28b0bc02a  docs/handoff/MANIFEST.json
d6ac3aec5b98ebe232eb26d5055d58fd91d6352bc3690357f457a1a7f7e73c89  docs/handoff/START_HERE.md
2d9d4ee020ec442f990e33b2e9c5a48da3089d7d0f120ada8750ba5e9f2fd51e  docs/handoff/fixture_summary.json
050aab48f30e09d9736f4e3b637d5b67175cb1a8a5e5af59607092b62b7cc172  fixtures/development.json
2d9d4ee020ec442f990e33b2e9c5a48da3089d7d0f120ada8750ba5e9f2fd51e  fixtures/fixture_summary.json
ce66e9a9dd74935a50f58c7252e50177702470676ebe7c98a060e8f0f3b38dc2  fixtures/heldout.json
d841b4adb500216ed3af903fae3159795dc16fad0cd60c37c79fc0161e60c0a4  reports/SUMMARY.md
5f06d91721352415dfc2db6dbfc648648760afdd6e61d4e9871636375e6df979  reports/development_baseline.json
cdc4bb3419279d74045350e56809a3faa47bfd27e509e1f3839dd6829e3479fb  reports/development_presidio.json
0c92d3fee4e37fcfdd53016b3ba70f8ca0888c1c3ba60f726c2bb2f2151f4ba5  reports/heldout_baseline.json
5f3b0ac82881934b64e6a722874b51cd653e7aba5df7c594417140cdac7d28ee  reports/heldout_presidio.json
561708e04dfd91a20c2b5e0c40b48164ec9edabc7880f1e5894eb90e1bce7651  requirements-presidio.txt
cfb49c5b89983c121688f5a0c8e7233546acddafeb61d7ac97121ef43aac3e23  sanitizer/__init__.py
feee13fbeac92c22792f5f967ef00ebf87633e177f90bfc28c0ad3c67b99390c  sanitizer/__main__.py
29736071c60dba1230c544c1d9acb272bb74e84981bdbbb0b0645dfb7cff202e  sanitizer/cli.py
b785ec2838d1398f2114c0fe046a1e34bd8bb92e59485fd334f7545d20c895e9  sanitizer/config.py
b83d8174ebf6fd10cc47a8469ce8fea2a50fcc5e9029f4483e61494db291a428  sanitizer/core.py
e29a865190a9c5434f4e760276bd1a2b706bc210c72185bf89844ae1cf2f6396  sanitizer/demo.py
5d5793820801e836a802ccc53b7c87f4d428442eb04908b73293909691f0b2bc  sanitizer/detectors.py
52384c1648d4a45244a0946987504dc319b15a7b6d8de2e21bfa284e741a88d6  sanitizer/evaluation.py
0cad7e01e5ab0f1480373b96913d3080e2945d5d945b996ae55ad5e96b1222d1  sanitizer/fixture.py
e79d3c8cb53abf28c4464ccc4a39919fc741d3abbeb54594b614b387768ca108  sanitizer/freeze.py
2f32540351f19955701b82e4a90c6e8ca2734e0e43ab18ed550b4c5851867e7a  sanitizer/presidio_check.py
958f96c36da7c87561837db74513b81ae26f56c6d752df159ac9732e181f014b  sanitizer/presidio_detector.py
fa4d1d056aa82df9977110388c45323bd5c8588a3df6f49716c89528cac095e3  scripts/check_reports.py
39cc7f66ffcbee0e46c29950c431efb71c81f2199f2cce81cf90d6ab317fc1cb  scripts/render_summary.py
4abdfa77b451367335105d07266d5c1784b5e147bf7232f471685bbd73b76789  scripts/run_tests_no_skips.py
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  tests/__init__.py
0ff634449fcb3ded1e09c474c9615294e022a2f7fad6abb4336ff0455f8bb5a7  tests/support.py
afdbbcc7c8db38260b149826a2506555edd55087356a07e670345baa8ba54c66  tests/test_cli.py
9ec97d20cee23283633e5ed9f57d993b75474b4d82d186d3c33782dec5687edf  tests/test_detectors_boundary.py
a27bf3e90a9fe6e7f07b88eab86797c3cbf19cbee1407345539a6d5eeed7cb66  tests/test_docs.py
ad016e77a994e5ac7eda2f0ebec3d3556450fa70c5394508416363683ab19aeb  tests/test_frozen_config.py
520b8236834fddbdf2950c0281faec0fda4f05349995d1fbc53940a0aed13176  tests/test_pipeline.py
e9a3c9b71f391e0010252a37839e6e5a442f71602a52632d0982b57c30e6ebb8  tests/test_presidio_optional.py
4d70befd56922e3aaaea1883d051808414ae4bb9b1bd62c60e96504061092d10  tests/test_sanitizer.py
2e2d056d23dad297f3801e7147db3be068b6115895c91c52649d12f2aa85ef0e  tests/test_scoring.py
````

The handoff manifest hashes for the three fixtures equal the files here: development `050aab48f30e09d9...`, heldout `ce66e9a9dd74935a...`.

## 12. Unresolved assumptions

1. `en_core_web_sm` was accepted by the reviewer; the offline suffix snapshot is the default email validator; the stock-email probe is diagnostic only.
2. `PHONE_NUMBER` sits between `EMAIL_ADDRESS` and `CUSTOMER_ID` in the tie-break (agreed priority).
3. The `presidio-analyzer` logger is set to INFO process-wide; protection holds only for the tested configuration, not against an application re-enabling DEBUG.
4. The frozen phone threshold (0.4) equals the recognizer's base score, so it has no margin; 50 development configurations tied at the top and the lexicographic rule chose it.
5. `request_id` rule `(?:demo|req)-[0-9]{3,12}`, strict detector contract, 40,000-byte precedence, BOM preserved: unchanged from earlier rounds.
6. Report `meta.python` records the interpreter version; the rerun check ignores only that key.
7. Test counts: a skipped candidate class counts as one skipped entry, so "4 skipped" understates the number of candidate tests not exercised without Presidio.

## 13. Pending or out of scope (not executed)

- **Hosted GitHub Actions run: PENDING.** The workflow file is untested on GitHub; its commands were run locally.
- Other operating systems / Python versions / Presidio or spaCy versions: untested.
- Gateway integration, retries/fallbacks, real-provider requests: out of scope, not done.
- Blinded or larger evaluation, real-world data: not done.
- Independent review of this packet: pending (the request in section 1).
- Independent verification that the ZIP equals the packet's embedded sources: pending on the reviewer's side; I checked it programmatically (reported in the handoff message).
