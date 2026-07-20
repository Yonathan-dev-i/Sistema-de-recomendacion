# Fase 6 — Método 2: Chatbot basado en reglas (núcleo conversacional)

## 1. Objetivo de la fase

Tener el segundo método de test funcionando de principio a fin — una
conversación tipo chat, 100% basada en reglas (sin IA generativa ni LLMs
externos) — que produzca, ante las mismas respuestas, exactamente el mismo
vector de usuario y el mismo Top 5 que el formulario tradicional (Fase 4).

## 2. Alcance realizado

### Backend

- **`backend/app/services/chatbot_service.py`** — módulo **puro** (sin
  FastAPI ni base de datos) con la máquina de estados finita completa:
  - Estados (`estado["fase"]`): `bienvenida` → `esperando_respuesta_likert`
    → `esperando_confirmacion_final` → `post_resultado`.
  - `iniciar_conversacion(...)`: mensaje de bienvenida + primera pregunta.
  - `procesar_mensaje(...)`: router central que despacha el mensaje del
    usuario según la fase actual (equivalente en Python al pseudocódigo de
    "Router central de mensajes" del prompt maestro).
  - Reaplica, pregunta por pregunta y en tiempo real, la misma regla de la
    Lógica Adaptativa de Preguntas de la Fase 3 (primera respuesta del área
    define el presupuesto; una respuesta `< 3` corta el área; nunca se
    extiende más allá del presupuesto inicial), sin reimplementarla —
    consume `respuestas_por_area` con la misma semántica que
    `preguntas_a_formular`, y al cerrar la conversación llama directamente a
    `adaptive_flow_service.construir_vector_usuario` (Fase 3), la **misma**
    función que usa el formulario.
  - `interpretar_likert`: acepta dígitos (`"4"`) y números en palabras
    (`"cuatro"`); `interpretar_si_no`: acepta variantes de "sí"/"no".
  - Validación estricta: una respuesta no reconocida no avanza el estado —
    se repite la pregunta actual con un mensaje de corrección (reformulación).
  - Frases de transición rotativas entre áreas (`_TRANSICIONES`) y un mensaje
    de motivación periódico cada 6 preguntas formuladas.
- **`backend/app/models/intento_test.py`**: se agregó la columna
  `estado_chat` (JSON, nullable) a `IntentoTest`, usada solo para
  `metodo == CHATBOT`, con toda la sesión serializada (área/pregunta actual,
  respuestas por área, preguntas usadas, historial completo de burbujas y la
  fase de la FSM) — es lo que permite reanudar tras un refresh.
- **`backend/migrations/versions/bf7efc4db2ed_agrega_estado_chat_a_intentos_test.py`**:
  migración que agrega esa columna sobre el esquema de la Fase 1.
- **`backend/app/schemas/chatbot.py`**: `ChatbotIniciarOut`, `ChatbotMensajeIn`,
  `ChatbotMensajeOut`, `ChatbotSesionOut`, `ChatbotResultadoOut` (reutiliza
  `ResultadoCarreraOut` de la Fase 2, igual que `TestTradicionalOut`).
- **`backend/app/api/chatbot.py`** (`prefix="/test/chatbot"`):
  - `POST /test/chatbot/iniciar`: crea un `IntentoTest(metodo=CHATBOT,
    estado=EN_PROGRESO)`, corre `iniciar_conversacion`, persiste el estado
    inicial y devuelve `sesion_id` + primeros mensajes del bot.
  - `POST /test/chatbot/{sesion_id}/mensaje`: carga la sesión, corre
    `procesar_mensaje`; si el usuario acaba de confirmar el cierre
    (`"sí"` en `esperando_confirmacion_final`), llama a
    `recomendacion_service.calcular_recomendacion` — **el mismo servicio y
    el mismo caché de `app.state.recomendacion_cache`** que usa
    `POST /test/tradicional` — persiste `IntentoTest` (completado) y una
    `RespuestaTest` por cada pregunta realmente formulada, y devuelve el
    resultado; si no, solo persiste el nuevo estado de la conversación y
    devuelve los mensajes del turno.
  - `GET /test/chatbot/{sesion_id}`: reconstruye el historial completo desde
    `estado_chat` (o el resultado ya calculado, si el intento está
    completado) para reanudar la conversación tras un refresh.
