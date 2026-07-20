# Fase 9c — Test de equivalencia formulario vs. chatbot

## 1. Objetivo de la fase

Verificar de forma automatizada la "regla de oro" del sistema: que el Método 1
(formulario tradicional) y el Método 2 (chatbot basado en reglas) producen
matemáticamente el mismo `vector_usuario` — y por lo tanto el mismo Top 5 —
ante exactamente la misma secuencia de respuestas del usuario.

## 2. Alcance realizado

- `backend/app/tests/test_fase9c_equivalencia_metodos.py`: suite de tests que:
  - Construye, para cada secuencia simulada, el `respuestas_dict`
    `{pregunta_id: respuesta}` que realmente produciría la Lógica Adaptativa
    (Fase 3) sobre esa secuencia (`_respuestas_dict_desde_secuencias`).
  - Alimenta ese mismo `respuestas_dict` a
    `test_service.procesar_respuestas_tradicional` (Método 1) y, por otro
    lado, conduce una sesión completa del chatbot
    (`chatbot_service.crear_sesion_inicial` →
    `chatbot_service.iniciar_conversacion` →
    `chatbot_service.procesar_mensaje` en bucle → confirmación final) usando
    los mismos valores (Método 2), a través del helper
    `_ejecutar_chatbot_completo`.
  - Compara, para cada secuencia: (a) las respuestas registradas por área,
    (b) el `vector_usuario` de 17 dimensiones, y (c) el Top 5 real calculado
    por `recomendacion_service.calcular_recomendacion` sobre la matriz real
    de 37×17 (`data/carreras.csv`), usando `motor_recomendacion` como fixture
    cacheado a nivel de módulo (igual que se cachea en producción vía
    `app/main.py`).
- **11 secuencias distintas** cubiertas (supera el mínimo de 10 exigido):
  1. `area_se_corta_de_inmediato_1` — `[1]`
  2. `presupuesto_3_no_se_extiende_3_5_4` — `[3, 5, 4]`
  3. `presupuesto_5_se_corta_por_baja_5_1` — `[5, 1]`
  4. `presupuesto_5_agota_las_5_preguntas` — `[5, 5, 5, 5, 5]`
  5. `presupuesto_4_se_corta_antes_4_4_2` — `[4, 4, 2]`
  6. `presupuesto_2_se_respeta_2_1` — `[2, 1]`
  7. `presupuesto_2_nunca_se_extiende_2_4` — `[2, 4]`
  8. `multiples_areas_con_recorte_simultaneo` — 4 áreas con distintos patrones de recorte/extensión a la vez.
  9. `todas_las_areas_en_minimo` — las 17 áreas en `[1]` (caso extremo mínimo, 17 preguntas totales).
  10. `todas_las_areas_al_maximo` — las 17 áreas en `[5,5,5,5,5]` (caso extremo máximo, 85 preguntas totales).
  11. `perfil_mixto_realista_variado_por_area` — las 17 áreas con secuencias distintas (mezcla de recorte y extensión), simulando un usuario real.

  Las 7 primeras replican exactamente los 7 casos de la tabla de validación
  de la Fase 3, aplicados a un área real distinta cada vez, para probar la
  equivalencia también en el contexto de la Lógica Adaptativa ya validada
  por separado.
- `test_hay_al_menos_una_secuencia_con_recorte_y_una_con_extension_maxima`:
  test de guardia que confirma explícitamente en el código (no solo en la
  documentación) que la suite cubre tanto recorte como extensión máxima.
- No se modificó ningún archivo de `services/` ni de `api/`: la suite pasó
  al primer intento salvo por un error en la propia fixture de datos de test
  (ver sección 6), no en el código de aplicación — es decir, **no se detectó
  ninguna divergencia real entre formulario y chatbot** que requiriera
  corrección de flujo.

## 3. Decisiones técnicas relevantes

- **Generación del `respuestas_dict` compartido:** en vez de escribir a mano
  qué preguntas exactas recibe cada método (lo cual sería frágil y podría
  "hacer que dé igual" artificialmente), la suite reutiliza
  `adaptive_flow_service.preguntas_a_formular` — el mismo código de
  producción — para derivar automáticamente, a partir de una secuencia
  "candidata" de hasta 5 valores por área, exactamente qué respuestas se
  habrían registrado. Esto garantiza que el insumo enviado a ambos métodos
  sea el que un usuario real produciría, sin overfitting del test.
