"""Modelo de una respuesta individual (Likert 1-5) dentro de un intento de test."""
import datetime as dt
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.intento_test import IntentoTest


class RespuestaTest(Base):
    __tablename__ = "respuestas_test"
    __table_args__ = (
        CheckConstraint("respuesta >= 1 AND respuesta <= 5", name="ck_respuesta_likert_1_5"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    intento_id: Mapped[int] = mapped_column(ForeignKey("intentos_test.id"), index=True)
    pregunta_id: Mapped[int] = mapped_column(ForeignKey("preguntas.id"))
    respuesta: Mapped[int]
    """Valor Likert 1-5."""
    respondida_en: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: dt.datetime.now(dt.UTC)
    )

    intento: Mapped["IntentoTest"] = relationship(back_populates="respuestas")
