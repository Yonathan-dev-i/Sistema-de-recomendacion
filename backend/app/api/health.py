"""Endpoint de salud (Fase 0): permite verificar que el backend está corriendo."""
from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict:
    """Devuelve el estado del servicio. Usado por el frontend y por CI/monitoring."""
    settings = get_settings()
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
    }
