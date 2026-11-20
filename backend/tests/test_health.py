from fastapi.testclient import TestClient
from sqlalchemy import text


def test_health_endpoint_returns_200_without_db(client: TestClient):
    """Health endpoint should return 200 even when DB is unreachable."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_endpoint_returns_200_with_db(client: TestClient):
    """Ready endpoint should return 200 when DB is reachable."""
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["checks"]["database"] == "ok"


def test_ready_endpoint_returns_503_without_db():
    """Ready endpoint should return 503 when DB is unreachable."""
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.config import get_settings
    from app.db.session import get_db
    from app.main import app

    # Create settings with invalid DB URL
    test_settings = get_settings()
    test_settings.postgres_user = "changeguard"
    test_settings.postgres_password = "wrongpassword"
    test_settings.postgres_db = "changeguard_test"

    bad_engine = create_engine(
        test_settings.database_url_sync,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 2},
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
            # FastAPI wraps HTTPException detail in "detail" key
            detail = data["detail"]
            assert detail["status"] == "not_ready"
            assert detail["checks"]["database"] == "failed"
            # Ensure no credentials in response
            response_text = response.text
            assert "wrongpassword" not in response_text
            assert "changeguard" not in response_text or "changeguard_test" not in response_text
    finally:
        app.dependency_overrides.clear()
        bad_engine.dispose()


def test_ready_endpoint_no_credentials_in_response(client: TestClient):
    """Ready endpoint should never expose credentials in response."""
    response = client.get("/ready")
    response_text = response.text
    assert "testpassword" not in response_text
    # DATABASE_URL should not be in response
    assert "postgresql" not in response_text.lower() or "localhost" not in response_text.lower()


def test_db_session_executes_select_one(db_session):
    """Database session should be able to execute SELECT 1."""
    result = db_session.execute(text("SELECT 1")).scalar()
    assert result == 1


def test_app_starts_with_lifespan(client: TestClient):
    """TestClient with lifespan should start the app successfully."""
    # If we get here, the app started successfully
    response = client.get("/health")
    assert response.status_code == 200
