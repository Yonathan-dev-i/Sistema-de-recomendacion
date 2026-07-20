# Prompt Maestro: Sistema Web de Orientación Vocacional (Next.js + FastAPI + Mahalanobis)

## Rol

Actúa como un **Arquitecto de Software Senior**, **UX/UI Designer**, **Desarrollador Full Stack (Next.js + FastAPI)**, **Data Scientist** (para el cálculo estadístico de recomendación) y **Especialista en Orientación Vocacional**.

El objetivo es desarrollar un **Sistema Inteligente de Orientación Vocacional** para la **Universidad Nacional del Altiplano (UNA Puno)**, con una interfaz moderna, intuitiva y profesional, y un motor de recomendación estadísticamente correcto basado en la **Distancia de Mahalanobis**.

### Stack tecnológico obligatorio

* **Frontend:** Next.js 15 (App Router) + TypeScript + Tailwind CSS + shadcn/ui
* **Backend:** FastAPI (Python 3.11+)
* **Base de datos:** PostgreSQL
* **ORM:** SQLAlchemy 2.0 (modo async con `asyncpg`)
* **Validación:** Pydantic v2 (schemas de entrada/salida)
* **Autenticación:** JWT (access + refresh token)
* **Estado global (frontend):** Zustand
* **Comunicación:** REST API (JSON)
* **Cálculo científico (backend):** NumPy + SciPy (`scipy.spatial.distance.mahalanobis`, `numpy.cov`, `numpy.linalg.pinv`)
* **Algoritmo de recomendación:** Distancia de Mahalanobis (detallado íntegramente en la sección "Algoritmo de recomendación")
* **Chatbot:** Basado en reglas (máquina de estados finita, SIN IA generativa, SIN llamadas a LLMs externos)
* **Diseño:** Minimalista, moderno, responsive, modo claro/oscuro

---

# Plan de Desarrollo por Fases

El sistema se construye de forma **incremental y verificable**: cada fase produce un entregable funcional y probado antes de avanzar a la siguiente. No se debe iniciar una fase sin haber cerrado los criterios de aceptación de la anterior. Esto permite mostrar avances reales en cada etapa (útil para sustentaciones o revisiones parciales) y evita construir sobre una base inestable.

**Regla de progresión:** cada fase termina con una lista de "Criterios de aceptación" que deben cumplirse antes de pasar a la siguiente. Si al llegar a una fase se descubre que algo de una fase anterior falla, se corrige ahí antes de continuar.

## Documentación obligatoria de cierre de fase

**Cada fase, sin excepción, termina generando un archivo Markdown de cierre** dentro de `docs/fases/`, con nomenclatura `docs/fases/fase-N-nombre-corto.md` (ej. `docs/fases/fase-0-andamiaje.md`, `docs/fases/fase-4-test-tradicional.md`). Este archivo no es opcional ni un resumen superficial: es el registro formal de qué se construyó, cómo se verificó y qué queda pendiente, y sirve tanto como bitácora de avance del proyecto como material de sustentación.

Todo `fase-N-*.md` debe seguir esta plantilla:

```markdown
# Fase N — {Nombre de la fase}

## 1. Objetivo de la fase
Qué se buscaba lograr, en 2-3 líneas, tal como está definido en el prompt maestro.

## 2. Alcance realizado
Lista concreta de lo que efectivamente se implementó (endpoints creados, componentes de
UI, servicios, modelos, migraciones, etc.), con rutas de archivo reales del proyecto.
Si algo del alcance original de la fase no se completó, debe indicarse aquí explícitamente
y no omitirse.

## 3. Decisiones técnicas relevantes
Cualquier decisión de diseño o implementación tomada durante la fase que no estaba
100% especificada en el prompt maestro (ej. una librería adicional usada, un ajuste al
esquema de base de datos, un cambio de contrato de API), junto con la razón de esa decisión.

## 4. Cómo se verificaron los criterios de aceptación
Para cada criterio de aceptación definido en el prompt maestro para esta fase, indicar
explícitamente cómo se comprobó (comando ejecutado, test corrido, captura de pantalla,
petición de ejemplo con su respuesta, etc.). Formato sugerido: tabla con columnas
"Criterio", "Método de verificación", "Resultado".

## 5. Pruebas realizadas
Tests automatizados agregados en esta fase (ruta del archivo de test + qué cubren) y,
si aplica, pruebas manuales relevantes (ej. flujo probado en el navegador).

## 6. Problemas encontrados y solución
Cualquier bloqueo, bug o comportamiento inesperado durante la fase, y cómo se resolvió.
Si algo quedó pendiente de resolver, debe quedar registrado aquí, no silenciado.

## 7. Estado final de la fase
Confirmación explícita de si la fase se considera CERRADA (todos los criterios cumplidos)
o PARCIAL (se avanzó a la siguiente fase con pendientes documentados y justificados).

## 8. Siguientes pasos
Qué habilita esta fase para la siguiente (ej. "el motor de Mahalanobis ya está testeado
y cacheado, listo para conectarse al flujo de formulario en la Fase 4").
```

Este archivo se genera **al cerrar la fase**, no al iniciarla, y debe reflejar el estado real del código en ese punto — no un plan a futuro (eso ya está cubierto por el prompt maestro). El conjunto de todos los `fase-N-*.md` al final del proyecto (Fase 9) debe poder leerse en orden como la historia completa de construcción del sistema.

## Fase 0 — Preparación del proyecto (andamiaje)

**Objetivo:** tener el esqueleto de ambos proyectos corriendo, sin lógica de negocio todavía.

- Crear repositorio con estructura monorepo o dos repos (`frontend/`, `backend/`).
- Backend: inicializar FastAPI, configurar `core/config.py` (variables de entorno), conexión a PostgreSQL con SQLAlchemy 2.0 async, estructura de carpetas (`api/`, `services/`, `models/`, `schemas/`, `data/`, `core/`, `tests/`).
- Frontend: inicializar Next.js 15 (App Router) + TypeScript + Tailwind + shadcn/ui, configurar tema claro/oscuro base, estructura de carpetas de rutas.
- Configurar linters/formatters (`ruff`/`black` en backend, `eslint`/`prettier` en frontend).
- Endpoint de salud (`GET /health`) y página de inicio placeholder para verificar que frontend y backend se comunican.
- Configurar CI básico (lint + test en cada push), aunque sea mínimo.

**Criterios de aceptación:**
- El backend levanta y responde `GET /health` con 200.
- El frontend levanta y hace un fetch exitoso a `GET /health`.
- Linters pasan sin errores en ambos proyectos.

**Documentación de cierre:** `docs/fases/fase-0-andamiaje.md`

---

## Fase 1 — Datos base y modelos (sin UI, sin cálculo aún)

**Objetivo:** tener toda la data del dominio cargada y accesible vía API, con los modelos de base de datos definidos.

- Crear `data/preguntas.json` (85 preguntas, 17 áreas) y `data/areas.json` (17 áreas con orden fijo) tal como se especifica en la sección "Banco de preguntas".
- Crear `data/carreras.csv` (o tabla `carreras`) con las 37 carreras × 17 áreas (el dataset `data_carreras` ya definido).
- Modelos SQLAlchemy: `Usuario`, `Carrera`, `Area`, `Pregunta`, `IntentoTest`, `RespuestaTest`.
- Migraciones (Alembic) para crear el esquema en PostgreSQL.
- Endpoints de solo lectura: `GET /preguntas`, `GET /areas`, `GET /carreras`, `GET /carrera/{id}`.
- Seed script que carga preguntas, áreas y carreras a la base de datos.
- **Validación de arranque:** chequeo automático de que las claves de `AREAS` coinciden exactamente con las columnas del dataset de carreras (ver sección "Implementación técnica").

**Criterios de aceptación:**
- Los 4 endpoints de lectura devuelven datos reales desde PostgreSQL, no mockeados.
- El seed corre de forma idempotente (se puede volver a ejecutar sin duplicar datos).
- Un test unitario confirma que `len(AREAS) == 17` y que coincide con las claves del dataset de carreras.

**Documentación de cierre:** `docs/fases/fase-1-datos-modelos.md`

---

## Fase 2 — Motor de recomendación (Mahalanobis) como servicio puro

**Objetivo:** tener el algoritmo de recomendación funcionando y testeado de forma aislada, sin depender todavía del flujo de test completo.

- Implementar `services/recomendacion_service.py`: `calcular_matriz_covarianza`, `calcular_recomendacion`, con regularización y pseudo-inversa como fallback (ver sección "Algoritmo de recomendación").
- Cachear `inv_cov_matrix` en memoria al iniciar el backend.
- Endpoint `POST /recomendacion` que recibe un `vector_usuario` de prueba (17 valores) y devuelve el Top 5.
- Tests unitarios (`pytest`) cubriendo los 4 casos descritos en "Requisitos no funcionales del cálculo": inversión sin error, longitud de distancias = 37, carrera con distancia mínima = top 1, caso de borde con vector promedio.

**Criterios de aceptación:**
- `POST /recomendacion` con un vector de prueba devuelve un Top 5 coherente (la carrera más cercana al vector de entrada aparece primero).
- Todos los tests de Mahalanobis pasan.
- El cálculo no se re-ejecuta desde cero en cada request (la matriz de covarianza inversa está cacheada).

**Documentación de cierre:** `docs/fases/fase-2-motor-mahalanobis.md`

---

## Fase 3 — Lógica Adaptativa de Preguntas (módulo aislado)

**Objetivo:** tener la lógica de recorte/extensión de preguntas por área funcionando y testeada, independiente de si se usa desde el formulario o el chatbot.

- Implementar `services/adaptive_flow_service.py` con la función `preguntas_a_formular` (ver sección dedicada).
- Tests unitarios cubriendo **exactamente** los 7 casos de la tabla de ejemplos de validación (`[1]`, `[3,5,4]`, `[5,1]`, etc.).
- Implementar `construir_vector_usuario` (promedio por área sobre las preguntas realmente formuladas).

**Criterios de aceptación:**
- Los 7 casos de la tabla de validación pasan como tests unitarios, sin excepciones.
- `construir_vector_usuario` devuelve un diccionario de 17 claves con valores en el rango [1.0, 5.0].

**Documentación de cierre:** `docs/fases/fase-3-logica-adaptativa.md`

---

## Fase 4 — Método 1: Test Tradicional (formulario) end-to-end

**Objetivo:** primer flujo completo usable por un usuario real, de principio a fin.

- Backend: endpoint `POST /test/tradicional` que recibe respuestas `{pregunta_id, respuesta}[]`, aplica la Lógica Adaptativa, calcula el vector y lo persiste (tabla `respuestas_test` + `intento_test`).
- Frontend: pantalla de formulario con barra de progreso por área, tarjeta de pregunta, selector Likert tipo *card*, navegación anterior/siguiente, autoguardado.
- Conectar el formulario al endpoint real (no mock).
- Pantalla de Resultados básica (sin gráficos avanzados todavía): Top 5 en tarjetas simples con `afinidad_pct`.

**Criterios de aceptación:**
- Un usuario puede completar el test tradicional de principio a fin y ver un Top 5 real, calculado con Mahalanobis sobre sus respuestas.
- El número de preguntas mostradas por área varía según las respuestas, verificable manualmente con los casos de la Fase 3.
- Los datos del intento quedan persistidos en PostgreSQL.

**Documentación de cierre:** `docs/fases/fase-4-test-tradicional.md`

---

## Fase 5 — Landing Page y navegación general

**Objetivo:** dar contexto y entrada profesional al sistema, ahora que el flujo principal ya funciona.

- Construir la Landing Page completa: Hero, "¿Cómo funciona?", "Métodos del Test", Beneficios, Footer (ver sección "Landing Page").
- Pantalla de selección de método (`/test`).
- Header/Navbar consistente en todas las pantallas, con toggle de modo claro/oscuro persistente.
- Conectar los botones de la landing al flujo real del formulario (Fase 4).

**Criterios de aceptación:**
- Desde la landing, un usuario puede llegar al formulario y completar el test sin pasos rotos.
- El modo oscuro/claro persiste entre recargas.
- La landing es responsive (verificado en al menos un breakpoint mobile y uno desktop).

**Documentación de cierre:** `docs/fases/fase-5-landing-navegacion.md`

---

