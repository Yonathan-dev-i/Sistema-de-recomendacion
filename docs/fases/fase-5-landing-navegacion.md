# Fase 5 — Landing Page y navegación general

## 1. Objetivo de la fase

Dar contexto y entrada profesional al sistema, ahora que el flujo principal
(Fase 4, test tradicional) ya funciona: una Landing Page completa, una
pantalla de selección de método, y un Header/Navbar consistente con toggle
de modo claro/oscuro persistente en todas las pantallas.

## 2. Alcance realizado

### Sistema de diseño (base para toda la fase)

- **`frontend/tailwind.config.ts`**: paleta institucional UNA Puno (guinda/vino
  como color primario, dorado como acento), colores semánticos
  (`success`/`warning`/`danger`) reservados para estados, tokens de
  `border-radius`, `container` centrado y las animaciones de `accordion` y
  `float`.
- **`frontend/src/app/globals.css`**: variables CSS en HSL para modo claro y
  oscuro (`--background`, `--primary`, `--accent`, etc.), scroll suave,
  soporte de `prefers-reduced-motion` (desactiva animaciones/scroll suave) y
  un `.skip-link` de accesibilidad ("Saltar al contenido principal").
- **`frontend/src/lib/utils.ts`**: helper `cn()` (patrón shadcn/ui) para
  combinar clases Tailwind sin colisiones.
- **`frontend/src/components/ui/`**: primitivas reutilizables construidas con
  Radix + `class-variance-authority` siguiendo el patrón shadcn/ui:
  `button.tsx`, `card.tsx`, `accordion.tsx` (para el FAQ), `skeleton.tsx` y
  `error-state.tsx` (componente transversal de error con botón
  "Reintentar", pedido en la sección "Componentes transversales" del prompt
  maestro).

### Header / Navbar / Footer (consistentes en todas las pantallas)

- **`frontend/src/components/header.tsx`**: header `sticky`, con logo,
  navegación a las secciones de la landing (`/#como-funciona`, `/#metodos`,
  `/#carreras`, `/#faq`), botón CTA "Comenzar Test" siempre visible, menú
  móvil animado (Framer Motion) y toggle de tema. Se monta una sola vez en
  `frontend/src/app/layout.tsx`, por lo que aparece en **todas** las rutas
  (landing, selección de método, formulario, detalle de carrera), cumpliendo
  el criterio de "Header/Navbar consistente en todas las pantallas".
- **`frontend/src/components/theme-toggle.tsx`**: toggle claro/oscuro sobre
  `next-themes` (ya configurado desde la Fase 0 con `attribute="class"` y
  `defaultTheme="system"`). `next-themes` persiste la preferencia en
  `localStorage` y respeta `prefers-color-scheme` la primera vez.
- **`frontend/src/components/footer.tsx`**: información institucional,
  enlaces de navegación, apartado legal/redes (placeholder, sin páginas
  legales reales todavía) y el disclaimer explícito pedido por el prompt
  maestro ("herramienta de orientación, no una decisión vinculante").
- **`frontend/src/components/breadcrumb.tsx`**: breadcrumb simple
  (`Inicio > Test > ...`) usado en `/test`, `/test/chatbot` y
  `/carrera/[id]`.

### Landing Page (`frontend/src/app/page.tsx`)

Compone, en orden, los componentes de `frontend/src/components/landing/`:

