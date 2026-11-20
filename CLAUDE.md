# ChangeGuard AI — Claude Code Project Instructions

## What this project is
ChangeGuard AI (provisional name) is a release-readiness tool for AI document-extraction
workflows (invoices first). It replays a versioned test dataset against a **baseline** and a
**candidate** workflow version (prompt / model / schema), evaluates outputs field by field with
**deterministic** checks, classifies regressions, applies a release policy
(PASS / FAIL / REVIEW_REQUIRED), and fails CI through a CLI when the policy fails.

Core loop: **Replay → Evaluate → Compare → Explain → Decide.**
Promise: "Know what your AI workflow broke before you release it."

This is a portfolio project for Applied AI Engineer roles. It is NOT a general observability
platform. Do not add tracing, dashboards, or features because competitors have them.

## Who you are working with
- Kunal: full-stack/AI developer (Python, FastAPI, React, TS, PostgreSQL, Supabase, pgvector, Docker).
- Has ~2 hours per day and a full-time job. Every task must fit in one ~2 hour session.
- Weak areas this project exists to close: LLM evaluation, versioned datasets, regression
  detection, CI release gates. Explain evaluation-related decisions briefly and plainly.
- He must be able to explain every line in an interview. Prefer simple, readable code over clever code.
- Do not trust yourself blindly and do not expect him to. Verifiable output beats confident claims.

## Docs map (read the relevant doc BEFORE working in that area)
| File | Read when |
|---|---|
| docs/PRD.md | Scope, user journey, MVP acceptance criteria, what not to claim |
| docs/ARCHITECTURE.md | Layout, module boundaries, worker, extraction contract, security |
| docs/DATA_MODEL.md | Any migration or model work |
| docs/API.md | Any endpoint or CLI work |
| docs/EVALUATION_ENGINE.md | Anything in app/core (evaluators, regression, policy, report) |
| docs/SAMPLE_DATA.md | Synthetic dataset and the demo scenario |
| docs/BACKLOG.md | Picking the next ticket and its "done when" |
| docs/DECISIONS.md | Why choices were made; open decisions (do not decide these silently) |
| docs/PROGRESS.md | Current state. Read at session start, update at session end |

## Non-negotiable rules
1. **Inspect first, then propose, then wait.** Before any change: read the relevant docs and
   existing files, state a short plan, and wait for approval unless the ticket is trivial.
2. **One ticket at a time** from docs/BACKLOG.md. No scope creep, no "while I'm here" features.
3. **Never claim something works unless you ran it.** Paste real command output. Never fabricate
   test results. If you could not run something, say so.
4. **Architecture boundary:** `backend/app/core/` is pure Python. It must NOT import sqlalchemy,
   fastapi, httpx, supabase, or anything from app.db / app.api / app.adapters / app.services.
   A boundary test enforces this (ticket T07).
5. **Deterministic over LLM-judged.** No LLM-as-judge in the MVP.
6. **Money uses `decimal.Decimal`, never float.** Amounts are strings in JSON.
7. **Immutability:** expected_outputs, dataset_versions(+cases), workflow_versions (except
   is_baseline) and completed runs are never edited. "Edit" means "create a new version".
8. **Failures never disappear.** Execution errors, missing results and partial runs are explicit
   states. A missing result must never count as a pass. Zero evaluated cases never passes.
9. **Security:** no secrets in code, logs, DB workflow records, or reports. Provider keys come
   from server environment variables. Validate uploads (magic bytes, size), generate storage keys,
   keep storage private, authorize every project-scoped request (return 404 for other users' resources).
10. **Tests ship with the code.** Automated tests use a mocked provider. Live-provider checks are
    separate, manual, and clearly marked.
11. **Git:** work on a branch per milestone (e.g. `m1-foundation`), small commits with clear
    messages. Never push, force-push, rebase shared history, or delete files outside the task
    without asking.
12. **No invented claims** (customers, accuracy gains, savings). Report only measured numbers.
13. **Do not decide open decisions** listed in docs/DECISIONS.md. Present options and ask.

## Stack (provisional; see DECISIONS.md)
Backend: Python, FastAPI, Pydantic v2, SQLAlchemy 2.x (sync), psycopg 3, Alembic, `uv`.
DB: PostgreSQL via Docker Compose. Auth + file storage: Supabase (engine stays independent of it).
Frontend (M7): React + TypeScript + Vite. CLI (M6): Typer. CI: GitHub Actions.
Tests: pytest (real Postgres, separate test DB), Vitest later.

## Target repository layout (create folders only when a ticket needs them)
```
changeguard-ai/
├── CLAUDE.md
├── docs/                      # these context docs
├── backend/
│   ├── app/
│   │   ├── main.py, config.py
│   │   ├── api/routes/        # thin HTTP layer
│   │   ├── services/          # orchestration, DB access
│   │   ├── core/              # PURE evaluation engine (no I/O)
│   │   ├── adapters/          # llm provider, pdf text, storage
│   │   ├── db/                # engine, session, Base
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic API schemas
│   │   └── worker/            # run executor loop
│   ├── alembic/, tests/, pyproject.toml, alembic.ini
├── cli/                       # `changeguard` Typer CLI (M6)
├── frontend/                  # React + TS (M7)
├── sample_data/               # generator script + generated PDFs + ground truth
├── .github/workflows/
├── docker-compose.yml, .env.example, README.md
```

## Commands (verified in M1)
```
docker compose up -d db
cd backend && uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8001
curl http://localhost:8001/health
curl http://localhost:8001/ready
uv run pytest -v
uv run ruff check .
uv run alembic downgrade base
uv run alembic upgrade head
docker compose stop db
# verify /ready returns 503
docker compose start db
# verify /ready returns 200
```

## Workflow for every ticket
1. Read docs/PROGRESS.md and the ticket in docs/BACKLOG.md.
2. Inspect existing files; propose a plan with files to touch and tests to write.
3. Wait for approval (skip only for trivial changes).
4. Implement the smallest slice. Write tests alongside.
5. Run tests/linters. Fix failures honestly.
6. Update docs/PROGRESS.md and the Commands section if they changed.
7. Produce the final report below. Do not commit until told, unless the ticket says to.

## Final report format (every ticket)
1. Summary of what changed. 2. Files created / modified. 3. Dependencies added and why.
4. Commands executed. 5. REAL test/lint output. 6. Errors hit and how fixed.
7. Decisions needing approval. 8. Exact commands for me to verify myself.
9. Anything not done or not verified.

## Out of scope for the MVP
Multi-provider, RAG evaluation, LLM-as-judge, OCR, line items, bounding boxes, scheduling,
teams/orgs, tracing, online monitoring, PDF report export, audit_events, Redis/Celery, Kubernetes,
microservices.
