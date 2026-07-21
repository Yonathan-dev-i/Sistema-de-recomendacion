"""
Función #3 de la capa de IA del chatbot híbrido: preguntas de seguimiento
libres sobre el resultado ya calculado (fase "post_resultado").

Se invoca desde `chatbot_service.responder_pregunta_seguimiento` como
ÚLTIMO recurso, después de que las reglas ya intentaron, en este orden:
1. los patrones fijos de "por qué"/"comparar" (regex sobre texto normalizado),
2. el banco de FAQs (`faq_service.buscar_intent_faq`).

Solo si ninguna de esas reglas coincidió se llama a esta función. El
contexto que recibe el modelo es EXCLUSIVAMENTE el Top 5 ya calculado por
`recomendacion_service.calcular_recomendacion` (nombre, afinidad,
fortalezas, distancia de Mahalanobis) — el prompt prohíbe explícitamente
mencionar cualquier cifra o dato que no venga en ese contexto, para que el
modelo no pueda inventar ni un % de afinidad ni una carrera fuera del Top 5.

Si la IA está deshabilitada o la llamada falla, devuelve `None`: el caller
debe usar el mismo mensaje fijo de "no logré identificar tu pregunta" que
ya existe hoy.
"""
from __future__ import annotations

import json

from app.services.ia.cliente_llm import llamar_llm

_SYSTEM_PROMPT = (
    "Eres el asistente conversacional de un test vocacional universitario, "
    "conversando con un estudiante DESPUÉS de que ya vio su resultado. Te "
    "doy su Top 5 de carreras recomendadas, con datos reales ya calculados "
    "(porcentaje de afinidad, fortalezas detectadas, distancia estadística "
    "de Mahalanobis). Responde su pregunta usando ÚNICAMENTE esos datos. "
    "Reglas estrictas: nunca menciones un porcentaje, carrera, distancia o "
    "dato que no aparezca literalmente en el Top 5 que te doy; nunca "
    "dictamines qué carrera 'debería' elegir el estudiante, eso es su "
    "decisión; si la pregunta no se puede responder con esos datos, dilo "
    "explícitamente en vez de inventar algo. Responde en español, en un "
    "máximo de 3 oraciones."
)


def _prompt_usuario(pregunta_usuario: str, resultados: list[dict]) -> str:
    contexto = json.dumps(
        [
            {
                "posicion": i + 1,
                "nombre": r["nombre"],
                "afinidad_pct": r["afinidad_pct"],
                "fortalezas": r.get("fortalezas", []),
                "distancia_mahalanobis": r["distancia_mahalanobis"],
            }
            for i, r in enumerate(resultados)
        ],
        ensure_ascii=False,
    )
    return (
        f"Top 5 de carreras del estudiante (JSON): {contexto}\n"
        f'Pregunta del estudiante: "{pregunta_usuario}"'
    )


async def responder_pregunta_sobre_resultado(
    pregunta_usuario: str, resultados: list[dict]
) -> str | None:
    """
    Responde una pregunta de seguimiento sobre el resultado ya calculado,
    ligada estrictamente a `resultados` (el Top 5 real). Devuelve `None` si
    la IA está deshabilitada o la llamada falla, para que el caller use el
    fallback fijo existente.
    """
    if not resultados:
        return None
    return await llamar_llm(
        _SYSTEM_PROMPT,
        _prompt_usuario(pregunta_usuario, resultados),
        max_tokens=250,
    )