"""Health check endpoints for container and service readiness."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.ollama.client import OllamaClient
from app.ai.ollama.model_config import OllamaModelConfig
from app.config import get_settings
from app.db.session import get_db
from app.schemas.common import HealthCheckResponse

router = APIRouter(tags=["System Health"])
settings = get_settings()


@router.get("/health", response_model=HealthCheckResponse)
async def check_health(db: AsyncSession = Depends(get_db)) -> HealthCheckResponse:
    """Service readiness probe checking database and local Ollama connectivity."""
    services: dict[str, str] = {}

    # 1. Database check
    try:
        await db.execute(text("SELECT 1"))
        services["database"] = "healthy"
    except Exception as exc:
        services["database"] = f"unhealthy: {str(exc)}"

    # 2. Ollama check
    try:
        ollama_config = OllamaModelConfig.from_settings(settings)
        ollama_client = OllamaClient(ollama_config)
        is_ollama_healthy = await ollama_client.health_check()
        await ollama_client.close()
        services["ollama"] = "healthy" if is_ollama_healthy else "unreachable"
    except Exception as exc:
        services["ollama"] = f"unreachable: {str(exc)}"

    # 3. Overall status
    overall = "ok" if services.get("database") == "healthy" else "degraded"

    return HealthCheckResponse(
        status=overall,
        version="0.1.0",
        services=services,
    )