## Fase 6 — Método 2: Chatbot basado en reglas (núcleo conversacional)

**Objetivo:** segundo método de test funcionando, produciendo el mismo resultado que el formulario ante las mismas respuestas.

- Backend: `services/chatbot_service.py` con la máquina de estados finita (bienvenida, pregunta actual, cambio de área, confirmación final).
- Endpoint `POST /test/chatbot` reutilizando el mismo servicio de cálculo que `POST /test/tradicional`.
- Persistencia de sesión en backend (para poder reanudar tras refresh).
- Frontend: interfaz tipo chat (burbujas, indicador de "escribiendo...", chips numerados 1–5).
- Validación estricta de entrada Likert y reformulación ante respuesta inválida.
- Frases de transición rotativas y mensajes de motivación periódicos.

**Criterios de aceptación:**
- Ante la misma secuencia de respuestas, el chatbot produce **el mismo vector de usuario y el mismo Top 5** que el formulario tradicional (test de equivalencia, ver Fase 9).
- Si se refresca la página a mitad del chat, la conversación se puede reanudar desde el mismo punto.
- Las respuestas inválidas no avanzan el estado del test.

**Documentación de cierre:** `docs/fases/fase-6-chatbot-nucleo.md`

---

## Fase 7 — Funcionalidades avanzadas del chatbot (preguntas abiertas y post-resultado)

**Objetivo:** enriquecer el chatbot con las funcionalidades del catálogo de "Funcionalidades Avanzadas del Chatbot", sin tocar el núcleo ya probado en la Fase 6.

- Crear `data/intents.json` con el banco de FAQs (duración del test, privacidad, diferencia entre métodos, etc.).
- Implementar el matching de intención por reglas (`buscar_intent_faq`) y su integración en el router de mensajes (`procesar_mensaje_usuario`).
- Comandos de navegación dentro del chat: repetir, anterior, ver progreso, pausar.
- Módulo post-resultado: "explícame el resultado" y comparación conversacional de carreras (ver "Preguntas de seguimiento tras el resultado").
- Límite de reintentos con oferta de cambio a formulario tradicional.
- Registro de analítica básica: intents disparados, respuestas inválidas, abandono por área.

**Criterios de aceptación:**
- El chatbot responde correctamente a al menos 5 preguntas frecuentes distintas sin salirse del flujo del test.
- Tras mostrar un resultado, el usuario puede preguntar "¿por qué esa carrera?" y recibir una respuesta basada en los datos reales de su Top 5.
- Ninguna respuesta del chatbot en esta fase proviene de generación de texto libre; todas son trazables a una plantilla + datos.

**Documentación de cierre:** `docs/fases/fase-7-chatbot-avanzado.md`

---

## Fase 8 — Resultados avanzados y páginas de carrera

**Objetivo:** llevar la experiencia de resultados al nivel final descrito en el diseño UI/UX.

- Gráfico radar (17 ejes) comparando `vector_usuario` vs. perfil de la carrera recomendada.
- Gráfico de barras del Top 5.
- Tarjetas completas con fortalezas, áreas por mejorar y explicación por reglas.
- Página de detalle de carrera (`/carrera/{id}`) con su propio radar y comparación opcional con el perfil del usuario.
- Botón "Descargar PDF" del resultado.
- Comparador de carreras (hasta 3 del Top 5) lado a lado.

**Criterios de aceptación:**
- El radar y las barras reflejan datos reales del backend, no valores de ejemplo.
- El PDF descargado contiene el Top 5 y el detalle de la carrera recomendada.
- El comparador permite seleccionar y visualizar al menos 2 carreras simultáneamente.

**Documentación de cierre:** `docs/fases/fase-8-resultados-avanzados.md`

---

## Fase 9 — Autenticación, historial y pulido final

**Objetivo:** cerrar funcionalidades que dependen de sesión de usuario y dejar el sistema listo para entrega/producción.

- Autenticación JWT (registro, login, refresh token).
- Asociar intentos de test a un usuario autenticado; flujo de invitado sigue disponible sin historial.
- Pantalla "Mis resultados anteriores" con línea de tiempo de intentos.
- Test de equivalencia formulario vs. chatbot: mismo set de respuestas simuladas en ambos flujos debe producir el mismo `vector_usuario` y el mismo Top 5 (test automatizado, no solo manual).
- Revisión de accesibilidad (WCAG AA): contraste, navegación por teclado, `aria-live` en el chat.
- Revisión de estados de carga/error/vacío en todas las pantallas (skeletons, mensajes de reintento).
- Optimización de performance (lazy loading de gráficos, memoización donde aplique) y revisión de responsive en dispositivos reales.

**Criterios de aceptación:**
- Un usuario autenticado puede ver el historial de sus intentos anteriores.
- El test de equivalencia formulario/chatbot pasa para al menos 10 secuencias de respuestas distintas.
- Auditoría de accesibilidad no reporta errores críticos (puede usarse Lighthouse o axe-core como referencia).
- El sistema está desplegado (o listo para desplegar) en un entorno accesible para revisión.

**Documentación de cierre:** `docs/fases/fase-9-auth-historial-pulido.md`

Además, al cerrar la Fase 9 se debe generar un `docs/fases/README.md` que enlace a los 10 archivos `fase-N-*.md` en orden, a modo de índice general del proceso de construcción del proyecto — este README es el punto de entrada para que cualquier persona (docente, jurado, nuevo integrante del equipo) entienda cómo se construyó el sistema de principio a fin.

---

## Resumen de dependencias entre fases

```
Fase 0 (andamiaje)
   ↓
Fase 1 (datos y modelos) ──► Fase 2 (Mahalanobis) ──► Fase 3 (lógica adaptativa)
                                                              ↓
                                                        Fase 4 (test tradicional E2E)
                                                              ↓
                                                        Fase 5 (landing y navegación)
                                                              ↓
                                                        Fase 6 (chatbot: núcleo)
                                                              ↓
                                                        Fase 7 (chatbot: funcionalidades avanzadas)
                                                              ↓
                                                        Fase 8 (resultados avanzados)
                                                              ↓
                                                        Fase 9 (auth, historial, pulido)
```

Las Fases 2 y 3 pueden desarrollarse en paralelo entre sí (ambas dependen solo de la Fase 1), pero la Fase 4 requiere que ambas estén cerradas, ya que el formulario usa tanto el motor de Mahalanobis como la lógica adaptativa.

---



El sistema permitirá que un estudiante descubra qué carrera profesional de la Universidad Nacional del Altiplano se adapta mejor a su perfil de intereses y habilidades, usando un modelo estadístico multivariado (Mahalanobis) en vez de una simple similitud euclidiana o de coseno.

Debe ofrecer **dos formas diferentes de realizar el test vocacional**, que comparten el mismo banco de preguntas, el mismo cálculo de vector de usuario y el mismo motor de recomendación:

1. Test tradicional mediante formulario (pregunta por pregunta, escala Likert).
2. Test mediante un chatbot basado en reglas (conversación guiada, mismo banco de hasta 85 preguntas).

Ambos métodos usan además la misma **Lógica Adaptativa de Preguntas por Área**: no siempre se formulan las 5 preguntas de un área, el número real depende de las respuestas del propio usuario (ver sección dedicada más abajo).

**Regla de oro: ambos métodos deben producir matemáticamente el mismo vector de usuario ante las mismas respuestas, y por lo tanto el mismo resultado final.** Esto se logra centralizando el cálculo del vector y el algoritmo de Mahalanobis en un único servicio de backend (`services/recomendacion_service.py`), nunca duplicando lógica entre el flujo de formulario y el flujo de chatbot.

---

# Landing Page

Diseñar una Landing Page moderna similar a plataformas como Coursera, Notion o OpenAI.

## Hero
- Título: "Descubre la carrera profesional ideal para ti"
- Subtítulo: "Realiza un test vocacional inteligente basado en tus intereses, habilidades y competencias."
- Botones: **Realizar Test** · **Conversar con el Chatbot**
- Imagen ilustrativa relacionada con estudiantes y orientación vocacional.

## Sección ¿Cómo funciona?
Tres tarjetas:
1. Responder el test (hasta 85 preguntas repartidas en 17 áreas; el sistema recorta preguntas automáticamente según tus respuestas).
2. Analizar intereses mediante la Distancia de Mahalanobis (comparación estadística contra el perfil de 37 carreras).
3. Obtener las carreras recomendadas (Top 5 con % de afinidad).

## Sección Métodos del Test
Dos tarjetas grandes:

**Opción 1 — Test Tradicional**
Descripción: Responder un cuestionario con escala Likert (hasta 85 preguntas, una por una, con recorte inteligente por área).
Botón: Comenzar Test

**Opción 2 — Test con Chatbot**
Descripción: Responder el mismo banco de preguntas conversando con un chatbot basado en reglas, que también recorta preguntas según tus intereses.
Botón: Iniciar Chat

## Beneficios
- Resultados personalizados
- Basado en intereses
- Recomendación objetiva y estadísticamente fundamentada (Mahalanobis, no solo distancia euclidiana)
- Comparación con perfiles profesionales reales de 37 carreras de la UNA Puno
- Explicación detallada del resultado (fortalezas, áreas por mejorar)

## Footer
Información institucional (UNA Puno).

---

# Método 1 — Test Tradicional

Utilizar el **banco de hasta 85 preguntas** (sección "Banco de 85 preguntas" más abajo). Cada pregunta pertenece a una de las **17 áreas** definidas. **El número real de preguntas mostradas por área es variable y se decide con la Lógica Adaptativa de Preguntas descrita en la sección siguiente** — no siempre se muestran las 5 preguntas de un área.

- Las preguntas se muestran una por una, en el orden de `id` dentro de cada área (la primera pregunta de cada área es siempre la de `id` más bajo de esa área).
- Escala Likert: 1 = No me gusta nada · 2 = Me gusta poco · 3 = Me gusta moderadamente · 4 = Me gusta bastante · 5 = Me gusta mucho.
- La interfaz debe mostrar: barra de progreso (estimada/dinámica, ver más abajo), número de pregunta dentro del área actual (ej. "Pregunta 2 de máx. 5 en Matemática"), área evaluada, tiempo estimado restante, botón anterior, botón siguiente.
- Debe permitir retroceder y modificar una respuesta ya dada. **Si el usuario modifica la respuesta a la primera pregunta de un área que ya había sido "recortada" o "extendida" por la lógica adaptativa, el frontend debe recalcular en vivo cuántas preguntas de esa área corresponde mostrar, y descartar/re-solicitar las respuestas de preguntas que ya no correspondan.**
- Como el total de preguntas ya no es fijo en 85 (puede ser menor), la barra de progreso debe mostrarse como progreso **por área** ("Área 6 de 17") combinado con una estimación de porcentaje global, no como una fracción fija "X/85".

## Cálculo del vector de usuario (idéntico en ambos métodos)

Al finalizar, para cada una de las 17 áreas, calcular el **promedio aritmético únicamente de las preguntas que efectivamente fueron formuladas y respondidas** en esa área (pueden ser 1, 2, 3, 4 o 5 preguntas, según la Lógica Adaptativa):

```
vector_usuario[area] = promedio( respuestas de las preguntas realmente formuladas en esa área )
```

Resultado: un vector de 17 dimensiones, cada componente en el rango [1.0, 5.0]. Ejemplo:

```
{
  "desarrollo_personal": 4.2,
  "matematica": 4.8,
  "comunicacion": 3.9,
  ...
}
```

Ese vector, junto con el detalle de qué preguntas fueron efectivamente formuladas y respondidas (ya que el número varía por usuario), se envía al backend (`POST /test/tradicional`) y se persiste asociado al intento de test (para trazabilidad e histórico).

---

# Método 2 — Chatbot basado en reglas

Implementar un chatbot conversacional **completamente basado en reglas** (máquina de estados finita determinista). **No utilizar IA generativa ni llamadas a modelos de lenguaje externos** para decidir el flujo o generar preguntas: el guion, las transiciones y la validación son 100% código determinista.

El chatbot debe utilizar el **mismo banco de hasta 85 preguntas** que el test tradicional, presentadas como diálogo natural, no como formulario. **El número de preguntas que el chatbot realmente formula por cada área también se decide con la Lógica Adaptativa de Preguntas** (sección siguiente) — el chatbot debe aplicar la misma función de decisión que el formulario tradicional, pregunta por pregunta, en tiempo real dentro de la conversación.

