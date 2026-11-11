# Frozen scope and evaluation contract, version 1

## Scope and text coordinates

Three types only: EMAIL_ADDRESS, PHONE_NUMBER, CUSTOMER_ID. All inputs/labels use Python Unicode code-point indices: zero-based and end-exclusive. Do not normalize Unicode, line endings, tabs, or whitespace. Offsets are not UTF-8 bytes or JavaScript UTF-16 units. Preserve the current 10,000-character and 40,000-byte input limits and strict UTF-8 decoding.

CUSTOMER_ID: case-sensitive `CUST-` followed by exactly six ASCII digits, bounded on both sides against ASCII letters, digits, and underscore. The regex remains `(?<![A-Za-z0-9_])CUST-[0-9]{6}(?![A-Za-z0-9_])`.

PHONE_NUMBER: the exact textual format `(AAA) BBB-CCCC`, with one literal ASCII space. A and the first B start in 2–9; every other digit is ASCII 0–9. Treat this as a documented US-style syntax rule, not validation that a number is assigned. Use:

```text
(?<![A-Za-z0-9_])\([2-9][0-9]{2}\) [2-9][0-9]{2}-[0-9]{4}(?![A-Za-z0-9_])
```

Presidio PhoneRecognizer must use US as its configured region. After validating all output spans, accept only phone candidates whose exact `(start,end)` is one of the matches of the scope regex on the original text. Do not repair, expand, trim, or synthesize candidate spans. This gate only restricts scope; it must not insert missing phone detections. Use the same scope regex in the regex baseline. Other phone formats in the fixture are negative examples for THIS narrow task, not assertions that those formats are globally non-sensitive.

EMAIL_ADDRESS: the fixture's email labels use ASCII local parts containing letters, digits, dot, underscore, percent, plus, or hyphen; no leading/trailing/consecutive dot; dotted ASCII domain labels; and an alphabetic final label of at least two characters. Validity under a live Public Suffix List is not a gold-label requirement. Thus `dev@training.invalid` and `audit@records.invalid` are sensitive email-shaped fields by project definition. Do not remove these labels because a recognizer rejects the suffix. The baseline regex and Presidio's distinct rules remain part of the comparison; no full RFC 5322 claim. Unicode occurs around fields rather than in labeled email local parts. With `CUST-200005@example.org`, label the entire email only; the internal customer-ID candidate is an overlap case.

## Validate, threshold, resolve, replace

Validate EVERY detector span before score/scope filtering. Require the existing strict shape, type allowlist, integer non-boolean offsets, in-bounds nonempty intervals, and finite non-boolean scores in [0,1]. Malformed output aborts dispatch. Apply scope and frozen type thresholds (`score >= threshold`), then deduplicate same-type/same-range predictions, retaining the highest score. Resolve overlaps by decreasing length, decreasing score, type order EMAIL_ADDRESS → PHONE_NUMBER → CUSTOMER_ID, then earlier start. Keep nonoverlapping intervals and replace from right to left with `[TYPE]`.

Use one shared pipeline to obtain the spans actually applied and the text dispatched. Evaluation must not reconstruct a different detector/resolver than dispatch. The public sanitize() API may keep returning text; a shared internal result or helper is fine. Validate model initialization and missing dependency failures without raw exceptions in CLI output.

## Select thresholds before held-out evaluation

Baseline scores remain 1.0 with threshold 1.0 for all three types.

For the candidate, collect raw candidates ONLY on development.json. Evaluate the threshold triples in `{0.0, 0.4, 0.6, 0.8, 1.0}^3` using cached development candidates and the full shared scope/resolve pipeline. Choose the triple with the highest development exact-span micro F1. Break ties by fewer benign characters removed, then lexicographically higher thresholds in EMAIL_ADDRESS, PHONE_NUMBER, CUSTOMER_ID order. This is 125 small configurations; do not rerun NLP 125 times. Every type has development gold, so the overall micro F1 is defined; a candidate with no predictions has F1 0.

Record the chosen triple, rule configuration, exact versions/model asset hash, fixture hash, selection rule, and development metrics. Freeze these before accessing held-out example text or predictions. Different values and templates already separate development and held-out examples; this is a tiny synthetic benchmark, not a representative production sample. Never optimize thresholds on the held-out set. Do not run a hidden fallback detector to improve the candidate's measured score.

## Primary accuracy metrics

Score the final applied spans AFTER validation, scope filtering, frozen thresholds, deduplication, and overlap resolution. A TP is an exact one-to-one match on `(example_id, entity_type, start, end)` with gold. Any unmatched prediction is FP; any unmatched gold span is FN. A wrong type or partial interval gives one FP and one FN. Repeated values at different positions are separate gold entities. Optional pre-resolution diagnostics must be labeled separately and cannot replace these metrics.

