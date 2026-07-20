"""
Modelo de carrera y su perfil de 17 puntajes (uno por área).

Se normaliza en dos tablas (`carreras` y `carrera_puntajes`) en vez de guardar
el vector de 17 valores en una sola columna JSON, para poder consultar/filtrar
por área desde SQL si se necesita más adelante (ej. "carreras con matemática >= 4").
"""
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Carrera(Base):
    __tablename__ = "carreras"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    facultad: Mapped[str | None] = mapped_column(String(150), nullable=True)

    puntajes: Mapped[list["CarreraPuntaje"]] = relationship(
        back_populates="carrera",
        cascade="all, delete-orphan",
        order_by="CarreraPuntaje.area_key",
    )

    def vector_por_area(self, orden_areas: list[str]) -> list[int]:
        """Devuelve el vector de 17 puntajes en el orden exacto de `AREAS`."""
        mapa = {p.area_key: p.valor for p in self.puntajes}
        return [mapa[area] for area in orden_areas]


class CarreraPuntaje(Base):
    __tablename__ = "carrera_puntajes"
    __table_args__ = (UniqueConstraint("carrera_id", "area_key", name="uq_carrera_area"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    carrera_id: Mapped[int] = mapped_column(ForeignKey("carreras.id"))
    area_key: Mapped[str] = mapped_column(String(64), ForeignKey("areas.key"), index=True)
    valor: Mapped[int]
    """Puntaje entero 1-5 definido por especialistas (ver data/carreras.csv)."""

    carrera: Mapped["Carrera"] = relationship(back_populates="puntajes")
