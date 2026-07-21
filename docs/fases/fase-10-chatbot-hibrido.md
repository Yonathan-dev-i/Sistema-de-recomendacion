# Fase 10 — Chatbot híbrido (reglas + IA)

## Objetivo

Agregar una capa de IA generativa **opcional y apagada por defecto** sobre
el chatbot 100% basado en reglas de la Fase 6/7, para cubrir tres puntos
donde las reglas son rígidas por diseño:

1. Respuestas Likert en lenguaje libre y ambiguo durante el test.
2. Preguntas del usuario que no calzan con ningún patrón del banco de FAQs.
3. Preguntas de seguimiento sobre el resultado que no calzan con los
   patrones fijos de "por qué"/"comparar".

## Principio no negociable

**El motor de recomendación y la Lógica Adaptativa del test nunca dependen
de un LLM.** Esta fase no toca:

- `adaptive_flow_service.py` (qué preguntas formular),
- `recomendacion_service.py` / `recomendacion_repository.py` (Mahalanobis,
  % de afinidad), ni
- `test_service.py` (validación y persistencia del Método 1).

Cualquier número que el usuario ve (afinidad %, distancia, puntajes por
área) sigue saliendo exclusivamente del cálculo determinista existente. La
IA puede **redactar** esos datos con otras palabras; nunca los inventa ni
los recalcula.

## Arquitectura: reglas primero, IA como fallback

```
Mensaje del usuario
       │
       ▼
¿Fase == "esperando_respuesta_likert"?
   │                              │
  Sí                              No
   │                              │
   ▼                              ▼
interpretar_likert() (reglas)     ¿Es un comando (_COMANDOS)?
   │                                        │
   ▼                                   Sí ──┴── No
¿Devolvió 1-5?                         │         │
   │        │                          ▼         ▼
  Sí        No                    Ejecutar   ¿Coincide con una FAQ
   │         │                    comando    conocida (faq_service)?
   ▼         ▼                               │
Seguir   ¿Coincide con una FAQ           Sí ──┴── No
el test  conocida (faq_service)?             │       │
             │                               ▼       ▼
        Sí ──┴── No                    faq_asistida  (fase
             │      │                  (IA redacta,   post_resultado:
             ▼      ▼                  con fallback   patrones fijos
        faq_asistida interprete_       al texto        de "por qué"/
        (IA, con      respuestas_libre fijo si         "comparar",
        fallback al   (IA, con umbral falla o está     luego FAQ,
        texto fijo)   de confianza;    apagada)         luego IA)
                      si falla o no
                      alcanza el
                      umbral, cae al
                      mensaje de
                      aclaración de
                      siempre)
```

La regla de oro: **la IA solo actúa cuando las reglas ya fallaron**, nunca
al revés, y siempre con manejo explícito de "esto puede fallar/estar
apagado, y si es así, el usuario ve exactamente el mismo comportamiento que
tenía el chatbot antes de esta fase".

## Feature flag: apagado por defecto

```env
CHATBOT_IA_HABILITADA=false   # default
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-sonnet-4-6
IA_TIMEOUT_SEGUNDOS=6.0
IA_UMBRAL_CONFIANZA=0.6
```

Con `CHATBOT_IA_HABILITADA=false` (el valor por defecto), `llamar_llm()` en
`app/services/ia/cliente_llm.py` devuelve `None` **sin intentar ninguna
llamada de red**, y todo el sistema se comporta exactamente igual que antes
de esta fase. Activar la IA es una decisión explícita de despliegue, no
algo que ocurre por accidente.

## Módulos nuevos (`backend/app/services/ia/`)

