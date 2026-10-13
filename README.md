# Sistema Inteligente de Orientación Vocacional — UNA Puno

Monorepo del sistema de orientación vocacional basado en la Distancia de Mahalanobis,
para la Universidad Nacional del Altiplano (UNA Puno).

## Stack

- **Frontend:** Next.js 15 (App Router) + TypeScript + Tailwind CSS
- **Backend:** FastAPI (Python 3.11+) + SQLAlchemy 2.0 async + PostgreSQL
- **Cálculo científico:** NumPy + SciPy (Distancia de Mahalanobis)
- **Chatbot:** máquina de estados basada en reglas (sin LLMs)

## Estado del proyecto

Las 15 fases del prompt maestro (`docs/prompt-maestro.md`) están construidas.
Ver el índice completo, con el resumen y el documento de cierre de cada una,
en [`docs/fases/README.md`](docs/fases/README.md).

🟢 14 de las 15 fases están **CERRADAS**. La Fase 9f (Performance y
despliegue) está **PARCIAL**: la configuración de despliegue con Docker está
completa y verificada por build, pero falta que el equipo ejecute un
`docker compose up` de punta a punta y una prueba en un dispositivo móvil
físico real — ver el detalle en
[`docs/fases/fase-9f-performance-despliegue.md`](docs/fases/fase-9f-performance-despliegue.md).

## Cómo correr el proyecto localmente

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # ajusta DATABASE_URL si tu Postgres no usa las credenciales por defecto

# Migraciones y datos iniciales
alembic upgrade head
python -m app.scripts.seed_data   # idempotente: se puede correr varias veces

uvicorn app.main:app --reload --port 8000
```

Verificar:
- `GET http://localhost:8000/health` → `{"status": "ok", ...}`
- `GET http://localhost:8000/areas` → 17 áreas
- `GET http://localhost:8000/preguntas` → 34 preguntas
- `GET http://localhost:8000/carreras` → 37 carreras
- `GET http://localhost:8000/carrera/1` → detalle con perfil de 17 áreas
- `POST http://localhost:8000/recomendacion` con body `{"vector_usuario": {"matematica": 5, "...": "..."}}` (17 claves, ver `app/core/constants.py`) → Top 5 con `afinidad_pct`

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Verificar: abrir `http://localhost:3000` — debe mostrar la landing page completa
(Hero, ¿Cómo funciona?, Métodos del Test, Explora las 37 carreras, Beneficios,
FAQ). Desde ahí, el botón "Realizar Test" lleva a `/test` (selección de
método) y "Comenzar Test" en la tarjeta de Test Tradicional lleva al
formulario real (`/test/tradicional`, Fase 4).

### Linters

```bash
# Backend
cd backend && ruff check app/

# Frontend
cd frontend && npx eslint src/
```

## Despliegue (Docker)

El stack completo (PostgreSQL + backend + frontend) se despliega con
`docker compose`, desde la raíz del repositorio:

```bash
cp .env.example .env
# completar POSTGRES_PASSWORD, JWT_SECRET_KEY, CORS_ORIGINS y
# NEXT_PUBLIC_API_URL con los valores reales del entorno de destino
docker compose up -d --build
```

- Frontend: `http://<host>:3000`
- Backend: `http://<host>:8000` (verificar con `GET /health`)

Las migraciones de Alembic corren automáticamente al levantar el
contenedor del backend (ver `backend/entrypoint.sh`), así que no hace
falta correrlas a mano. Detalle completo, decisiones de diseño y estado
de verificación de este despliegue en
[`docs/fases/fase-9f-performance-despliegue.md`](docs/fases/fase-9f-performance-despliegue.md).

## Estructura

```
.
├── backend/
│   ├── app/
│   │   ├── api/          # Routers (health, dominio: areas/preguntas/carreras)
│   │   ├── core/         # Config, conexión a BD, constants (AREAS), startup checks
│   │   ├── services/     # recomendacion_service.py (Mahalanobis, puro) + repository
│   │   ├── models/        # Modelos SQLAlchemy (Usuario, Area, Pregunta, Carrera, ...)
│   │   ├── schemas/       # Schemas Pydantic
│   │   ├── data/          # JSON/CSV fuente + loaders.py (preguntas, áreas, carreras)
│   │   ├── scripts/       # seed_data.py (idempotente)
│   │   └── tests/         # Tests pytest
│   ├── migrations/        # Alembic (modo async)
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/            # Rutas (App Router)
│       └── components/     # Componentes UI
├── docs/fases/            # Documentación de cierre de cada fase
└── .github/workflows/     # CI (lint + test)
```