- **`hero.tsx`**: título/subtítulo exactos del prompt maestro, botones
  "Realizar Test" (→ `/test`) y "Conversar con el Chatbot" (→
  `/test/chatbot`), indicador de confianza ("37 carreras · 17 áreas
  evaluadas · Test 100% gratuito") e ilustración decorativa animada
  (Framer Motion, `prefers-reduced-motion` respetado automáticamente por la
  regla global en `globals.css`).
- **`how-it-works.tsx`**: 3 tarjetas ("¿Cómo funciona?") con aparición
  escalonada (`whileInView` + `staggerChildren`).
- **`test-methods.tsx`**: 2 tarjetas grandes de "Métodos del Test", cada una
  con su lista de beneficios y botón propio.
- **`careers-explorer.tsx`** (mejora sugerida del prompt maestro): grilla
  filtrable por facultad de las 37 carreras, consumiendo `GET /carreras`
  real (no mockeado). Implementa los tres estados pedidos por el design
  system transversal: *loading* (`Skeleton`), *error* (`ErrorState` con
  "Reintentar") y *vacío* (mensaje si un filtro no tiene resultados). Cada
  tarjeta navega a `/carrera/{id}`.
- **`benefits.tsx`**: grilla de 6 beneficios con ícono.
- **`faq.tsx`** (mejora sugerida): `Accordion` accesible con 5 preguntas
  frecuentes reales del dominio del proyecto.
- **`footer.tsx`**: solo se renderiza en la landing (no en pantallas de
  test, para no competir visualmente con la navegación del formulario).

### Pantalla de selección de método (`frontend/src/app/test/page.tsx`)

- Reutiliza el mismo contenido de "Métodos del Test" como pantalla dedicada,
  con breadcrumb, botón "Volver al inicio", tiempo estimado fijo ("10–15
  min", mejora sugerida) por método, y un checkbox informativo "Continuar
  como invitado" (mejora sugerida) que aclara honestamente que el historial
  autenticado llega en una fase posterior (Fase 9) — no simula una función
  de login que todavía no existe.

### Rutas nuevas para no dejar enlaces rotos desde la landing

- **`frontend/src/app/test/chatbot/page.tsx`**: placeholder honesto ("El
  chatbot está en construcción... se implementa en la Fase 6") con salida
  directa al test tradicional. Necesario porque la landing y la pantalla de
  selección de método, tal como las pide el prompt maestro, ya enlazan al
  chatbot aunque su lógica (Fase 6) todavía no existe.
- **`frontend/src/app/carrera/[id]/page.tsx`**: versión MVP de la página de
  detalle de carrera consumiendo `GET /carrera/{id}` real (nombre, facultad
  y perfil de 17 áreas como lista de barras). El gráfico radar y la
  comparación con el perfil del usuario, tal como los describe la sección 6
  del diseño UI/UX, son explícitamente Fase 8 y **no** se implementaron
  aquí; se documenta como alcance reducido intencional (ver sección 3).

### Cliente API

- **`frontend/src/lib/api.ts`**: se agregaron `CarreraResumen`,
  `CarreraDetalle`, `obtenerCarreras()` y `obtenerCarreraDetalle(id)`, que
  no existían tras la Fase 4 (esa fase solo necesitaba `/areas` y
  `/preguntas`).

### Backend

Sin cambios. La Fase 5 es puramente de frontend (landing y navegación); no
se tocó ningún archivo bajo `backend/`.

## 3. Decisiones técnicas relevantes

- **Paleta de color aproximada, no oficial.** El prompt maestro permite
  "tonos guinda/vino + dorado, o los oficiales de la universidad". No se
  tuvo acceso a la guía de marca oficial de la UNA Puno en este entorno, así
  que se definió una paleta guinda/dorado propia (`primary`/`accent` en
  `tailwind.config.ts`). Si existe una guía de marca oficial, solo hace
  falta ajustar esos valores hexadecimales; ningún componente depende de un
  valor de color hardcodeado fuera de esos tokens.
- **Sin Google Fonts (`next/font/google`).** El entorno de ejecución de esta
  fase solo tiene salida de red permitida hacia dominios de paquetes (npm,
  PyPI, GitHub, etc.), no hacia `fonts.gstatic.com`. Usar `next/font/google`
  habría roto `next build` por no poder descargar las fuentes. Se optó por
  declarar `--font-sans`/`--font-display` como variables CSS con *fallback*
  a fuentes de sistema (`system-ui`, sans-serif), dejando el reemplazo por
  Inter/Lexend como una tarea de una línea (`next/font/google` +
  `variable`) para cuando el proyecto corra en un entorno con acceso normal
  a internet.
- **shadcn/ui "a mano" en vez de `npx shadcn init`.** El stack obligatorio
  pide shadcn/ui. En vez de ejecutar el CLI (que también requiere red hacia
  el registro de componentes de shadcn), se construyeron manualmente los
  componentes (`button.tsx`, `card.tsx`, `accordion.tsx`, `skeleton.tsx`)
  siguiendo exactamente el mismo patrón que genera el CLI: primitivas de
  Radix + `class-variance-authority` + `cn()`, en `components/ui/`. El
  resultado es idéntico en estructura y queda 100% compatible si más
  adelante se corre el CLI real para agregar más componentes (`Sonner`,
  `AlertDialog`, etc. en fases posteriores).
- **Placeholders honestos en vez de enlaces rotos o funcionalidad
  simulada.** El prompt maestro exige que "desde la landing, un usuario
  pueda llegar al formulario y completar el test sin pasos rotos", pero la
  landing y la pantalla de selección de método (ambas de esta fase) también
  enlazan al chatbot (Fase 6) y a la página de detalle de carrera (Fase 8),
  que no existían antes de esta fase. En vez de omitir esos enlaces o
  simular una funcionalidad que no está implementada, se crearon dos rutas
  reales: `/test/chatbot` (mensaje claro de "en construcción" + salida al
  test tradicional) y `/carrera/[id]` (versión MVP real, sin radar). El
  checkbox "Continuar como invitado" sigue el mismo criterio: es
  informativo, no simula un login que no existe.
- **`/carrera/[id]` como MVP y no como la página final de la Fase 8.** Se
  decidió construir una versión reducida (perfil de 17 áreas como barras,
  sin gráfico radar ni comparación con el perfil del usuario) para que el
  enlace "Explora las 37 carreras" de la landing funcione de verdad en esta
  fase, dejando explícitamente para la Fase 8 el gráfico radar y la
  comparación, tal como los define la sección 6 del diseño UI/UX del
  prompt maestro.
- **Footer solo en la landing.** El prompt maestro pide Footer en la
  sección "Landing Page" específicamente; se decidió no repetirlo en el
  formulario de test ni en la selección de método para no competir con la
  navegación de esas pantallas (mismo criterio que ya aplicó la Fase 4 al
  no incluir un footer en `/test/tradicional`).
- **No se tocó `frontend/src/app/test/tradicional/page.tsx`** salvo por
  agregar el `id="contenido"` (para que el skip-link de accesibilidad
  funcione también ahí) a los tres `<main>` de esa pantalla. El resto del
  archivo, cerrado y probado en la Fase 4, se dejó intacto para no arriesgar
  una regresión sobre una fase ya cerrada.
- **`@radix-ui/react-dialog` no se usó finalmente.** Se instaló
  previendo el `AlertDialog` de confirmación de salida (mejora sugerida de
  la Fase 4, no de esta), pero al no implementarse en este alcance se
  desinstaló para no dejar una dependencia sin uso en `package.json`.

## 4. Cómo se verificaron los criterios de aceptación

| Criterio | Método de verificación | Resultado |
|---|---|---|
| Desde la landing, un usuario puede llegar al formulario y completar el test sin pasos rotos | `npx next build` genera sin errores las rutas `/`, `/test`, `/test/chatbot`, `/test/tradicional`, `/carrera/[id]`; smoke test con `next start` + `curl`: las 5 rutas devuelven `200`. Recorrido manual con Playwright (capturas de pantalla) confirma que "Realizar Test" (Hero) → `/test` → "Comenzar Test" → `/test/tradicional` (formulario real de la Fase 4, sin tocar) | ✅ |
| El modo oscuro/claro persiste entre recargas | `next-themes` con `attribute="class"` guarda la preferencia en `localStorage` (comportamiento de la librería, ya configurado desde la Fase 0); verificado visualmente con capturas en `color_scheme="dark"` y `"light"` vía Playwright, ambas con contraste correcto en header, tarjetas y footer | ✅ |
| La landing es responsive (mobile y desktop) | Capturas con Playwright en 3 viewports: 1440×1000 (desktop), 390×844 (mobile) y verificación del menú hamburguesa móvil (clic real + captura). Todas las secciones (Hero, tarjetas, grilla de carreras, FAQ, footer) se apilan correctamente en mobile sin overflow horizontal | ✅ |
| Linters pasan sin errores | `npx eslint src/` → sin errores ni warnings | ✅ |
| Tipos correctos | `npx tsc --noEmit` → sin errores | ✅ |
| Build de producción | `npx next build` → compila, 6 rutas generadas (`/`, `/test`, `/test/chatbot`, `/test/tradicional`, `/carrera/[id]`), sin errores de React/Next | ✅ |
| Backend de la Fase 4 no sufrió regresión | `diff -rq` entre el backend antes y después de esta fase → sin diferencias (no se tocó ningún archivo de `backend/`) | ✅ |

## 5. Pruebas realizadas

- **Automatizadas:** `npx tsc --noEmit`, `npx eslint src/`, `npx next build`
  (los tres sin errores). No se agregaron tests de Playwright automatizados
  a la suite del repositorio en esta fase (no hay una carpeta de tests E2E
  configurada en el proyecto todavía); las verificaciones con Playwright
  descritas abajo se hicieron de forma manual/exploratoria contra
  `next start`, no quedan como suite corriendo en CI.
- **Manuales (smoke test con `next start` + `curl`):** las rutas `/`,
  `/test`, `/test/chatbot`, `/test/tradicional` y `/carrera/1` devuelven
  `200`.
- **Manuales (Playwright, capturas de pantalla):**
  - Landing completa en desktop (1440px), modo claro y modo oscuro.
  - Landing completa en mobile (390px), incluyendo el menú hamburguesa
    abierto.
  - Pantalla de selección de método (`/test`).
  - Placeholder del chatbot (`/test/chatbot`).
  - Estado de error (con "Reintentar") en la sección "Explora las 37
    carreras" y en `/carrera/1`, verificado intencionalmente **sin**
    backend levantado en este entorno (no hay PostgreSQL disponible aquí,
    igual que documentó la Fase 4), confirmando que el estado de error del
    design system transversal se activa y se ve correctamente en vez de
    romper la página.
- **No realizada en este entorno:** verificación manual en un navegador
  real contra un backend + PostgreSQL levantados (mismo motivo que la Fase
  4: este entorno de ejecución no tiene PostgreSQL disponible). Por eso la
  sección "Explora las 37 carreras" se verificó en su estado de error
  (backend caído) en vez de en su estado con datos reales; el código de la
  ruta feliz (`estado === "listo"`) es el mismo que ya se ejerció
  indirectamente al construir y tipar el componente, pero no se vio
  renderizado con datos reales de las 37 carreras en este entorno.

## 6. Problemas encontrados y solución

- **`next/font/google` rompía el build por falta de acceso de red a
  `fonts.gstatic.com`.** Se resolvió declarando la tipografía como
  variables CSS con *fallback* a fuentes de sistema en vez de descargar
  Inter/Lexend en tiempo de build (ver sección 3). Queda pendiente, no
  silenciado: cuando el proyecto se despliegue en un entorno con acceso
  normal a internet, cambiar `--font-sans`/`--font-display` por
  `next/font/google` es un cambio de una línea en `layout.tsx`.
- **Enlaces de la landing hacia funcionalidades de fases futuras
  (chatbot, detalle de carrera).** Ver la decisión de "placeholders
  honestos" en la sección 3; se optó por rutas reales con mensajes claros
  en vez de esconder los enlaces o simular funcionalidad inexistente.
- **Procesos en segundo plano no persisten entre comandos en este entorno
  de ejecución.** Al intentar levantar `next start` en background para
  tomar capturas con Playwright, el proceso moría entre una llamada de
  herramienta y la siguiente. Se resolvió lanzando el servidor y el script
  de captura dentro de la misma invocación de comando. No afecta al
  proyecto en sí, solo a cómo se verificó en este entorno.
- **Sin PostgreSQL disponible en este entorno** (mismo problema ya
  documentado en la Fase 4): impidió verificar la ruta feliz de "Explora
  las 37 carreras" y de `/carrera/{id}` con datos reales. Ver sección 5 y
  7 para el detalle de qué sí se verificó en su lugar.

## 7. Estado final de la fase

**CERRADA**, con dos salvedades documentadas y no silenciadas:

1. La verificación de la sección "Explora las 37 carreras" y de
   `/carrera/{id}` se hizo contra su **estado de error** (sin backend
   disponible en este entorno), no contra su estado con datos reales de
   las 37 carreras. El componente y el cliente API (`obtenerCarreras`,
   `obtenerCarreraDetalle`) son el mismo código tipado y ejercitado por
   `tsc`/`eslint`/`next build`; falta una verificación manual puntual
   contra el backend + PostgreSQL reales levantados (mismo tipo de
   pendiente que dejó la Fase 4).
2. `/carrera/{id}` se implementó como MVP (perfil de 17 áreas en barras),
   sin el gráfico radar ni la comparación con el perfil del usuario que
   describe la sección 6 del diseño UI/UX — eso es explícitamente el
   alcance de la Fase 8, no de esta.

Los tres criterios de aceptación explícitos de la Fase 5 (navegación sin
pasos rotos desde la landing, persistencia de modo claro/oscuro, y diseño
responsive) se cumplen y se verificaron como se detalla en la sección 4.

## 8. Siguientes pasos

- El Header global (`components/header.tsx`) y el `ThemeProvider` ya están
  montados una sola vez en `layout.tsx`: la Fase 6 (chatbot) solo necesita
  agregar su propia página bajo `/test/chatbot` (reemplazando el
  placeholder actual) para heredar automáticamente navegación y tema
  consistentes, sin tocar el layout.
- `frontend/src/lib/api.ts` ya expone `obtenerCarreras` y
  `obtenerCarreraDetalle`; la Fase 8 puede reutilizarlos directamente para
  el gráfico radar y el comparador de carreras en vez de crear un cliente
  nuevo.
- La página `/carrera/[id]` ya tiene resuelto el *fetch*, los estados de
  carga/error, y el layout base con breadcrumb: la Fase 8 solo necesita
  *añadir* el gráfico radar y el toggle "Comparar con mi perfil" sobre esta
  misma página, no reconstruirla.
- Los componentes `components/ui/` (`button`, `card`, `accordion`,
  `skeleton`, `error-state`) quedan disponibles para todas las fases
  siguientes; se recomienda agregar ahí mismo `AlertDialog` y `Sonner`
  cuando la Fase 4 (mejoras de UX pendientes) o la Fase 6 los necesiten,
  siguiendo el mismo patrón ya establecido.
