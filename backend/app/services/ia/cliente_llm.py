"""
Cliente HTTP mínimo hacia la API de Anthropic (`/v1/messages`), usado por las
tres funciones de la capa de IA del chatbot híbrido.

Diseño deliberadamente conservador:
- Si `chatbot_ia_habilitada` es False o no hay `anthropic_api_key`
  configurada, `llamar_llm` devuelve `None` de inmediato, SIN intentar
  ninguna llamada de red. Esto es lo que hace que el feature flag apague la
  capa de IA por completo sin tocar código.
- Cualquier error de red, timeout, o respuesta inesperada de la API se
  atrapa aquí mismo y también se traduce a `None`. El caller (los tres
  módulos hermanos de este paquete) siempre debe tratar `None` como "usa el
  fallback de reglas", nunca como una excepción a propagar.
- No se reintenta la llamada: un timeout corto + fallback inmediato es
  preferible a que el usuario espere varios segundos por una respuesta de
  chat.
"""
from __future__ import annotations

import logging

import httpx

from app.core.config import get_settings

logger = logging.getLogger("app.chatbot.ia")

_ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
_ANTHROPIC_VERSION = "2023-06-01"


async def llamar_llm(
    system_prompt: str,
    user_prompt: str,
    *,
    max_tokens: int = 300,
) -> str | None:
    """
    Llama al modelo configurado y devuelve el texto de su respuesta, o
    `None` si la capa de IA está deshabilitada, mal configurada, o la
    llamada falla por cualquier motivo (red, timeout, error de la API,
    formato de respuesta inesperado).
    """
    settings = get_settings()

    if not settings.chatbot_ia_habilitada:
        return None
    if not settings.anthropic_api_key:
        logger.warning(
            "CHATBOT_IA_HABILITADA=true pero falta ANTHROPIC_API_KEY; "
            "se usa el fallback de reglas."
        )
        return None

    try:
        async with httpx.AsyncClient(timeout=settings.ia_timeout_segundos) as client:
            respuesta = await client.post(
                _ANTHROPIC_URL,
                headers={
                    "x-api-key": settings.anthropic_api_key,
                    "anthropic-version": _ANTHROPIC_VERSION,
                    "content-type": "application/json",
                },
                json={
                    "model": settings.anthropic_model,
                    "max_tokens": max_tokens,
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": user_prompt}],
                },
            )
            respuesta.raise_for_status()
            data = respuesta.json()
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("Llamada a la IA del chatbot falló, se usa fallback: %s", exc)
        return None

    bloques = data.get("content", [])
    texto = "".join(b.get("text", "") for b in bloques if b.get("type") == "text")
    texto = texto.strip()
    return texto or None