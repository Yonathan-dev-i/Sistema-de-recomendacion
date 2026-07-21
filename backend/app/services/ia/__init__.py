"""
Capa de IA del chatbot híbrido (reglas + IA).

Todo lo que vive en este paquete es ADICIONAL a `chatbot_service.py` y
`faq_service.py`, nunca un reemplazo: se invoca únicamente cuando las reglas
ya intentaron interpretar el mensaje del usuario y no lo lograron. Ver
`docs/fases/fase-10-chatbot-hibrido.md` para el contrato completo.

Ningún módulo de este paquete participa en:
- la Lógica Adaptativa de Preguntas (`adaptive_flow_service.py`),
- el cálculo de afinidad/Mahalanobis (`recomendacion_service.py`), ni
- la persistencia del test (`test_service.py`).

Todas las funciones públicas de este paquete son `async`, manejan sus
propios timeouts y devuelven un valor "vacío" (`None`, confianza `0.0`, o el
texto original sin cambios) ante cualquier error, deshabilitación por
feature flag, o falta de API key — nunca dejan que una falla de la IA
tumbe la conversación.
"""