"""
Constante compartida `AREAS`: define el orden fijo de las 17 dimensiones del
vector vocacional. Este orden es usado por:
- `data/areas.json` / `data/carreras.csv` (deben coincidir exactamente).
- `construir_vector_usuario` (Fase 3).
- El motor de Mahalanobis (Fase 2).

**No reordenar.** Cualquier desalineación entre este listado y las columnas del
dataset de carreras produce un vector de usuario comparado contra la columna
equivocada (ver validación de arranque en `app.core.startup_checks`).
"""

AREAS: list[str] = [
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
    "liderazgo_equipo",
]
