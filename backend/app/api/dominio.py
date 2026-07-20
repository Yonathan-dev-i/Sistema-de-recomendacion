"""
Endpoints de solo lectura de la Fase 1: exponen preguntas, áreas y carreras
directamente desde PostgreSQL (no mockeados, no leídos de los JSON/CSV en
tiempo de request — esos archivos solo alimentan el seed inicial).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import AREAS
from app.core.database import get_db
from app.models import Area, Carrera, Pregunta
from app.schemas.lectura import (
    AreaOut,
    CarreraDetalleOut,
    CarreraResumenOut,
    PreguntaOut,
)

router = APIRouter(tags=["dominio"])


@router.get("/areas", response_model=list[AreaOut])
async def listar_areas(db: AsyncSession = Depends(get_db)) -> list[Area]:
    """Devuelve las 17 áreas en su orden fijo (columna `orden`)."""
    result = await db.execute(select(Area).order_by(Area.orden))
    return list(result.scalars().all())


@router.get("/preguntas", response_model=list[PreguntaOut])
async def listar_preguntas(db: AsyncSession = Depends(get_db)) -> list[dict]:
    """Devuelve las 85 preguntas del banco, ordenadas por id."""
    result = await db.execute(select(Pregunta).order_by(Pregunta.id))
    preguntas = result.scalars().all()
    return [{"id": p.id, "area": p.area_key, "texto": p.texto} for p in preguntas]


@router.get("/carreras", response_model=list[CarreraResumenOut])
async def listar_carreras(db: AsyncSession = Depends(get_db)) -> list[Carrera]:
    """Devuelve el listado (resumido) de las 37 carreras."""
    result = await db.execute(select(Carrera).order_by(Carrera.nombre))
    return list(result.scalars().all())


@router.get("/carrera/{carrera_id}", response_model=CarreraDetalleOut)
async def obtener_carrera(
    carrera_id: int, db: AsyncSession = Depends(get_db)
) -> dict:
    """Devuelve el detalle de una carrera, incluyendo su perfil de 17 áreas."""
    result = await db.execute(
        select(Carrera)
        .options(selectinload(Carrera.puntajes))
        .where(Carrera.id == carrera_id)
    )
    carrera = result.scalar_one_or_none()
    if carrera is None:
        raise HTTPException(status_code=404, detail="Carrera no encontrada")

    perfil = dict(zip(AREAS, carrera.vector_por_area(AREAS), strict=True))
    return {
        "id": carrera.id,
        "nombre": carrera.nombre,
        "facultad": carrera.facultad,
        "perfil_areas": perfil,
    }
