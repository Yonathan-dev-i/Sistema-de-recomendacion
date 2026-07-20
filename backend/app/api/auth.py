"""
Endpoints de autenticación (Fase 9a): `POST /auth/registro`, `POST /auth/login`,
`POST /auth/refresh`, y `GET /auth/me` (útil para que el frontend valide la
sesión activa y recupere los datos del usuario tras un refresh de página).

Este router solo orquesta: valida entrada (Pydantic), delega el hashing y la
emisión/verificación de tokens en `app.core.security`, y persiste vía
SQLAlchemy. No se toca aquí nada de historial de intentos (Fase 9b).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import obtener_usuario_actual
from app.core.security import (
    TipoToken,
    TokenInvalidoError,
    crear_access_token,
    crear_refresh_token,
    decodificar_token,
    hash_password,
    verificar_password,
)
from app.models import Usuario
from app.schemas.auth import LoginIn, RefreshIn, RegistroIn, TokenOut, UsuarioOut

router = APIRouter(prefix="/auth", tags=["auth"])


def _emitir_par_de_tokens(usuario: Usuario) -> TokenOut:
    return TokenOut(
        access_token=crear_access_token(usuario.id),
        refresh_token=crear_refresh_token(usuario.id),
        usuario=UsuarioOut.model_validate(usuario),
    )


@router.post("/registro", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
async def registrar_usuario(
    payload: RegistroIn,
    db: AsyncSession = Depends(get_db),
) -> TokenOut:
    """
    Crea una cuenta nueva. El password nunca se guarda en texto plano: se
    almacena únicamente su hash bcrypt (`password_hash`).
    """
    existente = await db.execute(select(Usuario).where(Usuario.email == payload.email))
    if existente.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una cuenta registrada con ese email.",
        )

    usuario = Usuario(
        nombre_completo=payload.nombre_completo,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(usuario)
    await db.commit()
    await db.refresh(usuario)

    return _emitir_par_de_tokens(usuario)


@router.post("/login", response_model=TokenOut)
async def iniciar_sesion(
    payload: LoginIn,
    db: AsyncSession = Depends(get_db),
) -> TokenOut:
    """Verifica credenciales y, si son válidas, emite un nuevo par access+refresh."""
    result = await db.execute(select(Usuario).where(Usuario.email == payload.email))
    usuario = result.scalar_one_or_none()

    credenciales_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Email o contraseña incorrectos.",
    )
    if usuario is None:
        raise credenciales_invalidas
    if not verificar_password(payload.password, usuario.password_hash):
        raise credenciales_invalidas

    return _emitir_par_de_tokens(usuario)


@router.post("/refresh", response_model=TokenOut)
async def refrescar_token(
    payload: RefreshIn,
    db: AsyncSession = Depends(get_db),
) -> TokenOut:
    """
    Canjea un refresh token válido por un nuevo par access+refresh (rotación
    de refresh token). Un refresh token expirado, inválido, o un access token
    usado aquí por error, se rechaza con 401.
    """
    try:
        usuario_id = decodificar_token(payload.refresh_token, TipoToken.REFRESH)
    except TokenInvalidoError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    result = await db.execute(select(Usuario).where(Usuario.id == usuario_id))
    usuario = result.scalar_one_or_none()
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El usuario del token ya no existe.",
        )

    return _emitir_par_de_tokens(usuario)


@router.get("/me", response_model=UsuarioOut)
async def obtener_perfil(usuario: Usuario = Depends(obtener_usuario_actual)) -> Usuario:
    """Devuelve los datos del usuario autenticado. Requiere access token válido."""
    return usuario