- **Conducción del chatbot turno por turno:** se implementó
  `_ejecutar_chatbot_completo`, que llama a `procesar_mensaje` en bucle,
  leyendo en cada turno `estado["pregunta_actual_id"]` (nunca asumiendo el
  orden de antemano) y respondiendo con el valor correspondiente de
  `respuestas_dict`. Esto verifica también, de forma indirecta, que el
  chatbot pregunta exactamente las mismas `pregunta_id` que el formulario
  habría formulado.
- **Comparación de Top 5 con datos reales:** se usa `data/carreras.csv` y
  `calcular_matriz_covarianza` reales (no mockeados), cacheados una sola vez
  por módulo vía fixture `scope="module"`, replicando cómo se cachea
  `inv_cov_matrix` en producción (`app/main.py`).
- No fue necesario tocar `.github/workflows/ci.yml`: dado que ese workflow ya
  ejecuta `pytest app/tests/` (ver Fase 0), el nuevo archivo se incorpora
  automáticamente a la suite de CI sin configuración adicional.

## 4. Cómo se verificaron los criterios de aceptación

| Criterio | Método de verificación | Resultado |
|---|---|---|
| El test de equivalencia pasa para las 10+ secuencias definidas, sin ajustar manualmente ninguna para que "dé igual" artificialmente | `pytest app/tests/test_fase9c_equivalencia_metodos.py -v` | **12/12 tests pasados** (11 secuencias parametrizadas + 1 test de guardia de cobertura). Las secuencias se derivan mediante `preguntas_a_formular` real, no hardcodeadas por resultado. |
| El test queda incorporado a la suite automatizada del proyecto (se ejecuta en cada corrida de CI, no solo manualmente) | El archivo vive en `backend/app/tests/`, recogido automáticamente por `pytest app/tests/`, el mismo comando que ya ejecuta `.github/workflows/ci.yml` (job `backend`, definido en la Fase 0) | El archivo se descubre y ejecuta sin cambios de configuración; se confirmó corriendo la suite completa del backend. |

## 5. Pruebas realizadas

- `backend/app/tests/test_fase9c_equivalencia_metodos.py` (nuevo, 12 tests):
  cubre la equivalencia formulario/chatbot para 11 secuencias + 1 test de
  cobertura de la propia suite.
- Suite completa del backend re-ejecutada para confirmar que nada se rompió:
  `pytest app/tests/ -q` → **109 passed** (incluye Fases 0–9b más los 12
  nuevos de esta fase).

```
$ pytest app/tests/test_fase9c_equivalencia_metodos.py -v
...
12 passed in 0.44s

$ pytest app/tests/ -q
109 passed, 2 warnings in 3.55s
```

## 6. Problemas encontrados y solución

- Al escribir la secuencia `perfil_mixto_realista_variado_por_area`, el
  primer intento definió `"ciencia_tecnologia": [5, 4, 3, 3]` (4 valores).
  Como la primera respuesta (5) habilita un presupuesto de 5 preguntas y
  ninguna de las siguientes bajó de 3, el algoritmo intentaba formular la 5ª
  pregunta del área y la fixture de test se quedaba sin valores
  (`IndexError`). **Esto era un error en el dato de prueba, no en el código
  de aplicación** (el algoritmo se comportó exactamente como especifica la
  Fase 3: no cortó el área porque ninguna respuesta bajó de 3). Se corrigió
  agregando un 5º valor a la secuencia (`[5, 4, 3, 3, 4]`). No se modificó
  ningún archivo de `services/`.
- No se encontró ninguna otra divergencia entre formulario y chatbot en las
  11 secuencias evaluadas: el diseño ya existente desde la Fase 6 (ambos
  métodos delegan en `adaptive_flow_service.preguntas_a_formular` y
  `adaptive_flow_service.construir_vector_usuario`) demostró ser
  efectivamente compartido y sin duplicación de lógica.

## 7. Estado final de la fase

**CERRADA.** Los dos criterios de aceptación se cumplen: la suite de
equivalencia pasa para 11 secuencias (más de las 10 exigidas) sin ajustes
artificiales, y queda incorporada a `app/tests/`, por lo que se ejecuta en
cada corrida de CI junto con el resto de la suite del backend.

## 8. Siguientes pasos

Con la garantía central del sistema (equivalencia formulario/chatbot) ahora
cubierta por tests automatizados y sin divergencias pendientes, el proyecto
queda listo para la Fase 9d — Accesibilidad (WCAG AA), que auditará todas
las pantallas construidas hasta ahora (landing, formulario, chatbot,
resultados, historial), incluyendo las dos formas de completar el test
verificadas en esta fase.
