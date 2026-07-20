# Fase 4 — Método 1: Test Tradicional (formulario) end-to-end

## 1. Objetivo de la fase

Tener el primer flujo completo usable por un usuario real, de principio a
fin: un formulario que aplica la Lógica Adaptativa de Preguntas (Fase 3)
pregunta por pregunta, envía las respuestas al backend, calcula el vector de
usuario y el Top 5 con el motor de Mahalanobis (Fase 2), persiste el intento
en PostgreSQL, y muestra una pantalla de resultados básica.

## 2. Alcance realizado

### Backend

- **`backend/app/services/test_service.py`**: `procesar_respuestas_tradicional`,
  función **pura** (sin FastAPI ni base de datos) que:
  - Recibe `preguntas_por_area` (ids de pregunta agrupados por área, ya
    ordenados) y `respuestas_dict` (lo que envió el cliente).
  - Reaplica `preguntas_a_formular` de la Fase 3, área por área, usando un
    callback que exige que exista respuesta para cada pregunta que el
    algoritmo adaptativo efectivamente pediría.
  - Detecta y rechaza dos formas de inconsistencia: respuestas **faltantes**
    (una pregunta que sí correspondía formular no tiene respuesta) y
    respuestas **sobrantes** (una pregunta que el algoritmo nunca habría
    llegado a pedir, dado el resto de respuestas, sí trae un valor). Ambas
    levantan `RespuestasInvalidasError`.
  - Si todo es consistente, calcula el vector de usuario con
    `construir_vector_usuario` (Fase 3) y devuelve también la lista de
    `pregunta_id` efectivamente usados (para persistir solo esas filas).
- **`backend/app/schemas/test_tradicional.py`**: `TestTradicionalIn`
  (`respuestas: list[{pregunta_id, respuesta}]`, longitud 17-85, sin ids
  repetidos) y `TestTradicionalOut` (`test_id`, `vector_usuario`,
  `resultados` — reutiliza `ResultadoCarreraOut` de la Fase 2).
- **`backend/app/api/test.py`**: `POST /test/tradicional`. Orquesta:
  1. Carga las preguntas reales desde PostgreSQL, agrupadas por área.
  2. Llama a `procesar_respuestas_tradicional` (422 si el payload no es
     consistente con la Lógica Adaptativa).
  3. Llama a `calcular_recomendacion` (Fase 2) usando la matriz de covarianza
     inversa ya cacheada en `app.state.recomendacion_cache` (no se recalcula
     por request).
  4. Persiste un `IntentoTest` (`metodo=TRADICIONAL`, `estado=COMPLETADO`,
     `vector_usuario`, `top5_resultado` como snapshot JSON) y una fila
     `RespuestaTest` por cada pregunta **realmente formulada** (nunca las 85).
  5. Devuelve `test_id`, `vector_usuario` y el Top 5.
- Router registrado en `backend/app/main.py`.

### Frontend

- **`frontend/src/lib/api.ts`**: cliente tipado (`obtenerAreas`,
  `obtenerPreguntas`, `enviarTestTradicional`) con manejo de errores HTTP
  (`ApiError`, incluyendo el `detail` que devuelve FastAPI en un 422).
- **`frontend/src/lib/adaptiveFlow.ts`**: espejo en TypeScript de
  `preguntas_a_formular` (`siguientePreguntaIndiceEnArea`), usado
  exclusivamente para decidir en vivo qué pregunta mostrar y cuándo cambiar
  de área/finalizar. La fuente de verdad sigue siendo el backend, que vuelve
  a validar todo de forma independiente.
- **`frontend/src/app/test/tradicional/page.tsx`**: pantalla del formulario:
  - Barra de progreso de dos niveles: segmentos por área (17) + porcentaje
    estimado global.
  - Tarjeta de pregunta con el área actual y "Pregunta X de máx. Y".
  - Selector Likert de 5 opciones tipo *card* (con emoji, número y texto de
    la escala), resaltado visual de la opción seleccionada.
  - Navegación Anterior/Siguiente; "Siguiente" deshabilitado hasta
    seleccionar una respuesta.
  - **Edición retroactiva**: si el usuario vuelve atrás y cambia una
    respuesta ya dada, se descartan los pasos posteriores ya calculados y se
    muestra un toast explicando que el número de preguntas se recalculó,
    exactamente como pide el prompt maestro.
  - Al completar las 17 áreas, envía las respuestas realmente formuladas a
    `POST /test/tradicional` (no simulado) y muestra un estado de carga
    ("Calculando tu recomendación con Mahalanobis…").
  - Pantalla de Resultados básica: tarjetas del Top 5 con `afinidad_pct`,
    explicación por reglas, chips de fortalezas/áreas por mejorar, y botones
    "Realizar nuevamente el test" / "Volver al inicio".
- **`frontend/src/app/page.tsx`**: se agregó un botón "Realizar Test
  Tradicional" hacia `/test/tradicional` (la landing completa es la Fase 5;
  esto es solo el enlace mínimo para poder probar el flujo end-to-end ahora).

### Fuera de alcance (según el prompt maestro para esta fase)

