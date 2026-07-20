# Fase 9a — Autenticación (registro, login, sesión)

## 1. Objetivo de la fase

Habilitar cuentas de usuario reales con autenticación JWT (registro, login,
refresh y cierre de sesión), sin tocar todavía el historial de intentos
(Fase 9b), la accesibilidad (Fase 9d) ni el despliegue (Fase 9f).

## 2. Alcance realizado

### Backend

- **`backend/app/core/security.py`** (nuevo): utilidades puras, sin
  dependencia de FastAPI ni de la base de datos:
  - `hash_password` / `verificar_password`, sobre `passlib[bcrypt]` (ya
    declarado en `requirements.txt` desde antes de esta fase).
  - `crear_access_token` / `crear_refresh_token` / `decodificar_token`, sobre
    `python-jose`. Cada token JWT lleva un claim `type` (`"access"` o
    `"refresh"`) además de `sub` (el `usuario_id`), `iat` y `exp`, para poder
    rechazar explícitamente un refresh token usado donde se espera un access
    token (y viceversa).
  - `TokenInvalidoError`: excepción única para token ausente, mal firmado,
    expirado, o de tipo incorrecto.
- **`backend/app/core/deps.py`** (nuevo): dependencias de FastAPI para
  proteger endpoints:
  - `obtener_usuario_actual`: dependencia obligatoria (401 si no hay token
    válido). Se usa en `GET /auth/me`.
  - `obtener_usuario_opcional`: dependencia "suave" (nunca lanza error;
    devuelve `None` si no hay sesión), pensada para que la Fase 9b pueda
    asociar un intento a `usuario_id` cuando hay sesión, sin romper el flujo
    de invitado.
- **`backend/app/schemas/auth.py`** (nuevo): `RegistroIn`, `LoginIn`,
  `RefreshIn`, `UsuarioOut` (nunca expone `password_hash`), `TokenOut`
  (`access_token`, `refresh_token`, `token_type`, `usuario`).
- **`backend/app/api/auth.py`** (nuevo): router `/auth` con:
  - `POST /auth/registro`: crea el `Usuario` (modelo ya existente desde la
    Fase 1, tabla `usuarios` ya migrada), rechaza con `409` si el email ya
    existe, y devuelve el par de tokens.
  - `POST /auth/login`: verifica email + password contra `password_hash`;
    `401` genérico ante email inexistente o password incorrecto (sin
    distinguir cuál de los dos falló, para no filtrar qué emails existen).
  - `POST /auth/refresh`: valida el refresh token y emite un **nuevo** par
    access+refresh (rotación de refresh token en cada uso).
  - `GET /auth/me`: devuelve el usuario autenticado; usado por el frontend
    para validar la sesión persistida al recargar la página.
- **`backend/app/main.py`**: se registra `auth.router` (antes que
  `dominio.router`, sin efecto funcional, solo orden de lectura).
- **`backend/requirements.txt`**: se agrega `email-validator`, requerido por
  `pydantic.EmailStr` (usado en `RegistroIn`/`LoginIn`).
- **Modelo `Usuario`, migración y `.env.example`**: no requirieron cambios —
  ya estaban completos desde la Fase 1 (tabla `usuarios` con
  `password_hash`, y las variables `JWT_*` ya en `.env.example`), anticipando
  esta fase.

### Frontend

- **`frontend/src/lib/api.ts`**: se agrega `fetchJsonAutenticado` (adjunta
  `Authorization: Bearer <token>`), los tipos `Usuario`/`TokenOut`, y las
  funciones `registrarUsuario`, `iniciarSesion`, `refrescarToken`,
  `obtenerPerfil`.
- **`frontend/src/lib/auth-store.ts`** (nuevo): store Zustand
  (`useAuthStore`) con `usuario`, `accessToken`, `refreshToken`, `cargando`,
  las acciones `registrarse` / `iniciarSesion` / `cerrarSesion` /
  `refrescarSesion`, persistido en `localStorage` vía el middleware
  `zustand/middleware` `persist` (clave `vocacional_auth`). También expone
  `validarSesionActual()`, que llama a `GET /auth/me` con el token
  persistido y, si expiró, intenta renovarlo antes de cerrar sesión.
- **`frontend/src/components/auth/session-init.tsx`** (nuevo): componente
  sin UI montado una vez en `layout.tsx`, que dispara
  `validarSesionActual()` al cargar la app.
