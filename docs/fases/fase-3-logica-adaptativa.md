# Fase 3 — Lógica Adaptativa de Preguntas (módulo aislado)

## 1. Objetivo de la fase

Tener la lógica de recorte/extensión de preguntas por área funcionando y
testeada, de forma completamente independiente de si se usa desde el
formulario tradicional o desde el chatbot — un único módulo compartido, para
que ambos métodos produzcan matemáticamente el mismo resultado ante las mismas
respuestas.

## 2. Alcance realizado

- **`backend/app/services/adaptive_flow_service.py`**:
  - `preguntas_a_formular(preguntas_area, respuestas_callback) -> list[int]`:
    implementación literal del algoritmo determinista del prompt maestro. La
    primera respuesta de un área fija el "presupuesto" máximo (1-5); las
    respuestas siguientes pueden recortarlo (si alguna es `< 3`, se corta ahí)
    pero nunca lo extienden, aunque una respuesta posterior sea mayor.
  - `construir_vector_usuario(respuestas_por_area) -> dict[str, float]`:
    promedio aritmético (redondeado a 2 decimales) de las respuestas
    *realmente formuladas* en cada área.
  - Ambas funciones son genéricas: `preguntas_a_formular` no asume que
    `preguntas_area` sea un modelo `Pregunta` de SQLAlchemy — acepta
    cualquier secuencia (ids, dicts, modelos ORM), ya que solo reenvía cada
    elemento al `respuestas_callback` sin inspeccionarlo. Esto permite
    reutilizarla igual desde el formulario tradicional (Fase 4, con
    `Pregunta` reales) y desde el chatbot (Fase 6, con el mismo banco).
- **Tests** (`backend/app/tests/test_adaptive_flow.py`): 21 tests, incluyendo:
  - Los **7 casos exactos** de la tabla de validación del prompt maestro,
    parametrizados (`[1]`→1, `[3,5,4]`→3, `[5,1]`→2, `[5,5,5,5,5]`→5,
    `[4,4,2]`→3, `[2,1]`→2, `[2,4]`→2) más una versión no-parametrizada de
    cada uno (nombrada explícitamente) para que el motivo de cada caso sea
    legible en el reporte de `pytest`.
  - Un test que verifica que el `callback` **nunca se invoca** para una
    pregunta más allá del presupuesto vigente (no solo que el resultado final
    sea correcto, sino que el algoritmo no "gasta" preguntas de más).
  - Un caso de borde con un área de menos de 5 preguntas (no debería romperse
    aunque el presupuesto habilitado sea mayor al total de preguntas
    disponibles).
  - Tests de `construir_vector_usuario`: 17 claves en rango válido, cálculo de
    promedio correcto, una sola respuesta por área, y una simulación con las
    17 áreas reales (`AREAS`) con cantidades variables de respuestas por área.

## 3. Decisiones técnicas relevantes

- **`preguntas_a_formular` es genérica en el tipo de "pregunta"** (usa
  `TypeVar` en vez de importar el modelo `Pregunta` de SQLAlchemy). Razón: el
  prompt maestro exige que el mismo módulo sirva tanto al formulario
  (que tendrá objetos `Pregunta` reales de la BD) como al chatbot (que puede
  operar sobre una estructura de sesión distinta); atarla a un tipo concreto
  hubiera obligado a adaptar o envolver datos en cada consumidor.
- **El helper de simulación de tests (`_simular`) vive en el archivo de
  tests, no en el servicio de producción.** Se escribió primero dentro de
  `adaptive_flow_service.py` por conveniencia, pero se movió a
  `test_adaptive_flow.py` al notar que era código exclusivamente de testing
  (generaba ids de pregunta genéricos y envolvía una lista fija en un
  callback) — no aporta nada al comportamiento real del sistema y no
  correspondía en el módulo de servicio.
- **No se agregó todavía persistencia ni un endpoint HTTP para esta lógica.**
  El prompt maestro es explícito en que la Fase 3 es "sin UI, sin
  persistencia": el objetivo es tener el módulo aislado y testeado; su
  integración con `POST /test/tradicional` (persistiendo qué preguntas se
  formularon realmente) es responsabilidad de la Fase 4.
- **Se mantuvo el nombre y la firma exactos** de `preguntas_a_formular` y
  `construir_vector_usuario` tal como aparecen en el prompt maestro, para que
  cualquier referencia cruzada en fases posteriores (o en el propio documento)
  siga siendo válida sin necesidad de traducir nombres.

## 4. Cómo se verificaron los criterios de aceptación

| Criterio | Método de verificación | Resultado |
|---|---|---|
| Los 7 casos de la tabla de validación pasan como tests unitarios, sin excepciones | `pytest app/tests/test_adaptive_flow.py -v` (casos parametrizados + versiones nombradas) | ✅ 14/14 (7 parametrizados + 7 nombrados), sin excepciones |
| `construir_vector_usuario` devuelve un diccionario de 17 claves con valores en el rango [1.0, 5.0] | Test con las 17 áreas reales (`AREAS`) y cantidades variables de respuestas (1 a 3) por área | ✅ `len(vector) == 17`, `set(vector.keys()) == set(AREAS)`, todos los valores en `[1.0, 5.0]` |
| Linters pasan sin errores | `ruff check app/` | ✅ "All checks passed!" |
| Suite completa de tests (Fases 0-3) sigue pasando | `pytest app/tests/ -v` | ✅ 37/37 |

## 5. Pruebas realizadas

- **Automatizadas:** los 21 tests de `test_adaptive_flow.py` descritos arriba,
  ejecutados de forma aislada (sin necesidad de PostgreSQL: este módulo no
  toca la base de datos) y luego como parte de la suite completa del proyecto.
- **Manuales:** ninguna verificación manual adicional aplica en esta fase —
  al ser un módulo puro sin UI ni endpoint, la validación reproducible vía
  `pytest` es la forma de prueba prevista explícitamente por el prompt
  maestro ("sin UI, sin persistencia").

## 6. Problemas encontrados y solución

- Ninguno bloqueante. El único ajuste de diseño fue notar, al revisar el
  primer borrador, que el helper de simulación de secuencias fijas de
  respuestas (`_simular`) no debía vivir en `adaptive_flow_service.py` — se
  movió a los tests antes de cerrar la fase (ver sección 3).

## 7. Estado final de la fase

**CERRADA.** Los 2 criterios de aceptación se verificaron de forma
reproducible: los 7 casos de la tabla de validación pasan exactamente como
`pytest`, y `construir_vector_usuario` produce un diccionario de 17 claves en
el rango esperado, tanto en casos sintéticos como con las 17 áreas reales del
sistema.

## 8. Siguientes pasos

Con el motor de Mahalanobis (Fase 2) y la Lógica Adaptativa (Fase 3) cerrados
en paralelo — ambos dependían solo de la Fase 1 —, la Fase 4 puede integrar
ambos en el primer flujo end-to-end real:

- `POST /test/tradicional`: recibe respuestas `{pregunta_id, respuesta}[]`,
  agrupa por área, aplica (conceptualmente) la misma decisión que
  `preguntas_a_formular` habría tomado, calcula el vector con
  `construir_vector_usuario`, y persiste en `intentos_test` + `respuestas_test`.
- El vector resultante se pasa directamente a
  `recomendacion_service.calcular_recomendacion` (Fase 2) — sin necesidad de
  ningún cambio en el motor de Mahalanobis, que ya espera exactamente un
  `dict[str, float]` de 17 claves.
- Frontend: formulario con barra de progreso por área, tarjeta de pregunta,
  selector Likert, navegación y autoguardado, conectado al endpoint real.
