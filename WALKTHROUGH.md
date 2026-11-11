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
