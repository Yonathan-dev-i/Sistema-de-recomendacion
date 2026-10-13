"""Modelo de pregunta del banco vocacional (34 preguntas, 17 áreas)."""
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.area import Area


class Pregunta(Base):
    __tablename__ = "preguntas"

    id: Mapped[int] = mapped_column(primary_key=True)
    """Usa el mismo id 1-34 definido en data/preguntas.json (no autoincremental libre)."""
    area_key: Mapped[str] = mapped_column(String(64), ForeignKey("areas.key"), index=True)
    texto: Mapped[str] = mapped_column(Text)

    area: Mapped["Area"] = relationship()