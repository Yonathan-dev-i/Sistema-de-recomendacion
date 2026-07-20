# Fase 9b — Intentos asociados a usuario e historial

## 1. Objetivo de la fase

Conectar la autenticación de la Fase 9a con los intentos de test ya
existentes desde la Fase 4: asociar cada intento a `usuario_id` cuando hay
sesión activa, y exponer ese historial al usuario en una pantalla "Mis
resultados anteriores", sin romper el flujo de invitado.

## 2. Alcance realizado

### Backend

- **`backend/app/api/test.py`**: `POST /test/tradicional` ahora depende de
  `obtener_usuario_opcional` (Fase 9a) y crea el `IntentoTest` con
  `usuario_id=usuario.id if usuario else None`. Sin token, o con un token
  inválido/expirado, el comportamiento es exactamente el de invitado (igual
  que antes de esta fase).
- **`backend/app/api/chatbot.py`**: `POST /test/chatbot/iniciar` recibe la
  misma dependencia opcional y asocia el `usuario_id` **al crear la sesión**.
  `POST /test/chatbot/{sesion_id}/mensaje` y `GET /test/chatbot/{sesion_id}`
  no necesitaron cambios: la asociación ya quedó fijada en el `IntentoTest`
  desde `/iniciar`, y ambos endpoints operan sobre ese mismo registro.
- **`backend/app/services/historial_service.py`** (nuevo): lógica pura,
  sin dependencia de la sesión de base de datos —
  - `resumen_intento(intento)`: arma el dict `{id, metodo, estado,
    iniciado_en, completado_en, carrera_top1_id, carrera_top1,
    afinidad_top1_pct}` a partir de un `IntentoTest`, leyendo el Top 1 desde
    el snapshot ya persistido en `top5_resultado` (nunca recalcula nada, así
    el historial no puede mostrar una carrera distinta a la que el usuario
    vio al terminar el test). Con `top5_resultado` nulo (intento en
    progreso/abandonado), los tres campos de resultado quedan en `None`.
  - `ordenar_intentos_por_fecha_desc(intentos)`: ordena por `iniciado_en`
    descendente sin mutar la lista recibida.
- **`backend/app/schemas/usuarios.py`** (nuevo): `IntentoResumenOut`, el
  schema de salida de la lista de intentos.
- **`backend/app/api/usuarios.py`** (nuevo): router `/usuarios` con
  `GET /usuarios/me/intentos`, protegido con `obtener_usuario_actual`
  (dependencia "dura" de la Fase 9a → `401` sin sesión válida). Filtra
  `IntentoTest.usuario_id == usuario.id`, ordena con
  `ordenar_intentos_por_fecha_desc` y serializa cada fila con
  `resumen_intento`.
- **`backend/app/main.py`**: se registra `usuarios.router` y se actualiza el
  docstring de arranque.

### Frontend

- **`frontend/src/lib/api.ts`**:
  - `enviarTestTradicional(respuestas, accessToken?)` y
    `iniciarChat(accessToken?)` ahora aceptan un access token opcional; si
    viene, usan `fetchJsonAutenticado` (adjunta `Authorization: Bearer`), si
    no, siguen usando `fetchJson` sin cambios de comportamiento para
    invitados.
  - Nuevo tipo `IntentoResumen` y función `obtenerMisIntentos(accessToken)`
    → `GET /usuarios/me/intentos`.
- **`frontend/src/app/test/tradicional/page.tsx`**: lee `accessToken` de
  `useAuthStore` y lo pasa a `enviarTestTradicional`.
- **`frontend/src/app/test/chatbot/page.tsx`**: lee `accessToken` de
  `useAuthStore` y lo pasa a `iniciarChat` (solo al crear una sesión nueva;
  al reanudar una sesión existente no hace falta, ya quedó asociada al
  crearse).
- **`frontend/src/app/historial/page.tsx`** (nuevo): pantalla "Mis
  resultados anteriores" —
  - Sin sesión: tarjeta explicando que el historial requiere cuenta, con
    botones a `/login` y `/registro` (nunca un error crudo ni una pantalla
    en blanco).
  - Con sesión: `useEffect` dispara `obtenerMisIntentos`, con skeletons
    mientras carga, `ErrorState` reutilizable con reintento ante fallo de
    red, y un estado vacío si el usuario aún no tiene intentos.
  - Cada fila muestra fecha, método (ícono distinto para formulario/chat),
    estado si no está completado, carrera Top 1 y `afinidad_pct`; si hay
    `carrera_top1_id`, la fila entera enlaza a `/carrera/{id}` (el "detalle
    de resultado" pedido por el criterio de aceptación, reutilizando la
    página de detalle de carrera ya existente desde la Fase 5/8 en vez de
    construir una pantalla nueva).