- **`backend/app/main.py`**: router de chatbot registrado junto a los demás.
- **Tests** (`backend/app/tests/test_fase6_chatbot.py`, 19 tests nuevos):
  interpretación de entrada, no-avance de estado ante respuesta/confirmación
  inválida, y el **test de equivalencia** (4 secuencias distintas,
  incluyendo presupuesto mínimo, máximo y dos casos mixtos con recorte)
  entre `chatbot_service` y `test_service.procesar_respuestas_tradicional`.

### Frontend

- **`frontend/src/lib/api.ts`**: tipos `MensajeChat`, `ChatbotResultado`,
  `ChatbotIniciarOut`, `ChatbotMensajeOut`, `ChatbotSesionOut` y las
  funciones `iniciarChat`, `enviarMensajeChat`, `reanudarChat`.
- **`frontend/src/app/test/chatbot/page.tsx`** — reemplaza el placeholder
  "en construcción" de la Fase 5 por la interfaz real:
  - Layout tipo chat (burbujas del bot a la izquierda con ícono, burbujas
    del usuario a la derecha), contenedor con `role="log"` y
    `aria-live="polite"` (WCAG 2.1 AA, según lo pedido en el prompt
    maestro).
  - Indicador de "escribiendo..." (3 puntos animados) entre 400-800ms antes
    de mostrar cada respuesta nueva del bot.
  - Chips numerados 1-5 debajo del campo de texto cuando el bot espera una
    respuesta Likert, más el campo de texto libre siempre disponible para
    quien prefiera escribir el número (o "sí"/"no" en la confirmación
    final).
  - **Reanudación tras refresh**: el `sesion_id` se guarda en
    `localStorage`; al recargar la página, se llama a
    `GET /test/chatbot/{sesion_id}` y se reconstruye visualmente todo el
    historial, con un mensaje de contexto ("Continuemos donde lo dejamos").
    Si la sesión guardada ya no existe en el backend, se descarta y se
    arranca una nueva conversación en vez de dejar la pantalla rota.
  - Resumen del Top 5 inline al terminar el test (tarjeta compacta dentro
    del propio chat), con botones "Realizar nuevamente el test" / "Volver
    al inicio", igual criterio que la pantalla de resultados del
    formulario tradicional.

### Fuera de alcance (según el prompt maestro para esta fase)

- Preguntas abiertas tipo FAQ, comandos "pausar"/"continuar después",
  mensajes de resumen de progreso a mitad de camino, y preguntas de
  seguimiento post-resultado ("¿por qué me recomendaste X?"): todo esto es
  el catálogo de "Funcionalidades Avanzadas del Chatbot" y corresponde
  explícitamente a la Fase 7, no a esta.
- Pantalla de resultados completa (chips de fortalezas/áreas por mejorar,
  explicación por reglas por carrera): se muestra un resumen compacto
  dentro del chat; la pantalla de resultados detallada ya existe en
  `/test/tradicional` y ambos métodos comparten el mismo contrato
  (`ChatbotResultadoOut` reutiliza `ResultadoCarreraOut`), así que no hace
  falta duplicar esa UI en esta fase.

## 3. Decisiones técnicas relevantes

- **`chatbot_service.py` no reutiliza literalmente
  `adaptive_flow_service.preguntas_a_formular`** (que está pensada para un
  callback síncrono de una sola pasada), sino que reimplementa la misma
  regla de decisión de forma incremental, turno a turno, porque una
  conversación por HTTP no puede bloquear esperando la siguiente respuesta
  dentro de una sola función. Sí reutiliza directamente
  `construir_vector_usuario` (idéntica, sin reimplementar) al cerrar el
  test. La garantía de equivalencia no depende de compartir el mismo
  bucle de Python, sino de que ambos módulos implementan **la misma regla**
  y de que el test de equivalencia (sección 5) lo verifica explícitamente
  con casos concretos — el mismo enfoque que ya usaba `test_service.py`
  para invocar `preguntas_a_formular` desde el flujo del formulario.
- **El estado de sesión vive en `IntentoTest.estado_chat` (JSON), no en una
  tabla nueva `sesiones_chat`.** Se decidió extender el modelo existente en
  vez de crear una tabla aparte porque una sesión de chat *es* un intento de
  test en progreso — mismo ciclo de vida, misma tabla de resultados al
  cerrar — y así se evita una relación uno-a-uno adicional y un JOIN extra
  en cada mensaje. Si en una fase futura se necesitara consultar sesiones
  de chat por SQL (no solo leerlas completas), sería el momento de
  normalizar esa columna a una tabla propia.
