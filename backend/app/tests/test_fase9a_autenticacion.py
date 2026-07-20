"""
Tests de la Fase 9a — Autenticación.

Cubren `app.core.security` (hashing de contraseñas y ciclo de vida de tokens
JWT), que es lógica pura sin dependencia de PostgreSQL. Igual que en
`test_fase4_tradicional.py`, las pruebas de integración HTTP contra
`POST /auth/registro` / `/auth/login` / `/auth/refresh` (con PostgreSQL real)
se documentan como manuales en `docs/fases/fase-9a-autenticacion.md`, ya que
este entorno de CI no levanta una base de datos Postgres para los tests
unitarios.
"""
import datetime as dt

import pytest
from jose import jwt

from app.core.config import get_settings
from app.core.security import (
    TipoToken,
    TokenInvalidoError,
    crear_access_token,
    crear_refresh_token,
    decodificar_token,
    hash_password,
    verificar_password,
)


def test_hash_password_nunca_devuelve_el_password_en_texto_plano():
    hashed = hash_password("mi_password_super_secreto")
    assert hashed != "mi_password_super_secreto"
    assert hashed.startswith("$2b$")  # prefijo estándar de bcrypt


def test_verificar_password_correcta_devuelve_true():
    hashed = hash_password("clave-correcta-123")
    assert verificar_password("clave-correcta-123", hashed) is True


def test_verificar_password_incorrecta_devuelve_false():
    hashed = hash_password("clave-correcta-123")
    assert verificar_password("clave-incorrecta", hashed) is False


def test_access_token_se_decodifica_al_mismo_usuario_id():
    token = crear_access_token(usuario_id=42)
    assert decodificar_token(token, TipoToken.ACCESS) == 42


def test_refresh_token_se_decodifica_al_mismo_usuario_id():
    token = crear_refresh_token(usuario_id=7)
    assert decodificar_token(token, TipoToken.REFRESH) == 7


def test_usar_un_refresh_token_como_access_token_es_rechazado():
    refresh = crear_refresh_token(usuario_id=1)
    with pytest.raises(TokenInvalidoError):
        decodificar_token(refresh, TipoToken.ACCESS)


def test_usar_un_access_token_como_refresh_token_es_rechazado():
    access = crear_access_token(usuario_id=1)
    with pytest.raises(TokenInvalidoError):
        decodificar_token(access, TipoToken.REFRESH)


def test_token_con_firma_invalida_es_rechazado():
    token = crear_access_token(usuario_id=1)
    token_alterado = token[:-1] + ("A" if token[-1] != "A" else "B")
    with pytest.raises(TokenInvalidoError):
        decodificar_token(token_alterado, TipoToken.ACCESS)


def test_token_expirado_es_rechazado():
    settings = get_settings()
    ahora = dt.datetime.now(dt.UTC)
    payload = {
        "sub": "1",
        "type": TipoToken.ACCESS.value,
        "iat": ahora - dt.timedelta(minutes=10),
        "exp": ahora - dt.timedelta(minutes=1),  # ya expiró
    }
    token_expirado = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    with pytest.raises(TokenInvalidoError):
        decodificar_token(token_expirado, TipoToken.ACCESS)


def test_token_sin_claim_sub_es_rechazado():
    settings = get_settings()
    ahora = dt.datetime.now(dt.UTC)
    payload = {
        "type": TipoToken.ACCESS.value,
        "iat": ahora,
        "exp": ahora + dt.timedelta(minutes=5),
    }
    token_sin_sub = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    with pytest.raises(TokenInvalidoError):
        decodificar_token(token_sin_sub, TipoToken.ACCESS)