- **`frontend/src/components/header.tsx`**: agrega el enlace "Mis
  resultados" (con ícono `History`) junto al nombre del usuario, en desktop
  y en el menú móvil, visible únicamente cuando hay sesión — así el usuario
  invitado nunca ve la opción de historial.
- **`frontend/src/app/test/page.tsx`**:
  - Se actualiza el texto de "Continuar como invitado", que hasta esta fase
    decía "el historial de resultados llega en una fase posterior"; ahora
    explica que solo los intentos con sesión iniciada quedan guardados en
    "Mis resultados anteriores", con link directo.
  - Se corrige `disponible: false` → `disponible: true` en la tarjeta del
    método "Test con Chatbot" (ver sección 6: era un dato desactualizado de
    una fase anterior, detectado al verificar el flujo de invitado de esta
    fase).

## 3. Decisiones técnicas relevantes

- **`GET /usuarios/me/intentos` no acepta paginación ni filtros** (por
  método, por fecha, etc.): no estaba pedido por el prompt maestro y el
  volumen esperado de intentos por usuario es bajo (un test dura ~10-15
  min); se prefirió no construir esa complejidad ahora. Si el catálogo de
  intentos por usuario creciera, es un cambio aislado al router y al
  servicio, sin tocar el modelo.
- **El Top 1 del historial se lee del snapshot (`top5_resultado[0]`), nunca
  se recalcula**: es la misma decisión de diseño que ya usa
  `PantallaResultados` (Fase 8) para no depender de que la matriz de
  covarianza cacheada siga siendo idéntica más adelante; garantiza que el
  historial y la pantalla de resultados original nunca puedan divergir.
- **`carrera_top1_id` se agregó al schema** (no estaba explícitamente
  pedido) para poder cumplir el criterio "cada uno enlazando a su detalle de
  resultado" enlazando directamente a `/carrera/{id}` (página ya construida
  en la Fase 5), en vez de crear una pantalla de "detalle de intento" nueva
  que hubiera duplicado la mayor parte de esa vista.
- **La sesión de chatbot solo resuelve el usuario en `POST
  /test/chatbot/iniciar`**, no en `/mensaje` ni en el `GET` de reanudación:
  el `usuario_id` es un atributo del intento completo (una sola sesión de
  principio a fin), no de cada mensaje, así que fijarlo una vez al crear la
  sesión es suficiente y evita depender de que el usuario mantenga el mismo
  token disponible turno a turno.
- **Intentos de invitado (`usuario_id` nulo) nunca se pueden "reclamar"
  retroactivamente iniciando sesión después**: no había un mecanismo para
  esto en el prompt maestro y añadirlo implica decisiones de seguridad no
  triviales (¿cómo probar que ese intento anónimo es tuyo?); se deja fuera
  de alcance explícitamente.
- **Corrección de `disponible: false` en el método chatbot** (`frontend/src/app/test/page.tsx`):
  no es parte del alcance nominal de la Fase 9b, pero se detectó al revisar
  el flujo de invitado/autenticado de punta a punta y es una línea que
  contradice el estado real del proyecto desde la Fase 6/7 (el chatbot ya
  está completo y probado). Se corrige aquí siguiendo la regla del prompt
  maestro de resolver primero lo que se descubre roto de una fase anterior.

## 4. Cómo se verificaron los criterios de aceptación

