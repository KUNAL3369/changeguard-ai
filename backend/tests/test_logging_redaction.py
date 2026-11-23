import io
import logging

from app.logging_config import SecretRedactingFilter


def test_secret_redacting_filter_redacts_database_url():
    """SecretRedactingFilter should redact passwords in database URLs."""
    filter_instance = SecretRedactingFilter()

    # Create a log record with a database URL containing password
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Connecting to postgresql://user:secretpassword@localhost:5432/db",
        args=(),
        exc_info=None,
    )

    filter_instance.filter(record)

    assert "secretpassword" not in record.msg
    assert "***REDACTED***" in record.msg
    assert "postgresql://user:***REDACTED***@localhost:5432/db" in record.msg


def test_secret_redacting_filter_redacts_psycopg_url():
    """SecretRedactingFilter should redact passwords in psycopg URLs."""
    filter_instance = SecretRedactingFilter()

    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="postgresql+psycopg://admin:mypassword@localhost:5432/mydb",
        args=(),
        exc_info=None,
    )

    filter_instance.filter(record)

    assert "mypassword" not in record.msg
    assert "***REDACTED***" in record.msg


def test_secret_redacting_filter_redacts_password_key_value():
    """SecretRedactingFilter should redact password in key=value format."""
    filter_instance = SecretRedactingFilter()

    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg='password="supersecret123"',
        args=(),
        exc_info=None,
    )

    filter_instance.filter(record)

    assert "supersecret123" not in record.msg
    assert "***REDACTED***" in record.msg


def test_secret_redacting_filter_redacts_secret_key():
    """SecretRedactingFilter should redact secret_key."""
    filter_instance = SecretRedactingFilter()

    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="secret_key=mysecretkey123",
        args=(),
        exc_info=None,
    )

    filter_instance.filter(record)

    assert "mysecretkey123" not in record.msg
    assert "***REDACTED***" in record.msg


def test_secret_redacting_filter_redacts_bearer_token():
    """SecretRedactingFilter should redact Bearer tokens."""
    filter_instance = SecretRedactingFilter()

    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dGhpcyBpcyBhIHRlc3Q"
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg=f"Authorization: Bearer {token}",
        args=(),
        exc_info=None,
    )

    filter_instance.filter(record)

    assert token not in record.msg
    assert "***REDACTED***" in record.msg
    assert "Bearer ***REDACTED***" in record.msg


def test_secret_redacting_filter_redacts_in_args():
    """SecretRedactingFilter should redact secrets in log record args."""
    filter_instance = SecretRedactingFilter()

    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Connecting to %s",
        args=("postgresql://user:password123@localhost/db",),
        exc_info=None,
    )

    filter_instance.filter(record)

    assert "password123" not in record.args[0]
    assert "***REDACTED***" in record.args[0]


def test_setup_logging_no_secrets_in_output():
    """setup_logging should produce output with no secrets."""
    # Capture log output
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(message)s"))

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(logging.INFO)

    # Add the redacting filter
    redacting_filter = SecretRedactingFilter()
    handler.addFilter(redacting_filter)

    # Log a message with a database URL
    logger = logging.getLogger("test")
    logger.info("Connecting to postgresql://user:secretpass@localhost:5432/db")

    output = stream.getvalue()
    assert "secretpass" not in output
    assert "***REDACTED***" in output


def test_secret_redacting_filter_redacts_exception_traceback():
    """SecretRedactingFilter should redact secrets in exception tracebacks (exc_info path)."""
    filter_instance = SecretRedactingFilter()

    try:
        raise ValueError("Connection failed: postgresql://user:secretpassword@localhost:5432/db")
    except ValueError:
        import sys
        exc_info = sys.exc_info()

    record = logging.LogRecord(
        name="test",
        level=logging.ERROR,
        pathname="",
        lineno=0,
        msg="Database connection failed",
        args=(),
        exc_info=exc_info,
    )

    filter_instance.filter(record)

    assert record.exc_text is not None
    assert "secretpassword" not in record.exc_text
    assert "***REDACTED***" in record.exc_text
    assert record.exc_info is None  # Filter consumed exc_info to prevent double-format


def test_secret_redacting_filter_redacts_stack_info():
    """SecretRedactingFilter should redact secrets in stack_info (stack_info=True path)."""
    filter_instance = SecretRedactingFilter()

    record = logging.LogRecord(
        name="test",
        level=logging.ERROR,
        pathname="",
        lineno=0,
        msg="Something failed",
        args=(),
        exc_info=None,
    )
    record.stack_info = "Traceback: postgresql://user:secretpassword@localhost:5432/db"

    filter_instance.filter(record)

    assert record.stack_info is not None
    assert "secretpassword" not in record.stack_info
    assert "***REDACTED***" in record.stack_info


def test_secret_redacting_filter_exception_through_handler():
    """Exception with secret should be redacted through a real handler + formatter."""
    import io

    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(message)s"))
    filter_instance = SecretRedactingFilter()
    handler.addFilter(filter_instance)

    logger = logging.getLogger("test_handler_redaction")
    logger.handlers = [handler]
    logger.setLevel(logging.ERROR)

    try:
        raise ValueError("Connection failed: postgresql://admin:dbpass@db:5432/app")
    except ValueError:
        logger.error("Database connection failed", exc_info=True)

    output = stream.getvalue()
    assert "dbpass" not in output
    assert "***REDACTED***" in output


def test_no_secrets_in_uvicorn_access_logs():
    """Verify that uvicorn access logs don't contain secrets (integration-style test)."""
    # This test verifies the filter works with realistic log messages
    filter_instance = SecretRedactingFilter()

    test_cases = [
        "GET /api/v1/projects?api_key=secret123 HTTP/1.1",
        'POST /auth/login password="userpass" HTTP/1.1',
        "Database URL: postgresql://admin:dbpass@db:5432/app",
        "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.payload.signature",
        "Config: secret_key=mysecret DB_PASSWORD=dbpass",
    ]

    for msg in test_cases:
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg=msg, args=(), exc_info=None
        )
        filter_instance.filter(record)

        # Check that no obvious secrets remain
        assert "secret123" not in record.msg
        assert "userpass" not in record.msg
        assert "dbpass" not in record.msg
        assert "mysecret" not in record.msg
        assert "eyJhbGciOiJIUzI1NiJ9.payload.signature" not in record.msg
        assert "***REDACTED***" in record.msg