- **`frontend/src/components/ui/input.tsx`** (nuevo): input de formulario
  reutilizable, mismo patrón (`cva`/`cn`) que `button.tsx`.
- **`frontend/src/app/login/page.tsx`** y **`frontend/src/app/registro/page.tsx`**
  (nuevos): pantallas de login y registro con `Card` + `Input` existentes,
  validación mínima en cliente (longitud de password), manejo de errores por
  código HTTP (`401`, `409`, `422`) y redirección a `/` tras éxito.
- **`frontend/src/components/header.tsx`**: si hay sesión, muestra el
  nombre de pila del usuario y un botón "Salir"; si no, un botón "Iniciar
  sesión" hacia `/login`. Replicado en el menú móvil.

## 3. Decisiones técnicas relevantes

- **Rotación de refresh token en cada `/auth/refresh`**: en vez de reusar el
  mismo refresh token hasta su expiración, cada refresh emite uno nuevo. No
  estaba explícitamente pedido por el prompt maestro, pero es una práctica
  estándar de seguridad de bajo costo (evita que un refresh token robado
  siga siendo válido indefinidamente si el usuario legítimo sigue usando la
  app y renovando).
- **Error 401 genérico en login** (no distingue "email no existe" de
  "password incorrecto"): decisión de seguridad estándar para no permitir
  enumerar emails registrados.
- **Dependencia "opcional" (`obtener_usuario_opcional`) ya creada en esta
  fase**, aunque su primer uso real es en la Fase 9b: se decidió incluirla
  ahora porque es parte del mismo módulo de autenticación y su ausencia
  bloquearía el arranque de 9b; no se conecta a ningún endpoint de test
  todavía, respetando el alcance de 9a.
- **`email-validator` agregado a `requirements.txt`**: no estaba listado
  explícitamente en el stack tecnológico del prompt maestro, pero es una
  dependencia obligatoria de `pydantic.EmailStr` (sin ella, Pydantic lanza
  `ImportError` en tiempo de arranque).
- **Persistencia de sesión en `localStorage` vía Zustand `persist`**: sigue
  el mismo patrón ya usado en el proyecto para `ultimo-resultado.ts`
  (Fase 8), reutilizando la convención existente en vez de introducir una
  librería nueva.

## 4. Cómo se verificaron los criterios de aceptación

| Criterio | Método de verificación | Resultado |
|---|---|---|
| Un usuario puede registrarse con email y contraseña, y el password nunca se guarda en texto plano | Lectura de código: `RegistroIn` exige `password` (min. 8) pero el modelo `Usuario` solo persiste `password_hash = hash_password(payload.password)`; `UsuarioOut` (lo único que se devuelve) no incluye `password_hash`. Verificado también por los tests unitarios de `hash_password`/`verificar_password` (ver sección 5) | Cumplido a nivel de código y de tests unitarios. **Pendiente de verificación HTTP real** (ver sección 6) |
| Un usuario puede iniciar sesión y recibir un token válido; un token expirado o inválido es rechazado por los endpoints protegidos | Tests unitarios de `decodificar_token` cubren: token válido, token con firma alterada, token expirado, token del tipo incorrecto, token sin claim `sub`. `obtener_usuario_actual` traduce cualquier `TokenInvalidoError` a `401` | Cumplido a nivel de tests unitarios de la lógica JWT. **Pendiente de verificación HTTP real** (ver sección 6) |
| Un usuario puede cerrar sesión desde el frontend y el token deja de usarse en las siguientes peticiones | Lectura de código: `cerrarSesion()` limpia `usuario`/`accessToken`/`refreshToken` del store (y por lo tanto de `localStorage`, vía `persist`); el Header deja de mostrar el estado autenticado inmediatamente | Cumplido a nivel de código. **Pendiente de verificación manual en navegador** (ver sección 6) |

## 5. Pruebas realizadas

- **`backend/app/tests/test_fase9a_autenticacion.py`** (nuevo, 10 tests):
  cubre `app.core.security` de punta a punta sin necesitar PostgreSQL (igual
  patrón que `test_fase4_tradicional.py` y `test_mahalanobis.py`):
  - Hash de password nunca es igual al texto plano y usa el prefijo bcrypt.
  - Verificación de password correcta / incorrecta.
  - Access token y refresh token se decodifican al mismo `usuario_id`.
  - Un refresh token es rechazado si se usa como access token, y viceversa.
  - Un token con la firma alterada es rechazado.
  - Un token expirado es rechazado.
  - Un token sin claim `sub` es rechazado.
