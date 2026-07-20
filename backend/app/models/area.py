"""Modelo de área vocacional (una de las 17 dimensiones del vector)."""
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Area(Base):
    __tablename__ = "areas"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    label: Mapped[str] = mapped_column(String(120))
    orden: Mapped[int] = mapped_column(unique=True)
    """Posición 0-16 según la constante AREAS (define el orden del vector)."""