| Módulo | Función | Se invoca desde | Fallback si falla/está apagada |
|---|---|---|---|
| `cliente_llm.py` | `llamar_llm(system, user)` | los 3 módulos de abajo | `None` |
| `interprete_respuestas.py` | `interpretar_respuesta_libre(texto, pregunta)` | `chatbot_service._procesar_respuesta_likert`, solo si ni `interpretar_likert` ni `buscar_intent_faq` reconocieron el mensaje | `(None, 0.0)` → mismo mensaje de aclaración de siempre |
| `faq_asistida.py` | `generar_respuesta_faq_asistida(pregunta, respuesta_faq)` | `_procesar_respuesta_likert` y `responder_pregunta_seguimiento`, después de que `buscar_intent_faq` ya encontró la FAQ | devuelve `respuesta_faq` sin cambios |
| `explicacion_resultado.py` | `responder_pregunta_sobre_resultado(pregunta, resultados)` | `responder_pregunta_seguimiento`, como último recurso antes del mensaje fijo de "no logré identificar tu pregunta" | `None` → mismo mensaje fijo de siempre |

## Cambios en `chatbot_service.py`

- `procesar_mensaje`, `_procesar_respuesta_likert` y
  `responder_pregunta_seguimiento` pasaron de `def` a `async def`, porque
  ahora pueden necesitar hacer una llamada de red (I/O) a la capa de IA. El
  módulo sigue sin tocar la base de datos ni importar FastAPI — esa
  responsabilidad sigue siendo 100% del router (`app/api/chatbot.py`), que
  ahora hace `await procesar_mensaje(...)`.
- Nuevo campo `estado["analitica"]["respuestas_ia_usadas"]`: contador de
  trazabilidad reglas/IA. Se incrementa cada vez que una respuesta salió de
  la capa de IA en vez de una regla determinista. Puramente informativo
  (logging/depuración); nunca afecta el flujo del test.
- Cuando la IA interpreta una respuesta Likert ambigua, el chatbot se lo
  **confirma explícitamente al usuario** ("Entendí tu respuesta como un N
  de 5.") antes de continuar, en vez de avanzar en silencio. Así, si la
  interpretación fue incorrecta, el usuario lo nota de inmediato y puede
  usar el comando `anterior` para corregirla.
- De paso, se corrigió un bug preexistente: el mensaje de fallback en
  `post_resultado` prometía un comando `reiniciar` que nunca estuvo
  implementado en `_COMANDOS`. Se quitó la mención de ese comando inexistente
  del texto.

## Qué NO cambia para un despliegue con el flag apagado

Con `CHATBOT_IA_HABILITADA=false` (default de fábrica):
- Cero llamadas de red nuevas.
- Cero cambios de comportamiento visibles para el usuario.
- Los tests de la Fase 6/7/9c (`test_fase6_chatbot.py`,
  `test_fase7_chatbot_avanzado.py`, `test_fase9c_equivalencia_metodos.py`)
  siguen verificando exactamente las mismas garantías de antes; solo
  cambiaron de `def` a `async def` porque las funciones que llaman ahora
  son `async` (requisito técnico de Python, no un cambio de lo que se
  prueba).

## Tests de esta fase

`app/tests/test_fase10_chatbot_hibrido.py` cubre, de forma aislada del resto
del chatbot y **sin ninguna llamada de red real** (se reemplaza
`httpx.AsyncClient` por un stub que hace fallar el test si se le llama):

1. Apagado seguro: con el flag apagado, o encendido sin API key, ninguna de
   las 3 funciones intenta una llamada de red.
2. Parseo defensivo: una respuesta del modelo que no es JSON válido, o que
   trae un valor fuera de 1-5, se descarta como si la IA no hubiera
   reconocido nada.
3. Umbral de confianza: una interpretación con confianza por debajo del
   umbral configurado se descarta igual que si no hubiera match.

## Limitación conocida de esta implementación

Los prompts de sistema de los 3 módulos son un punto de partida razonable,
pero no fueron afinados con evaluaciones (evals) reales contra el modelo en
producción — antes de habilitar `CHATBOT_IA_HABILITADA=true` en un entorno
real, se recomienda correr un conjunto de casos de prueba manuales
(respuestas ambiguas típicas, preguntas de FAQ fuera del banco, preguntas de
seguimiento variadas) y ajustar la redacción de los prompts según haga
falta.