"""
Modelo de un intento de test vocacional.

Un `IntentoTest` representa una corrida completa (o en progreso) del test,
por cualquiera de los dos métodos (formulario tradicional o chatbot). Se usa
desde la Fase 4 en adelante; se define aquí porque el esquema de base de datos
completo se cierra en la Fase 1.
"""
import datetime as dt
import enum
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Enum, ForeignKey
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.respuesta_test import RespuestaTest
    from app.models.usuario import Usuario


class MetodoTest(enum.StrEnum):
    TRADICIONAL = "tradicional"
    CHATBOT = "chatbot"


class EstadoIntento(enum.StrEnum):
    EN_PROGRESO = "en_progreso"
    COMPLETADO = "completado"
    ABANDONADO = "abandonado"


class IntentoTest(Base):
    __tablename__ = "intentos_test"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id"), nullable=True, index=True
    )
    """Nulo si el intento fue realizado como invitado (sin cuenta)."""

    metodo: Mapped[MetodoTest] = mapped_column(Enum(MetodoTest))
    estado: Mapped[EstadoIntento] = mapped_column(
        Enum(EstadoIntento), default=EstadoIntento.EN_PROGRESO
    )

    vector_usuario: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    """Diccionario {area_key: promedio 1.0-5.0}, calculado al completar el intento."""

    top5_resultado: Mapped[list | None] = mapped_column(JSON, nullable=True)
    """Snapshot del Top 5 calculado (nombre, afinidad_pct, etc.) al momento del cierre."""

    estado_chat: Mapped[dict | None] = mapped_column(MutableDict.as_mutable(JSON), nullable=True)
    """
    Estado de la máquina de estados finita del Método 2 (Fase 6), solo usado
    cuando `metodo == MetodoTest.CHATBOT`. Guarda todo lo necesario para
    reanudar la conversación tras un refresh: área/pregunta actual,
    respuestas por área, preguntas ya usadas, el historial de burbujas
    mostradas y el estado (bienvenida / esperando_respuesta_likert /
    esperando_confirmacion_final / post_resultado). Nulo para intentos del
    Método 1 (formulario tradicional).

    Bug corregido (ver docs/fases/fase-10-chatbot-hibrido.md, sección
    "Bug de persistencia"): con un `JSON` liso, SQLAlchemy compara el valor
    "antiguo" contra el "nuevo" al hacer `intento.estado_chat = estado`. Como
    `chatbot_service` muta `estado` EN EL MISMO objeto que ya estaba cargado
    (no crea uno nuevo), esa comparación los ve como "iguales" (son el mismo
    objeto) y SQLAlchemy omite la columna del UPDATE — la conversación nunca
    se guardaba realmente, así que cada mensaje siguiente releía el estado
    viejo desde la BD y el chatbot repetía la misma pregunta sin avanzar,
    sin importar la respuesta dada. `MutableDict.as_mutable(...)` hace que
    cualquier `estado[clave] = valor` a nivel raíz se detecte como cambio
    automáticamente. Como defensa adicional para las mutaciones anidadas
    (listas dentro del dict, ej. `estado["historial"].append(...)`, que
    `MutableDict` NO detecta por sí solo), `app/api/chatbot.py` además llama
    explícitamente a `flag_modified(intento, "estado_chat")` antes de cada
    commit.
    """

    iniciado_en: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: dt.datetime.now(dt.UTC)
    )
    completado_en: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    usuario: Mapped["Usuario | None"] = relationship(back_populates="intentos")
    respuestas: Mapped[list["RespuestaTest"]] = relationship(
        back_populates="intento", cascade="all, delete-orphan"
    )