"""
Endpoint `GET /usuarios/me/intentos` (Fase 9b): historial de intentos del
usuario autenticado, más reciente primero.

Solo se listan los intentos con `usuario_id == usuario.id` (los intentos de
invitado, con `usuario_id` nulo, nunca aparecen aquí ni para nadie — no hay
forma de reclamarlos retroactivamente, por diseño). Protegido con
`obtener_usuario_actual`: sin sesión válida, `401`.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import obtener_usuario_actual
from app.models import IntentoTest, Usuario
from app.schemas.usuarios import IntentoResumenOut
from app.services.historial_service import ordenar_intentos_por_fecha_desc, resumen_intento

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.get("/me/intentos", response_model=list[IntentoResumenOut])
async def listar_mis_intentos(
    usuario: Usuario = Depends(obtener_usuario_actual),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    result = await db.execute(
        select(IntentoTest).where(IntentoTest.usuario_id == usuario.id)
    )
    intentos = list(result.scalars().all())
    intentos_ordenados = ordenar_intentos_por_fecha_desc(intentos)
    return [resumen_intento(i) for i in intentos_ordenados]
