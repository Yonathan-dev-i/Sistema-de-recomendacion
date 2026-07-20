# Fase 2 — Motor de recomendación (Mahalanobis) como servicio puro

## 1. Objetivo de la fase

Tener el algoritmo de recomendación (Distancia de Mahalanobis) funcionando y
testeado de forma aislada, expuesto en un endpoint de prueba, sin depender
todavía del flujo de test completo (formulario/chatbot).

## 2. Alcance realizado

- **`backend/app/services/recomendacion_service.py`** — módulo puro (sin
  FastAPI ni sesión de BD dentro de las funciones de cálculo):
  - `calcular_matriz_covarianza(X)`: estima `cov_matrix = np.cov(X, rowvar=False)`
    y su inversa, con el manejo de estabilidad numérica exigido: intento
    directo → shrinkage (`+ 1e-6 * I`) si está mal condicionada
    (`cond > 1e10`) → pseudo-inversa de Moore-Penrose (`np.linalg.pinv`) como
    último recurso.
  - `calcular_distancias(x_usuario, X, inv_cov_matrix)`: vector de 37
    distancias usando `scipy.spatial.distance.mahalanobis`.
  - `calcular_recomendacion(...)`: función central pura — normaliza distancias
    a `afinidad_pct` (0-100, relativa al propio ranking del usuario), ordena,
    toma el Top N, y calcula `fortalezas`, `areas_por_mejorar` y `explicacion`
    por reglas para cada resultado.
- **`backend/app/services/recomendacion_repository.py`** — única pieza que
  toca la base de datos: `cargar_matriz_carreras(db)` lee las 37 carreras +
  sus `CarreraPuntaje` desde PostgreSQL y arma `(ids, nombres, X)` en el orden
  exacto de `AREAS`.
- **Caché al arranque:** el `lifespan` de `app/main.py` ahora, además de la
  validación de la Fase 1, abre una sesión de BD una sola vez, carga la matriz
  de carreras, calcula `inv_cov_matrix` y lo guarda todo en
  `app.state.recomendacion_cache` (`RecomendacionCache`, un dataclass). El
  cálculo **no se repite en cada request**.
- **`backend/app/schemas/recomendacion.py`** — `VectorUsuarioIn` valida que el
  vector recibido tenga **exactamente** las 17 claves de `AREAS` (ni de más ni
  de menos) y que todos los valores estén en `[1.0, 5.0]`, antes de llegar al
  motor de cálculo.
- **`POST /recomendacion`** (`backend/app/api/recomendacion.py`): recibe
  `{"vector_usuario": {...}}`, delega en `calcular_recomendacion` usando el
  caché de `app.state`, y devuelve el contrato exacto especificado en el
  prompt maestro (`vector_usuario` + `resultados[]` con `carrera_id`,
  `distancia_mahalanobis`, `afinidad_pct`, `explicacion`, `fortalezas`,
  `areas_por_mejorar`).
- **Tests** (`backend/app/tests/test_mahalanobis.py`): los 4 casos exigidos
  por el prompt maestro + 2 adicionales, corriendo sobre los datos reales de
  `data/carreras.csv` (no mockeados), sin depender de PostgreSQL ni de FastAPI.

## 3. Decisiones técnicas relevantes

- **La matriz `X` para el motor se carga desde PostgreSQL en producción**
  (vía `recomendacion_repository.cargar_matriz_carreras`), **pero los tests
  unitarios usan `data/loaders.cargar_carreras()`** directamente (el mismo
  CSV que alimentó el seed). Razón: los tests de un algoritmo matemático puro
  no deberían depender de que haya una base de datos corriendo — y como el
  seed de la Fase 1 garantiza que ambas fuentes son idénticas, el test sigue
  siendo representativo del comportamiento real.
- **La conversión a `afinidad_pct` se hace sobre las 37 distancias completas,
  antes de recortar al Top N.** Esto es intencional y sigue el orden de las
  secciones 4 y 5 de la especificación: la normalización 0-100% es relativa a
  *todo* el ranking del estudiante, no solo a sus 5 mejores opciones — si se
  normalizara solo sobre el Top 5, la carrera #5 casi nunca llegaría a 0%,
  distorsionando la comparación entre estudiantes distintos.
- **El caché vive en `app.state`, no en una variable de módulo global ni en
  Redis.** Se eligió `app.state` (mecanismo nativo de FastAPI) para esta fase
  por simplicidad, ya que basta con un solo proceso backend; si se necesitara
  compartir el caché entre múltiples workers/procesos, la migración natural
  sería mover `RecomendacionCache` a Redis, sin tocar `recomendacion_service.py`
  (que ya recibe `inv_cov_matrix` como parámetro, no como global).
- **`fortalezas` se ordena por el valor del propio usuario (`x_usuario`), no
  por la brecha con la carrera.** La especificación pide "ordenadas de mayor a
  menor valor del usuario", que es distinto de ordenar por qué tan por encima
  del perfil de la carrera está el usuario; se implementó literalmente como
  se describe.
