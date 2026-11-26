# Progress Log (update at the end of every session)

## Current state
- Milestone: M2 (owner approved M1 only)
- Last completed ticket: T08 (exact + required evaluators; committed on `m2-evaluation-core`, not pushed)
- Next ticket: M2 T09 (normalized_string evaluator + tests)
- Note: PR #1 is MERGED on GitHub as true merge commit `36ab80b`; local `main` now matches `origin/main`. Unpushed local commits on `m2-evaluation-core`: docs, `6b994dc` (T07), `fea4d42` (CI), plus the T08 commit.

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
- Context folders (`changeguard-claude-code-context/`, `KICKOFF_PROMPT.md`, `changeguard-reference-research.md`) moved out of repo into parent directory on 2026-11-26

## Verified facts added 2026-11-25 (T05)
- Public GitHub remote created: `https://github.com/KUNAL3369/changeguard-ai`; default branch is `main`
- Both `main` and `m1-foundation` pushed at `ce65d1f` before the CI commit, then `m1-foundation` advanced to `af42de3`
- PR #1 opened: `https://github.com/KUNAL3369/changeguard-ai/pull/1` (`m1-foundation` → `main`)
- CI check `Lint and test` → SUCCESS in 27s; GitGuardian Security Checks → SUCCESS
- Local `uv run ruff check .` → `All checks passed!`
- Local `uv run pytest -v` → `18 passed, 2 warnings in 21.32s`
- PR #1 was merged on GitHub as a true merge commit `36ab80b`; local `main` was stale until the 2026-11-26 sync

## Verified facts added 2026-11-26 (T07)
- Owner approved M1 only; T04 was reconciled as done in `docs/BACKLOG.md`.
- Created `backend/app/core/types.py` with immutable `FieldSpec`, `FieldResult`, `Evidence`, `Severity`, `EvaluatorType`, `FailureReason`, `SEVERITY_ORDER`, and `EVALUATOR_VERSION` using Python 3.12 stdlib only.
- Created `backend/tests/test_core_types.py` and `backend/tests/test_core_boundary.py`; 10 new tests pass.
- `uv run ruff check .` → `All checks passed!`
- `uv run python -m pytest tests/test_core_types.py tests/test_core_boundary.py -v` → `10 passed, 2 warnings in 0.54s`
- `uv run pytest -v` → `28 passed, 2 warnings in 22.40s` against healthy `changeguard-db` on port 5433 in the fresh 2026-11-26 audit.
- Initial `uv run pytest` failed with `uv trampoline failed to canonicalize script path`; `uv sync --reinstall` regenerated Python entry-point launchers, after which the canonical command passed. No dependency or source changes were needed for that repair.
- Ruff required Python 3.12 `StrEnum` instead of `str, Enum` (rule `UP042`); implementation was adjusted before green.
- Core boundary test verifies no forbidden app-layer, framework, I/O, or clock-call imports in `app/core`.
- PR #1 is MERGED on GitHub. At audit time T07 was uncommitted; no push was performed.

## Verified facts added 2026-11-26 (T08)
- `uv run pytest -v` → `69 passed, 2 warnings in 18.91s` (28 existing + 41 new/changed).
- `uv run ruff check .` → `All checks passed!`
- `backend/app/core/evaluators.py` created: `evaluate_field(expected, actual, spec, *, actual_state)`; state/value contradiction raises `ValueError`; unimplemented evaluator type raises `NotImplementedError` (never a silent pass).
- `backend/app/core/types.py` extended: `ValueState` StrEnum (`present`/`absent`/`null`), `FailureReason.UNEXPECTED_VALUE` + `VALUE_MISMATCH`, `FieldResult.actual_state` (default `PRESENT`) with `__post_init__` state/value consistency guards, `expected`/`actual` widened to `object | None`.
- Boundary test extended with an AST float guard (float literals, `float()` calls, float annotations; `isinstance(x, float)` allowed per D7) plus a synthetic-violation self-test.
- `_is_empty` is not truthiness: `0` and `False` pass `required`; `""` and whitespace-only strings fail `empty`.
- `EVALUATOR_VERSION` remains `"0.1.0"` (D5); no float, no I/O, no clock in `app/core`.
- No push; one local commit for T08 only.

## Open questions / blockers
- See OPEN items in docs/DECISIONS.md
- Python version: 3.12 (decided for O4)
- PDF text library (O7): pdfplumber vs pypdf; PyMuPDF license - need to decide in T26
- Stale-run recovery rule (O5): re-queue vs fail - decide in T29
- Supabase JWT verification mode (O3): shared secret vs JWKS - check Supabase project settings
- LLM provider (O1): OpenAI, Claude, Gemini, Groq - choose after M1
- Hosting platform (O2): decide before M8
- Max upload size (O6): default 10 MB - assumption, confirm
- Context/research files were moved out of repo to the parent folder on 2026-11-26.

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

### 2026-11-25 (T05 CI)
- Added `.github/workflows/ci.yml`: Python 3.12 + uv, PostgreSQL 16 service, `ruff check .`, `pytest -v`.
- Verified locally: ruff clean; 18 tests passed.
- Created public remote `KUNAL3369/changeguard-ai`, pushed `main` and `m1-foundation`, opened PR #1.
- CI check `Lint and test` SUCCESS in 27s; GitGuardian Security Checks SUCCESS.
- PR #1 was merged on GitHub as a true merge commit `36ab80b`.

### 2026-11-26 (M1 approval + T07)
- Owner approved M1 only; reconciled T04 from pending audit to done with prior evidence.
- Implemented pure-Python core types and an AST-based import-boundary test.
- Fixed ruff `UP042` by using `StrEnum`; added `__post_init__` guard so a failed `FieldResult` always has a `failure_reason`.
- Repaired local uv Python entry-point launchers with `uv sync --reinstall` after a Windows trampoline error.
- Verified: ruff clean; 10 new tests pass; full suite 28 passed against real Postgres.
- At audit time T07 was uncommitted; PR #1 was already merged on GitHub. No push was performed.

### 2026-11-26 (T08 evaluators)
- Implemented `evaluate_field` with the approved evaluation order: state invariant → expected-null rules (D1 required-fails-missing, D2 `unexpected_value`, D3 required evaluator presence-only) → non-null expected + absent/null → `missing` → required empty/whitespace gate → dispatch (`exact` type-identity then `value_mismatch`; `required` presence-only; others `NotImplementedError`).
- Widened `FieldResult.expected`/`actual` to `object | None`; added `actual_state` and its `__post_init__` guards; added `ValueState`, `UNEXPECTED_VALUE`, `VALUE_MISMATCH`.
- Adjusted existing tests: fixture now sets `actual_state=ABSENT` where `actual=None`; added default-state assertion; narrowed the AST float guard (D7) and added its synthetic self-test.
- Documented signature and D1/D2 rules in `docs/EVALUATION_ENGINE.md`, decisions 031–036 in `docs/DECISIONS.md`, plus ownership notes for T13/T22/T25/T27 (absent-vs-null mapping, reject `required` + null expected, `parse_float=Decimal`, empty-string-to-null mapping must be explicit).
- Verified: 69 passed; ruff clean. One local commit; no push.
