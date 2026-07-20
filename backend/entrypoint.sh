#!/bin/sh
# Fase 9f — entrypoint del contenedor backend.
#
# Corre las migraciones de Alembic (esquema al día) antes de levantar el
# proceso principal (uvicorn, vía "$@" con el CMD del Dockerfile). Así un
# despliegue nuevo o un `docker compose up` desde una base de datos vacía
# terminan con el esquema creado sin un paso manual aparte.
set -e

echo "[entrypoint] Aplicando migraciones de Alembic..."
alembic upgrade head

echo "[entrypoint] Migraciones al día. Iniciando: $*"
exec "$@"