| Criterio | Método de verificación | Resultado |
|---|---|---|
| Un usuario autenticado que completa el test ve su intento reflejado en "Mis resultados anteriores" sin recargar manualmente nada raro | Lectura de código: `enviarTestTradicional`/`iniciarChat` adjuntan el token cuando `useAuthStore` tiene sesión → el intento queda con `usuario_id`; `/historial` hace `fetch` en `useEffect` al montar, por lo que una navegación normal (sin recarga manual) desde resultados hacia `/historial` ya trae los datos frescos | Cumplido a nivel de código. **Pendiente de verificación HTTP/E2E real** (ver sección 6) |
| Un usuario invitado puede completar el test sin errores ni pantallas rotas, y no ve la opción de historial (o la ve deshabilitada con una explicación) | Lectura de código: sin `accessToken`, `enviarTestTradicional`/`iniciarChat` siguen llamando a `fetchJson` exactamente como antes de esta fase (mismo payload, sin header `Authorization`); `obtener_usuario_opcional` nunca lanza error ante ausencia de token, así que el backend no cambia su respuesta para invitados. El enlace "Mis resultados" en `Header` solo se renderiza si `usuario` no es `null`; `/historial` sin sesión muestra la tarjeta `RequiereSesion` con explicación y enlaces a login/registro, no un error | Cumplido a nivel de código |
| El historial muestra al menos fecha, método usado (formulario/chatbot) y la carrera top 1 de cada intento | Lectura de código: `TarjetaIntento` en `historial/page.tsx` renderiza `fecha`, el label de `metodo`, y `carrera_top1` (con `afinidad_top1_pct`); `IntentoResumenOut` expone esos campos desde `resumen_intento` | Cumplido; verificado también por los tests unitarios de `resumen_intento` (ver sección 5) |

## 5. Pruebas realizadas

- **`backend/app/tests/test_fase9b_intentos_historial.py`** (nuevo, 4
  tests): cubre `app.services.historial_service` construyendo instancias de
  `IntentoTest` en memoria (sin PostgreSQL, mismo patrón que
  `test_fase9a_autenticacion.py`):
  - `resumen_intento` de un intento completado incluye `carrera_top1_id`,
    `carrera_top1` y `afinidad_top1_pct` correctos, leídos del snapshot.
  - `resumen_intento` de un intento en progreso (`top5_resultado=None`) deja
    esos tres campos en `None`, y `completado_en` también.
  - `ordenar_intentos_por_fecha_desc` ordena de más reciente a más antiguo.
  - `ordenar_intentos_por_fecha_desc` no muta la lista original.
- **Suite completa ejecutada en este entorno**: a diferencia de fases
  9a en adelante, esta vez sí hubo acceso a red (`pypi.org` está en la
  lista de dominios permitidos), así que se pudo instalar
  `requirements.txt` y correr la suite completa:
  `python -m pytest app/tests/ -q` → **97 passed** (94 tests previos + los
  4 nuevos de esta fase, sin restar ninguno).
  - Al correr por primera vez aparecieron **3 fallos preexistentes** en
    `test_fase9a_autenticacion.py` (`hash_password`/`verificar_password`
    lanzaban `ValueError: password cannot be longer than 72 bytes...`), por
    una incompatibilidad entre `passlib==1.7.4` y `bcrypt>=4.1` (passlib lee
    `bcrypt.__about__.__version__`, atributo removido en bcrypt 4.1+). Se
    corrigió fijando `bcrypt<4.1` en `requirements.txt` (ver sección 6);
    tras la corrección, los 97 tests pasan.
- **Frontend**: se pudo correr `npm install` (dominios de npm también
  permitidos) y:
  - `npx tsc --noEmit` → sin errores de tipos en todo el proyecto.
  - `npx eslint` sobre los archivos nuevos/modificados de esta fase → sin
    errores.
  - `npm run build` (Next.js, producción) → build exitoso, incluyendo la
    nueva ruta estática `/historial` (4.42 kB, 121 kB First Load JS) junto a
    todas las rutas previas.
- **Backend, verificación de rutas**: se importó `app.main:app` con
  variables de entorno mínimas (sin PostgreSQL real disponible) y se generó
  `app.openapi()`, confirmando que `GET /usuarios/me/intentos` queda
  registrado junto a los 14 endpoints previos, sin conflictos de rutas.
