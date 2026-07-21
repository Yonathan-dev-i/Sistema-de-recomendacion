"""
Función #2 de la capa de IA del chatbot híbrido: redacción asistida de
respuestas del banco de FAQs (RAG acotado, no búsqueda abierta).

Se invoca DESPUÉS de que `faq_service.buscar_intent_faq` (reglas, por
Levenshtein) ya identificó cuál intent coincide con la pregunta del
usuario. Esta función NO decide qué FAQ usar ni si hay match — solo toma el
texto fijo de la FAQ ya encontrada y le pide al modelo que lo redacte de
forma más natural, respondiendo directamente a la pregunta tal como la
escribió el usuario.

Restricción dura: el prompt prohíbe explícitamente agregar información que
no esté en `respuesta_faq`. Si la llamada a la IA falla, se devuelve
`respuesta_faq` sin cambios — el usuario nunca se queda sin respuesta por
un problema de esta capa.
"""
from __future__ import annotations

from app.services.ia.cliente_llm import llamar_llm

_SYSTEM_PROMPT = (
    "Eres el asistente conversacional de un test vocacional universitario. "
    "Te doy la pregunta textual de un estudiante y la respuesta OFICIAL ya "
    "verificada a esa pregunta. Tu única tarea es redactar esa misma "
    "respuesta de forma más natural y conversacional, dirigida al "
    "estudiante. Reglas estrictas: no agregues ningún dato, cifra, plazo o "
    "afirmación que no esté en la respuesta oficial; no inventes nada; si "
    "la respuesta oficial no encaja del todo con la pregunta, redacta de "
    "todos modos usando solo esa información, sin rellenar los huecos. "
    "Responde en 1-3 oraciones, en español, sin encabezados ni viñetas."
)


def _prompt_usuario(pregunta_usuario: str, respuesta_faq: str) -> str:
    return (
        f'Pregunta del estudiante: "{pregunta_usuario}"\n'
        f'Respuesta oficial a reproducir con tus palabras: "{respuesta_faq}"'
    )


async def generar_respuesta_faq_asistida(
    pregunta_usuario: str, respuesta_faq: str
) -> str:
    """
    Redacta `respuesta_faq` de forma más natural en función de
    `pregunta_usuario`. Si la IA está deshabilitada o la llamada falla,
    devuelve `respuesta_faq` tal cual (mismo comportamiento que hoy).
    """
    redaccion = await llamar_llm(
        _SYSTEM_PROMPT,
        _prompt_usuario(pregunta_usuario, respuesta_faq),
        max_tokens=200,
    )
    return redaccion if redaccion else respuesta_faq