## Ejemplo de flujo (con corte adaptativo dentro de una misma área)

```
Chatbot: Hola. Soy tu orientador vocacional. Durante unos minutos conversaré
         contigo para descubrir cuáles son tus intereses. ¿Comenzamos?
Usuario: Sí.
Chatbot: Perfecto. Primera pregunta de Matemática. ¿Qué tanto disfrutas
         resolver problemas matemáticos? Responde usando un número del 1
         al 5 (1 = No me gusta, 5 = Me encanta).
Usuario: 5
Chatbot: Excelente. Seguimos en Matemática. ¿Te consideras hábil para el
         cálculo mental y el razonamiento numérico?
Usuario: 1
Chatbot: Gracias por tu sinceridad. Con eso ya tengo suficiente sobre
         Matemática, pasemos a la siguiente área: Ciencia y Tecnología.
         ¿Te apasiona la investigación científica y descubrir cómo
         funcionan las cosas?
Usuario: 3
Chatbot: Muy bien. Otra de Ciencia y Tecnología. ¿Disfrutas experimentar
         con equipos, herramientas o software para crear soluciones?
Usuario: 3
Chatbot: Perfecto, una más de esta área y avanzamos. ¿Te interesa la
         inteligencia artificial, la robótica o la programación?
Usuario: 3
Chatbot: Gracias. Con eso cerramos Ciencia y Tecnología y seguimos con la
         siguiente área...
```

En el ejemplo: en Matemática, la primera respuesta fue 5 (lo que en principio habilitaba hasta 5 preguntas), pero la segunda respuesta fue 1 (menor a 3), así que el chatbot corta el área en 2 preguntas. En Ciencia y Tecnología, la primera respuesta fue 3 (habilita hasta 3 preguntas) y las siguientes se mantuvieron en 3, así que el chatbot pregunta exactamente 3 veces y avanza — nunca extiende más allá de lo que habilitó la primera respuesta del área, aunque una respuesta posterior sea más alta.

## Reglas de validación e inteligencia conversacional

El chatbot debe:
- Validar que el usuario responda **únicamente** con un número entero del 1 al 5.
- Si la respuesta es inválida (texto, número fuera de rango, vacío), volver a formular la pregunta con un mensaje de corrección, sin avanzar el índice.
- Aplicar la Lógica Adaptativa de Preguntas después de **cada** respuesta dentro de un área, para decidir si formula la siguiente pregunta del área, salta a la siguiente área, o finaliza el test.
- Mantener en estado de sesión (backend, no solo frontend) el área actual, la pregunta actual dentro del área, y las respuestas ya registradas, para poder reanudar si se refresca la página.
- Mostrar el progreso por área ("Vamos por el área 6 de 17"), no como fracción fija sobre 85, ya que el total real de preguntas varía según las respuestas del usuario.
- Confirmar cada respuesta registrada con una frase de transición, y anunciar explícitamente cuando se pasa de área (ver ejemplo arriba), para que el usuario entienda por qué a veces hay menos preguntas en una misma área.
- Variar ligeramente las frases de transición eligiendo aleatoriamente (pero de forma determinista/basada en reglas, ej. una lista rotativa) entre: "Excelente.", "Perfecto.", "Muy bien.", "Continuemos.", "Gracias por responder.", "Pasemos a la siguiente pregunta."
- Dar mensajes de motivación cada cierto número de áreas completadas (ej. cada 5 áreas).
- Finalizar con un mensaje de agradecimiento y transición automática a la pantalla de resultados.
- **No responder preguntas fuera del flujo del test** (si el usuario escribe algo no relacionado, redirigir amablemente de vuelta a la pregunta pendiente).

Al finalizar, calcular el vector de usuario con la **misma fórmula** de promedio por área (sobre las preguntas realmente formuladas) descrita en el Método 1, y enviarlo a `POST /test/chatbot`, que internamente reutiliza el mismo servicio de cálculo — incluida la misma función de Lógica Adaptativa de Preguntas — que `POST /test/tradicional`.

---

# Funcionalidades Avanzadas del Chatbot Basado en Reglas

Esta sección amplía el Método 2 con un catálogo completo de funcionalidades adicionales, todas implementables **sin IA generativa ni LLMs externos** — se basan en máquinas de estado, matching de patrones (keywords/regex) y plantillas de texto con variables, nunca en generación libre de texto. El objetivo es que el chatbot sea más robusto, natural y útil sin romper la garantía central del sistema: **determinismo total y trazabilidad completa**.

## Principio rector: preguntas abiertas SÍ, generación de texto NO

El chatbot puede aceptar y responder preguntas abiertas del usuario (ej. "¿cuánto dura el test?", "¿mis datos son privados?", "¿por qué me recomendaste esa carrera?"), siempre que la respuesta provenga de un **banco de intenciones predefinido** (`data/intents.json`) y no de un modelo de lenguaje generando texto en tiempo real. La diferencia clave:

- ✅ **Permitido:** detectar la intención del mensaje por palabras clave/regex y devolver una respuesta de plantilla ya escrita, opcionalmente rellenada con variables (nombre del usuario, área actual, resultado ya calculado).
- ❌ **No permitido:** conectar un LLM (interno o externo) para que "entienda" y redacte una respuesta nueva ante cualquier mensaje.

Cuando el mensaje del usuario no coincide con ninguna intención conocida, el chatbot usa un **fallback fijo**, nunca inventa una respuesta.

## Catálogo de funcionalidades del chatbot

### 1. Núcleo del flujo conversacional
- Máquina de estados finita: cada estado representa un punto del flujo (bienvenida, pregunta actual, cambio de área, confirmación final, post-resultado).
- Validación de entrada estricta: solo acepta los formatos esperados por el estado actual (número 1–5, "sí"/"no", comandos reconocidos).
- Reformulación ante respuesta inválida: repite la pregunta con un mensaje de corrección, sin avanzar el estado.
- Persistencia de sesión en backend: guarda área actual, pregunta actual y respuestas ya registradas, para poder reanudar tras un refresh o cierre de pestaña.
- Aplicación en tiempo real de la Lógica Adaptativa de Preguntas (sección siguiente) dentro de la conversación.

### 2. Reconocimiento de intención por reglas (sin LLM)
- Matching por palabras clave/regex para detectar intenciones fuera del flujo Likert (preguntas abiertas tipo FAQ).
- Tolerancia a errores de tipeo con distancia de edición (Levenshtein) o normalización de texto (minúsculas, sin tildes, sin puntuación).
- Sinónimos y variantes mapeadas a la misma intención (ej. "cuánto dura", "cuánto tiempo toma", "cuántos minutos son").
- Reconocimiento de números en palabras ("cinco" → 5, "tres" → 3) además de dígitos.
- Detección de comandos especiales: "ayuda", "reiniciar", "saltar pregunta", "repetir", "salir".

### 3. Respuestas predefinidas y contenido dinámico
- Banco de FAQs por reglas (duración del test, privacidad, diferencia entre métodos, cómo se calcula la recomendación).
- Plantillas de texto con variables (ej. "Vamos por el área {n} de 17, ¡vas muy bien!") rellenadas dinámicamente sin generación libre.
- Rotación de frases de transición para no sonar repetitivo ("Perfecto.", "Muy bien.", "Continuemos.") elegidas de una lista fija, no generadas.
- Mensajes de motivación periódicos cada cierto número de áreas completadas.
- Mensajes contextuales de reanudación ("Continuemos donde lo dejamos, estábamos en el área de Matemática").

### 4. Navegación y control del usuario dentro del chat
- Comando "repetir pregunta": vuelve a mostrar la pregunta actual tal cual.
- Comando "anterior" / "corregir última respuesta": retrocede una pregunta dentro del área actual (con las mismas reglas de recorte/extensión que el formulario).
- Comando "saltar área" (opcional): marca el área como no respondida o con valor neutro, documentando el impacto en el vector.
- Comando "ver mi progreso": resumen de áreas completadas y pendientes.
- Comando "pausar" / "continuar después": cierra la sesión de forma explícita conservando el estado.

### 5. Personalización basada en reglas (no en generación)
- Ramificación condicional simple: si el usuario respondió muy bajo en varias áreas seguidas, mostrar un mensaje de aliento distinto al estándar (regla condicional, no generación).
- Ajuste de tono por reglas fijas: modo "formal" vs. "cercano" seleccionable al inicio, cada uno con su propio set de plantillas de texto.
- Recordar el nombre del usuario (si lo pide al inicio) e insertarlo en las plantillas ("Gracias, {nombre}, sigamos con...").

### 6. Accesibilidad e inclusión
- Compatibilidad con lectores de pantalla (`aria-live`, `role="log"`).
- Alternativa 100% por teclado: chips numerados también navegables y confirmables sin mouse.
- Modo texto simplificado: respuestas más cortas para conexiones lentas o pantallas pequeñas.

### 7. Manejo de errores y casos límite
- Fallback genérico: mensaje claro cuando ninguna regla coincide, sin fingir comprensión.
- Límite de reintentos: tras N respuestas inválidas seguidas, ofrecer cambiar al formulario tradicional.
- Detección de inactividad: mensaje de "¿sigues ahí?" tras cierto tiempo sin respuesta, con opción de continuar o guardar y salir.
- Manejo de mensajes vacíos o solo emojis: tratarlos como entrada inválida con mensaje de corrección específico.

### 8. Analítica y trazabilidad (basado en reglas, no en IA)
- Registro de qué intents se dispararon (útil para detectar preguntas frecuentes y mejorar el banco de FAQs).
- Registro de respuestas inválidas para detectar preguntas mal formuladas o UX confusa.
- Métricas de abandono por área: en qué área se cierran más sesiones sin terminar.

### 9. Cierre y transición
- Resumen final antes de calcular resultados ("Respondiste X de 85 preguntas posibles en Y áreas, ¿confirmas para ver tu recomendación?").
- Confirmación explícita antes de enviar a `POST /test/chatbot`, evitando envíos accidentales.
- Mensaje de despedida personalizado con transición automática a la pantalla de resultados.

### 10. Extensiones post-resultado (más ambiciosas, siguen siendo por reglas)
- Modo "explícame el resultado": el usuario pregunta "¿por qué me recomendaste X?" y el bot responde con una plantilla que usa las fortalezas/áreas por mejorar ya calculadas (no genera texto nuevo, solo arma la plantilla con datos existentes).
- Comparación conversacional: "compara Ingeniería de Sistemas con Ingeniería Civil" — dispara la vista de comparador ya definida, con una respuesta de texto armada por plantilla usando los datos de ambas carreras.
- Árbol de decisión para recomendaciones rápidas tipo "quiz corto" antes del test completo, como gancho de landing.

---

# Implementación técnica: del chatbot al resultado de Mahalanobis

Esta sección detalla, con código de referencia, cómo el backend conecta las respuestas recolectadas por el chatbot con el cálculo final de recomendación contra la matriz de 37 carreras × 17 áreas.

## 1. Preparación de la matriz de carreras

El dataset de perfiles de carrera (`data_carreras`) se recibe en formato "columnas" (un array por área, con 37 valores, uno por carrera) y debe transformarse a una matriz numpy de 37×17 para el cálculo. **El orden de `AREAS` debe coincidir exactamente, nombre por nombre, con las claves de `data_carreras`** y con el orden usado para construir `vector_usuario` en el chatbot y en el formulario — cualquier desalineación produce un vector de usuario comparado contra la columna equivocada.

```python
import numpy as np

AREAS = [
    'desarrollo_personal', 'ciencias_sociales', 'educacion_fisica', 'arte_cultura',
    'comunicacion', 'castellano_segunda', 'ingles_extranjero', 'matematica',
    'ciencia_tecnologia', 'educacion_trabajo', 'pensamiento_analitico',
    'alfabetizacion_digital', 'adaptabilidad_resiliencia', 'comunicacion_efectiva',
    'inteligencia_emocional', 'curiosidad_aprendizaje', 'liderazgo_equipo'
]

carreras_nombres = data_carreras['carrera']  # lista de 37 nombres

# Matriz 37 (carreras) x 17 (áreas)
matriz_carreras = np.array([
    data_carreras[area] for area in AREAS
]).T

assert matriz_carreras.shape == (len(carreras_nombres), len(AREAS))
```

