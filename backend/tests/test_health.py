from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.db.session import get_db
from app.main import app


def test_health_endpoint_returns_200_without_db():
    """Health endpoint should return 200 even when DB is unreachable."""
    with TestClient(app) as test_client:
        response = test_client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


def test_ready_endpoint_returns_200_with_db(client: TestClient):
    """Ready endpoint should return 200 when DB is reachable."""
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "ready", "checks": {"database": "ok"}}


def test_ready_endpoint_returns_503_without_db():
    """Ready endpoint should return 503 with clean top-level JSON when DB is unreachable.
    Uses a real 503 by pointing the session at an unreachable port with short timeout.
    """
    test_settings = get_settings()

    # Point at an unreachable port (e.g. 59999) with 1s timeout to generate a real connection failure
    unreachable_url = (
        f"postgresql+psycopg://{test_settings.postgres_user}:{test_settings.postgres_password}"
        f"@{test_settings.postgres_host}:59999/{test_settings.postgres_db}"
    )

    bad_engine = create_engine(
        unreachable_url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 1},
    )
    BadSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=bad_engine,
    )

    def bad_get_db():
        db = BadSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = bad_get_db

    try:
        with TestClient(app) as test_client:
            response = test_client.get("/ready")
            assert response.status_code == 503
            data = response.json()

            # Must be top-level JSON, not wrapped in detail
            assert data == {"status": "not_ready", "checks": {"database": "failed"}}
            assert "detail" not in data

            # Assert INDIVIDUALLY that none of these forbidden strings appear in the response:
            # the password, the DB user, the host, "postgresql", "psycopg", "Traceback", "OperationalError"
            response_text = response.text
            forbidden_strings = [
                test_settings.postgres_password,
                test_settings.postgres_user,
                test_settings.postgres_host,
                "postgresql",
                "psycopg",
                "Traceback",
                "OperationalError",
            ]
            for forbidden in forbidden_strings:
                assert forbidden not in response_text, f"Forbidden string '{forbidden}' leaked in 503 response"
    finally:
        app.dependency_overrides.clear()
        bad_engine.dispose()


def test_ready_endpoint_no_credentials_in_response(client: TestClient):
    """Ready endpoint should never expose credentials or internal URLs in a 200 response."""
    test_settings = get_settings()
    response = client.get("/ready")
    assert response.status_code == 200
    response_text = response.text

    forbidden_strings = [
        test_settings.postgres_password,
        test_settings.postgres_user,
        test_settings.postgres_host,
        "postgresql",
        "psycopg",
    ]
    for forbidden in forbidden_strings:
        assert forbidden not in response_text, f"Forbidden string '{forbidden}' leaked in 200 response"


def test_app_starts_with_lifespan():
    """TestClient with lifespan should start the app successfully without database access."""
    with TestClient(app) as test_client:
        response = test_client.get("/health")
        assert response.status_code == 200