For each type and micro total, report integer TP, FP, FN and:

```text
precision = TP / (TP + FP)
recall    = TP / (TP + FN)
F1        = 2*TP / (2*TP + FP + FN)
```

Use JSON null when a metric's own denominator is zero. Thus no predictions with positive gold means precision null, recall 0, F1 0. With no gold but positive predictions, recall null and F1 0. With neither, all three are null. Aggregate counts across examples BEFORE computing micro metrics. Keep unrounded numbers in JSON and round only presentation, e.g. four decimal places. No bootstrap intervals or statistical superiority claims are needed for this sample.

## Redaction coverage and unnecessary redaction

For each gold interval G, take the union R of actual applied original-coordinate intervals. Full coverage means every original character position in G is in R, regardless of placeholder type; partial coverage means some but not all positions; untouched means none. Coverage rate = fully covered gold / all gold, null if no gold. Partial coverage is a failure. Report full, partial, untouched and rate overall and per gold entity type. Coverage is distinct from exact-span/type accuracy.

Let U be the union of gold character positions. Report:

- replacements_touching_benign: count of applied replacements with at least one position outside U;
- replacements_touching_no_gold: count whose intersection with U is empty;
- benign_characters_removed: size of R minus U (set difference, not subtracting unrelated interval lengths).

Count punctuation, whitespace, and line breaks as characters. A replacement may fully cover gold AND remove benign characters. Assert that reconstructing text from the actual applied intervals yields the actual sanitized output. If the whole example has no gold, assert exact original-text preservation and report how many such examples were preserved. Also report number of all examples whose output equals expected_sanitized. Do not use a raw substring-absence check as coverage: repeated values and reintroduced placeholder text make it insufficient.

## Hand-calculated scoring oracle

This is a synthetic scoring-unit-test case with injected predictions, not detector training/evaluation data.

```json
{
  "text": "ABCD----WXYZ--pq",
  "gold": [
    {"entity_type": "EMAIL_ADDRESS", "start": 0, "end": 4},
    {"entity_type": "CUSTOMER_ID", "start": 8, "end": 12}
  ],
  "applied_predictions": [
    {"entity_type": "EMAIL_ADDRESS", "start": 0, "end": 3},
    {"entity_type": "CUSTOMER_ID", "start": 7, "end": 12},
    {"entity_type": "PHONE_NUMBER", "start": 14, "end": 16}
  ],
  "expected_output": "[EMAIL_ADDRESS]D---[CUSTOMER_ID]--[PHONE_NUMBER]"
}
```

Expected micro: TP=0, FP=3, FN=2, precision=0, recall=0, F1=0. Full=1 (customer ID), partial=1 (email), untouched=0, coverage=0.5. replacements_touching_benign=2; replacements_touching_no_gold=1; benign_characters_removed=3 (original indices 7,14,15). Include separate wrong-type/full-coverage and adjacent-interval-union unit cases.

## Reports, demo, boundary evidence

Evaluation reports may contain example IDs, entity types, numeric scores, start/end coordinates, counts, metrics, and fixed status codes. Do not emit raw input, matched values, partially sanitized text that may contain misses, or raw exceptions into default reports/logs. Actual synthetic value inspection belongs only to an explicit fixture-inspection/demo command. Such a command may show one actual missed gold field and one actual unnecessary redaction IF they occur; do not invent them. If none occur, say zero observed on these fixtures. Reports should link to the corresponding synthetic example ID and intervals so a reviewer can inspect explicitly.

The fixture's expected_sanitized is an oracle, NEVER a detector output or provider input shortcut. A mock call must run through the real sanitization/dispatch path and capture exactly `{request_id, text}`. Test exact equality for known-correct development cases and the all-three-entity synthetic canary. For evaluation examples, separately record whether the actual payload equals the actual sanitized text; any leaked gold characters still count as detector/coverage failures. Do not call a detector miss a successful privacy outcome. Never assert universal PII removal from passing boundary tests.

Default normal CLI output can contain detector misses because it returns sanitized text; document that limitation. Input/matched values must stay out of default LOGS and evaluation REPORTS. The synthetic fixture source is intentionally readable. A provider can already have been invoked when it raises; distinguish that from detector/validation failure, which must produce zero provider calls.

## Completion evidence

Completion requires both detectors and the CLI working for the scoped types; frozen development selection; held-out comparison with all raw counts and defined metrics; meaningful boundary/failure/logging tests; basic CI configuration; exact reproducible setup/demo/evaluation commands verified in a fresh environment; README and short walkthrough; and source/report/config/fixture evidence exported together. Hosted CI, other platforms, gateway integration, retries/fallbacks and real-provider runs remain PENDING or OUT OF SCOPE unless actually executed and evidenced. Do not label skipped Presidio tests as passing candidate verification.