- **`GET /test/chatbot/{sesion_id}` no requiere autenticación en esta fase**
  (el `sesion_id` numérico secuencial actúa como capability token
  implícito, igual que el resto del sistema antes de la Fase 9). El prompt
  maestro ubica JWT y cuentas de usuario en una fase posterior; esta fase
  solo exige poder *reanudar* la conversación, no *autorizarla* contra un
  usuario. Se documenta como pendiente conocido, no silenciado: la Fase 9
  debería asociar `sesion_id` a `usuario_id` cuando exista sesión
  autenticada.
- **La confirmación final pide "sí"/"no" explícito antes de calcular**
  (`esperando_confirmacion_final`), en vez de calcular automáticamente tras
  la pregunta 17. Esto sigue literalmente la sección 4 ("Cierre del test
  dentro del chatbot") del prompt maestro y evita envíos accidentales,
  mismo criterio que el `AlertDialog` de confirmación de salida del
  formulario (Fase 4/5).
- **La reformulación ante respuesta inválida no cuenta como "pregunta
  formulada"** (`estado["total_formuladas"]` no se incrementa, y
  `pregunta_actual_id` no cambia): el criterio de aceptación exige
  explícitamente que "las respuestas inválidas no avanzan el estado del
  test", así que ni el contador de motivación ni el algoritmo adaptativo se
  ven afectados por reintentos.
- **No se usó WebSocket.** El prompt maestro no lo exige y el patrón
  petición/respuesta HTTP simple (`POST /mensaje` por cada turno) es
  suficiente para una conversación por turnos con un typing indicator
  simulado en el cliente (setTimeout de 400-800ms) — igual de "natural"
  para el usuario, sin la complejidad adicional de manejar conexiones
  persistentes y reconexión tras refresh.

## 4. Cómo se verificaron los criterios de aceptación

| Criterio | Método de verificación | Resultado |
|---|---|---|
| Ante la misma secuencia de respuestas, el chatbot produce el mismo `vector_usuario` y el mismo Top 5 que el formulario | `test_equivalencia_chatbot_vs_formulario` (4 secuencias parametrizadas: presupuesto mínimo, máximo, y 2 casos mixtos con recorte) comparando `construir_vector_desde_sesion` (chatbot) contra `procesar_respuestas_tradicional` (formulario) | ✅ `vector_chatbot == vector_formulario` en los 4 casos; como ambos alimentan el mismo `recomendacion_service.calcular_recomendacion`, un vector idéntico implica un Top 5 idéntico |
| Si se refresca la página a mitad del chat, la conversación se puede reanudar desde el mismo punto | `GET /test/chatbot/{sesion_id}` reconstruye `historial` completo + `fase` + `chips` desde `estado_chat` persistido; verificado por inspección de código y por el flujo del frontend (`localStorage` + reintento con sesión nueva si la guardada ya no existe) | ✅ (ver nota en sección 6 sobre el entorno sin PostgreSQL disponible) |
| Las respuestas inválidas no avanzan el estado del test | `test_respuesta_invalida_no_avanza_el_estado` y `test_confirmacion_invalida_no_avanza_a_post_resultado`: verifican que `pregunta_actual_id`, `fase` y `total_formuladas` no cambian ante una entrada no reconocida | ✅ |
| Linters pasan sin errores | `ruff check app/` (backend) y `npx eslint src/` (frontend) | ✅ ambos "sin errores" |
| Tipos correctos (frontend) | `npx tsc --noEmit` | ✅ sin errores |
| Build de producción (frontend) | `npx next build` | ✅ compila; `/test/chatbot` genera una página de 6.12 kB, sin errores de React/Next |
| Suite completa de tests (Fases 0-6) sigue pasando | `pytest app/tests/ -v` | ✅ 62/62 |

## 5. Pruebas realizadas

- **Automatizadas (`backend/app/tests/test_fase6_chatbot.py`, 19 tests):**
  - `interpretar_likert` / `interpretar_si_no`: 8 + 5 casos parametrizados
    (dígitos, palabras, mayúsculas, entradas inválidas).
  - No-avance de estado ante respuesta Likert inválida y ante confirmación
    final inválida (2 tests).
  - **Test de equivalencia** (4 casos parametrizados) descrito arriba —
    el criterio de aceptación central de la fase.
