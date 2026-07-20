"""
Utilidades de seguridad para la Fase 9a (autenticación).

Contiene dos responsabilidades puras, sin dependencia de FastAPI ni de la
base de datos, para que sean fáciles de testear de forma unitaria:

1. Hash y verificación de contraseñas (bcrypt vía passlib).
2. Creación y decodificación de tokens JWT (access + refresh), vía python-jose.

El resto del flujo de autenticación (endpoints, dependencia de usuario
actual) vive en `app.api.auth` y `app.core.deps`.
"""
import datetime as dt
import enum
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TipoToken(enum.StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


class TokenInvalidoError(Exception):
    """El token JWT es inválido, expiró, o no es del tipo esperado."""


def hash_password(password: str) -> str:
    """Genera el hash bcrypt de una contraseña en texto plano."""
    return _pwd_context.hash(password)


def verificar_password(password: str, password_hash: str) -> bool:
    """Compara una contraseña en texto plano contra su hash almacenado."""
    return _pwd_context.verify(password, password_hash)


def _crear_token(usuario_id: int, tipo: TipoToken, expira_en: dt.timedelta) -> str:
    settings = get_settings()
    ahora = dt.datetime.now(dt.UTC)
    payload: dict[str, Any] = {
        "sub": str(usuario_id),
        "type": tipo.value,
        "iat": ahora,
        "exp": ahora + expira_en,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def crear_access_token(usuario_id: int) -> str:
    settings = get_settings()
    return _crear_token(
        usuario_id,
        TipoToken.ACCESS,
        dt.timedelta(minutes=settings.jwt_access_token_expire_minutes),
    )


def crear_refresh_token(usuario_id: int) -> str:
    settings = get_settings()
    return _crear_token(
        usuario_id,
        TipoToken.REFRESH,
        dt.timedelta(days=settings.jwt_refresh_token_expire_days),
    )


def decodificar_token(token: str, tipo_esperado: TipoToken) -> int:
    """
    Decodifica y valida un token JWT, devolviendo el `usuario_id` (claim `sub`).

    Lanza `TokenInvalidoError` si el token está expirado, mal firmado, o si es
    de un tipo distinto al esperado (ej. usar un refresh token donde se espera
    un access token, o viceversa).
    """
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise TokenInvalidoError("Token inválido o expirado.") from exc

    if payload.get("type") != tipo_esperado.value:
        raise TokenInvalidoError(
            f"Se esperaba un token de tipo '{tipo_esperado.value}', "
            f"se recibió '{payload.get('type')}'."
        )

    sub = payload.get("sub")
    if sub is None:
        raise TokenInvalidoError("El token no contiene el claim 'sub'.")

    try:
        return int(sub)
    except (TypeError, ValueError) as exc:
        raise TokenInvalidoError("El claim 'sub' del token no es un id válido.") from exc
