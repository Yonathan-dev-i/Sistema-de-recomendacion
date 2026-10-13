# Fase 1 — Datos base y modelos

## 1. Objetivo de la fase

Tener el dominio de datos completo en PostgreSQL: las 17 áreas, las 34 preguntas
del banco vocacional y las 37 carreras (con su perfil de 17 puntajes cada una),
accesibles a través de endpoints de solo lectura, con migraciones versionadas y
un seed reproducible.

## 2. Alcance realizado

- **Datasets fuente** (usados solo para el seed, no leídos en tiempo de request):
  - `backend/app/data/areas.json`: 17 áreas, en el orden fijo que define el
    vector vocacional.
  - `backend/app/data/preguntas.json`: 34 preguntas (2 por área × 17 áreas,
    reducido desde las 5 por área originales a pedido del equipo — ver nota
    en la sección 6), con `id` 1-34 sin huecos.
  - `backend/app/data/carreras.csv`: 37 carreras × 17 columnas de puntaje
    (escala 1-5), transcritas directamente del prompt maestro.
  - `backend/app/data/loaders.py`: funciones puras que leen estos 3 archivos.
- **Constante compartida:** `backend/app/core/constants.py` define `AREAS`
  (lista de 17 keys en el orden canónico), usada por modelos, seed y — en fases
  futuras — por el motor de Mahalanobis.
- **Validación de arranque:** `backend/app/core/startup_checks.py` verifica, en
  el evento `lifespan` de FastAPI, que `AREAS`, `areas.json` y las columnas de
  `carreras.csv` coincidan exactamente (mismo orden, mismo contenido, 17
  elementos), y que el banco de preguntas tenga 34 entradas válidas. Si algo no
  coincide, la aplicación **no arranca** y lanza un `RuntimeError` explícito.
- **Modelos SQLAlchemy 2.0** (`backend/app/models/`):
  - `Usuario`, `Area`, `Pregunta`, `Carrera` + `CarreraPuntaje` (tabla de unión
    normalizada para el perfil de 17 puntajes por carrera), `IntentoTest`,
    `RespuestaTest`.
  - Se registran todos en `app/models/__init__.py` para que Alembic los
    autodetecte.
- **Alembic** configurado en modo async (`migrations/`), conectado a la misma
  `DATABASE_URL` que el resto de la app vía `Settings`. Migración inicial
  autogenerada y aplicada, creando las 7 tablas del dominio.
- **Seed idempotente:** `backend/app/scripts/seed_data.py` — corre
  `run_startup_checks()` antes de escribir nada, y luego inserta áreas,
  preguntas y carreras solo si no existen ya (por clave natural: `key`, `id`,
  `nombre`). Puede ejecutarse múltiples veces sin duplicar filas.
- **Endpoints de solo lectura** (`backend/app/api/dominio.py`), montados junto
  al router de salud existente:
  - `GET /areas` → las 17 áreas ordenadas.
  - `GET /preguntas` → las 34 preguntas ordenadas por id.
  - `GET /carreras` → listado resumido de las 37 carreras.
  - `GET /carrera/{id}` → detalle de una carrera + su perfil de 17 áreas
    (404 si no existe).
- **Tests** (`backend/app/tests/test_fase1_datos.py`): 8 tests nuevos que
  verifican el tamaño y alineación de `AREAS`, el banco de preguntas (34
  entradas, ids 1-34 sin huecos, 2 preguntas por área) y que la validación de
  arranque falla explícitamente ante datos corruptos (test con `monkeypatch`).

## 3. Decisiones técnicas relevantes

- **Perfil de carrera normalizado en una tabla aparte (`carrera_puntajes`)**
  en vez de una columna JSON de 17 valores en `carreras`. Razón: permite
  consultas SQL directas por área (ej. "carreras con matemática ≥ 4") sin
  deserializar JSON, a costa de una fila extra por (carrera, área) — aceptable
  dado que son solo 37 × 17 = 629 filas.
- **`IntentoTest.vector_usuario` y `top5_resultado` sí son columnas JSON.**
  Razón inversa: esos datos son un snapshot de un cálculo (resultado final de
  un intento), no algo que se necesite filtrar por SQL — JSON es más simple y
  evita una tabla adicional para 17 valores que solo se leen como bloque.
- **`Pregunta.id` no es autoincremental "libre":** se usan explícitamente los
  ids 1-34 del `preguntas.json` original (`db.add(Pregunta(id=..., ...))`), para
  que el id de una pregunta sea estable entre entornos y coincida con el usado
  en el frontend/chatbot de fases posteriores.
- **`AREAS` como single source of truth del orden del vector:** ni `areas.json`
  ni `carreras.csv` "mandan" por sí solos; ambos se validan contra la constante
  Python en el arranque. Esto se decidió para que un futuro cambio accidental
  en el orden de un archivo de datos falle ruidosamente (`RuntimeError` al
  arrancar) en vez de silenciosamente desalinear el vector de usuario con la
  columna equivocada en el motor de Mahalanobis (Fase 2).
- **Migración con Alembic en modo async** (`alembic init -t async`), reutilizando
  `Settings.database_url` en `migrations/env.py` en vez de hardcodear la URL en
  `alembic.ini`, para que dev/staging/prod usen exactamente la misma fuente de
  configuración que la aplicación.
- **Se migró `@app.on_event("startup")` (Fase 0) a `lifespan`** al integrar la
  validación de arranque, porque `on_event` ya está deprecado en FastAPI y
  generaba warnings en cada test.

