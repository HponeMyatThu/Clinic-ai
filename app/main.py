"""GCMS Clinical AI Backend — FastAPI Application Factory."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.middleware.error_handler import register_error_handlers
from app.api.middleware.rate_limiter import RateLimiterMiddleware
from app.api.middleware.request_id import RequestIdMiddleware
from app.api.v1.router import api_v1_router
from app.config import get_settings
from app.db.session import engine
from app.models.base import Base
import app.models  # noqa: F401
from sqlalchemy import text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("gcms.main")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle startup and shutdown hooks."""
    logger.info(f"Starting {settings.app_name} (env: {settings.app_env})")
    logger.info(f"Ollama base URL: {settings.ollama_base_url}, model: {settings.ollama_model}")

    # Ensure PostgreSQL extensions and tables exist on startup
    try:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
            await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
            await conn.run_sync(Base.metadata.create_all)
        logger.info("PostgreSQL extensions and tables verified.")
    except Exception as exc:
        logger.warning(f"Database table verification on startup encountered: {exc}")

    yield
    logger.info("Shutting down GCMS Clinical AI Backend")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    app = FastAPI(
        title="GCMS Clinical AI Backend",
        description=(
            "Secure, modular clinical AI consultation backend providing local Ollama differential diagnosis "
            "and medication suggestions grounded in licensed SNOMED CT and Singapore Drug Dictionary (SDD)."
        ),
        version="1.2.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # 1. Register global exception handlers
    register_error_handlers(app)

    # 2. CORS configuration (allowing React frontend)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Restrict to trusted CMS React domain in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 3. Rate limiting middleware
    app.add_middleware(
        RateLimiterMiddleware,
        max_requests=settings.rate_limit_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )

    # 4. Request ID tracing middleware
    app.add_middleware(RequestIdMiddleware)

    # 5. Mount API routes
    app.include_router(api_v1_router)

    @app.get("/", tags=["Root"])
    async def root():
        return {
            "name": "GCMS Clinical AI Backend",
            "version": "1.2.0",
            "status": "operational",
            "documentation": "/docs",
        }

    return app


app = create_app()

