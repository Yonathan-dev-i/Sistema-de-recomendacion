# Fase 7 — Funcionalidades avanzadas del chatbot (preguntas abiertas y post-resultado)

## 1. Objetivo de la fase

Enriquecer el chatbot (Fase 6) con el catálogo de "Funcionalidades Avanzadas
del Chatbot" — preguntas abiertas tipo FAQ, comandos de navegación dentro del
chat, seguimiento post-resultado y analítica básica — sin tocar ni romper el
núcleo conversacional ya probado (máquina de estados Likert/confirmación).

## 2. Alcance realizado

### Backend

- **`backend/app/data/intents.json`**: banco de 8 FAQs (duración del test,
  privacidad, diferencia entre métodos, cómo se calcula la recomendación,
  costo, repetir el test, cuántas carreras se evalúan, carácter no vinculante
  del resultado), como archivo de datos versionado (no código hardcodeado),
  tal como exige el prompt maestro.
- **`backend/app/services/faq_service.py`** (nuevo, módulo puro):
  - `normalizar_texto`: minúsculas, sin tildes/diacríticos, sin puntuación.
  - `_levenshtein`: distancia de edición clásica (programación dinámica).
  - `_patron_coincide`: un patrón coincide por substring exacto **o** porque
    sus palabras aparecen consecutivas en el texto del usuario con hasta 1
    carácter de diferencia por palabra (tolerancia a tipeos, ej. "cuanro
    dura" → "cuanto dura").
  - `buscar_intent_faq(texto) -> (intent_id, respuesta) | None`: recorre
    `intents.json` y devuelve el primer intent cuyo patrón coincida.
- **`backend/app/services/chatbot_service.py`** (extendido, Fase 6 intacta):
  - **Comandos de navegación** (`_detectar_comando`, `_COMANDOS`): "ayuda",
    "repetir", "anterior"/"corregir", "ver progreso", "pausar"/"salir",
    reconocidos por texto normalizado antes de intentar interpretar la
    respuesta como Likert.
    - `repetir`: vuelve a mostrar la pregunta actual tal cual.
    - `anterior` (`_retroceder_pregunta`): descarta la última respuesta del
      área actual, recalcula el presupuesto (`limite_area_actual`) con la
      misma regla de la Lógica Adaptativa, y vuelve a formular esa pregunta.
    - `ver progreso` (`_resumen_progreso`): resumen de áreas completadas y
      preguntas respondidas hasta el momento.
    - `pausar`/`salir`: marca `estado["pausado"] = True` y confirma que el
      avance quedó guardado (la persistencia real ya la garantiza
      `IntentoTest.estado_chat` desde la Fase 6).
    - `ayuda`: lista las opciones disponibles como plantilla fija.
  - **Matching de FAQ integrado en el router de mensajes**: si el texto no es
    un 1-5 válido ni un comando, se intenta `buscar_intent_faq` antes de
    contarlo como respuesta inválida — tanto en `esperando_respuesta_likert`
    como en `esperando_confirmacion_final`. Si hay match, se responde la FAQ
    y se repite la pregunta/confirmación pendiente, **sin** avanzar el
    estado ni sumar al contador de reintentos.
  - **Límite de reintentos** (`LIMITE_REINTENTOS_INVALIDOS = 3`): tras 3
    respuestas Likert inválidas seguidas (que no matchearon ni Likert ni
    FAQ), se ofrece cambiar al formulario tradicional y se reinicia el
    contador (no queda "atascado" repitiendo la oferta en cada turno).
  - **Post-resultado** (`responder_pregunta_seguimiento`, funcionalidad #10):
    - "¿por qué esa carrera?" (`_PATRONES_POR_QUE`, regex): arma una
      respuesta de plantilla con el nombre, fortalezas y distancia de
      Mahalanobis reales del Top 1 (`estado["ultimo_resultado"]`).
    - "compara X con Y" (`_PATRONES_COMPARAR`, regex): detecta qué carreras
      del Top 5 fueron mencionadas por nombre (`_detectar_carreras_
      mencionadas`) y arma la comparación (`_armar_comparacion`) con
      afinidad y fortalezas reales de ambas; si no identifica 2 carreras,
      pide aclaración usando los nombres reales del propio Top 5 del
      usuario.
    - Si no es ninguna de las dos, intenta `buscar_intent_faq` (las FAQs
      generales siguen disponibles tras el resultado).
    - Fallback fijo si nada coincide — nunca se inventa una respuesta.
  - **Analítica básica** (`estado["analitica"]`, dentro de `estado_chat`,
    persistido igual que el resto de la sesión desde la Fase 6): lista de
    `intents_disparados` (id de cada FAQ que se disparó) y contador de
    `respuestas_invalidas`. `area_abandono` queda reservado (`None`) para
    cuando exista un job que marque intentos `EN_PROGRESO` abandonados como
    tales; no se implementó ese job en esta fase (ver sección 3).
  - `crear_sesion_inicial()` ahora también inicializa `intentos_invalidos`,
    `pausado`, `ultimo_resultado`, `ultimo_vector_usuario` y `analitica`.
- **`backend/app/api/chatbot.py`**: `_finalizar_y_persistir` ahora guarda
  `estado["ultimo_resultado"]` y `estado["ultimo_vector_usuario"]` **antes**
  de persistir `intento.estado_chat`, para que `responder_pregunta_
  seguimiento` tenga acceso a los datos reales del Top 5 en el siguiente
  turno (fase `post_resultado`). No se tocó el contrato de ningún endpoint.
- **Tests** (`backend/app/tests/test_fase7_chatbot_avanzado.py`, 21 tests
  nuevos): FAQs sin salirse del flujo (6 preguntas distintas parametrizadas),
  banco con ≥5 intents, seguimiento post-resultado ("por qué" y "compara")
  con datos reales, fallback fijo, los 5 comandos de navegación, límite de
  reintentos, y el servicio de matching (normalización, tolerancia a tipeos,
  no-match).

### Frontend

- **`frontend/src/app/test/chatbot/page.tsx`**: se actualizó el `placeholder`
  del campo de texto libre para sugerir explícitamente que también admite
  preguntas ("¿cuánto dura?") y comandos ("ayuda"), ya que la interfaz de
  chat de la Fase 6 no necesitaba ningún cambio estructural — el campo de
  texto libre y el envío por `POST /test/chatbot/{sesion_id}/mensaje` ya
  soportaban cualquier texto; solo faltaba que el backend supiera
  interpretarlo, que es lo que hace esta fase.

### Fuera de alcance (documentado, no silenciado)

- **Modo de tono "formal" vs. "cercano"** y **recordar el nombre del
  usuario** (funcionalidad #5 del catálogo): no se implementaron en esta
  fase; el criterio de aceptación de la Fase 7 no los exige explícitamente
  (a diferencia de FAQs, post-resultado y trazabilidad, que sí son
  criterios). Quedan como extensión natural del banco de plantillas ya
  existente.
- **Detección de inactividad ("¿sigues ahí?")** y **modo texto simplificado**
  (funcionalidades #6/#7 adicionales): no implementadas; requieren un
  mecanismo de temporización en el frontend que no forma parte de los 3
  criterios de aceptación de esta fase.
- **Job de métricas de abandono por área** (`area_abandono`): se reservó el
  campo en `estado["analitica"]` pero no se implementó el proceso que
  marcaría un intento `EN_PROGRESO` como abandonado tras inactividad
  prolongada; eso requeriría un job en background (cron/worker) fuera del
  alcance de un request/response síncrono, no descrito como criterio de
  aceptación explícito de la fase.
- **Comando "saltar área"** (opcional según el catálogo): no implementado;
  el prompt maestro lo marca explícitamente como opcional.

## 3. Decisiones técnicas relevantes

- **El matching de FAQ se prueba únicamente cuando el texto no es un valor
  Likert válido ni un comando reconocido.** Esto evita el caso ambiguo de
  que alguien responda literalmente "5" (que es Likert válido) y que el
  sistema intente además buscarlo como una intención FAQ; el orden de
  chequeo (comando → Likert → FAQ → inválido) sigue el mismo patrón que ya
  usaba `procesar_mensaje_usuario` en el prompt maestro.
- **La tolerancia a tipeos se implementó a nivel de ventana de palabras
  consecutivas, no solo para patrones de una sola palabra.** La primera
  versión solo toleraba errores en patrones de una palabra; se generalizó a
  patrones multi-palabra (comparando cada palabra del patrón contra la
  palabra correspondiente de una ventana del mismo tamaño en el texto del
  usuario) porque la mayoría de los patrones reales de `intents.json` son
  frases de 2-4 palabras (ej. "cuanto dura"), y limitarla a una sola palabra
  dejaba fuera el caso de uso principal descrito en el catálogo ("cuanro
  dura" → "cuanto").
- **El límite de reintentos se reinicia tras ofrecer el cambio a
  formulario**, en vez de seguir acumulando o bloquear la conversación. Se
  decidió así porque el prompt maestro pide "ofrecer" el cambio, no forzarlo
  — el usuario puede seguir intentando en el chat con un contador limpio, o
  cambiar de método por su cuenta desde la navegación existente (Fase 5).
- **`ultimo_resultado`/`ultimo_vector_usuario` se guardan dentro del mismo
  `estado` (y por lo tanto en `IntentoTest.estado_chat`)**, en vez de leer
  `intento.top5_resultado` directamente en `responder_pregunta_seguimiento`.
  Razón: ese servicio es puro (no debe depender de un modelo SQLAlchemy ni
  de una sesión de BD), igual que el resto de `chatbot_service.py`; guardar
  una copia en el propio diccionario de estado mantiene esa pureza y permite
  testear la función de seguimiento con un `dict` sintético, sin mocks de
  base de datos (ver los tests de `_por_que_esa_carrera_`/`_comparacion_`).
- **La comparación de carreras identifica menciones por nombre exacto
  normalizado** (`_detectar_carreras_mencionadas`), no por número de
  posición en el Top 5 (ej. "compara la 1 con la 3"). Se eligió esta opción
  porque el ejemplo del prompt maestro (`"compara Ingeniería de Sistemas con
  Ingeniería Civil"`) usa nombres, y es más natural para el usuario que
  memorizar posiciones; si no se detectan 2 nombres, el mensaje de
  aclaración ya sugiere los nombres reales del propio Top 5 del usuario en
  vez de un ejemplo genérico.
- **No se creó una tabla de analítica aparte.** Se decidió registrar
  `intents_disparados` y `respuestas_invalidas` dentro del mismo
  `estado["analitica"]` (persistido en `IntentoTest.estado_chat`, columna ya
  existente desde la Fase 6) en vez de una tabla `eventos_analitica` nueva.
  Es la opción más simple que cumple el criterio de "registro de analítica
  básica" sin una migración adicional; si en una fase futura se necesitara
  agregar analítica entre sesiones (ej. "top 10 preguntas más frecuentes en
  toda la plataforma"), sería el momento de normalizarla a una tabla propia
  con un evento por fila.

## 4. Cómo se verificaron los criterios de aceptación

| Criterio | Método de verificación | Resultado |
|---|---|---|
| El chatbot responde correctamente a al menos 5 preguntas frecuentes distintas sin salirse del flujo del test | `test_chatbot_responde_faqs_sin_salirse_del_flujo` (6 preguntas distintas parametrizadas) + `test_al_menos_5_intents_distintos_configurados` | ✅ Las 6 preguntas obtienen respuesta FAQ y la `fase`/`pregunta_actual_id`/`total_formuladas` quedan exactamente igual que antes de preguntar; `intents.json` tiene 8 intents |
| Tras mostrar un resultado, el usuario puede preguntar "¿por qué esa carrera?" y recibir una respuesta basada en los datos reales de su Top 5 | `test_por_que_esa_carrera_usa_datos_reales_del_top5`: verifica que el nombre, la distancia de Mahalanobis exacta y al menos una fortaleza real del Top 1 aparecen en la respuesta | ✅ |
| Ninguna respuesta del chatbot en esta fase proviene de generación de texto libre; todas son trazables a una plantilla + datos | Inspección de código: `responder_pregunta_seguimiento`, `_armar_comparacion` y las respuestas de comandos son f-strings sobre plantillas fijas + `estado["ultimo_resultado"]`/`intents.json`; `test_fallback_fijo_post_resultado_no_inventa_respuesta` confirma el fallback fijo ante texto sin match | ✅ |
| Linters pasan sin errores | `ruff check app/` | ✅ "All checks passed!" |
| Suite completa de tests (Fases 0-7) sigue pasando | `pytest app/tests/ -v` | ✅ 83/83 (62 de Fases 0-6 + 21 nuevos de Fase 7) |

## 5. Pruebas realizadas

- **Automatizadas (`test_fase7_chatbot_avanzado.py`, 21 tests):**
  - 6 FAQs distintas respondidas sin salir del flujo (parametrizado) + 1 test
    de que el banco tiene ≥5 intents.
  - Seguimiento post-resultado: "por qué esa carrera" con datos reales,
    comparación con datos reales, comparación sin 2 carreras identificadas
    (pide aclaración), FAQ disponible en post-resultado, fallback fijo.
  - Los 5 comandos de navegación: `repetir`, `ver progreso`, `anterior`
    (verificando que efectivamente descarta la última respuesta y
    recalcula el presupuesto), `pausar` (verificando `estado["pausado"]` y
    que no se pierde el avance), `ayuda`.
  - Límite de 3 reintentos inválidos → oferta de cambio a formulario +
    reinicio del contador.
  - Servicio `faq_service`: normalización de texto, tolerancia a un error de
    tipeo, y ausencia de match ante texto no relacionado.
- **Manual:** ejecución interactiva por consola (`python3 -c ...`) de una
  conversación completa simulada: pregunta FAQ a mitad de una pregunta
  Likert, comando `ayuda`, respuesta Likert normal, comando `anterior`
  corrigiendo esa misma respuesta, y 3 respuestas inválidas seguidas
  disparando la oferta de cambio a formulario — confirmando visualmente el
  contenido exacto de cada mensaje antes de fijarlo en los tests
  automatizados.
- **No realizada en este entorno:** verificación end-to-end vía los
  endpoints HTTP reales (`POST /test/chatbot/iniciar` / `.../mensaje`)
  contra PostgreSQL real, por el mismo motivo ya documentado en las Fases 6
  y 5 (no hay un servidor PostgreSQL disponible en este entorno de
  ejecución). El cambio en `api/chatbot.py` (`_finalizar_y_persistir`) es
  mínimo (dos asignaciones de diccionario antes de un `intento.estado_chat =
  estado` que ya existía) y no se tocó ningún otro endpoint; toda la lógica
  nueva de esta fase vive en `chatbot_service.py`/`faq_service.py`, módulos
  puros ya cubiertos por los 21 tests automatizados.

## 6. Problemas encontrados y solución

- **La tolerancia a tipeos inicial (solo patrones de una palabra) no cubría
  el caso de uso principal del catálogo** ("cuanro dura" → "cuanto dura",
  un patrón de dos palabras). Se detectó al escribir el primer test de
  tolerancia a tipeos (`test_buscar_intent_faq_tolera_un_error_de_tipeo`),
  que falló contra la implementación inicial. Se corrigió generalizando
  `_patron_coincide` a una comparación por ventana de palabras consecutivas
  (ver sección 3), sin necesidad de reescribir el resto del servicio.
- Ninguno más bloqueante. El resto de la fase se integró sin regresiones:
  los 62 tests de las Fases 0-6 siguen pasando exactamente igual que antes
  de esta fase.

## 7. Estado final de la fase

**CERRADA.** Los 3 criterios de aceptación definidos en el prompt maestro
para la Fase 7 se verificaron de forma reproducible con tests automatizados
puros (21 nuevos, 83/83 en la suite completa) y con una verificación manual
interactiva adicional. Quedan documentadas como fuera de alcance (sección 2)
algunas funcionalidades opcionales o no exigidas explícitamente por los
criterios de aceptación (tono formal/cercano, detección de inactividad, job
de abandono por área), sin afectar el cierre de la fase.

## 8. Siguientes pasos

- El banco `data/intents.json` y `faq_service.buscar_intent_faq` quedan
  listos para crecer con más FAQs sin tocar `chatbot_service.py` — es
  justamente el objetivo de la funcionalidad #8 (analítica) de una fase
  futura: usar `estado["analitica"]["intents_disparados"]` agregado entre
  sesiones para detectar qué preguntas frecuentes faltan en el banco.
- `responder_pregunta_seguimiento` y `_armar_comparacion` ya consumen
  exactamente el mismo contrato (`ResultadoCarreraOut`/`ResultadoCarrera`)
  que usan las Fases 2/4/6; la Fase 8 (resultados avanzados, comparador
  visual de hasta 3 carreras) puede reutilizar la misma lógica de comparación
  de datos, solo cambiando la presentación (visual en vez de texto).
- El límite de reintentos y la oferta de cambio a formulario tradicional
  quedan como un punto de entrada natural para una futura métrica de
  "abandono del chatbot hacia el formulario", si se decide instrumentar el
  job de analítica agregada mencionado en la sección 2.
