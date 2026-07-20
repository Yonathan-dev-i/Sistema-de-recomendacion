"""
Importa todos los modelos en un solo lugar para que:
- `Base.metadata` los conozca (necesario para Alembic autogenerate).
- El resto del código pueda hacer `from app.models import Usuario, Carrera, ...`.
"""
from app.models.area import Area
from app.models.carrera import Carrera, CarreraPuntaje
from app.models.intento_test import EstadoIntento, IntentoTest, MetodoTest
from app.models.pregunta import Pregunta
from app.models.respuesta_test import RespuestaTest
from app.models.usuario import Usuario

__all__ = [
    "Area",
    "Carrera",
    "CarreraPuntaje",
    "EstadoIntento",
    "IntentoTest",
    "MetodoTest",
    "Pregunta",
    "RespuestaTest",
    "Usuario",
]