- **Pruebas HTTP de integración no ejecutadas en este entorno**: igual que
  se documentó desde la Fase 4, este entorno de trabajo no tiene acceso a
  red para instalar `python-jose`, `passlib[bcrypt]`, `email-validator` ni
  para levantar PostgreSQL, por lo que los tests anteriores no pudieron
  correrse aquí (se verificó únicamente que todos los módulos nuevos
  compilan sin errores de sintaxis con `python -m py_compile`). Quedan como
  **pendiente de ejecución** en un entorno con dependencias instaladas y
  PostgreSQL disponible, antes de dar la fase por completamente cerrada:
  1. `pip install -r requirements.txt && pytest app/tests/test_fase9a_autenticacion.py -v`
  2. Con el backend y PostgreSQL corriendo: `POST /auth/registro` con un
     email nuevo → esperar `201` y un `TokenOut`; repetir con el mismo email
     → esperar `409`.
  3. `POST /auth/login` con esas credenciales → esperar `200`; repetir con
     password incorrecto → esperar `401`.
  4. `GET /auth/me` con el `access_token` recibido → esperar `200` con los
     datos del usuario; repetir sin header `Authorization` → esperar `401`.
  5. `POST /auth/refresh` con el `refresh_token` recibido → esperar `200`
     con un nuevo par de tokens.
- **Prueba manual de frontend no ejecutada** (requiere `npm install`, que
  tampoco fue posible en este entorno sin red): flujo sugerido — abrir
  `/registro`, crear una cuenta, verificar que el Header pasa a mostrar el
  nombre y el botón "Salir"; recargar la página y confirmar que la sesión
  persiste (gracias a `SessionInit` + `localStorage`); hacer clic en "Salir"
  y confirmar que el Header vuelve a mostrar "Iniciar sesión".

## 6. Problemas encontrados y solución

- **Sin acceso a red en este entorno de trabajo**: no fue posible ejecutar
  `pip install` (faltan `python-jose`, `passlib[bcrypt]`, `email-validator`)
  ni `npm install`, por lo que ni la suite de tests de backend ni el
  frontend pudieron ejecutarse realmente aquí. Se mitigó verificando la
  sintaxis de todos los módulos Python nuevos con `python -m py_compile` (sin
  errores) y revisando manualmente cada import/tipo contra las convenciones
  ya usadas en el resto del proyecto (Fases 0-8). **Esto queda pendiente**:
  antes de considerar 9a totalmente cerrada, se debe ejecutar la suite de
  tests y el flujo manual descrito en la sección 5 en un entorno con
  dependencias instaladas.
- **`pydantic.EmailStr` requiere `email-validator`**, no listado
  originalmente en `requirements.txt`: se agregó explícitamente (ver sección
  3), sin lo cual la app fallaría al arrancar con `ImportError`.

## 7. Estado final de la fase

**PARCIAL.** El código de los tres criterios de aceptación está completo e
implementado siguiendo las convenciones del proyecto, y la lógica pura de
seguridad (hashing + JWT) está cubierta por 10 tests unitarios. Sin embargo,
ni esos tests ni las pruebas de integración HTTP/frontend pudieron
ejecutarse en este entorno por falta de acceso a red para instalar
dependencias y levantar PostgreSQL/`npm`. La fase se documenta como avance
real pero **no debe considerarse cerrada** hasta correr `pytest` y el flujo
manual de la sección 5 en un entorno de desarrollo completo.

## 8. Siguientes pasos

Con `Usuario`, `/auth/registro`, `/auth/login`, `/auth/refresh`,
`obtener_usuario_actual` y `obtener_usuario_opcional` ya implementados, la
Fase 9b puede conectar `usuario_id` (columna ya existente en `IntentoTest`
desde la Fase 4) a los endpoints `POST /test/tradicional` / `POST
/test/chatbot` usando `obtener_usuario_opcional`, y exponer
`GET /usuarios/me/intentos` protegido con `obtener_usuario_actual`. Antes de
avanzar, se recomienda cerrar el pendiente de la sección 6 (ejecutar la
suite de tests y la verificación manual) para no construir 9b sobre una
base de autenticación no verificada en ejecución real.
