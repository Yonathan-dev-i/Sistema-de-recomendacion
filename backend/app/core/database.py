"""
Configuración de la conexión asíncrona a PostgreSQL usando SQLAlchemy 2.0 + asyncpg.

En la Fase 0 solo se define el motor/sesión y la clase base declarativa.
Los modelos concretos (Usuario, Carrera, Area, Pregunta, etc.) se agregan en la Fase 1.
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Clase base declarativa para todos los modelos ORM del sistema."""


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency de FastAPI que entrega una sesión de base de datos por request."""
    async with AsyncSessionLocal() as session:
        yield session