- **Pruebas HTTP de integración contra PostgreSQL real, y prueba manual de
  navegador, no ejecutadas en este entorno** (no hay un servidor PostgreSQL
  disponible aquí). Quedan como **pendiente de ejecución** en un entorno
  con PostgreSQL levantado:
  1. `POST /auth/registro` → guardar `access_token`.
  2. `POST /test/tradicional` con ese `access_token` en `Authorization` →
     verificar en la fila `intentos_test` de la base de datos que
     `usuario_id` quedó seteado (no nulo).
  3. `POST /test/tradicional` **sin** header `Authorization` → verificar que
     el intento se crea igual, con `usuario_id` nulo, y la respuesta HTTP es
     idéntica en forma a la del paso anterior.
  4. `GET /usuarios/me/intentos` con el `access_token` → esperar `200` con
     al menos el intento del paso 2, `carrera_top1`/`afinidad_top1_pct`
     poblados.
  5. `GET /usuarios/me/intentos` sin header `Authorization` → esperar `401`.
  6. En el navegador: iniciar sesión, completar el test tradicional,
     navegar a "Mis resultados" desde el Header → confirmar que el intento
     recién creado aparece primero en la lista, con fecha/método/Top 1
     correctos, y que el clic sobre la fila navega a `/carrera/{id}` de esa
     carrera.
  7. En el navegador, sin sesión: confirmar que el Header no muestra "Mis
     resultados", que navegar manualmente a `/historial` muestra la tarjeta
     de "necesitas una cuenta" (no un error), y que completar el test como
     invitado sigue funcionando exactamente igual que en la Fase 4/6.

## 6. Problemas encontrados y solución

- **`passlib` + `bcrypt>=4.1` incompatibles** (detectado al correr la suite
  completa por primera vez en este entorno, ver sección 5): se fijó
  `bcrypt<4.1` en `backend/requirements.txt`. Es un problema heredado de la
  Fase 9a (no de esta fase), pero se corrige aquí siguiendo la regla del
  prompt maestro de resolver primero lo que se descubre roto de una fase
  anterior antes de seguir avanzando. Con la corrección, los 10 tests de
  `test_fase9a_autenticacion.py` pasan realmente (antes solo se había
  verificado que compilaban, no que corrían).
- **`disponible: false` desactualizado en la tarjeta del chatbot**
  (`frontend/src/app/test/page.tsx`): quedó así desde la Fase 5 (landing),
  pero el chatbot está completo y probado desde la Fase 6/7. No bloqueaba
  funcionalmente el flujo de invitado (el enlace igual navegaba a
  `/test/chatbot`), pero contradecía el estado real del sistema y hubiera
  confundido a un usuario invitado leyendo "(próximamente)" junto a un
  método que sí funciona. Se corrigió a `disponible: true`.
- **Sin PostgreSQL disponible en este entorno**: igual que en fases
  anteriores, no fue posible correr las pruebas de integración HTTP reales
  ni la verificación manual en navegador. Se mitigó extrayendo toda la
  lógica de armado/orden del historial a `historial_service.py` (puro,
  testeable sin base de datos) y verificando el resto por lectura de código
  más los chequeos automatizados que sí corrieron (pytest, tsc, eslint,
  build de Next.js, generación de `openapi()`). **Esto queda pendiente**:
  correr los 7 pasos de verificación manual listados en la sección 5 antes
  de dar la Fase 9b por completamente cerrada.

## 7. Estado final de la fase

**PARCIAL.** El código de los tres criterios de aceptación está completo,
sigue las convenciones ya establecidas en el proyecto, y esta vez se pudo
verificar con herramientas reales (no solo lectura de código): la suite
completa de backend corre y pasa (97/97, incluyendo una corrección a un
bug heredado de la Fase 9a), el frontend compila sin errores de tipos ni de
lint, y el build de producción de Next.js genera la nueva ruta `/historial`
correctamente. Sin embargo, no fue posible levantar PostgreSQL en este
entorno, por lo que la asociación real de `usuario_id` en la base de datos
y el flujo completo en el navegador (login → test → historial) no se
verificaron de punta a punta. La fase se documenta como avance real, con
una base más verificada que en 9a, pero **no debe considerarse cerrada**
hasta correr los 7 pasos manuales de la sección 5 en un entorno con
PostgreSQL disponible.

## 8. Siguientes pasos

Con el historial ya conectado a la autenticación, la Fase 9c (test de
equivalencia formulario vs. chatbot) puede construirse sin depender de
nada de esta fase — sigue comparando `vector_usuario`/Top 5 a nivel de los
servicios puros (`test_service`, `chatbot_service`), que no cambiaron aquí.
Antes de avanzar, se recomienda:

1. Cerrar el pendiente de la sección 6 de la **Fase 9a** (ya no bloqueado
   por el bug de `bcrypt`, solo falta correr los pasos manuales contra
   PostgreSQL real).
2. Cerrar el pendiente de la sección 6 de **esta fase** (los 7 pasos
   manuales/HTTP contra PostgreSQL real).
3. Recién entonces, avanzar a la Fase 9c con la autenticación y el
   historial verificados en ejecución real, no solo por lectura de código.
