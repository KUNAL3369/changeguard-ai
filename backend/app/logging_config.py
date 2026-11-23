import logging
import re
import traceback
from re import Pattern

# Patterns for sensitive data that should be redacted
SENSITIVE_PATTERNS: list[Pattern[str]] = [
    # Database URLs with passwords
    re.compile(r"(postgresql://[^:]+:)[^@]+(@)"),
    re.compile(r"(postgresql\+psycopg://[^:]+:)[^@]+(@)"),
    # Generic password patterns
    re.compile(r"(password[\"']?\s*[:=]\s*[\"']?)[^\"'\s]+", re.IGNORECASE),
    re.compile(r"(pwd[\"']?\s*[:=]\s*[\"']?)[^\"'\s]+", re.IGNORECASE),
    # Secret key patterns
    re.compile(r"(secret[\"']?\s*[:=]\s*[\"']?)[^\"'\s]+", re.IGNORECASE),
    re.compile(r"(api[_-]?key[\"']?\s*[:=]\s*[\"']?)[^\"'\s]+", re.IGNORECASE),
    # JWT tokens
    re.compile(r"(Bearer\s+)[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+"),
    # Generic key=value patterns where value looks like a secret
    re.compile(r"([a-z_]*key[a-z_]*\s*[:=]\s*)[^\"'\s]{8,}", re.IGNORECASE),
]


class SecretRedactingFilter(logging.Filter):
    """Logging filter that redacts sensitive information from log records."""

    def __init__(self, extra_secrets: list[str] | None = None):
        super().__init__()
        self.extra_secrets = extra_secrets or []

    def filter(self, record: logging.LogRecord) -> bool:
        # Redact in the main message
        if isinstance(record.msg, str):
            record.msg = self._redact(record.msg)

        # Redact in args if they are strings
        if record.args:
            new_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    new_args.append(self._redact(arg))
                else:
                    new_args.append(arg)
            record.args = tuple(new_args)

        # Redact in exception info (exc_info path): secrets can leak into
        # tracebacks when an exception is logged with exc_info=True.
        if record.exc_info:
            exc_text = "".join(traceback.format_exception(*record.exc_info))
            record.exc_text = self._redact(exc_text)
            record.exc_info = None  # Prevent formatter from double-formatting

        # Redact in stack_info: secrets can leak into stack traces.
        if record.stack_info:
            record.stack_info = self._redact(record.stack_info)

        return True

    def _redact(self, text: str) -> str:
        """Redact sensitive patterns and known secret values in text."""
        result = text
        for pattern in SENSITIVE_PATTERNS:
            result = pattern.sub(
                r"\1***REDACTED***\2" if pattern.groups >= 2 else r"\1***REDACTED***",
                result,
            )
        # Redact actual secret values loaded from settings (e.g. SECRET_KEY, DB password).
        for secret in self.extra_secrets:
            if secret and len(secret) >= 4:
                result = result.replace(secret, "***REDACTED***")
        return result


def setup_logging(log_level: str = "INFO") -> None:
    """Configure application logging with secret redaction."""
    from app.config import get_settings

    settings = get_settings()
    redacting_filter = SecretRedactingFilter(
        extra_secrets=[
            settings.secret_key,
            settings.postgres_password,
        ]
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler with filter
    handler = logging.StreamHandler()
    handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    handler.addFilter(redacting_filter)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    )
    root_logger.addHandler(handler)

    # Ensure SQLAlchemy doesn't log SQL with parameters
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    # Also add filter to sqlalchemy loggers
    for logger_name in ["sqlalchemy.engine", "sqlalchemy.pool"]:
        logger = logging.getLogger(logger_name)
        logger.addFilter(redacting_filter)

    # Also add filter to uvicorn loggers so access logs are redacted.
    for logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error"]:
        logger = logging.getLogger(logger_name)
        logger.addFilter(redacting_filter)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the application's configuration."""
    return logging.getLogger(name)
