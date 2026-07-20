"""Schemas Pydantic v2 para `POST /test/tradicional` (Fase 4)."""
from pydantic import BaseModel, Field, field_validator

from app.schemas.recomendacion import ResultadoCarreraOut


class RespuestaItemIn(BaseModel):
    """Una respuesta individual tal como la envía el formulario tradicional."""

    pregunta_id: int = Field(..., ge=1, le=85)
    respuesta: int = Field(..., ge=1, le=5)


class TestTradicionalIn(BaseModel):
    """
    Payload del formulario: lista de longitud variable (mínimo 17, una por
    área si el usuario respondió 1 en la primera pregunta de todas; máximo 85),
    exactamente como lo describe el prompt maestro.
    """

    respuestas: list[RespuestaItemIn] = Field(..., min_length=17, max_length=85)

    @field_validator("respuestas")
    @classmethod
    def _sin_pregunta_id_repetido(cls, v: list[RespuestaItemIn]) -> list[RespuestaItemIn]:
        ids = [r.pregunta_id for r in v]
        if len(ids) != len(set(ids)):
            raise ValueError("No puede haber pregunta_id repetidos en el payload.")
        return v


class TestTradicionalOut(BaseModel):
    test_id: int
    vector_usuario: dict[str, float]
    resultados: list[ResultadoCarreraOut]
