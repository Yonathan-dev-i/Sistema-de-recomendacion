# Fase 8 — Resultados avanzados y páginas de carrera

## 1. Objetivo de la fase

Llevar la experiencia de resultados al nivel final descrito en el diseño
UI/UX: gráfico radar (17 ejes) comparando el perfil del usuario contra la
carrera recomendada, gráfico de barras del Top 5, tarjetas completas,
página de detalle de carrera con su propio radar y comparación opcional, un
botón "Descargar PDF" del resultado, y un comparador de hasta 3 carreras del
Top 5 lado a lado.

## 2. Alcance realizado

Fase puramente de **frontend** (no se tocó ningún archivo bajo `backend/`):
los tres endpoints que ya existían desde fases anteriores (`POST
/test/tradicional`, `POST /test/chatbot/...`, `GET /carrera/{id}`) exponen
todos los datos que esta fase necesita (`vector_usuario`, el Top 5 completo
con `fortalezas`/`areas_por_mejorar`/`explicacion`, y `perfil_areas` de
cualquier carrera).

- **`frontend/src/components/resultados/radar-chart.tsx`** (nuevo): gráfico
  radar de 17 ejes en **SVG puro**, sin librería externa. Soporta N series
  (2 en "usuario vs. carrera recomendada", hasta 3 en el mini-radar del
  comparador). Cada vértice expone su valor exacto vía `<title>` nativo del
  navegador y un círculo de área táctil ampliada (radio 16, ≈44px de
  diámetro) para hover/tap, con un texto `aria-live="polite"` que anuncia el
  valor activo.
- **`frontend/src/components/resultados/barras-top5.tsx`** (nuevo): barras
  horizontales del Top 5 con animación de "llenado" (`whileInView` de
  Framer Motion, respeta `prefers-reduced-motion` vía la regla global ya
  definida en `globals.css` desde la Fase 5).
- **`frontend/src/components/resultados/tarjeta-carrera.tsx`** (nuevo):
  tarjeta completa por carrera — indicador circular de `afinidad_pct`,
  nombre, explicación en un `<details>` expandible (para no saturar la
  vista inicial, como sugiere la sección 5 del diseño UI/UX), chips de
  fortalezas (verde) y áreas por mejorar (ámbar), botón "Ver detalle" hacia
  `/carrera/{id}` y un botón "Comparar" opcional para el comparador.
- **`frontend/src/components/resultados/comparador-carreras.tsx`** (nuevo):
  el usuario elige 2-3 carreras del Top 5 (botón "Comparar" de cada
  tarjeta); cada carrera elegida se muestra lado a lado (afinidad,
  fortalezas, áreas por mejorar) y, cuando ya se cargó el detalle de todas
  las elegidas, un mini-radar superpuesto con una serie por carrera.
- **`frontend/src/components/resultados/pantalla-resultados.tsx`** (nuevo):
  composición central de la Fase 8 — encabezado con el resultado principal,
  radar (usuario vs. Top 1), barras del Top 5, grid de tarjetas completas,
  el comparador, y la fila de botones "Ver perfil profesional", "Comparar
  carreras" (ancla al comparador), "Descargar PDF" y "Realizar nuevamente el
  test". Al montarse, persiste el resultado actual en `localStorage` (ver
  `lib/ultimo-resultado.ts`) para que `/carrera/{id}` pueda ofrecer
  "Comparar con mi perfil".
- **`frontend/src/lib/ultimo-resultado.ts`** (nuevo): `guardarUltimoResultado`
  / `leerUltimoResultado` sobre `localStorage`, usado por la pantalla de
  resultados (fase 8) y por `/carrera/{id}` para el toggle de comparación.
- **`frontend/src/app/test/tradicional/page.tsx`**: la pantalla de
  resultados reducida de la Fase 4 (tarjetas simples, sin radar/barras/PDF)
  se reemplazó por `PantallaResultados`; el estado `resultado` ahora también
  guarda `vector_usuario` (antes solo se guardaba `test_id` y `resultados`),
  necesario para dibujar el radar.
- **`frontend/src/app/test/chatbot/page.tsx`**: cuando la conversación
  termina y hay resultado (`terminado && resultado`), la pantalla completa
  se reemplaza por `PantallaResultados` (antes se mostraba un resumen
  compacto dentro del propio chat, con solo nombre + `afinidad_pct` por
  carrera). El chat en sí (burbujas, chips, escritura) no se tocó.
