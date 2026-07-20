# Fase 9f — Performance y despliegue

## 1. Objetivo de la fase

Optimizar lo ya construido (Fases 0–9e) y dejar el sistema desplegado o
listo para desplegar, como cierre final del proyecto: lazy loading de
gráficos pesados, memoización donde aplique, revisión responsive en un
dispositivo móvil real, y configuración/verificación de despliegue
(backend + frontend + base de datos) en un entorno accesible para revisión.

## 2. Alcance realizado

### 2.1 Performance del frontend

- **`frontend/src/components/resultados/pantalla-resultados.tsx`**: los
  tres componentes más pesados de la pantalla de resultados —
  `RadarChart`, `BarrasTop5` y `ComparadorCarreras` (que puede montar un
  segundo radar) — se cambiaron de import estático a `next/dynamic` con
  `ssr: false` y un `Skeleton` del tamaño real como `loading`. Su JS ahora
  va en chunks aparte que no bloquean el render inicial del encabezado y
  las tarjetas.
- **`frontend/src/components/resultados/radar-chart.tsx`**: la geometría
  del radar (ángulos, anillos, puntos por serie) se recalculaba en cada
  render, incluido cada `onMouseEnter`/`onMouseLeave` de un vértice. Se
  extrajo a un único `useMemo` (dependiente de `areas`, `series`, `size`,
  `maxValue`), y el componente se exporta envuelto en `memo`.
- **`frontend/src/components/resultados/tarjeta-carrera.tsx`** y
  **`barras-top5.tsx`**: envueltos en `memo`. Sin esto, alternar una
  selección en el comparador (estado del padre `PantallaResultados`)
  volvía a renderizar las 5 tarjetas y el gráfico de barras aunque sus
  props no cambiaran.
- **`frontend/src/app/historial/page.tsx`**: `TarjetaIntento` (una por
  cada intento en la línea de tiempo) se envolvió en `memo`, para que un
  reintento tras error no re-monte toda la lista.
- **`frontend/next.config.mjs`**:
  - `output: "standalone"` — necesario para el `Dockerfile` del frontend
    (ver 2.2): genera un servidor Node autocontenido con solo las
    dependencias de runtime realmente usadas, en vez de la imagen completa
    con todo `node_modules`.
  - `experimental.optimizePackageImports: ["lucide-react"]` — evita que
    Next incluya el barrel completo de íconos cuando cada archivo importa
    solo unos pocos.
  - `poweredByHeader: false` y `compress: true`.

No se tocó `careers-explorer.tsx` (grilla de las 37 carreras): ya usa
`viewport: { once: true }` de Framer Motion para animar solo una vez al
entrar en pantalla, y no monta gráficos pesados, así que no había ganancia
clara de aplicar lazy loading ahí sin agregar complejidad innecesaria.

### 2.2 Despliegue

No existía ninguna configuración de despliegue previa a esta fase (sin
Dockerfiles, sin `docker-compose.yml`). Se agregó:

- **`backend/Dockerfile`**: imagen `python:3.11-slim`, instala
  `requirements.txt`, corre como usuario no-root, expone `8000`.
- **`backend/entrypoint.sh`**: corre `alembic upgrade head` antes de
  levantar `uvicorn`, para que un despliegue nuevo (o `docker compose up`
  desde una base de datos vacía) quede con el esquema al día sin un paso
  manual aparte.
- **`backend/.dockerignore`**.
- **`frontend/Dockerfile`**: build multi-stage sobre `node:20-slim`. La
  etapa `builder` instala todas las dependencias y corre `next build`; la
  etapa `runner` copia solo la salida de `output: "standalone"` (más
  `public/` y `.next/static`), como usuario no-root, expone `3000`.
  Recibe `NEXT_PUBLIC_API_URL` como build arg (las variables
  `NEXT_PUBLIC_*` de Next.js se incrustan en el bundle de cliente en
  tiempo de build, no de arranque del contenedor).
- **`frontend/.dockerignore`**.
- **`docker-compose.yml`** (raíz del proyecto): orquesta `db` (Postgres
  16), `backend` y `frontend`. `backend` espera a que `db` pase su
  `healthcheck` (`pg_isready`); `frontend` espera a que `backend` pase el
  suyo (`GET /health`, reutilizando el endpoint ya existente desde la
  Fase 0). Variables sensibles (`POSTGRES_PASSWORD`, `JWT_SECRET_KEY`) se
  leen de `.env` y el compose falla explícitamente (`:?mensaje`) si no
  están definidas, en vez de arrancar con un secreto vacío.
