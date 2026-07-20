"""
Dependencias de FastAPI para la Fase 9a: protección de endpoints vía JWT.

`obtener_usuario_actual` es la dependencia "dura" (401 si no hay sesión) que
se usa en endpoints que requieren estar autenticado, ej. `GET /usuarios/me`
y, desde la Fase 9b, `GET /usuarios/me/intentos`.

`obtener_usuario_opcional` es la variante "suave" (nunca falla) pensada para
endpoints que deben funcionar igual para invitados y para usuarios logueados
(ej. `POST /test/tradicional` en la Fase 9b, donde el intento se asocia al
usuario si hay sesión, o queda anónimo si no la hay).
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import TipoToken, TokenInvalidoError, decodificar_token
from app.models import Usuario

# `auto_error=False`: para poder implementar la variante opcional sin que
# FastAPI lance un 403 automático cuando no viene el header Authorization.
_bearer_scheme = HTTPBearer(auto_error=False)


async def _resolver_usuario_desde_token(
    credenciales: HTTPAuthorizationCredentials | None,
    db: AsyncSession,
) -> Usuario | None:
    if credenciales is None:
        return None
    try:
        usuario_id = decodificar_token(credenciales.credentials, TipoToken.ACCESS)
    except TokenInvalidoError:
        return None

    result = await db.execute(select(Usuario).where(Usuario.id == usuario_id))
    return result.scalar_one_or_none()


async def obtener_usuario_actual(
    credenciales: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Usuario:
    """Dependencia obligatoria: 401 si el token falta, es inválido o expiró."""
    if credenciales is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se proporcionó un token de acceso.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        usuario_id = decodificar_token(credenciales.credentials, TipoToken.ACCESS)
    except TokenInvalidoError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    result = await db.execute(select(Usuario).where(Usuario.id == usuario_id))
    usuario = result.scalar_one_or_none()
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El usuario del token ya no existe.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return usuario


async def obtener_usuario_opcional(
    credenciales: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Usuario | None:
    """Dependencia suave: devuelve `None` (sin error) si no hay sesión válida."""
    return await _resolver_usuario_desde_token(credenciales, db)
