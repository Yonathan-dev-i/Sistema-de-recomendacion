# Fase 9f — imagen de producción del frontend Next.js.
#
# Multi-stage: la etapa `builder` instala TODAS las dependencias (incluidas
# devDependencies, necesarias para compilar TS/Tailwind) y corre `next
# build`. La etapa final `runner` copia únicamente la salida de
# `output: "standalone"` (server.js + node_modules mínimos, ver
# `next.config.mjs`) más `public/` y `.next/static`, así la imagen que
# realmente se despliega no carga devDependencies ni el código fuente.
#
# `NEXT_PUBLIC_API_URL` se recibe como build arg porque Next.js incrusta las
# variables `NEXT_PUBLIC_*` en el bundle de cliente en tiempo de build, no
# de arranque del contenedor — hay que pasarla en `docker build --build-arg`
# (o en el `args:` del servicio en docker-compose.yml) apuntando a la URL
# pública real del backend, no a `localhost`.

FROM node:20-slim AS builder
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_TELEMETRY_DISABLED=1

RUN npm run build

FROM node:20-slim AS runner
WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

RUN useradd --create-home appuser
USER appuser

COPY --from=builder --chown=appuser:appuser /app/public ./public
COPY --from=builder --chown=appuser:appuser /app/.next/standalone ./
COPY --from=builder --chown=appuser:appuser /app/.next/static ./.next/static

EXPOSE 3000
CMD ["node", "server.js"]
