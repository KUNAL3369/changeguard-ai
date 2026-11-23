# Progress Log (update at the end of every session)

## Current state
- Milestone: M1 (Foundation fixes & audit cleanup complete)
- Last completed ticket: T01–T04 foundation fixes
- Next ticket: T05 (GitHub Actions: lint + tests on PR)

## Verified facts (only things actually run and seen on 2026-11-24)
- `docker info` → Docker Desktop Server 29.7.2 active and healthy
- `docker compose config` fails with exit code 1 when `POSTGRES_PASSWORD` is UNSET or EMPTY (`set POSTGRES_PASSWORD in .env`), and succeeds when set
- `docker compose up -d db` → healthy (PostgreSQL 16, container `changeguard-db` bound to `127.0.0.1:5433:5432`)
- `uv sync` and `uv sync --frozen` succeed; dev tools (`pytest`, `ruff`) placed in `[dependency-groups] dev` remain installed
- `alembic upgrade head` works on empty DB; `downgrade base` then `upgrade head` also works cleanly against port 5433
- `uv run pytest -v` → 18 passed (11 unit tests pass even when DB is stopped; 7 DB/health integration tests pass)
- `uv run ruff check .` passes with zero warnings (`[tool.ruff.lint]` format)
- `curl http://localhost:8001/health` → 200 `{"status":"ok"}`
- `curl http://localhost:8001/ready` → 200 `{"status":"ready","checks":{"database":"ok"}}`
- After `docker compose stop db`, `curl http://localhost:8001/ready` → 503 `{"status":"not_ready","checks":{"database":"failed"}}` (clean top-level JSON, no credentials leaked) in ~4.18s
- After `docker compose start db`, `curl http://localhost:8001/ready` → 200 `{"status":"ready","checks":{"database":"ok"}}`
- Safety assertions in `conftest.py` verify test DB name ends with `_test` and differs from dev DB before create/drop
- Naming conventions test verifies constraint compilation on PostgreSQL dialect
- Context folders (`changeguard-claude-code-context/` and `KICKOFF_PROMPT.md`) moved out of repo into parent directory

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
### 2026-11-24 (Foundation Fixes & New Machine Audit)
- Fixed port collision by introducing `POSTGRES_PORT` (default 5433) in docker-compose.yml, config.py, .env.example, and tests
- Made `POSTGRES_PASSWORD` required in docker-compose.yml with `${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD in .env}`
- Switched dev dependencies to uv `[dependency-groups] dev` and updated ruff settings to `[tool.ruff.lint]`
- Tracked `backend/uv.lock` and untracked `.env`
- Made `setup_test_database` fixture in `conftest.py` non-autouse, allowing logging redaction unit tests to run with DB down
- Added safety assertions in `conftest.py` checking `_test` suffix before create/drop
- Updated `/ready` failure response to top-level `JSONResponse(status_code=503)`
- Added test for constraint naming convention compilation in `test_db.py`
- Aligned `README.md` and `CLAUDE.md` port documentation (API: 8001, DB host: 5433)
- Replaced `docs/API.md` with bundle contract and marked proposed endpoints
- Moved `changeguard-claude-code-context/` and `KICKOFF_PROMPT.md` to parent directory
- All 18 tests passing, ruff clean, health/ready probes verified live.
