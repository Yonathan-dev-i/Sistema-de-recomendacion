"""Schemas Pydantic v2 para el endpoint `POST /recomendacion` (Fase 2)."""
from pydantic import BaseModel, Field, field_validator

from app.core.constants import AREAS


class VectorUsuarioIn(BaseModel):
    """
    Vector de 17 valores (uno por área), escala Likert 1.0-5.0.

    Se valida que las claves recibidas coincidan **exactamente** con `AREAS`
    (ni de más ni de menos), para no comparar contra la columna equivocada.
    """

    vector_usuario: dict[str, float] = Field(
        ...,
        description="Diccionario {area_key: promedio 1.0-5.0}, con las 17 claves de AREAS.",
    )

    @field_validator("vector_usuario")
    @classmethod
    def _validar_claves_y_rango(cls, v: dict[str, float]) -> dict[str, float]:
        claves_recibidas = set(v.keys())
        claves_esperadas = set(AREAS)
        if claves_recibidas != claves_esperadas:
            faltantes = claves_esperadas - claves_recibidas
            sobrantes = claves_recibidas - claves_esperadas
            raise ValueError(
                "vector_usuario debe tener exactamente las 17 claves de AREAS. "
                f"Faltantes: {sorted(faltantes) or 'ninguna'}. "
                f"Sobrantes/desconocidas: {sorted(sobrantes) or 'ninguna'}."
            )
        fuera_de_rango = {k: val for k, val in v.items() if not (1.0 <= val <= 5.0)}
        if fuera_de_rango:
            raise ValueError(
                f"Todos los valores deben estar en el rango [1.0, 5.0]. "
                f"Fuera de rango: {fuera_de_rango}"
            )
        return v


class ResultadoCarreraOut(BaseModel):
    carrera_id: int
    nombre: str
    distancia_mahalanobis: float
    afinidad_pct: float
    explicacion: str
    fortalezas: list[str]
    areas_por_mejorar: list[str]


class RecomendacionOut(BaseModel):
    vector_usuario: dict[str, float]
    resultados: list[ResultadoCarreraOut]