- **Se optó por devolver `fortalezas`/`areas_por_mejorar` como listas de
  `area_key`** (no de labels legibles) en el contrato de la API, igual que en
  el ejemplo de salida del prompt maestro (`["matematica", "pensamiento_analitico", ...]`);
  la traducción a label legible es responsabilidad del frontend (Fase 4+), que
  ya tiene acceso a `GET /areas` para mapear `key → label`.

## 4. Cómo se verificaron los criterios de aceptación

Se usó PostgreSQL real (con las 37 carreras ya sembradas en la Fase 1) para
levantar el backend completo y probar el endpoint en vivo, no solo con tests.

| Criterio | Método de verificación | Resultado |
|---|---|---|
| `POST /recomendacion` con un vector de prueba devuelve un Top 5 coherente (la carrera más cercana aparece primero) | Backend levantado + `curl -X POST /recomendacion` con un vector orientado a tecnología/matemática | ✅ Top 1 con distancia 0.0 y `afinidad_pct: 100.0`; resultados ordenados de mayor a menor afinidad, con `fortalezas`/`areas_por_mejorar` coherentes |
| Todos los tests de Mahalanobis pasan | `pytest app/tests/test_mahalanobis.py -v` | ✅ 6/6 (los 4 exigidos + 2 adicionales) |
| El cálculo no se re-ejecuta desde cero en cada request | Inspección de `app/main.py`: `inv_cov_matrix` se calcula una vez en `lifespan` y se lee de `app.state` en el router — el router no importa `calcular_matriz_covarianza` | ✅ Confirmado por código; el log de arranque muestra la consulta a `carreras`/`carrera_puntajes` una sola vez, no en cada `POST /recomendacion` |
| Linters pasan sin errores | `ruff check app/` | ✅ "All checks passed!" |
| Suite completa de tests (Fase 0+1+2) sigue pasando | `pytest app/tests/ -v` | ✅ 16/16, incluyendo `test_health.py` (que ahora ejercita el `lifespan` completo con BD real) |

## 5. Pruebas realizadas

- **Automatizadas — los 4 casos exigidos:**
  1. `test_matriz_covarianza_se_invierte_sin_error`: verifica forma `(17,17)`,
     valores finitos, y que `cov_matrix @ inv_cov_matrix ≈ I`.
  2. `test_vector_de_distancias_tiene_longitud_37`: 37 distancias, todas ≥ 0.
  3. `test_carrera_con_distancia_minima_es_el_top_1`: usando el perfil exacto
     de una carrera como vector de usuario, confirma que esa misma carrera
     (distancia mínima) es el resultado #1 devuelto por `calcular_recomendacion`.
  4. `test_vector_usuario_promedio_general_no_lanza_excepciones`: vector =
     promedio de las 17 columnas de `X`, sin excepciones, afinidades en [0,100].
  - Adicional: verificación de orden monótono del Top 5 y de que la
    normalización global (top_n=37) produce exactamente 100% y 0% en los
    extremos.
- **Manuales, end-to-end contra PostgreSQL real:**
  - Backend levantado con `uvicorn`, confirmando en el log que la consulta a
    `carreras`/`carrera_puntajes` corre una sola vez durante el `lifespan`.
  - `POST /recomendacion` probado con un vector real vía `curl`, inspeccionando
    el JSON completo de respuesta contra el contrato del prompt maestro.

## 6. Problemas encontrados y solución

- Ninguno bloqueante. El único ajuste de diseño fue decidir en qué punto de la
  tubería (antes o después de recortar al Top 5) se normalizan las distancias
  a porcentaje — resuelto siguiendo el orden literal de las secciones 4 y 5 de
  la especificación (normalizar primero sobre las 37, recortar después).
- `ruff` marcó inicialmente el uso de `X[i]` como parámetro no tipado en
  algunos borradores; se resolvió tipando explícitamente `np.ndarray` en las
  firmas de las funciones públicas del servicio.

## 7. Estado final de la fase

**CERRADA.** Los 3 criterios de aceptación se verificaron de forma
reproducible: Top 5 coherente vía `curl`, 6/6 tests de Mahalanobis (superset de
los 4 exigidos), y caché de `inv_cov_matrix` confirmado tanto por inspección de
código como por el log de arranque (una sola consulta a BD, no una por request).

## 8. Siguientes pasos

Con el motor de recomendación aislado y testeado, la Fase 3 puede enfocarse en
la Lógica Adaptativa de Preguntas, en paralelo (ambas dependen solo de la
Fase 1, según el prompt maestro):

- Implementar `services/adaptive_flow_service.py` con `preguntas_a_formular`.
- Implementar `construir_vector_usuario` (promedio Likert por área sobre las
  preguntas realmente formuladas), que es exactamente el `vector_usuario` que
  `recomendacion_service.calcular_recomendacion` ya sabe consumir — no requiere
  ningún cambio en el motor de Mahalanobis construido en esta fase.
