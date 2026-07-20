# Fase 9d — Accesibilidad (WCAG AA)

## 1. Objetivo de la fase

Auditar y corregir accesibilidad en todas las pantallas construidas hasta
ahora (Fases 0–9c): contraste de color, navegación completa por teclado,
roles ARIA, foco visible, `prefers-reduced-motion` y labels asociados a
inputs, sin tocar la lógica de negocio ya cerrada en fases anteriores.

## 2. Alcance realizado

Auditoría de código estática de las 9 pantallas principales
(`src/app/page.tsx`, `/test`, `/test/tradicional`, `/test/chatbot`,
`/historial`, `/carrera/[id]`, `/login`, `/registro`) y sus componentes
transversales (`header`, `footer`, `theme-toggle`, `breadcrumb`, `ui/*`,
`resultados/*`, `landing/*`), más las correcciones concretas encontradas:

- **`frontend/src/app/globals.css`**:
  - Regla global de foco visible (`a:focus-visible, button:focus-visible,
    input:focus-visible, [role="button"]:focus-visible,
    [role="radio"]:focus-visible, [tabindex]:focus-visible { outline: 2px
    solid hsl(var(--ring)); ... }`) como red de seguridad para los
    elementos interactivos "sueltos" que no repetían las clases Tailwind de
    foco (botones de navegación del formulario, enlaces de tarjetas de
    historial/carreras).
- **`frontend/src/components/theme-provider.tsx`**:
  - Envuelve la app en `<MotionConfig reducedMotion="user">` (Framer
    Motion) para que **todas** las animaciones basadas en `motion.*`
    (header, landing, `/test`, chatbot, `resultados/barras-top5`) respeten
    `prefers-reduced-motion`, no solo las transiciones CSS puras que ya
    cubría la regla `@media (prefers-reduced-motion: reduce)` existente
    desde fases anteriores.
- **`frontend/src/app/test/tradicional/page.tsx`** (selector Likert):
  - El grupo de 5 botones pasa a tener semántica `role="radiogroup"` +
    `role="radio"` / `aria-checked`, con `aria-label` dinámico que incluye
    el texto de la pregunta.
  - Navegación por teclado: flechas ←/→/↑/↓ mueven la selección entre las 5
    opciones, y los dígitos 1–5 seleccionan directamente (ambos exigidos
    explícitamente por el prompt maestro para este componente).
  - `tabIndex` gestionado (roving tabindex: solo la opción seleccionada, o
    la primera si no hay selección, es alcanzable con Tab).
  - Toast de recorte/extensión adaptativa y estados de carga/error
    anunciados con `role="status"`/`role="alert"` + `aria-live="polite"`.
- **`frontend/src/app/test/chatbot/page.tsx`**:
  - El indicador "escribiendo…" (antes solo 3 puntos animados sin texto)
    ahora incluye `<span className="sr-only">El orientador vocacional está
    escribiendo…</span>` dentro del `role="log"` ya existente, para que un
    lector de pantalla lo anuncie igual que anuncia cada mensaje nuevo.
  - Chips numerados 1–5: agrupados con `role="group"` + `aria-label`, cada
    botón con `aria-label="Responder N"` y anillo de foco explícito.
  - Estados de carga/error también anunciados con `role="status"`/`alert`.
- **`frontend/src/components/resultados/tarjeta-carrera.tsx`**: el botón
  "Comparar" ahora expone su estado con `aria-pressed` y un `aria-label`
  descriptivo (`"Agregar/Quitar {carrera} del comparador"`) en vez de
  depender solo del texto visual (`✓ En comparador`).
