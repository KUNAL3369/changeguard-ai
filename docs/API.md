# API Contracts

Base path `/api/v1` (except `/health`, `/ready` at root). JSON; uploads are multipart.
Auth: `Authorization: Bearer <JWT>`. Timestamps ISO 8601 UTC. IDs are UUIDs.
Pagination: `?limit=50&offset=0` → `{"items":[...],"total":N}` (limit max 200).
Errors: `{"error":{"code":"string","message":"string","details":{}}}`
Status codes: 401 unauthenticated; 404 for missing OR other user's resource; 409 conflict;
413 too large; 415 wrong type; 422 validation. Never leak internals or credentials in errors.

## Phase 1 — Health (no auth)
- `GET /health` → 200 `{"status":"ok"}` (no DB access)
- `GET /ready` → 200 `{"status":"ready","checks":{"database":"ok"}}`;
  503 `{"status":"not_ready","checks":{"database":"failed"}}` (short connect timeout; no details)

## Phase 2 — Projects, documents, test cases, datasets
### Projects
- `POST /projects` `{"name":"Invoice Extraction","description":"...","document_type":"invoice"}` → 201
  `{id,name,description,document_type,created_at,updated_at,archived_at:null}` (name 1–120 chars)
- `GET /projects` (excludes archived unless `?include_archived=true`) · `GET /projects/{id}`
- `PATCH /projects/{id}` (name, description) · `DELETE /projects/{id}` → 204 (soft archive)
### Documents
- `POST /projects/{id}/documents` multipart `file`: application/pdf only, magic bytes `%PDF`,
  max 10 MB (assumption, configurable) → 201 `{id,original_filename,size_bytes,sha256,page_count,created_at}`.
  Duplicate sha256 in project → 409 with `details.existing_document_id`.
- `GET /projects/{id}/documents` · `GET /documents/{id}`
- `GET /documents/{id}/download` → `{"url":"...","expires_in":300}` (signed, short-lived)
### Test cases
- `POST /projects/{id}/test-cases`
```json
{"name":"acme-inv-001","document_id":"uuid","tags":["simple"],
 "expected":{"invoice_number":"INV-1042","vendor_name":"Northstar Supplies","invoice_date":"2026-01-15",
 "currency":"USD","subtotal":"1000.00","tax_amount":"180.00","total_amount":"1180.00"}}
```
  → 201 `{id,name,document_id,tags,current_expected:{version:1,expected_json:{...},created_at},created_at}`
- `GET /projects/{id}/test-cases` · `GET /test-cases/{id}` · `PATCH /test-cases/{id}` (name, tags only)
- `PUT /test-cases/{id}/expected` `{"expected":{...}}` → 201 new version (version+1); old versions untouched
### Datasets
- `POST /projects/{id}/datasets` `{"name":"baseline-set","description":"...","test_case_ids":["uuid"],"field_specs":{...}}`
  → 201 `{id,version_number,name,case_count,field_specs,created_at}`; version_number auto-increments;
  pins each case's current expected_output_id.
- `GET /projects/{id}/datasets` · `GET /datasets/{id}`
- `GET /datasets/{id}/cases` → `[{test_case_id,name,document_id,expected_output_id,expected_json}]`

## Phase 3+ (OUTLINE — finalize exact payloads at the start of each phase)
- `POST /projects/{id}/workflow-versions`, `GET .../workflow-versions`, `GET /workflow-versions/{id}`,
  `POST /workflow-versions/{id}/mark-baseline`
- `POST /projects/{id}/evaluation-runs` `{dataset_version_id, workflow_version_id}` → 202 (PENDING);
  `GET /evaluation-runs/{id}`; `GET /evaluation-runs/{id}/results`; `GET /evaluation-runs/{id}/results/{result_id}`
- `POST /projects/{id}/comparisons` `{baseline_run_id, candidate_run_id}`; `GET /comparisons/{id}`;
  `GET /comparisons/{id}/regressions` (filters: severity, field, classification, test_case)
- Policies: `POST/GET /projects/{id}/release-policies`
- `POST /comparisons/{id}/release-decision` `{policy_id}`; `GET /comparisons/{id}/release-decision`
- `GET /comparisons/{id}/report?format=md|json`

## CLI (M6) — `changeguard evaluate`
Args (finalize in ticket): `--api-url`, `--project`, `--dataset`, `--candidate`, `--baseline` (defaults to
project baseline), `--policy`, `--wait/--no-wait`, `--fail-on-review`.
Exit codes (stable, documented): **0** release PASS · **1** release FAIL · **2** execution/config error ·
**3** REVIEW_REQUIRED (unless `--fail-on-review`, then 1).
Token from env var (e.g. CHANGEGUARD_TOKEN); never printed.

## Proposed Endpoints (PROPOSED, needs approval)
- `POST /evaluation-runs/{id}/cancel` — Cancel run (if PENDING/RUNNING) [PROPOSED, needs approval]
- `DELETE /documents/{id}` — Delete document (soft) [PROPOSED, needs approval]
- `PATCH /workflow-versions/{id}` — Toggle is_baseline (or update metadata) [PROPOSED, needs approval]
