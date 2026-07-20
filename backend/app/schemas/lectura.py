"""Schemas Pydantic v2 de salida para los endpoints de solo lectura de la Fase 1."""
from pydantic import BaseModel, ConfigDict


class AreaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    label: str
    orden: int


class PreguntaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    area: str
    texto: str


class CarreraResumenOut(BaseModel):
    """Versión ligera para listados (`GET /carreras`)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    facultad: str | None = None


class CarreraDetalleOut(CarreraResumenOut):
    """Versión completa con el perfil de 17 áreas (`GET /carrera/{id}`)."""

    perfil_areas: dict[str, int]
