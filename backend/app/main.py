from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.config import get_settings
from app.db.session import engine
from app.logging_config import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: configure logging with secret redaction
    settings = get_settings()
    setup_logging(settings.log_level)
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
