# Architecture

## Style
Modular monolith. No microservices, Kubernetes, Kafka, Redis/Celery in MVP.

```
React+TS (Vite) ──HTTP──► FastAPI (api/)
CLI (Typer) ────HTTP──►      │
                              ├─ services/  projects, datasets, workflows, runs, comparisons
                              ├─ core/      PURE PYTHON: evaluators, normalizers, regression, policy, report
                              ├─ adapters/  llm provider, pdf text, storage
                              └─ db/        SQLAlchemy models, Alembic
Worker process (same codebase) ──polls Postgres──► executes runs
PostgreSQL  +  private object storage (Supabase Storage) for PDFs
```

## Layer rules
- `api/routes`: parse/validate HTTP, call services, return schemas. No business logic.
- `services`: orchestration and DB access. May use core + adapters.
- `core`: pure functions/types. No DB, HTTP, filesystem, env, clock or network. Testable in isolation.
- `adapters`: all external I/O behind small interfaces (LLMProvider, PdfTextExtractor, Storage).
  Provide a mock/fake implementation of each for tests.
- Supabase appears ONLY in the auth dependency and the storage adapter. The storage adapter also has a local-disk implementation for dev/tests.

## Background execution
- `POST evaluation-runs` creates a run (PENDING) and returns immediately.
- Worker (`python -m app.worker`) claims PENDING runs with `SELECT ... FOR UPDATE SKIP LOCKED`,
  sets RUNNING, writes `heartbeat_at` periodically, processes cases with a bounded semaphore
  (default 3), persists each case result as it completes, then sets final status.
- Stale-run recovery: RUNNING runs with an old heartbeat are marked back to PENDING or FAILED per a
  documented rule (decide in the ticket; record in DECISIONS.md).
- Frontend/CLI poll `GET /evaluation-runs/{id}`.
- Do NOT use FastAPI BackgroundTasks for runs (lost on restart).

## Run statuses
PENDING, RUNNING, COMPLETED (every case has a result, even with field failures),
PARTIAL (some cases EXECUTION_ERROR), FAILED (run-level failure), CANCELLED.
Only COMPLETED/PARTIAL runs can be compared. Case statuses: PENDING, RUNNING, SUCCEEDED, EXECUTION_ERROR.

## Document handling
- Text-layer PDFs only. Extract text per page (pdfplumber or pypdf; check PyMuPDF license before use).
- Prompt includes page markers like `[[PAGE 1]]` so the model can cite pages.
- Document-level extraction failures (e.g. no text layer) are execution errors, not quality failures.

## Extraction contract (LLM → system)
Model must return JSON only:
```json
{"fields": {"invoice_number": {"value": "INV-1042", "page": 1, "quote": "Invoice No: INV-1042"},
            "total_amount":   {"value": "1180.00", "page": 1, "quote": "Total 1,180.00"}}}
```
- Parse and schema-validate. Invalid JSON/schema → recorded as schema failure on the case (not a crash).
- Evidence check: normalize whitespace, test that `quote` occurs in the text of `page`.
  Set `evidence_verified` true/false. Never invent evidence when the model gives none (store null).
- Store raw model output untouched; store normalized output separately.

## Provider adapter
Implementations: one real provider (open decision O1), `mock` (unit tests), `replay` (reproducible demo; see SAMPLE_DATA.md).
Interface: `extract(document_text_pages, prompt_template, extraction_schema, config) -> ProviderResult`
(raw text, parsed JSON, token usage, latency, provider/model actually used). Retries only on
transient errors (timeouts, 429, 5xx), max 2, each attempt recorded. Provider chosen later
(see DECISIONS.md). Keys from env only; redact in logs.

## Auth and access
- UI: Supabase Auth JWT. Verification method (shared secret vs JWKS) depends on the Supabase project
  config: check Supabase docs; do not guess.
- `get_current_user` is a single dependency; tests override it.
- Every project-scoped query filters by owner_id. Other users' resources return 404.
- CLI (M6): personal API tokens, stored hashed (table api_tokens).

## Security checklist
Validate upload type by magic bytes (%PDF) and size limit (default 10 MB, configurable, assumption);
generated storage keys; private bucket; short-lived signed download URLs; no secrets or full document
text in logs; redact secrets; rate-limit costly endpoints (run creation); documents not exposed in
public reports by default; document retention/deletion behavior in README.

## Observability (MVP level)
Structured logs with run_id/case_id; persisted run/case status, errors, retries, latency, tokens,
estimated cost when calculable, release decision. The system must be able to explain why a run failed
without server access.

## Deployment (M8)
Docker images for API and worker; one cloud platform (undecided); health/ready endpoints; env-based config.
