"""Schemas Pydantic v2 para la Fase 9a (autenticación JWT)."""
from pydantic import BaseModel, EmailStr, Field


class RegistroIn(BaseModel):
    """Payload de `POST /auth/registro`."""

    nombre_completo: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)


class LoginIn(BaseModel):
    """Payload de `POST /auth/login`."""

    email: EmailStr
    password: str = Field(..., min_length=1, max_length=72)


class RefreshIn(BaseModel):
    """Payload de `POST /auth/refresh`."""

    refresh_token: str


class UsuarioOut(BaseModel):
    """Representación pública de un usuario (nunca incluye el password_hash)."""

    id: int
    nombre_completo: str
    email: str

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    """Respuesta estándar tras registro/login/refresh: par de tokens JWT."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut
