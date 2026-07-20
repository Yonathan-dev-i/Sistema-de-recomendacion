"""Schemas Pydantic v2 para `GET /usuarios/me/intentos` (Fase 9b)."""
import datetime as dt

from pydantic import BaseModel

from app.models.intento_test import EstadoIntento, MetodoTest


class IntentoResumenOut(BaseModel):
    """
    Una fila de la línea de tiempo de "Mis resultados anteriores".

    `carrera_top1` / `afinidad_top1_pct` son `None` cuando el intento quedó
    en progreso o abandonado (nunca llegó a calcular un resultado).
    """

    id: int
    metodo: MetodoTest
    estado: EstadoIntento
    iniciado_en: dt.datetime
    completado_en: dt.datetime | None
    carrera_top1_id: int | None
    carrera_top1: str | None
    afinidad_top1_pct: float | None

    model_config = {"from_attributes": True}
