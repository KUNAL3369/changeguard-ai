from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings

settings = Settings()

# Create the sync engine
# pool_pre_ping helps detect stale connections
engine = create_engine(
    settings.database_url_sync,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session,
)


def get_db():
    """Dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
