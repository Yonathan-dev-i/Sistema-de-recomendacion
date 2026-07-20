# Fase 9f — imagen de producción del backend FastAPI.
#
# Una sola etapa (no hay compilación de assets como en el frontend): instala
# dependencias desde requirements.txt sobre python:3.11-slim, corre las
# migraciones de Alembic al arrancar el contenedor (no en build time, porque
# la base de datos todavía no existe/no es alcanzable durante `docker build`)
# y levanta uvicorn.
FROM python:3.11-slim

# Evita que pip guarde caché (imagen más chica) y que Python genere .pyc /
# bufferee stdout (logs en tiempo real en `docker logs`).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# libpq-dev + gcc: requeridos para compilar dependencias con extensiones C
# (ej. algunos backends de asyncpg/cryptography en imágenes slim). Se
# eliminan del apt-cache tras instalar para no inflar la imagen final.
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Usuario no-root: buena práctica de seguridad para contenedores expuestos.
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# `entrypoint.sh` corre las migraciones pendientes antes de levantar uvicorn,
# para que un despliegue nuevo (o un `docker compose up` desde cero) quede
# con el esquema al día sin un paso manual aparte.
COPY --chown=appuser:appuser entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
