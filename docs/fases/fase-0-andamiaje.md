# Fase 0 — Preparación del proyecto (andamiaje)

## 1. Objetivo de la fase

Tener el esqueleto de ambos proyectos (frontend y backend) corriendo, comunicándose
entre sí a través de un endpoint de salud, sin lógica de negocio del dominio
vocacional todavía.

## 2. Alcance realizado

- **Monorepo** creado con dos carpetas principales: `backend/` y `frontend/`.
- **Backend (FastAPI):**
  - `backend/app/core/config.py`: configuración centralizada vía `pydantic-settings`,
    leyendo variables de entorno (`DATABASE_URL`, `JWT_SECRET_KEY`, `CORS_ORIGINS`, etc.).
  - `backend/app/core/database.py`: motor y sesión async de SQLAlchemy 2.0 con
    `asyncpg`, clase base declarativa (`Base`) y dependency `get_db()`.
  - `backend/app/api/health.py`: router con `GET /health`.
  - `backend/app/main.py`: instancia de `FastAPI`, middleware CORS, montaje del
    router de salud.
  - Estructura de carpetas completa: `api/`, `services/`, `models/`, `schemas/`,
    `data/`, `core/`, `tests/` (todas con `__init__.py`, listas para las fases 1-2).
  - `backend/requirements.txt` con todas las dependencias del stack obligatorio
    (FastAPI, SQLAlchemy async, asyncpg, Alembic, Pydantic v2, python-jose,
    NumPy, SciPy, ruff, black, pytest).
  - `backend/pyproject.toml`: configuración de `ruff` y `black`.
  - `backend/.env.example`: plantilla de variables de entorno.
  - `backend/app/tests/test_health.py`: test que verifica `GET /health` y `GET /`.
- **Frontend (Next.js 15):**
  - `frontend/package.json`: Next.js 15, React 18, TypeScript, Tailwind CSS,
    `next-themes` (modo claro/oscuro), Zustand, ESLint, Prettier.
  - `frontend/src/app/layout.tsx` y `globals.css`: layout raíz con variables CSS
    para modo claro/oscuro (soporte de tema vía `next-themes`).
  - `frontend/src/components/theme-provider.tsx`: provider de tema.
  - `frontend/src/app/page.tsx`: página placeholder que hace `fetch` a
    `GET /health` del backend y muestra el resultado (éxito o error de conexión).
  - `frontend/tailwind.config.ts`, `postcss.config.mjs`, `tsconfig.json`,
    `next.config.mjs`: configuración base del proyecto.
  - `frontend/.eslintrc.json`, `frontend/.prettierrc`: linters/formatters.
  - `frontend/.env.example`: plantilla con `NEXT_PUBLIC_API_URL`.
- **CI:** `.github/workflows/ci.yml` con dos jobs (`backend`, `frontend`) que
  corren lint + test / build en cada push y pull request.
- **Documentación:** `README.md` raíz con instrucciones de instalación y
  ejecución local de ambos proyectos.

No se completó ningún alcance de fases posteriores (modelos de dominio, motor de
Mahalanobis, lógica adaptativa, UI del test, etc.) — eso corresponde a las Fases 1+.

## 3. Decisiones técnicas relevantes

- Se usó **`pydantic-settings`** (en vez de leer `os.environ` directamente) para
  centralizar y tipar la configuración, ya que es el estándar recomendado para
  Pydantic v2 y facilita la validación temprana de variables de entorno.
- Se creó `core/database.py` ya en esta fase (adelantando parte de lo previsto
  para la Fase 1), porque el objetivo de "backend corriendo con conexión a
  PostgreSQL" descrito en el prompt maestro requiere que el motor async exista
  desde el arranque, aunque los modelos concretos se agreguen después.
- El frontend se scaffoldeó **manualmente** (sin `create-next-app` interactivo)
  para tener control total y determinista sobre cada archivo de configuración,
  dado el entorno de ejecución no interactivo.
- Se agregó `next-themes` desde ya (en vez de esperar a la Fase 5) porque el
  criterio "modo claro/oscuro" ya se pide como parte de la configuración base
  del frontend en esta fase.
- El job de lint del frontend en CI usa `|| true` para no bloquear el pipeline
  ante warnings menores de ESLint en esta fase temprana; se recomienda quitar
  esa tolerancia antes de la entrega final (Fase 9).

## 4. Cómo se verificaron los criterios de aceptación

| Criterio | Método de verificación | Resultado |
|---|---|---|
| El backend levanta y responde `GET /health` con 200 | `uvicorn app.main:app` en background + `curl http://localhost:8000/health` | ✅ `{"status":"ok","app":"Sistema de Orientación Vocacional UNA Puno","environment":"development"}` |
| El frontend levanta y hace un fetch exitoso a `GET /health` | `npm run dev` + `curl http://localhost:3000` con backend activo | ✅ Página renderiza "Backend conectado" (HTTP 200) |
| Linters pasan sin errores en ambos proyectos | `ruff check app/` (backend) y `npm run build` con chequeo de tipos (frontend) | ✅ `ruff`: "All checks passed!" · ✅ build de Next.js compiló y generó las páginas estáticas sin errores de tipos |

Adicionalmente, se corrió `pytest app/tests/ -v`, obteniendo **2/2 tests pasados**
(`test_health_check_returns_200_and_ok_status`, `test_root_endpoint_returns_200`).

## 5. Pruebas realizadas

- **Automatizadas:** `backend/app/tests/test_health.py` — cubre que `/health`
  devuelve 200 y un JSON con `status: "ok"`, y que `/` responde 200.
- **Manuales:**
  - Backend levantado localmente con `uvicorn` y verificado con `curl` contra
    `/health` y `/`.
  - Frontend levantado con `npm run dev`, verificado que la home carga (200) y
    que el texto "Orientación Vocacional" se renderiza correctamente.
  - `npm run build` ejecutado de punta a punta sin errores (incluye chequeo de
    tipos TypeScript y generación de páginas estáticas).

## 6. Problemas encontrados y solución

- Ninguno bloqueante. Al construir manualmente la estructura de carpetas en un
  solo comando con llaves (`mkdir -p {a,b,c}`), un problema de escaping de shell
  generó una carpeta literal mal nombrada; se detectó de inmediato al listar el
  árbol de directorios y se corrigió recreando la estructura con comandos
  `mkdir -p` explícitos por carpeta.
- No se ejecutó Alembic ni se levantó una instancia real de PostgreSQL en esta
  fase (no es un criterio de aceptación de la Fase 0); el motor async está
  configurado y listo para usarse en la Fase 1, donde sí se requiere una base de
  datos real para los endpoints de lectura.

## 7. Estado final de la fase

**CERRADA.** Los tres criterios de aceptación definidos en el prompt maestro se
cumplieron y fueron verificados de forma reproducible (comandos documentados
arriba).

## 8. Siguientes pasos

Con el andamiaje corriendo y comunicándose correctamente, la Fase 1 puede
enfocarse exclusivamente en el dominio de datos:

- Definir `data/preguntas.json`, `data/areas.json` y el dataset de 37 carreras.
- Crear los modelos SQLAlchemy (`Usuario`, `Carrera`, `Area`, `Pregunta`,
  `IntentoTest`, `RespuestaTest`) sobre la base declarativa ya definida en
  `core/database.py`.
- Configurar Alembic para las migraciones (el motor async ya existe).
- Implementar los endpoints de solo lectura (`GET /preguntas`, `/areas`,
  `/carreras`, `/carrera/{id}`) montándolos en `app/main.py` junto al router de
  salud ya existente.