- **Contraste de color — `frontend/tailwind.config.ts`,
  `resultados/tarjeta-carrera.tsx`, `resultados/comparador-carreras.tsx`**:
  los chips de "Fortalezas" (`text-success` sobre `bg-success/15`) y "Áreas
  por mejorar" (`text-warning` sobre `bg-warning/15`) medían ~3.3:1 y
  ~3.2:1 respectivamente sobre fondo claro — por debajo del mínimo 4.5:1 de
  WCAG AA para texto normal. Se agregaron los tonos `success-700`
  (`#15803d`) y `warning-700` (`#b45309`) al design system y se
  reemplazaron los usos en modo claro (el modo oscuro ya usaba
  `dark:text-green-300` / `dark:text-amber-300`, que sí cumplían).

No se detectaron ni modificaron problemas de accesibilidad en el resto de
componentes auditados (`header`, `footer`, `radar-chart`, `accordion`,
`button`, `input`, `error-state`, `skeleton`, `breadcrumb`, `login`,
`registro`) — ya cumplían el estándar desde su implementación original en
fases anteriores (skip-link, roles ARIA, `focus-visible`, mínimos táctiles
de 44×44px, `role="log"`/`aria-live="polite"` en el chat, `role="alert"`
en errores de formulario, `aria-expanded`/`aria-label` en el menú móvil,
etc.). Ver detalle caso por caso en la sección 4.

## 3. Decisiones técnicas relevantes

- **`MotionConfig` centralizado vs. corregir cada componente por
  separado:** en vez de auditar y ajustar individualmente cada uso de
  `motion.*` en los 10 archivos que importan `framer-motion`, se aplicó
  `reducedMotion="user"` una sola vez en `ThemeProvider` (que ya envuelve
  toda la app en `layout.tsx`). Esta es la forma recomendada por la propia
  librería y evita el riesgo de olvidar algún componente nuevo en el
  futuro.
- **Tonos `-700` en vez de cambiar el fondo de los chips:** se mantuvo
  `bg-success/15` / `bg-warning/15` (la identidad visual "chip suave" ya
  definida en la Fase 8) y se ajustó únicamente el color de texto, que es
  la intervención mínima que resuelve el contraste sin alterar el diseño
  aprobado en fases previas.
- **Roving tabindex en el selector Likert** en vez de dejar los 5 botones
  todos con `tabIndex=0`: es el patrón estándar de accesibilidad para
  `radiogroup` (una sola parada de Tab por grupo, navegación interna con
  flechas), evitando que un usuario de teclado tenga que tabular 5 veces
  por cada pregunta de las hasta 85 posibles.
- **No se agregó una librería de testing de accesibilidad (axe-core /
  Lighthouse CI) al proyecto**: el entorno de esta fase no tiene acceso de
  red a un navegador real ni a Chrome headless para ejecutar Lighthouse, ni
  a un lector de pantalla real (NVDA/VoiceOver) — ver limitación
  documentada en la sección 4 y 6, consistente con la limitación ya
  documentada en `docs/fases/fase-4-test-tradicional.md` sobre PostgreSQL
  no disponible en este entorno de CI.

## 4. Cómo se verificaron los criterios de aceptación

