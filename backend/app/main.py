import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.db.session import engine

# Configure logging to not print sensitive data
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

# Ensure SQLAlchemy doesn't log SQL with parameters by default
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown
    engine.dispose()


app = FastAPI(
    title="ChangeGuard AI",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Health endpoints at root level (per ARCHITECTURE.md decision 013)
app.include_router(health_router)

# API v1 will be mounted here later
# app.include_router(api_v1_router, prefix="/api/v1")
