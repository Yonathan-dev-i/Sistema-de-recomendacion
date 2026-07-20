# Historia de construcción del sistema

Este índice enlaza, en orden, el documento de cierre de cada una de las 15
fases en las que se construyó el **Sistema Inteligente de Orientación
Vocacional — UNA Puno** (Next.js + FastAPI + Distancia de Mahalanobis),
según lo definido en `docs/prompt-maestro.md`. Leído de principio a fin,
es la bitácora completa del proyecto: qué se construyó en cada etapa, qué
decisiones técnicas se tomaron, cómo se verificó cada criterio de
aceptación y qué quedó pendiente en cada punto.

Pensado como punto de entrada para un docente, un jurado o una persona
nueva en el equipo que quiera entender cómo se llegó al sistema actual sin
tener que leer todo el código.

| # | Fase | Resumen |
|---|---|---|
| 0 | [Preparación del proyecto (andamiaje)](fase-0-andamiaje.md) | Esqueleto de frontend y backend corriendo y comunicándose vía un endpoint de salud, sin lógica de negocio todavía. |
| 1 | [Datos base y modelos](fase-1-datos-modelos.md) | Las 17 áreas, 85 preguntas y 37 carreras (con su perfil de 17 puntajes) en PostgreSQL, con migraciones y seed reproducible. |
| 2 | [Motor de recomendación (Mahalanobis)](fase-2-motor-mahalanobis.md) | Algoritmo de Distancia de Mahalanobis funcionando y testeado de forma aislada. |
| 3 | [Lógica Adaptativa de Preguntas](fase-3-logica-adaptativa.md) | Módulo compartido de recorte/extensión de preguntas por área, independiente del método de test. |
| 4 | [Test Tradicional (formulario) end-to-end](fase-4-test-tradicional.md) | Primer flujo completo usable: formulario → cálculo de vector → Top 5 → persistencia del intento. |
| 5 | [Landing Page y navegación general](fase-5-landing-navegacion.md) | Landing completa, pantalla de selección de método, Header/Navbar con modo claro/oscuro. |
| 6 | [Chatbot: núcleo conversacional](fase-6-chatbot-nucleo.md) | Segundo método de test (chat basado en reglas), matemáticamente equivalente al formulario. |
| 7 | [Chatbot: funcionalidades avanzadas](fase-7-chatbot-avanzado.md) | Preguntas abiertas tipo FAQ, comandos de navegación y seguimiento post-resultado dentro del chat. |
| 8 | [Resultados avanzados y páginas de carrera](fase-8-resultados-avanzados.md) | Radar de 17 ejes, barras del Top 5, tarjetas completas, comparador de carreras y página de detalle. |
| 9a | [Autenticación](fase-9a-autenticacion.md) | Registro, login, refresh y cierre de sesión con JWT. |
| 9b | [Intentos e historial](fase-9b-intentos-historial.md) | Intentos asociados a `usuario_id` y pantalla "Mis resultados anteriores". |
| 9c | [Equivalencia formulario vs. chatbot](fase-9c-equivalencia-metodos.md) | Verificación automatizada de que ambos métodos producen el mismo `vector_usuario`. |
| 9d | [Accesibilidad (WCAG AA)](fase-9d-accesibilidad.md) | Contraste, navegación por teclado, roles ARIA, foco visible y `prefers-reduced-motion` en todas las pantallas. |
| 9e | [Estados de carga, error y vacíos](fase-9e-estados-carga-error.md) | Skeletons, mensajes de error con reintento y empty states en toda pantalla dependiente de datos remotos. |
| 9f | [Performance y despliegue](fase-9f-performance-despliegue.md) | Lazy loading y memoización de gráficos pesados; Dockerfiles, `docker-compose.yml` y checklist de verificación móvil real (cierre del proyecto). |

---

**Estado general al cierre:** 14 de las 15 fases están CERRADAS. La Fase
9f quedó **PARCIAL**: la configuración de despliegue (Docker) y las
optimizaciones de performance están completas y verificadas por build,
pero dos pasos de verificación manual —un `docker compose up` de punta a
punta y una prueba en un dispositivo móvil físico real— no pudieron
ejecutarse desde el entorno de desarrollo usado para construir el
sistema y quedan documentados como pendientes explícitos en la sección 6
de [fase-9f-performance-despliegue.md](fase-9f-performance-despliegue.md).
