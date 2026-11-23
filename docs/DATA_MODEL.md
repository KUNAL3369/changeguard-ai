# Data Model (logical design; refine types/indexes in the migration ticket)

Conventions: UUID PKs, `timestamptz` UTC, JSONB where noted, snake_case. "imm" = immutable after
insert (enforced in service layer and tested; DB triggers optional later).
No users table: `owner_id` is the Supabase auth user id (UUID). Do not store passwords.

| Table | Columns | Constraints / notes |
|---|---|---|
| projects | id, owner_id, name, description, document_type, created_at, updated_at, archived_at | index owner_id |
| documents | id, project_id, original_filename, storage_key, content_type, size_bytes, sha256, page_count, created_at | UNIQUE(project_id, sha256); storage_key generated |
| test_cases | id, project_id, document_id, name, tags jsonb, created_at, archived_at | |
| expected_outputs (imm) | id, test_case_id, version int, expected_json jsonb, created_at | UNIQUE(test_case_id, version); edit = new row |
| dataset_versions (imm) | id, project_id, version_number, name, description, field_specs jsonb, created_at, created_by | UNIQUE(project_id, version_number) |
| dataset_version_cases (imm) | dataset_version_id, test_case_id, expected_output_id | composite PK |
| workflow_versions (imm*) | id, project_id, version_number, name, provider, model_identifier, prompt_template, prompt_hash, extraction_schema jsonb, config jsonb, notes, is_baseline bool, created_at | *only is_baseline mutable; NO secrets; UNIQUE(project_id, version_number) |
| evaluation_runs | id, project_id, dataset_version_id, workflow_version_id, status, total_cases, completed_cases, failed_cases, claimed_at, heartbeat_at, started_at, completed_at, total_latency_ms, total_tokens, estimated_cost, error_summary, evaluator_version, app_version | statuses in ARCHITECTURE.md |
| case_results | id, run_id, test_case_id, status, raw_output jsonb, normalized_output jsonb, execution_error, attempts, latency_ms, token_usage jsonb, provider_used, model_used, created_at | UNIQUE(run_id, test_case_id) |
| field_evaluations | id, case_result_id, field_path, expected_value jsonb, actual_value jsonb, evaluator_type, passed, score, severity, failure_reason, evidence jsonb, evidence_verified bool | UNIQUE(case_result_id, field_path) |
| comparisons | id, project_id, baseline_run_id, candidate_run_id, status, summary jsonb, created_at | CHECK baseline <> candidate; same dataset_version enforced in service |
| regression_results | id, comparison_id, test_case_id, field_path, baseline_passed, candidate_passed, classification, severity, explanation, created_at | |
| release_policies | id, project_id, name, rules jsonb, enabled, created_at, updated_at | |
| release_decisions | id, comparison_id, policy_id, policy_snapshot jsonb, decision, reasons jsonb, created_at | snapshot so later policy edits do not rewrite history |
| api_tokens (M6) | id, owner_id, name, token_hash, created_at, last_used_at, revoked_at | store hash only |

Deferred: audit_events.

## Enumerations
- run.status: PENDING, RUNNING, COMPLETED, PARTIAL, FAILED, CANCELLED
- case.status: PENDING, RUNNING, SUCCEEDED, EXECUTION_ERROR
- severity: critical > high > medium > low
- classification: IMPROVED, UNCHANGED_PASS, UNCHANGED_FAIL, REGRESSION, EXECUTION_ERROR, MISSING_RESULT
- decision: PASS, FAIL, REVIEW_REQUIRED

## field_specs (stored on dataset_versions)
```json
{
  "invoice_number": {"evaluator":"exact","severity":"critical","required":true},
  "vendor_name":    {"evaluator":"normalized_string","case_sensitive":false,"severity":"high","required":true},
  "invoice_date":   {"evaluator":"date","severity":"high","required":true},
  "currency":       {"evaluator":"exact","severity":"high","required":true},
  "subtotal":       {"evaluator":"numeric","tolerance":"0.02","severity":"high","required":true},
  "tax_amount":     {"evaluator":"numeric","tolerance":"0.02","severity":"high","required":false},
  "total_amount":   {"evaluator":"numeric","tolerance":"0.02","severity":"critical","required":true}
}
```
Optional custom rules live beside field_specs, e.g. `{"rule":"subtotal_plus_tax_equals_total","tolerance":"0.02","severity":"high"}`.

## Expected output example (synthetic)
```json
{"invoice_number":"INV-1042","vendor_name":"Northstar Supplies","invoice_date":"2026-01-15",
 "currency":"USD","subtotal":"1000.00","tax_amount":"180.00","total_amount":"1180.00"}
```
Optional fields (e.g. tax_amount on a tax-free invoice) use null in expected output (meaning: must be absent/null in actual).

## Release policy example (release_policies.rules)
```json
{"rules":[
 {"type":"no_critical_regression","on_fail":"fail"},
 {"type":"no_high_regression","on_fail":"review"},
 {"type":"min_pass_rate","value":0.95,"on_fail":"fail"},
 {"type":"max_execution_error_rate","value":0.02,"on_fail":"fail"},
 {"type":"schema_valid","on_fail":"fail"}
]}
```

## Integrity rules to test
Dataset creation pins current expected_output_id per case and rejects cases without expected output or
from another project. Editing expected values never alters existing dataset versions. Runs cannot be
created against another project's dataset/workflow. Comparing runs on different dataset versions → 422.
