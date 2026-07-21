"""
Función #1 de la capa de IA del chatbot híbrido: interpretación de
respuestas Likert en lenguaje libre.

Se invoca ÚNICAMENTE desde `chatbot_service._procesar_respuesta_likert`, y
solo después de que las reglas ya fallaron en dos pasos: ni
`interpretar_likert` (dígitos/palabras exactas) ni `buscar_intent_faq`
(pregunta conocida del banco de FAQs) reconocieron el mensaje. En ese punto,
lo único que puede ser es una respuesta ambigua a la pregunta Likert actual
(ej. "ni fu ni fa", "más o menos", "bastante, la verdad").

Contrato estricto:
- Devuelve `(valor, confianza)` donde `valor` es `1`-`5` o `None`.
- Si `confianza < settings.ia_umbral_confianza`, el caller debe tratarlo
  exactamente igual que si `valor` fuera `None` (mismo mensaje de
  aclaración que ya existe hoy en `chatbot_service`).
- Nunca decide por sí mismo el flujo del test, ni toca
  `preguntas_a_formular` ni el vector de usuario: solo traduce texto a un
  entero 1-5, tal como si el usuario lo hubiera tipeado directamente.
"""
from __future__ import annotations

import json
import logging

from app.core.config import get_settings
from app.services.ia.cliente_llm import llamar_llm

logger = logging.getLogger("app.chatbot.ia")

_SYSTEM_PROMPT = (
    "Clasificas una respuesta de estudiante a una pregunta de test "
    "vocacional en una escala Likert de 1 a 5, donde 1 = No me gusta nada "
    "y 5 = Me gusta mucho. Responde ÚNICAMENTE un JSON de una línea con "
    'las claves "valor" (entero 1-5, o null si el texto no expresa un '
    'nivel de agrado/desagrado interpretable) y "confianza" (número entre '
    "0 y 1). No agregues texto antes ni después del JSON. No expliques tu "
    "razonamiento."
)


def _prompt_usuario(texto_usuario: str, texto_pregunta: str) -> str:
    return (
        f'Pregunta formulada: "{texto_pregunta}"\n'
        f'Respuesta del estudiante: "{texto_usuario}"'
    )


async def interpretar_respuesta_libre(
    texto_usuario: str, texto_pregunta: str
) -> tuple[int | None, float]:
    """
    Intenta traducir una respuesta en lenguaje libre a un valor 1-5.

    Devuelve `(None, 0.0)` si la capa de IA está deshabilitada, la llamada
    falla, o la respuesta del modelo no es un JSON válido con la forma
    esperada — en todos esos casos el caller debe caer al comportamiento de
    reglas ya existente (pedir aclaración).
    """
    respuesta = await llamar_llm(
        _SYSTEM_PROMPT,
        _prompt_usuario(texto_usuario, texto_pregunta),
        max_tokens=60,
    )
    if respuesta is None:
        return None, 0.0

    try:
        data = json.loads(respuesta)
        valor = data.get("valor")
        confianza = float(data.get("confianza", 0.0))
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        logger.warning(
            "Respuesta de la IA no fue un JSON válido, se usa fallback: %s", exc
        )
        return None, 0.0

    if valor is None:
        return None, confianza

    try:
        valor_int = int(valor)
    except (TypeError, ValueError):
        return None, 0.0

    if valor_int not in (1, 2, 3, 4, 5):
        return None, 0.0

    confianza = max(0.0, min(1.0, confianza))

    settings = get_settings()
    if confianza < settings.ia_umbral_confianza:
        return None, confianza

    return valor_int, confianza