- Gráfico radar / barras avanzados de resultados: quedan para la Fase 8.
- Panel/modal de "Resumen de áreas" y botón de salida con confirmación: son
  mejoras de UX listadas en la sección de diseño, no criterios de aceptación
  de la Fase 4; no se implementaron aún.
- Landing page y navegación general: Fase 5.

## 3. Decisiones técnicas relevantes

- **`procesar_respuestas_tradicional` es una función pura**, separada del
  router HTTP, siguiendo el mismo patrón que `recomendacion_service.py`
  (Fase 2) y `adaptive_flow_service.py` (Fase 3): permite testear la parte
  crítica (validación adaptativa + construcción del vector) sin necesitar
  PostgreSQL en la suite de `pytest`.
- **Validación estricta de respuestas sobrantes.** El prompt maestro no lo
  exige explícitamente, pero se decidió que el backend rechace (422) un
  payload que incluya respuestas para preguntas que la Lógica Adaptativa
  nunca habría llegado a formular (dado el resto de respuestas del mismo
  payload), en vez de ignorarlas silenciosamente. Razón: aceptar esas
  respuestas de forma silenciosa permitiría a un cliente malicioso o con un
  bug enviar un vector de usuario que no corresponde a ningún recorrido
  válido del test, rompiendo la garantía de trazabilidad del sistema.
- **Persistencia solo de las preguntas realmente formuladas.** `RespuestaTest`
  solo recibe filas para los `pregunta_id` que el algoritmo adaptativo
  efectivamente consumió (`preguntas_usadas`), tal como exige el prompt
  maestro en "Impacto en el resto del sistema": *"la tabla de respuestas debe
  guardar (...) qué pregunta_id fueron efectivamente mostradas y respondidas
  (no todas las 85 tendrán una fila)"*.
- **Edición retroactiva simplificada al alcance de la Fase 4.** El frontend sí
  recalcula en vivo el número de preguntas de un área cuando se edita una
  respuesta anterior (requisito explícito de la Fase 4/sección Método 1), y
  descarta los pasos futuros ya calculados. No se implementó todavía el panel
  lateral de "Resumen de áreas" con salto directo a cualquier pregunta
  (listado como mejora de UX, no como criterio de aceptación de esta fase);
  la edición retroactiva funciona mediante el botón "Anterior" paso a paso.
- **Lógica adaptativa duplicada intencionalmente en el frontend.** Se
  reimplementó una versión mínima (`siguientePreguntaIndiceEnArea`) en
  TypeScript para poder decidir la navegación sin hacer una petición HTTP por
  cada pregunta. Esto **no** debilita la garantía de "misma lógica en ambos
  métodos" del prompt maestro, porque el backend no confía en absoluto en lo
  que decidió el cliente: revalida el payload completo contra
  `preguntas_a_formular` (la misma función Python de la Fase 3) antes de
  calcular o persistir nada.
- **Sin endpoint "siguiente pregunta" pregunta-a-pregunta.** Se optó por que
  el frontend cargue el banco completo de preguntas una vez (`GET
  /preguntas`) y decida la navegación localmente, en vez de pedir cada
  pregunta al backend una por una. Es más simple y evita latencia percibida
  en cada clic; el chatbot (Fase 6), que sí necesita estado de sesión en
  backend por naturaleza conversacional, no reutiliza esta decisión.

## 4. Cómo se verificaron los criterios de aceptación

| Criterio | Método de verificación | Resultado |
|---|---|---|
| Un usuario puede completar el test tradicional de principio a fin y ver un Top 5 real, calculado con Mahalanobis sobre sus respuestas | `npx next build` sin errores + smoke test end-to-end vía `TestClient` (FastAPI) contra una base SQLite en memoria sembrada con las 17 áreas, 85 preguntas y 37 carreras reales: `POST /test/tradicional` con respuesta=1 en la primera pregunta de cada área → `200 OK` con `test_id`, `vector_usuario` (17 claves en 1.0) y Top 5 real (`afinidad_pct` 100.0 → 96.9 → ... ordenado) | ✅ |
| El número de preguntas mostradas por área varía según las respuestas, verificable manualmente con los casos de la Fase 3 | `app/tests/test_fase4_tradicional.py`: caso mixto reproduce exactamente el ejemplo `[3, 5, 4]` → 3 preguntas de la Fase 3 dentro del flujo completo del formulario (16 áreas con 1 pregunta + matemática con 3 = 19 preguntas usadas) | ✅ |
| Los datos del intento quedan persistidos en PostgreSQL | El endpoint hace `db.add(IntentoTest(...))` + `db.flush()` + `db.add(RespuestaTest(...))` por cada pregunta usada + `db.commit()`; verificado en el smoke test (SQLite, mismo motor SQLAlchemy async) que devuelve `test_id: 1` tras el `commit`, confirmando que la fila se creó y obtuvo id | ✅ (verificado con SQLAlchemy async real; pendiente de una verificación manual adicional contra PostgreSQL real en un entorno con la base levantada, ver sección 6) |
| (Implícito) el payload debe ser rechazado si no es consistente con la Lógica Adaptativa | Smoke test: enviar una respuesta "sobrante" (pregunta que no correspondía) → `422` con `detail` explicando cuál pregunta sobra | ✅ |
| Linters pasan sin errores | `ruff check app/` (backend) y `npx eslint src/` (frontend) | ✅ ambos "sin errores" |
| Suite completa de tests (Fases 0-4) sigue pasando | `pytest app/tests/ -v` | ✅ 43/43 |

