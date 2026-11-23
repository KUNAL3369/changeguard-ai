import os
import subprocess

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import get_settings

# Get the backend directory path
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_test_db_config():
    """Get database configuration for testing from Settings or environment."""
    settings = get_settings()
    host = os.environ.get("POSTGRES_HOST", settings.postgres_host)
    port = int(os.environ.get("POSTGRES_PORT", str(settings.postgres_port)))
    user = os.environ.get("POSTGRES_USER", settings.postgres_user)
    password = os.environ.get("POSTGRES_PASSWORD", settings.postgres_password)
    dev_db = os.environ.get("POSTGRES_DB", settings.postgres_db)

    # Test database must end with _test and differ from dev_db
    test_db = os.environ.get("TEST_POSTGRES_DB", f"{dev_db}_test" if not dev_db.endswith("_test") else f"{dev_db}_custom_test")

    # Safety assertions before ANY create or drop
    assert test_db.endswith("_test"), f"Safety check failed: test DB name '{test_db}' must end with '_test'"
    assert test_db != dev_db, f"Safety check failed: test DB '{test_db}' must not be equal to dev DB '{dev_db}'"

    admin_url = f"postgresql+psycopg://{user}:{password}@{host}:{port}/postgres"
    test_db_url = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{test_db}"

    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "dev_db": dev_db,
        "test_db": test_db,
        "admin_url": admin_url,
        "test_db_url": test_db_url,
    }


@pytest.fixture(scope="session")
def setup_test_database():
    """Create test database and run migrations before tests (non-autouse)."""
    cfg = get_test_db_config()
    test_db = cfg["test_db"]
    dev_db = cfg["dev_db"]

    assert test_db.endswith("_test"), f"Safety check failed: test DB '{test_db}' must end with '_test'"
    assert test_db != dev_db, f"Safety check failed: test DB '{test_db}' must differ from dev DB '{dev_db}'"

    # Create test database via admin connection
    admin_engine = create_engine(
        cfg["admin_url"],
        isolation_level="AUTOCOMMIT",
    )
    with admin_engine.connect() as conn:
        # Terminate existing connections to test DB
        conn.execute(text(f"""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = '{test_db}' AND pid <> pg_backend_pid()
        """))
        # Drop and recreate test database
        conn.execute(text(f"DROP DATABASE IF EXISTS {test_db}"))
        conn.execute(text(f"CREATE DATABASE {test_db}"))
    admin_engine.dispose()

    # Run alembic migrations on test database
    env = os.environ.copy()
    env["POSTGRES_HOST"] = cfg["host"]
    env["POSTGRES_PORT"] = str(cfg["port"])
    env["POSTGRES_USER"] = cfg["user"]
    env["POSTGRES_PASSWORD"] = cfg["password"]
    env["POSTGRES_DB"] = test_db
    env["DATABASE_URL"] = cfg["test_db_url"]

    result = subprocess.run(
        ["uv", "run", "alembic", "upgrade", "head"],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.fail(f"Alembic upgrade failed: {result.stderr}")

    yield cfg

    # Cleanup: drop test database
    assert test_db.endswith("_test"), f"Safety check failed: test DB '{test_db}' must end with '_test'"
    assert test_db != dev_db, f"Safety check failed: test DB '{test_db}' must differ from dev DB '{dev_db}'"

    admin_engine = create_engine(
        cfg["admin_url"],
        isolation_level="AUTOCOMMIT",
    )
    with admin_engine.connect() as conn:
        conn.execute(text(f"""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = '{test_db}' AND pid <> pg_backend_pid()
        """))
        conn.execute(text(f"DROP DATABASE IF EXISTS {test_db}"))
    admin_engine.dispose()


@pytest.fixture
def client(setup_test_database) -> TestClient:
    """Create a test client with the test database."""
    from app.config import get_settings
    from app.db.session import get_db as original_get_db
    from app.main import app

    cfg = setup_test_database
    test_settings = get_settings()
    test_settings.postgres_host = cfg["host"]
    test_settings.postgres_port = cfg["port"]
    test_settings.postgres_user = cfg["user"]
    test_settings.postgres_password = cfg["password"]
    test_settings.postgres_db = cfg["test_db"]

    test_engine = create_engine(
        cfg["test_db_url"],
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )
    TestSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )

    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[original_get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    test_engine.dispose()


@pytest.fixture
def db_session(setup_test_database):
    """Create a direct database session for testing."""
    cfg = setup_test_database
    test_engine = create_engine(
        cfg["test_db_url"],
        pool_pre_ping=True,
    )
    TestSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()
        test_engine.dispose()