- **`frontend/src/app/carrera/[id]/page.tsx`**: la lista de barras simples
  del perfil de 17 áreas se reemplazó por `RadarChart`, con un checkbox
  "Comparar con mi perfil" que solo aparece si `localStorage` tiene un
  resultado previo (`leerUltimoResultado()`); al activarlo, el radar dibuja
  dos series (el perfil de la carrera y el `vector_usuario` guardado).
- **`frontend/src/components/header.tsx`** y **`globals.css`**: se agregó
  `print:hidden` al `<header>` y una regla `@media print` de respaldo, para
  que "Descargar PDF" (ver sección 3) oculte la navegación y dimensione el
  contenido a ancho completo.

### Fuera de alcance (documentado, no silenciado)

- **Compartir resultado como enlace de solo lectura o imagen para redes
  sociales**: es una mejora sugerida explícitamente opcional en la sección 5
  del diseño UI/UX, no un criterio de aceptación de la Fase 8; no se
  implementó.
- **Pestaña "Mis resultados anteriores"**: depende de autenticación de
  usuario, que el propio prompt maestro ubica en la Fase 9.
- **Malla curricular resumida y campo laboral en `/carrera/{id}`**: el
  prompt maestro los pide "si se dispone del dato"; el dataset de carreras
  (`data/carreras.csv`, Fase 1) no incluye esa información, así que no hay
  nada que mostrar todavía sin una fuente de datos nueva (fuera del alcance
  definido para esta fase).

## 3. Decisiones técnicas relevantes

