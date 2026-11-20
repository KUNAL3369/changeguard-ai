import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/health")
def health_check():
    """Liveness probe - does not check database."""
    return {"status": "ok"}


@router.get("/ready")
def readiness_check(db: Session = Depends(get_db)):
    """Readiness probe - checks database connectivity."""
    try:
        # Short timeout for fast failure detection
        logger.info("Executing readiness check query")
        result = db.execute(text("SELECT 1"))
        logger.info("Query result: %s", result.scalar())
        return {"status": "ready", "checks": {"database": "ok"}}
    except Exception as e:
        logger.warning("Database readiness check failed: %s: %s", type(e).__name__, e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not_ready", "checks": {"database": "failed"}},
        ) from None