## 4. Cómo se verificaron los criterios de aceptación

Se instaló PostgreSQL 16 localmente (`apt-get install postgresql`) para
verificar contra una base de datos real, no simulada.

| Criterio | Método de verificación | Resultado |
|---|---|---|
| Migraciones aplican sin error | `alembic revision --autogenerate` + `alembic upgrade head` | ✅ 7 tablas creadas (`areas`, `preguntas`, `carreras`, `carrera_puntajes`, `intentos_test`, `respuestas_test`, `usuarios`) |
| Seed carga los 3 datasets correctamente | `python -m app.scripts.seed_data` + `SELECT count(*)` en cada tabla | ✅ 17 áreas, 34 preguntas, 37 carreras, 629 puntajes (37×17) |
| Seed es idempotente | Seed ejecutado dos veces seguidas | ✅ Mismos conteos tras la 2ª corrida, sin duplicados ni errores |
| Los 4 endpoints responden con datos reales | Backend levantado + `curl` a cada endpoint | ✅ `/areas`→17, `/preguntas`→34, `/carreras`→37, `/carrera/1`→200, `/carrera/999`→404 |
| Linters pasan sin errores | `ruff check app/` | ✅ "All checks passed!" (tras corregir 6 hallazgos: forward-refs sin `TYPE_CHECKING`, `enum.Enum`→`enum.StrEnum`, `datetime.timezone.utc`→`datetime.UTC`, orden de imports) |
| Tests pasan | `pytest app/tests/ -v` | ✅ 10/10 (2 de Fase 0 + 8 nuevos de Fase 1), sin warnings propios |

## 5. Pruebas realizadas

- **Automatizadas:** los 8 tests nuevos de `test_fase1_datos.py`, incluyendo un
  caso negativo (`monkeypatch` para simular un área faltante) que confirma que
  `validar_alineacion_areas()` lanza `RuntimeError` en vez de fallar en
  silencio.
- **Manuales, contra una base de datos PostgreSQL real:**
  - Migración autogenerada inspeccionada antes de aplicar (revisé que creara
    las 7 tablas esperadas, con sus foreign keys y el `CheckConstraint` de
    `respuesta_test.respuesta BETWEEN 1 AND 5`).
  - Seed corrido dos veces, verificando conteos idénticos en la segunda corrida
    (idempotencia real, no solo el diseño del código).
  - Servidor levantado con `uvicorn` y los 4 endpoints probados con `curl`,
    incluyendo el caso 404 explícito para una carrera inexistente.

## 6. Problemas encontrados y solución

- **Bug real en `seed_data.py`:** la primera versión llamaba
  `asyncio.run(run_seed())` seguido de `asyncio.run(engine.dispose())` como dos
  corridas de asyncio separadas, lo que producía un error de "event loop is
  closed" al cerrar la conexión de asyncpg. Se corrigió moviendo
  `await engine.dispose()` **dentro** de `run_seed()`, para que corra en el
  mismo event loop que el resto del seed.
- **6 hallazgos de `ruff`** tras escribir los modelos (forward references sin
  `TYPE_CHECKING`, `enum.Enum` en vez de `enum.StrEnum`, uso de
  `datetime.timezone.utc` en vez de `datetime.UTC`, orden de imports). Se
  corrigieron todos antes de cerrar la fase; `ruff check app/` termina limpio.
- **PostgreSQL se detiene entre comandos** en este entorno de ejecución (no es
  un servicio persistente tipo systemd) — cualquier verificación contra la base
  de datos requirió reiniciar el servicio (`service postgresql start`) antes de
  cada ronda de pruebas. Esto es una particularidad del entorno de desarrollo
  de esta sesión, no del proyecto en sí.
- **Reducción posterior del banco de preguntas (85 → 34).** A pedido del
  equipo, después del cierre original de esta fase se redujo el banco de 5 a
  2 preguntas por área (17 × 2 = 34 en total), conservando las 2 primeras
  preguntas de cada área en su orden original. La Lógica Adaptativa de
  Preguntas (Fase 3) no necesitó cambios de código porque ya acotaba el
  presupuesto al tamaño real del área (`min(limite_area, len(preguntas_area))`);
  solo se actualizaron `data/preguntas.json`, la validación de arranque, los
  límites de `TestTradicionalIn` y los tests que asumían 85/5 como valores
  fijos. Detalle completo en el historial de esta conversación de
  construcción del proyecto.

## 7. Estado final de la fase

**CERRADA.** Los 6 criterios de aceptación se verificaron de forma reproducible
contra una base de datos PostgreSQL real (no mockeada), incluyendo un ciclo
completo de migración + seed + lectura vía API.

## 8. Siguientes pasos

Con el dominio de datos completo y expuesto, la Fase 2 puede enfocarse en el
motor de cálculo:

- Implementar la Distancia de Mahalanobis (`services/mahalanobis.py`) usando
  NumPy/SciPy sobre la matriz de 37×17 carreras (ya disponible vía
  `data/loaders.py` o consultando `Carrera`/`CarreraPuntaje`).
- Definir la matriz de covarianza (o su inversa) a partir del propio dataset de
  carreras, y las funciones de conversión de distancia a "afinidad %".
- Tests unitarios del motor con casos conocidos (ej. un vector de usuario
  idéntico al perfil de una carrera debe dar distancia 0 / afinidad 100%).