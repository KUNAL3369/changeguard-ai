import os
import subprocess

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Set test environment variables BEFORE importing app modules
os.environ["POSTGRES_USER"] = "changeguard"
os.environ["POSTGRES_PASSWORD"] = "testpassword"
os.environ["POSTGRES_DB"] = "changeguard_test"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["LOG_LEVEL"] = "DEBUG"
os.environ["MAX_UPLOAD_MB"] = "10"

# Get the backend directory path
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create test database and run migrations before tests."""
    # Create test database
    admin_engine = create_engine(
        "postgresql+psycopg://changeguard:testpassword@localhost:5432/postgres",
        isolation_level="AUTOCOMMIT",
    )
    with admin_engine.connect() as conn:
        # Terminate existing connections to test DB
        conn.execute(text("""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = 'changeguard_test' AND pid <> pg_backend_pid()
        """))
        # Drop and recreate test database
        conn.execute(text("DROP DATABASE IF EXISTS changeguard_test"))
        conn.execute(text("CREATE DATABASE changeguard_test"))
    admin_engine.dispose()

    # Run alembic migrations on test database
    env = os.environ.copy()
    env["DATABASE_URL"] = "postgresql+psycopg://changeguard:testpassword@localhost:5432/changeguard_test"
    result = subprocess.run(
        ["uv", "run", "alembic", "upgrade", "head"],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.fail(f"Alembic upgrade failed: {result.stderr}")

    yield

    # Cleanup: drop test database
    admin_engine = create_engine(
        "postgresql+psycopg://changeguard:testpassword@localhost:5432/postgres",
        isolation_level="AUTOCOMMIT",
    )
    with admin_engine.connect() as conn:
        conn.execute(text("""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = 'changeguard_test' AND pid <> pg_backend_pid()
        """))
        conn.execute(text("DROP DATABASE IF EXISTS changeguard_test"))
    admin_engine.dispose()


@pytest.fixture
def client() -> TestClient:
    """Create a test client with the test database."""
    from app.config import get_settings
    from app.main import app

    # Override the settings to use test database
    test_settings = get_settings()
    test_settings.postgres_user = "changeguard"
    test_settings.postgres_password = "testpassword"
    test_settings.postgres_db = "changeguard_test"

    # Recreate engine with test database
    test_engine = create_engine(
        test_settings.database_url_sync,
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

    app.dependency_overrides = {}
    from app.db.session import get_db as original_get_db
    app.dependency_overrides[original_get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    test_engine.dispose()


@pytest.fixture
def db_session():
    """Create a direct database session for testing."""
    from app.config import get_settings
    test_settings = get_settings()
    test_settings.postgres_user = "changeguard"
    test_settings.postgres_password = "testpassword"
    test_settings.postgres_db = "changeguard_test"

    test_engine = create_engine(
        test_settings.database_url_sync,
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