- **`.env.example`** (raíz): plantilla de las variables que necesita
  `docker compose up`.

## 3. Decisiones técnicas relevantes

- **Docker + `docker-compose.yml` como mecanismo de despliegue**, en vez
  de atarse a un proveedor específico (Render, Railway, Fly.io, un VPS
  propio). El prompt maestro no especifica un hosting obligatorio, y una
  imagen Docker estándar corre igual en cualquiera de esos proveedores
  (todos aceptan un `Dockerfile` o un `docker-compose.yml` como entrada) o
  en un servidor propio. Esto evita acoplar el cierre del proyecto a la
  disponibilidad de una cuenta gratuita de un proveedor externo — ver
  sección 6 sobre las limitaciones de red de este entorno de desarrollo.
- **Migraciones en el `entrypoint.sh` del backend, no en el `Dockerfile`**:
  correrlas en tiempo de build fallaría porque la base de datos no existe
  todavía durante `docker build`; correrlas en el arranque del contenedor
  (antes de `exec uvicorn`) es el patrón estándar para que cualquier
  despliegue nuevo quede con el esquema listo automáticamente.
- **`next/dynamic` con `ssr: false` en vez de `React.lazy` +
  `<Suspense>`**: en el App Router de Next.js, `next/dynamic` es la forma
  soportada oficialmente de hacer code-splitting con un `loading` propio
  por componente, y permite desactivar SSR específicamente para los
  gráficos (que dependen de interacción de mouse/tap del cliente) sin
  desactivarlo para el resto de la pantalla.
- **`memo` selectivo, no memoización global**: solo se envolvieron los
  componentes que (a) se repiten varias veces en la misma pantalla
  (tarjetas, radar puntos) o (b) hacen cálculo trigonométrico no trivial
  (radar). No se aplicó `memo`/`useMemo` de forma indiscriminada a
  componentes simples de una sola instancia, donde el costo de comparar
  props supera cualquier ahorro de render.

## 4. Cómo se verificaron los criterios de aceptación

| Criterio (prompt maestro) | Método de verificación | Resultado |
|---|---|---|
| El sistema está desplegado (o listo para desplegar) en un entorno accesible para revisión, con instrucciones claras de cómo acceder. | Se construyó la configuración completa de despliegue (`Dockerfile` de backend y frontend, `docker-compose.yml`, `.env.example`) y se documentaron los pasos de arranque en la sección 6 de este documento y en el `README.md` raíz. **No se ejecutó un `docker compose up` real** porque este entorno de desarrollo no tiene un daemon de Docker disponible (ver sección 6, limitación explícita). | **PARCIAL** — listo para desplegar, verificado por revisión de código y por los builds nativos equivalentes (ver filas siguientes), no por un contenedor corriendo de punta a punta. |
| Las pantallas con gráficos o listas largas (resultados, comparador, historial) cargan de forma perceptible como rápida, sin bloqueos visibles de UI. | `npm run build` de producción corrido en este entorno: compiló sin errores, generó el `output: "standalone"` y los chunks separados de `RadarChart`/`BarrasTop5`/`ComparadorCarreras` ya no están en el bundle inicial de la ruta de resultados. `npx tsc --noEmit` sin errores tras memoizar los componentes. | **Cumplido** (verificado por build; la percepción real de velocidad requiere probarse en el navegador, recomendado como parte de la revisión manual del equipo). |
| El sistema se probó manualmente en al menos un dispositivo móvil real, confirmando que el formulario y el chatbot son usables con el pulgar. | **No se pudo ejecutar en este entorno**: es un entorno de desarrollo sin acceso a un dispositivo físico ni a un navegador con el que interactuar a mano. Se dejó documentado en la sección 6 un checklist de verificación manual concreto para que el equipo lo ejecute en un teléfono real antes de dar la fase por cerrada. | **PENDIENTE** — requiere ejecución humana, no automatizable desde este entorno. |

## 5. Pruebas realizadas

- **`cd backend && python -m pytest app/tests -q`**: 109 tests pasan
  (ninguno se modificó ni se agregó en esta fase — no hubo cambios de
  lógica de negocio en el backend, solo Dockerfile/entrypoint).
- **`cd frontend && npx tsc --noEmit`**: sin errores de tipos tras
  memoizar/lazy-loadear los componentes de resultados e historial.
- **`cd frontend && npm run build`**: build de producción exitoso;
  confirma que `output: "standalone"` genera `.next/standalone/server.js`
  (usado por `frontend/Dockerfile`) y que el code-splitting de los
  gráficos pesados efectivamente separó esos chunks del bundle inicial.