## 5. Pruebas realizadas

- **Automatizadas (`backend/app/tests/test_fase4_tradicional.py`, 6 tests):**
  - Presupuesto mínimo (respuesta 1 en las 17 áreas) → 17 preguntas usadas,
    vector con las 17 claves en 1.0.
  - Presupuesto máximo (respuesta 5 constante) → 85 preguntas usadas, vector
    en 5.0.
  - Caso mixto que reproduce el ejemplo `[3, 5, 4]` de la Fase 3 dentro del
    flujo completo de 17 áreas.
  - Rechazo por respuesta faltante que sí correspondía formular.
  - Rechazo por respuesta sobrante más allá del presupuesto adaptativo.
  - Vector de usuario resultante con 17 claves en rango `[1.0, 5.0]`.
- **Manuales / smoke test end-to-end:** script ejecutado contra `TestClient`
  de FastAPI con una base SQLite en memoria sembrada con los datasets reales
  (`data/areas.json`, `data/preguntas.json`, `data/carreras.csv`), sin mockear
  ninguna parte de la lógica de negocio (solo se sustituye el motor de base
  de datos de Postgres por SQLite vía `dependency_overrides`, y se
  precalcula la matriz de covarianza inversa igual que hace `lifespan` en
  producción). Confirmó: `200 OK` con resultado coherente en el caso válido,
  `422` con mensaje explicativo en el caso inválido.
- **Frontend:** `npx tsc --noEmit` (sin errores de tipos), `npx eslint src/`
  (sin errores) y `npx next build` (compila y genera `/test/tradicional`
  como página estática de 3.17 kB, sin errores de React/Next).
- **No realizada en este entorno:** ejecución manual del formulario en un
  navegador contra un backend + PostgreSQL reales levantados (este entorno de
  ejecución no tiene un servidor PostgreSQL disponible ni un navegador con el
  que interactuar). El smoke test con SQLite cubre la misma ruta de código
  (mismo ORM async, mismos modelos, mismo servicio de cálculo) con la
  excepción del motor de base de datos concreto.

## 6. Problemas encontrados y solución

- **Ambigüedad en cómo tratar respuestas "sobrantes" del cliente.** El prompt
  maestro no especifica explícitamente qué hacer si el frontend envía más
  respuestas de las que la Lógica Adaptativa habría pedido. Se decidió
  rechazar explícitamente (422) en vez de ignorar silenciosamente, ver
  sección 3 para la justificación completa.
- **Test unitario inicial mal diseñado.** La primera versión de
  `test_vector_usuario_resultante_tiene_17_claves_en_rango_valido` enviaba
  solo una respuesta por área con valor 4, pero un valor de 4 en la primera
  pregunta habilita un presupuesto de 4 preguntas — el test fallaba porque
  el payload era inconsistente con su propio presupuesto (exactamente el
  comportamiento correcto que debía validar `RespuestasInvalidasError`, pero
  aplicado por error a un test que no buscaba probar eso). Se corrigió
  enviando dos respuestas por área (presupuesto de 2, ambas respondidas).
- **Sin PostgreSQL disponible en este entorno de ejecución** (ver sección 5):
  se optó por un smoke test equivalente con SQLite async en vez de omitir la
  verificación end-to-end del endpoint. Queda pendiente, no silenciado, una
  verificación manual contra PostgreSQL real la primera vez que el proyecto
  se levante con `docker compose` / un Postgres real disponible.

## 7. Estado final de la fase

**CERRADA**, con una salvedad documentada y no silenciada: la verificación
end-to-end del endpoint se hizo contra SQLite (mismo código, mismo ORM
async, mismos datos reales) en lugar de PostgreSQL real, por no haber un
servidor PostgreSQL disponible en este entorno de ejecución. Los tres
criterios de aceptación explícitos de la Fase 4 se cumplen; se recomienda una
verificación manual puntual contra PostgreSQL antes de dar por cerrada la
fase en un entorno con la base de datos real levantada (`docker compose up`
+ `python -m app.scripts.seed_data` + `POST /test/tradicional` real).

## 8. Siguientes pasos

- El endpoint `POST /test/tradicional` y su motor de validación
  (`procesar_respuestas_tradicional`) quedan listos para ser el punto de
  comparación de la Fase 6 (chatbot): el "test de equivalencia" de la Fase 9
  puede reutilizar directamente `procesar_respuestas_tradicional` como
  oráculo de referencia.
- La pantalla de resultados básica (tarjetas + chips) ya consume el contrato
  real de `TestTradicionalOut`; en la Fase 8 solo hace falta *añadir*
  visualizaciones (radar, barras) sobre los mismos datos, no rediseñar el
  contrato.
- La Fase 5 (landing) puede enlazar directamente a `/test/tradicional`, que
  ya funciona de forma autónoma.
