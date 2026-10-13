from __future__ import annotations

import logging

import httpx

from app.core.config import get_settings

logger = logging.getLogger("app.chatbot.ia")

_GEMINI_URL_TEMPLATE = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)


async def llamar_llm(
    system_prompt: str,
    user_prompt: str,
    *,
    max_tokens: int = 300,
) -> str | None:
    settings = get_settings()

    if not settings.chatbot_ia_habilitada:
        return None
    if not settings.gemini_api_key:
        logger.warning(
            "CHATBOT_IA_HABILITADA=true pero falta GEMINI_API_KEY; "
            "se usa el fallback de reglas."
        )
        return None

    url = _GEMINI_URL_TEMPLATE.format(model=settings.gemini_model)

    try:
        async with httpx.AsyncClient(timeout=settings.ia_timeout_segundos) as client:
            respuesta = await client.post(
                url,
                headers={
                    "x-goog-api-key": settings.gemini_api_key,
                    "content-type": "application/json",
                },
                json={
                    "system_instruction": {"parts": [{"text": system_prompt}]},
                    "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
                    "generationConfig": {"maxOutputTokens": max_tokens},
                },
            )
            respuesta.raise_for_status()
            data = respuesta.json()
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("Llamada a la IA del chatbot falló, se usa fallback: %s", exc)
        return None

    candidatos = data.get("candidates", [])
    if not candidatos:
        return None
    partes = candidatos[0].get("content", {}).get("parts", [])
    texto = "".join(p.get("text", "") for p in partes).strip()
    return texto or None