"""
Repositorio de acceso a datos para el motor de recomendación.

Aísla la única consulta a PostgreSQL que necesita el motor de Mahalanobis
(cargar la matriz de perfiles de las 37 carreras) del cálculo puro en
`recomendacion_service.py`. Se llama una sola vez al arranque (ver
`app/main.py` → `lifespan`) y el resultado se cachea en `app.state`.
"""
import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import AREAS
from app.models import Carrera


async def cargar_matriz_carreras(
    db: AsyncSession,
) -> tuple[list[int], list[str], np.ndarray]:
    """
    Devuelve `(carrera_ids, carrera_nombres, X)`:
    - `carrera_ids` / `carrera_nombres`: longitud 37, mismo orden que las filas de `X`.
    - `X`: matriz `(37, 17)`, columnas en el orden exacto de `AREAS`.
    """
    result = await db.execute(
        select(Carrera).options(selectinload(Carrera.puntajes)).order_by(Carrera.id)
    )
    carreras = list(result.scalars().all())

    if not carreras:
        raise RuntimeError(
            "No hay carreras en la base de datos. Corre `python -m app.scripts.seed_data` "
            "antes de levantar el backend."
        )

    ids = [c.id for c in carreras]
    nombres = [c.nombre for c in carreras]
    X = np.array([c.vector_por_area(AREAS) for c in carreras], dtype=float)
    return ids, nombres, X