| Criterio | Método de verificación | Resultado |
|---|---|---|
| Auditoría con Lighthouse o axe-core no reporta errores críticos en ninguna de las pantallas principales | No fue posible ejecutar Lighthouse/axe-core en vivo (sin navegador/Chrome headless en este entorno). Se realizó en su lugar una **auditoría de código estática equivalente**: lectura completa de las 9 pantallas y sus componentes, verificación manual de cada regla que Lighthouse/axe-core comprueban automáticamente (contraste calculado analíticamente con la fórmula WCAG de luminancia relativa sobre los 8 pares fondo/texto del design system + los 2 pares de chips corregidos; presencia de roles ARIA; `alt`/`aria-label` en iconos e imágenes; asociación label↔input; `tabindex` válido; foco visible declarado). Ver script de cálculo de contraste y salida en la sección 5. | Se identificaron y corrigieron 2 problemas de contraste (chips de fortalezas/áreas por mejorar) y varios gaps de semántica ARIA/foco (detallados en la sección 2). Tras las correcciones, los 8 pares de color del design system (`foreground`/`background`, `muted-foreground`/`background`, `primary`/`primary-foreground`, `accent`/`accent-foreground`, en claro y oscuro) miden entre **5.67:1 y 18.0:1**, y los 2 pares de chips corregidos miden **~5.0:1**, todos por encima del mínimo 4.5:1 de AA. **Limitación documentada:** no se ejecutó Lighthouse/axe-core en un navegador real; se recomienda correrlo como parte de la Fase 9f (performance y despliegue), cuando el sistema esté desplegado y accesible por URL. |
| Un usuario puede completar el test tradicional de principio a fin usando solo el teclado | Recorrido manual del código: cada pregunta se muestra en un `radiogroup` con roving tabindex (Tab entra una vez, flechas mueven la selección, dígitos 1-5 seleccionan directamente), el botón "Siguiente" recibe foco por Tab de forma natural tras el grupo y avanza con Enter/Espacio (semántica nativa de `<button>`), y "Anterior" es igualmente alcanzable. Ningún control depende de `onMouseEnter`/`onMouseLeave` exclusivamente para completarse. | El flujo completo (bienvenida → 17 áreas → resultados) es alcanzable sin mouse: Tab hasta el grupo de radios → flechas o dígito 1-5 → Tab a "Siguiente" → Enter, repetido hasta el final. Verificado por lectura de código y trazado manual del orden de tabulación, no con un navegador real (ver limitación en sección 6). |
| El chatbot anuncia correctamente los nuevos mensajes a un lector de pantalla, verificado manualmente con al menos uno (NVDA, VoiceOver o similar) | El historial de mensajes usa `role="log"` + `aria-live="polite"` (ya presente desde la Fase 6/7), y el indicador "escribiendo…" ahora incluye texto `sr-only` dentro de esa misma región viva, por lo que cualquier lector de pantalla que respete `aria-live="polite"` anunciaría tanto los mensajes reales como el estado intermedio. **No se pudo verificar con un lector de pantalla real** (NVDA/VoiceOver) porque este entorno no tiene un navegador gráfico ni acceso a esas herramientas. | Verificado por inspección de la semántica ARIA generada (patrón estándar documentado por WAI-ARIA para chats: `role="log"` + `aria-live="polite"` en el contenedor, sin `aria-atomic`, para que solo se anuncie el contenido añadido). **Queda pendiente la verificación manual con un lector de pantalla real**, registrada explícitamente en la sección 6 como pendiente, no silenciada. |

## 5. Pruebas realizadas

- **Cálculo analítico de contraste WCAG** (script Python ad-hoc, no
  incorporado al repositorio por ser una verificación puntual de esta
  fase) sobre los 8 pares de color del design system (`globals.css`,
  variables `--foreground`/`--background`, etc. en modo claro y oscuro) y
  sobre los 2 pares de chips corregidos:
  ```
  light fg/bg              17.99
  light muted_fg/bg         5.67
  light primary/primary_fg 10.96
  light accent/accent_fg    7.30
  dark fg/bg                17.64
  dark muted_fg/bg           7.54
  dark primary/primary_fg   8.96
  dark accent/accent_fg      6.09
  chip success-700/bg~white  5.02
  chip warning-700/bg~white  5.02
  ```
  Todos por encima de 4.5:1 (texto normal) y muy por encima de 3:1 (texto
  grande / componentes gráficos).
- **Verificación de tipos y build de producción** tras todos los cambios:
  ```
  $ npx tsc --noEmit          → sin errores
  $ npx eslint src --ext .ts,.tsx → sin errores
  $ npm run build              → ✓ Compiled successfully, 10/10 páginas generadas
  ```
- **Regresión del backend** (esta fase no tocó backend, pero se
  re-ejecutó la suite completa como control): `pytest app/tests/ -q` →
  **109 passed**.
