"""
Punto de entrada de la aplicación FastAPI.

Fase 0: router de salud (/health) y CORS para el frontend.
Fase 1: router de dominio (áreas, preguntas, carreras) + validación de arranque.
Fase 2: motor de recomendación (Mahalanobis), con la matriz de covarianza
        inversa calculada una única vez al arrancar y cacheada en `app.state`.
Fase 4: `POST /test/tradicional`, primer flujo end-to-end (formulario).
Fase 9a: router de autenticación JWT (`/auth/registro`, `/auth/login`,
        `/auth/refresh`, `/auth/me`), sin tocar aún historial de intentos.
Fase 9b: `POST /test/tradicional` y `POST /test/chatbot/iniciar` asocian el
        intento a `usuario_id` cuando hay sesión activa; router de usuarios
        (`GET /usuarios/me/intentos`) expone el historial.
"""
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass

import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, chatbot, dominio, health, recomendacion, test, usuarios
from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.core.startup_checks import run_startup_checks
from app.services.recomendacion_repository import cargar_matriz_carreras
from app.services.recomendacion_service import calcular_matriz_covarianza

settings = get_settings()


@dataclass
class RecomendacionCache:
    """Todo lo que el motor de Mahalanobis necesita, calculado una sola vez."""

    carrera_ids: list[int]
    carrera_nombres: list[str]
    X: np.ndarray
    inv_cov_matrix: np.ndarray


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Chequeo obligatorio de la Fase 1 (AREAS alineado con los datasets) +
    cálculo/caché obligatorio de la Fase 2 (matriz de covarianza inversa,
    para no recalcularla en cada request a `/recomendacion`).
    """
    run_startup_checks()

    async with AsyncSessionLocal() as db:
        carrera_ids, carrera_nombres, X = await cargar_matriz_carreras(db)

    _, inv_cov_matrix = calcular_matriz_covarianza(X)

    app.state.recomendacion_cache = RecomendacionCache(
        carrera_ids=carrera_ids,
        carrera_nombres=carrera_nombres,
        X=X,
        inv_cov_matrix=inv_cov_matrix,
    )
    yield


app = FastAPI(
    title=settings.app_name,
    description="Sistema Inteligente de Orientación Vocacional - UNA Puno",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(dominio.router)
app.include_router(recomendacion.router)
app.include_router(test.router)
app.include_router(chatbot.router)
app.include_router(usuarios.router)


@app.get("/")
async def root() -> dict:
    return {"message": f"{settings.app_name} - API en funcionamiento"}
