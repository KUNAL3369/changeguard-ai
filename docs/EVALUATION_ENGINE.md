# Evaluation Engine (app/core) — the portfolio centerpiece

Pure Python. No DB/HTTP/env/clock. Everything here is a function or a typed model and is unit-tested.
Statements marked (proposed) should be confirmed with the developer in the ticket that implements them.

## Principles
1. Deterministic over LLM judging. 2. Preserve raw outputs. 3. Normalize transparently (record what was normalized).
4. Explain every failure in `failure_reason`. 5. Missing execution is never a pass.
6. Thresholds are configurable. 7. Version the evaluator (`EVALUATOR_VERSION` constant stored with runs).

## Field evaluation
`evaluate_field(expected, actual, spec, *, actual_state) -> FieldResult{passed, evaluator_type, score|None, failure_reason|None, severity, expected, actual, actual_state, normalized_expected|None, normalized_actual|None}`
`evaluate_case(expected_json, normalized_output, field_specs) -> list[FieldResult]`

Presence/state rules (T08, decisions D1–D4 in docs/DECISIONS.md): actual values carry a `ValueState` —
`present` (key holds a value), `absent` (key missing), `null` (explicit JSON null) — passed as the required
keyword `actual_state` and echoed in `FieldResult.actual_state`.
- expected null + actual absent/null → pass, unless `required: true`, which fails `missing` (D1: a required promise never silently passes).
- expected null + actual present → fail `unexpected_value` (D2); the `required` evaluator passes when the value is present and non-empty (D3: required checks presence only).
- expected non-null + actual absent/null → fail `missing`.
- `required: true` + empty/whitespace-only actual → fail `empty` (never truthiness: `0` and `False` are present values).
- score is `None` for exact/required (D4); numeric (T10) defines partial credit. State/value contradictions raise `ValueError`;
  unimplemented evaluator types raise `NotImplementedError` — never a silent pass.

Ownership notes for later tickets:
- T13 (`evaluate_case`) and T27 (case runner) own the raw-output mapping: missing key → `absent`, explicit null → `null`.
  Any empty-string-to-null mapping must be an explicit, documented normalization step, never implicit.
- T22 (dataset version) must reject field specs with `required: true` and a null expected value (D1/D3 contradiction).
- T25 (provider adapters) and T27 must parse model JSON with `parse_float=Decimal` — never float (ADR-008).

### Evaluators
- **exact**: strict equality after type check. No normalization.
- **normalized_string** (T09, confirmed in O8): runs after the presence/state rules above. Both expected and actual must be `str` —
  any other type fails `type_mismatch` with **no `str()` coercion**. Both sides are normalized with `normalize_text`
  (`backend/app/core/normalizers.py`) in this order: (1) Unicode **NFC** (canonical composition, so composed vs decomposed
  input compare equal — NFKC is deliberately NOT used because compatibility folding can change meaning); (2) trim and collapse
  every whitespace run (`" ".join(value.split())` — spaces, tabs, newlines, NBSP) to a single space; (3) if `case_sensitive: false`
  (spec default `true`), apply `casefold()` last, so `Straße` and `STRASSE` compare equal. Equal normalized values → pass,
  otherwise fail `value_mismatch`. The normalized forms are recorded on the result as `normalized_expected`/`normalized_actual`
  for both pass and value mismatch (normalization is transparent, principle 3). Score is `None`.
  **Known limits:** punctuation and dash variants are significant (`Acme Ltd.` ≠ `Acme Ltd`, en dash ≠ hyphen) and
  zero-width characters (e.g. U+200B) are NOT treated as whitespace and are NOT removed — both are expected differences until
  a future ticket decides otherwise.
- **numeric**: parse to `Decimal`. Accept thousands separators with "." as decimal point by default; strip currency symbols only if configured;
  unparseable → fail with reason. Pass if `abs(a-e) <= tolerance` (tolerance is a Decimal string in spec). Never use float. (proposed)
- **date**: normalize to ISO `YYYY-MM-DD`. Default accepted: ISO, `D Mon YYYY`, `Month D, YYYY`. Slash formats (`03/04/2026`) require explicit
  `day_first` in spec; otherwise fail as "ambiguous date". (proposed)
- **required**: present and non-empty.
- **json_schema**: validate the whole normalized output (case-level, field_path `$`) with `jsonschema`; feeds the `schema_valid` policy rule.
- **custom_rule**: `subtotal_plus_tax_equals_total` checks the ACTUAL output's internal consistency within tolerance; if inputs unavailable → fail
  with reason `inputs_unavailable` (proposed). Business rules are configurable examples, not accounting advice.

Severity order: critical > high > medium > low.

## Pass-rate definition
Field-level pass rate = passed field checks / total field checks, over cases whose status is SUCCEEDED.
Cases with EXECUTION_ERROR are excluded from the rate and reported separately, then gated by `max_execution_error_rate`.
If zero cases were evaluated, no rule may pass vacuously: decision = FAIL.

## Regression classification (per test_case × field_path)
Precedence (first match wins):
1. Either run has no result row for the case → MISSING_RESULT
2. Either run's case status is EXECUTION_ERROR → EXECUTION_ERROR
3. baseline pass & candidate pass → UNCHANGED_PASS
4. baseline pass & candidate fail → REGRESSION
5. baseline fail & candidate pass → IMPROVED
6. baseline fail & candidate fail → UNCHANGED_FAIL
A field failing in both runs is NOT a new regression. Severity for the row = field's severity from field_specs.
Comparison requires both runs on the same dataset_version.
Tests: one test per row above plus mixed-case summaries.

## Release policy
Rule types: `no_critical_regression`, `no_high_regression`, `min_pass_rate`, `max_execution_error_rate`, `schema_valid`.
Each rule has `on_fail` = `fail` | `review`.
`evaluate_policy(comparison_summary, policy) -> Decision{decision, rule_results[]}` where each rule result =
`{rule, passed, on_fail, observed, threshold, message}`.
Aggregation: any failed rule with on_fail=fail → FAIL; else any failed rule with on_fail=review → REVIEW_REQUIRED; else PASS.
Also FAIL if zero cases evaluated, or if either run is not COMPLETED/PARTIAL.
MISSING_RESULT is treated like an execution problem and must never silently pass.

## Report (core renders from data; services supply the data)
Project, dataset version, baseline & candidate versions, case count, pass rate (baseline, candidate, delta), regression count,
critical regression count, improvements, existing failures, execution errors, latency, cost if known, decision, per-rule reasons,
failure details (case, field, expected, baseline, candidate, reason, evidence + verified flag). Output: Markdown and JSON.

## Test matrix (minimum)
Each evaluator: pass, fail, missing, null/optional, edge values (rounding at tolerance boundary, ambiguous date, comma/dot amounts).
Classifier: every precedence row. Policy: PASS / REVIEW / FAIL paths, zero-case FAIL, boundary values for thresholds.
Boundary test: no forbidden imports inside app/core.