> **Nota de validación obligatoria:** al cargar `data_carreras` en el backend (idealmente en `data/carreras.csv` o una tabla, no hardcodeado en código), debe existir un chequeo de arranque que compare las claves de `AREAS` contra las claves reales del dataset y falle de forma explícita (no silenciosa) si no coinciden en cantidad o nombre.

## 2. Servicio de recomendación (Mahalanobis)

```python
from scipy.spatial.distance import mahalanobis

def calcular_matriz_covarianza(matriz_carreras: np.ndarray) -> np.ndarray:
    cov = np.cov(matriz_carreras, rowvar=False)
    try:
        inv_cov = np.linalg.inv(cov)
    except np.linalg.LinAlgError:
        cov_reg = cov + np.eye(cov.shape[0]) * 1e-6
        try:
            inv_cov = np.linalg.inv(cov_reg)
        except np.linalg.LinAlgError:
            inv_cov = np.linalg.pinv(cov_reg)  # fallback robusto
    return inv_cov

# Se calcula UNA VEZ al iniciar el backend y se cachea en memoria (no recalcular por request)
INV_COV = calcular_matriz_covarianza(matriz_carreras)

def calcular_recomendacion(vector_usuario: dict[str, float]) -> list[dict]:
    x_usuario = np.array([vector_usuario[area] for area in AREAS])

    distancias = np.array([
        mahalanobis(x_usuario, matriz_carreras[i], INV_COV)
        for i in range(len(carreras_nombres))
    ])

    d_min, d_max = distancias.min(), distancias.max()
    if d_max == d_min:
        afinidad = [100.0] * len(distancias)
    else:
        afinidad = [round(100 * (1 - (d - d_min) / (d_max - d_min)), 1) for d in distancias]

    resultados = []
    for i, nombre_carrera in enumerate(carreras_nombres):
        mu_c = matriz_carreras[i]
        fortalezas = [
            AREAS[j] for j in range(len(AREAS))
            if x_usuario[j] >= mu_c[j] and x_usuario[j] >= 4
        ]
        areas_por_mejorar = sorted(
            [AREAS[j] for j in range(len(AREAS)) if x_usuario[j] < mu_c[j]],
            key=lambda a: mu_c[AREAS.index(a)] - x_usuario[AREAS.index(a)],
            reverse=True
        )[:3]

        resultados.append({
            "carrera": nombre_carrera,
            "distancia": round(float(distancias[i]), 3),
            "afinidad_pct": afinidad[i],
            "fortalezas": fortalezas,
            "areas_por_mejorar": areas_por_mejorar,
        })

    resultados.sort(key=lambda r: r["distancia"])
    return resultados[:5]
```

## 3. Construcción del vector de usuario desde las respuestas del chatbot

```python
def construir_vector_usuario(respuestas_por_area: dict[str, list[int]]) -> dict[str, float]:
    """
    respuestas_por_area: { "matematica": [4, 5, 3], "comunicacion": [5], ... }
    Solo contiene las preguntas realmente formuladas por área (1 a 5 valores),
    según la Lógica Adaptativa de Preguntas.
    """
    return {
        area: round(sum(respuestas) / len(respuestas), 2)
        for area, respuestas in respuestas_por_area.items()
    }
```

## 4. Cierre del test dentro del chatbot (aplica funcionalidades #3 y #9 del catálogo)

```python
def finalizar_test_chatbot(sesion_chat):
    # Resumen y confirmación antes de calcular (funcionalidad #9)
    total_respondidas = sum(len(r) for r in sesion_chat.respuestas_por_area.values())
    enviar_mensaje(
        f"Respondiste {total_respondidas} preguntas en "
        f"{len(sesion_chat.respuestas_por_area)} áreas. "
        f"¿Confirmas para ver tu recomendación? (sí/no)"
    )
    # El estado pasa a "esperando_confirmacion_final"; el cálculo solo ocurre tras "sí"

    vector_usuario = construir_vector_usuario(sesion_chat.respuestas_por_area)
    top5 = calcular_recomendacion(vector_usuario)

    # Se guarda en la sesión para habilitar preguntas de seguimiento (funcionalidad #10)
    sesion_chat.ultimo_resultado = top5
    sesion_chat.ultimo_vector_usuario = vector_usuario
    sesion_chat.estado = "post_resultado"

    carrera_top1 = top5[0]
    enviar_mensaje(
        f"¡Listo! Según tus respuestas, la carrera que mejor se alinea contigo es "
        f"{carrera_top1['carrera']} con un {carrera_top1['afinidad_pct']}% de afinidad. "
        f"Tus fortalezas destacadas fueron: {', '.join(carrera_top1['fortalezas'][:3])}. "
        f"Te muestro el detalle completo con el Top 5 a continuación."
    )

    # Persistencia vía POST /test/chatbot y transición a la pantalla de resultados
    return top5
```

## 5. Preguntas de seguimiento tras el resultado (funcionalidad #10, sin LLM)

```python
import re

INTENTS_POST_RESULTADO = {
    "por_que_carrera": [r"por qu[eé]", r"raz[oó]n", r"explica"],
    "comparar": [r"compara", r"diferencia entre", r"\bvs\b"],
}

def responder_pregunta_seguimiento(texto_usuario: str, sesion_chat) -> str:
    texto_norm = texto_usuario.lower().strip()

    if any(re.search(p, texto_norm) for p in INTENTS_POST_RESULTADO["por_que_carrera"]):
        c = sesion_chat.ultimo_resultado[0]
        return (
            f"Te recomendé {c['carrera']} porque tu perfil mostró alta afinidad en "
            f"{', '.join(c['fortalezas'][:3])}, áreas clave para esa carrera. "
            f"Tu distancia estadística fue de {c['distancia']}, la más baja entre las 37 carreras evaluadas."
        )

    if any(re.search(p, texto_norm) for p in INTENTS_POST_RESULTADO["comparar"]):
        nombres_top5 = [r["carrera"].lower() for r in sesion_chat.ultimo_resultado]
        mencionadas = [n for n in nombres_top5 if n in texto_norm]
        if len(mencionadas) >= 2:
            return armar_comparacion(mencionadas[:2], sesion_chat.ultimo_resultado)
        return "Dime cuáles dos carreras de tu Top 5 quieres comparar, por ejemplo: 'compara Ingeniería de Sistemas con Ingeniería Civil'."

    # Fallback fijo (funcionalidad #7) — nunca se inventa una respuesta
    return (
        "No logré identificar tu pregunta. Puedo explicarte por qué te recomendé una carrera, "
        "o comparar dos carreras de tu Top 5. ¿Qué te gustaría saber?"
    )


def armar_comparacion(nombres: list[str], top5: list[dict]) -> str:
    c1 = next(r for r in top5 if r["carrera"].lower() == nombres[0])
    c2 = next(r for r in top5 if r["carrera"].lower() == nombres[1])
    return (
        f"{c1['carrera']}: {c1['afinidad_pct']}% de afinidad, fortalezas en {', '.join(c1['fortalezas'][:2])}.\n"
        f"{c2['carrera']}: {c2['afinidad_pct']}% de afinidad, fortalezas en {', '.join(c2['fortalezas'][:2])}.\n"
        f"La diferencia de afinidad entre ambas es de {abs(c1['afinidad_pct'] - c2['afinidad_pct'])} puntos porcentuales."
    )
```

## 6. Router central de mensajes (orquesta Likert, FAQs y comandos)

