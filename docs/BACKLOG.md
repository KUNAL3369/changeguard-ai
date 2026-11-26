# Backlog (each ticket ≈ 2 hours). Mark done only with evidence in PROGRESS.md.

## M1 Foundation (~4 days)
- [x] T01 Repo layout, uv project, FastAPI app, `/health`. Done when: `uv sync` ok, curl /health 200.
- [x] T02 Docker Compose Postgres, SQLAlchemy session, Alembic init + empty baseline revision, `/ready`. Done when: upgrade/downgrade/upgrade ok; /ready 200, and 503 after `docker compose stop db`.
- [x] T03 Typed settings (pydantic-settings), `.env.example`, secret-redaction in logging. Done when: no URL/password in logs (test).
- [x] T04 Pytest setup with separate test DB fixture. Done: health/ready tests pass against real Postgres; 18 tests passed on 2026-11-25; CI green.
- [x] T05 GitHub Actions: lint + tests on PR. Done: PR #1 green check (`Lint and test` SUCCESS, 27s) on 2026-11-25.
**M1 verification (owner approved M1 only; PR #1 MERGED as true merge commit `36ab80b`):** clean clone → compose up → alembic upgrade → uvicorn → curl.exe health/ready → pytest → CI green.

## M2 Evaluation core — pure Python (~8 days)
- [x] T07 Core types (FieldSpec, FieldResult, Severity) + import-boundary test. Done: ruff clean; 28 tests passed (10 new) on 2026-11-26; committed as `6b994dc` (not pushed).
- [x] T08 exact + required evaluators + tests. Done: `evaluate_field(expected, actual, spec, *, actual_state)` in `backend/app/core/evaluators.py`; `ValueState`, `UNEXPECTED_VALUE`, `VALUE_MISMATCH`, `actual_state` added to core types; 69 tests passed + ruff clean on 2026-11-26 (evidence in PROGRESS.md); committed, not pushed.
- [x] T09 normalized_string evaluator + tests. Done: `app/core/normalizers.py` (`normalize_text`: NFC → whitespace collapse → optional casefold) + type-strict `normalized_string` dispatch in `evaluate_field`; `FieldSpec.case_sensitive`, `FieldResult.normalized_expected/normalized_actual`; `107 passed` + `All checks passed!` (ruff) on 2026-11-26 (evidence in PROGRESS.md); committed, not pushed.
- T10 numeric evaluator (Decimal, tolerance) + boundary tests.
- T11 date evaluator + ambiguity tests.
- T12 json_schema + custom_rule evaluators + tests.
- T13 `evaluate_case` + tests.
- T14 regression classifier (one test per precedence row).
- T15 policy engine (PASS/REVIEW/FAIL, zero-case FAIL).
- T16 Markdown + JSON report renderer (golden-file tests).
- T17 Synthetic invoice generator + ground_truth.json (deterministic seed).

## M3 Projects and datasets (~6 days)
- T06 `get_current_user` dependency (Supabase JWT; check docs for verification mode, O3) + test override. Done when: protected route 401 without token, 200 with a valid test token. (Moved from M1; starts only after M1/M2 review.)
- T18 Models + migration: projects, documents, test_cases, expected_outputs.
- T19 Project CRUD with ownership checks + tests (other user → 404).
- T20 Storage adapter (private) + PDF upload validation (magic bytes, size, sha256 dedupe).
- T21 Test-case + expected-output versioning (PUT creates new version).
- T22 Dataset version creation + immutability tests.
- T23 Import script loading the synthetic dataset through the API.

## M4 Workflows and execution (~6 days)
- T24 Workflow version model + API (prompt hash, no secrets).
- T25 Provider adapter interface + `mock` + `replay` providers (reproducible demo) + extraction contract parsing; then one real provider (resolve O1 first for that part).
- T26 PDF text extraction adapter + evidence verification. (Resolve O7.)
- T27 Case runner: one case → raw + normalized output + error capture.
- T28 Run + case_results models; `POST evaluation-runs` (202).
- T29 Worker loop (SKIP LOCKED, heartbeat, bounded concurrency, stale recovery). (Resolve O5.)
- T30 Persist field_evaluations; status transitions COMPLETED/PARTIAL/FAILED.

## M5 Comparison and release (~5 days)
- T31 Comparison service on persisted runs (same-dataset check) + regression_results.
- T32 Policy CRUD + release decision with policy snapshot.
- T33 Report endpoint (md/json).
- T34 Controlled-regression integration test using replay recordings: v1 vs v2 → FAIL with critical total_amount regressions; v1 vs v3 → improvement, not FAIL. Also create `sample_data/recordings/` v1/v2/v3 with honest meta.

## M6 CLI + CI (~4 days)
- T35 API tokens (hashed) + auth for CLI.
- T36 `changeguard evaluate` with polling, readable summary, exit codes 0/1/2/3.
- T37 Sample GitHub Actions workflow + docs; verify a failing check on a real regression.

## M7 UI (~6 days)
- T38 Frontend scaffold + API client from OpenAPI + auth. T39 Project list/detail + document upload.
- T40 Test cases + expected values + dataset versions. T41 Workflow versions + run start/progress.
- T42 Comparison screen (key screen; filters severity/field/classification/case).
- T43 Failure detail (PDF + expected/baseline/candidate + evidence + reason) and report view.

## M8 Ship (~5 days)
- T44 Dockerfiles (API, worker, frontend). T45 Deploy + env config. T46 Security review against ARCHITECTURE checklist.
- T47 Optional live verification with a real provider (manual, documented, measured results only). T48 README (architecture + limitations), diagram, demo video, case study.

## Ticket prompt template
Context · Objective · Docs to read · Existing files to inspect · Required changes · Constraints ·
Acceptance criteria · Required tests · Verification commands · Expected final report (CLAUDE.md format).