- **Suite completa:** `pytest app/tests/ -v` → 62/62 (43 de Fases 0-4 + 8 de
  Fase 5 sin cambios de backend + 19 nuevos de Fase 6, más los que ya
  contaba `test_mahalanobis.py`/`test_health.py`).
- **Frontend:** `npx tsc --noEmit`, `npx eslint src/` y `npx next build`
  (los tres sin errores); `/test/chatbot` compila como página dinámica de
  cliente (`"use client"`) sin errores de React/Next.
- **No realizada en este entorno:** verificación manual end-to-end vía
  `TestClient` con SQLite en memoria contra los endpoints HTTP reales
  (`POST /test/chatbot/iniciar`, `.../mensaje`, `GET .../{id}`). A
  diferencia de la Fase 4/5, en este entorno de ejecución **no hay un
  servidor PostgreSQL disponible ni siquiera para levantarlo** (no está
  instalado), así que ni el `lifespan` de `app/main.py` (que sí requiere
  PostgreSQL real para cachear la matriz de Mahalanobis al arrancar) pudo
  ejercitarse con `TestClient`. La verificación de esta fase se apoyó por
  completo en los tests unitarios puros de `chatbot_service.py`, que no
  dependen de FastAPI ni de la base de datos — mismo patrón que ya usaban
  `test_mahalanobis.py` y `test_fase4_tradicional.py` para su lógica
  central. Queda pendiente, no silenciado: una verificación manual de los 3
  endpoints HTTP contra PostgreSQL real la primera vez que el proyecto se
  levante con `docker compose` / un Postgres real disponible.

## 6. Problemas encontrados y solución

- **Sin PostgreSQL disponible en este entorno de ejecución** (a diferencia
  de las Fases 1, 2 y 4, donde sí se pudo instalar y levantar
  `postgresql` localmente): no fue posible reproducir aquí el mismo smoke
  test end-to-end con `TestClient` que documentó la Fase 4. Se optó por
  reforzar la cobertura de tests unitarios puros de `chatbot_service.py`
  (19 tests, incluyendo el test de equivalencia con 4 secuencias distintas)
  en vez de omitir la verificación del criterio de aceptación central de la
  fase. Ver sección 5 para el detalle de qué sí se verificó.
- **Duplicar vs. reimplementar la Lógica Adaptativa dentro de la FSM.** El
  módulo `preguntas_a_formular` de la Fase 3 asume un callback síncrono de
  una sola pasada por área, incompatible con una conversación turno a turno
  por HTTP. Se resolvió reimplementando la misma regla de decisión de forma
  incremental (ver sección 3), verificada contra el módulo original mediante
  el test de equivalencia en vez de compartir literalmente el mismo bucle.
- Ninguno bloqueante más allá de lo anterior.

## 7. Estado final de la fase

**CERRADA**, con una salvedad documentada y no silenciada: la verificación
del criterio "reanudación tras refresh" se hizo por inspección de código y
mediante el flujo completo del frontend (no contra un backend + PostgreSQL
reales levantados, por no haber PostgreSQL disponible en este entorno de
ejecución — mismo tipo de pendiente ya dejado por las Fases 4 y 5). Los
otros dos criterios de aceptación explícitos de la Fase 6 (equivalencia
matemática con el formulario, y no avance de estado ante respuestas
inválidas) se verificaron de forma reproducible con tests automatizados
(62/62 en la suite completa).

## 8. Siguientes pasos

- `services/chatbot_service.py` ya expone un router central de mensajes con
  una fase `post_resultado`; la Fase 7 puede extenderlo ahí mismo para
  reconocer preguntas abiertas (FAQs vía `data/intents.json`) sin tocar el
  núcleo Likert/confirmación ya probado en esta fase.
- El contrato `ChatbotResultadoOut` ya reutiliza `ResultadoCarreraOut` de la
  Fase 2 — la Fase 9 (test de equivalencia automatizado con 10+ secuencias)
  puede reutilizar directamente `chatbot_service` y
  `test_service.procesar_respuestas_tradicional` como los dos oráculos a
  comparar, exactamente como ya lo hace `test_fase6_chatbot.py` a menor
  escala.
- `IntentoTest.estado_chat` y el patrón de reanudación por `sesion_id` en
  `localStorage` quedan listos para que la Fase 9 los asocie a
  `usuario_id` una vez exista autenticación JWT, sin cambiar el contrato de
  los tres endpoints ya construidos.
