# Fase 9e — Estados de carga, error y vacíos

## 1. Objetivo de la fase

Revisar de punta a punta que ninguna pantalla dependiente de datos remotos
se quede en blanco o rota ante una falla, ahora que el catálogo completo de
pantallas ya existe (Fases 0–9d): skeletons coherentes con el layout real
en cada pantalla que espera datos, mensajes de error con "Reintentar" ante
fallos de red, y empty states con mensaje y acción claros.

## 2. Alcance realizado

Auditoría de código de las 9 pantallas principales y sus componentes de
resultados, con foco específico en tres patrones prohibidos por el criterio
de aceptación ("ninguna pantalla usa un spinner genérico de pantalla
completa fuera de la carga inicial de la app"): (a) spinners de texto
centrado sin forma, (b) reintentos que recargan toda la página en vez de
repetir solo la petición fallida, y (c) errores sin acción de recuperación.

- **`frontend/src/app/test/tradicional/page.tsx`**:
  - Los tres estados que antes mostraban `EstadoCentrado` (un `<p>` de texto
    centrado sobre pantalla en blanco) fueron reemplazados por dos
    skeletons nuevos que imitan el layout real:
    - `SkeletonFormulario`: reproduce la barra de progreso por área, la
      tarjeta de pregunta y los 5 botones de la escala Likert, usado tanto
      en la carga inicial de áreas/preguntas como en el instante de cálculo
      del siguiente paso ("preparando la primera pregunta").
    - `SkeletonEnviando`: reproduce la estructura de la pantalla de
      resultados que está por aparecer (radar + tarjetas), mostrado
      mientras se envía el test y se calcula la recomendación.
  - El botón "Reintentar" del estado de error **ya no ejecuta
    `window.location.reload()`** (que perdía cualquier contexto de la
    página y recargaba toda la app): la carga inicial se extrajo a la
    función `cargarDatosIniciales` (con `useCallback`), reutilizada tanto
    en el `useEffect` de montaje como en `onRetry` del nuevo `ErrorState`.
- **`frontend/src/app/test/chatbot/page.tsx`**:
  - El spinner de texto "Conectando con tu orientador vocacional..." se
    reemplazó por `SkeletonChat`, que imita burbujas de conversación
    alternadas y los chips numerados, dentro de un contenedor
    `role="status" aria-live="polite"` con texto `sr-only` equivalente
    (mismo patrón de anuncio a lectores de pantalla que ya usaba el
    spinner de texto, sin perder ese comportamiento).
  - El estado de error ahora usa el componente transversal `ErrorState`
    (antes un `<p>` + `<Button>` armado a mano), consistente con el resto
    de pantallas del sistema.
- **`frontend/src/components/resultados/comparador-carreras.tsx`**:
  - El error de carga de detalles de carreras (usado al armar el
    comparador) mostraba un simple texto rojo sin acción de recuperación.
    Se reemplazó por `ErrorState` con `onRetry`, para lo cual la carga de
    detalles faltantes se extrajo de un `useEffect` inline a una función
    `cargarFaltantes` reutilizable (misma lógica, ahora invocable también
    desde el botón "Reintentar").
- **`frontend/src/components/resultados/radar-chart.tsx`** (empty state):
  - El componente no tenía guarda para `areas.length === 0`: con cero ejes,
    la división `(Math.PI * 2 * i) / n` produce `NaN` y el SVG se renderiza
    roto (sin polígonos, sin ejes, sin mensaje) — el caso "carrera sin datos
    suficientes" mencionado explícitamente en el criterio de aceptación de
    esta fase. Se agregó un empty state explícito ("Sin datos suficientes
    para graficar / Esta carrera todavía no tiene un perfil de áreas
    configurado") antes de cualquier cálculo geométrico.

No se detectaron ni modificaron problemas en el resto de pantallas
auditadas — ya cumplían el patrón esperado desde su implementación
original en fases anteriores:

- **`frontend/src/app/historial/page.tsx`**: ya tenía skeleton (3 tarjetas
  fantasma), `ErrorState` con `onRetry`, empty state con CTA ("Realizar el
  test") para usuario nuevo sin intentos, y un estado adicional correcto
  para invitado sin sesión (`RequiereSesion`).
- **`frontend/src/app/carrera/[id]/page.tsx`**: ya tenía skeleton fiel al
  layout (título + 17 filas) y `ErrorState` con `onRetry`.
- **`frontend/src/components/landing/careers-explorer.tsx`**: ya tenía
  skeleton de grilla (9 tarjetas), `ErrorState` con `onRetry`, y un empty
  state por filtro de facultad sin resultados.
- **`frontend/src/components/resultados/pantalla-resultados.tsx`**: ya
  tenía `ErrorState` con `onRetry` para el detalle de la carrera top 1, y
  usa `Skeleton` puntual mientras el radar carga sus datos adicionales.
- **`frontend/src/app/login/page.tsx`** y **`registro/page.tsx`**: no
  cargan datos remotos al montarse (solo envían un formulario); el estado
  de envío se comunica con el texto del propio botón deshabilitado
  ("Ingresando...", "Creando cuenta...") en vez de un spinner de pantalla
  completa, lo cual ya cumplía el criterio.
- **`frontend/src/app/test/page.tsx`**: pantalla estática de selección de
  método, sin datos remotos.

## 3. Decisiones técnicas relevantes

- **Skeletons "de forma", no genéricos:** en vez de un solo componente
  `<Spinner />` reutilizado en todas partes, cada pantalla obtuvo un
  skeleton que reproduce su propio layout (barra de progreso + tarjeta de
  pregunta en el formulario; burbujas de chat en el chatbot; radar +
  tarjetas en el envío del test). Esto es consistente con el patrón que
  ya existía en `historial`, `carrera/[id]` y `careers-explorer` desde
  fases anteriores, y evita la regresión a un "spinner genérico de
  pantalla completa" que el criterio de aceptación prohíbe explícitamente.
- **`role="status"`/`aria-live="polite"` + texto `sr-only` en los nuevos
  skeletons**, en vez de solo animación visual: mantiene el mismo
  comportamiento de anuncio a lectores de pantalla que tenían los
  spinners de texto que reemplazan (requisito ya establecido en la Fase
  9d para estos mismos estados), sin sacrificar accesibilidad al
  cambiar la implementación visual.
- **`cargarDatosIniciales` / `cargarFaltantes` como funciones reutilizables
  en vez de repetir la llamada fetch en el `onRetry`:** un solo punto de
  verdad para "cómo se cargan estos datos", invocado tanto al montar el
  componente como al reintentar, evitando que ambas rutas de código
  diverjan con el tiempo.
- **No se tocó el backend ni la lógica de negocio**: esta fase es
  exclusivamente de UI states (carga/error/vacío), consistente con el
  alcance definido en el prompt maestro para 9e.

## 4. Cómo se verificaron los criterios de aceptación

| Criterio | Método de verificación | Resultado |
|---|---|---|
| Simulando el backend apagado, cada pantalla principal muestra un error claro con opción de reintentar, no una pantalla en blanco ni un error de consola visible al usuario | Este entorno no tiene un navegador real para apagar físicamente el backend y observar el resultado en vivo (misma limitación de entorno documentada en la Fase 9d). En su lugar, se trazó manualmente cada `fetch` de las 9 pantallas/componentes contra su `catch`: todas las promesas que llaman a `lib/api.ts` (que lanza `ApiError` en respuestas no-OK y deja propagar el `TypeError` nativo de `fetch` cuando el backend está inalcanzable) terminan en un `catch` que setea un estado de error legible y, en las 8 rutas con datos remotos, en un `ErrorState`/skeleton-transicional con `onRetry` conectado a la función de carga correspondiente. | Las 8 superficies con datos remotos (`historial`, `carrera/[id]`, `careers-explorer`, `pantalla-resultados`, `comparador-carreras`, `test/tradicional`, `test/chatbot`, y el radar dentro de resultados) muestran un mensaje de error con botón "Reintentar" en vez de pantalla en blanco. Verificado por lectura de código y build de producción en verde (sin errores no capturados que pudieran filtrarse a consola/UI). |
| Un usuario nuevo sin intentos previos ve un empty state explicativo en "Mis resultados anteriores", con una llamada a la acción para hacer su primer test | Ya implementado desde la Fase 9b/9d (`ListaVacia` en `historial/page.tsx`); se confirmó que sigue intacto tras los cambios de esta fase (no se tocó ese archivo). | Un usuario autenticado con `intentos.length === 0` ve "Todavía no tienes intentos guardados" + botón "Realizar el test" enlazando a `/test`. |
| Ninguna pantalla usa un spinner genérico de pantalla completa fuera de la carga inicial de la app | Búsqueda dirigida de los tres patrones de spinner genérico que existían (`EstadoCentrado` en `test/tradicional` y `test/chatbot`, texto de error sin acción en `comparador-carreras`) y reemplazo por skeletons de forma + `ErrorState`. Confirmado con `grep -rn "EstadoCentrado"` sobre `src/` tras los cambios: sin resultados (ambas funciones fueron eliminadas del código, no solo dejadas de usar). | Ya no queda ningún componente de spinner de pantalla completa genérico en el árbol de `src/app` ni `src/components`; los únicos indicadores de "cargando" restantes son los `Skeleton` con forma específica por pantalla y el indicador "escribiendo…" del chatbot (que es un elemento inline dentro de la conversación, no de pantalla completa, y ya existía desde la Fase 6/9d). |

## 5. Pruebas realizadas

- **Verificación de tipos y build de producción** tras todos los cambios:
  ```
  $ npx tsc --noEmit              → sin errores
  $ npx eslint src --ext .ts,.tsx  → sin errores
  $ npm run build                  → ✓ Compiled successfully, 10/10 páginas generadas
  ```
- **Búsqueda de regresión de patrones eliminados**:
  ```
  $ grep -rn "EstadoCentrado" src/     → sin resultados
  $ grep -rn "location.reload"  src/   → sin resultados
  ```
- **Regresión del backend** (esta fase no tocó backend, pero se
  re-ejecutó la suite completa como control): `pytest app/tests/ -q` →
  **109 passed**, sin cambios respecto a la Fase 9d.
- **Prueba manual pendiente** (ver sección 6): apagar el backend real y
  observar en un navegador en vivo cada pantalla no fue posible en este
  entorno de desarrollo sin navegador gráfico; la verificación se hizo por
  trazado de código de cada ruta `try/catch` hacia su estado de error en
  UI, siguiendo el mismo patrón de limitación ya documentado en la Fase
  9d.

## 6. Problemas encontrados y solución

- **Spinners de texto de pantalla completa en `test/tradicional` y
  `test/chatbot`** (`EstadoCentrado`): violaban directamente el criterio
  de aceptación de esta fase. **Solución:** `SkeletonFormulario`,
  `SkeletonEnviando` y `SkeletonChat`, cada uno con la forma de la
  pantalla que reemplaza (sección 2).
- **Reintento con `window.location.reload()`** en `test/tradicional`: además
  de no encajar con el patrón `ErrorState`/`onRetry` del resto del sistema,
  recargaba la aplicación completa (perdiendo, por ejemplo, el estado de
  sesión ya validado por `SessionInit` hasta que se revalida de nuevo).
  **Solución:** función `cargarDatosIniciales` reutilizable invocada desde
  `onRetry`.
- **Error sin acción de recuperación en `comparador-carreras`**: un
  usuario cuya conexión falla justo al armar el comparador no tenía forma
  de reintentar sin recargar toda la pantalla de resultados (perdiendo su
  selección de carreras a comparar). **Solución:** `ErrorState` con
  `onRetry` conectado a `cargarFaltantes`, que conserva la selección
  (`seleccionadas` no se resetea).
- **`RadarChart` sin empty state para `areas.length === 0`**: producía un
  SVG roto (coordenadas `NaN`) en vez del empty state que el criterio de
  aceptación pide explícitamente para "carrera sin datos suficientes".
  **Solución:** guarda temprana que retorna un mensaje explicativo antes
  de cualquier cálculo geométrico (sección 2).
- **Pendiente, no resuelto en esta fase (registrado explícitamente, no
  silenciado):** no fue posible apagar un backend real y observar el
  comportamiento en un navegador en vivo, por no contar este entorno con
  un navegador gráfico ni con el backend corriendo como proceso de larga
  duración accesible desde fuera de la suite de tests. La verificación se
  basó en trazado de código de cada ruta de error hacia su UI
  correspondiente, que cubre razonablemente el criterio pero no reemplaza
  una prueba en vivo. Se recomienda repetirla durante la Fase 9f
  (performance y despliegue), una vez el sistema esté desplegado y se
  pueda apagar/reiniciar el backend real para observar el frontend en
  producción.

## 7. Estado final de la fase

**COMPLETA**, con el pendiente de verificación en vivo explícitamente
documentado en la sección 6 (misma naturaleza que el pendiente ya aceptado
en el cierre de la Fase 9d, por la misma limitación de entorno). Los tres
patrones prohibidos por el criterio de aceptación (spinner de pantalla
completa genérico, reintento por recarga total, error sin acción) fueron
localizados por auditoría de código, corregidos y verificados con
`tsc`/`eslint`/`build` en verde y sin regresión en la suite de backend
(109/109).

## 8. Siguientes pasos

Con las pantallas principales cubiertas para carga/error/vacío, el
proyecto puede avanzar a la Fase 9f — Performance y despliegue, que
además de optimizar y desplegar el sistema, debe ejecutar las
verificaciones en vivo que quedaron pendientes tanto de la Fase 9d
(Lighthouse/axe-core, lector de pantalla real) como de esta fase (apagar
el backend real y observar el frontend desplegado), todas en el mismo
entorno con navegador gráfico y dispositivo móvil real que esa fase ya
requiere.