- No se agregaron tests automatizados nuevos en esta fase: el alcance es
  performance (verificable por build/bundle) y despliegue (verificable
  por revisión de configuración), no lógica de negocio con casos de
  prueba propios.

## 6. Problemas encontrados y solución

- **Sin daemon de Docker disponible en este entorno de desarrollo**: no
  fue posible correr `docker build`/`docker compose up` para verificar
  las imágenes de punta a punta dentro de esta sesión. Se mitigó
  verificando cada mitad del proceso con las herramientas nativas
  disponibles (`pip install -r requirements.txt` + `pytest` para el
  backend, `npm run build` para el frontend con exactamente los mismos
  comandos que corren dentro de cada `Dockerfile`), pero **queda
  pendiente que el equipo corra `docker compose up -d --build` una vez
  en un entorno con Docker** antes de considerar el despliegue
  verificado de punta a punta. Instrucciones exactas:

  ```bash
  cp .env.example .env
  # completar POSTGRES_PASSWORD, JWT_SECRET_KEY, CORS_ORIGINS y
  # NEXT_PUBLIC_API_URL con los valores reales del entorno de destino
  docker compose up -d --build
  # backend:  http://<host>:8000/health  (debe responder {"status":"ok",...})
  # frontend: http://<host>:3000
  ```

- **Sin dispositivo móvil real ni navegador interactivo en este entorno**:
  el criterio de aceptación pide explícitamente probar "en al menos un
  dispositivo móvil real (no solo el modo responsive del navegador de
  escritorio)", algo que este entorno de desarrollo no puede ejecutar por
  sí mismo. Queda como checklist pendiente para el equipo, a ejecutar en
  un teléfono real antes de dar la Fase 9f (y el proyecto) por cerrada:

  1. Abrir la Landing en un teléfono real (no el modo responsive de
     Chrome DevTools) y confirmar que el hero, las tarjetas de método y
     el explorador de 37 carreras se ven sin scroll horizontal.
  2. Completar el Test Tradicional de principio a fin con el pulgar:
     confirmar que los 5 botones tipo *card* del Likert son cómodos de
     tocar sin errores de precisión, y que "Anterior"/"Siguiente" no
     quedan tapados por el teclado virtual al escribir (si aplica) ni por
     la barra de gestos del sistema operativo.
  3. Completar el Test por Chatbot con el pulgar: confirmar que los chips
     numerados 1–5 son cómodos de tocar y que el teclado virtual no tapa
     el input al escribir una respuesta libre.
  4. Ver una pantalla de Resultados completa: confirmar que el radar y el
     gráfico de barras se leen sin necesidad de hacer zoom, y que el
     scroll de la página es fluido con los gráficos ya cargados
     (lazy-loaded en esta fase).
  5. Anotar el modelo de teléfono y navegador usados en la verificación,
     y agregar esa nota como actualización a este mismo documento
     (sección 7) una vez completado.

  Este documento **no** marca este punto como resuelto porque hacerlo sin
  la prueba real sería falsear el criterio de aceptación tal como está
  redactado en el prompt maestro.

## 7. Estado final de la fase

**PARCIAL.** Se cumplió el criterio de performance (lazy loading +
memoización, verificado por build) y se dejó completamente lista la
configuración de despliegue (Dockerfiles, `docker-compose.yml`,
healthchecks, migraciones automáticas, variables de entorno
documentadas). Quedan dos pasos explícitamente pendientes, ambos
imposibles de ejecutar desde este entorno de desarrollo y ambos
documentados arriba con instrucciones exactas para que el equipo los
cierre:

1. Correr `docker compose up -d --build` una vez en un entorno con Docker
   disponible, para confirmar el despliegue de punta a punta (no solo por
   partes, como se verificó acá).
2. Ejecutar el checklist de la sección 6 en un dispositivo móvil real y
   registrar el resultado.

Ninguno de los dos pendientes requiere cambios de código adicionales: el
sistema ya está preparado para ambos, solo falta la ejecución manual.

## 8. Siguientes pasos

Con esta fase, las 15 fases del prompt maestro (0 a 9f) quedan
documentadas. Se genera `docs/fases/README.md` como índice general de
todo el proceso de construcción, enlazando en orden los 15
`fase-N-*.md`, para que cualquier persona (docente, jurado, nuevo
integrante del equipo) pueda leer la historia completa del sistema de
principio a fin. Antes de una sustentación o entrega final, el equipo
debe completar los dos pendientes de la sección 7 y actualizar este
archivo con el resultado.
