# ChangeGuard AI

Release-readiness tool for AI document-extraction workflows (invoices first).
Replay → Evaluate → Compare → Explain → Decide.

## Quick Start (Local Development)

### Prerequisites
- Docker & Docker Compose
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Git

### Setup

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd changeguard-ai

# 2. Copy environment template and fill in values
cp .env.example .env
# Edit .env with your values (required: POSTGRES_PASSWORD, SECRET_KEY)

# 3. Start PostgreSQL
docker compose up -d db

# 4. Install dependencies
cd backend
uv sync

# 5. Run database migrations
uv run alembic upgrade head

# 6. Start the API server (port 8001 avoids port 8000 conflicts on Windows)
uv run uvicorn app.main:app --reload --port 8001

# 7. Verify health endpoints (in another terminal)
curl.exe http://localhost:8001/health
# {"status":"ok"}

curl.exe http://localhost:8001/ready
# {"status":"ready","checks":{"database":"ok"}}

# 8. Run tests
uv run pytest -v
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `POSTGRES_USER` | Yes | PostgreSQL username |
| `POSTGRES_PASSWORD` | Yes | PostgreSQL password (no default) |
| `POSTGRES_DB` | Yes | PostgreSQL database name |
| `POSTGRES_HOST` | No | PostgreSQL host (default: localhost) |
| `POSTGRES_PORT` | No | PostgreSQL host port (default: 5433, avoids native port 5432 collision) |
| `SECRET_KEY` | Yes | Application secret key (min 32 chars) |
| `LOG_LEVEL` | No | Log level (default: INFO) |
| `MAX_UPLOAD_MB` | No | Max upload size in MB (default: 10) |

### Project Structure

```
changeguard-ai/
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
├── CLAUDE.md
├── docs/
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   ├── DECISIONS.md
│   ├── BACKLOG.md
│   ├── PROGRESS.md
│   ├── DATA_MODEL.md
│   ├── API.md
│   ├── EVALUATION_ENGINE.md
│   └── SAMPLE_DATA.md
└── backend/
    ├── pyproject.toml
    ├── alembic.ini
    ├── alembic/
    │   ├── env.py
    │   ├── script.py.mako
    │   └── versions/
    ├── app/
    │   ├── __init__.py
    │   ├── main.py
    │   ├── config.py
    │   ├── api/
    │   │   ├── __init__.py
    │   │   └── routes/
    │   │       ├── __init__.py
    │   │       └── health.py
    │   ├── db/
    │   │   ├── __init__.py
    │   │   ├── base.py
    │   │   └── session.py
    │   └── (core/, adapters/, models/, schemas/, services/, worker/ - created later)
    └── tests/
        ├── __init__.py
        ├── conftest.py
        ├── test_health.py
        └── test_db.py
```

### Commands Reference

```bash
# Start database
docker compose up -d db

# Stop database
docker compose stop db

# View database logs
docker compose logs db

# Run migrations
cd backend && uv run alembic upgrade head

# Create new migration
cd backend && uv run alembic revision --autogenerate -m "description"

# Downgrade one revision
cd backend && uv run alembic downgrade -1

# Run server
cd backend && uv run uvicorn app.main:app --reload

# Run tests
cd backend && uv run pytest -v

# Lint
cd backend && uv run ruff check .

# Format
cd backend && uv run ruff format .
```

### Health Endpoints

- `GET /health` — Liveness probe (200 OK, no DB check)
- `GET /ready` — Readiness probe (200 OK with DB, 503 without DB)

### API Documentation

- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

## Architecture Overview

Modular monolith with clear layer separation:

- **API Routes** (`app/api/routes/`) — Thin HTTP layer, validation, delegation
- **Services** (`app/services/`) — Orchestration, DB access (later)
- **Core** (`app/core/`) — Pure Python evaluation engine, no I/O (later)
- **Adapters** (`app/adapters/`) — External I/O: LLM, PDF, Storage (later)
- **DB** (`app/db/`) — SQLAlchemy models, Alembic migrations
- **Worker** (`app/worker/`) — Background run executor (later)

## Development Notes

- Python 3.12+
- Sync SQLAlchemy 2.x + psycopg 3 (no async)
- Pydantic v2 for settings and schemas
- Ruff for linting/formatting
- pytest with real PostgreSQL test database
- No hardcoded secrets; `.env` is gitignored

## License

MIT (or your choice)