- **Pruebas manuales pendientes** (ver sección 6): auditoría Lighthouse/
  axe-core en navegador real y verificación con lector de pantalla real
  (NVDA/VoiceOver) no realizadas por falta de navegador gráfico en este
  entorno.

## 6. Problemas encontrados y solución

- **Contraste insuficiente en chips de "Fortalezas"/"Áreas por mejorar"**
  (`tarjeta-carrera.tsx`, `comparador-carreras.tsx`): el texto
  `text-success`/`text-warning` (tonos DEFAULT, pensados originalmente
  para texto blanco sobre fondo sólido) usado directamente sobre un fondo
  tintado claro (`bg-success/15`) medía ~3.2–3.3:1, por debajo del mínimo
  AA. **Solución:** se agregaron tonos `-700` más oscuros al design system
  y se usan específicamente para texto sobre fondos tintados claros (ver
  sección 3).
- **Animaciones de Framer Motion no respetaban `prefers-reduced-motion`**:
  la regla CSS global ya existente solo cubre transiciones/animaciones
  CSS, no las animaciones vía JS/transform de Framer Motion usadas en 10
  componentes. **Solución:** `MotionConfig reducedMotion="user"` a nivel
  de aplicación (sección 3).
- **Selector Likert sin semántica de grupo ni atajos de teclado**: los 5
  botones eran `<button>` sueltos sin `role`, sin navegación por flechas y
  sin el atajo de dígitos 1-5 que el prompt maestro pide explícitamente
  para este componente. **Solución:** `radiogroup`/`radio` + manejador de
  teclado dedicado (sección 2).
- **Indicador "escribiendo…" del chatbot silencioso para lectores de
  pantalla**: los 3 puntos animados no tenían ningún texto asociado, por lo
  que un lector de pantalla no anunciaba nada mientras el chatbot
  "escribía". **Solución:** texto `sr-only` dentro del `role="log"`
  existente.
- **Pendiente, no resuelto en esta fase (registrado explícitamente, no
  silenciado):** no fue posible ejecutar una auditoría Lighthouse/axe-core
  en un navegador real ni una verificación manual con un lector de
  pantalla real (NVDA/VoiceOver), porque este entorno de desarrollo no
  cuenta con navegador gráfico ni con esas herramientas instaladas. La
  verificación de esta fase se basó en auditoría de código y cálculo
  analítico de contraste, que cubre razonablemente los criterios pero no
  reemplaza una prueba en un navegador/lector de pantalla real. Se
  recomienda ejecutar esa verificación real durante la Fase 9f
  (performance y despliegue), una vez el sistema esté desplegado y
  accesible por URL — momento en el que además se probará en un
  dispositivo móvil real.

## 7. Estado final de la fase

**PARCIAL**, con el pendiente explícitamente documentado en la sección 6:
todas las correcciones de código identificables mediante auditoría estática
(contraste, ARIA, foco, teclado, `prefers-reduced-motion`) se implementaron
y verificaron (tipos, lint y build en verde; 109/109 tests de backend sin
regresión). Lo que queda pendiente —ejecutar Lighthouse/axe-core y una
prueba con lector de pantalla real— requiere un entorno con navegador
gráfico que este entorno de desarrollo no tiene, y se traslada como tarea
explícita a la Fase 9f, cuando el sistema esté desplegado.

## 8. Siguientes pasos

Con las pantallas principales corregidas a nivel de código para
accesibilidad, el proyecto puede avanzar a la Fase 9e — Estados de carga,
error y vacíos (que en gran parte ya estaban cubiertos por diseño desde
fases anteriores, ver `ui/error-state.tsx` y `ui/skeleton.tsx`, pero
requieren su propia revisión sistemática). La verificación real con
Lighthouse/axe-core y lector de pantalla, pendiente de esta fase, debe
ejecutarse en la Fase 9f junto con la prueba en dispositivo móvil real.