Punto de entrada único que decide qué hacer con cada mensaje del usuario según el estado de la sesión — conecta el reconocimiento de intención (funcionalidad #2) con el flujo del test:

```python
def procesar_mensaje_usuario(sesion_chat, texto_usuario: str) -> str:
    if sesion_chat.estado == "esperando_respuesta_likert":
        valor = interpretar_likert(texto_usuario)  # acepta dígitos y números en palabras
        if valor is not None:
            return registrar_respuesta_test(sesion_chat, valor)

        respuesta_faq = buscar_intent_faq(texto_usuario)  # data/intents.json
        if respuesta_faq:
            enviar_mensaje(respuesta_faq)
            return repetir_pregunta_actual(sesion_chat)  # no avanza el índice del test

        sesion_chat.intentos_invalidos += 1
        if sesion_chat.intentos_invalidos >= 3:
            return "Parece que el chat no es lo tuyo ahora mismo — ¿prefieres cambiar al formulario tradicional?"
        return repetir_pregunta_actual(sesion_chat, con_correccion=True)

    elif sesion_chat.estado == "esperando_confirmacion_final":
        if texto_usuario.lower().strip() in ("si", "sí", "yes", "ok"):
            return finalizar_test_chatbot(sesion_chat)
        return "Sin problema, puedes revisar tus respuestas antes de continuar."

    elif sesion_chat.estado == "post_resultado":
        return responder_pregunta_seguimiento(texto_usuario, sesion_chat)
```

## 7. Requisitos no funcionales de esta implementación

- Todo el código de esta sección vive en `services/chatbot_service.py` y `services/recomendacion_service.py`; los routers de FastAPI solo orquestan, nunca calculan directamente (consistente con la sección "Algoritmo de recomendación").
- El banco de intenciones (`data/intents.json`) es un archivo de datos versionado, no código hardcodeado, para que pueda crecer con analítica real (funcionalidad #8) sin tocar lógica de negocio.
- Debe existir un test unitario que valide que `AREAS` coincide exactamente con las claves de `data_carreras`/`carreras.csv` al arrancar el backend, para prevenir desalineación silenciosa entre el vector de usuario y la matriz de carreras.
- Todas las respuestas de seguimiento post-resultado deben poder trazarse a una plantilla y unos datos de entrada específicos (carrera, distancia, fortalezas) — si una respuesta no puede explicarse señalando la plantilla y los datos que la generaron, no cumple con el principio de "basado en reglas".

---

# Lógica Adaptativa de Preguntas por Área (Cuestionario Inteligente)

Esta lógica es **obligatoria y compartida** entre el Método 1 (formulario) y el Método 2 (chatbot); debe vivir en un único módulo de backend (`services/adaptive_flow_service.py`) para garantizar que ambos métodos generen exactamente el mismo comportamiento ante las mismas respuestas.

## Idea general

No siempre se formulan las 5 preguntas de un área. **La respuesta a la primera pregunta de cada área "presupuesta" cuántas preguntas de esa área se van a formular como máximo**, y las respuestas siguientes pueden **recortar** ese presupuesto (si decae el interés), pero **nunca lo extienden** más allá de lo que habilitó la primera respuesta.

- Si el usuario responde **1** a la primera pregunta de un área → no le interesa nada esa área → **no se muestran más preguntas de esa área**, se pasa directamente a la siguiente área.
- Si el usuario responde **3** a la primera pregunta → se formulan **hasta 3 preguntas** de esa área (la primera más 2 adicionales), salvo que una respuesta posterior sea menor a 3, en cuyo caso se corta antes.
- Si el usuario responde **5** a la primera pregunta → se habilitan **hasta 5 preguntas**, pero si en cualquier punto posterior responde algo **menor a 3**, el área se corta ahí mismo, sin llegar a la quinta pregunta.
- Si una respuesta posterior es **mayor** al presupuesto inicial (ej. primera respuesta = 3, segunda respuesta = 5), **no se extiende** el número de preguntas: se mantiene el tope definido por la primera respuesta del área (en este ejemplo, 3 preguntas en total, ni una más).

## Algoritmo determinista (pseudocódigo, aplica igual en formulario y chatbot)

```python
def preguntas_a_formular(preguntas_area: list[Pregunta], respuestas_callback) -> list[int]:
    """
    preguntas_area: las hasta 5 preguntas de un área, ordenadas por id ascendente.
    respuestas_callback: función que formula la siguiente pregunta y devuelve la
                          respuesta Likert (1-5) del usuario (form o chatbot).
    Retorna la lista de respuestas efectivamente registradas para el área.
    """
    respuestas = []

    # 1) Siempre se formula la primera pregunta del área.
    r1 = respuestas_callback(preguntas_area[0])
    respuestas.append(r1)

    # 2) La primera respuesta define el "presupuesto" máximo de preguntas del área.
    limite_area = r1  # r1 está en el rango 1-5, igual que el número de preguntas del área

    # 3) Si el presupuesto es 1 (no le gusta nada), no se formulan más preguntas de esta área.
    if limite_area <= 1:
        return respuestas

    # 4) Formular preguntas adicionales solo hasta el límite definido por r1,
    #    pero cortar antes si alguna respuesta posterior es menor a 3.
    for i in range(1, min(limite_area, len(preguntas_area))):
        r_i = respuestas_callback(preguntas_area[i])
        respuestas.append(r_i)
        if r_i < 3:
            # Interés decayó: se recorta el área aquí, sin llegar al presupuesto original.
            break
        # Si r_i >= 3 (igual o mayor), se continúa, pero jamás más allá de `limite_area`
        # preguntas en total, aunque r_i sea mayor que r1.

    return respuestas
```

## Ejemplos de validación (deben pasar como tests unitarios)

| Respuestas formuladas en orden | Preguntas realmente formuladas | Explicación |
|---|---|---|
| `[1]` | 1 | Primera respuesta = 1 → se corta el área de inmediato, se pasa a la siguiente área. |
| `[3, 5, 4]` | 3 | Primera respuesta = 3 → presupuesto de 3. La segunda (5) es mayor, pero **no extiende** el presupuesto: se formula la 3ª pregunta y el área termina en 3, no en 5. |
| `[5, 1]` | 2 | Primera respuesta = 5 → presupuesto de 5, pero la segunda respuesta (1) es menor a 3 → se corta ahí: solo 2 preguntas formuladas. |
| `[5, 5, 5, 5, 5]` | 5 | Presupuesto de 5 y todas las respuestas se mantienen ≥ 3 → se formulan las 5 preguntas completas del área. |
| `[4, 4, 2]` | 3 | Presupuesto de 4, pero la tercera respuesta (2) es menor a 3 → se corta en 3 preguntas, aunque el presupuesto permitía una 4ª. |
| `[2, 1]` | 2 | Primera respuesta = 2 → presupuesto de 2 preguntas. Se formula la 2ª pregunta (respuesta 1, menor a 3) → de todas formas el área ya termina en 2, porque ese era el presupuesto original. |
| `[2, 4]` | 2 | Primera respuesta = 2 → presupuesto de 2. Se formula la 2ª pregunta (respuesta 4, mayor a 3) → aun así el área termina en 2 preguntas, porque el presupuesto de la primera respuesta nunca se extiende. |

## Impacto en el resto del sistema

- **Vector de usuario:** cada componente del vector de 17 dimensiones se calcula como el promedio de las preguntas *realmente formuladas* en esa área (puede ser 1 a 5 valores), no siempre sobre 5. Ver "Cálculo del vector de usuario" en el Método 1.
- **Persistencia:** la tabla de respuestas (`respuestas_test`) debe guardar, para cada intento de test, qué `pregunta_id` fueron efectivamente mostradas y respondidas (no todas las 85 tendrán una fila).
- **Contrato de los endpoints `POST /test/tradicional` y `POST /test/chatbot`:** ya no reciben necesariamente 85 respuestas; reciben una lista de `{pregunta_id, respuesta}` de longitud variable (mínimo 17, una por área — el mínimo posible si el usuario responde 1 en la primera pregunta de cada una de las 17 áreas; máximo 85).
- **Progreso en la UI (ambos métodos):** dado que el total real de preguntas no se conoce de antemano, el progreso se debe comunicar por área completada (ej. "Área 6 de 17") y opcionalmente con una barra de progreso estimada que se recalcula dinámicamente conforme el sistema conoce el presupuesto real de cada área ya visitada.
- **Tests unitarios (`pytest`):** deben cubrir exactamente los casos de la tabla de ejemplos anterior, verificando la lista de respuestas devuelta por `preguntas_a_formular` para cada secuencia de entrada simulada.

---

# Banco de preguntas (85 preguntas, 17 áreas)

Usar **exactamente** este banco de preguntas, sin alterar el texto, el orden ni la asignación de área. Debe almacenarse en `data/preguntas.json` (no hardcodeado en el código).


### Desarrollo Personal (`desarrollo_personal`)

1. ¿Te gusta motivar a otras personas para que logren sus metas?
2. ¿Disfrutas participar en actividades de crecimiento personal, como talleres o lecturas de autoayuda?
3. ¿Te consideras una persona capaz de influir positivamente en el estado de ánimo de los demás?
4. ¿Te interesa aprender técnicas para mejorar tu autoconocimiento y bienestar emocional?
5. ¿Te gusta ayudar a otros a descubrir sus fortalezas y debilidades?


### Ciencias Sociales (`ciencias_sociales`)

6. ¿Te fascina analizar cómo se organizan las sociedades y cómo cambian con el tiempo?
7. ¿Te interesa investigar las causas de problemas sociales como la pobreza o la desigualdad?
8. ¿Disfrutas debatir sobre temas políticos, económicos o culturales con otras personas?
9. ¿Te gustaría proponer soluciones innovadoras para mejorar la calidad de vida de las comunidades?
10. ¿Te apasiona leer sobre historia, sociología o antropología?


### Educación Física (`educacion_fisica`)

11. ¿Practicas algún deporte o actividad física con regularidad?
12. ¿Te gusta enseñar ejercicios o rutinas de entrenamiento a otras personas?
13. ¿Crees que el ejercicio físico es fundamental para tener una vida saludable?
14. ¿Disfrutas participar en competencias deportivas o eventos de actividad física?
15. ¿Te interesaría estudiar los efectos del deporte en la salud y el rendimiento?


### Arte y Cultura (`arte_cultura`)

16. ¿Te gusta expresar tus emociones a través del arte (dibujo, pintura, música, danza, etc.)?
17. ¿Disfrutas visitar museos, galerías o asistir a eventos culturales?
18. ¿Te interesa la historia del arte y el patrimonio cultural de tu región?
19. ¿Te consideras una persona creativa y con sensibilidad estética?
20. ¿Te gustaría aprender a tocar un instrumento o perfeccionar una técnica artística?


### Comunicación (`comunicacion`)

21. ¿Te consideras hábil para expresar tus ideas de forma clara y convincente?
22. ¿Disfrutas escribir artículos, cuentos o cualquier tipo de contenido creativo?
23. ¿Te atrae el mundo de los medios de comunicación (radio, TV, prensa, redes sociales)?
24. ¿Sabes escuchar activamente y comprendes el punto de vista de los demás?
25. ¿Te gustaría trabajar en relaciones públicas, periodismo o marketing digital?


### Castellano (segunda lengua) (`castellano_segunda`)

26. ¿Disfrutas leer libros, poemas o artículos en castellano?
27. ¿Te sientes seguro al redactar textos formales o informales en castellano?
28. ¿Te gusta analizar la gramática y la riqueza del idioma castellano?
29. ¿Participarías con gusto en talleres de escritura creativa o declamación?
30. ¿Te interesa la literatura hispanoamericana y sus autores?


### Inglés (extranjero) (`ingles_extranjero`)

31. ¿Te motiva aprender inglés y usarlo para comunicarte con personas de otros países?
32. ¿Disfrutas ver películas, series o escuchar música en inglés sin subtítulos?
33. ¿Te gusta leer artículos o libros en inglés sobre temas que te interesan?
34. ¿Te sentirías capaz de mantener una conversación fluida en inglés?
35. ¿Te interesa la cultura de los países angloparlantes?


### Matemática (`matematica`)

36. ¿Disfrutas resolviendo problemas matemáticos o acertijos lógicos?
37. ¿Te consideras hábil para el cálculo mental y el razonamiento numérico?
38. ¿Te gusta explorar patrones y relaciones matemáticas en la naturaleza o en la tecnología?
39. ¿Te sentirías cómodo estudiando materias como álgebra, cálculo o estadística?
40. ¿Crees que las matemáticas son una herramienta fundamental para resolver problemas reales?


### Ciencia y Tecnología (`ciencia_tecnologia`)

41. ¿Te apasiona la investigación científica y descubrir cómo funcionan las cosas?
42. ¿Disfrutas experimentar con equipos, herramientas o software para crear soluciones?
43. ¿Te interesa la inteligencia artificial, la robótica o la programación?
44. ¿Te gusta estar al día sobre los últimos avances tecnológicos y científicos?
45. ¿Te considerarías una persona curiosa y con espíritu innovador?


### Educación para el Trabajo (`educacion_trabajo`)

46. ¿Te interesa la formación profesional y el desarrollo de habilidades laborales?
47. ¿Te gustaría asesorar o guiar a jóvenes en su inserción al mundo laboral?
48. ¿Disfrutas planificar proyectos y organizar equipos de trabajo?
49. ¿Te parece importante la educación continua y la capacitación en el trabajo?
50. ¿Te ves como un facilitador del aprendizaje práctico para otros?


### Pensamiento Analítico y Crítico (`pensamiento_analitico`)

51. ¿Te gusta descomponer problemas complejos en partes más pequeñas para entenderlos mejor?
52. ¿Evalúas la información de manera crítica antes de tomar una decisión?
53. ¿Disfrutas de los juegos de estrategia o de resolver acertijos lógicos?
54. ¿Te consideras capaz de anticipar las consecuencias de tus acciones?
55. ¿Te gusta cuestionar las cosas y buscar explicaciones fundamentadas?


### Alfabetización Digital e IA (`alfabetizacion_digital`)

56. ¿Te sientes cómodo usando aplicaciones y plataformas digitales?
57. ¿Te interesa aprender a usar la inteligencia artificial para mejorar tu trabajo?
58. ¿Disfrutas explorando nuevas herramientas tecnológicas por tu cuenta?
59. ¿Crees que saber programar o entender datos es importante hoy en día?
60. ¿Te gustaría especializarte en tecnología o ciencia de datos?


### Adaptabilidad y Resiliencia (`adaptabilidad_resiliencia`)

61. ¿Te adaptas fácilmente a los cambios inesperados en tu vida?
62. ¿Mantienes la calma y la concentración cuando enfrentas situaciones difíciles?
63. ¿Aprendes de los fracasos y los usas como impulso para mejorar?
64. ¿Te consideras una persona flexible y abierta a nuevas ideas?
65. ¿Te resulta fácil cambiar de planes cuando las circunstancias lo requieren?


### Comunicación Efectiva (`comunicacion_efectiva`)

66. ¿Expresas tus pensamientos de manera clara y ordenada?
67. ¿Te consideras un buen oyente y captas el mensaje de los demás?
68. ¿Sabes dar y recibir críticas constructivas de forma asertiva?
69. ¿Te gusta participar en debates o presentaciones orales?
70. ¿Adaptas tu forma de hablar según la persona o el contexto?


### Inteligencia Emocional e Interpersonal (`inteligencia_emocional`)

71. ¿Reconoces y entiendes tus propias emociones?
72. ¿Eres empático y te pones en el lugar de los demás?
73. ¿Sabes manejar el estrés y la presión sin perder el control?
74. ¿Resuelves conflictos de manera pacífica y asertiva?
75. ¿Te gusta trabajar en equipo y apoyar a tus compañeros?


### Curiosidad y Aprendizaje Continuo (`curiosidad_aprendizaje`)

76. ¿Sientes curiosidad por aprender sobre temas nuevos todos los días?
77. ¿Buscas activamente oportunidades de aprendizaje (cursos, libros, etc.)?
78. ¿Te gusta investigar por tu cuenta cuando algo te llama la atención?
79. ¿Crees que la educación no termina nunca y siempre hay algo nuevo por descubrir?
80. ¿Te motiva compartir lo que aprendes con los demás?


### Liderazgo y Trabajo en Equipo (`liderazgo_equipo`)

81. ¿Te gusta asumir el rol de líder cuando trabajas en un equipo?
82. ¿Disfrutas coordinar tareas y motivar a un grupo para alcanzar un objetivo común?
83. ¿Te sientes cómodo tomando decisiones que afectan a un equipo de trabajo?
84. ¿Te gusta delegar responsabilidades y confiar en las capacidades de los demás?
85. ¿Consideras que un buen líder debe saber escuchar y valorar las ideas de su equipo?


## `data/areas.json` — las 17 áreas (mantener este orden exacto; el orden define el orden de las dimensiones del vector)

```json
[
  {"key": "desarrollo_personal", "label": "Desarrollo Personal"},
  {"key": "ciencias_sociales", "label": "Ciencias Sociales"},
  {"key": "educacion_fisica", "label": "Educación Física"},
  {"key": "arte_cultura", "label": "Arte y Cultura"},
  {"key": "comunicacion", "label": "Comunicación"},
  {"key": "castellano_segunda", "label": "Castellano (segunda lengua)"},
  {"key": "ingles_extranjero", "label": "Inglés (extranjero)"},
  {"key": "matematica", "label": "Matemática"},
  {"key": "ciencia_tecnologia", "label": "Ciencia y Tecnología"},
  {"key": "educacion_trabajo", "label": "Educación para el Trabajo"},
  {"key": "pensamiento_analitico", "label": "Pensamiento Analítico y Crítico"},
  {"key": "alfabetizacion_digital", "label": "Alfabetización Digital e IA"},
  {"key": "adaptabilidad_resiliencia", "label": "Adaptabilidad y Resiliencia"},
  {"key": "comunicacion_efectiva", "label": "Comunicación Efectiva"},
  {"key": "inteligencia_emocional", "label": "Inteligencia Emocional e Interpersonal"},
  {"key": "curiosidad_aprendizaje", "label": "Curiosidad y Aprendizaje Continuo"},
  {"key": "liderazgo_equipo", "label": "Liderazgo y Trabajo en Equipo"}
]
```


## `data/preguntas.json` — formato esperado por pregunta

```json
{"id": 1, "area": "desarrollo_personal", "texto": "¿Te gusta motivar a otras personas para que logren sus metas?"}
```

Generar las 85 entradas exactamente como se listaron arriba, en el mismo orden de `id` (1 a 85).

---

# Datos de carreras (37 carreras × 17 áreas)

Usar **exactamente** esta matriz de perfiles (valores enteros 1–5, definidos por especialistas en orientación vocacional). Debe almacenarse en `data/carreras.csv`, **no hardcodeada dentro del código de la aplicación**. El backend la carga en memoria al iniciar (o la migra a la tabla `carreras` de PostgreSQL en el seed inicial).

```csv
carrera,desarrollo_personal,ciencias_sociales,educacion_fisica,arte_cultura,comunicacion,castellano_segunda,ingles_extranjero,matematica,ciencia_tecnologia,educacion_trabajo,pensamiento_analitico,alfabetizacion_digital,adaptabilidad_resiliencia,comunicacion_efectiva,inteligencia_emocional,curiosidad_aprendizaje,liderazgo_equipo
Ingeniería Agronómica,3,3,3,2,3,3,3,4,5,4,5,4,4,3,3,4,3
Ingeniería Agroindustrial,3,3,2,2,3,3,3,4,5,4,5,4,4,3,3,4,3
Ingeniería Topográfica y Agrimensura,2,3,3,3,3,2,3,5,4,4,4,4,4,3,3,4,3
Medicina Veterinaria y Zootecnia,3,3,3,2,3,3,3,3,5,3,4,3,5,5,5,4,4
Ingeniería Económica,4,4,2,2,4,3,4,5,3,4,5,4,5,4,3,4,4
Ciencias Contables,3,2,1,1,3,1,2,4,3,5,4,4,5,4,4,4,4
Administración,4,4,1,2,4,3,3,5,5,4,4,4,5,5,4,4,5
Enfermería,4,3,3,2,4,3,3,2,5,3,4,3,5,5,5,4,4
Trabajo Social,5,5,3,3,5,4,2,2,3,3,4,3,4,5,5,4,4
Ingeniería de Minas,3,3,4,2,3,2,3,5,5,4,5,4,4,3,3,4,4
Sociología,5,5,2,3,5,4,3,2,3,2,5,3,4,5,4,4,4
Turismo,4,5,3,4,5,4,5,2,3,3,3,3,4,5,4,4,4
Antropología,4,5,1,3,4,1,1,2,3,5,4,3,4,5,4,4,3
Ciencias de la Comunicación Social,3,4,1,4,5,2,1,2,3,3,4,4,4,5,4,4,4
Arte,2,3,1,5,3,1,2,2,3,4,3,3,3,5,5,5,3
Biología,2,2,1,1,3,1,3,4,5,3,4,4,4,4,4,5,3
Educación Secundaria,5,5,4,4,5,5,4,3,3,3,4,4,4,5,5,4,4
Educación Física,3,3,5,2,3,2,1,3,5,3,3,3,5,4,4,3,4
Educación Primaria,4,4,3,4,5,4,3,3,3,3,4,4,4,5,5,4,4
Educación Inicial,4,4,4,5,5,4,2,2,3,3,4,4,4,5,5,4,4
Ingeniería Estadística e Informática,3,2,1,2,3,3,4,5,4,5,5,5,4,3,3,5,3
Ingeniería Geológica,3,4,3,3,3,2,3,4,5,4,5,4,4,3,3,4,3
Ingeniería Metalúrgica,3,2,3,1,3,2,3,4,5,4,5,4,4,3,3,4,3
Derecho,5,5,1,2,5,4,3,2,2,3,5,3,4,5,4,4,4
Ingeniería Química,2,2,2,1,3,2,4,5,5,4,5,4,4,3,3,4,3
Nutrición Humana,3,3,3,2,4,3,3,3,5,3,4,3,5,4,4,4,3
Odontología,3,3,3,3,4,3,4,3,5,3,4,3,5,5,5,4,4
Ingeniería Agrícola,3,3,3,2,3,2,3,4,5,4,5,4,4,3,3,4,3
Ingeniería Civil,3,3,2,3,3,3,4,5,5,4,5,4,5,3,3,4,4
Arquitectura y Urbanismo,2,3,1,5,3,3,4,3,4,4,4,4,4,3,3,4,4
Ciencias Físico – Matemáticas,2,2,1,1,3,1,3,5,5,3,5,4,4,3,3,5,3
Medicina Humana,4,3,3,2,5,4,5,3,5,3,5,4,5,5,5,5,4
Ingeniería Mecánica Eléctrica,2,2,1,1,2,1,2,5,5,3,5,4,4,3,3,4,3
Ingeniería Electrónica,2,2,1,1,2,1,2,5,5,2,5,5,4,3,3,5,3
Ingeniería de Sistemas,2,2,1,2,3,1,2,5,5,3,5,5,4,3,3,5,4
Ingeniería de Inteligencia Artificial y Ciencia de Datos,3,2,1,3,3,3,5,5,5,5,5,5,5,3,3,5,4
Psicología,5,4,3,3,5,4,4,3,3,3,5,3,5,5,5,4,5
```


Este mismo dataset, en formato Python (para el script de seed/migración `scripts/seed_carreras.py`), es:

```python
AREAS = [
    "desarrollo_personal",
    "ciencias_sociales",
    "educacion_fisica",
    "arte_cultura",
    "comunicacion",
    "castellano_segunda",
    "ingles_extranjero",
    "matematica",
    "ciencia_tecnologia",
    "educacion_trabajo",
    "pensamiento_analitico",
    "alfabetizacion_digital",
    "adaptabilidad_resiliencia",
    "comunicacion_efectiva",
    "inteligencia_emocional",
    "curiosidad_aprendizaje",
    "liderazgo_equipo"
]

data_carreras = {
    'carrera': ['Ingeniería Agronómica', 'Ingeniería Agroindustrial', 'Ingeniería Topográfica y Agrimensura', 'Medicina Veterinaria y Zootecnia', 'Ingeniería Económica', 'Ciencias Contables', 'Administración', 'Enfermería', 'Trabajo Social', 'Ingeniería de Minas', 'Sociología', 'Turismo', 'Antropología', 'Ciencias de la Comunicación Social', 'Arte', 'Biología', 'Educación Secundaria', 'Educación Física', 'Educación Primaria', 'Educación Inicial', 'Ingeniería Estadística e Informática', 'Ingeniería Geológica', 'Ingeniería Metalúrgica', 'Derecho', 'Ingeniería Química', 'Nutrición Humana', 'Odontología', 'Ingeniería Agrícola', 'Ingeniería Civil', 'Arquitectura y Urbanismo', 'Ciencias Físico – Matemáticas', 'Medicina Humana', 'Ingeniería Mecánica Eléctrica', 'Ingeniería Electrónica', 'Ingeniería de Sistemas', 'Ingeniería de Inteligencia Artificial y Ciencia de Datos', 'Psicología'],
    'desarrollo_personal': [3, 3, 2, 3, 4, 3, 4, 4, 5, 3, 5, 4, 4, 3, 2, 2, 5, 3, 4, 4, 3, 3, 3, 5, 2, 3, 3, 3, 3, 2, 2, 4, 2, 2, 2, 3, 5],
    'ciencias_sociales': [3, 3, 3, 3, 4, 2, 4, 3, 5, 3, 5, 5, 5, 4, 3, 2, 5, 3, 4, 4, 2, 4, 2, 5, 2, 3, 3, 3, 3, 3, 2, 3, 2, 2, 2, 2, 4],
    'educacion_fisica': [3, 2, 3, 3, 2, 1, 1, 3, 3, 4, 2, 3, 1, 1, 1, 1, 4, 5, 3, 4, 1, 3, 3, 1, 2, 3, 3, 3, 2, 1, 1, 3, 1, 1, 1, 1, 3],
    'arte_cultura': [2, 2, 3, 2, 2, 1, 2, 2, 3, 2, 3, 4, 3, 4, 5, 1, 4, 2, 4, 5, 2, 3, 1, 2, 1, 2, 3, 2, 3, 5, 1, 2, 1, 1, 2, 3, 3],
    'comunicacion': [3, 3, 3, 3, 4, 3, 4, 4, 5, 3, 5, 5, 4, 5, 3, 3, 5, 3, 5, 5, 3, 3, 3, 5, 3, 4, 4, 3, 3, 3, 3, 5, 2, 2, 3, 3, 5],
    'castellano_segunda': [3, 3, 2, 3, 3, 1, 3, 3, 4, 2, 4, 4, 1, 2, 1, 1, 5, 2, 4, 4, 3, 2, 2, 4, 2, 3, 3, 2, 3, 3, 1, 4, 1, 1, 1, 3, 4],
    'ingles_extranjero': [3, 3, 3, 3, 4, 2, 3, 3, 2, 3, 3, 5, 1, 1, 2, 3, 4, 1, 3, 2, 4, 3, 3, 3, 4, 3, 4, 3, 4, 4, 3, 5, 2, 2, 2, 5, 4],
    'matematica': [4, 4, 5, 3, 5, 4, 5, 2, 2, 5, 2, 2, 2, 2, 2, 4, 3, 3, 3, 2, 5, 4, 4, 2, 5, 3, 3, 4, 5, 3, 5, 3, 5, 5, 5, 5, 3],
    'ciencia_tecnologia': [5, 5, 4, 5, 3, 3, 5, 5, 3, 5, 3, 3, 3, 3, 3, 5, 3, 5, 3, 3, 4, 5, 5, 2, 5, 5, 5, 5, 5, 4, 5, 5, 5, 5, 5, 5, 3],
    'educacion_trabajo': [4, 4, 4, 3, 4, 5, 4, 3, 3, 4, 2, 3, 5, 3, 4, 3, 3, 3, 3, 3, 5, 4, 4, 3, 4, 3, 3, 4, 4, 4, 3, 3, 3, 2, 3, 5, 3],
    'pensamiento_analitico': [5, 5, 4, 4, 5, 4, 4, 4, 4, 5, 5, 3, 4, 4, 3, 4, 4, 3, 4, 4, 5, 5, 5, 5, 5, 4, 4, 5, 5, 4, 5, 5, 5, 5, 5, 5, 5],
    'alfabetizacion_digital': [4, 4, 4, 3, 4, 4, 4, 3, 3, 4, 3, 3, 3, 4, 3, 4, 4, 3, 4, 4, 5, 4, 4, 3, 4, 3, 3, 4, 4, 4, 4, 4, 4, 5, 5, 5, 3],
    'adaptabilidad_resiliencia': [4, 4, 4, 5, 5, 5, 5, 5, 4, 4, 4, 4, 4, 4, 3, 4, 4, 5, 4, 4, 4, 4, 4, 4, 4, 5, 5, 4, 5, 4, 4, 5, 4, 4, 4, 5, 5],
    'comunicacion_efectiva': [3, 3, 3, 5, 4, 4, 5, 5, 5, 3, 5, 5, 5, 5, 5, 4, 5, 4, 5, 5, 3, 3, 3, 5, 3, 4, 5, 3, 3, 3, 3, 5, 3, 3, 3, 3, 5],
    'inteligencia_emocional': [3, 3, 3, 5, 3, 4, 4, 5, 5, 3, 4, 4, 4, 4, 5, 4, 5, 4, 5, 5, 3, 3, 3, 4, 3, 4, 5, 3, 3, 3, 3, 5, 3, 3, 3, 3, 5],
    'curiosidad_aprendizaje': [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 4, 3, 4, 4, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 4, 5, 5, 5, 4],
    'liderazgo_equipo': [3, 3, 3, 4, 4, 4, 5, 4, 4, 4, 4, 4, 3, 4, 3, 3, 4, 4, 4, 4, 3, 3, 3, 4, 3, 3, 4, 3, 4, 4, 3, 4, 3, 3, 4, 4, 5]
}
```

Restricciones:
- 37 carreras exactas, en el orden dado.
- 17 columnas de puntaje exactas, en el orden dado por `AREAS`.
- No inventar, redondear ni modificar ningún valor de esta matriz.
- Esta matriz es la que se usa como **población de referencia** para estimar la matriz de covarianza en el algoritmo de Mahalanobis (ver siguiente sección).

---

# Algoritmo de recomendación — Distancia de Mahalanobis (especificación exacta)

El algoritmo de recomendación **debe implementarse exactamente así**, en un único módulo `services/recomendacion_service.py`, reutilizado por los tres endpoints (`/test/tradicional`, `/test/chatbot`, `/recomendacion`).

## 1. Definiciones

- `X`: matriz de perfiles de carreras, forma `(37, 17)`, construida desde `data/carreras.csv` en el **mismo orden de columnas** que `data/areas.json`.
- `x_usuario`: vector de 17 dimensiones del estudiante (promedios Likert 1–5 por área, ver Método 1).
- `μ_c`: vector de perfil (fila) de la carrera `c` dentro de `X`.
- `Σ`: matriz de covarianza (17×17) estimada a partir de `X` (la variabilidad conjunta de las 17 áreas **entre las 37 carreras**).

## 2. Estimación de la matriz de covarianza

```python
import numpy as np

X = ...  # shape (37, 17), cargada desde data/carreras.csv, columnas en el orden de AREAS

cov_matrix = np.cov(X, rowvar=False)  # shape (17, 17)
```

**Problema conocido y manejo obligatorio:** con 37 observaciones y 17 dimensiones, la matriz de covarianza está cerca del límite de ser numéricamente inestable o singular (número de muestras no muy superior al número de variables). El sistema **debe** manejar esto así:

1. Intentar invertir con `np.linalg.inv(cov_matrix)`.
2. Si `cov_matrix` es singular o mal condicionada (capturar `np.linalg.LinAlgError`, o verificar `np.linalg.cond(cov_matrix) > 1e10`), aplicar **regularización tipo shrinkage** antes de invertir:
   ```python
   epsilon = 1e-6
   cov_matrix_reg = cov_matrix + epsilon * np.eye(cov_matrix.shape[0])
   ```
3. Si aún así hay problemas de inversión, usar la **pseudo-inversa de Moore-Penrose** como fallback robusto:
   ```python
   inv_cov_matrix = np.linalg.pinv(cov_matrix_reg)
   ```
4. Cachear `inv_cov_matrix` en memoria (o Redis) al iniciar el backend; **no recalcularla en cada request**, solo cuando cambien los datos de `carreras.csv`/tabla `carreras`.

## 3. Cálculo de la distancia de Mahalanobis por carrera

Para cada carrera `c` de las 37:

```python
from scipy.spatial.distance import mahalanobis

d_c = mahalanobis(x_usuario, mu_c, inv_cov_matrix)
# equivalente matemático:
# d_c = sqrt( (x_usuario - mu_c)^T · inv_cov_matrix · (x_usuario - mu_c) )
```

Esto produce un vector de 37 distancias, una por carrera.

## 4. Conversión de distancia a porcentaje de afinidad

Las distancias de Mahalanobis no tienen un límite superior fijo, así que deben normalizarse dentro del conjunto de resultados del propio usuario antes de mostrarse como porcentaje:

```python
d_min = min(distancias)
d_max = max(distancias)

# Evitar división por cero si todas las distancias son iguales
if d_max == d_min:
    afinidad_pct = [100.0 for _ in distancias]
else:
    afinidad_pct = [
        round(100 * (1 - (d - d_min) / (d_max - d_min)), 1)
        for d in distancias
    ]
```

Esto garantiza que la carrera más cercana (menor distancia) obtenga la afinidad más alta dentro del ranking de ese estudiante, y la más lejana la más baja, en una escala 0–100% relativa y comparable entre carreras para ese mismo resultado.

## 5. Ranking y salida

1. Ordenar las 37 carreras de **menor a mayor** distancia de Mahalanobis.
2. Tomar el **Top 5**.
3. Para cada una de las 5, calcular:
   - **Fortalezas / áreas fuertes**: las áreas donde `x_usuario[area] >= mu_c[area]` y `x_usuario[area] >= 4`, ordenadas de mayor a menor valor del usuario.
   - **Áreas por mejorar**: las áreas donde `x_usuario[area] < mu_c[area]` con la mayor brecha (`mu_c[area] - x_usuario[area]`), tomar hasta 3.
   - **Explicación**: texto generado por reglas (plantilla) que menciona las 2-3 áreas de mayor coincidencia, ej: "Tu perfil muestra una fuerte afinidad en Matemática y Pensamiento Analítico, competencias clave para {carrera}."

## 6. Contrato de salida del endpoint `/recomendacion`

```json
{
  "vector_usuario": { "matematica": 4.8, "...": "..." },
  "resultados": [
    {
      "carrera_id": 35,
      "nombre": "Ingeniería de Sistemas",
      "distancia_mahalanobis": 1.732,
      "afinidad_pct": 94.6,
      "explicacion": "...",
      "fortalezas": ["matematica", "pensamiento_analitico", "ciencia_tecnologia"],
      "areas_por_mejorar": ["arte_cultura"]
    }
  ]
}
```

## 7. Requisitos no funcionales del cálculo

- Toda la lógica de Mahalanobis vive en `services/recomendacion_service.py`; los routers de FastAPI (`api/test.py`, `api/recomendacion.py`) solo orquestan, nunca calculan directamente.
- Debe existir un test unitario (`pytest`) que verifique: (a) que la matriz de covarianza se invierte sin error con los 37×17 datos reales, (b) que el vector de distancias tiene longitud 37, (c) que la carrera con distancia mínima corresponde al resultado top 1, (d) un caso de borde con vector de usuario idéntico al promedio general (todas las áreas en el promedio de `X`) no debe lanzar excepciones.
- El servicio debe exponer una función pura `calcular_recomendacion(vector_usuario: dict[str, float]) -> list[ResultadoCarrera]` fácilmente testeable, sin dependencias de FastAPI ni de la base de datos dentro de la función de cálculo puro (las carreras y la matriz de covarianza se le inyectan como parámetros o se cargan vía un repositorio inyectado).

---

# Backend (FastAPI)

Crear módulos separados:

```
backend/
├── api/            # routers: preguntas, areas, test, recomendacion, carreras
├── services/        # recomendacion_service.py, test_service.py, chatbot_service.py
├── models/           # SQLAlchemy ORM models
├── schemas/          # Pydantic v2 schemas (request/response)
├── data/             # preguntas.json, areas.json, labels.json, carreras.csv
├── core/              # config, seguridad JWT, dependencias
└── tests/             # pytest, incluyendo los tests de Mahalanobis descritos arriba
```

Endpoints:

- `GET /preguntas` — devuelve el banco completo de hasta 85 preguntas (el frontend/chatbot decide cuáles formular realmente aplicando la Lógica Adaptativa de Preguntas)
- `GET /areas` — devuelve las 17 áreas con sus labels
- `POST /test/tradicional` — recibe respuestas 1–85, calcula vector, devuelve `test_id`
- `POST /test/chatbot` — mismo contrato de entrada/salida que el anterior, alimentado por el flujo conversacional
- `POST /recomendacion` — recibe `vector_usuario` o `test_id`, ejecuta Mahalanobis, devuelve Top 5
- `GET /carreras` — lista las 37 carreras con su perfil
- `GET /carrera/{id}` — detalle de una carrera

---

# Resultados

Diseñar una página moderna que muestre:
- Gráfico radar (17 ejes) comparando `vector_usuario` vs el perfil de la carrera recomendada.
- Gráfico de barras con el `afinidad_pct` de las Top 5 carreras.
- Tarjetas modernas para cada una de las Top 5, con distancia, afinidad %, fortalezas y áreas por mejorar.
- Botones: Ver perfil profesional · Comparar carreras · Descargar PDF · Realizar nuevamente el test.

---

# Arquitectura esperada

```
Frontend (Next.js)
Landing Page
  ↓
Seleccionar método
  ↓
Formulario tradicional  ó  Chatbot basado en reglas
  ↓ (mismo payload: vector de 17 áreas)
FastAPI
  ↓
services/recomendacion_service.py
  ↓
Cálculo de covarianza + inversa (cacheada) → Distancia de Mahalanobis (scipy) → normalización a %
  ↓
Top 5 resultados
  ↓
Dashboard de resultados (Next.js)
```

---

# Diseño UI/UX (especificación detallada)

Esta sección define, pantalla por pantalla, componente por componente, todo lo que la interfaz debe tener. El objetivo es que cualquier desarrollador o modelo que implemente el sistema no tenga que inventar decisiones de diseño: deben quedar resueltas aquí. Se incluyen además mejoras propuestas (no pedidas explícitamente antes) que elevan la calidad percibida y la usabilidad del producto.

## Stack visual y principios generales

- **Tailwind CSS + shadcn/ui + Lucide Icons + Framer Motion** para toda animación de entrada/salida, transiciones de pregunta a pregunta y micro-interacciones.
- **Tipografía:** una fuente sans-serif moderna para textos (ej. Inter o Geist) y opcionalmente una fuente de acento para títulos grandes de landing/resultados. Jerarquía tipográfica clara: H1 (landing hero), H2 (secciones), H3 (tarjetas), body, caption/metadata.
- **Sistema de color:** paleta institucional UNA Puno (tonos guinda/vino + dorado, o los oficiales de la universidad) como color primario, con una paleta neutra (grises) para fondos/texto y colores semánticos (verde=éxito/alta afinidad, ámbar=media, rojo=baja/error) reservados solo para estados, nunca como color decorativo.
- **Modo claro y oscuro**, con toggle persistente (guardado en `localStorage`/cookie), respetando `prefers-color-scheme` por defecto la primera vez. Todos los componentes (gráficos incluidos) deben adaptar contraste correctamente en ambos modos.
- **Responsive-first:** diseño mobile-first con breakpoints estándar de Tailwind (`sm`, `md`, `lg`, `xl`). El test (ambos métodos) debe ser perfectamente usable en un celular de gama media, con áreas táctiles de al menos 44×44px.
- **Animaciones:** transiciones suaves (200–350ms, easing `ease-out`) para cambios de pregunta, apertura de tarjetas y navegación entre pantallas. Nunca animaciones que bloqueen la interacción por más de lo estrictamente necesario. Debe respetarse `prefers-reduced-motion` desactivando o simplificando animaciones para usuarios que lo soliciten a nivel de sistema operativo.
- **Estados de carga:** usar *skeletons* (shadcn `Skeleton`) en vez de spinners genéricos siempre que se esté esperando data (lista de áreas, cálculo de recomendación, carga de perfil de carrera).
- **Estados vacíos y de error:** cada pantalla que dependa de datos remotos debe definir su propio *empty state* (ilustración + mensaje + acción) y su propio *error state* (mensaje claro + botón "Reintentar"), nunca una pantalla en blanco o un stack trace.
- **Accesibilidad (WCAG 2.1 AA):** contraste mínimo 4.5:1 en texto, navegación completa por teclado (incluido el flujo de test y el chatbot), roles ARIA en el chatbot (`role="log"` para el historial, `aria-live="polite"` para nuevos mensajes), focus visible en todos los elementos interactivos, labels asociados a cada input, textos alternativos en ilustraciones.
- **Feedback táctil/visual inmediato:** cada acción del usuario (seleccionar una respuesta Likert, enviar un mensaje al chatbot, hacer clic en un botón) debe tener una respuesta visual inmediata (<100ms) antes de que llegue la respuesta del backend, para que la interfaz nunca se sienta "congelada".

## 1. Landing Page (detalle adicional de UI)

- **Header fijo (sticky)** con logo UNA Puno, links de navegación (Cómo funciona, Métodos, Carreras, Preguntas frecuentes), botón de toggle claro/oscuro y botón CTA "Comenzar Test" siempre visible.
- **Hero:** título + subtítulo + dos botones CTA (primario "Realizar Test", secundario outline "Conversar con el Chatbot") + ilustración/animación decorativa (Framer Motion, elementos flotando suavemente) + un indicador de confianza pequeño debajo de los botones, ej. "37 carreras · 17 áreas evaluadas · Test 100% gratuito".
- **Sección "¿Cómo funciona?":** 3 tarjetas con ícono (Lucide), número de paso, título y descripción, animadas con aparición escalonada (`stagger`) al hacer scroll (usar `whileInView`).
- **Sección "Métodos del Test":** dos tarjetas grandes lado a lado (en mobile, apiladas), cada una con ícono distintivo (formulario vs. burbuja de chat), lista corta de beneficios de ese método y su botón de acción propio.
- **Sección "Explora las 37 carreras" (mejora sugerida):** carrusel o grilla filtrable (por facultad/área) de las carreras disponibles, cada una como tarjeta compacta con nombre y facultad, que al hacer clic navega al detalle de esa carrera (`/carrera/{id}`) — esto ayuda a generar confianza mostrando de antemano el catálogo real contra el que se compara el usuario.
- **Sección Beneficios:** grilla de 4–6 íconos con texto corto.
- **Sección "Preguntas frecuentes" (mejora sugerida):** accordion (shadcn `Accordion`) con dudas típicas: "¿Cuánto dura el test?", "¿Mis datos son privados?", "¿Puedo repetir el test?", "¿Qué diferencia hay entre el formulario y el chatbot?".
- **Footer:** información institucional, links legales (privacidad, términos), redes sociales de la universidad, y un pequeño disclaimer de que el sistema es una herramienta de orientación, no una decisión vinculante.

## 2. Pantalla de selección de método

- Reutiliza el diseño de las tarjetas de "Métodos del Test" pero como pantalla dedicada (`/test`), con un botón "Volver al inicio".
- **Mejora sugerida:** mostrar tiempo estimado dinámico por método basado en el promedio histórico de duración de otros usuarios (si no hay datos aún, usar una estimación fija tipo "10–15 min").
- **Mejora sugerida:** ofrecer un checkbox opcional "Continuar como invitado" vs. flujo autenticado, dejando claro que solo el usuario autenticado puede ver su historial de tests pasados y comparar resultados en el tiempo.

## 3. Test Tradicional (formulario) — componentes obligatorios

- **Barra de progreso superior** de dos niveles: (a) progreso por área ("Área 6 de 17") con puntos/segmentos, uno por área, que se van rellenando; (b) barra continua fina debajo mostrando el porcentaje estimado global, recalculada dinámicamente conforme se conoce el presupuesto real de cada área ya visitada.
- **Encabezado de pregunta:** nombre del área actual (con ícono propio por área, ej. calculadora para Matemática, paleta para Arte y Cultura) + "Pregunta X de máx. Y en {Área}".
- **Tarjeta de pregunta central**, tipografía grande y legible, con transición de deslizamiento/fundido (Framer Motion) al cambiar de pregunta.
- **Selector Likert:** 5 opciones presentadas como botones grandes tipo *card* (no radio buttons pequeños), cada uno con emoji/ícono + texto de la escala ("No me gusta nada" … "Me gusta mucho"), resaltado visual claro de la opción seleccionada, navegable con teclado (flechas + Enter) y con números 1–5 del teclado como atajo.
- **Navegación:** botón "Anterior" (deshabilitado en la primera pregunta absoluta), botón "Siguiente" (deshabilitado hasta seleccionar una respuesta), y un indicador de autoguardado ("Guardado automáticamente") ya que el progreso se persiste en cada respuesta.
- **Panel lateral o modal de "Resumen de áreas" (mejora sugerida):** accesible desde un botón flotante, muestra qué áreas ya se completaron, cuántas preguntas tuvo cada una, y permite saltar a revisar/editar una respuesta anterior sin perder el progreso posterior no afectado.
- **Al recortar/extender un área por edición retroactiva:** mostrar un toast/notificación breve explicando qué pasó (ej. "Como cambiaste tu respuesta, esta área ahora tiene 3 preguntas en vez de 5"), para que el usuario entienda el comportamiento adaptativo y no lo perciba como un error.
- **Botón de salida con confirmación:** si el usuario intenta cerrar/navegar fuera a mitad del test, mostrar un diálogo de confirmación (shadcn `AlertDialog`) indicando que el progreso se guardó y puede continuar después (si hay sesión) o que se perderá (si es invitado).

## 4. Test por Chatbot — componentes obligatorios

- **Layout tipo chat moderno** (similar a apps de mensajería): burbujas del chatbot alineadas a la izquierda con avatar/ícono del "orientador vocacional", burbujas del usuario alineadas a la derecha.
- **Indicador de "escribiendo..."** (typing indicator animado) de 400–800ms antes de que aparezca cada nuevo mensaje del chatbot, para dar sensación de conversación natural (aun siendo 100% basado en reglas).
- **Input de respuesta contextual:** en vez de un campo de texto libre genérico, cuando el chatbot espera una respuesta Likert (1–5) mostrar **botones rápidos numerados** (chips 1 al 5, cada uno con su etiqueta corta) debajo del campo de texto, para minimizar errores de validación; el campo de texto libre queda disponible igual por si el usuario prefiere escribir el número.
- **Mini indicador de progreso persistente** (barra delgada fija en la parte superior del chat) mostrando "Área 6 de 17", sin interrumpir el flujo conversacional.
- **Mensajes de sistema diferenciados visualmente** (fondo distinto, más sutil) para anuncios de cambio de área o mensajes de motivación, distinguiéndolos de las preguntas normales.
- **Scroll automático** al último mensaje, con botón "Ir al final" si el usuario sube a revisar el historial.
- **Mejora sugerida — retomar sesión:** si el usuario refresca o cierra la pestaña, al volver debe aparecer un mensaje del chatbot tipo "Continuemos donde lo dejamos, estábamos en el área de {X}", reconstruyendo visualmente el historial desde el estado guardado en backend.
- **Accesibilidad del chat:** historial con `role="log"` y `aria-live="polite"`, para que lectores de pantalla anuncien cada nuevo mensaje sin interrumpir al usuario a mitad de una acción.

## 5. Pantalla de Resultados — componentes obligatorios

- **Encabezado de resultado principal:** nombre y facultad de la carrera #1, badge grande con el `afinidad_pct`, botón destacado "Ver perfil completo de la carrera".
- **Gráfico radar (17 ejes)** comparando `vector_usuario` vs. el perfil de la carrera recomendada, con leyenda clara y colores distintos para cada serie; debe soportar hover/tap por eje mostrando el valor exacto.
- **Gráfico de barras horizontales** con el Top 5 y su `afinidad_pct`, ordenado de mayor a menor, con animación de "llenado" al entrar en viewport.
- **Tarjetas del Top 5** (grid responsive: 1 columna en mobile, hasta 3 en desktop), cada una con: posición en el ranking, nombre de carrera, facultad, `afinidad_pct` (con barra de progreso circular o lineal), lista de fortalezas (chips verdes) y áreas por mejorar (chips ámbar), y botón "Ver detalle".
- **Explicación en lenguaje natural** (generada por reglas) debajo de cada tarjeta o en un acordeón expandible, evitando saturar la vista inicial.
- **Botones de acción:** "Ver perfil profesional", "Comparar carreras" (mejora: selector de hasta 3 carreras del Top 5 para verlas lado a lado en una tabla comparativa), "Descargar PDF", "Realizar nuevamente el test".
- **Mejora sugerida — Comparador de carreras:** vista de tabla/columnas donde el usuario elige 2–3 carreras del Top 5 y ve lado a lado: afinidad %, fortalezas, áreas por mejorar y un mini-radar superpuesto por carrera.
- **Mejora sugerida — Historial de resultados:** si el usuario está autenticado, una pestaña "Mis resultados anteriores" con línea de tiempo de tests realizados y cómo cambiaron sus recomendaciones a lo largo del tiempo.
- **Compartir resultado (mejora sugerida):** botón para compartir un enlace de solo lectura del resultado (sin datos sensibles) o exportarlo como imagen para redes sociales.

## 6. Página de detalle de carrera (`/carrera/{id}`)

- Encabezado con nombre, facultad, ícono/imagen representativa.
- Descripción de la carrera, malla curricular resumida (si se dispone del dato), campo laboral, y el **perfil de las 17 áreas de esa carrera** visualizado como el mismo tipo de gráfico radar usado en resultados, para que sea comparable visualmente.
- Si el usuario llega desde una recomendación, mostrar además superpuesto su propio vector con un toggle "Comparar con mi perfil".

## 7. Componentes transversales (design system)

- **Navbar / Header** consistente en todas las pantallas post-landing, con breadcrumb simple (ej. Inicio > Test > Resultados).
- **Toast/notificaciones** (shadcn `Sonner` o `Toast`) para confirmaciones, autoguardado, errores de red y explicaciones del recorte adaptativo de preguntas.
- **Modales de confirmación** (shadcn `AlertDialog`) para acciones destructivas o de salida a mitad de proceso.
- **Loading global** con skeletons específicos por tipo de contenido (tarjetas de carrera, gráfico radar, lista de preguntas), nunca un spinner genérico de pantalla completa salvo en la carga inicial de la app.
- **Manejo de errores de red/backend:** componente reutilizable de error con ícono, mensaje amigable en español y botón "Reintentar", usado en cualquier fetch fallido (preguntas, envío de test, cálculo de recomendación).

## 8. Resumen de mejoras de UX agregadas (no solicitadas explícitamente, recomendadas)

1. Sección "Explora las 37 carreras" en la landing para generar confianza antes de iniciar el test.
2. Sección de Preguntas Frecuentes (FAQ) en la landing.
3. Panel/modal de "Resumen de áreas" durante el formulario, para revisar y saltar a editar respuestas.
4. Toast explicativo cuando el recorte/extensión adaptativa de preguntas ocurre por una edición retroactiva.
5. Confirmación de salida a mitad del test para evitar pérdida accidental de progreso.
6. Botones rápidos numerados (chips 1–5) en el chatbot, en vez de depender solo de texto libre.
7. Reanudación conversacional del chatbot tras refresco de página, con mensaje de contexto.
8. Comparador de carreras lado a lado (hasta 3) en la pantalla de resultados.
9. Historial de resultados para usuarios autenticados, con línea de tiempo de intentos.
10. Opción de compartir/exportar el resultado como imagen o enlace de solo lectura.
11. Indicador de confianza cuantitativo en el hero de la landing (número de carreras, áreas, duración).
12. Soporte explícito de `prefers-reduced-motion` y navegación completa por teclado como requisitos de accesibilidad, no como opcional.

---

# Objetivo final

Generar un sistema completo, modular, escalable y profesional que permita a un estudiante realizar el test vocacional mediante un formulario tradicional o mediante un chatbot basado en reglas. Ambos métodos deben utilizar **exactamente** el banco de hasta 85 preguntas y la matriz de 37 carreras × 17 áreas especificados en este documento, aplicar la **misma Lógica Adaptativa de Preguntas por Área** (recortando o manteniendo el número de preguntas de cada área según la primera respuesta y las respuestas subsecuentes, nunca extendiéndolo por encima de lo que habilitó la primera respuesta), y producir las mismas recomendaciones mediante el algoritmo de **Distancia de Mahalanobis** (con regularización/pseudo-inversa como fallback, normalización a porcentaje de afinidad, y explicación por reglas), ofreciendo una experiencia intuitiva, moderna y fácil de usar.
