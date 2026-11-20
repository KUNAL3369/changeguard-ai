# Progress Log (update at the end of every session)

## Current state
- Milestone: M1 (Foundation in progress)
- Last completed ticket: T03
- Next ticket: T04 (Pytest setup with separate test DB fixture — already done)

## Verified facts (only things actually run and seen)
- `uv sync` succeeds
- `docker compose up -d db` → healthy (PostgreSQL 16)
- `alembic upgrade head` works on empty DB; `downgrade base` then `upgrade head` also works; `alembic_version` exists
- `curl localhost:8001/health` → 200 `{"status":"ok"}`
- `curl localhost:8001/ready` → 200 `{"status":"ready","checks":{"database":"ok"}}`
- After `docker compose stop db`, `/ready` → 503 within ~3s; after start, 200 again
- `uv run pytest` passes (15 tests)
- `uv run ruff check .` passes (all checks passed)
- README steps work from a clean clone
- Secret redaction in logging works: no URL/password in logs (tested)

## Open questions / blockers
- See OPEN items in docs/DECISIONS.md
- Python version: 3.12 (decided for O4)
- PDF text library (O7): pdfplumber vs pypdf; PyMuPDF license - need to decide in T26
- Stale-run recovery rule (O5): re-queue vs fail - decide in T29
- Supabase JWT verification mode (O3): shared secret vs JWKS - check Supabase project settings
- LLM provider (O1): OpenAI, Claude, Gemini, Groq - choose after M1
- Hosting platform (O2): decide before M8
- Max upload size (O6): default 10 MB - assumption, confirm

## Session log
### 2026-11-20
- Ticket: T01–T02 (Foundation)
- Done:
  - Created docker-compose.yml with PostgreSQL 16, named volume, healthcheck, port bound to 127.0.0.1
  - Created .env.example with required variables (no default password)
  - Created .gitignore
  - Created backend/pyproject.toml with uv project (Python 3.12, deps: fastapi, uvicorn, sqlalchemy, psycopg, pydantic, pydantic-settings, alembic, python-dotenv, pytest, httpx, ruff)
  - Created backend/alembic.ini, env.py, script.py.mako
  - Created backend/app/db/base.py (DeclarativeBase with constraint naming convention)
  - Created backend/app/db/session.py (engine, sessionmaker, get_db dependency)
  - Created backend/app/config.py (Settings with pydantic-settings, finds .env in parent dir)
  - Created backend/app/main.py (FastAPI app with lifespan, health router)
  - Created backend/app/api/routes/health.py (GET /health, GET /ready with DB check)
  - Created backend/tests/conftest.py (test DB fixture with separate changeguard_test DB)
  - Created backend/tests/test_health.py (7 tests: health, ready with/without DB, no credentials, session, lifespan)
  - Created backend/tests/test_db.py (session executes SELECT 1)
  - Created README.md with exact local run steps
  - Verified all acceptance criteria
- Evidence (commands + results):
  - `uv sync` → success
  - `docker compose up -d db` → healthy
  - `uv run alembic upgrade head` → success
  - `uv run alembic downgrade base` → success
  - `uv run alembic upgrade head` → success
  - `curl /health` → 200 `{"status":"ok"}`
  - `curl /ready` → 200 `{"status":"ready","checks":{"database":"ok"}}`
  - `docker compose stop db` + `curl /ready` → 503 `{"detail":{"status":"not_ready","checks":{"database":"failed"}}}`
  - `docker compose start db` + `curl /ready` → 200 `{"status":"ready","checks":{"database":"ok"}}`
  - `uv run pytest -v` → 7 passed
  - `uv run ruff check .` → All checks passed
- Decisions made (add to DECISIONS.md):
  - Python version: 3.12 (O4 resolved)
  - PostgreSQL version: 16 (pinned)

### 2026-11-20 (continued)
- Ticket: T03 (Typed settings, secret-redaction in logging)
- Done:
  - Created `backend/app/logging_config.py` with `SecretRedactingFilter` that redacts:
    - Database URLs (postgresql://, postgresql+psycopg://)
    - Password/secret key patterns (password=, secret_key=, api_key=, etc.)
    - Bearer tokens (JWT)
    - Generic key=value patterns with secret-like values
  - Updated `backend/app/main.py` to use `setup_logging()` in lifespan with settings.log_level
  - Created `backend/tests/test_logging_redaction.py` with 8 tests verifying redaction of:
    - Database URLs with passwords
    - psycopg URLs
    - Password key=value
    - Secret keys
    - Bearer tokens
    - Secrets in log args
    - Full logging output capture
    - Realistic access log scenarios
- Evidence (commands + results):
  - `uv run pytest tests/test_logging_redaction.py -v` → 8 passed
  - `uv run pytest -v` → 15 passed (all tests)
  - `uv run ruff check .` → All checks passed
  - Server startup logs show no secrets (verified)
- Decisions made: None new
- Next: T04 (Pytest setup — already complete, effectively done)