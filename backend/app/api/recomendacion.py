"""
Endpoint `POST /recomendacion` (Fase 2): recibe un vector de usuario de prueba
(17 valores) y devuelve el Top 5 de carreras calculado con Mahalanobis.

El router solo orquesta: toma la matriz `X`, ids, nombres e inversa de
covarianza ya cacheados en `app.state` (calculados una sola vez al arranque,
ver `app/main.py`) y delega el cálculo puro a `recomendacion_service`.
"""
from fastapi import APIRouter, Request

from app.core.constants import AREAS
from app.data.loaders import cargar_areas
from app.schemas.recomendacion import RecomendacionOut, VectorUsuarioIn
from app.services.recomendacion_service import calcular_recomendacion

router = APIRouter(tags=["recomendacion"])

_AREAS_LABELS = {a["key"]: a["label"] for a in cargar_areas()}


@router.post("/recomendacion", response_model=RecomendacionOut)
async def obtener_recomendacion(payload: VectorUsuarioIn, request: Request) -> dict:
    cache = request.app.state.recomendacion_cache

    resultados = calcular_recomendacion(
        vector_usuario=payload.vector_usuario,
        X=cache.X,
        carrera_ids=cache.carrera_ids,
        carrera_nombres=cache.carrera_nombres,
        areas=AREAS,
        inv_cov_matrix=cache.inv_cov_matrix,
        areas_labels=_AREAS_LABELS,
        top_n=5,
    )

    return {
        "vector_usuario": payload.vector_usuario,
        "resultados": [r.__dict__ for r in resultados],
    }