- **Gráfico radar y de barras implementados en SVG/Tailwind puro, sin
  `recharts` ni ninguna otra librería de gráficos.** El prompt maestro no
  exige una librería específica para los gráficos (a diferencia del stack
  obligatorio de la sección inicial, que no menciona ninguna). Se intentó
  evaluar `recharts` como primera opción por ser la más común en proyectos
  Next.js, pero **este entorno de ejecución no tiene acceso de red al
  registro de npm** (`registry.npmjs.org` responde `403 host_not_allowed` al
  intentar `npm install`), y no hay forma de agregar una dependencia nueva
  de forma verificable aquí. Se optó por construir ambos gráficos a mano
  (SVG puro para el radar, `div`s + Framer Motion para las barras), usando
  únicamente dependencias que el proyecto ya tenía instaladas desde fases
  anteriores. El resultado cumple el criterio de aceptación ("el radar y
  las barras reflejan datos reales del backend") sin agregar una dependencia
  que no se pudo instalar ni verificar en este entorno.
- **"Descargar PDF" implementado con la impresión nativa del navegador
  (`window.print()` + `@media print`), no con `jsPDF`/`react-pdf`.** Mismo
  motivo que el punto anterior: sin acceso al registro de npm no se puede
  agregar una librería de generación de PDF de forma verificable. La
  solución elegida es un patrón real y ampliamente usado en producción:
  el botón llama a `window.print()`, y las reglas `print:hidden` (Tailwind)
  ocultan el header, los botones de acción y el comparador, dejando solo
  `#resultado-imprimible` (encabezado, radar, barras, tarjetas del Top 5)
  visible; el usuario elige "Guardar como PDF" en el diálogo nativo de
  impresión del navegador, lo que produce un PDF real con el Top 5 y el
  detalle de la carrera recomendada, tal como exige el criterio de
  aceptación. Se documenta como decisión explícita, no como atajo
  silenciado: si en un entorno con acceso a npm se prefiere un PDF generado
  programáticamente (sin depender de que el usuario use el diálogo de
  impresión), `jsPDF` es la migración natural sin cambiar el resto de
  `PantallaResultados`.
- **El comparador de carreras vive en la misma pantalla de resultados (ancla
  `#comparador`), no en una ruta separada.** El prompt maestro lo describe
  como una vista/tabla accesible desde el botón "Comparar carreras"; en vez
  de navegar a otra página (con el costo de volver a pedir el Top 5), se
  implementó como una sección de la misma pantalla a la que el botón hace
  scroll, evitando duplicar el fetch de resultados.
- **El estado de selección del comparador (`seleccionComparador`) vive en
  `PantallaResultados`, no en `TarjetaCarrera`.** Cada tarjeta es
  "controlada" (recibe `seleccionada`/`onToggleSeleccion` desde el padre) en
  vez de manejar su propio estado, porque el comparador necesita conocer
  la selección completa de las 5 tarjetas para decidir qué mostrar.
- **`localStorage` (no una tabla nueva ni un parámetro de URL) para
  "Comparar con mi perfil" en `/carrera/{id}`.** El prompt maestro no
  especifica cómo debe llegar el `vector_usuario` del usuario a una página
  de carrera visitada de forma independiente (ej. desde el catálogo de la
  landing, no desde el botón "Ver detalle" de un resultado). Se decidió
  guardar el último resultado calculado (cualquiera de los dos métodos) en
  `localStorage` al mostrarse `PantallaResultados`, y leerlo en
  `/carrera/{id}` solo para *ofrecer* el checkbox (si no hay nada guardado,
  el checkbox ni aparece). Es el mismo criterio de "invitado sin cuenta"
  que ya usaron las Fases 4-6 antes de que exista autenticación (Fase 9);
  cuando esa fase agregue sesión de usuario, la migración natural es leer
  el último `IntentoTest` del usuario autenticado en vez de `localStorage`.
- **El indicador de afinidad usa un círculo de progreso SVG hecho a mano**
  (`stroke-dasharray` sobre un círculo, en `TarjetaCarrera`), en vez de un
  componente de terceros, por la misma razón de falta de acceso a npm; es
  una técnica CSS/SVG estándar y no requiere ninguna dependencia.
- **No se cambió ningún contrato de API.** Todos los datos que esta fase
  necesita (`vector_usuario`, `perfil_areas` de cualquier carrera) ya
  estaban expuestos por endpoints de fases anteriores; `PantallaResultados`
  simplemente encadena `obtenerAreas()` + `obtenerCarreraDetalle(top1_id)`
  (ya existentes desde la Fase 5) además de los datos que ya traía la
  respuesta del test.

## 4. Cómo se verificaron los criterios de aceptación

| Criterio | Método de verificación | Resultado |
|---|---|---|
| El radar y las barras reflejan datos reales del backend, no valores de ejemplo | Inspección de código: `RadarChart` en `PantallaResultados` recibe `vectorUsuario` (viene de `TestTradicionalOut`/`ChatbotResultado`, calculado por `construir_vector_usuario` en el backend) y `top1Detalle.perfil_areas` (viene de `GET /carrera/{id}` real); `BarrasTop5` recibe `resultados` tal cual los devuelve `POST /test/tradicional` / `.../chatbot`, sin ningún dato hardcodeado en los componentes nuevos | ✅ (verificado por inspección de código; ver sección 6 sobre por qué no se pudo levantar el stack completo en este entorno) |
| El PDF descargado contiene el Top 5 y el detalle de la carrera recomendada | Inspección de código y de estilos: `#resultado-imprimible` incluye el encabezado (carrera #1 + afinidad), el radar usuario-vs-carrera, las barras del Top 5 completo y las 5 tarjetas completas; las reglas `print:hidden` ocultan únicamente el header global y la fila de botones/comparador, dejando el resto visible al imprimir/exportar | ✅ (verificado por inspección de CSS/JSX; no se pudo generar y abrir un PDF real en este entorno por no tener un navegador disponible, ver sección 6) |
| El comparador permite seleccionar y visualizar al menos 2 carreras simultáneamente | Inspección de código: `ComparadorCarreras` renderiza un mensaje de "selecciona al menos 2" mientras `seleccionadas.length < 2`, y a partir de 2 muestra la grilla lado a lado + el mini-radar superpuesto; `toggleComparador` en `PantallaResultados` limita la selección a un máximo de 3 | ✅ (verificado por inspección de código; ver sección 6) |

## 5. Pruebas realizadas

- **No se pudieron ejecutar pruebas automatizadas ni manuales de frontend en
  este entorno** (ver sección 6 para el detalle): no hay `node_modules`
  instalado y el entorno de ejecución de esta fase no tiene acceso de red
  al registro de npm, por lo que ni `npm install`, ni `npx tsc --noEmit`, ni
  `npx eslint src/`, ni `npx next build` pudieron correr aquí (a diferencia
  de las Fases 0, 4, 5 y 6, que sí pudieron ejecutar estos comandos con las
  dependencias ya instaladas en esos entornos de sesión).
- **Verificación manual realizada — revisión exhaustiva de código en su
  lugar:** se releyó cada componente nuevo verificando tipos contra
  `frontend/src/lib/api.ts` (`ResultadoCarrera`, `CarreraDetalle`,
  `Area`), consistencia de props entre `PantallaResultados` y sus hijos
  (`RadarChart`, `BarrasTop5`, `TarjetaCarrera`, `ComparadorCarreras`), y que
  ningún import quedara sin usar tras reemplazar las pantallas de
  resultados de las Fases 4 y 6 (se eliminaron las funciones
  `PantallaResultados` reducida de `test/tradicional/page.tsx` y
  `ResumenResultado`/`reiniciar` de `test/chatbot/page.tsx`, que quedaron
  huérfanas).
- **No se agregó ninguna dependencia nueva a `package.json`** (ver sección
  3), por lo que no hay un cambio de `package-lock.json` que pudiera romper
  una instalación futura en un entorno con red disponible.

## 6. Problemas encontrados y solución

- **Sin acceso de red al registro de npm en este entorno de ejecución.**
  A diferencia de las Fases 0 y 5 (que sí pudieron instalar dependencias vía
  npm), un intento de `npm install`/`npm ping` en esta sesión devuelve
  `403 host_not_allowed` contra `registry.npmjs.org`. Esto impidió: (a)
  agregar `recharts` (o cualquier librería de gráficos) para el radar/barras,
  resuelto construyendo ambos en SVG/Tailwind puro (ver sección 3); (b)
  agregar `jsPDF` para el botón "Descargar PDF", resuelto con
  `window.print()` + CSS de impresión (ver sección 3); (c) ejecutar
  `npm install` para tener `node_modules` y correr `tsc`/`eslint`/`next
  build` sobre el código nuevo, lo que dejó la verificación de esta fase
  limitada a una revisión manual de código (ver sección 5), no silenciada.
- **Sin `node_modules` ni build disponible, no se pudo confirmar visualmente
  el radar, las barras ni el comparador en un navegador real.** Mismo
  motivo que el punto anterior. Queda pendiente, no silenciado: una
  verificación con `npm install && npx next build && npx playwright ...`
  (o el flujo manual ya usado en la Fase 5) la primera vez que el proyecto
  se ejecute en un entorno con acceso normal a internet.
- Ningún otro bloqueo relacionado con la lógica de negocio: los datos que
  esta fase consume (`vector_usuario`, `perfil_areas`, Top 5) ya estaban
  completamente resueltos y probados en las Fases 2-6.

## 7. Estado final de la fase

**PARCIAL, con salvedades documentadas y no silenciadas.** Los tres
criterios de aceptación de la Fase 8 se implementaron y se verificaron por
inspección exhaustiva de código (tipos, props, y que los datos mostrados
provienen siempre de la respuesta real del backend, nunca de valores de
ejemplo), pero **no pudieron verificarse en un navegador real ni con
`tsc`/`eslint`/`next build`**, porque este entorno de ejecución no tiene
`node_modules` instalado y no tiene acceso de red al registro de npm para
instalarlo. Este es el mismo tipo de salvedad que ya dejaron documentadas
las Fases 4, 5 y 6 respecto a PostgreSQL (código correcto por inspección y
por reutilizar exactamente los mismos tipos/contratos ya probados, pero sin
una ejecución end-to-end real en esta sesión). Se recomienda, como primer
paso al retomar el proyecto en un entorno con red disponible: `npm install`
+ `npx tsc --noEmit` + `npx eslint src/` + `npx next build`, y una pasada
manual (o con Playwright) por `/test/tradicional`, `/test/chatbot` y
`/carrera/{id}` para confirmar visualmente el radar, las barras, el
comparador y la exportación a PDF antes de considerar la fase
completamente cerrada.

## 8. Siguientes pasos

- `lib/ultimo-resultado.ts` (persistencia en `localStorage` del último
  resultado) queda como el puente natural para que la Fase 9 lo reemplace
  por una lectura real de `IntentoTest` del usuario autenticado en la
  pantalla "Mis resultados anteriores", sin cambiar el contrato de
  `PantallaResultados` ni de `/carrera/{id}`.
- Si al retomar el proyecto hay acceso a npm, migrar el radar/barras a una
  librería como `recharts` (o mantener la versión SVG propia, que ya
  funciona sin dependencias) y el botón "Descargar PDF" a `jsPDF` son
  cambios acotados a `components/resultados/`, sin tocar el resto del
  frontend ni ningún endpoint del backend.
- El test de equivalencia automatizado formulario/chatbot (10+ secuencias)
  que exige la Fase 9 no se ve afectado por esta fase: ninguno de los
  cambios tocó `test_service.py` ni `chatbot_service.py`.
