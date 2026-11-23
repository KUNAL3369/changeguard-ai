# Decisions Log

## Settled (ADR-lite)
| # | Decision | Why |
|---|---|---|
| 001 | Modular monolith | One developer, 2h/day; microservices add cost with no benefit |
| 002 | `app/core` pure Python, boundary-tested | Portfolio centerpiece; unit-testable; independent of Supabase/DB |
| 003 | Postgres-backed worker (SKIP LOCKED), no Redis/Celery | Survives restarts; minimal infra; revisit only with evidence |
| 004 | Immutable versions (expected outputs, datasets, workflows); runs are immutable | Reproducibility; history never rewritten |
| 005 | `field_specs` (evaluators, tolerances, severities) live on the dataset version | Old comparisons stay reproducible |
| 006 | Supabase Auth + private Storage; engine independent of Supabase | Reuses known tools; no custom crypto |
| 007 | Sync SQLAlchemy 2.x + psycopg 3 | Simpler to test/debug at this pace |
| 008 | Decimal for money; strings in JSON | Float rounding errors |
| 009 | Evidence = model quote + page, verified against extracted text; no bounding boxes | Honest evidence without OCR/layout complexity |
| 010 | Build order: foundation → core engine → datasets → execution → comparison → CLI/CI → UI → ship | Core demo works by ~week 4; UI can't block it |
| 011 | Synthetic generated dataset | Free ground truth; no confidentiality risk |
| 012 | Reruns create new runs; transient provider retries (max 2) inside a run | Retry cannot corrupt history |
| 013 | Health endpoints at root, API under `/api/v1` | Probe convention |
| 014 | `replay` provider (recorded outputs) powers the reproducible demo; real provider optional/manual | PROJECT_UPDATE: regression must be reproducible |
| 015 | Authentication starts at M3, after M1/M2 are reviewed | PROJECT_UPDATE execution rules |
| 016 | MVP fields exclude po_number; RAG is post-MVP | PROJECT_UPDATE |
| 017 | Python 3.12 (pinned in pyproject.toml) | psycopg-binary wheel unavailable for Python 3.14; 3.12 is stable and supported by all deps |
| 018 | PostgreSQL 16 (Docker Compose) | Mature, stable, matches production intent; pg_isready healthcheck |
| 019 | Port 8001 for uvicorn (not 8000) | Port 8000 conflicts on Windows; documented in CLAUDE.md Commands |
| 020 | Ruff for linting (configured in pyproject.toml) | Fast, replaces flake8+isort+black; enforced in CI |
| 021 | Pydantic v2 + pydantic-settings for config | Type-safe settings with .env discovery in parent dirs |
| 022 | Secret-redacting logging filter (SecretRedactingFilter) | Redacts DB URLs, passwords, secrets, Bearer tokens from all logs |
| 023 | POSTGRES_PORT default 5433 | Host port 5432 often owned by native PostgreSQL on Windows; avoids port collision |
| 024 | Dev dependency group via PEP 735 | [dependency-groups] dev in pyproject.toml ensures plain `uv sync` keeps dev tools installed |
| 025 | API error envelope format | `{"error":{"code":"string","message":"string","details":{}}}` per bundle API specification |
| 026 | Port 8001 for FastAPI server | Port 8000 conflicts on Windows development environments; README and CLAUDE.md aligned |

## OPEN — ask the developer, do not decide silently
| # | Question | Notes |
|---|---|---|
| O1 | LLM provider and model (for the real provider adapter) | Choose after M1; needed only at T25. The demo itself uses `replay`. Candidates: OpenAI, Claude, Gemini, Groq |
| O2 | Hosting platform for API/worker/frontend | Decide before M8 |
| O3 | Supabase JWT verification mode (shared secret vs JWKS) | Check the Supabase project settings and docs |
| O5 | Stale-run recovery rule (re-queue vs fail) | Decide in worker ticket (T29) |
| O6 | Max upload size (default 10 MB) | Assumption; confirm |
| O7 | PDF text library (pdfplumber vs pypdf; PyMuPDF license) | Decide in T26 |
| O8 | Exact normalization rules marked "(proposed)" in EVALUATION_ENGINE.md | Confirm in T08–T12 |
