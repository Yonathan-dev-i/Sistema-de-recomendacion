"""
Endpoint `POST /test/tradicional` (Fase 4): primer flujo completo
usable por un usuario real, de principio a fin.

El router solo orquesta:
1. Carga las preguntas reales desde PostgreSQL, agrupadas por área.
2. Delega en `test_service.procesar_respuestas_tradicional` (puro, Fase 3+4)
   la validación contra la Lógica Adaptativa y el cálculo del vector.
3. Delega en `recomendacion_service.calcular_recomendacion` (Fase 2) el Top 5,
   usando la matriz de covarianza inversa ya cacheada en `app.state`.
4. Persiste el intento (`IntentoTest`) y las respuestas efectivamente
   formuladas (`RespuestaTest`) — nunca las 34, solo las que el algoritmo
   adaptativo realmente consumió.

Fase 9b: si la petición trae un access token válido (`Authorization: Bearer`),
el intento queda asociado a `usuario_id`; si no, queda como intento de
invitado (`usuario_id` nulo), exactamente igual que antes de esta fase.
"""
import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import AREAS
from app.core.database import get_db
from app.core.deps import obtener_usuario_opcional
from app.data.loaders import cargar_areas
from app.models import EstadoIntento, IntentoTest, MetodoTest, Pregunta, RespuestaTest, Usuario
from app.schemas.test_tradicional import TestTradicionalIn, TestTradicionalOut
from app.services.recomendacion_service import calcular_recomendacion
from app.services.test_service import RespuestasInvalidasError, procesar_respuestas_tradicional

router = APIRouter(tags=["test"])

_AREAS_LABELS = {a["key"]: a["label"] for a in cargar_areas()}


async def _cargar_preguntas_por_area(db: AsyncSession) -> dict[str, list[int]]:
    result = await db.execute(select(Pregunta.id, Pregunta.area_key).order_by(Pregunta.id))
    preguntas_por_area: dict[str, list[int]] = {area: [] for area in AREAS}
    for pregunta_id, area_key in result.all():
        preguntas_por_area[area_key].append(pregunta_id)
    return preguntas_por_area


@router.post("/test/tradicional", response_model=TestTradicionalOut)
async def crear_test_tradicional(
    payload: TestTradicionalIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario | None = Depends(obtener_usuario_opcional),
) -> dict:
    preguntas_por_area = await _cargar_preguntas_por_area(db)
    respuestas_dict = {r.pregunta_id: r.respuesta for r in payload.respuestas}

    try:
        vector_usuario, _respuestas_por_area, preguntas_usadas = procesar_respuestas_tradicional(
            preguntas_por_area, respuestas_dict
        )
    except RespuestasInvalidasError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    cache = request.app.state.recomendacion_cache
    resultados = calcular_recomendacion(
        vector_usuario=vector_usuario,
        X=cache.X,
        carrera_ids=cache.carrera_ids,
        carrera_nombres=cache.carrera_nombres,
        areas=AREAS,
        inv_cov_matrix=cache.inv_cov_matrix,
        areas_labels=_AREAS_LABELS,
        top_n=5,
    )
    resultados_dict = [r.__dict__ for r in resultados]

    intento = IntentoTest(
        usuario_id=usuario.id if usuario else None,
        metodo=MetodoTest.TRADICIONAL,
        estado=EstadoIntento.COMPLETADO,
        vector_usuario=vector_usuario,
        top5_resultado=resultados_dict,
        completado_en=dt.datetime.now(dt.UTC),
    )
    db.add(intento)
    await db.flush()  # asigna intento.id sin cerrar la transacción

    for pregunta_id in preguntas_usadas:
        db.add(
            RespuestaTest(
                intento_id=intento.id,
                pregunta_id=pregunta_id,
                respuesta=respuestas_dict[pregunta_id],
            )
        )

    await db.commit()

    return {
        "test_id": intento.id,
        "vector_usuario": vector_usuario,
        "resultados": resultados_dict,
    }